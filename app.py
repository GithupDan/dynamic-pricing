
import streamlit as st
import pandas as pd
import plotly.express as px
from PIL import Image
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import xgboost as xgb

st.set_page_config(page_title="Merchify - Dynamic Pricing", layout="wide")

# Logo & Header
col1, col2 = st.columns([1, 6])
with col1:
    st.image("merchify_logo.png", width=120)
with col2:
    st.markdown("### **Merchify – Dynamic Pricing**")
    st.caption("📈 Mit KI-gestützter Reduktions- & Preislogik")

# Upload
uploaded_file = st.file_uploader("📤 Lade deine Verkaufsdaten (CSV) hoch", type="csv")
if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # KW → Monat Mapping
    kw_to_month = {
        **dict.fromkeys(range(1, 5), "Januar"),
        **dict.fromkeys(range(5, 9), "Februar"),
        **dict.fromkeys(range(9, 14), "März"),
        **dict.fromkeys(range(14, 18), "April"),
        **dict.fromkeys(range(18, 23), "Mai"),
        **dict.fromkeys(range(23, 27), "Juni"),
        **dict.fromkeys(range(27, 32), "Juli"),
        **dict.fromkeys(range(32, 36), "August"),
        **dict.fromkeys(range(36, 40), "September"),
        **dict.fromkeys(range(40, 45), "Oktober"),
        **dict.fromkeys(range(45, 49), "November"),
        **dict.fromkeys(range(49, 54), "Dezember"),
    }
    df["Monat"] = df["Kalenderwoche"].map(kw_to_month)

    # Saison-Tagging
    saison_mapping = {
        "Winter": ["Dezember", "Januar", "Februar"],
        "Frühling": ["März", "April", "Mai"],
        "Sommer": ["Juni", "Juli", "August"],
        "Herbst": ["September", "Oktober", "November"],
    }
    def get_saison(monat):
        for saison, monate in saison_mapping.items():
            if monat in monate:
                return saison
        return "Unbekannt"
    df["Saison"] = df["Monat"].apply(get_saison)

    # Zielreichweiten je Warengruppe & Saison
    st.sidebar.header("🎯 Zielreichweite pro Warengruppe & Saison")
    warengruppen = df["Warengruppe"].unique()
    saisonen = ["Winter", "Frühling", "Sommer", "Herbst"]
    zielwerte_matrix = {}

    for warengruppe in warengruppen:
        for saison in saisonen:
            key = f"{warengruppe}_{saison}"
            default = 6 if saison in ["Winter", "Herbst"] else 4
            zielwerte_matrix[key] = st.sidebar.slider(f"{warengruppe} ({saison})", 2, 20, default)

    # Anwenden auf df
    def zielwert_lookup(row):
        return zielwerte_matrix.get(f"{row['Warengruppe']}_{row['Saison']}", 6)

    df["Zielreichweite (Wochen)"] = df.apply(zielwert_lookup, axis=1)

    # Reichweite berechnen
    if "RW" not in df.columns:
        df["RW"] = (df["Lagerbestand"] / (df["Verkäufe"] + 0.1)).round(1)

    # Dummy-Encoding
    df_ml = pd.get_dummies(df, columns=["Monat", "Saison"], drop_first=True)

    # Feature Auswahl
    features = [
        'Preis', 'EK', 'VK_UVP', 'Lagerbestand', 'Deckungsbeitrag', 'RW', 'Kalenderwoche'
    ] + [col for col in df_ml.columns if col.startswith("Monat_") or col.startswith("Saison_")]

    # Ziel: Absatz
    X = df_ml[features]
    y_sales = df["Verkäufe"]
    model_sales = xgb.XGBRegressor(n_estimators=100, max_depth=3)
    model_sales.fit(X, y_sales)
    df["Absatz_Prognose"] = model_sales.predict(X).round()

    # Ziel: Preis
    y_price = df["Preis"]
    model_price = xgb.XGBRegressor(n_estimators=100, max_depth=3)
    model_price.fit(X, y_price)
    df["Preis_Empfehlung"] = model_price.predict(X).round(2)

    # Ziel: Reduktionsbedarf
    df["Reduktionsbedarf"] = df["RW"] > df["Zielreichweite (Wochen)"]
    y_red = df["Reduktionsbedarf"]
    model_red = RandomForestClassifier(n_estimators=100, max_depth=5)
    model_red.fit(X, y_red)
    df["Reduktionsbedarf_Prognose"] = model_red.predict(X)

    # Tabs
    tab1, tab2, tab3 = st.tabs(["📋 Artikelliste", "📊 Dashboard", "⚙️ Reduktionslogik"])

    with tab1:
        st.subheader("📋 Artikelliste mit Prognosen")
        st.dataframe(df[[
            "Artikelnummer", "Warengruppe", "Kalenderwoche", "Saison", "RW",
            "Zielreichweite (Wochen)", "Reduktionsbedarf_Prognose", "Preis", "Preis_Empfehlung",
            "Verkäufe", "Absatz_Prognose"
        ]], use_container_width=True)

    with tab2:
        st.subheader("📊 Dashboard")
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Ø Prognose Absatz", f"{df['Absatz_Prognose'].mean():.1f}")
        kpi2.metric("Ø Preisempfehlung", f"{df['Preis_Empfehlung'].mean():.2f} €")
        kpi3.metric("Reduktionsquote", f"{df['Reduktionsbedarf_Prognose'].mean()*100:.1f} %")

        fig = px.box(df, x="Saison", y="RW", color="Reduktionsbedarf_Prognose",
                     title="Reichweite nach Saison")
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("⚙️ Reduktionslogik")
        st.write("Ein Artikel wird zur Reduktion vorgeschlagen, wenn:")
        st.write("- Die berechnete Reichweite **größer** ist als die definierte Zielreichweite für Saison & Warengruppe.")
        st.write("- Die Prognose des Modells zusätzlich diesen Bedarf bestätigt.")
