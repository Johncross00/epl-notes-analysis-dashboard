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


@app.get("/stats/ues", tags=["Statistiques"])
def stats_toutes_ues():
    """Statistiques pour toutes les UE"""
    result = (
        df.groupby("ue")["note"]
        .agg(
            moyenne="mean",
            mediane="median",
            ecart_type="std",
            min="min",
            max="max",
            taux_reussite=lambda x: (x >= 10).mean() * 100,
            nombre_notes="count"
        )
        .reset_index()
    )
    return result.to_dict(orient="records")


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


# ==============================
# CLASSEMENTS
# ==============================

@app.get("/classement/general", tags=["Classements"])
def classement_general(limit: Optional[int] = Query(None, ge=1, le=1000, description="Nombre d'étudiants à retourner")):
    """Classement général de tous les étudiants"""
    classement = (
        df.groupby(["student_id", "nom", "prenom", "departement", "filiere", "niveau"])["note"]
        .mean()
        .reset_index()
        .rename(columns={"note": "moyenne"})
    )
    classement["rang"] = classement["moyenne"].rank(ascending=False, method="dense").astype(int)
    classement = classement.sort_values("rang")
    
    if limit:
        classement = classement.head(limit)
    
    return classement.to_dict(orient="records")


@app.get("/classement/departement", tags=["Classements"])
def classement_departement(
    departement: Optional[str] = Query(None, description="Filtrer par département"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Nombre d'étudiants à retourner")
):
    """Classement par département"""
    data = df.copy()
    
    if departement:
        data = data[data["departement"] == departement]
    
    classement = (
        data.groupby(["departement", "student_id", "nom", "prenom"])["note"]
        .mean()
        .reset_index()
        .rename(columns={"note": "moyenne"})
    )
    classement["rang"] = classement.groupby("departement")["moyenne"].rank(
        ascending=False, method="dense"
    ).astype(int)
    classement = classement.sort_values(["departement", "rang"])
    
    if limit:
        classement = classement.groupby("departement").head(limit)
    
    return classement.to_dict(orient="records")


@app.get("/classement/filiere-niveau", tags=["Classements"])
def classement_filiere_niveau(
    filiere: Optional[str] = Query(None, description="Filtrer par filière"),
    niveau: Optional[str] = Query(None, description="Filtrer par niveau"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Nombre d'étudiants à retourner")
):
    """Classement par filière et niveau"""
    data = df.copy()
    
    if filiere:
        data = data[data["filiere"] == filiere]
    if niveau:
        data = data[data["niveau"] == niveau]
    
    classement = (
        data.groupby(["filiere", "niveau", "student_id", "nom", "prenom"])["note"]
        .mean()
        .reset_index()
        .rename(columns={"note": "moyenne"})
    )
    classement["rang"] = classement.groupby(["filiere", "niveau"])["moyenne"].rank(
        ascending=False, method="dense"
    ).astype(int)
    classement = classement.sort_values(["filiere", "niveau", "rang"])
    
    if limit:
        classement = classement.groupby(["filiere", "niveau"]).head(limit)
    
    return classement.to_dict(orient="records")


@app.get("/classement/ue", tags=["Classements"])
def classement_ue(
    ue: Optional[str] = Query(None, description="Filtrer par UE"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Nombre d'étudiants à retourner")
):
    """Classement par UE"""
    data = df.copy()
    
    if ue:
        data = data[data["ue"] == ue]
    
    classement = (
        data.groupby(["ue", "student_id", "nom", "prenom"])["note"]
        .mean()
        .reset_index()
        .rename(columns={"note": "moyenne"})
    )
    classement["rang"] = classement.groupby("ue")["moyenne"].rank(
        ascending=False, method="dense"
    ).astype(int)
    classement = classement.sort_values(["ue", "rang"])
    
    if limit:
        classement = classement.groupby("ue").head(limit)
    
    return classement.to_dict(orient="records")


@app.get("/classement/top", tags=["Classements"])
def classement_top(
    n: int = Query(10, ge=1, le=100, description="Nombre d'étudiants à retourner")
):
    """Top N étudiants (classement général)"""
    classement = (
        df.groupby(["student_id", "nom", "prenom", "departement", "filiere", "niveau"])["note"]
        .mean()
        .reset_index()
        .rename(columns={"note": "moyenne"})
    )
    classement["rang"] = classement["moyenne"].rank(ascending=False, method="dense").astype(int)
    classement = classement.sort_values("rang").head(n)
    
    return classement.to_dict(orient="records")


# ==============================
# INFORMATIONS ÉTUDIANT
# ==============================

@app.get("/etudiant/{student_id}", tags=["Étudiants"])
def get_etudiant(student_id: str):
    """Informations détaillées sur un étudiant"""
    data = df[df["student_id"] == student_id]
    
    if data.empty:
        return {"error": f"Étudiant {student_id} non trouvé"}
    
    # Informations de base
    etudiant_info = data.iloc[0][["nom", "prenom", "sexe", "date_naissance", "departement", "filiere", "niveau"]].to_dict()
    
    # Statistiques
    moyenne_generale = data["note"].mean()
    notes_par_ue = data.groupby("ue")["note"].agg(["mean", "count"]).reset_index()
    notes_par_ue.columns = ["ue", "moyenne", "nombre_notes"]
    
    return {
        "student_id": student_id,
        "informations": etudiant_info,
        "moyenne_generale": round(moyenne_generale, 2),
        "nombre_total_notes": len(data),
        "notes_par_ue": notes_par_ue.to_dict(orient="records")
    }


@app.get("/etudiant/{student_id}/notes", tags=["Étudiants"])
def get_notes_etudiant(student_id: str):
    """Toutes les notes d'un étudiant"""
    data = df[df["student_id"] == student_id]
    
    if data.empty:
        return {"error": f"Étudiant {student_id} non trouvé"}
    
    result = data[["ue", "enseignant", "note"]].copy()
    return result.to_dict(orient="records")
