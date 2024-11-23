from geopy.geocoders import Nominatim
import time


# Lire les stations uniques depuis metro.txt
def read_unique_stations(file_path):
    stations = set()
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            if line.startswith("V"):
                parts = line.split(" ", 2)
                if len(parts) > 2:
                    station_name = parts[2].split(";")[0].strip().replace(' - ', ', ')
                    stations.add(station_name)
    return list(stations)


# Trouver les coordonnées GPS des stations
def fetch_coordinates(stations):
    geolocator = Nominatim(user_agent="metro_locator")
    results = {}

    for station in stations:
        try:
            location = geolocator.geocode(f"{station}, Paris, France")
            if location:
                results[station] = (location.latitude, location.longitude)
                print(f"Station: {station} | Coords: {location.latitude}, {location.longitude}")
            else:
                results[station] = None
                print(f"Station: {station} not found.")
            time.sleep(1)  # Pause pour éviter d'être bloqué par l'API
        except Exception as e:
            print(f"Erreur pour {station}: {e}")
    return results


# Sauvegarder les coordonnées dans un fichier
def save_coordinates_to_file(coordinates, output_file):
    with open(output_file, 'w', encoding='utf-8') as file:
        for station, coord in coordinates.items():
            if coord:
                file.write(f"{station};{coord[0]};{coord[1]}\n")
            else:
                file.write(f"{station};NOT FOUND\n")


if __name__ == "__main__":
    input_file = "C:/Users/Joe/Desktop/Metro/Metro/data/metro.txt"  # Remplacez par le chemin correct
    output_file = "C:/Users/Joe/Desktop/Metro/Metro/data/stations_coordinates.csv"

    stations = read_unique_stations(input_file)
    print(f"Stations uniques trouvées : {len(stations)}")
    coordinates = fetch_coordinates(stations)
    save_coordinates_to_file(coordinates, output_file)

    print(f"Les coordonnées ont été enregistrées dans {output_file}")
