
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image

st.set_page_config(page_title="Merchify – Dynamic Pricing", layout="wide", initial_sidebar_state="expanded")

# Logo laden und anzeigen (Cloud-kompatibel)
logo = Image.open("images/merchify_logo.png")
st.image(logo, width=280)
st.markdown("### _The smart way to optimize your markdowns._")
st.markdown("---")

uploaded_file = st.file_uploader("📤 CSV-Datei hochladen", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file, parse_dates=["Datum"])
    st.subheader("🔍 Datenvorschau")
    st.dataframe(df.head())

    # Auswahloptionen
    if "KW" in df.columns and "Jahr" in df.columns:
        jahre = sorted(df["Jahr"].unique())
        jahr = st.selectbox("📅 Jahr wählen", jahre, index=len(jahre)-1)
        wochen = sorted(df[df["Jahr"] == jahr]["KW"].unique())
        kw = st.selectbox("📆 Kalenderwoche wählen", wochen)

        df_kw = df[(df["Jahr"] == jahr) & (df["KW"] == kw)]
        st.subheader(f"📊 Analyse für KW {kw}, {jahr}")
        st.dataframe(df_kw[["SKU", "Preis", "Verkäufe", "RW_KW", "Lager"]].sort_values("RW_KW", ascending=False))

        st.subheader("📉 Preis vs. Verkäufe")
        fig, ax = plt.subplots()
        ax.scatter(df_kw["Preis"], df_kw["Verkäufe"], alpha=0.6, color="#00b3b1")
        ax.set_xlabel("Preis")
        ax.set_ylabel("Verkäufe")
        ax.set_title("Preis-Absatz-Übersicht")
        st.pyplot(fig)

        st.subheader("📦 Reichweitenbewertung (RW_KW)")
        def logik(rw):
            if rw <= 4:
                return "✅ OK"
            elif 4 < rw <= 8:
                return "🔸 Beobachten"
            elif rw > 8:
                return "🔻 Reduzieren"
        df_kw["Reduktions-Empfehlung"] = df_kw["RW_KW"].apply(logik)
        st.dataframe(df_kw[["SKU", "RW_KW", "Reduktions-Empfehlung"]])

        st.download_button("📥 Download Woche als CSV", df_kw.to_csv(index=False), file_name=f"Reduktionsanalyse_KW{kw}_{jahr}.csv")
else:
    st.info("Bitte lade eine CSV-Datei mit Spalten 'Datum', 'KW', 'Jahr', 'Preis', 'RW_KW' usw. hoch.")
