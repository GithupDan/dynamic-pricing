
import streamlit as st
from PIL import Image
import pandas as pd
import numpy as np
import datetime
import plotly.express as px

# Logo anzeigen
logo = Image.open("merchify_logo.png")
st.image(logo, width=280)

# Titel und Untertitel
st.title("🧠 Merchify – Dynamic Pricing Intelligence")
st.markdown("**Smartere Entscheidungen. Schnellere Reduzierungen. Mehr Deckungsbeitrag.**")

# Datei-Upload
uploaded_file = st.file_uploader("Lade deine POS-Daten hoch (CSV mit Kalenderwochen)", type=["csv"])

# Eingabefelder für Reduktionslogik
st.sidebar.header("🔧 Reduktionslogik anpassen")
grenze1 = st.sidebar.number_input("Grenzwert RW für -50%", min_value=0.0, value=12.0)
grenze2 = st.sidebar.number_input("Grenzwert RW für -30%", min_value=0.0, value=8.0)
grenze3 = st.sidebar.number_input("Grenzwert RW für -20%", min_value=0.0, value=4.0)

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    if 'Lagerbestand' in df.columns and 'Verkäufe' in df.columns:
        df['Reichweite (Wochen)'] = df['Lagerbestand'] / (df['Verkäufe'].replace(0, np.nan) + 1e-5)

        def berechne_reduktion(rw):
            if rw > grenze1:
                return "-50%"
            elif rw > grenze2:
                return "-30%"
            elif rw > grenze3:
                return "-20%"
            else:
                return "Keine"

        df['Reduktionsvorschlag'] = df['Reichweite (Wochen)'].apply(berechne_reduktion)

        st.subheader("📈 Berechnete Reichweiten")
        st.dataframe(df[['SKU', 'Reichweite (Wochen)', 'Reduktionsvorschlag']])

        st.subheader("📊 Dashboard")
        col1, col2, col3 = st.columns(3)
        col1.metric("⛓ Anzahl Artikel", df['SKU'].nunique())
        col2.metric("🏬 POS", df['POS_ID'].nunique())
        col3.metric("📦 Schnitt RW", round(df['Reichweite (Wochen)'].mean(), 2))

        # Plotly Charts
        st.plotly_chart(px.histogram(df, x='Reichweite (Wochen)', nbins=30, title='Verteilung der Reichweite (Wochen)'))
        st.plotly_chart(px.bar(df['Reduktionsvorschlag'].value_counts().reset_index(),
                               x='index', y='Reduktionsvorschlag',
                               labels={'index': 'Vorschlag'},
                               title='Häufigkeit der Reduktionsvorschläge'))

        # Durchschnittlicher Deckungsbeitrag pro KW
        if 'KW' in df.columns and 'Deckungsbeitrag' in df.columns:
            kpi_df = df.groupby('KW')['Deckungsbeitrag'].mean().reset_index()
            st.plotly_chart(px.line(kpi_df, x='KW', y='Deckungsbeitrag',
                                    title='Ø Deckungsbeitrag pro Kalenderwoche'))

        # KPI nach Warengruppe
        if 'Warengruppe' in df.columns:
            gruppe_df = df.groupby('Warengruppe')['Deckungsbeitrag'].mean().reset_index()
            st.plotly_chart(px.bar(gruppe_df, x='Warengruppe', y='Deckungsbeitrag',
                                   title='Ø Deckungsbeitrag je Warengruppe'))

    else:
        st.warning("Bitte sicherstellen, dass die Spalten 'Lagerbestand' und 'Verkäufe' vorhanden sind.")
