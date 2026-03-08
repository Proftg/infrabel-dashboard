# 🚆 Dashboard Qualité de Service — SNCB / Infrabel

Analyse de la ponctualité et de la fiabilité du réseau ferroviaire belge à partir des données Open Data Infrabel.

## 🎯 Objectif
Construire un dashboard interactif permettant à un manager de visualiser les KPIs de ponctualité du réseau, identifier les gares problématiques et comprendre les causes des retards.

## 📊 Sources de données
5 datasets Open Data Infrabel :
- **Ponctualité par gare** (27 343 lignes) — dimension géographique
- **Causes des retards** (425 lignes) — dimension causale
- **Ponctualité par moment** (484 lignes) — dimension temporelle (matin/soir/WE)
- **Trains supprimés** (73 lignes) — KPI Reliability
- **KPIs Contrat de Performance** (177 lignes) — objectifs officiels 2023-2032

## 🛠️ Stack Technique
- **Python** — Pandas, Plotly
- **Jupyter Notebook** — Exploration & analyse
- **Streamlit** — Dashboard interactif
- **PowerBI** — Version BI entreprise

## 📁 Structure du projet
```
dashboard/
├── dashboard.ipynb     ← ETL + EDA + KPIs + Visualisation
├── app.py              ← Dashboard Streamlit (à venir)
└── data/
    ├── raw/            ← CSV bruts (non versionnés)
    └── clean/          ← CSV nettoyés (non versionnés)
```

## 🚀 Lancer le notebook
```bash
git clone https://github.com/Proftg/infrabel-dashboard
cd infrabel-dashboard
pip install pandas plotly streamlit jupyter
jupyter notebook dashboard.ipynb
```

## 👤 Auteur
**Tahar Guenfoud**  
[GitHub](https://github.com/Proftg)
