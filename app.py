
import streamlit as st
from PIL import Image
import pandas as pd
import numpy as np
import datetime

# Logo anzeigen
logo = Image.open("merchify_logo.png")
st.image(logo, width=280)

# Titel und Untertitel
st.title("🧠 Merchify – Dynamic Pricing Intelligence")
st.markdown("**Smartere Entscheidungen. Schnellere Reduzierungen. Mehr Deckungsbeitrag.**")

# Datei-Upload
uploaded_file = st.file_uploader("Lade deine POS-Daten hoch (CSV mit Kalenderwochen)", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.subheader("📊 Eingeladene Daten")
    st.dataframe(df.head())

    # Rechenlogik: Beispiel für Reichweite
    if 'Lagerbestand' in df.columns and 'Verkäufe' in df.columns:
        df['Reichweite (Wochen)'] = df['Lagerbestand'] / (df['Verkäufe'].replace(0, np.nan) + 1e-5)
        st.subheader("📈 Berechnete Reichweiten")
        st.dataframe(df[['SKU', 'Reichweite (Wochen)']])

        # Beispielhafte Reduktionslogik
        def berechne_reduktion(rw):
            if rw > 12:
                return "-50%"
            elif rw > 8:
                return "-30%"
            elif rw > 4:
                return "-20%"
            else:
                return "Keine"

        df['Reduktionsvorschlag'] = df['Reichweite (Wochen)'].apply(berechne_reduktion)
        st.subheader("🛒 Reduktionsvorschläge")
        st.dataframe(df[['SKU', 'Reichweite (Wochen)', 'Reduktionsvorschlag']])
    else:
        st.warning("Bitte sicherstellen, dass die Spalten 'Lagerbestand' und 'Verkäufe' vorhanden sind.")
