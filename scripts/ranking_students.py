import pandas as pd
from datetime import datetime

# ==============================
# Chargement & préparation
# ==============================

def load_and_prepare_data(path="data/raw/notes_epl.csv"):
    print("📥 Chargement des données...")
    df = pd.read_csv(path)

    df["date_naissance"] = pd.to_datetime(
        df["date_naissance"], format="%d/%m/%Y"
    )

    today = datetime(2025, 9, 1)
    df["age"] = df["date_naissance"].apply(
        lambda d: today.year - d.year - ((today.month, today.day) < (d.month, d.day))
    )

    return df


# ==============================
# Classements
# ==============================

def classement_general(df):
    print("\n🏆 Classement général des étudiants...")

    classement = (
        df.groupby(
            ["student_id", "nom", "prenom", "departement", "filiere", "niveau"]
        )["note"]
        .mean()
        .reset_index()
        .rename(columns={"note": "moyenne"})
    )

    classement["rang"] = classement["moyenne"].rank(
        ascending=False, method="dense"
    ).astype(int)

    return classement.sort_values("rang")


def classement_par_departement(df):
    print("\n🏫 Classement par département...")

    classement = (
        df.groupby(
            ["departement", "student_id", "nom", "prenom"]
        )["note"]
        .mean()
        .reset_index()
        .rename(columns={"note": "moyenne"})
    )

    classement["rang"] = (
        classement.groupby("departement")["moyenne"]
        .rank(ascending=False, method="dense")
        .astype(int)
    )

    return classement.sort_values(["departement", "rang"])


def classement_par_filiere_niveau(df):
    print("\n🎓 Classement par filière et niveau...")

    classement = (
        df.groupby(
            ["filiere", "niveau", "student_id", "nom", "prenom"]
        )["note"]
        .mean()
        .reset_index()
        .rename(columns={"note": "moyenne"})
    )

    classement["rang"] = (
        classement.groupby(["filiere", "niveau"])["moyenne"]
        .rank(ascending=False, method="dense")
        .astype(int)
    )

    return classement.sort_values(["filiere", "niveau", "rang"])


def classement_par_ue(df):
    print("\n📘 Classement par UE...")

    classement = (
        df.groupby(
            ["ue", "student_id", "nom", "prenom"]
        )["note"]
        .mean()
        .reset_index()
        .rename(columns={"note": "moyenne"})
    )

    classement["rang"] = (
        classement.groupby("ue")["moyenne"]
        .rank(ascending=False, method="dense")
        .astype(int)
    )

    return classement.sort_values(["ue", "rang"])


# ==============================
# Exécution principale
# ==============================

def main():
    print("\n==============================")
    print("🏆 CLASSEMENT DES ÉTUDIANTS EPL")
    print("==============================")

    df = load_and_prepare_data()

    general = classement_general(df)
    departement = classement_par_departement(df)
    filiere_niveau = classement_par_filiere_niveau(df)
    ue = classement_par_ue(df)

    print("\n🏆 TOP 10 - Classement général")
    print(general.head(10))

    # Exports
    general.to_csv("exports/classement_general.csv", index=False)
    departement.to_csv("exports/classement_par_departement.csv", index=False)
    filiere_niveau.to_csv("exports/classement_par_filiere_niveau.csv", index=False)
    ue.to_csv("exports/classement_par_ue.csv", index=False)

    print("\n📁 Classements exportés dans le dossier 'exports/'")
    print("✅ Classement terminé avec succès")


if __name__ == "__main__":
    main()
