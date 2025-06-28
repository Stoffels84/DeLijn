import streamlit as st
from streamlit_sortables import sort_items
import pandas as pd
import requests
from datetime import datetime

# Titel
st.markdown("<h1 style='color: #DAA520;'>Maak je keuze: dienstrollen</h1>", unsafe_allow_html=True)

# Vraag 1: Selectie
st.markdown("<h2 style='color: #DAA520;'>Vraag 1: Kies je gewenste diensten</h2>", unsafe_allow_html=True)
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
geselecteerd = st.multiselect("Selecteer één of meerdere diensten:", diensten)

# Vraag 2: Rangschikking
st.markdown("<h2 style='color: #DAA520;'>Vraag 2: Rangschik je voorkeuren (versleep de items)</h2>", unsafe_allow_html=True)
volgorde = sort_items(geselecteerd, direction="vertical") if geselecteerd else []

if geselecteerd:
    st.subheader("Jouw voorkeursvolgorde:")
    for i, item in enumerate(volgorde, 1):
        st.write(f"{i}. {item}")
else:
    st.info("Selecteer eerst één of meerdere diensten om verder te gaan.")

# Vraag 3: Personeelsnummer
st.markdown("<h2 style='color: #DAA520;'>Vraag 3: Personeelsnummer</h2>", unsafe_allow_html=True)
personeelsnummer = st.text_input(label="", placeholder="Vul hier je personeelsnummer in", key="personeelsnummer")

# Vraag 4: Naam en voornaam
st.markdown("<h2 style='color: #DAA520;'>Vraag 4: Naam en voornaam</h2>", unsafe_allow_html=True)
naam = st.text_input(label="", placeholder="Vul hier je naam en voornaam in", key="naam")

# Vraag 5: Teamcoach
st.markdown("<h2 style='color: #DAA520;'>Vraag 5: Wie is jouw teamcoach?</h2>", unsafe_allow_html=True)
teamcoach = st.radio("Selecteer je teamcoach:", [
    "Christoff Rotty", "Steven Storm", "Dominique De Clercq", "Els Dewulf",
    "Lucie Van De Velde", "Els Vanhoe", "Kenneth De Rick", "Bart Van Der Beken"
])

# Verzenden
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
    if not personeelsnummer or not naam or not volgorde:
        st.error("Gelieve alle verplichte velden in te vullen.")
    elif not personeelsnummer.isdigit():
        st.error("Het personeelsnummer moet enkel cijfers bevatten.")
    else:
        resultaat = {
            "Personeelsnummer": personeelsnummer,
            "Naam": naam,
            "Teamcoach": teamcoach,
            "Voorkeuren": ", ".join(volgorde),
            "Ingevuld op": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }

        # ⬇️ SheetDB: API-verzending
        sheetdb_url = "https://sheetdb.io/api/v1/r0nrllqfrw8v6"  # <-- VERVANG DOOR JOUW ECHTE URL
        data = {"data": resultaat}
        response = requests.post(sheetdb_url, json=data)

        if response.status_code == 201:
            st.success(f"Bedankt {naam}, je voorkeuren werden opgeslagen via SheetDB!")
            with st.expander("Bekijk je ingediende gegevens"):
                st.json(resultaat)
        else:
            st.error("Er ging iets mis bij het verzenden naar SheetDB.")

# Downloadgedeelte kan eventueel uitgeschakeld worden als je geen Excel meer gebruikt
