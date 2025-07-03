
import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

# App-Konfiguration
st.set_page_config(page_title="Merchify – Dynamic Pricing", layout="wide")

# Logo und Titel
logo_path = "merchify_logo.png"
if Path(logo_path).exists():
    st.image(logo_path, width=200)

st.markdown("<h1 style='color: white;'>Merchify – Dynamic Pricing Dashboard</h1>", unsafe_allow_html=True)
st.markdown("---")

# Datei-Upload
uploaded_file = st.file_uploader("📤 Lade deine CSV-Datei hoch:", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()

    # Berechnung durchschnittlicher Absatz & Reichweite der letzten 4 Wochen
    absatz_cols = ['Absatz 1', 'Absatz 2', 'Absatz 3', 'Absatz 4']
    if all(col in df.columns for col in absatz_cols):
        df["Ø Absatz 4W"] = df[absatz_cols].mean(axis=1)
        df["Ø RW (Wochen)"] = (df["Lagerbestand"] / (df["Ø Absatz 4W"] + 0.01)).round(1)

    # Tabs für Navigation
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Artikelliste", "📈 Dashboard", "📊 Forecast", "🎯 Zielreichweiten"])

    with tab1:
        st.subheader("📋 Artikelliste")
        st.dataframe(df[['Artikelnr', 'Warengruppe', 'Preis', 'Lagerbestand', 'Absatz 1', 'Absatz 2', 'Absatz 3', 'Absatz 4', 'Ø Absatz 4W', 'Ø RW (Wochen)', 'Zielreichweite']], use_container_width=True)

    with tab2:
        st.subheader("📈 Dashboard")
        kpis = df.groupby('Warengruppe').agg({'Verkäufe': 'sum', 'Absatz_Prognose': 'sum'}).reset_index()
        fig = px.bar(kpis, x='Warengruppe', y=['Verkäufe', 'Absatz_Prognose'], barmode='group', title="Verkäufe vs Prognose je Warengruppe")
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("📊 Forecast Vorschau")
        forecast = df.groupby(['Warengruppe', 'Saison']).agg({'Absatz_Prognose': 'sum'}).reset_index()
        st.dataframe(forecast, use_container_width=True)

    with tab4:
        st.subheader("🎯 Zielreichweiten")
        seasons = df['Saison'].unique()
        warengruppen = df['Warengruppe'].unique()

        ziel_rw_input = {}
        for saison in seasons:
            st.markdown(f"**{saison}**")
            cols = st.columns(len(warengruppen))
            for i, wg in enumerate(warengruppen):
                key = f"{saison}_{wg}"
                ziel_rw_input[key] = cols[i].number_input(f"{wg}", min_value=1, max_value=30, value=8, key=key)

        if st.button("💾 Speichern & Anwenden"):
            def get_zielrw(row):
                return ziel_rw_input.get(f"{row['Saison']}_{row['Warengruppe']}", 8)
            df['Zielreichweite'] = df.apply(get_zielrw, axis=1)
            df["Reduktion (%)"] = df.apply(lambda row: 20 if row["Ø RW (Wochen)"] > row["Zielreichweite"] else 0, axis=1)
            st.success("Zielreichweiten angewendet!")

