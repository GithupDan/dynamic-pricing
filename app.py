
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from pathlib import Path
from PIL import Image

# === Seitenkonfiguration ===
st.set_page_config(
    page_title="Merchify – Dynamic Pricing",
    layout="wide",
)

# === Logo anzeigen ===
logo_path = "images/merchify_logo.png"
if Path(logo_path).exists():
    logo = Image.open(logo_path)
    st.image(logo, width=300)

# === Titel ===
st.markdown("<h1 style='color:white;'>Merchify – Dynamic Pricing Dashboard</h1>", unsafe_allow_html=True)

# === Datei-Upload ===
uploaded_file = st.file_uploader("📂 Lade deine CSV-Datei hoch", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # === Tabs ===
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Artikelliste", "🎯 Zielreichweiten", "📊 Dashboard", "📈 Forecast"])

    with tab1:
        st.subheader("📋 Artikelliste")
        st.dataframe(df)

    with tab2:
        st.subheader("🎯 Zielreichweiten definieren")
        saisons = df["Saison"].unique()
        warengruppen = df["Warengruppe"].unique()
        ziel_rw = {}

        for saison in saisons:
            st.markdown(f"**Saison: {saison}**")
            cols = st.columns(len(warengruppen))
            for i, wg in enumerate(warengruppen):
                key = f"{saison}_{wg}"
                ziel_rw[key] = cols[i].number_input(f"{wg}", value=8, step=1, key=key)

    with tab3:
        st.subheader("📊 Dashboard")
        col1, col2 = st.columns(2)
        with col1:
            fig1 = px.bar(df.groupby("Warengruppe")["Absatz"].sum().reset_index(),
                          x="Warengruppe", y="Absatz", title="Absatz nach Warengruppe")
            st.plotly_chart(fig1, use_container_width=True)
        with col2:
            fig2 = px.line(df.groupby("KW")["Absatz"].sum().reset_index(),
                           x="KW", y="Absatz", title="Absatzverlauf über die Kalenderwochen")
            st.plotly_chart(fig2, use_container_width=True)

    with tab4:
        st.subheader("📈 Absatz-Forecast")
        if "Absatz_Prognose" in df.columns:
            forecast_df = df.groupby(["Saison", "Warengruppe"])[
                "Absatz_Prognose"].sum().reset_index().sort_values(by="Saison")
            st.dataframe(forecast_df)
        else:
            st.warning("⚠️ Keine Spalte 'Absatz_Prognose' gefunden.")
