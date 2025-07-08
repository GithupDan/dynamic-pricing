
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json

st.set_page_config(page_title="Dynamic Pricing Web-App", layout="wide", initial_sidebar_state="expanded")

st.title("🧠 Dynamic Pricing Web-App")
st.markdown("Lade eine CSV-Datei hoch, um deine Verkaufsdaten zu analysieren und **optimale Preise** zu simulieren.")

uploaded_file = st.file_uploader("CSV-Datei hochladen", type="csv")

def get_last_4_weeks_data(df):
    # Datum in Kalenderwoche und Jahr
    df['Jahr'] = df['Datum'].dt.year
    df['KW'] = df['Datum'].dt.isocalendar().week

    # Aktuellste Kalenderwoche im Datensatz
    max_jahr = df['Jahr'].max()
    max_kw = df[df['Jahr'] == max_jahr]['KW'].max()

    # Liste der letzten 4 Kalenderwochen (Jahr, KW)
    # Achtung: KW kann bei Jahreswechsel < 4 sein, daher mit Jahr anpassen
    def prev_weeks(year, week, n):
        weeks = []
        for i in range(n):
            w = week - i - 1
            y = year
            if w < 1:
                y -= 1
                # Anzahl KW des Vorjahres (52 oder 53)
                w = pd.Timestamp(year=y, month=12, day=28).isocalendar().week
            weeks.append((y, w))
        return weeks[::-1]  # aufsteigend
    last_4_weeks = prev_weeks(max_jahr, max_kw, 4)

    # Filtern nach diesen Wochen und aggregieren
    df_agg = df.groupby(['SKU', 'Jahr', 'KW'])['Verkäufe'].sum().reset_index()

    # Erstelle DataFrame mit SKU als Index und 4 Spalten für die KW
    result = pd.DataFrame({'SKU': df['SKU'].unique()})
    for i, (y, w) in enumerate(last_4_weeks):
        col_name = f'Absatz_KW_{w}_{y}'
        temp = df_agg[(df_agg['Jahr'] == y) & (df_agg['KW'] == w)][['SKU', 'Verkäufe']].rename(columns={'Verkäufe': col_name})
        result = result.merge(temp, on='SKU', how='left')
    result.fillna(0, inplace=True)
    return result, last_4_weeks

if uploaded_file:
    df = pd.read_csv(uploaded_file, parse_dates=["Datum"])
    st.subheader("📊 Datenvorschau")
    st.dataframe(df.head())

    # Berechnung der Absätze der letzten 4 Kalenderwochen
    kw_absatz_df, last_4_weeks = get_last_4_weeks_data(df)

    # Sidebar Eingabe: Zielreichweiten je Monat & Warengruppe als JSON (vereinfachte Variante)
    st.sidebar.header("⚙️ Einstellungen")
    st.sidebar.markdown("Definiere Zielreichweiten (in Wochen) pro Warengruppe und Monat (Format: JSON)")

    # Beispiel-Template für die Eingabe
    example_json = """
{
    "Warengruppe1": {
        "2025-06": 4,
        "2025-07": 3
    },
    "Warengruppe2": {
        "2025-06": 6,
        "2025-07": 5
    }
}
"""
    zielreichweiten_input = st.sidebar.text_area("Zielreichweiten JSON", value=example_json, height=150)

    try:
        zielreichweiten = json.loads(zielreichweiten_input)
    except json.JSONDecodeError:
        st.sidebar.error("Ungültiges JSON-Format!")
        zielreichweiten = {}

    # Prüfung, ob erforderliche Spalten vorhanden sind
    required_cols = ["SKU", "Preis", "Verkäufe", "Lagerbestand", "Warengruppe"]
    if all(col in df.columns for col in required_cols):
        # Berechnung Reichweite (Lagerbestand / Absatz letzte Woche)
        # Wir nehmen letzte Kalenderwoche aus last_4_weeks
        letzte_kw = last_4_weeks[-1]
        jahr_kw_str = f'Absatz_KW_{letzte_kw[1]}_{letzte_kw[0]}'

        # Kombiniere Hauptdf mit kw_absatz_df (SKU + Absatz letzte KW)
        df_absatz = df[['SKU', 'Preis', 'Lagerbestand', 'Warengruppe']].drop_duplicates(subset=['SKU'])
        df_absatz = df_absatz.merge(kw_absatz_df[['SKU', jahr_kw_str]], on='SKU', how='left')
        df_absatz.rename(columns={jahr_kw_str: 'Absatz_letzte_KW'}, inplace=True)
        df_absatz['Absatz_letzte_KW'] = df_absatz['Absatz_letzte_KW'].fillna(0)

        # Reichweite in Wochen berechnen (Lagerbestand / Absatz letzte Woche)
        # Achtung: Division durch 0 vermeiden
        df_absatz['Reichweite'] = df_absatz.apply(
            lambda row: row['Lagerbestand'] / row['Absatz_letzte_KW'] if row['Absatz_letzte_KW'] > 0 else float('inf'), axis=1)

        # Ermittle den Monat/Jahr aus dem letzten Datum im Dataframe (für Zielreichweitenvergleich)
        letzter_monat = df['Datum'].max().strftime("%Y-%m")

        def get_zielreichweite(row):
            wg = row['Warengruppe']
            if wg in zielreichweiten and letzter_monat in zielreichweiten[wg]:
                return zielreichweiten[wg][letzter_monat]
            else:
                return None

        df_absatz['Zielreichweite'] = df_absatz.apply(get_zielreichweite, axis=1)

        # Reduzierungsvorschlag basierend auf Vergleich Reichweite vs Zielreichweite
        def reduktion(row):
            if row['Zielreichweite'] is None:
                return "Keine Zielvorgabe"
            if row['Reichweite'] == float('inf'):
                return "Kein Absatz letzte Woche"
            if row['Reichweite'] > row['Zielreichweite']:
                return "🔻 Reduzieren"
            else:
                return "✅ OK"

        df_absatz['Reduzierungsvorschlag'] = df_absatz.apply(reduktion, axis=1)

        # Berechnung neuer Verkaufspreis (z.B. wenn Reichweite zu hoch, Preis senken um 5%)
        def neuer_preis(row):
            if row['Reduzierungsvorschlag'] == "🔻 Reduzieren":
                return round(row['Preis'] * 0.95, 2)
            else:
                return row['Preis']

        df_absatz['Neuer_Preis'] = df_absatz.apply(neuer_preis, axis=1)

        # Ausgabe der erweiterten Artikelliste mit Kennzahlen
        st.subheader("🧾 Erweiterte Artikelliste mit Kennzahlen")

        # Merge mit den Absätzen der letzten 4 Kalenderwochen (kw_absatz_df)
        artikelliste = df_absatz.merge(kw_absatz_df, on='SKU', how='left')

        st.dataframe(artikelliste)

        # Download-Button
        csv = artikelliste.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Artikelliste herunterladen", csv, file_name="artikelliste_kennzahlen.csv", mime='text/csv')

    else:
        st.warning(f"Für die erweiterten Berechnungen werden folgende Spalten benötigt: {required_cols}")

    # Zusätzlich weiterhin deine bisherige Preis-Absatz-Kurve & Reduktionslogik (RW_Tage) anzeigen, falls vorhanden
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
