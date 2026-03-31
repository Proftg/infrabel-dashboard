import os
import streamlit as st
import pandas as pd
import plotly.express as px

# ============================================================
# Configuration de la page
# ============================================================
st.set_page_config(
    page_title="Dashboard Infrabel",
    page_icon="🚆",
    layout="wide"
)

# Couleurs texte forcées (fix thème sombre Streamlit)
FONT = dict(color="#1e293b", family="Arial, sans-serif")
BG   = "#ffffff"

# ============================================================
# Chargement des données
# ============================================================
RAW_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")

BASE_API = (
    "https://opendata.infrabel.be/api/explore/v2.1/catalog/datasets"
    "/{}/exports/csv?lang=fr&timezone=Europe%2FBrussels&use_labels=true&delimiter=%3B"
)

DATASETS = {
    "ponctualite_gares.csv"  : "maandelijkse-stiptheid-per-stopplaats",
    "causes_retards.csv"     : "oorzaken-vertraging-per-maand",
    "ponctualite_moment.csv" : "nationale-stiptheid-per-moment-en-per-maand",
    "trains_supprimes.csv"   : "afgeschafte-treinen-per-maand-vanaf-2020",
}

def load_csv(filename, dataset_id):
    path = os.path.join(RAW_DIR, filename)
    if os.path.exists(path):
        return pd.read_csv(path, sep=";")
    df = pd.read_csv(BASE_API.format(dataset_id), sep=";")
    os.makedirs(RAW_DIR, exist_ok=True)
    df.to_csv(path, index=False, sep=";")
    return df

@st.cache_data
def load_data():
    # Ponctualité par gare (9 colonnes)
    df_gare = load_csv("ponctualite_gares.csv", DATASETS["ponctualite_gares.csv"])
    df_gare.columns = [
        "date", "nom_gare", "id_gare", "classification",
        "ponctualite_pct", "nb_trains", "nb_trains_ponctuels", "geo_point", "geo_shape"
    ]
    df_gare["date"] = pd.to_datetime(df_gare["date"], format="%Y-%m")
    df_gare["nb_trains_retard"] = df_gare["nb_trains"] - df_gare["nb_trains_ponctuels"]
    df_gare = df_gare.drop(columns=["geo_shape"])

    # Trains supprimés (7 colonnes)
    df_suppression = load_csv("trains_supprimes.csv", DATASETS["trains_supprimes.csv"])
    df_suppression.columns = [
        "date", "nb_trains_supprimes_total", "nb_trains_supprimes_partiel",
        "nb_trains_supprimes_entier", "nb_trains", "pct_trains_supprimes", "annee"
    ]
    df_suppression["date"] = pd.to_datetime(df_suppression["date"], format="%Y-%m")
    df_suppression = df_suppression.drop(columns=["annee"])

    # Causes des retards (12 colonnes)
    df_causes = load_csv("causes_retards.csv", DATASETS["causes_retards.csv"])
    df_causes.columns = [
        "annee", "date", "mois", "responsable",
        "nb_trains_en_retard", "nb_trains_total", "perte_ponctualite", "proportion_pct",
        "nb_trains_en_retard_ytd", "nb_trains_total_ytd", "perte_ponctualite_ytd", "proportion_ytd_pct"
    ]
    df_causes["date"] = pd.to_datetime(df_causes["date"], format="%Y-%m")
    df_causes = df_causes.drop(columns=["annee", "mois"])

    # Ponctualité par moment (7 colonnes)
    df_moment = load_csv("ponctualite_moment.csv", DATASETS["ponctualite_moment.csv"])
    df_moment.columns = [
        "date", "periode", "ponctualite_pct",
        "nb_trains", "nb_trains_ponctuels", "nb_minutes_retard", "annee"
    ]
    df_moment["date"] = pd.to_datetime(df_moment["date"], format="%Y-%m")
    df_moment = df_moment.drop(columns=["annee"])

    return df_gare, df_suppression, df_causes, df_moment

df_gare, df_suppression, df_causes, df_moment = load_data()

# ============================================================
# Sidebar — Filtres
# ============================================================
st.sidebar.title("🎛️ Filtres")

annees = sorted(df_gare["date"].dt.year.unique(), reverse=True)
annee_selectionnee = st.sidebar.selectbox("📅 Année", annees)

toutes_les_gares = sorted(df_gare["nom_gare"].dropna().unique())
gares_selectionnees = st.sidebar.multiselect(
    "🚉 Gares (optionnel)",
    options=toutes_les_gares,
    placeholder="Toutes les gares..."
)

df_annee = df_gare[df_gare["date"].dt.year == annee_selectionnee]
if gares_selectionnees:
    df_annee = df_annee[df_annee["nom_gare"].isin(gares_selectionnees)]

# ============================================================
# Titre
# ============================================================
st.title("🚆 Dashboard Qualité de Service — Réseau Infrabel")
st.caption(f"Année sélectionnée : **{annee_selectionnee}** | Source : Open Data Infrabel")
st.divider()

# ============================================================
# KPI Cards
# ============================================================
kpi_ponctualite   = df_annee["ponctualite_pct"].mean().round(2)
kpi_fiabilite     = (100 - df_suppression["pct_trains_supprimes"].mean()).round(2)
kpi_trains_retard = int(df_annee["nb_trains_retard"].sum())

col1, col2, col3 = st.columns(3)
col1.metric("⏱️ Ponctualité",      f"{kpi_ponctualite}%",
            delta=f"{round(kpi_ponctualite - 90, 2)}% vs objectif 90%")
col2.metric("✅ Fiabilité",        f"{kpi_fiabilite}%",
            delta=f"{round(kpi_fiabilite - 99, 2)}% vs objectif 99%")
col3.metric("🚆 Trains en retard", f"{kpi_trains_retard:,}")

st.divider()

# ============================================================
# Téléchargement des données filtrées
# ============================================================
with st.expander("📥 Télécharger les données filtrées"):
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button(
            "⬇️ Ponctualité par gare (.csv)",
            data=df_annee.to_csv(index=False).encode("utf-8"),
            file_name=f"ponctualite_gares_{annee_selectionnee}.csv",
            mime="text/csv"
        )
    with col_dl2:
        st.download_button(
            "⬇️ Causes des retards (.csv)",
            data=df_causes.to_csv(index=False).encode("utf-8"),
            file_name=f"causes_retards_{annee_selectionnee}.csv",
            mime="text/csv"
        )

st.divider()

# ============================================================
# Line Chart — Évolution historique complète (2016–2026)
# ============================================================
st.subheader("📈 Évolution de la Ponctualité")

df_tendance = df_gare.groupby("date")["ponctualite_pct"].mean().round(2).reset_index()
df_tendance["tendance_3m"] = df_tendance["ponctualite_pct"].rolling(3, center=True).mean().round(2)

fig_line = px.line(
    df_tendance, x="date", y=["ponctualite_pct", "tendance_3m"],
    labels={"value": "Ponctualité (%)", "date": "Mois", "variable": ""},
    color_discrete_map={"ponctualite_pct": "rgba(59,130,246,0.4)", "tendance_3m": "#3b82f6"},
    markers=True
)
fig_line.add_hline(y=90, line_dash="dash", line_color="red",
                   annotation_text="Objectif 90%",
                   annotation_font_color="red")
fig_line.update_layout(
    template="plotly_white", paper_bgcolor=BG, plot_bgcolor=BG, font=FONT,
    yaxis=dict(range=[80, 100], ticksuffix="%"),
    hovermode="x unified",
    legend=dict(orientation="h", y=-0.2)
)
st.plotly_chart(fig_line, use_container_width=True)

st.divider()

# ============================================================
# Bar Chart + Donut (côte à côte)
# ============================================================
col_bar, col_donut = st.columns(2)

with col_bar:
    st.subheader("🚉 Top 5 Gares — Trains en Retard")
    top5 = (
        df_annee.groupby("nom_gare")["nb_trains_retard"]
        .sum().sort_values(ascending=False).head(5).reset_index()
    )
    fig_bar = px.bar(
        top5, x="nb_trains_retard", y="nom_gare", orientation="h",
        labels={"nb_trains_retard": "Trains en retard", "nom_gare": ""},
        color="nb_trains_retard", color_continuous_scale="RdYlGn_r",
        text="nb_trains_retard"
    )
    fig_bar.update_traces(texttemplate="%{text:,}", textposition="outside",
                          textfont=dict(color="#1e293b"))
    fig_bar.update_layout(
        template="plotly_white", paper_bgcolor=BG, plot_bgcolor=BG, font=FONT,
        coloraxis_showscale=False,
        yaxis=dict(autorange="reversed"),
        xaxis=dict(range=[0, top5["nb_trains_retard"].max() * 1.25]),
        margin=dict(r=80, l=20, t=20, b=40),
        height=350
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_donut:
    st.subheader("🔍 Responsables des Retards")
    df_pie = df_causes.groupby("responsable")["perte_ponctualite"].sum().reset_index()
    fig_pie = px.pie(
        df_pie, values="perte_ponctualite", names="responsable",
        color_discrete_sequence=["#ef4444", "#3b82f6", "#f59e0b", "#10b981", "#8b5cf6"],
        hole=0.4
    )
    fig_pie.update_traces(textinfo="percent",
                          pull=[0.05] + [0] * (len(df_pie) - 1),
                          textfont=dict(color="#1e293b"))
    fig_pie.update_layout(
        template="plotly_white", paper_bgcolor=BG, font=FONT,
        showlegend=True,
        legend=dict(
            orientation="v", x=1.02, y=0.5,
            font=dict(color="#1e293b", size=12)
        ),
        margin=dict(l=20, r=120, t=20, b=20),
        height=350
    )
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# ============================================================
# Heatmap — Ponctualité par Période & Mois (tri chronologique)
# ============================================================
st.subheader("🌡️ Ponctualité par Période & Mois")

df_pivot = df_moment.pivot_table(
    index="periode", columns="date",
    values="ponctualite_pct", aggfunc="mean"
).round(1)
df_pivot.columns = pd.to_datetime(df_pivot.columns).strftime("%b %Y")

fig_heat = px.imshow(
    df_pivot,
    color_continuous_scale="RdYlGn",
    zmin=80, zmax=100,
    text_auto=True,
    aspect="auto",
    labels={"color": "% Ponctuel"}
)
fig_heat.update_layout(
    template="plotly_white", paper_bgcolor=BG, font=FONT,
    xaxis=dict(title="Mois",   tickangle=45),
    yaxis=dict(title="Période"),
    coloraxis_colorbar=dict(
        title=dict(text="% Ponctuel", font=FONT),
        tickfont=dict(color="#1e293b")
    )
)
st.plotly_chart(fig_heat, use_container_width=True)
