
import streamlit as st
import pandas as pd
import xgboost as xgb
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import mean_squared_error

st.set_page_config(page_title="Dynamic Pricing", layout="wide")

st.title("📈 Dynamic Pricing Web-App")
st.markdown("Lade eine CSV-Datei hoch, um deine Verkaufsdaten zu analysieren und optimale Preise zu simulieren.")

uploaded_file = st.file_uploader("📤 CSV-Datei hochladen", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.subheader("Datenvorschau")
    st.dataframe(df.head())

    if "Preis" in df.columns and "Verkäufe" in df.columns:
        df_filtered = df.copy()

        # Feature-Engineering: Kategorische Variablen encoden
        cat_cols = ["Wochentag", "Saison", "Wetter"]
        df_encoded = pd.get_dummies(df_filtered, columns=cat_cols)

        X = df_encoded.drop(columns=["Datum", "SKU", "POS_ID", "Verkäufe"])
        y = df_encoded["Verkäufe"]

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        model = xgb.XGBRegressor(objective="reg:squarederror", n_estimators=100)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        mse = mean_squared_error(y_test, y_pred)

        st.success(f"✅ Modell trainiert – MSE auf Testdaten: {mse:.2f}")

        st.subheader("💡 Preis-Absatz-Kurve Simulation")

        min_price = float(df["Preis"].min())
        max_price = float(df["Preis"].max())
        ek = float(df["EK"].mean())

        price_range = list(range(int(min_price), int(max_price) + 1))
        pred_sales = []
        pred_db = []

        for p in price_range:
            sample = X_test.iloc[[0]].copy()
            sample["Preis"] = p
            pred = model.predict(sample)[0]
            db = max(0, (p - ek) * pred)
            pred_sales.append(pred)
            pred_db.append(db)

        fig, ax = plt.subplots()
        ax.plot(price_range, pred_sales, label="Prognostizierter Absatz", marker="o")
        ax.set_xlabel("Preis (€)")
        ax.set_ylabel("Verkäufe")
        ax.set_title("Preis-Absatz-Kurve")
        ax.legend()
        st.pyplot(fig)

        fig2, ax2 = plt.subplots()
        ax2.plot(price_range, pred_db, label="Deckungsbeitrag", color="green", marker="x")
        ax2.set_xlabel("Preis (€)")
        ax2.set_ylabel("Deckungsbeitrag (€)")
        ax2.set_title("Deckungsbeitrag je Preis")
        ax2.legend()
        st.pyplot(fig2)

        optimal_index = pred_db.index(max(pred_db))
        optimal_price = price_range[optimal_index]
        st.success(f"🔧 Empfohlener optimaler Preis: **{optimal_price:.2f} €**")
    else:
        st.warning("Bitte sicherstellen, dass die CSV-Datei die Spalten 'Preis' und 'Verkäufe' enthält.")
else:
    st.info("⬆️ Bitte lade zuerst eine CSV-Datei hoch.")
