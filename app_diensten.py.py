import streamlit as st
from streamlit_sortables import sort_items
import pandas as pd
import requests
from datetime import datetime
import matplotlib.pyplot as plt

# ====== Configuratie ======
sheetdb_url = "https://sheetdb.io/api/v1/r0nrllqfrw8v6"
google_sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTSz_OE8qzi-4J4AMEnWgXUM-HqBhiLOVxEQ36AaCzs2xCNBxbF9Hd2ZAn6NcLOKdeMXqvfuPSMI27_/pub?output=csv"
geheime_code = "OTGentPlanning"

# ====== Query parameters ophalen (NIEUWE MANIER) ======
query_params = st.query_params
is_admin = query_params.get("admin_toegang", [""])[0] == geheime_code

# ====== ADMINPAGINA ======
if is_admin:
    st.markdown("<h1 style='color: #DAA520;'>🔐 Adminoverzicht: Dienstvoorkeuren</h1>", unsafe_allow_html=True)

    try:
        response = requests.get(sheetdb_url)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)

        if not df.empty:
            df["Ingevuld op"] = pd.to_datetime(df["Ingevuld op"], dayfirst=True, errors="coerce")
            df["Aantal voorkeuren"] = df["Voorkeuren"].apply(lambda x: len(str(x).split(",")))

            # Filters
            st.sidebar.header("🔎 Filters")
            coaches = sorted(df["Teamcoach"].dropna().unique())
            gekozen_coach = st.sidebar.multiselect("Filter op teamcoach", coaches, default=coaches)
            df_filtered = df[df["Teamcoach"].isin(gekozen_coach)]

            # Tabel
            st.subheader("📋 Overzicht van inzendingen")
            st.dataframe(df_filtered.sort_values("Ingevuld op", ascending=False), use_container_width=True)

            # Grafiek
            st.subheader("📊 Populairste voorkeuren")
            alle_voorkeuren = df_filtered["Voorkeuren"].dropna().str.cat(sep=",").split(",")
            telling = pd.Series([v.strip() for v in alle_voorkeuren if v.strip()]).value_counts()

            fig, ax = plt.subplots()
            telling.head(15).plot(kind="barh", ax=ax)
            ax.invert_yaxis()
            ax.set_xlabel("Aantal voorkeuren")
            ax.set_ylabel("Dienst")
            st.pyplot(fig)

            # Export
            st.subheader("📤 Exporteer overzicht")
            csv = df_filtered.to_csv(index=False).encode("utf-8")
            st.download_button("Download als CSV", data=csv, file_name="dienstvoorkeuren_adminoverzicht.csv", mime="text/csv")
        else:
            st.info("Er zijn nog geen inzendingen.")
    except Exception as e:
        st.error(f"❌ Fout bij ophalen gegevens: {e}")

# ====== GEBRUIKERSPAGINA ======
else:
    st.markdown("<h1 style='color: #DAA520;'>Maak je keuze: dienstrollen</h1>", unsafe_allow_html=True)
    
    # (Vanaf hier kan je gewoon je gebruikerspagina laten staan zoals ze was)
    # De rest van je code kan ongewijzigd blijven vanaf dit punt
