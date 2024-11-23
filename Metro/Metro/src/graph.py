import re
import heapq
from tkinter import Tk, Label, Entry, Button, Text, Scrollbar, END, StringVar, OptionMenu
from collections import deque

# Fonction pour lire les données du fichier metro.txt et construire le graphe
def lire_graphe(fichier):
    sommets = {}
    aretes = []
    graphe = {}
    noms_station_to_num = {}
    lignes_station = {}

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
                    except ValueError as e:
                        print(f"Erreur de format dans la ligne de sommet : {ligne} ({e})")
                else:
                    print(f"Erreur de format dans la ligne de sommet : {ligne}")

            elif ligne.startswith("E"):
                parts = ligne.split(" ")
                if len(parts) == 4:
                    try:
                        sommet1 = str(int(parts[1]))
                        sommet2 = str(int(parts[2]))
                        temps = int(parts[3])

                        if sommet1 not in sommets or sommet2 not in sommets:
                            print(f"Avertissement : Le sommet {sommet1} ou {sommet2} n'a pas été défini.")
                            continue

                        graphe[sommet1].append((sommet2, temps))
                        graphe[sommet2].append((sommet1, temps))
                        aretes.append((sommet1, sommet2, temps))
                    except ValueError as e:
                        print(f"Erreur de conversion lors de la lecture d'une arête : {ligne} ({e})")
                else:
                    print(f"Erreur de format dans la ligne d'arête : {ligne}")

    return sommets, graphe, aretes, noms_station_to_num, lignes_station


# Algorithme de Bellman-Ford pour trouver le plus court chemin
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


# Fonction pour reconstruire le chemin à partir du prédécesseur
def reconstruire_chemin(pred, start, end):
    chemin = []
    current = end
    while current != start:
        chemin.insert(0, current)
        current = pred[current]
    chemin.insert(0, start)
    return chemin


# Fonction pour afficher l'itinéraire
def afficher_itineraire(chemin, graphe, start, end, noms_station_to_num, lignes_station):
    total_time = 0
    result = f"Itinéraire de {noms_station_to_num[start]} à {noms_station_to_num[end]}:\n"

    ligne_active = None
    trajet_direct = True

    for i in range(len(chemin) - 1):
        station1 = chemin[i]
        station2 = chemin[i + 1]

        for voisin, temps in graphe[station1]:
            if voisin == station2:
                total_time += temps

                lignes_communes = set(lignes_station[station1]) & set(lignes_station[station2])
                if lignes_communes:
                    ligne = list(lignes_communes)[0]
                    if ligne_active is None:
                        ligne_active = ligne
                    elif ligne != ligne_active:
                        trajet_direct = False
                break

    minutes = total_time // 60
    secondes = total_time % 60

    if trajet_direct:
        result += f"- Prenez la ligne {ligne_active} de {noms_station_to_num[start]} jusqu'à {noms_station_to_num[end]}.\n"
    else:
        result += "- Trajet avec changement (détails non implémentés).\n"

    result += f"- Vous devriez arriver à {noms_station_to_num[chemin[-1]]} dans environ {minutes} minutes et {secondes} secondes.\n"
    return result


# Algorithme de Prim pour trouver l'ACPM
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


# Interface Graphique
def lancer_interface():
    def verifier_connexite():
        if est_connexe(graphe):
            result_text.insert(END, "Le graphe est connexe.\n")
        else:
            result_text.insert(END, "Le graphe n'est pas connexe.\n")

    def trouver_chemin_court():
        start = station_depart.get().strip().lower()
        end = station_arrivee.get().strip().lower()

        start_station = None
        end_station = None

        for num_sommet, nom_sommet in noms_station_to_num.items():
            if nom_sommet.lower() == start:
                start_station = num_sommet
            if nom_sommet.lower() == end:
                end_station = num_sommet

        if not start_station or not end_station:
            result_text.insert(END, "Une ou les deux stations ne sont pas dans le réseau.\n")
        else:
            distances, pred = bellman_ford(graphe, start_station)
            if distances[end_station] == float('inf'):
                result_text.insert(END, "Il n'y a pas de chemin entre ces deux stations.\n")
            else:
                chemin = reconstruire_chemin(pred, start_station, end_station)
                itineraire = afficher_itineraire(chemin, graphe, start_station, end_station, noms_station_to_num, lignes_station)
                result_text.insert(END, itineraire + "\n")

    def calculer_acpm():
        acpm, total_weight = prim(graphe)
        result_text.insert(END, "\nArbre Couvrant de Poids Minimum (ACPM):\n")
        for parent, enfant, poids in acpm:
            result_text.insert(END, f"- {noms_station_to_num[parent]} -> {noms_station_to_num[enfant]} (poids : {poids})\n")
        result_text.insert(END, f"Poids total de l'ACPM : {total_weight}\n")

    # Interface principale
    root = Tk()
    root.title("Interface Métro")

    # Formulaire pour trouver le chemin
    Label(root, text="Station de départ:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
    station_depart = Entry(root)
    station_depart.grid(row=0, column=1, padx=10, pady=5)

    Label(root, text="Station d'arrivée:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
    station_arrivee = Entry(root)
    station_arrivee.grid(row=1, column=1, padx=10, pady=5)

    Button(root, text="Trouver le chemin le plus court", command=trouver_chemin_court).grid(row=2, column=0, columnspan=2, pady=10)

    # Bouton pour vérifier la connexité
    Button(root, text="Vérifier Connexité", command=verifier_connexite).grid(row=3, column=0, columnspan=2, pady=10)

    # Bouton pour calculer l'ACPM
    Button(root, text="Calculer l'ACPM", command=calculer_acpm).grid(row=4, column=0, columnspan=2, pady=10)

    # Zone de résultats
    result_text = Text(root, wrap="word", height=20, width=60)
    result_text.grid(row=5, column=0, columnspan=2, padx=10, pady=10)

    # Ajouter une barre de défilement
    scrollbar = Scrollbar(root, command=result_text.yview)
    scrollbar.grid(row=5, column=2, sticky="ns")
    result_text.config(yscrollcommand=scrollbar.set)

    root.mainloop()


# Charger les données et lancer l'interface
if __name__ == "__main__":
    fichier_metro = "C:/Users/Joe/Desktop/Metro/Metro/data/metro.txt"
    sommets, graphe, aretes, noms_station_to_num, lignes_station = lire_graphe(fichier_metro)
    lancer_interface()
