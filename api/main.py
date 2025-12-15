from fastapi import FastAPI, Query
import pandas as pd
from datetime import datetime
from typing import Optional

app = FastAPI(
    title="API Statistiques EPL",
    description="API pour l’analyse statistique des notes des étudiants de l’EPL",
    version="1.0"
)

# ==============================
# Chargement et préparation
# ==============================

def load_data():
    df = pd.read_csv("data/raw/notes_epl.csv")

    df["date_naissance"] = pd.to_datetime(
        df["date_naissance"], format="%d/%m/%Y"
    )

    today = datetime(2025, 9, 1)
    df["age"] = df["date_naissance"].apply(
        lambda d: today.year - d.year - ((today.month, today.day) < (d.month, d.day))
    )

    return df


df = load_data()

# ==============================
# ENDPOINTS DE BASE (LISTES)
# ==============================

@app.get("/departements", tags=["Référentiels"])
def get_departements():
    """Retourne la liste de tous les départements"""
    return sorted(df["departement"].unique().tolist())


@app.get("/filieres", tags=["Référentiels"])
def get_filieres(departement: Optional[str] = None):
    """Retourne les filières, optionnellement filtrées par département"""
    data = df
    if departement:
        data = data[data["departement"] == departement]
    return sorted(data["filiere"].unique().tolist())


@app.get("/enseignants", tags=["Référentiels"])
def get_enseignants(departement: Optional[str] = None):
    """Retourne les enseignants, optionnellement filtrés par département"""
    data = df
    if departement:
        data = data[data["departement"] == departement]
    return sorted(data["enseignant"].unique().tolist())


@app.get("/ues", tags=["Référentiels"])
def get_ues(niveau: Optional[str] = None):
    """Retourne les UE, optionnellement filtrées par niveau"""
    data = df
    if niveau:
        data = data[data["niveau"] == niveau]
    return sorted(data["ue"].unique().tolist())


# ==============================
# STATISTIQUES GLOBALES
# ==============================

@app.get("/stats/globales", tags=["Statistiques"])
def stats_globales():
    """Statistiques descriptives globales"""
    return {
        "moyenne": df["note"].mean(),
        "mediane": df["note"].median(),
        "ecart_type": df["note"].std(),
        "min": df["note"].min(),
        "max": df["note"].max(),
        "Q1": df["note"].quantile(0.25),
        "Q3": df["note"].quantile(0.75),
        "taux_reussite_%": (df["note"] >= 10).mean() * 100
    }


# ==============================
# STATISTIQUES PAR REGROUPEMENT
# ==============================

@app.get("/stats/departement", tags=["Statistiques"])
def stats_departement():
    """Statistiques par département"""
    result = (
        df.groupby("departement")["note"]
        .agg(
            moyenne="mean",
            mediane="median",
            ecart_type="std",
            taux_reussite=lambda x: (x >= 10).mean() * 100
        )
        .reset_index()
    )
    return result.to_dict(orient="records")


@app.get("/stats/enseignant", tags=["Statistiques"])
def stats_enseignant(enseignant: str = Query(..., example="Mme KOUADIO")):
    """Statistiques pour un enseignant donné"""
    data = df[df["enseignant"] == enseignant]

    return {
        "enseignant": enseignant,
        "moyenne": data["note"].mean(),
        "ecart_type": data["note"].std(),
        "taux_reussite_%": (data["note"] >= 10).mean() * 100,
        "nombre_notes": len(data)
    }


@app.get("/stats/ue", tags=["Statistiques"])
def stats_ue(ue: str = Query(..., example="UE302")):
    """Statistiques pour une UE donnée"""
    data = df[df["ue"] == ue]

    return {
        "ue": ue,
        "moyenne": data["note"].mean(),
        "ecart_type": data["note"].std(),
        "taux_reussite_%": (data["note"] >= 10).mean() * 100
    }


# ==============================
# STATISTIQUES DÉMOGRAPHIQUES
# ==============================

@app.get("/stats/genre", tags=["Démographie"])
def stats_genre():
    """Statistiques par genre"""
    result = df.groupby("sexe")["note"].describe().reset_index()
    return result.to_dict(orient="records")


@app.get("/stats/tranche-age", tags=["Démographie"])
def stats_tranche_age():
    """Moyenne des notes par tranche d'âge"""
    data = df.copy()
    data["tranche_age"] = pd.cut(
        data["age"],
        bins=[17, 20, 23, 26, 30],
        labels=["18-20", "21-23", "24-26", "27+"]
    )
    result = data.groupby("tranche_age")["note"].mean().reset_index()
    return result.to_dict(orient="records")
