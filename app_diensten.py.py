import streamlit as st
from streamlit_sortables import sort_items
import pandas as pd
import requests
from datetime import datetime
import matplotlib.pyplot as plt

# ====== Configuratie ======
sheetdb_url = "https://sheetdb.io/api/v1/r0nrllqfrw8v6"
google_sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTSz_OE8qzi-4J4AMEnWgXUM-HqBhiLOVxEQ36AaCzs2xCNBxbF9Hd2ZAn6NcLOKdeMXqvfuPSMI27_/pub?output=csv"
geheime_code = "OT03GentPlanning"

# ====== Toegang controleren ======
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
    df_personeel = pd.read_csv(google_sheet_url, dtype=str)
    df_personeel.columns = df_personeel.columns.str.strip().str.lower()

    st.markdown("<h2 style='color: #DAA520;'>Vraag 1: Personeelsnummer</h2>", unsafe_allow_html=True)
    personeelsnummer = st.text_input(label="", placeholder="Vul hier je personeelsnummer in", key="personeelsnummer").strip()

    naam_gevonden = ""
    coach_gevonden = ""
    match = pd.DataFrame()

    if personeelsnummer:
        if not personeelsnummer.isdigit():
            st.warning("⚠️ Het personeelsnummer moet enkel cijfers bevatten.")
        else:
            match = df_personeel[df_personeel["personeelsnummer"] == personeelsnummer]
            if not match.empty:
                naam_gevonden = match.iloc[0]["naam"]
                coach_gevonden = match.iloc[0]["teamcoach"]
            else:
                st.warning("⚠️ Personeelsnummer niet gevonden in de personeelslijst.")

    bestaande_data = None
    eerder_voorkeuren = []

    if personeelsnummer and not match.empty:
        try:
            response_check = requests.get(f"{sheetdb_url}/search?Personeelsnummer={personeelsnummer}")
            response_check.raise_for_status()
            gevonden = response_check.json()
            if gevonden:
                bestaande_data = gevonden[0]
                st.info("We hebben eerder ingevulde gegevens gevonden. Je kan ze nu bewerken.")
                voorkeur_string = bestaande_data.get("Voorkeuren", "")
                eerder_voorkeuren = [v.strip() for v in voorkeur_string.split(",") if v.strip()]
        except requests.RequestException as e:
            st.error(f"❌ Fout bij ophalen van gegevens uit SheetDB: {e}")

    st.markdown("<h3 style='color: #DAA520;'>Jouw naam</h3>", unsafe_allow_html=True)
    naam = st.text_input(label="", value=naam_gevonden or (bestaande_data.get("Naam") if bestaande_data else ""), 
                         placeholder="Naam wordt automatisch ingevuld", disabled=bool(naam_gevonden), key="naam").strip()

    st.markdown("<h3 style='color: #DAA520;'>Jouw teamcoach</h3>", unsafe_allow_html=True)
    teamcoach = st.text_input(label="", value=coach_gevonden or (bestaande_data.get("Teamcoach") if bestaande_data else ""), 
                              placeholder="Teamcoach wordt automatisch ingevuld", disabled=bool(coach_gevonden), key="coach").strip()

    st.markdown("<h3 style='color: #DAA520;'>Voor welke roosters stel je u kandidaat?</h3>", unsafe_allow_html=True)
    diensten = [
        "T24 (Tram Laat-Vroeg)", "TW24 (Tram Week-Week)", "TV12 (Tram Vroeg)", "TL12 (Tram Reserve)",
        "G09 (Gelede Bus 9 & 11 Laat-Vroeg)", "GW09 (Gelede Bus 9 & 11 Week-Week)", "B24 (Busmix Laat-Vroeg)",
        "G70 (Gelede Bus 70 & 71 Laat-Vroeg)", "G10 (Gelede Bus 10 & 12 Laat-Vroeg)", "GW10 (Gelede Bus 10 & 12 Week-Week)",
        "S05 (Standaardbus 5 & 33 Laat-Vroeg)", "SW05 (Standaardbus 5 & 33 Week-Week)", "TD12 (Dagdiensten Tram)",
        "BD12 (Dagdiensten Bus)", "MV12 (Bustrammix Vroeg)", "ML12 (Bustrammix Reserve)",
        "TR15 (Tram Weekend Thuis met Onderbroken Diensten)", "BR15 (Bus Weekend Thuis met Onderbroken Diensten)",
        "M15 (Bustrammix Weekend Thuis Zonder Onderbroken Diensten)", "BN24 (Late Nachtdiensten Bus)",
        "TN24 (Late Nachtdiensten Tram)", "MN24 (Late Nachtdiensten Bustrammix)",
        "BO15 (Onderbroken Diensten Bus)", "TO15 (Onderbroken Diensten Tram)", "MW12 (Bustrammix Weekendrol)"
    ]
    geselecteerd = st.multiselect("Selecteer één of meerdere diensten:", diensten, default=eerder_voorkeuren)
    volgorde = sort_items(geselecteerd, direction="vertical") if geselecteerd else eerder_voorkeuren

    if geselecteerd:
        st.subheader("Jouw voorkeursvolgorde:")
        for i, item in enumerate(volgorde, 1):
            st.write(f"{i}. {item}")
    else:
        st.info("Selecteer eerst één of meerdere diensten om verder te gaan.")

    bevestigd = st.checkbox(
        "Ik bevestig dat mijn voorkeur correct is ingevuld. Bij wijzigingen in de planning mag ik automatisch ingepland worden op basis van mijn plaatsvoorkeur binnen deze rol(len)."
    )

    st.markdown("""
        <style>
        div.stButton > button {
            background-color: #DAA520;
            color: white;
            font-weight: bold;
            width: 100%%;
            padding: 0.75em;
            border-radius: 5px;
            position: fixed;
            bottom: 10px;
            left: 0;
            right: 0;
            margin-left: auto;
            margin-right: auto;
            max-width: 400px;
            z-index: 9999;
        }
        </style>
    """, unsafe_allow_html=True)

    if st.button("Verzend je antwoorden"):
        if not bevestigd:
            st.error("Je moet eerst bevestigen dat je akkoord gaat met de plaatsvoorkeurregel.")
        elif not personeelsnummer or not naam or not teamcoach or not volgorde:
            st.error("Gelieve alle verplichte velden in te vullen.")
        elif not personeelsnummer.isdigit():
            st.error("Het personeelsnummer moet enkel cijfers bevatten.")
        elif match.empty:
            st.error("⚠️ Personeelsnummer komt niet voor in de personeelslijst.")
        else:
            resultaat = {
                "Personeelsnummer": personeelsnummer,
                "Naam": naam,
                "Teamcoach": teamcoach,
                "Voorkeuren": ", ".join(volgorde),
                "Bevestiging plaatsvoorkeur": "Ja",
                "Ingevuld op": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }

            with st.spinner("Gegevens worden verwerkt..."):
                try:
                    if bestaande_data:
                        response = requests.put(f"{sheetdb_url}/Personeelsnummer/{personeelsnummer}", json={"data": resultaat})
                    else:
                        response = requests.post(sheetdb_url, json={"data": resultaat})
                    response.raise_for_status()

                    st.success(f"Bedankt {naam}, je voorkeuren werden opgeslagen via SheetDB!")
                    with st.expander("Bekijk je ingediende gegevens"):
                        st.json(resultaat)

                except requests.RequestException as e:
                    st.error(f"❌ Er ging iets mis bij het verzenden naar SheetDB: {e}")
