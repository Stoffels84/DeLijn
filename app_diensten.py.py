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
wachtwoord_admin = st.secrets["ADMIN_WACHTWOORD"]

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

# ====== ADMINPAGINA ======
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
            alle_voorkeuren = df["Voorkeuren"].dropna().str.cat(sep=", ").split(",")
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

# ====== GEBRUIKERSPAGINA ======
if not is_admin:
    st.markdown("<h1 style='color: #DAA520;'>Maak je keuze: dienstrollen</h1>", unsafe_allow_html=True)

    with st.container():
        st.info("""
        ### ℹ️ Uitleg
        **Om voor een dienstrol met 1 type voertuig te kunnen kiezen**, moet je over de (actieve) kwalificatie beschikken of hiervoor al ingepland zijn. Een **gemengde dienstrol** kan je wel kiezen met maar 1 kwalificatie indien je bereid bent om de andere kwalificatie te behalen.

        ---
        #### 🚏 Invulling open plaats
        De open plaats wordt gepubliceerd voor alle chauffeurs die zich kandidaat wensen te stellen. 
        Kandidaten worden gerangschikt volgens **stelplaatsanciënniteit**. De eerst gerangschikte neemt de open plaats in.

        ---
        #### 🔄 Invulling doorgeschoven plaats
        Chauffeurs mogen steeds een aanvraag via mail doorsturen waarin zij hun voorkeur kenbaar maken voor een andere plaats die op dat moment nog niet open staat, maar die ze in de toekomst graag zouden innemen. 
        Als een plaats open komt via doorschuiven omdat een chauffeur een andere plaats inneemt, wordt deze plaats **niet meer uitgehangen** maar onmiddellijk ingevuld. Hiervoor worden de aanvragen nagekeken op **stelplaatsanciënniteit**. De chauffeur met de hoogste stelplaatsanciënniteit zal deze plaats toegewezen krijgen.
        """, icon="ℹ️")

    personeelsnummer = st.text_input("Personeelsnummer")
    persoonlijke_code = st.text_input("Persoonlijke code (4 cijfers)", type="password")

    if personeelsnummer and persoonlijke_code:
        try:
            df_personeel = pd.read_csv(google_sheet_url, dtype=str)
            df_personeel.columns = df_personeel.columns.str.strip().str.lower()
            match = df_personeel[(df_personeel["personeelsnummer"] == personeelsnummer) &
                                 (df_personeel["controle"] == persoonlijke_code)]

            if match.empty:
                st.warning("⚠️ Combinatie van personeelsnummer en code niet gevonden.")
            else:
                naam_gevonden = match.iloc[0]["naam"]
                coach_gevonden = match.iloc[0]["teamcoach"]
                st.success(f"👋 Welkom terug, **{naam_gevonden}**!")

                bestaande_data = None
                eerder_voorkeuren = []
                response_check = requests.get(f"{sheetdb_url}/search?Personeelsnummer={personeelsnummer}")
                gevonden = response_check.json()
                if gevonden:
                    bestaande_data = gevonden[0]
                    voorkeur_string = bestaande_data.get("Voorkeuren", "")
                    eerder_voorkeuren = [v.strip() for v in voorkeur_string.split(",") if v.strip()]
                    laatst = bestaande_data.get("Laatste aanpassing", "onbekend")
                    st.info(f"Eerdere inzending gevonden. Laatste wijziging op: **{laatst}**")

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

                geselecteerd = st.multiselect("Selecteer diensten:", diensten, default=eerder_voorkeuren)
                volgorde = sort_items(geselecteerd, direction="vertical") if geselecteerd else eerder_voorkeuren
                if set(volgorde) != set(geselecteerd):
                    volgorde = geselecteerd

                if geselecteerd:
                    st.subheader("Jouw voorkeursvolgorde:")
                    for i, item in enumerate(volgorde, 1):
                        st.write(f"{i}. {item}")
                else:
                    st.info("Selecteer eerst één of meerdere diensten.")

                bevestigd = st.checkbox("Ik bevestig mijn voorkeur en ga akkoord met automatische toewijzing bij wijzigingen.")

                if st.button("Verzend je antwoorden"):
                    if not bevestigd:
                        st.error("Bevestig je voorkeur eerst.")
                    elif not volgorde:
                        st.error("Selecteer minstens één dienst.")
                    else:
                        resultaat = {
                            "Personeelsnummer": personeelsnummer,
                            "Naam": naam_gevonden,
                            "Teamcoach": coach_gevonden,
                            "Voorkeuren": ", ".join(volgorde),
                            "Bevestiging plaatsvoorkeur": "True",
                            "Ingevuld op": bestaande_data.get("Ingevuld op", datetime.now().strftime("%d/%m/%Y %H:%M:%S")) if bestaande_data else datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                            "Laatste aanpassing": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        }
                        try:
                            with st.spinner("Gegevens worden verwerkt..."):
                                if bestaande_data:
                                    response = requests.put(f"{sheetdb_url}/Personeelsnummer/{personeelsnummer}", json={"data": resultaat})
                                    st.success(f"✅ Voorkeuren van {naam_gevonden} succesvol bijgewerkt.")
                                else:
                                    response = requests.post(sheetdb_url, json={"data": resultaat})
                                    st.success(f"✅ Bedankt {naam_gevonden}, je voorkeuren zijn succesvol ingediend.")
                                response.raise_for_status()
                                with st.expander("Bekijk je ingediende gegevens"):
                                    st.json(resultaat)
                        except Exception as e:
                            st.error(f"❌ Fout bij verzenden: {e}")

        except Exception as e:
            st.error(f"❌ Fout bij laden van personeelsgegevens: {e}")
