import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta  # voeg timedelta hier toe
import matplotlib.pyplot as plt
import hashlib
import io
from openpyxl import Workbook

# ✅ Toegevoegde functie direct na de imports
def excel_serial_to_datetime(serial):
    try:
        serial = float(serial)
        return (datetime(1899, 12, 30) + timedelta(days=serial)).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return serial  # Laat originele waarde zien als conversie mislukt

# ====== Configuratie ======
sheetdb_url = "https://sheetdb.io/api/v1/r0nrllqfrw8v6"
google_sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTSz_OE8qzi-4J4AMEnWgXUM-HqBhiLOVxEQ36AaCzs2xCNBxbF9Hd2ZAn6NcLOKdeMXqvfuPSMI27_/pub?output=csv"

# === Lijsten met alle diensten ===
diensten_tram = [
    "T24 (Tram Laat-Vroeg groep1)", "T24 (Tram Laat-Vroeg groep2)", "T24 (Tram Laat-Vroeg groep3)",
    "T24 (Tram Laat-Vroeg groep4)", "T24 (Tram Laat-Vroeg groep5)", "T24 (Tram Laat-Vroeg groep6)",
    "TW24 (Tram Week-Week groep1)", "TW24 (Tram Week-Week groep2)", "TW24 (Tram Week-Week groep3)",
    "TW24 (Tram Week-Week groep4)", "TW24 (Tram Week-Week groep5)", "TW24 (Tram Week-Week groep6)",
    "TV12 (Tram Vroeg groep1)", "TV12 (Tram Vroeg groep2)", "TV12 (Tram Vroeg groep3)",
    "TV12 (Tram Vroeg groep4)", "TV12 (Tram Vroeg groep5)", "TV12 (Tram Vroeg groep6)",
    "TL12 (Tram Reserve groep1)", "TL12 (Tram Reserve groep2)", "TL12 (Tram Reserve groep3)",
    "TL12 (Tram Reserve groep4)", "TL12 (Tram Reserve groep5)", "TL12 (Tram Reserve groep6)",
    "TD12 (Dagdiensten Tram groep1)", "TD12 (Dagdiensten Tram groep2)", "TD12 (Dagdiensten Tram groep3)",
    "TD12 (Dagdiensten Tram groep4)", "TD12 (Dagdiensten Tram groep5)", "TD12 (Dagdiensten Tram groep6)",
    "TR15 (Tram Weekend Thuis met Onderbroken Diensten groep1)", "TR15 (Tram Weekend Thuis met Onderbroken Diensten groep2)",
    "TR15 (Tram Weekend Thuis met Onderbroken Diensten groep3)", "TR15 (Tram Weekend Thuis met Onderbroken Diensten groep4)",
    "TR15 (Tram Weekend Thuis met Onderbroken Diensten groep5)", "TR15 (Tram Weekend Thuis met Onderbroken Diensten groep6)",
    "TN24 (Late Nachtdiensten Tram groep1)", "TN24 (Late Nachtdiensten Tram groep2)", "TN24 (Late Nachtdiensten Tram groep3)",
    "TN24 (Late Nachtdiensten Tram groep4)", "TN24 (Late Nachtdiensten Tram groep5)", "TN24 (Late Nachtdiensten Tram groep6)",
    "TO15 (Onderbroken Diensten Tram groep1)", "TO15 (Onderbroken Diensten Tram groep2)", "TO15 (Onderbroken Diensten Tram groep3)",
    "TO15 (Onderbroken Diensten Tram groep4)", "TO15 (Onderbroken Diensten Tram groep5)", "TO15 (Onderbroken Diensten Tram groep6)"
]

diensten_bus = [
    "S05 (Standaardbus 5 & 33 Laat-Vroeg groep1)", "S05 (Standaardbus 5 & 33 Laat-Vroeg groep2)",
    "S05 (Standaardbus 5 & 33 Laat-Vroeg groep3)", "S05 (Standaardbus 5 & 33 Laat-Vroeg groep4)",
    "S05 (Standaardbus 5 & 33 Laat-Vroeg groep5)", "S05 (Standaardbus 5 & 33 Laat-Vroeg groep6)",
    "G09 (Gelede Bus 9 & 11 Laat-Vroeg groep1)", "G09 (Gelede Bus 9 & 11 Laat-Vroeg groep2)", "G09 (Gelede Bus 9 & 11 Laat-Vroeg groep3)",
    "G09 (Gelede Bus 9 & 11 Laat-Vroeg groep4)", "G09 (Gelede Bus 9 & 11 Laat-Vroeg groep5)", "G09 (Gelede Bus 9 & 11 Laat-Vroeg groep6)",
    "GW09 (Gelede Bus 9 & 11 Week-Week groep1)", "GW09 (Gelede Bus 9 & 11 Week-Week groep2)", "GW09 (Gelede Bus 9 & 11 Week-Week groep3)",
    "GW09 (Gelede Bus 9 & 11 Week-Week groep4)", "GW09 (Gelede Bus 9 & 11 Week-Week groep5)", "GW09 (Gelede Bus 9 & 11 Week-Week groep6)",
    "B24 (Busmix Laat-Vroeg groep1)", "B24 (Busmix Laat-Vroeg groep2)", "B24 (Busmix Laat-Vroeg groep3)",
    "B24 (Busmix Laat-Vroeg groep4)", "B24 (Busmix Laat-Vroeg groep5)", "B24 (Busmix Laat-Vroeg groep6)",
    "G70 (Gelede Bus 70 & 71 Laat-Vroeg groep1)", "G70 (Gelede Bus 70 & 71 Laat-Vroeg groep2)", "G70 (Gelede Bus 70 & 71 Laat-Vroeg groep3)",
    "G70 (Gelede Bus 70 & 71 Laat-Vroeg groep4)", "G70 (Gelede Bus 70 & 71 Laat-Vroeg groep5)", "G70 (Gelede Bus 70 & 71 Laat-Vroeg groep6)",
    "G10 (Gelede Bus 10 & 12 Laat-Vroeg groep1)", "G10 (Gelede Bus 10 & 12 Laat-Vroeg groep2)", "G10 (Gelede Bus 10 & 12 Laat-Vroeg groep3)",
    "G10 (Gelede Bus 10 & 12 Laat-Vroeg groep4)", "G10 (Gelede Bus 10 & 12 Laat-Vroeg groep5)", "G10 (Gelede Bus 10 & 12 Laat-Vroeg groep6)",
    "GW10 (Gelede Bus 10 & 12 Week-Week groep1)", "GW10 (Gelede Bus 10 & 12 Week-Week groep2)", "GW10 (Gelede Bus 10 & 12 Week-Week groep3)",
    "GW10 (Gelede Bus 10 & 12 Week-Week groep4)", "GW10 (Gelede Bus 10 & 12 Week-Week groep5)", "GW10 (Gelede Bus 10 & 12 Week-Week groep6)",
    "SW05 (Standaardbus 5 & 33 Week-Week groep1)", "SW05 (Standaardbus 5 & 33 Week-Week groep2)", "SW05 (Standaardbus 5 & 33 Week-Week groep3)",
    "SW05 (Standaardbus 5 & 33 Week-Week groep4)", "SW05 (Standaardbus 5 & 33 Week-Week groep5)", "SW05 (Standaardbus 5 & 33 Week-Week groep6)",
    "BD12 (Dagdiensten Bus groep1)", "BD12 (Dagdiensten Bus groep2)", "BD12 (Dagdiensten Bus groep3)",
    "BD12 (Dagdiensten Bus groep4)", "BD12 (Dagdiensten Bus groep5)", "BD12 (Dagdiensten Bus groep6)",
    "BR15 (Bus Weekend Thuis met Onderbroken Diensten groep1)", "BR15 (Bus Weekend Thuis met Onderbroken Diensten groep2)",
    "BR15 (Bus Weekend Thuis met Onderbroken Diensten groep3)", "BR15 (Bus Weekend Thuis met Onderbroken Diensten groep4)",
    "BR15 (Bus Weekend Thuis met Onderbroken Diensten groep5)", "BR15 (Bus Weekend Thuis met Onderbroken Diensten groep6)",
    "BN24 (Late Nachtdiensten Bus groep1)", "BN24 (Late Nachtdiensten Bus groep2)", "BN24 (Late Nachtdiensten Bus groep3)",
    "BN24 (Late Nachtdiensten Bus groep4)", "BN24 (Late Nachtdiensten Bus groep5)", "BN24 (Late Nachtdiensten Bus groep6)",
    "BO15 (Onderbroken Diensten Bus groep1)", "BO15 (Onderbroken Diensten Bus groep2)", "BO15 (Onderbroken Diensten Bus groep3)",
    "BO15 (Onderbroken Diensten Bus groep4)", "BO15 (Onderbroken Diensten Bus groep5)", "BO15 (Onderbroken Diensten Bus groep6)"
]

diensten_gemengd = [
    "MW12 (Bustrammix Weekendrol groep1)", "MW12 (Bustrammix Weekendrol groep2)", "MW12 (Bustrammix Weekendrol groep3)",
    "MW12 (Bustrammix Weekendrol groep4)", "MW12 (Bustrammix Weekendrol groep5)", "MW12 (Bustrammix Weekendrol groep6)",
    "MV12 (Bustrammix Vroeg groep1)", "MV12 (Bustrammix Vroeg groep2)", "MV12 (Bustrammix Vroeg groep3)",
    "MV12 (Bustrammix Vroeg groep4)", "MV12 (Bustrammix Vroeg groep5)", "MV12 (Bustrammix Vroeg groep6)",
    "ML12 (Bustrammix Reserve groep1)", "ML12 (Bustrammix Reserve groep2)", "ML12 (Bustrammix Reserve groep3)",
    "ML12 (Bustrammix Reserve groep4)", "ML12 (Bustrammix Reserve groep5)", "ML12 (Bustrammix Reserve groep6)",
    "M15 (Bustrammix Weekend Thuis Zonder Onderbroken Diensten groep1)", "M15 (Bustrammix Weekend Thuis Zonder Onderbroken Diensten groep2)",
    "M15 (Bustrammix Weekend Thuis Zonder Onderbroken Diensten groep3)", "M15 (Bustrammix Weekend Thuis Zonder Onderbroken Diensten groep4)",
    "M15 (Bustrammix Weekend Thuis Zonder Onderbroken Diensten groep5)", "M15 (Bustrammix Weekend Thuis Zonder Onderbroken Diensten groep6)",
    "MN24 (Late Nachtdiensten Bustrammix groep1)", "MN24 (Late Nachtdiensten Bustrammix groep2)", "MN24 (Late Nachtdiensten Bustrammix groep3)",
    "MN24 (Late Nachtdiensten Bustrammix groep4)", "MN24 (Late Nachtdiensten Bustrammix groep5)", "MN24 (Late Nachtdiensten Bustrammix groep6)"
]

# Totale lijst voor validatie
diensten = diensten_tram + diensten_bus + diensten_gemengd


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
        df["Ingevuld op"] = pd.to_datetime(df["Ingevuld op"], errors="coerce")
        df["Aantal voorkeuren"] = df["Voorkeuren"].apply(lambda x: len(str(x).split(",")))
        df["Bevestigd"] = df["Bevestiging plaatsvoorkeur"].map({"True": "✅", "False": "❌"})

        # ========== Filters ==========
        st.sidebar.header("🔎 Filters")
        zoeknummer = st.sidebar.text_input("Zoek op personeelsnummer")

        alle_voorkeuren_flat = df["Voorkeuren"].dropna().astype(str).str.cat(sep=",").split(",")
        alle_voorkeuren_flat = [v.strip() for v in alle_voorkeuren_flat if v.strip()]
        diensten_uniek = sorted(set(alle_voorkeuren_flat))

        if not diensten_uniek:
            st.warning("⚠️ Geen unieke diensten gevonden in de data.")
            st.stop()

        gekozen_diensten = st.sidebar.multiselect("Filter op dienst", diensten_uniek)

        df_filtered = df.copy()
        if zoeknummer:
            df_filtered = df_filtered[df_filtered["Personeelsnummer"].str.contains(zoeknummer.strip(), na=False)]
        if gekozen_diensten:
            df_filtered = df_filtered[df_filtered["Voorkeuren"].apply(
        lambda x: any(d == v.strip() for v in str(x).split(",") for d in gekozen_diensten)
    )]
        st.subheader("📋 Overzicht van inzendingen")
        st.dataframe(df_filtered.sort_values("Ingevuld op", ascending=False), use_container_width=True)

        # ========== Populairste diensten ==========
        st.subheader("📊 Populairste voorkeuren")
        telling = pd.Series(alle_voorkeuren_flat).value_counts()
        top15 = telling.head(15)
        fig, ax = plt.subplots()

        if not top15.empty:
            kleuren = ['#DAA520' if dienst == top15.idxmax() else '#CCCCCC' for dienst in top15.index]
            top15.plot(kind="barh", ax=ax, edgecolor="black", color=kleuren)
            ax.invert_yaxis()
            ax.set_title("Top 15 Populairste Diensten")
            ax.set_xlabel("Aantal voorkeuren")
            ax.set_ylabel("Dienst")
            st.pyplot(fig)
        else:
           st.info("📉 Nog geen voorkeuren beschikbaar voor de grafiek.")


        # ========== Overzicht per dienst ==========
        st.subheader("👥 Overzicht per dienst")

        excel_output = io.BytesIO()
        wb = Workbook()
        ws_first = True

        werkbladen_aangemaakt = False

        for dienst in diensten_uniek:
            df_dienst = df[df["Voorkeuren"].apply(
                lambda x: dienst in [v.strip() for v in str(x).split(",")]
            )].copy()

            df_dienst = df_dienst[["Personeelsnummer", "Naam"]].dropna()
            df_dienst["Personeelsnummer"] = pd.to_numeric(df_dienst["Personeelsnummer"], errors="coerce")
            df_dienst = df_dienst.dropna(subset=["Personeelsnummer"])
            df_dienst["Personeelsnummer"] = df_dienst["Personeelsnummer"].astype(int)
            df_dienst = df_dienst.sort_values("Personeelsnummer")

            st.markdown(f"### 🚌 {dienst}")
            if df_dienst.empty:
                st.info("⚠️ Geen geldige inschrijvingen gevonden.")
                continue

            werkbladen_aangemaakt = True
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

        if werkbladen_aangemaakt:
            wb.save(excel_output)
            st.download_button(
                label="📥 Download Excel-overzicht per dienst",
                data=excel_output.getvalue(),
                file_name="Overzicht_per_dienst.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("⚠️ Er werden geen werkbladen aangemaakt. Geen geldige voorkeuren gevonden.")

    except Exception as e:
        st.error(f"❌ Fout bij ophalen of verwerken gegevens: {e}")

# ====== GEBRUIKERSPAGINA ======
if not is_admin:
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

    st.markdown("<h1 style='color: #DAA520;'>Maak je keuze: dienstrollen</h1>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        personeelsnummer = st.text_input("Personeelsnummer")
    with col2:
        persoonlijke_code = st.text_input("Persoonlijke code = laatste 4 cijfers rijksregisternummer", type="password")

    if persoonlijke_code and (not persoonlijke_code.isdigit() or len(persoonlijke_code) != 4):
        st.warning("De persoonlijke code moet exact 4 cijfers bevatten.")

    if personeelsnummer and persoonlijke_code and persoonlijke_code.isdigit() and len(persoonlijke_code) == 4:
        try:
            df_personeel = pd.read_csv(google_sheet_url, dtype=str)
            df_personeel.columns = df_personeel.columns.str.strip().str.lower()
            match = df_personeel[
                (df_personeel["personeelsnummer"] == personeelsnummer) &
                (df_personeel["controle"] == persoonlijke_code)
           ]
        except Exception as e:
            st.error(f"❌ Fout bij laden van personeelsgegevens: {e}")
            st.stop()  # Stop het script als het fout gaat

    if match.empty:
        st.warning("⚠️ Combinatie van personeelsnummer en code niet gevonden.")
    else:
        naam = match.iloc[0]["naam"]
        coach = match.iloc[0]["teamcoach"]
        st.success(f"👋 Welkom terug, **{naam}**!")


        # Ophalen eerdere inzending
        bestaande_data = None
        eerdere_voorkeuren = []

    try:
        response_check = requests.get(f"{sheetdb_url}/search?Personeelsnummer={personeelsnummer}")
        gevonden = response_check.json()

        if gevonden:
            bestaande_data = gevonden[0]
            eerdere_voorkeuren = [
                v.strip()
                for v in bestaande_data.get("Voorkeuren", "").split(",")
                if v.strip()
            ]
            laatst_raw = bestaande_data.get("Laatste aanpassing", "onbekend")
            laatst = excel_serial_to_datetime(laatst_raw)
            st.info(f"Eerdere inzending gevonden. Laatste wijziging op: **{laatst}**")

    except Exception as e:
        st.error(f"❌ Fout bij laden van personeelsgegevens: {e}")

    # Check op verouderde voorkeuren
    ongeldige = [v for v in eerdere_voorkeuren if v not in diensten]
    if ongeldige:
        st.warning(f"⚠️ Volgende oude voorkeuren bestaan niet meer: {ongeldige}")
    eerdere_voorkeuren = [v for v in eerdere_voorkeuren if v in diensten]


    # Stap 1: roostertypes kiezen
    gekozen_types = st.multiselect(
        "Stap 1: Kies de type roosters waarin je diensten wilt selecteren",
        ["🚋 Tramdiensten", "🚌 Busdiensten", "🔀 Gemengde diensten"],
        default=["🚋 Tramdiensten"]
    )

    diensten_in_groep = []
    gekozen_filters = []

    if "🚋 Tramdiensten" in gekozen_types:
        st.markdown("#### 🚋 Filter tramdiensten")
        roosters_tram = st.multiselect("Kies één of meerdere tramroosters", sorted(set(d.split(" ")[0] for d in diensten_tram)), key="roosters_tram")
        groepen_tram = st.multiselect("Kies één of meerdere tramgroepen", [f"groep{i}" for i in range(1, 7)], key="groepen_tram")
        gefilterd = [
            d for d in diensten_tram
            if any(d.startswith(r) for r in roosters_tram) and any(g in d for g in groepen_tram)
        ]

        diensten_in_groep += gefilterd
        gekozen_filters.extend([f"{r} {g} (Tram)" for r in roosters_tram for g in groepen_tram])

    if "🚌 Busdiensten" in gekozen_types:
        st.markdown("#### 🚌 Filter busdiensten")
        roosters_bus = st.multiselect("Kies één of meerdere busroosters", sorted(set(d.split(" ")[0] for d in diensten_bus)), key="roosters_bus")
        groepen_bus = st.multiselect("Kies één of meerdere busgroepen", [f"groep{i}" for i in range(1, 7)], key="groepen_bus")
        gefilterd = [
            d for d in diensten_bus
            if any(d.startswith(r) for r in roosters_bus) and any(g in d for g in groepen_bus)
        ]

        diensten_in_groep += gefilterd
        gekozen_filters.extend([f"{r} {g} (Bus)" for r in roosters_bus for g in groepen_bus])

    if "🔀 Gemengde diensten" in gekozen_types:
        st.markdown("#### 🔀 Filter gemengde diensten")
        roosters_mix = st.multiselect("Kies één of meerdere gemengde roosters", sorted(set(d.split(" ")[0] for d in diensten_gemengd)), key="roosters_mix")
        groepen_mix = st.multiselect("Kies één of meerdere gemengde groepen", [f"groep{i}" for i in range(1, 7)], key="groepen_mix")
        gefilterd = [
            d for d in diensten_gemengd
            if any(d.startswith(r) for r in roosters_mix) and any(g in d for g in groepen_mix)
        ]

        diensten_in_groep += gefilterd
        gekozen_filters.extend([f"{r} {g} (Gemengd)" for r in roosters_mix for g in groepen_mix])

    diensten_in_groep = sorted(set(diensten_in_groep))
    eerder_in_groep = [v for v in eerder_voorkeuren if v in diensten_in_groep]

     # Stap 2: voorkeuren kiezen + slepen
    geselecteerd = st.multiselect(
        "Stap 2: Selecteer je voorkeuren binnen deze roosters:",
        diensten_in_groep,
        default=eerder_in_groep
    )

    volgorde = sort_items(geselecteerd, direction="vertical") if geselecteerd else eerder_in_groep
    if set(volgorde) != set(geselecteerd):
                    volgorde = geselecteerd

    if volgorde:
        st.subheader("Jouw voorkeursvolgorde:")
        for i, dienst in enumerate(volgorde, start=1):
            st.write(f"{i}. {dienst}")
    else:
        st.info("Selecteer eerst één of meerdere diensten.")

    bevestigd = st.checkbox("Ik bevestig mijn voorkeur en ga akkoord met automatische toewijzing bij wijzigingen.")

    if st.button("Verzend je antwoorden"):
        if not bevestigd:
            st.error("❌ Bevestig je voorkeur eerst.")
        elif not volgorde:
                        st.error("❌ Selecteer minstens één dienst.")
        else:
            resultaat = {
                "Personeelsnummer": personeelsnummer,
                "Naam": naam,
                "Teamcoach": coach,
                "Voorkeuren": ", ".join(volgorde),
                "Roostertype": ", ".join(gekozen_filters),
                "Bevestiging plaatsvoorkeur": "True",
                "Ingevuld op": bestaande_data.get("Ingevuld op", datetime.now().strftime("%Y-%m-%d %H:%M:%S")) if bestaande_data else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Laatste aanpassing": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            try:
                with st.spinner("Gegevens worden verwerkt..."):
                    if bestaande_data:
                        requests.put(f"{sheetdb_url}/Personeelsnummer/{personeelsnummer}", json={"data": resultaat})
                        st.success(f"✅ Voorkeuren van {naam} succesvol bijgewerkt.")
                    else:
                        requests.post(sheetdb_url, json={"data": resultaat})
                        st.success(f"✅ Bedankt {naam}, je voorkeuren zijn succesvol ingediend.")

                    with st.expander("📋 Bekijk je ingediende gegevens"):
                        st.json(resultaat)
            except Exception as e:
                st.error(f"❌ Fout bij verzenden: {e}")

