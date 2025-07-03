
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Merchify – Dynamic Pricing Intelligence", layout="wide")

# --- Styling ---
st.markdown("""
    <style>
        body, .stApp {
            color: white;
            background-color: #111;
        }
        .css-18e3th9 {
            background-color: #111;
        }
        .stTextInput > div > input {
            background-color: #222;
            color: white;
        }
        .stSelectbox > div > div {
            background-color: #222;
            color: white;
        }
        .stNumberInput > div > input {
            background-color: #222;
            color: white;
        }
    </style>
""", unsafe_allow_html=True)

# --- Title Section ---
st.image("merchify_logo.png", width=450)
st.title("Merchify – Dynamic Pricing Intelligence")
st.markdown("**Smartere Entscheidungen. Schnellere Reduzierungen. Mehr Deckungsbeitrag.**")

# --- Tabs ---
tab1, tab2, tab3 = st.tabs([
    "🎯 Zielreichweiten", "📦 Artikelliste & Regeln", "📊 Dashboard"
])

# --- Load Data ---
uploaded_file = st.sidebar.file_uploader("📁 CSV-Datei hochladen", type=["csv"])
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df.columns = df.columns.str.strip()  # remove whitespace
    if "RW" not in df.columns:
        if "Lagerbestand" in df.columns and "Verkäufe" in df.columns:
            df["RW"] = (df["Lagerbestand"] / (df["Verkäufe"] + 0.01)).round(1)

    with tab1:
        st.subheader("📊 Zielreichweiten pro Warengruppe + Monat")
        st.markdown("Hier kannst du die Zielreichweiten je Warengruppe und Monat anpassen:")
        ziel_df = pd.DataFrame(index=["Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep"],
                               columns=["KW-T-Shirts/Polos", "Hemden lang", "Jeans/Hosen"])
        for col in ziel_df.columns:
            for row in ziel_df.index:
                ziel_df.loc[row, col] = st.number_input(f"{col} – {row}", min_value=0, value=8)
        st.dataframe(ziel_df)

    with tab2:
        st.subheader("🛠️ Reduktionsstufen anpassen")
        col1, col2, col3, col4 = st.columns(4)
        red1 = col1.number_input("> Ziel +10", value=-30)
        red2 = col2.number_input("RW > Ziel +4–8", value=-20)
        red3 = col3.number_input("RW > Ziel +1–4", value=-10)
        red4 = col4.number_input("RW ≤ Ziel", value=0)

        st.subheader("📦 Artikelliste mit Vorschlägen")
        if "RW" in df.columns:
            df["Reduktion (%)"] = df["RW"].apply(lambda x: red1 if x > 10 else red2 if x > 4 else red3 if x > 1 else red4)
        st.dataframe(df)

    with tab3:
        st.subheader("📊 Dashboard")
        try:
            col1, col2 = st.columns(2)
            col1.metric("🔐 Artikel", df["SKU"].nunique())
            col2.metric("⏳ Ø RW", round(df["RW"].mean(), 1))
            fig = px.histogram(df, x="RW", nbins=20, title="Verteilung der Reichweiten")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Fehler im Dashboard: {e}")
else:
    st.warning("Bitte lade eine CSV-Datei hoch.")
