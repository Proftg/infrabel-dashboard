import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# Configuration de la page
# ============================================================
st.set_page_config(
    page_title="Dashboard Infrabel",
    page_icon="🚆",
    layout="wide"
)

# ============================================================
# Chargement des données
# ============================================================
@st.cache_data  # mise en cache → l'app ne recharge pas à chaque interaction
def load_data():
    BASE = (
        "https://opendata.infrabel.be/api/explore/v2.1/catalog/datasets"
        "/{}/exports/csv?lang=fr&timezone=Europe%2FBrussels&use_labels=true&delimiter=%3B"
    )

    # Ponctualité par gare
    df_gare = pd.read_csv(BASE.format("maandelijkse-stiptheid-per-stopplaats"), sep=";")
    df_gare.columns = [
        "date", "nom_gare_fr", "nom_gare_nl", "nom_gare_de", "id_gare",
        "classification_fr", "classification_nl", "classification_de",
        "ponctualite_pct", "nb_trains", "nb_trains_ponctuels", "geo_point", "geo_shape"
    ]
    df_gare["date"] = pd.to_datetime(df_gare["date"], format="%Y-%m")
    df_gare = df_gare.drop(columns=["nom_gare_nl", "nom_gare_de",
                                     "classification_nl", "classification_de", "geo_shape"])
    df_gare["nb_trains_retard"] = df_gare["nb_trains"] - df_gare["nb_trains_ponctuels"]

    # Trains supprimés
    df_suppression = pd.read_csv(BASE.format("afgeschafte-treinen-per-maand-vanaf-2020"), sep=";")
    df_suppression.columns = [
        "date", "nb_trains_supprimes_total", "nb_trains_supprimes_partiel",
        "nb_trains_supprimes_entier", "nb_trains", "pct_trains_supprimes", "annee"
    ]
    df_suppression["date"] = pd.to_datetime(df_suppression["date"], format="%Y-%m")
    df_suppression = df_suppression.drop(columns=["annee"])

    # Causes des retards
    df_causes = pd.read_csv(BASE.format("oorzaken-vertraging-per-maand"), sep=";")
    df_causes.columns = [
        "annee", "date", "mois", "responsable_nl", "responsable", "responsable_en",
        "nb_trains_en_retard", "nb_trains_total", "perte_ponctualite", "proportion_pct",
        "nb_trains_en_retard_ytd", "nb_trains_total_ytd", "perte_ponctualite_ytd", "proportion_ytd_pct"
    ]
    df_causes["date"] = pd.to_datetime(df_causes["date"], format="%Y-%m")
    df_causes = df_causes.drop(columns=["annee", "mois", "responsable_nl", "responsable_en"])

    # Ponctualité par moment
    df_moment = pd.read_csv(BASE.format("nationale-stiptheid-per-moment-en-per-maand"), sep=";")
    df_moment.columns = [
        "date", "periode_nl", "periode", "periode_en",
        "ponctualite_pct", "nb_trains", "nb_trains_ponctuels", "nb_minutes_retard", "annee"
    ]
    df_moment["date"] = pd.to_datetime(df_moment["date"], format="%Y-%m")
    df_moment = df_moment.drop(columns=["periode_nl", "periode_en", "annee"])

    return df_gare, df_suppression, df_causes, df_moment

df_gare, df_suppression, df_causes, df_moment = load_data()

# ============================================================
# Sidebar — Filtres
# ============================================================
st.sidebar.title("🎛️ Filtres")

# Filtre 1 — Année
annees = sorted(df_gare["date"].dt.year.unique(), reverse=True)
annee_selectionnee = st.sidebar.selectbox("📅 Année", annees)

# Filtre 2 — Gares
toutes_les_gares = sorted(df_gare["nom_gare_fr"].dropna().unique())
gares_selectionnees = st.sidebar.multiselect(
    "🚉 Gares (optionnel)",
    options=toutes_les_gares,
    placeholder="Toutes les gares..."
)

# Filtrer sur l'année
df_annee = df_gare[df_gare["date"].dt.year == annee_selectionnee]

# Si des gares sont sélectionnées → filtrer, sinon garder tout
if gares_selectionnees:
    df_annee = df_annee[df_annee["nom_gare_fr"].isin(gares_selectionnees)]

# ============================================================
# Titre
# ============================================================
st.title("🚆 Dashboard Qualité de Service — Réseau Infrabel")
st.caption(f"Année sélectionnée : **{annee_selectionnee}** | Source : Open Data Infrabel")
st.divider()

# ============================================================
# KPI Cards
# ============================================================
kpi_ponctualite  = df_annee["ponctualite_pct"].mean().round(2)
kpi_fiabilite    = (100 - df_suppression["pct_trains_supprimes"].mean()).round(2)
kpi_trains_retard = int(df_annee["nb_trains_retard"].sum())

col1, col2, col3 = st.columns(3)

col1.metric(
    label="⏱️ Ponctualité",
    value=f"{kpi_ponctualite}%",
    delta=f"{round(kpi_ponctualite - 90, 2)}% vs objectif 90%"
)
col2.metric(
    label="✅ Fiabilité",
    value=f"{kpi_fiabilite}%",
    delta=f"{round(kpi_fiabilite - 99, 2)}% vs objectif 99%"
)
col3.metric(
    label="🚆 Trains en retard",
    value=f"{kpi_trains_retard:,}",
)

st.divider()

# ============================================================
# Téléchargement des données filtrées
# ============================================================
with st.expander("📥 Télécharger les données filtrées"):
    col_dl1, col_dl2 = st.columns(2)

    with col_dl1:
        csv_gare = df_annee.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Ponctualité par gare (.csv)",
            data=csv_gare,
            file_name=f"ponctualite_gares_{annee_selectionnee}.csv",
            mime="text/csv"
        )
    with col_dl2:
        csv_causes = df_causes.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Causes des retards (.csv)",
            data=csv_causes,
            file_name=f"causes_retards_{annee_selectionnee}.csv",
            mime="text/csv"
        )

st.divider()

# ============================================================
# 5.2 — Line Chart : Tendance Ponctualité
# ============================================================
st.subheader("📈 Évolution de la Ponctualité")

df_tendance = df_annee.groupby("date")["ponctualite_pct"].mean().round(2).reset_index()
df_tendance["tendance_3m"] = df_tendance["ponctualite_pct"].rolling(3, center=True).mean().round(2)

fig_line = px.line(
    df_tendance, x="date", y=["ponctualite_pct", "tendance_3m"],
    labels={"value": "Ponctualité (%)", "date": "Mois", "variable": ""},
    color_discrete_map={"ponctualite_pct": "rgba(59,130,246,0.4)", "tendance_3m": "#3b82f6"},
    markers=True
)
fig_line.add_hline(y=90, line_dash="dash", line_color="red", annotation_text="Objectif 90%")
fig_line.update_layout(yaxis=dict(range=[80, 100], ticksuffix="%"),
                       paper_bgcolor="#f8fafc", plot_bgcolor="white",
                       hovermode="x unified", legend=dict(orientation="h", y=-0.2))
st.plotly_chart(fig_line, use_container_width=True)

st.divider()

# ============================================================
# 5.3 + 5.4 — Bar Chart & Donut (côte à côte)
# ============================================================
col_bar, col_donut = st.columns(2)

with col_bar:
    st.subheader("🚉 Top 5 Gares — Trains en Retard")
    top5 = (
        df_annee.assign(nb_trains_retard=df_annee["nb_trains"] - df_annee["nb_trains_ponctuels"])
        .groupby("nom_gare_fr")["nb_trains_retard"].sum()
        .sort_values(ascending=False).head(5).reset_index()
    )
    fig_bar = px.bar(
        top5, x="nb_trains_retard", y="nom_gare_fr", orientation="h",
        labels={"nb_trains_retard": "Trains en retard", "nom_gare_fr": ""},
        color="nb_trains_retard", color_continuous_scale="RdYlGn_r",
        text="nb_trains_retard"
    )
    fig_bar.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig_bar.update_layout(paper_bgcolor="#f8fafc", plot_bgcolor="white",
                          coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig_bar, use_container_width=True)

with col_donut:
    st.subheader("🔍 Responsables des Retards")
    fig_pie = px.pie(
        df_causes.groupby("responsable")["perte_ponctualite"].sum().reset_index(),
        values="perte_ponctualite", names="responsable",
        color_discrete_sequence=["#ef4444", "#3b82f6", "#f59e0b"],
        hole=0.4
    )
    fig_pie.update_traces(textinfo="percent+label", pull=[0.05, 0, 0])
    fig_pie.update_layout(paper_bgcolor="#f8fafc", showlegend=False)
    st.plotly_chart(fig_pie, use_container_width=True)

st.divider()

# ============================================================
# 5.5 — Heatmap : Ponctualité par Mois × Période
# ============================================================
st.subheader("🌡️ Ponctualité par Période & Mois")

df_heat = df_moment.copy()
df_heat["mois"] = df_heat["date"].dt.strftime("%b %Y")
pivot = df_heat.pivot_table(
    index="periode", columns="mois",
    values="ponctualite_pct", aggfunc="mean"
).round(1)

fig_heat = px.imshow(
    pivot,
    color_continuous_scale="RdYlGn",
    zmin=80, zmax=100,
    text_auto=True,
    aspect="auto"
)
fig_heat.update_layout(
    paper_bgcolor="#f8fafc",
    coloraxis_colorbar=dict(title="%", ticksuffix="%"),
    xaxis_title="", yaxis_title=""
)
st.plotly_chart(fig_heat, use_container_width=True)
