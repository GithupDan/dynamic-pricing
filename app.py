
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from PIL import Image

st.set_page_config(page_title="Merchify – Dynamic Pricing", layout="wide")

# Logo und Farben
st.markdown("""<style>
    .block-container {
        padding-top: 2rem;
    }
    .stApp {
        background-color: #f9f9f9;
        color: #111;
    }
    .css-1d391kg {
        background-color: white;
    }
    .st-emotion-cache-1avcm0n {
        background-color: white;
    }
</style>""", unsafe_allow_html=True)

# Logo anzeigen
col1, col2 = st.columns([0.1, 0.9])
with col1:
    try:
        logo = Image.open("merchify_logo.png")
        st.image(logo, width=70)
    except:
        st.write("🧠")
with col2:
    st.markdown("## **Merchify – Dynamic Pricing Intelligence**")
    st.caption("**Smartere Entscheidungen. Schnellere Reduzierungen. Mehr Deckungsbeitrag.**")

# Tabs
tabs = st.tabs(["🎯 Zielreichweiten", "📦 Artikelliste & Regeln", "📊 Dashboard"])

# 1. Zielreichweiten
with tabs[0]:
    st.subheader("📅 Zielreichweiten pro Warengruppe + Monat (Beispiel FS Saison)")
    ziel_df = pd.DataFrame({
        "Monat": ["Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep"],
        "KW-T-Shirts/Polos": ["X", "X", 24, 20, 16, 12, 8, 4],
        "Hemden lang": ["X", "X", 12, 10, 8, 6, 4, 4],
        "Jeans/Hosen": ["X", "X", 12, 10, 8, 6, 4, 4]
    })
    st.dataframe(ziel_df)

# 2. Artikelliste + Regeln
with tabs[1]:
    st.subheader("📥 Lade deine POS-Daten hoch (CSV mit Kalenderwochen)")
    uploaded_file = st.file_uploader("Drag and drop file here", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file, encoding='utf-8')
        st.dataframe(df.head())

        st.markdown("### 🧮 Reduktionsstufen laut Notiz:")

        st.markdown("""
        - RW > Ziel + 10 → **-30%**
        - RW > Ziel + 4–8 → **-20%**
        - RW > Ziel + 1–4 → **-10%**
        - RW ≤ Ziel → **0%**
        """)

        st.markdown("### 🛠️ Optional: Passe Reduktionsstufen an")
        col1, col2, col3, col4 = st.columns(4)
        step_30 = col1.number_input("RW > Ziel + 10", value=-30)
        step_20 = col2.number_input("RW > Ziel + 4–8", value=-20)
        step_10 = col3.number_input("RW > Ziel + 1–4", value=-10)
        step_0 = col4.number_input("RW ≤ Ziel", value=0)

        st.markdown("### 💡 Beispiel-Reduktionslogik (vereinfacht)")
        def vorschlag(row):
            rw = row['Reichweite (Wochen)']
            ziel = 8
            if rw > ziel + 10:
                return f"{step_30}%"
            elif rw > ziel + 4:
                return f"{step_20}%"
            elif rw > ziel:
                return f"{step_10}%"
            else:
                return f"{step_0}%"

        if 'Reichweite (Wochen)' in df.columns:
            df["Reduktionsvorschlag"] = df.apply(vorschlag, axis=1)
            st.dataframe(df[['Artikelnummer', 'Reichweite (Wochen)', 'Reduktionsvorschlag']])
        else:
            st.warning("Spalte 'Reichweite (Wochen)' fehlt in der Datei.")

# 3. Dashboard
with tabs[2]:
    st.subheader("📊 Dashboard")
    if uploaded_file and 'Reduktionsvorschlag' in df.columns:
        col1, col2, col3 = st.columns(3)
        col1.metric("🛍️ Artikel", len(df))
        col2.metric("📦 Gesamtbestand", df['Lagerbestand'].sum())
        col3.metric("💰 Ø Deckungsbeitrag", round((df['VK_UVP'] - df['EK']).mean(), 2))

        chart_data = df['Reduktionsvorschlag'].value_counts().reset_index()
        chart_data.columns = ['Vorschlag', 'Anzahl']
        fig = px.bar(chart_data, x='Vorschlag', y='Anzahl', title="Häufigkeit der Reduktionsvorschläge", text_auto=True)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Bitte lade zuerst eine Datei unter 'Artikelliste & Regeln' hoch.")
