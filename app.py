
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Dynamic Pricing Web-App", layout="wide", initial_sidebar_state="expanded")

st.title("🧠 Dynamic Pricing Web-App")
st.markdown("Lade eine CSV-Datei hoch, um deine Verkaufsdaten zu analysieren und **optimale Preise** zu simulieren.")

uploaded_file = st.file_uploader("CSV-Datei hochladen", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file, parse_dates=["Datum"])
    st.subheader("📊 Datenvorschau")
    st.dataframe(df.head())

    if "Preis" in df.columns and "Verkäufe" in df.columns:
        st.subheader("📉 Preis-Absatz-Kurve")
        fig, ax = plt.subplots()
        ax.plot(df["Preis"], df["Verkäufe"], "o-", label="Prognostizierter Absatz")
        ax.set_xlabel("Preis")
        ax.set_ylabel("Verkäufe")
        ax.set_title("Preis-Absatz-Kurve")
        ax.legend()
        st.pyplot(fig)

    if "RW_Tage" in df.columns:
        st.subheader("📦 Reichweitenbasierte Reduktionslogik")
        def logik(rw):
            if rw <= 28:
                return "OK"
            elif 28 < rw <= 56:
                return "🔸 Beobachten"
            elif rw > 56:
                return "🔻 Reduzieren"
        df["Reduktions-Empfehlung"] = df["RW_Tage"].apply(logik)
        st.dataframe(df[["Datum", "SKU", "Preis", "RW_Tage", "Reduktions-Empfehlung"]].sort_values("RW_Tage", ascending=False))

        st.download_button("📥 Tabelle herunterladen", df.to_csv(index=False), file_name="Analyse_Reduktionslogik.csv")
