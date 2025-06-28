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

    col1, col2 = st.columns([1.5, 2])  # Verbreed linkerkolom
    with col1:
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

    with col2:
        # ... alle code van col2 blijft ongewijzigd ...

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

        personeelsnummer = st.text_input("Personeelsnummer").strip()
        persoonlijke_code = st.text_input("Persoonlijke code (4 cijfers)", max_chars=4, type="password").strip()

        if personeelsnummer and persoonlijke_code:
            match = df_personeel[(df_personeel["personeelsnummer"] == personeelsnummer) &
                                 (df_personeel["controle"] == persoonlijke_code)]
            if match.empty:
                st.warning("⚠️ Combinatie van personeelsnummer en code niet gevonden.")
                st.stop()
            else:
                naam_gevonden = match.iloc[0]["naam"]
                coach_gevonden = match.iloc[0]["teamcoach"]
                st.success(f"Welkom {naam_gevonden}!")

                try:
                    response_check = requests.get(f"{sheetdb_url}/search?Personeelsnummer={personeelsnummer}")
                    bestaande_data = response_check.json()[0] if response_check.json() else None
                except:
                    bestaande_data = None

                eerder_voorkeuren = []
                if bestaande_data and "Voorkeuren" in bestaande_data:
                    eerder_voorkeuren = [v.strip() for v in bestaande_data["Voorkeuren"].split(",") if v.strip()]

                st.markdown("---")
                st.markdown("### Selecteer jouw voorkeuren:")
                diensten = [
                    "T24 (Tram Laat-Vroeg)", "TW24 (Tram Week-Week)", "TV12 (Tram Vroeg)", "TL12 (Tram Reserve)",
                    "G09 (Gelede Bus 9 & 11 Laat-Vroeg)", "GW09 (Gelede Bus 9 & 11 Week-Week)",
                    "B24 (Busmix Laat-Vroeg)", "G70 (Gelede Bus 70 & 71 Laat-Vroeg)",
                    "G10 (Gelede Bus 10 & 12 Laat-Vroeg)", "GW10 (Gelede Bus 10 & 12 Week-Week)",
                    "S05 (Standaardbus 5 & 33 Laat-Vroeg)", "SW05 (Standaardbus 5 & 33 Week-Week)",
                    "TD12 (Dagdiensten Tram)", "BD12 (Dagdiensten Bus)", "MV12 (Bustrammix Vroeg)",
                    "ML12 (Bustrammix Reserve)", "TR15 (Tram Weekend Thuis met Onderbroken Diensten)",
                    "BR15 (Bus Weekend Thuis met Onderbroken Diensten)",
                    "M15 (Bustrammix Weekend Thuis Zonder Onderbroken Diensten)",
                    "BN24 (Late Nachtdiensten Bus)", "TN24 (Late Nachtdiensten Tram)", "MN24 (Late Nachtdiensten Bustrammix)",
                    "BO15 (Onderbroken Diensten Bus)", "TO15 (Onderbroken Diensten Tram)", "MW12 (Bustrammix Weekendrol)"
                ]

                selectie = st.multiselect("Selecteer diensten", opties=diensten, default=eerder_voorkeuren)
                volgorde = sort_items(selectie, direction="vertical") if selectie else []

                if set(volgorde) != set(selectie):
                    st.warning("⚠️ Gebruik de sorteerfunctie om je voorkeuren te rangschikken.")

                bevestiging = st.checkbox("Ik bevestig mijn voorkeuren en ga akkoord met automatische toewijzing.")
                if st.button("Verzend"):
                    if not selectie:
                        st.error("Selecteer minstens één voorkeur.")
                    elif not bevestiging:
                        st.error("Gelieve eerst te bevestigen dat je akkoord bent.")
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
                            if bestaande_data:
                                response = requests.put(f"{sheetdb_url}/Personeelsnummer/{personeelsnummer}", json={"data": resultaat})
                            else:
                                response = requests.post(sheetdb_url, json={"data": resultaat})
                            st.success("✅ Gegevens succesvol opgeslagen.")
                        except Exception as e:
                            st.error(f"Fout bij verzenden: {e}")
