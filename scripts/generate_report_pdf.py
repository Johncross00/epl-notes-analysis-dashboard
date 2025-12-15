import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import shutil
import tempfile
from datetime import datetime
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# ==============================
# Chargement & préparation
# ==============================

def load_data(path="data/raw/notes_epl.csv"):
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
# Statistiques globales
# ==============================

def statistiques_globales(df):
    return {
        "Moyenne": round(df["note"].mean(), 2),
        "Médiane": round(df["note"].median(), 2),
        "Écart-type": round(df["note"].std(), 2),
        "Minimum": round(df["note"].min(), 2),
        "Maximum": round(df["note"].max(), 2),
        "Taux de réussite (%)": round((df["note"] >= 10).mean() * 100, 2)
    }


# ==============================
# Fonctions de classement
# ==============================

def classement_general(df):
    c = (
        df.groupby(["student_id", "nom", "prenom", "departement", "filiere", "niveau"])["note"]
        .mean()
        .reset_index()
        .rename(columns={"note": "moyenne"})
    )
    c["rang"] = c["moyenne"].rank(ascending=False, method="dense").astype(int)
    return c.sort_values("rang")


def classement_par_departement(df):
    c = (
        df.groupby(["departement", "student_id", "nom", "prenom"])["note"]
        .mean()
        .reset_index()
        .rename(columns={"note": "moyenne"})
    )
    c["rang"] = c.groupby("departement")["moyenne"].rank(
        ascending=False, method="dense"
    ).astype(int)
    return c.sort_values(["departement", "rang"])


# ==============================
# Génération des graphiques
# ==============================

def generate_histogram_notes(df, output_path):
    """Distribution complète des notes"""
    plt.figure(figsize=(10, 6))
    sns.histplot(df["note"], bins=20, kde=True, color="#4dd0e1")
    plt.title("Distribution complète des notes", fontsize=14, fontweight="bold")
    plt.xlabel("Note", fontsize=12)
    plt.ylabel("Fréquence", fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


def generate_boxplot_departement(df, output_path):
    """Répartition par département"""
    plt.figure(figsize=(12, 6))
    sns.boxplot(data=df, x="departement", y="note", palette="Set2")
    plt.title("Répartition des notes par département", fontsize=14, fontweight="bold")
    plt.xlabel("Département", fontsize=12)
    plt.ylabel("Note", fontsize=12)
    plt.xticks(rotation=20)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


def generate_barplot_ue(df, output_path):
    """Moyennes par UE"""
    ue_stats = df.groupby("ue")["note"].mean().reset_index()
    plt.figure(figsize=(12, 6))
    sns.barplot(data=ue_stats, x="ue", y="note", palette="viridis")
    plt.title("Moyennes des notes par UE", fontsize=14, fontweight="bold")
    plt.xlabel("UE", fontsize=12)
    plt.ylabel("Note moyenne", fontsize=12)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


def generate_heatmap_ue_niveau(df, output_path):
    """Heatmap UE / Niveau"""
    pivot = df.pivot_table(values="note", index="ue", columns="niveau", aggfunc="mean")
    plt.figure(figsize=(10, 6))
    sns.heatmap(pivot, annot=True, cmap="coolwarm", fmt=".2f", cbar_kws={"label": "Note moyenne"})
    plt.title("Heatmap des moyennes par UE et Niveau", fontsize=14, fontweight="bold")
    plt.xlabel("Niveau", fontsize=12)
    plt.ylabel("UE", fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


def generate_boxplot_genre(df, output_path):
    """Analyse par genre"""
    plt.figure(figsize=(8, 6))
    sns.boxplot(data=df, x="sexe", y="note", palette="pastel")
    plt.title("Répartition des notes par genre", fontsize=14, fontweight="bold")
    plt.xlabel("Genre", fontsize=12)
    plt.ylabel("Note", fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


def generate_barplot_tranche_age(df, output_path):
    """Performances par tranche d'âge"""
    df_tmp = df.copy()
    df_tmp["tranche_age"] = pd.cut(
        df_tmp["age"], [17, 20, 23, 26, 30],
        labels=["18-20", "21-23", "24-26", "27+"]
    )
    plt.figure(figsize=(10, 6))
    sns.barplot(data=df_tmp, x="tranche_age", y="note", palette="magma")
    plt.title("Performances par tranche d'âge", fontsize=14, fontweight="bold")
    plt.xlabel("Tranche d'âge", fontsize=12)
    plt.ylabel("Note moyenne", fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()


# ==============================
# Création du PDF
# ==============================

def dataframe_to_table_data(df, max_rows=50):
    """Convertit un DataFrame en données de tableau pour ReportLab"""
    # En-têtes
    headers = [str(col) for col in df.columns]
    table_data = [headers]
    
    # Limiter le nombre de lignes
    df_display = df.head(max_rows)
    
    # Données
    for _, row in df_display.iterrows():
        table_data.append([str(val) if pd.notna(val) else "" for val in row.values])
    
    return table_data


def create_table_from_dataframe(df, col_widths=None, max_rows=50):
    """Crée un tableau ReportLab à partir d'un DataFrame"""
    table_data = dataframe_to_table_data(df, max_rows)
    
    if col_widths is None:
        num_cols = len(df.columns)
        col_widths = [400 / num_cols] * num_cols
    
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.lightgrey])
    ]))
    return table


def generate_pdf():
    df = load_data()
    
    # Créer un répertoire temporaire pour les images
    temp_dir = tempfile.mkdtemp()
    image_paths = {}

    print("📊 Génération des graphiques...")
    
    # Générer tous les graphiques
    image_paths["histogram"] = os.path.join(temp_dir, "histogram_notes.png")
    generate_histogram_notes(df, image_paths["histogram"])
    
    image_paths["boxplot_dept"] = os.path.join(temp_dir, "boxplot_departement.png")
    generate_boxplot_departement(df, image_paths["boxplot_dept"])
    
    image_paths["barplot_ue"] = os.path.join(temp_dir, "barplot_ue.png")
    generate_barplot_ue(df, image_paths["barplot_ue"])
    
    image_paths["heatmap"] = os.path.join(temp_dir, "heatmap_ue_niveau.png")
    generate_heatmap_ue_niveau(df, image_paths["heatmap"])
    
    image_paths["boxplot_genre"] = os.path.join(temp_dir, "boxplot_genre.png")
    generate_boxplot_genre(df, image_paths["boxplot_genre"])
    
    image_paths["barplot_age"] = os.path.join(temp_dir, "barplot_tranche_age.png")
    generate_barplot_tranche_age(df, image_paths["barplot_age"])

    # S'assurer que le répertoire exports existe
    os.makedirs("exports", exist_ok=True)

    doc = SimpleDocTemplate(
        "exports/rapport_analyse_notes_EPL.pdf",
        pagesize=A4
    )

    styles = getSampleStyleSheet()
    elements = []

    # Page de garde
    elements.append(Paragraph("<b>Analyse des Notes de l'EPL</b>", styles["Title"]))
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        "Rapport généré automatiquement à l'aide de Python",
        styles["Normal"]
    ))
    elements.append(Paragraph(
        "Année académique : 2025–2026",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 30))
    elements.append(PageBreak())

    # Description
    elements.append(Paragraph("<b>1. Présentation du projet</b>", styles["Heading2"]))
    elements.append(Paragraph(
        "Ce projet vise à analyser les notes des étudiants de l'EPL à l'aide de Python. "
        "Les données ont été simulées et analysées afin de produire des statistiques "
        "descriptives, des visualisations et des classements académiques.",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 20))

    # Dataset
    elements.append(Paragraph("<b>2. Description du dataset</b>", styles["Heading2"]))
    elements.append(Paragraph(
        f"Le dataset contient {len(df)} notes d'étudiants réparties sur plusieurs "
        "départements, filières et niveaux.",
        styles["Normal"]
    ))
    elements.append(Spacer(1, 20))

    # Statistiques globales
    elements.append(Paragraph("<b>3. Statistiques globales</b>", styles["Heading2"]))

    stats = statistiques_globales(df)
    table_data = [["Indicateur", "Valeur"]] + list(stats.items())

    table = Table(table_data, colWidths=[250, 100])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold")
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    # Statistiques descriptives détaillées
    elements.append(Paragraph("<b>3.1. Statistiques descriptives détaillées</b>", styles["Heading3"]))
    desc_stats = df["note"].describe().reset_index()
    desc_stats.columns = ["Statistique", "Valeur"]
    desc_stats["Valeur"] = desc_stats["Valeur"].round(2)
    desc_table = create_table_from_dataframe(desc_stats, col_widths=[200, 100])
    elements.append(desc_table)
    elements.append(Spacer(1, 20))
    elements.append(PageBreak())

    # ===========================================
    # VUE GLOBALE - Visualisations
    # ===========================================
    elements.append(Paragraph("<b>4. Vue globale - Visualisations</b>", styles["Heading2"]))
    
    # Distribution complète des notes
    elements.append(Paragraph("<b>4.1. Distribution complète des notes</b>", styles["Heading3"]))
    try:
        elements.append(Image(image_paths["histogram"], width=500, height=300))
        elements.append(Spacer(1, 20))
    except Exception as e:
        elements.append(Paragraph(f"Erreur lors du chargement de l'image: {str(e)}", styles["Normal"]))
    
    elements.append(PageBreak())

    # ===========================================
    # ANALYSES DÉTAILLÉES
    # ===========================================
    elements.append(Paragraph("<b>5. Analyses détaillées</b>", styles["Heading2"]))
    
    # Répartition par département
    elements.append(Paragraph("<b>5.1. Répartition par département</b>", styles["Heading3"]))
    try:
        elements.append(Image(image_paths["boxplot_dept"], width=500, height=300))
        elements.append(Spacer(1, 20))
    except Exception as e:
        elements.append(Paragraph(f"Erreur lors du chargement de l'image: {str(e)}", styles["Normal"]))
    
    # Moyennes par UE
    elements.append(Paragraph("<b>5.2. Moyennes par UE</b>", styles["Heading3"]))
    try:
        elements.append(Image(image_paths["barplot_ue"], width=500, height=300))
        elements.append(Spacer(1, 20))
    except Exception as e:
        elements.append(Paragraph(f"Erreur lors du chargement de l'image: {str(e)}", styles["Normal"]))
    
    # Heatmap UE / Niveau
    elements.append(Paragraph("<b>5.3. Heatmap UE / Niveau</b>", styles["Heading3"]))
    try:
        elements.append(Image(image_paths["heatmap"], width=500, height=300))
        elements.append(Spacer(1, 20))
    except Exception as e:
        elements.append(Paragraph(f"Erreur lors du chargement de l'image: {str(e)}", styles["Normal"]))
    
    elements.append(PageBreak())

    # ===========================================
    # DÉMOGRAPHIE
    # ===========================================
    elements.append(Paragraph("<b>6. Démographie</b>", styles["Heading2"]))
    
    # Analyse par genre
    elements.append(Paragraph("<b>6.1. Analyse par genre</b>", styles["Heading3"]))
    try:
        elements.append(Image(image_paths["boxplot_genre"], width=400, height=300))
        elements.append(Spacer(1, 20))
    except Exception as e:
        elements.append(Paragraph(f"Erreur lors du chargement de l'image: {str(e)}", styles["Normal"]))
    
    # Performances par tranche d'âge
    elements.append(Paragraph("<b>6.2. Performances par tranche d'âge</b>", styles["Heading3"]))
    try:
        elements.append(Image(image_paths["barplot_age"], width=500, height=300))
        elements.append(Spacer(1, 20))
    except Exception as e:
        elements.append(Paragraph(f"Erreur lors du chargement de l'image: {str(e)}", styles["Normal"]))
    
    # Statistiques âge / genre
    elements.append(Paragraph("<b>6.3. Statistiques âge / genre</b>", styles["Heading3"]))
    df_tmp = df.copy()
    df_tmp["tranche_age"] = pd.cut(
        df_tmp["age"], [17, 20, 23, 26, 30],
        labels=["18-20", "21-23", "24-26", "27+"]
    )
    stats_age_genre = df_tmp.groupby(["sexe", "tranche_age"])["note"].mean().unstack()
    stats_age_genre = stats_age_genre.round(2).reset_index()
    stats_age_genre.columns = ["Genre"] + [str(col) for col in stats_age_genre.columns[1:]]
    age_genre_table = create_table_from_dataframe(stats_age_genre, col_widths=[100, 80, 80, 80, 80])
    elements.append(age_genre_table)
    elements.append(Spacer(1, 20))
    elements.append(PageBreak())

    # ===========================================
    # CLASSEMENTS
    # ===========================================
    elements.append(Paragraph("<b>7. Classements</b>", styles["Heading2"]))
    
    # Classement général (Top 20)
    elements.append(Paragraph("<b>7.1. Classement général (Top 20)</b>", styles["Heading3"]))
    cg = classement_general(df)
    cg_display = cg.head(20)[["rang", "student_id", "nom", "prenom", "departement", "filiere", "moyenne"]]
    cg_display["moyenne"] = cg_display["moyenne"].round(2)
    cg_table = create_table_from_dataframe(
        cg_display, 
        col_widths=[40, 60, 80, 80, 80, 80, 60],
        max_rows=20
    )
    elements.append(cg_table)
    elements.append(Spacer(1, 20))
    elements.append(PageBreak())
    
    # Classement par département (Top 10 par département)
    elements.append(Paragraph("<b>7.2. Classement par département (Top 10 par département)</b>", styles["Heading3"]))
    cpd = classement_par_departement(df)
    for dept in sorted(cpd["departement"].unique()):
        dept_ranking = cpd[cpd["departement"] == dept].head(10)
        elements.append(Paragraph(f"<b>{dept}</b>", styles["Heading4"]))
        dept_display = dept_ranking[["rang", "student_id", "nom", "prenom", "moyenne"]]
        dept_display["moyenne"] = dept_display["moyenne"].round(2)
        dept_table = create_table_from_dataframe(
            dept_display,
            col_widths=[40, 60, 100, 100, 60],
            max_rows=10
        )
        elements.append(dept_table)
        elements.append(Spacer(1, 15))
    
    elements.append(PageBreak())

    # Conclusion
    elements.append(Paragraph("<b>8. Conclusion</b>", styles["Heading2"]))
    elements.append(Paragraph(
        "L'analyse des notes de l'EPL à l'aide de Python permet une meilleure compréhension "
        "des performances académiques. Les statistiques, visualisations et classements "
        "constituent un outil d'aide à la décision pour les responsables pédagogiques.",
        styles["Normal"]
    ))

    doc.build(elements)
    
    # Nettoyer les fichiers temporaires
    shutil.rmtree(temp_dir)
    
    print("✅ Rapport PDF généré avec succès")


if __name__ == "__main__":
    generate_pdf()
