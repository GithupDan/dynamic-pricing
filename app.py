
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from PIL import Image

st.set_page_config(page_title="Merchify – Dynamic Pricing", layout="wide")

# Custom Styling
st.markdown("""<style>
    .block-container { padding-top: 2rem; }
    .stApp { background-color: #f8f9fa; color: #111; }
</style>""", unsafe_allow_html=True)

# Logo
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

# Initialisierung
ziel_rw_dict = {}

# Tab 1: Zielreichweiten
with tabs[0]:
    st.subheader("🎯 Zielreichweiten pro Warengruppe + Monat")
    warengruppen = ["T-Shirts", "Hemden lang", "Jeans/Hosen"]
    monate = ["Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep"]

    data = {}
    for wg in warengruppen:
        data[wg] = []
        for monat in monate:
            key = f"{wg}_{monat}"
            val = st.number_input(f"{wg} – {monat}", min_value=0, max_value=30, value=8, step=1, key=key)
            data[wg].append(val)
            ziel_rw_dict[key] = val

    ziel_df = pd.DataFrame(data, index=monate)
    st.dataframe(ziel_df)

# Tab 2: Artikelliste & Regeln
with tabs[1]:
    st.subheader("📥 Lade deine POS-Daten hoch")
    uploaded_file = st.file_uploader("CSV-Datei mit Verkaufsdaten", type=["csv"])

    if uploaded_file:
        df = pd.read_csv(uploaded_file, encoding="utf-8")
        if "RW" in df.columns:
            df.rename(columns={"RW": "Reichweite (Wochen)"}, inplace=True)

        # Reduktionslogik Eingabe
        st.markdown("### 🛠️ Reduktionsstufen anpassen")
        col1, col2, col3, col4 = st.columns(4)
        step_30 = col1.number_input("RW > Ziel +10", value=-30)
        step_20 = col2.number_input("RW > Ziel +4–8", value=-20)
        step_10 = col3.number_input("RW > Ziel +1–4", value=-10)
        step_0 = col4.number_input("RW ≤ Ziel", value=0)

        ziel_standard = 8

        def vorschlag(row):
            rw = row.get("Reichweite (Wochen)", 0)
            if rw > ziel_standard + 10:
                return f"{step_30}%"
            elif rw > ziel_standard + 4:
                return f"{step_20}%"
            elif rw > ziel_standard:
                return f"{step_10}%"
            else:
                return f"{step_0}%"

        df["Reduktionsvorschlag"] = df.apply(vorschlag, axis=1)

        st.markdown("### 📦 Artikelliste mit Vorschlägen")
        st.dataframe(df, use_container_width=True)

# Tab 3: Dashboard
with tabs[2]:
    st.subheader("📊 Dashboard")
    if uploaded_file:
        if "Reichweite (Wochen)" not in df.columns:
            st.error("Spalte 'Reichweite (Wochen)' fehlt.")
        else:
            col1, col2, col3 = st.columns(3)
            col1.metric("🛍️ Artikel", df['Artikelnummer'].nunique())
            col2.metric("📦 Lagerbestand", int(df["Lagerbestand"].sum()))
            col3.metric("💰 Ø DB", round((df["VK_UVP"] - df["EK"]).mean(), 2))

            chart_data = df["Reduktionsvorschlag"].value_counts().reset_index()
            chart_data.columns = ["Vorschlag", "Anzahl"]
            fig = px.bar(chart_data, x="Vorschlag", y="Anzahl", title="Reduktionsvorschläge", text_auto=True)
            st.plotly_chart(fig, use_container_width=True)
