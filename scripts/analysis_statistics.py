import pandas as pd
from datetime import datetime

# ==============================
# 1. Chargement & préparation
# ==============================

def load_and_prepare_data(path="data/raw/notes_epl.csv"):
    print("📥 Chargement des données...")
    df = pd.read_csv(path)

    print("🔄 Conversion des dates de naissance...")
    df["date_naissance"] = pd.to_datetime(
        df["date_naissance"], format="%d/%m/%Y"
    )

    print("📐 Calcul de l'âge des étudiants...")
    today = datetime(2025, 9, 1)
    df["age"] = df["date_naissance"].apply(
        lambda d: today.year - d.year - ((today.month, today.day) < (d.month, d.day))
    )

    print("✅ Données prêtes")
    print(df[["nom", "prenom", "date_naissance", "age"]].head())

    return df


# ==============================
# 2. Statistiques globales
# ==============================

def statistiques_globales(df):
    print("\n📊 Calcul des statistiques globales...")
    return pd.DataFrame([{
        "moyenne": df["note"].mean(),
        "mediane": df["note"].median(),
        "ecart_type": df["note"].std(),
        "min": df["note"].min(),
        "max": df["note"].max(),
        "Q1": df["note"].quantile(0.25),
        "Q3": df["note"].quantile(0.75),
        "taux_reussite_%": (df["note"] >= 10).mean() * 100
    }])


# ==============================
# 3. Statistiques par regroupement
# ==============================

def stats_par_departement(df):
    print("\n🏫 Statistiques par département...")
    return df.groupby("departement")["note"].agg(
        moyenne="mean",
        mediane="median",
        ecart_type="std",
        taux_reussite=lambda x: (x >= 10).mean() * 100
    )


def stats_par_filiere_niveau(df):
    print("\n🎓 Moyenne par filière et niveau...")
    return df.groupby(
        ["departement", "filiere", "niveau"]
    )["note"].mean()


def stats_par_ue_enseignant(df):
    print("\n👩‍🏫📘 Statistiques par UE et enseignant...")
    return df.groupby(
        ["ue", "enseignant"]
    )["note"].agg(
        moyenne="mean",
        ecart_type="std",
        taux_reussite=lambda x: (x >= 10).mean() * 100
    )


# ==============================
# 4. Statistiques démographiques
# ==============================

def stats_par_genre(df):
    print("\n👥 Statistiques par genre...")
    return df.groupby("sexe")["note"].describe()


def stats_par_tranche_age(df):
    print("\n📆 Statistiques par tranche d'âge...")
    df = df.copy()
    df["tranche_age"] = pd.cut(
        df["age"],
        bins=[17, 20, 23, 26, 30],
        labels=["18-20", "21-23", "24-26", "27+"]
    )
    return df.groupby("tranche_age")["note"].mean()


def classement_etudiants(df):
    print("\n🏆 Calcul du classement des étudiants...")

    moyennes = (
        df.groupby(["student_id", "nom", "prenom", "departement", "filiere", "niveau"])
        ["note"]
        .mean()
        .reset_index()
        .rename(columns={"note": "moyenne_generale"})
    )

    moyennes["rang"] = moyennes["moyenne_generale"].rank(
        ascending=False, method="dense"
    )

    return moyennes.sort_values("rang")


# ==============================
# 5. Exécution principale
# ==============================

def main():
    print("\n==============================")
    print("🚀 DÉMARRAGE DE L'ANALYSE EPL")
    print("==============================")

    df = load_and_prepare_data()

    globales = statistiques_globales(df)
    dept = stats_par_departement(df)
    filiere_niveau = stats_par_filiere_niveau(df)
    ue_ens = stats_par_ue_enseignant(df)
    genre = stats_par_genre(df)
    age = stats_par_tranche_age(df)
    classement = classement_etudiants(df)

    print("\n📊 Statistiques globales")
    print(globales)

    print("\n📊 Par département")
    print(dept)

    print("\n📊 Par filière et niveau")
    print(filiere_niveau)

    print("\n📊 Par UE et enseignant")
    print(ue_ens)

    print("\n📊 Par genre")
    print(genre)

    print("\n📊 Par tranche d'âge")
    print(age)

    print("\n📊 Classement des étudiants")
    print(classement)

    # Exports
    globales.to_csv("exports/stats_globales.csv", index=False)
    dept.to_csv("exports/stats_par_departement.csv")
    ue_ens.to_csv("exports/stats_par_ue_enseignant.csv")
    genre.to_csv("exports/stats_par_genre.csv")
    classement.to_csv("exports/classement_etudiants.csv", index=False)

    print("\n📁 Exports réalisés dans le dossier 'exports/'")
    print("✅ Analyse terminée avec succès")


if __name__ == "__main__":
    main()
