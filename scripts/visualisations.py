import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

def load_and_prepare_data(path="data/raw/notes_epl.csv"):
    df = pd.read_csv(path)

    df["date_naissance"] = pd.to_datetime(
        df["date_naissance"], format="%d/%m/%Y"
    )

    today = datetime(2025, 9, 1)
    df["age"] = df["date_naissance"].apply(
        lambda d: today.year - d.year - ((today.month, today.day) < (d.month, d.day))
    )

    return df

def histogramme_notes(df):
    print("📊 Génération de l'histogramme des notes...")

    plt.figure(figsize=(8, 5))
    sns.histplot(df["note"], bins=20, kde=True)
    plt.title("Distribution des notes")
    plt.xlabel("Note")
    plt.ylabel("Nombre d'étudiants")

    plt.savefig("exports/histogramme_notes.png")
    plt.show()


def boxplot_par_departement(df):
    print("📦 Génération du boxplot par département...")

    plt.figure(figsize=(10, 5))
    sns.boxplot(data=df, x="departement", y="note")
    plt.title("Répartition des notes par département")
    plt.xlabel("Département")
    plt.ylabel("Note")

    plt.savefig("exports/boxplot_departement.png")
    plt.show()


def barplot_filiere(df):
    print("📊 Génération du barplot par filière...")

    moyennes = df.groupby("filiere")["note"].mean().reset_index()

    plt.figure(figsize=(10, 5))
    sns.barplot(data=moyennes, x="filiere", y="note")
    plt.title("Moyenne des notes par filière")
    plt.xlabel("Filière")
    plt.ylabel("Note moyenne")
    plt.xticks(rotation=30)

    plt.savefig("exports/barplot_filiere.png")
    plt.show()


def boxplot_genre(df):
    print("👥 Génération du boxplot par genre...")

    plt.figure(figsize=(6, 5))
    sns.boxplot(data=df, x="sexe", y="note")
    plt.title("Répartition des notes par genre")
    plt.xlabel("Genre")
    plt.ylabel("Note")

    plt.savefig("exports/boxplot_genre.png")
    plt.show()


def barplot_tranche_age(df):
    print("📆 Génération du barplot par tranche d'âge...")

    df = df.copy()
    df["tranche_age"] = pd.cut(
        df["age"],
        bins=[17, 20, 23, 26, 30],
        labels=["18-20", "21-23", "24-26", "27+"]
    )

    moyennes = df.groupby("tranche_age")["note"].mean().reset_index()

    plt.figure(figsize=(8, 5))
    sns.barplot(data=moyennes, x="tranche_age", y="note")
    plt.title("Moyenne des notes par tranche d'âge")
    plt.xlabel("Tranche d'âge")
    plt.ylabel("Note moyenne")

    plt.savefig("exports/barplot_tranche_age.png")
    plt.show()


def main():
    print("\n==============================")
    print("📈 DÉMARRAGE DES VISUALISATIONS")
    print("==============================")

    df = load_and_prepare_data()

    histogramme_notes(df)
    boxplot_par_departement(df)
    barplot_filiere(df)
    boxplot_genre(df)
    barplot_tranche_age(df)

    print("\n✅ Tous les graphiques ont été générés et sauvegardés")


if __name__ == "__main__":
    main()
