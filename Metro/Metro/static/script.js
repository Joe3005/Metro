// Fonction pour chercher les stations avec saisie rapide
async function fetchStations(inputId) {
    const query = document.getElementById(inputId).value.trim();
    const suggestionsDiv = document.getElementById(`${inputId}-suggestions`);

    if (query.length === 0) {
        suggestionsDiv.style.display = "none";
        return;
    }

    try {
        const response = await fetch(`/search_stations?q=${query}`);
        const stations = await response.json();

        suggestionsDiv.innerHTML = "";
        if (stations.length > 0) {
            stations.forEach(station => {
                const suggestion = document.createElement('div');
                suggestion.textContent = station.name;
                suggestion.className = "suggestion-item";
                suggestion.onclick = () => {
                    document.getElementById(inputId).value = station.name;
                    suggestionsDiv.style.display = "none";
                };
                suggestionsDiv.appendChild(suggestion);
            });
            suggestionsDiv.style.display = "block";
        } else {
            suggestionsDiv.style.display = "none";
        }
    } catch (error) {
        console.error("Erreur lors de la recherche des stations :", error);
    }
}

// Ajouter les événements d'entrée pour la recherche rapide
document.getElementById('start').addEventListener('input', () => fetchStations('start'));
document.getElementById('end').addEventListener('input', () => fetchStations('end'));

// Fonction pour calculer le chemin le plus court
async function findShortestPath() {
    const start = document.getElementById('start').value.trim();
    const end = document.getElementById('end').value.trim();

    if (!start || !end) {
        alert("Veuillez remplir les champs de départ et d'arrivée.");
        return;
    }

    try {
        const response = await fetch('/chemin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ start, end })
        });
        const data = await response.json();

        const resultsDiv = document.getElementById('results');
        if (data.error) {
            resultsDiv.innerHTML = `<p style="color: red;">${data.error}</p>`;
        } else {
            let itineraireHTML = data.instructions.map(instr => `<li>${instr}</li>`).join('');
            resultsDiv.innerHTML = `
                <h3>Itinéraire :</h3>
                <ul>${itineraireHTML}</ul>
                <p><strong>Temps estimé :</strong> ${data.time}</p>
            `;

            // Dessiner le chemin sur la carte
            drawPath(data.x_coords, data.y_coords);
        }
    } catch (error) {
        console.error("Erreur lors du calcul du chemin :", error);
    }
}

// Fonction pour vérifier la connexité
async function checkConnectivity() {
    try {
        const response = await fetch('/connexite');
        const data = await response.json();

        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = `
            <h3>Connexité :</h3>
            <p>Le graphe est ${data.connexe ? "" : "non "}connexe.</p>
        `;
    } catch (error) {
        console.error("Erreur lors de la vérification de la connexité :", error);
    }
}

// Fonction pour calculer l'ACPM
async function calculateACPM() {
    try {
        const response = await fetch('/acpm');
        const data = await response.json();

        let acpmHTML = data.acpm.map(edge => `<li>${edge.parent} → ${edge.child} (poids : ${edge.poids})</li>`).join('');
        const resultsDiv = document.getElementById('results');
        resultsDiv.innerHTML = `
            <h3>ACPM :</h3>
            <ul>${acpmHTML}</ul>
            <p><strong>Poids total :</strong> ${data.total_weight}</p>
        `;
    } catch (error) {
        console.error("Erreur lors du calcul de l'ACPM :", error);
    }
}

// Fonction pour dessiner un chemin sur la carte avec Plotly
function drawPath(x_coords, y_coords) {
    const plotDiv = document.getElementById('carte-stations');

    Plotly.addTraces(plotDiv, {
        x: x_coords,
        y: y_coords,
        mode: 'lines',
        line: {
            color: 'cyan',
            width: 2
        }
    });
}

// Ajout des événements aux boutons
document.getElementById('search-btn').addEventListener('click', findShortestPath);
document.getElementById('connexite-btn').addEventListener('click', checkConnectivity);
document.getElementById('acpm-btn').addEventListener('click', calculateACPM);

