import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

np.random.seed(42)
random.seed(42)

N_STUDENTS = 1200
ANNEE_ACADEMIQUE = "2025-2026"

# Noms et prénoms réalistes
noms = [
    "SCHMITT", "DELANNOY", "DIJOUX", "WAGNER", "MARTIN",
    "DUPONT", "BERNARD", "MOREAU", "ROBERT", "PETIT"
]

prenoms = [
    "Danielle", "Agathe", "Madeleine", "Stéphane", "Lucas",
    "Emma", "Sophie", "Thomas", "Julie", "Antoine"
]

# Structure académique EPL
departements = {
    "Génie Civil": {
        "filieres": ["GC Bâtiment", "GC Travaux Publics"],
        "niveaux": ["L2", "L3", "M1"],
        "ues": {
            "L2": [("UE102", "Électricité")],
            "L3": [("UE201", "Résistance des matériaux")],
            "M1": [("UE301", "Mathématiques")]
        }
    },
    "Informatique": {
        "filieres": ["Génie Logiciel", "Intelligence Artificielle"],
        "niveaux": ["L3", "M1"],
        "ues": {
            "L3": [("UE302", "Base de données")],
            "M1": [("UE401", "Machine Learning")]
        }
    },
    "Réseaux & Télécoms": {
        "filieres": ["Télécommunications"],
        "niveaux": ["L1", "L2"],
        "ues": {
            "L1": [("UE101", "Réseaux de base")],
            "L2": [("UE202", "Transmission de données")]
        }
    }
}

enseignants = ["Mme KOUADIO", "M. DADEOU", "Prof TRAORE"]

def random_birthdate(start_year=1995, end_year=2007):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))

rows = []

for i in range(N_STUDENTS):
    nom = random.choice(noms)
    prenom = random.choice(prenoms)
    sexe = random.choice(["M", "F"])
    date_naissance = random_birthdate().strftime("%d/%m/%Y")

    departement = random.choice(list(departements.keys()))
    filiere = random.choice(departements[departement]["filieres"])
    niveau = random.choice(departements[departement]["niveaux"])

    ue_code, matiere = random.choice(departements[departement]["ues"][niveau])
    enseignant = random.choice(enseignants)

    note = round(np.clip(np.random.normal(12, 3), 0, 20), 2)

    rows.append({
        "student_id": f"EPL{i+1:04}",
        "nom": nom,
        "prenom": prenom,
        "sexe": sexe,
        "date_naissance": date_naissance,
        "departement": departement,
        "filiere": filiere,
        "niveau": niveau,
        "annee_academique": ANNEE_ACADEMIQUE,
        "ue": ue_code,
        "matiere": matiere,
        "enseignant": enseignant,
        "note": note
    })

df = pd.DataFrame(rows)

df.to_csv("data/raw/notes_epl.csv", index=False, encoding="utf-8")
df.to_excel("data/raw/notes_epl.xlsx", index=False)

print("✅ Dataset EPL enrichi généré avec succès")
print(df.head())
