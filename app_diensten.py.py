import streamlit as st
from streamlit_sortables import sort_items
import pandas as pd
import requests
from datetime import datetime
import matplotlib.pyplot as plt
import hashlib

# ====== Configuratie ======
sheetdb_url = "https://sheetdb.io/api/v1/r0nrllqfrw8v6"
google_sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTSz_OE8qzi-4J4AMEnWgXUM-HqBhiLOVxEQ36AaCzs2xCNBxbF9Hd2ZAn6NcLOKdeMXqvfuPSMI27_/pub?output=csv"
wachtwoord_admin = "OTGentPlanning"

# ====== Functie voor wachtwoordhashing ======
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ====== Toegang controleren via wachtwoord (veiliger dan query param) ======
is_admin = False
st.sidebar.header("🔐 Admin login")
password_input = st.sidebar.text_input("Admin wachtwoord", type="password")
if hash_password(password_input) == hash_password(wachtwoord_admin):
    is_admin = True

# ====== CSS voor mobiele optimalisatie ======
st.markdown("""
    <style>
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    .dataframe-container {
        overflow-x: auto;
    }
    div.stButton > button {
        width: 100% !important;
        padding: 0.75rem;
        font-size: 1rem;
    }
    input[type="text"], textarea {
        font-size: 1rem;
    }
    .element-container {
        max-width: 100% !important;
        overflow-x: auto;
    }
    </style>
""", unsafe_allow_html=True)

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

            # ========== Filters ==========
            st.sidebar.header("🔎 Filters")

            coaches = sorted(df["Teamcoach"].dropna().unique())
            gekozen_coach = st.sidebar.multiselect("Filter op teamcoach", coaches, default=coaches)

            zoeknummer = st.sidebar.text_input("Zoek op personeelsnummer (volledig of gedeeltelijk)")

            alle_voorkeuren_flat = df["Voorkeuren"].dropna().str.cat(sep=",").split(",")
            diensten_uniek = sorted(set(v.strip() for v in alle_voorkeuren_flat if v.strip()))
            gekozen_diensten = st.sidebar.multiselect("Filter op dienst", diensten_uniek)

            df_filtered = df[df["Teamcoach"].isin(gekozen_coach)]

            if zoeknummer:
                df_filtered = df_filtered[df_filtered["Personeelsnummer"].str.contains(zoeknummer.strip(), na=False)]

            if gekozen_diensten:
                df_filtered = df_filtered[
                    df_filtered["Voorkeuren"].apply(lambda x: any(dienst in x for dienst in gekozen_diensten))
                ]

            # ========== Tabel ==========
            st.subheader("📋 Overzicht van inzendingen")
            st.dataframe(df_filtered.sort_values("Ingevuld op", ascending=False), use_container_width=True)

            # ========== Grafiek ==========
            st.subheader("📊 Populairste voorkeuren")
            alle_voorkeuren = df_filtered["Voorkeuren"].dropna().str.cat(sep=",").split(",")
            telling = pd.Series([v.strip() for v in alle_voorkeuren if v.strip()]).value_counts()

            fig, ax = plt.subplots()
            telling.head(15).plot(kind="barh", ax=ax, edgecolor="black")
            ax.invert_yaxis()
            ax.set_title("Top 15 Populairste Diensten")
            ax.set_xlabel("Aantal voorkeuren")
            ax.set_ylabel("Dienst")
            st.pyplot(fig)

            # ========== Export ==========
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

    personeelsnummer = st.text_input("Personeelsnummer", label_visibility="collapsed", placeholder="Vul je personeelsnummer in").strip()

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
                st.success(f"👋 Welkom terug, **{naam_gevonden}**!")
            else:
                st.warning("⚠️ Personeelsnummer niet gevonden in de personeelslijst.")

    if not personeelsnummer or not personeelsnummer.isdigit() or match.empty:
        st.stop()

    # Overzichtssamenvatting bovenaan
    if naam_gevonden:
        st.markdown(f"""
        ### 📝 Overzichtssamenvatting
        - **Naam:** {naam_gevonden}  
        - **Teamcoach:** {coach_gevonden}  
        - **Personeelsnummer:** {personeelsnummer}
        """)

    bestaande_data = None
    eerder_voorkeuren = []

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

    with st.expander("👤 Jouw gegevens"):
    naam = st.text_input("Naam", value=naam_gevonden or bestaande_data.get("Naam", "") if bestaande_data else "", label_visibility="collapsed").strip()
        teamcoach = st.text_input("Teamcoach", value=coach_gevonden or bestaande_data.get("Teamcoach", "") if bestaande_data else "", label_visibility="collapsed").strip()

    st.markdown("<h3 style='color: #DAA520;'>Voor welke roosters stel je u kandidaat?</h3>", unsafe_allow_html=True)
    with st.expander("📋 Jouw dienstvoorkeuren"):
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
    if set(volgorde) != set(geselecteerd):
        volgorde = geselecteerd

    if geselecteerd:
        st.subheader("Jouw voorkeursvolgorde:")
        for i, item in enumerate(volgorde, 1):
            st.write(f"{i}. {item}")
    else:
        st.info("Selecteer eerst één of meerdere diensten om verder te gaan.")

    with st.expander("✅ Bevestiging"):
    bevestigd = st.checkbox(
        "Ik bevestig dat mijn voorkeur correct is ingevuld. Bij wijzigingen in de planning mag ik automatisch ingepland worden op basis van mijn plaatsvoorkeur binnen deze rol(len)."
    )

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
                "Bevestiging plaatsvoorkeur": "True" if bevestigd else "False",
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
s