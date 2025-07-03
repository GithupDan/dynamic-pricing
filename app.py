
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import os
from PIL import Image
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

st.set_page_config(layout="wide", page_title="Merchify – Dynamic Pricing", page_icon="📈")

# === STYLING ===
st.markdown(
    """
    <style>
        body {
            background-color: #fdfdfd;
        }
        .stApp {
            background-color: #f9f9f9;
        }
        .css-18e3th9 {
            background-color: #ffffff;
        }
        .css-1d391kg {
            color: black;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# === LOGO ===
col1, col2 = st.columns([0.3, 0.7])
with col1:
    if os.path.exists("images/merchify_logo.png"):
        logo = Image.open("images/merchify_logo.png")
        st.image(logo, width=260)
with col2:
    st.title("Merchify – Dynamic Pricing")
    st.markdown("**Machine-Learning-basiertes Preis- und Bestandsmanagement für den Einzelhandel.**")

# === DATEI-UPLOAD ===
uploaded_file = st.file_uploader("📥 Lade deine CSV-Datei mit Artikeldaten hoch", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.success("Datei erfolgreich geladen.")

    # Saison berechnen
    def saison_from_kw(kw):
        if kw in range(1, 10) or kw >= 49:
            return "Winter"
        elif kw in range(10, 22):
            return "Frühling"
        elif kw in range(22, 35):
            return "Sommer"
        else:
            return "Herbst"

    df["Saison"] = df["Kalenderwoche"].apply(saison_from_kw)

    # Zielreichweiten-Definition (optional: extern laden)
    zielreichweiten = {
        ("T-Shirts", "Sommer"): 6,
        ("T-Shirts", "Winter"): 3,
        ("Sweatshirts", "Winter"): 7,
        ("Jackets", "Winter"): 10,
        ("Pants", "Herbst"): 5,
        ("Denim Pants", "Herbst"): 4,
    }

    df["Zielreichweite"] = df.apply(
        lambda row: zielreichweiten.get((row["Warengruppe"], row["Saison"]), 4), axis=1
    )

    # Reichweite berechnen
    df["Reichweite (Wochen)"] = (df["Lagerbestand"] / (df["Absatz"] + 0.01)).round(1)

    # Reduktionsvorschlag
    def vorschlag(row):
        rw, ziel = row["Reichweite (Wochen)"], row["Zielreichweite"]
        if rw > ziel * 1.5:
            return 30
        elif rw > ziel * 1.2:
            return 20
        elif rw > ziel:
            return 10
        return 0

    df["Reduktionsvorschlag (%)"] = df.apply(vorschlag, axis=1)

    # ========== MACHINE LEARNING PROGNOSE ==========
    features = ['Preis', 'Lagerbestand', 'Absatz', 'Zielreichweite']
    missing_cols = [col for col in features if col not in df.columns]

    if missing_cols:
        st.warning(f"⚠️ Folgende Spalten fehlen für die ML-Prognose: {missing_cols}")
    else:
        df_ml = df.dropna(subset=features + ['Absatz'])

        X = df_ml[features]
        y = df_ml['Absatz']
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        model = xgb.XGBRegressor(objective="reg:squarederror")
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)

        st.success(f"✅ ML-Modell trainiert. MSE: {mse:.2f}")

        df["Absatz-Prognose (ML)"] = model.predict(df[features])

    # === TABS ===
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Artikelliste", "📉 Dashboard", "🧠 Reduktionslogik", "🔮 Saisonprognose"])

    with tab1:
        st.subheader("Artikelliste mit Reduktionsvorschlägen")
        st.dataframe(df, use_container_width=True)

    with tab2:
        st.subheader("Dashboard")
        st.plotly_chart(
            px.box(df, x="Warengruppe", y="Preis", color="Saison", title="Preisspanne nach Warengruppe"),
            use_container_width=True
        )

    with tab3:
        st.subheader("Reduktionslogik")
        st.markdown("Reduktion erfolgt abhängig von der Differenz aus Reichweite und Zielreichweite:")
        st.markdown("""
        - 📦 **>150 % Zielreichweite** → **30 % Reduktion**  
        - 📦 **>120 % Zielreichweite** → **20 % Reduktion**  
        - 📦 **>100 % Zielreichweite** → **10 % Reduktion**  
        - ✅ **Sonst** → Keine Reduktion  
        """)

    with tab4:
        st.subheader("Saisonale Prognose je Warengruppe (kommende 12 Wochen)")
        try:
            df_forecast = pd.read_csv("merchify_forecast_register.csv")
            st.dataframe(df_forecast, use_container_width=True)
            st.plotly_chart(
                px.line(
                    df_forecast,
                    x="Kalenderwoche",
                    y="Prognostizierter Absatz",
                    color="Warengruppe",
                    line_group="Saison",
                    title="Absatzprognose nach Saison und Warengruppe"
                ),
                use_container_width=True
            )
        except FileNotFoundError:
            st.error("❌ Forecast-Datei nicht gefunden. Bitte sicherstellen, dass 'merchify_forecast_register.csv' im Verzeichnis liegt.")

