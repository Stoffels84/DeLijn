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
        persoonlijke_code = st.text_input("Persoonlijke code (4 cijfers)", type="password")

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

            if match.empty:
                st.warning("⚠️ Combinatie van personeelsnummer en code niet gevonden.")
            else:
                naam = match.iloc[0]["naam"]
                coach = match.iloc[0]["teamcoach"]
                st.success(f"👋 Welkom terug, **{naam}**!")

                # Ophalen eerdere inzending
                bestaande_data = None
                eerder_voorkeuren = []
                response_check = requests.get(f"{sheetdb_url}/search?Personeelsnummer={personeelsnummer}")
                gevonden = response_check.json()
                if gevonden:
                    bestaande_data = gevonden[0]
                    eerder_voorkeuren = [v.strip() for v in bestaande_data.get("Voorkeuren", "").split(",") if v.strip()]
                    laatst = bestaande_data.get("Laatste aanpassing", "onbekend")
                    st.info(f"Eerdere inzending gevonden. Laatste wijziging op: **{laatst}**")

                # Check op verouderde voorkeuren
                ongeldige = [v for v in eerder_voorkeuren if v not in diensten]
                if ongeldige:
                    st.warning(f"⚠️ Volgende oude voorkeuren bestaan niet meer: {ongeldige}")
                eerder_voorkeuren = [v for v in eerder_voorkeuren if v in diensten]

                # Stap 1: rooster kiezen
                roosteropties = {
                    "🚋 Tramrooster": diensten_tram,
                    "🚌 Busrooster": diensten_bus,
                    "🔀 Gemengd rooster": diensten_gemengd
                }

                gekozen_rooster = st.selectbox("Stap 1: Kies je type rooster", list(roosteropties.keys()))
                diensten_in_groep = sorted(roosteropties[gekozen_rooster])
                eerder_in_groep = [v for v in eerder_voorkeuren if v in diensten_in_groep]

                # Stap 2: voorkeuren kiezen + slepen
                geselecteerd = st.multiselect(
                    "Stap 2: Selecteer je voorkeuren binnen dit rooster:",
                    opties := diensten_in_groep,
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
                            "Roostertype": gekozen_rooster,
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
        except Exception as e:
            st.error(f"❌ Fout bij laden van personeelsgegevens: {e}")

