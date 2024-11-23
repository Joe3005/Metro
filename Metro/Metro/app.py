from flask import Flask, render_template, request, jsonify
import re
import heapq
from collections import deque
from plotly import graph_objs as go


app = Flask(__name__)

# Global variables
sommets, graphe, aretes, noms_station_to_num, lignes_station = {}, {}, [], {}, {}

# Function to load graph
def lire_graphe(fichier):
    global sommets, graphe, aretes, noms_station_to_num, lignes_station
    sommets, graphe, aretes, noms_station_to_num, lignes_station = {}, {}, [], {}, {}

    with open(fichier, 'r', encoding='utf-8') as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne:
                continue

            if ligne.startswith("V"):
                match = re.match(r"V (\d+) (.+) ;([\w]+) ;(True|False)\s*(\d+)", ligne)
                if match:
                    try:
                        num_sommet = str(int(match.group(1)))
                        nom_sommet = match.group(2).replace(' - ', ', ')
                        ligne_num = match.group(3)
                        terminus = match.group(4) == 'True'
                        branchement = int(match.group(5))

                        noms_station_to_num[num_sommet] = nom_sommet
                        if num_sommet not in lignes_station:
                            lignes_station[num_sommet] = []
                        lignes_station[num_sommet].append(ligne_num)

                        sommets[num_sommet] = {
                            'nom': nom_sommet,
                            'ligne_num': ligne_num,
                            'terminus': terminus,
                            'branchements': branchement,
                        }
                        graphe[num_sommet] = []
                    except ValueError:
                        continue

            elif ligne.startswith("E"):
                parts = ligne.split(" ")
                if len(parts) == 4:
                    try:
                        sommet1 = str(int(parts[1]))
                        sommet2 = str(int(parts[2]))
                        temps = int(parts[3])

                        if sommet1 not in sommets or sommet2 not in sommets:
                            continue

                        graphe[sommet1].append((sommet2, temps))
                        graphe[sommet2].append((sommet1, temps))
                        aretes.append((sommet1, sommet2, temps))
                    except ValueError:
                        continue

# Bellman-Ford algorithm
def bellman_ford(graphe, start):
    distances = {station: float('inf') for station in graphe}
    pred = {station: None for station in graphe}
    distances[start] = 0

    for _ in range(len(graphe) - 1):
        for sommet1, voisins in graphe.items():
            for sommet2, temps in voisins:
                if distances[sommet1] + temps < distances[sommet2]:
                    distances[sommet2] = distances[sommet1] + temps
                    pred[sommet2] = sommet1

    return distances, pred


# Prim's algorithm
def prim(graphe):
    acpm = []
    total_weight = 0
    visited = set()
    edges = []

    start_node = next(iter(graphe))
    visited.add(start_node)

    for voisin, poids in graphe[start_node]:
        heapq.heappush(edges, (poids, start_node, voisin))

    while edges:
        poids, parent, enfant = heapq.heappop(edges)
        if enfant not in visited:
            visited.add(enfant)
            acpm.append((parent, enfant, poids))
            total_weight += poids

            for voisin, poids_voisin in graphe[enfant]:
                if voisin not in visited:
                    heapq.heappush(edges, (poids_voisin, enfant, voisin))

    return acpm, total_weight

# Fonction pour reconstruire le chemin à partir des prédécesseurs
def reconstruire_chemin(pred, start, end):
    chemin = []
    current = end
    while current != start:
        chemin.insert(0, current)
        current = pred[current]
    chemin.insert(0, start)
    return chemin



# Connectivity check
def est_connexe(graphe):
    visited = set()
    start_node = next(iter(graphe))

    queue = deque([start_node])
    while queue:
        current = queue.popleft()
        if current not in visited:
            visited.add(current)
            for voisin, _ in graphe[current]:
                if voisin not in visited:
                    queue.append(voisin)

    return len(visited) == len(graphe)

import pandas as pd

def lire_pospoints(fichier):
    points = []
    with open(fichier, 'r', encoding='utf-8') as f:
        for ligne in f:
            try:
                x, y, label = ligne.strip().split(';')
                points.append({'x': int(x), 'y': int(y), 'label': label.replace('@', ' ')})
            except ValueError:
                continue

    # Supprimer les doublons en utilisant un dictionnaire
    unique_points = {f"{point['x']},{point['y']}": point for point in points}
    return list(unique_points.values())

# Charger les points une fois (par exemple dans une variable globale ou dans une fonction dédiée)
pos_points = lire_pospoints('C:/Users/Joe/Desktop/Metro/Metro/data/pospoints.txt')


@app.route('/plot')
def plot():
    # Chargement des données sans doublons
    unique_points = {}
    for point in pos_points:
        if point["label"] not in unique_points:
            unique_points[point["label"]] = (point["x"], -point["y"])

    x_values = [coord[0] for coord in unique_points.values()]
    y_values = [coord[1] for coord in unique_points.values()]
    labels = list(unique_points.keys())

    # Création de la figure Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_values,
        y=y_values,
        mode='markers',
        marker=dict(size=8, color='orange'),
        text=labels,
        hoverinfo='text'
    ))

    # Mise à jour du layout pour occuper toute la largeur
    fig.update_layout(
        title='Carte des Stations',
        title_font=dict(color="orange"),
        paper_bgcolor="#1e1e1e",
        plot_bgcolor="#1e1e1e",
        font=dict(color="white"),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        margin=dict(l=0, r=0, t=50, b=0),
        height=600
    )

    # Retourner la figure comme un HTML Plotly
    return fig.to_html(full_html=True)


@app.route('/stations', methods=['GET'])
def get_stations():
    fichier_pospoints = "C:/Users/Joe/Desktop/Metro/Metro/data/pospoints.txt"  # Chemin du fichier
    points = lire_pospoints(fichier_pospoints)
    # Renvoie les données au format JSON
    return jsonify(points)



@app.route('/')
def index():
    return render_template('index.html')


@app.route('/connexite', methods=['GET'])
def verifier_connexite():
    connected = est_connexe(graphe)
    return jsonify({'connexe': connected})


@app.route('/chemin', methods=['POST'])
def chemin_court():
    data = request.json
    start_name = data['start'].strip().lower()
    end_name = data['end'].strip().lower()

    start_station = None
    end_station = None

    # Recherche des stations
    for num_sommet, nom_sommet in noms_station_to_num.items():
        if nom_sommet.lower() == start_name:
            start_station = num_sommet
        if nom_sommet.lower() == end_name:
            end_station = num_sommet

    if not start_station or not end_station:
        return jsonify({'error': "Une ou les deux stations ne sont pas dans le réseau."})

    # Calcul du plus court chemin
    distances, pred = bellman_ford(graphe, start_station)
    if distances[end_station] == float('inf'):
        return jsonify({'error': "Il n'y a pas de chemin entre ces deux stations."})

    chemin = reconstruire_chemin(pred, start_station, end_station)

    # Préparer le format des résultats
    total_time = distances[end_station]
    minutes, seconds = divmod(total_time, 60)

    instructions = []  # Liste pour stocker les instructions d'itinéraire
    ligne_active = None
    current_start = noms_station_to_num[start_station]

    # Tracé du chemin sur la carte
    chemin_coords = []
    station_coords = {point["label"].lower(): (point["x"], -point["y"]) for point in pos_points}

    for i in range(len(chemin) - 1):
        station1 = chemin[i]
        station2 = chemin[i + 1]

        for voisin, temps in graphe[station1]:
            if voisin == station2:
                lignes_communes = set(lignes_station[station1]) & set(lignes_station[station2])
                if lignes_communes:
                    ligne = list(lignes_communes)[0]
                    if ligne_active is None:
                        ligne_active = ligne
                    elif ligne != ligne_active:
                        # Si la ligne change, on ajoute une instruction
                        instructions.append(
                            f"Prenez la ligne {ligne_active} de {current_start} jusqu'à {noms_station_to_num[station1]}."
                        )
                        current_start = noms_station_to_num[station1]
                        ligne_active = ligne

                # Ajouter les coordonnées pour le tracé
                if noms_station_to_num[station1].lower() in station_coords:
                    chemin_coords.append(station_coords[noms_station_to_num[station1].lower()])
                if noms_station_to_num[station2].lower() in station_coords:
                    chemin_coords.append(station_coords[noms_station_to_num[station2].lower()])
                break

    # Ajouter la dernière instruction
    instructions.append(
        f"Prenez la ligne {ligne_active} de {current_start} jusqu'à {noms_station_to_num[end_station]}."
    )

    # Ajouter les coordonnées de la dernière station
    if noms_station_to_num[end_station].lower() in station_coords:
        chemin_coords.append(station_coords[noms_station_to_num[end_station].lower()])

    # Préparer les coordonnées X et Y pour le tracé
    x_coords = [coord[0] for coord in chemin_coords]
    y_coords = [coord[1] for coord in chemin_coords]

    return jsonify({
        'instructions': instructions,
        'time': f"{minutes} minutes et {seconds} secondes",
        'x_coords': x_coords,
        'y_coords': y_coords
    })



@app.route('/acpm', methods=['GET'])
def calculer_acpm():
    acpm, total_weight = prim(graphe)
    acpm_list = [
        {
            'parent': noms_station_to_num[parent],
            'child': noms_station_to_num[enfant],
            'poids': poids
        }
        for parent, enfant, poids in acpm
    ]
    return jsonify({'acpm': acpm_list, 'total_weight': total_weight})

@app.route('/search_stations')
def search_stations():
    query = request.args.get('q', '').strip().lower()
    if not query:
        return jsonify([])

    seen = set()  # Utilisé pour éviter les doublons
    matching_stations = []

    for num, name in noms_station_to_num.items():
        lower_name = name.lower()
        if lower_name.startswith(query) and lower_name not in seen:
            matching_stations.append({'id': num, 'name': name})
            seen.add(lower_name)  # Ajoute le nom à l'ensemble pour éviter les doublons

    return jsonify(matching_stations)



if __name__ == '__main__':
    lire_graphe("C:/Users/Joe/Desktop/Metro/Metro/data/metro.txt")  # Load graph data
    app.run(debug=True)

