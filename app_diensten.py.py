import streamlit as st
from streamlit_sortables import sort_items
import pandas as pd
import requests
from datetime import datetime
import matplotlib.pyplot as plt
import hashlib
import os

# ====== Configuratie ======
sheetdb_url = "https://sheetdb.io/api/v1/r0nrllqfrw8v6"
google_sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTSz_OE8qzi-4J4AMEnWgXUM-HqBhiLOVxEQ36AaCzs2xCNBxbF9Hd2ZAn6NcLOKdeMXqvfuPSMI27_/pub?output=csv"
wachtwoord_admin = os.getenv("ADMIN_WACHTWOORD", "OTGentPlanning")

# ====== Functie voor wachtwoordhashing ======
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ====== Admin login ======
is_admin = False
st.sidebar.header("🔐 Admin login")
password_input = st.sidebar.text_input("Admin wachtwoord", type="password")
if hash_password(password_input) == hash_password(wachtwoord_admin):
    is_admin = True

# ====== CSS ======
st.markdown("""
    <style>
    .block-container {padding-left: 1rem !important; padding-right: 1rem !important;}
    .dataframe-container {overflow-x: auto;}
    div.stButton > button {width: 100% !important; padding: 0.75rem; font-size: 1rem;}
    input[type="text"], textarea {font-size: 1rem;}
    .element-container {max-width: 100% !important; overflow-x: auto;}
    </style>
""", unsafe_allow_html=True)

# ====== GEBRUIKERSPAGINA ======
if not is_admin:
    st.markdown("<h1 style='color: #DAA520;'>Maak je keuze: dienstrollen</h1>", unsafe_allow_html=True)
    try:
        df_personeel = pd.read_csv(google_sheet_url, dtype=str)
        if df_personeel.columns.isnull().any():
            st.error("❌ Fout: De Google Sheet bevat geen geldige kolomnamen.")
            st.stop()
        df_personeel.columns = df_personeel.columns.str.strip().str.lower()

        vereiste_kolommen = {"personeelsnummer", "controle", "naam", "teamcoach"}
        if not vereiste_kolommen.issubset(set(df_personeel.columns)):
            st.error("❌ Fout: ontbrekende kolommen in personeelsbestand. Controleer de structuur van de Google Sheet.")
            st.stop()
    except Exception as e:
        st.error(f"❌ Fout bij laden van personeelsgegevens: {e}")
        st.stop()

# ====== ADMIN ======
if is_admin:
    st.markdown("<h1 style='color: #DAA520;'>🔐 Adminoverzicht: Dienstvoorkeuren</h1>", unsafe_allow_html=True)
    try:
        response = requests.get(sheetdb_url)
        response.raise_for_status()
        df = pd.DataFrame(response.json())

        if not df.empty:
            df["Ingevuld op"] = pd.to_datetime(df["Ingevuld op"], dayfirst=True, errors="coerce")
            df["Aantal voorkeuren"] = df["Voorkeuren"].apply(lambda x: len(str(x).split(",")))
            df["Bevestigd"] = df["Bevestiging plaatsvoorkeur"].map({"True": "✅", "False": "❌"})

            st.sidebar.header("🔎 Filters")
            coaches = sorted(df["Teamcoach"].dropna().unique())
            gekozen_coach = st.sidebar.multiselect("Filter op teamcoach", coaches, default=coaches)
            zoeknummer = st.sidebar.text_input("Zoek op personeelsnummer")
            alle_voorkeuren = df["Voorkeuren"].dropna().str.cat(sep=",").split(",")
            diensten_uniek = sorted(set(v.strip() for v in alle_voorkeuren if v.strip()))
            gekozen_diensten = st.sidebar.multiselect("Filter op dienst", diensten_uniek)

            df_filtered = df[df["Teamcoach"].isin(gekozen_coach)]
            if zoeknummer:
                df_filtered = df_filtered[df_filtered["Personeelsnummer"].str.contains(zoeknummer.strip(), na=False)]
            if gekozen_diensten:
                df_filtered = df_filtered[df_filtered["Voorkeuren"].apply(lambda x: any(d in x for d in gekozen_diensten))]

            st.subheader("📋 Overzicht van inzendingen")
            st.dataframe(df_filtered.sort_values("Ingevuld op", ascending=False), use_container_width=True)

            st.subheader("📊 Populairste voorkeuren")
            telling = pd.Series([v.strip() for v in alle_voorkeuren if v.strip()]).value_counts()
            fig, ax = plt.subplots()
            telling.head(15).plot(kind="barh", ax=ax, edgecolor="black")
            ax.invert_yaxis()
            ax.set_title("Top 15 Populairste Diensten")
            ax.set_xlabel("Aantal voorkeuren")
            ax.set_ylabel("Dienst")
            st.pyplot(fig)

            st.subheader("📄 Exporteer overzicht")
            csv = df_filtered.to_csv(index=False).encode("utf-8")
            st.download_button("Download als CSV", data=csv, file_name="dienstvoorkeuren_admin.csv", mime="text/csv")
        else:
            st.info("Er zijn nog geen inzendingen.")
    except Exception as e:
        st.error(f"❌ Fout bij ophalen gegevens: {e}")
