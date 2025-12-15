import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime

# =================================
# Configuration de la page
# =================================
st.set_page_config(
    page_title="Dashboard EPL – Analyse des Notes",
    layout="wide"
)
st.markdown("""
<style>
/* Fond général */
.stApp {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: white;
}

/* Cartes glassmorphism */
.glass {
    background: rgba(255, 255, 255, 0.12);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-radius: 18px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.25);
}

/* Titres */
h1, h2, h3 {
    color: #ffffff;
}

/* Dataframe */
[data-testid="stDataFrame"] {
    background-color: rgba(255,255,255,0.05);
    border-radius: 12px;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: rgba(0,0,0,0.35);
    backdrop-filter: blur(10px);
}
</style>
""", unsafe_allow_html=True)


st.title("📊 Tableau de Bord Statistique – EPL")

# =================================
# Chargement des données
# =================================
@st.cache_data
def load_data():
    df = pd.read_csv("data/raw/notes_epl.csv")
    df["date_naissance"] = pd.to_datetime(df["date_naissance"], format="%d/%m/%Y")

    today = datetime(2025, 9, 1)
    df["age"] = df["date_naissance"].apply(
        lambda d: today.year - d.year - ((today.month, today.day) < (d.month, d.day))
    )
    return df


def load_external_data(uploaded_file):
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        if df.empty:
            raise ValueError("Le fichier est vide")
        
        return df
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement du fichier : {str(e)}")
        return None


# =================================
# Sidebar - File Uploader
# =================================
st.sidebar.header("📤 Importer des données")

uploaded_file = st.sidebar.file_uploader(
    "📂 Charger un fichier CSV ou Excel",
    type=["csv", "xlsx"]
)

st.sidebar.divider()


# =================================
# Chargement effectif du dataset
# =================================
df = None
data_source = "Dataset interne du projet"
mapping_complete = True

if uploaded_file is not None:
    df = load_external_data(uploaded_file)
    if df is None:
        st.stop()
    
    st.success(f"✅ Fichier chargé : {uploaded_file.name}")
    data_source = f"Fichier importé : {uploaded_file.name}"

    EXPECTED_COLUMNS = {
        "student_id": "Identifiant étudiant",
        "nom": "Nom",
        "prenom": "Prénom",
        "sexe": "Genre",
        "date_naissance": "Date de naissance",
        "departement": "Département",
        "filiere": "Filière",
        "niveau": "Niveau",
        "ue": "UE",
        "enseignant": "Enseignant",
        "note": "Note"
    }

    st.markdown("## 🔁 Mapping des colonnes")

    mapping = {}
    for key, label in EXPECTED_COLUMNS.items():
        mapping[key] = st.selectbox(
            f"{label}",
            options=[""] + list(df.columns),
            key=f"map_{key}"
        )

    if "" in mapping.values():
        st.warning("⚠️ Veuillez mapper toutes les colonnes avant de continuer")
        mapping_complete = False
        st.stop()
    else:
        # Renommer les colonnes
        df = df.rename(columns={v: k for k, v in mapping.items()})
        
        # Traitement des dates et âges
        try:
            df["date_naissance"] = pd.to_datetime(
                df["date_naissance"], format="%d/%m/%Y", errors="coerce"
            )
            today = datetime(2025, 9, 1)
            df["age"] = df["date_naissance"].apply(
                lambda d: today.year - d.year - ((today.month, today.day) < (d.month, d.day))
                if pd.notnull(d) else None
            )
        except Exception as e:
            st.warning(f"⚠️ Erreur lors du traitement des dates : {str(e)}")

    # Validation des colonnes requises
    required_columns = [
        "student_id", "nom", "prenom", "sexe", "date_naissance",
        "departement", "filiere", "niveau", "ue", "enseignant", "note"
    ]

    missing_cols = [col for col in required_columns if col not in df.columns]

    if missing_cols:
        st.error(
            "❌ Le fichier importé n'est pas valide.\n\n"
            f"Colonnes manquantes après mapping : {', '.join(missing_cols)}"
        )
        st.stop()
    
    # Validation des types de données
    try:
        # Vérifier que la colonne note est numérique
        df["note"] = pd.to_numeric(df["note"], errors="coerce")
        if df["note"].isna().all():
            st.error("❌ La colonne 'note' ne contient pas de valeurs numériques valides")
            st.stop()
    except Exception as e:
        st.error(f"❌ Erreur lors de la validation de la colonne 'note' : {str(e)}")
        st.stop()
else:
    df = load_data()
    st.info("ℹ️ Dataset par défaut utilisé")

# Ensure df is defined and valid
if df is None or df.empty:
    st.error("❌ Erreur lors du chargement des données")
    st.stop()

# =================================
# Fonctions de classement
# =================================
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


def classement_par_filiere_niveau(df):
    c = (
        df.groupby(["filiere", "niveau", "student_id", "nom", "prenom"])["note"]
        .mean()
        .reset_index()
        .rename(columns={"note": "moyenne"})
    )
    c["rang"] = c.groupby(["filiere", "niveau"])["moyenne"].rank(
        ascending=False, method="dense"
    ).astype(int)
    return c.sort_values(["filiere", "niveau", "rang"])


# =================================
# Filtres (sidebar)
# =================================
st.sidebar.header("🔎 Filtres")

# Gestion sécurisée des filtres avec vérification des colonnes
try:
    departements = ["Tous"] + sorted([str(x) for x in df["departement"].dropna().unique()])
    departement = st.sidebar.selectbox("Département", departements)
except Exception:
    departement = "Tous"
    st.sidebar.warning("⚠️ Colonne 'departement' non disponible")

try:
    filieres = ["Toutes"] + sorted([str(x) for x in df["filiere"].dropna().unique()])
    filiere = st.sidebar.selectbox("Filière", filieres)
except Exception:
    filiere = "Toutes"
    st.sidebar.warning("⚠️ Colonne 'filiere' non disponible")

try:
    niveaux = ["Tous"] + sorted([str(x) for x in df["niveau"].dropna().unique()])
    niveau = st.sidebar.selectbox("Niveau", niveaux)
except Exception:
    niveau = "Tous"
    st.sidebar.warning("⚠️ Colonne 'niveau' non disponible")

try:
    enseignants = ["Tous"] + sorted([str(x) for x in df["enseignant"].dropna().unique()])
    enseignant = st.sidebar.selectbox("Enseignant", enseignants)
except Exception:
    enseignant = "Tous"
    st.sidebar.warning("⚠️ Colonne 'enseignant' non disponible")

df_filtered = df.copy()
try:
    if departement != "Tous" and "departement" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["departement"] == departement]
    if filiere != "Toutes" and "filiere" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["filiere"] == filiere]
    if niveau != "Tous" and "niveau" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["niveau"] == niveau]
    if enseignant != "Tous" and "enseignant" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["enseignant"] == enseignant]
    
    if df_filtered.empty:
        st.sidebar.warning("⚠️ Aucune donnée ne correspond aux filtres sélectionnés")
        df_filtered = df.copy()  # Réinitialiser aux données complètes
except Exception as e:
    st.sidebar.error(f"❌ Erreur lors du filtrage : {str(e)}")
    df_filtered = df.copy()

# =================================
# ONGLET PRINCIPAUX
# =================================
tab_global, tab_analysis, tab_demo, tab_rank, tab_export, tab_data, tab_comparison = st.tabs([
    "📊 Vue globale",
    "📈 Analyses détaillées",
    "👥 Démographie",
    "🏆 Classements",
    "📄 Exports & rapports",
    "📋 Données brutes",
    "📊 Comparaison"
])

# =================================
# 📊 VUE GLOBALE
# =================================
with tab_global:
    try:
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.subheader("📌 Indicateurs généraux")

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Moyenne", round(df_filtered["note"].mean(), 2) if not df_filtered["note"].isna().all() else 0)
        c2.metric("Médiane", round(df_filtered["note"].median(), 2) if not df_filtered["note"].isna().all() else 0)
        c3.metric("Écart-type", round(df_filtered["note"].std(), 2) if not df_filtered["note"].isna().all() else 0)
        c4.metric("Taux réussite (%)", round((df_filtered["note"] >= 10).mean()*100, 2) if not df_filtered["note"].isna().all() else 0)
        c5.metric("Nombre de notes", len(df_filtered))
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.markdown("### 📈 Distribution complète des notes")
        try:
            fig, ax = plt.subplots()
            sns.histplot(df_filtered["note"].dropna(), bins=20, kde=True, color="#4dd0e1")
            st.pyplot(fig)
            plt.close(fig)
        except Exception as e:
            st.error(f"❌ Erreur lors de la génération du graphique : {str(e)}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.markdown("### 📊 Statistiques descriptives détaillées")
        try:
            st.dataframe(df_filtered["note"].describe())
        except Exception as e:
            st.error(f"❌ Erreur lors de l'affichage des statistiques : {str(e)}")
        st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Erreur dans la vue globale : {str(e)}")

# =================================
# 📈 ANALYSES DÉTAILLÉES
# =================================
with tab_analysis:
    try:
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.markdown("### 📦 Répartition par département")
        try:
            if "departement" in df_filtered.columns and not df_filtered["departement"].isna().all():
                fig, ax = plt.subplots()
                sns.boxplot(data=df_filtered.dropna(subset=["departement", "note"]), x="departement", y="note", palette="Set2")
                plt.xticks(rotation=20)
                st.pyplot(fig)
                plt.close(fig)
            else:
                st.warning("⚠️ Données insuffisantes pour générer ce graphique")
        except Exception as e:
            st.error(f"❌ Erreur lors de la génération du graphique : {str(e)}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.markdown("### 📊 Moyennes par UE")
        try:
            if "ue" in df_filtered.columns and not df_filtered["ue"].isna().all():
                ue_stats = df_filtered.groupby("ue")["note"].mean().reset_index()
                fig, ax = plt.subplots()
                sns.barplot(data=ue_stats, x="ue", y="note", palette="viridis")
                plt.xticks(rotation=45, ha="right")
                st.pyplot(fig)
                plt.close(fig)
            else:
                st.warning("⚠️ Données insuffisantes pour générer ce graphique")
        except Exception as e:
            st.error(f"❌ Erreur lors de la génération du graphique : {str(e)}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.markdown("### 🔥 Heatmap UE / Niveau")
        try:
            if "ue" in df_filtered.columns and "niveau" in df_filtered.columns:
                pivot = df_filtered.pivot_table(values="note", index="ue", columns="niveau", aggfunc="mean")
                if not pivot.empty:
                    fig, ax = plt.subplots(figsize=(8,4))
                    sns.heatmap(pivot, annot=True, cmap="coolwarm", fmt=".2f")
                    st.pyplot(fig)
                    plt.close(fig)
                else:
                    st.warning("⚠️ Données insuffisantes pour générer ce graphique")
            else:
                st.warning("⚠️ Colonnes 'ue' ou 'niveau' manquantes")
        except Exception as e:
            st.error(f"❌ Erreur lors de la génération du graphique : {str(e)}")
        st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Erreur dans les analyses détaillées : {str(e)}")

# =================================
# 👥 DÉMOGRAPHIE
# =================================
with tab_demo:
    try:
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.markdown("### 👥 Analyse par genre")
        try:
            if "sexe" in df_filtered.columns and not df_filtered["sexe"].isna().all():
                fig, ax = plt.subplots()
                sns.boxplot(data=df_filtered.dropna(subset=["sexe", "note"]), x="sexe", y="note", palette="pastel")
                st.pyplot(fig)
                plt.close(fig)
            else:
                st.warning("⚠️ Données insuffisantes pour générer ce graphique")
        except Exception as e:
            st.error(f"❌ Erreur lors de la génération du graphique : {str(e)}")
        st.markdown("</div>", unsafe_allow_html=True)

        df_tmp = df_filtered.copy()
        try:
            if "age" in df_tmp.columns and not df_tmp["age"].isna().all():
                df_tmp["tranche_age"] = pd.cut(
                    df_tmp["age"], [17,20,23,26,30],
                    labels=["18-20","21-23","24-26","27+"]
                )
            else:
                df_tmp["tranche_age"] = None
                st.warning("⚠️ Colonne 'age' manquante ou vide")

            st.markdown("<div class='glass'>", unsafe_allow_html=True)
            st.markdown("### 📆 Performances par tranche d'âge")
            try:
                if "tranche_age" in df_tmp.columns and not df_tmp["tranche_age"].isna().all():
                    fig, ax = plt.subplots()
                    sns.barplot(data=df_tmp.dropna(subset=["tranche_age", "note"]), x="tranche_age", y="note", palette="magma")
                    st.pyplot(fig)
                    plt.close(fig)
                else:
                    st.warning("⚠️ Données d'âge insuffisantes pour générer ce graphique")
            except Exception as e:
                st.error(f"❌ Erreur lors de la génération du graphique : {str(e)}")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='glass'>", unsafe_allow_html=True)
            st.markdown("### 📊 Statistiques âge / genre")
            try:
                if "sexe" in df_tmp.columns and "tranche_age" in df_tmp.columns and not df_tmp["tranche_age"].isna().all():
                    stats = df_tmp.groupby(["sexe","tranche_age"])["note"].mean().unstack()
                    st.dataframe(stats)
                else:
                    st.warning("⚠️ Données insuffisantes pour générer ce tableau")
            except Exception as e:
                st.error(f"❌ Erreur lors de la génération du tableau : {str(e)}")
            st.markdown("</div>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"❌ Erreur lors du traitement des tranches d'âge : {str(e)}")
    except Exception as e:
        st.error(f"❌ Erreur dans la section démographie : {str(e)}")

# =================================
# 🏆 CLASSEMENTS
# =================================
with tab_rank:
    try:
        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.markdown("### 🏆 Classement général")
        try:
            top_n = st.slider("Top N étudiants", 5, 100, 10)
            cg = classement_general(df_filtered)
            st.dataframe(cg.head(top_n))
        except Exception as e:
            st.error(f"❌ Erreur lors de la génération du classement : {str(e)}")
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='glass'>", unsafe_allow_html=True)
        st.markdown("### 🏫 Classement par département")
        try:
            if "departement" in df_filtered.columns:
                st.dataframe(classement_par_departement(df_filtered))
            else:
                st.warning("⚠️ Colonne 'departement' manquante")
        except Exception as e:
            st.error(f"❌ Erreur lors de la génération du classement : {str(e)}")
        st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"❌ Erreur dans la section classements : {str(e)}")

# =================================
# 📄 EXPORTS & RAPPORT
# =================================
with tab_export:
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    import os

    def generate_pdf_from_df(df, filename="exports/rapport_dynamic.pdf"):
        try:
            os.makedirs("exports", exist_ok=True)
            doc = SimpleDocTemplate(filename)
            styles = getSampleStyleSheet()
            elements = []

            elements.append(Paragraph("Rapport d'analyse des notes", styles["Title"]))
            elements.append(Paragraph(
                f"Nombre de notes : {len(df)}", styles["Normal"]
            ))
            elements.append(Paragraph(
                f"Moyenne générale : {round(df['note'].mean(),2)}", styles["Normal"]
            ))
            elements.append(Paragraph(
                f"Taux de réussite : {round((df['note']>=10).mean()*100,2)}%", styles["Normal"]
            ))

            doc.build(elements)
            return True
        except Exception as e:
            st.error(f"❌ Erreur lors de la génération du PDF : {str(e)}")
            return False

    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.markdown("### 📄 Rapport académique final")
    
    # Rapport principal
    try:
        if os.path.exists("exports/rapport_analyse_notes_EPL.pdf"):
            with open("exports/rapport_analyse_notes_EPL.pdf", "rb") as f:
                st.download_button(
                    "📥 Télécharger le rapport PDF principal",
                    f.read(),
                    "rapport_EPL.pdf",
                    mime="application/pdf"
                )
        else:
            st.info("ℹ️ Le rapport principal n'est pas encore généré")
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement du rapport : {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)

    # Génération de rapport dynamique
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.markdown("### 📄 Générer un rapport PDF (dataset courant)")
    
    if st.button("📄 Générer le rapport PDF (dataset courant)"):
        if generate_pdf_from_df(df_filtered):
            st.success("✅ Rapport PDF généré avec succès")
            st.rerun()
    
    try:
        if os.path.exists("exports/rapport_dynamic.pdf"):
            with open("exports/rapport_dynamic.pdf", "rb") as f:
                st.download_button(
                    "⬇️ Télécharger le rapport généré",
                    f.read(),
                    "rapport_dynamic.pdf",
                    mime="application/pdf"
                )
    except Exception as e:
        st.info("ℹ️ Aucun rapport dynamique disponible")
    
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.markdown("### 📊 Exports de données")
    st.download_button(
        "⬇️ Données filtrées (CSV)",
        df_filtered.to_csv(index=False),
        "donnees_filtrees.csv",
        mime="text/csv"
    )
    st.markdown("</div>", unsafe_allow_html=True)

# =================================
# 📋 DONNÉES BRUTES
# =================================
with tab_data:
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.markdown("### 📋 Données académiques complètes")

    st.info(f"📌 Source des données : {data_source}")

    st.markdown("#### Aperçu des données")
    st.dataframe(df_filtered.head(100))

    st.markdown("#### Informations générales")
    c1, c2, c3 = st.columns(3)
    c1.metric("Lignes", df_filtered.shape[0])
    c2.metric("Colonnes", df_filtered.shape[1])
    c3.metric("Valeurs manquantes", int(df_filtered.isna().sum().sum()))

    st.markdown("#### Types des colonnes")
    st.dataframe(
        pd.DataFrame({
            "Colonne": df_filtered.columns,
            "Type": df_filtered.dtypes.astype(str)
        })
    )

    st.markdown("</div>", unsafe_allow_html=True)


with tab_comparison:
    st.markdown("<div class='glass'>", unsafe_allow_html=True)
    st.markdown("### 📊 Comparaison de datasets")
    
    file_2 = st.file_uploader(
        "📂 Charger un deuxième fichier pour comparaison",
        type=["csv", "xlsx"],
        key="file2"
    )
    
    if file_2:
        df2 = load_external_data(file_2)
        
        if df2 is not None and not df2.empty:
            # Vérifier que le dataset 2 a une colonne note
            if "note" not in df2.columns:
                st.error("❌ Le deuxième fichier doit contenir une colonne 'note'")
            else:
                try:
                    # Convertir la colonne note en numérique
                    df2["note"] = pd.to_numeric(df2["note"], errors="coerce")
                    
                    st.markdown("#### 📊 Comparaison des moyennes")
                    comp = pd.DataFrame({
                        "Dataset 1": [round(df_filtered["note"].mean(), 2)],
                        "Dataset 2": [round(df2["note"].mean(), 2)]
                    })
                    st.bar_chart(comp)

                    st.markdown("#### 🎯 Comparaison taux de réussite")
                    comp2 = pd.DataFrame({
                        "Dataset 1": [round((df_filtered["note"] >= 10).mean() * 100, 2)],
                        "Dataset 2": [round((df2["note"] >= 10).mean() * 100, 2)]
                    })
                    st.bar_chart(comp2)
                    
                    st.markdown("#### 📈 Statistiques comparatives")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Dataset 1 (actuel)**")
                        st.metric("Moyenne", round(df_filtered["note"].mean(), 2))
                        st.metric("Médiane", round(df_filtered["note"].median(), 2))
                        st.metric("Taux réussite", f"{round((df_filtered['note'] >= 10).mean()*100, 2)}%")
                        st.metric("Nombre de notes", len(df_filtered))
                    
                    with col2:
                        st.markdown("**Dataset 2 (comparaison)**")
                        st.metric("Moyenne", round(df2["note"].mean(), 2))
                        st.metric("Médiane", round(df2["note"].median(), 2))
                        st.metric("Taux réussite", f"{round((df2['note'] >= 10).mean()*100, 2)}%")
                        st.metric("Nombre de notes", len(df2))
                except Exception as e:
                    st.error(f"❌ Erreur lors de la comparaison : {str(e)}")
        else:
            st.warning("⚠️ Le deuxième fichier est vide ou invalide")
    
    st.markdown("</div>", unsafe_allow_html=True)
