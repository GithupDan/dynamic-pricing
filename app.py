
import streamlit as st
import pandas as pd
import calendar
import plotly.express as px

st.set_page_config(layout="wide")

st.markdown("""
    <style>
        .main {
            background-color: #f8f9fa;
            color: #000;
        }
        section[tabindex] h1, section[tabindex] h2, section[tabindex] h3 {
            color: #000;
        }
        .css-1d391kg {color: #000 !important;}
    </style>
""", unsafe_allow_html=True)

st.title("🧠 Merchify – Dynamic Pricing Intelligence")
st.caption("**Smartere Entscheidungen. Schnellere Reduzierungen. Mehr Deckungsbeitrag.**")

tab1, tab2, tab3 = st.tabs(["🎯 Zielreichweiten", "📦 Artikelliste & Regeln", "📊 Dashboard"])

with tab1:
    st.header("📅 Zielreichweiten pro Warengruppe + Monat")
    months = list(calendar.month_name)[2:10]
    warengruppen = ["T-Shirts/Polos", "Hemden lang", "Jeans/Hosen"]
    zielwerte = {}

    cols = st.columns(len(warengruppen))
    for i, wg in enumerate(warengruppen):
        with cols[i]:
            st.markdown(f"**{wg}**")
            for m in months:
                key = f"{wg}_{m}"
                zielwerte[key] = st.number_input(f"{m}", min_value=0, max_value=52, value=8, key=key)

with tab2:
    st.header("🛠️ Reduktionsstufen anpassen")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        r30 = st.number_input("> Ziel +10", value=-30)
    with col2:
        r20 = st.number_input("RW > Ziel +4–8", value=-20)
    with col3:
        r10 = st.number_input("RW > Ziel +1–4", value=-10)
    with col4:
        r00 = st.number_input("RW ≤ Ziel", value=0)

    uploaded_file = st.file_uploader("📤 Lade deine Datei hoch", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        if "Reichweite (Wochen)" not in df.columns:
            df["Reichweite (Wochen)"] = (df["Lagerbestand"] / (df["Absatz"] + 0.01)).round(1)
        df["Reduktionsvorschlag"] = df["Reichweite (Wochen)"] - 0
        df["Reduktionsvorschlag"] = df["Reichweite (Wochen)"].apply(lambda x: r30 if x > 10 else (r20 if x > 8 else (r10 if x > 4 else r00)))
        st.subheader("📦 Artikelliste mit Vorschlägen")
        st.dataframe(df, use_container_width=True)

with tab3:
    st.header("📊 Dashboard")
    if uploaded_file is not None:
        try:
            col1, col2, col3 = st.columns(3)
            col1.metric("🔐 Artikel", df["Artikelnummer"].nunique())
            col2.metric("🛍️ Warengruppen", df["Warengruppe"].nunique())
            col3.metric("📆 Kalenderwochen", df["KW"].nunique())

            st.subheader("📉 Reduktionsvorschläge Verteilung")
            fig = px.bar(df["Reduktionsvorschlag"].value_counts().reset_index(),
                         x="index", y="Reduktionsvorschlag",
                         labels={"index": "Reduktion", "Reduktionsvorschlag": "Anzahl"},
                         title="Verteilung der Reduktionsvorschläge")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Fehler im Dashboard: {e}")
