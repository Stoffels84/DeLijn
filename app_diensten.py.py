import streamlit as st
from streamlit_sortables import sort_items
import pandas as pd
import requests
from datetime import datetime
import matplotlib.pyplot as plt
import hashlib
import io
from openpyxl import Workbook

# ====== Configuratie ======
sheetdb_url = "https://sheetdb.io/api/v1/r0nrllqfrw8v6"
google_sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTSz_OE8qzi-4J4AMEnWgXUM-HqBhiLOVxEQ36AaCzs2xCNBxbF9Hd2ZAn6NcLOKdeMXqvfuPSMI27_/pub?output=csv"

try:
    wachtwoord_admin = st.secrets["ADMIN_WACHTWOORD"]
except KeyError:
    st.error("ADMIN_WACHTWOORD ontbreekt in je secrets.toml. Voeg dit toe.")
    st.stop()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ====== CSS ======
st.markdown("""
    <style>
    .block-container {padding-left: 1rem !important; padding-right: 1rem !important;}
    div.stButton > button {width: 100% !important; padding: 0.75rem; font-size: 1rem;}
    </style>
""", unsafe_allow_html=True)

# ====== Admin login ======
is_admin = False
st.sidebar.header("🔐 Admin login")
password_input = st.sidebar.text_input("Admin wachtwoord", type="password")
if hash_password(password_input) == hash_password(wachtwoord_admin):
    is_admin = True

# ====== ADMINPAGINA ======
if is_admin:
    st.markdown("<h1 style='color: #DAA520;'>🔐 Adminoverzicht: Dienstvoorkeuren</h1>", unsafe_allow_html=True)

    try:
        response = requests.get(sheetdb_url)
        response.raise_for_status()
        df = pd.DataFrame(response.json())

        if df.empty:
            st.info("Er zijn nog geen inzendingen.")
            st.stop()

        df["Voorkeuren"] = df["Voorkeuren"].fillna("")
        df["Personeelsnummer"] = df["Personeelsnummer"].astype(str).str.strip()
        df["Ingevuld op"] = pd.to_datetime(df["Ingevuld op"], dayfirst=True, errors="coerce")
        df["Aantal voorkeuren"] = df["Voorkeuren"].apply(lambda x: len(str(x).split(",")))
        df["Bevestigd"] = df["Bevestiging plaatsvoorkeur"].map({"True": "✅", "False": "❌"})

        # Filteren op personeelsnummer en dienst
        st.sidebar.header("🔎 Filters")
        zoeknummer = st.sidebar.text_input("Zoek op personeelsnummer")
        alle_voorkeuren = df["Voorkeuren"].str.cat(sep=", ").split(",")
        diensten_uniek = sorted(set(v.strip() for v in alle_voorkeuren if v.strip()))
        gekozen_diensten = st.sidebar.multiselect("Filter op dienst", diensten_uniek)

        df_filtered = df.copy()
        if zoeknummer:
            df_filtered = df_filtered[df_filtered["Personeelsnummer"].str.contains(zoeknummer.strip(), na=False)]
        if gekozen_diensten:
            df_filtered = df_filtered[df_filtered["Voorkeuren"].apply(lambda x: any(d in x for d in gekozen_diensten))]

        st.subheader("📋 Overzicht van inzendingen")
        st.dataframe(df_filtered.sort_values("Ingevuld op", ascending=False), use_container_width=True)

        st.subheader("📊 Populairste voorkeuren")
        telling = pd.Series([v.strip() for v in alle_voorkeuren if v.strip()]).value_counts()
        fig, ax = plt.subplots()
        top15 = telling.head(15)
        kleuren = ['#DAA520' if dienst == top15.idxmax() else '#CCCCCC' for dienst in top15.index]
        top15.plot(kind="barh", ax=ax, edgecolor="black", color=kleuren)
        ax.invert_yaxis()
        ax.set_title("Top 15 Populairste Diensten")
        ax.set_xlabel("Aantal voorkeuren")
        ax.set_ylabel("Dienst")
        st.pyplot(fig)

        st.subheader("👥 Overzicht per dienst")

        excel_output = io.BytesIO()
        wb = Workbook()
        ws_first = True

        for dienst in diensten_uniek:
            df_dienst = df[df["Voorkeuren"].str.contains(dienst, na=False)].copy()
            df_dienst = df_dienst[["Personeelsnummer", "Naam"]].dropna()
            df_dienst["Personeelsnummer"] = pd.to_numeric(df_dienst["Personeelsnummer"], errors="coerce")
            df_dienst = df_dienst.dropna(subset=["Personeelsnummer"])
            df_dienst["Personeelsnummer"] = df_dienst["Personeelsnummer"].astype(int)
            df_dienst = df_dienst.sort_values("Personeelsnummer")

            st.markdown(f"### 🚌 {dienst}")
            if df_dienst.empty:
                st.info("⚠️ Geen geldige inschrijvingen gevonden.")
                continue

            st.dataframe(df_dienst, use_container_width=True)

            titel = dienst[:31]
            if ws_first:
                ws = wb.active
                ws.title = titel
                ws_first = False
            else:
                ws = wb.create_sheet(title=titel)

            ws.append(["Personeelsnummer", "Naam"])
            for _, row in df_dienst.iterrows():
                ws.append([row["Personeelsnummer"], row["Naam"]])

        wb.save(excel_output)
        st.download_button(
            label="📥 Download Excel-overzicht per dienst",
            data=excel_output.getvalue(),
            file_name="Overzicht_per_dienst.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Fout bij ophalen of verwerken gegevens: {e}")

# ====== GEBRUIKERSPAGINA ======
if not is_admin:
    st.markdown("<h1 style='color: #DAA520;'>Maak je keuze: dienstrollen</h1>", unsafe_allow_html=True)

    st.info("""
    ### ℹ️ Uitleg
    Je kan enkel een dienstrol kiezen waarvoor je gekwalificeerd bent of ingepland werd. Bij gemengde rollen mag je kiezen als je bereid bent de tweede kwalificatie te behalen.
    """)

    personeelsnummer = st.text_input("Personeelsnummer")
    persoonlijke_code = st.text_input("Persoonlijke code (4 cijfers)", type="password")

    if persoonlijke_code and (not persoonlijke_code.isdigit() or len(persoonlijke_code) != 4):
        st.warning("De persoonlijke code moet exact 4 cijfers bevatten.")

    if personeelsnummer and persoonlijke_code and persoonlijke_code.isdigit() and len(persoonlijke_code) == 4:
        try:
            df_personeel = pd.read_csv(google_sheet_url, dtype=str)
            df_personeel.columns = df_personeel.columns.str.strip().str.lower()
            match = df_personeel[(df_personeel["personeelsnummer"] == personeelsnummer) &
                                 (df_personeel["controle"] == persoonlijke_code)]

            if match.empty:
                st.warning("⚠️ Combinatie van personeelsnummer en code niet gevonden.")
            else:
                naam = match.iloc[0]["naam"]
                coach = match.iloc[0]["teamcoach"]
                st.success(f"👋 Welkom terug, **{naam}**!")

                bestaande_data = None
                eerder_voorkeuren = []
                response_check = requests.get(f"{sheetdb_url}/search?Personeelsnummer={personeelsnummer}")
                gevonden = response_check.json()
                if gevonden:
                    bestaande_data = gevonden[0]
                    eerder_voorkeuren = [v.strip() for v in bestaande_data.get("Voorkeuren", "").split(",") if v.strip()]
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
                            "Naam": naam,
                            "Teamcoach": coach,
                            "Voorkeuren": ", ".join(volgorde),
                            "Bevestiging plaatsvoorkeur": "True",
                            "Ingevuld op": bestaande_data.get("Ingevuld op", datetime.now().strftime("%d/%m/%Y %H:%M:%S")) if bestaande_data else datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                            "Laatste aanpassing": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                        }
                        try:
                            with st.spinner("Gegevens worden verwerkt..."):
                                if bestaande_data:
                                    requests.put(f"{sheetdb_url}/Personeelsnummer/{personeelsnummer}", json={"data": resultaat})
                                    st.success(f"✅ Voorkeuren van {naam} succesvol bijgewerkt.")
                                else:
                                    requests.post(sheetdb_url, json={"data": resultaat})
                                    st.success(f"✅ Bedankt {naam}, je voorkeuren zijn succesvol ingediend.")
                                with st.expander("Bekijk je ingediende gegevens"):
                                    st.json(resultaat)
                        except Exception as e:
                            st.error(f"❌ Fout bij verzenden: {e}")
        except Exception as e:
            st.error(f"❌ Fout bij laden van personeelsgegevens: {e}")
