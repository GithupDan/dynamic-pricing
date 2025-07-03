
import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image

# ==== CONFIG ====
st.set_page_config(
    page_title="Merchify – Dynamic Pricing Intelligence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="auto"
)

# ==== STYLE ====
custom_css = '''
<style>
    body, .stApp {
        background-color: #f9f9f9;
        color: #1e1e1e;
    }
    .css-18e3th9 {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 2rem;
    }
    .stButton>button {
        background-color: #1976d2;
        color: white;
        border-radius: 5px;
    }
</style>
'''
st.markdown(custom_css, unsafe_allow_html=True)

# ==== LOGO ====
try:
    logo = Image.open("merchify_logo.png")
    st.image(logo, width=280)
except FileNotFoundError:
    st.warning("Logo konnte nicht geladen werden. Stelle sicher, dass 'merchify_logo.png' im Hauptverzeichnis liegt.")

# ==== TITLE ====
st.title("🧠 Merchify – Dynamic Pricing Intelligence")
st.markdown("**Smartere Entscheidungen. Schnellere Reduzierungen. Mehr Deckungsbeitrag.**")

# ==== FILE UPLOAD ====
uploaded_file = st.file_uploader("Lade deine POS-Daten hoch (CSV mit Kalenderwochen)", type=["csv"])
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(uploaded_file, encoding="latin1")

    st.markdown("### 📊 Eingeladene Daten")
    st.dataframe(df.head())

    # === KRITERIEN FÜR REDUKTIONSVORSCHLÄGE ===
    st.markdown("#### ⚙️ Kriterien für Reduktionsvorschläge (anpassbar)")
    mindest_wochen = st.slider("Minimale Reichweite (in Wochen) für Reduktion", 1, 20, 6)
    max_preis = st.slider("Maximaler Preis für Reduktion", 5.0, 150.0, 60.0)

    # === REDUKTIONSLOGIK ===
    if "Preis" in df.columns and "Reichweite (Wochen)" in df.columns:
        df["Reduktionsvorschlag"] = df.apply(
            lambda row: "Reduzieren" if row["Reichweite (Wochen)"] > mindest_wochen and row["Preis"] > max_preis else "Beibehalten",
            axis=1
        )
        st.markdown("### 🧾 Reduktionsvorschläge")
        st.dataframe(df[["Artikelnummer", "Reichweite (Wochen)", "Preis", "Reduktionsvorschlag"]].head(20))

        # === DASHBOARD ===
        st.markdown("### 📈 Dashboard")
        if "Reduktionsvorschlag" in df.columns and not df["Reduktionsvorschlag"].isnull().all():
            vorschlags_df = df["Reduktionsvorschlag"].value_counts().reset_index()
            vorschlags_df.columns = ["Vorschlag", "Anzahl"]
            fig = px.bar(
                vorschlags_df,
                x="Vorschlag",
                y="Anzahl",
                title="Häufigkeit der Reduktionsvorschläge",
                labels={"Anzahl": "Vorkommen"},
                color="Vorschlag"
            )
            st.plotly_chart(fig)
        else:
            st.warning("Keine Reduktionsvorschläge vorhanden oder Spalte fehlt.")
    else:
        st.error("Die Spalten 'Preis' und 'Reichweite (Wochen)' fehlen in deiner Datei.")
else:
    st.info("Bitte lade eine Datei hoch, um zu starten.")
