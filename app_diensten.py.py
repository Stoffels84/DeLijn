import streamlit as st
from streamlit_sortables import sort_items
import pandas as pd
import requests
from datetime import datetime

# ====== Configuratie: SheetDB API en Google Sheet ======
sheetdb_url = "https://sheetdb.io/api/v1/r0nrllqfrw8v6"  # ← SheetDB-link
google_sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTSz_OE8qzi-4J4AMEnWgXUM-HqBhiLOVxEQ36AaCzs2xCNBxbF9Hd2ZAn6NcLOKdeMXqvfuPSMI27_/pub?output=csv"

# ====== Personeelslijst ophalen en kolomnamen normaliseren ======
df_personeel = pd.read_csv(google_sheet_url, dtype=str)
df_personeel.columns = df_personeel.columns.str.strip().str.lower()

# ====== Titel ======
st.markdown("<h1 style='color: #DAA520;'>Maak je keuze: dienstrollen</h1>", unsafe_allow_html=True)

# ====== Vul je personeelsnummer in ======
st.markdown("<h2 style='color: #DAA520;'>Vraag 1: Personeelsnummer</h2>", unsafe_allow_html=True)
personeelsnummer = st.text_input(label="", placeholder="Vul hier je personeelsnummer in", key="personeelsnummer").strip()

# ====== Automatisch naam + teamcoach ophalen uit lijst ======
naam_gevonden = ""
coach_gevonden = ""

if personeelsnummer:
    match = df_personeel[df_personeel["personeelsnummer"] == personeelsnummer]
    if not match.empty:
        naam_gevonden = match.iloc[0]["naam"]
        coach_gevonden = match.iloc[0]["teamcoach"]

# ====== Eerdere gegevens ophalen uit SheetDB ======
bestaande_data = None
eerder_voorkeuren = []

if personeelsnummer:
    response_check = requests.get(f"{sheetdb_url}/search?Personeelsnummer={personeelsnummer}")
    if response_check.status_code == 200:
        gevonden = response_check.json()
        if gevonden:
            bestaande_data = gevonden[0]
            st.info("We hebben eerder ingevulde gegevens gevonden. Je kan ze nu bewerken.")
            eerder_voorkeuren = bestaande_data.get("Voorkeuren", "").split(", ")

# ====== Je naam ======
st.markdown("<h3 style='color: #DAA520;'>Jouw naam</h3>", unsafe_allow_html=True)
naam = st.text_input(label="", value=naam_gevonden or (bestaande_data.get("Naam") if bestaande_data else ""), 
                     placeholder="Naam wordt automatisch ingevuld", disabled=bool(naam_gevonden), key="naam")

# ====== Je teamcoach? ======
st.markdown("<h3 style='color: #DAA520;'>Jouw teamcoach</32>", unsafe_allow_html=True)
teamcoach = st.text_input(label="", value=coach_gevonden or (bestaande_data.get("Teamcoach") if bestaande_data else ""), 
                          placeholder="Teamcoach wordt automatisch ingevuld", disabled=bool(coach_gevonden), key="coach")

# ====== voor welke roosters stel je u kandidaat? ======
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
volgorde = sort_items(geselecteerd, direction="vertical") if geselecteerd else []

if geselecteerd:
    st.subheader("Jouw voorkeursvolgorde:")
    for i, item in enumerate(volgorde, 1):
        st.write(f"{i}. {item}")
else:
    st.info("Selecteer eerst één of meerdere diensten om verder te gaan.")

# ====== Bevestig of je gegevens correct zijn ======
bevestigd = st.checkbox(
    "Ik bevestig dat mijn voorkeur correct is ingevuld. Bij wijzigingen in de planning mag ik automatisch ingepland worden op basis van mijn plaatsvoorkeur binnen deze rol(len)."
)

# ====== Verzenden-knop styling ======
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

# ====== Verzendactie ======
if st.button("Verzend je antwoorden"):
    if not bevestigd:
        st.error("Je moet eerst bevestigen dat je akkoord gaat met de plaatsvoorkeurregel.")
    elif not personeelsnummer or not naam or not teamcoach or not volgorde:
        st.error("Gelieve alle verplichte velden in te vullen.")
    elif not personeelsnummer.isdigit():
        st.error("Het personeelsnummer moet enkel cijfers bevatten.")
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
            if bestaande_data:
                response = requests.put(f"{sheetdb_url}/Personeelsnummer/{personeelsnummer}", json={"data": resultaat})
            else:
                response = requests.post(sheetdb_url, json={"data": resultaat})

        if response.status_code in [200, 201]:
            st.success(f"Bedankt {naam}, je voorkeuren werden opgeslagen via SheetDB!")
            with st.expander("Bekijk je ingediende gegevens"):
                st.json(resultaat)
        else:
            st.error("Er ging iets mis bij het verzenden naar SheetDB.")
