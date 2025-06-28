import streamlit as st
from streamlit_sortables import sort_items
import pandas as pd
import requests
from datetime import datetime
import matplotlib.pyplot as plt
import hashlib
import smtplib
from email.mime.text import MIMEText

# ====== Configuratie ======
sheetdb_url = "https://sheetdb.io/api/v1/r0nrllqfrw8v6"
google_sheet_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTSz_OE8qzi-4J4AMEnWgXUM-HqBhiLOVxEQ36AaCzs2xCNBxbF9Hd2ZAn6NcLOKdeMXqvfuPSMI27_/pub?output=csv"
wachtwoord_admin = "OTGentPlanning"

smtp_server = "smtp.gmail.com"
smtp_port = 587
smtp_user = "no.reply.de.lijn.9050@gmail.com"
smtp_password = "btsz olze cgdh kygp"
ontvanger_email = "29076@delijn.be"  # fallback

# ====== Functie voor wachtwoordhashing ======
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# ====== Functie om e-mail te verzenden ======
def verzend_email(naam, personeelsnummer, teamcoach, voorkeuren, timestamp):
    coach_emails = {
        "Lien": "lien@delijn.be",
        "Bart": "bart@delijn.be",
        "Sofie": "sofie@delijn.be",
        "Tom": "tom@delijn.be",
        # Voeg meer teamcoaches toe indien nodig
    }
    ontvanger = coach_emails.get(teamcoach, ontvanger_email)
    onderwerp = f"Nieuwe dienstvoorkeur van {naam}"
    inhoud = f"""
Naam: {naam}
Personeelsnummer: {personeelsnummer}
Teamcoach: {teamcoach}

Voorkeursvolgorde:
{chr(10).join(f"{i+1}. {v}" for i, v in enumerate(voorkeuren))}

Ingevuld op: {timestamp}
"""
    msg = MIMEText(inhoud)
    msg["Subject"] = onderwerp
    msg["From"] = smtp_user
    msg["To"] = ontvanger

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
    except Exception as e:
        st.warning(f"📧 Kon geen e-mail verzenden: {e}")

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

# ====== ADMIN ======
if is_admin:
    st.markdown("<h1 style='color: #DAA520;'>🔐 Adminoverzicht: Dienstvoorkeuren</h1>", unsafe_allow_html=True)
    try:
        response = requests.get(sheetdb_url)
        response.raise_for_status()
        df = pd.DataFrame(response.json())

        if not df.empty:
            df["Ingevuld op"] = pd.to_datetime(df["Ingevuld op"], dayfirst=True, errors="coerce")
            df["Aantal voorkeuren"] = df["Voorkeuren"].apply(lambda x: len(str(x).split(",")))

            st.sidebar.header("🔎 Filters")
            coaches = sorted(df["Teamcoach"].dropna().unique())
            gekozen_coach = st.sidebar.multiselect("Filter op teamcoach", coaches, default=coaches)
            zoeknummer = st.sidebar.text_input("Zoek op personeelsnummer")
            alle_voorkeuren = df["Voorkeuren"].dropna().str.cat(sep=",").split(",")
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

            st.subheader("📤 Exporteer overzicht")
            csv = df_filtered.to_csv(index=False).encode("utf-8")
            st.download_button("Download als CSV", data=csv, file_name="dienstvoorkeuren_admin.csv", mime="text/csv")

        else:
            st.info("Er zijn nog geen inzendingen.")
    except Exception as e:
        st.error(f"❌ Fout bij ophalen gegevens: {e}")

# ====== GEBRUIKERSPAGINA ======
else:
    st.markdown("<h1 style='color: #DAA520;'>Maak je keuze: dienstrollen</h1>", unsafe_allow_html=True)
    df_personeel = pd.read_csv(google_sheet_url, dtype=str)
    df_personeel.columns = df_personeel.columns.str.strip().str.lower()

    personeelsnummer = st.text_input("Personeelsnummer", placeholder="Vul je personeelsnummer in").strip()
    persoonlijke_code = st.text_input("Persoonlijke code (4 cijfers)", max_chars=4).strip()

    naam_gevonden = ""
    coach_gevonden = ""
    match = pd.DataFrame()

    if personeelsnummer and persoonlijke_code:
        if not personeelsnummer.isdigit():
            st.warning("⚠️ Het personeelsnummer moet enkel cijfers bevatten.")
        else:
            match = df_personeel[
                (df_personeel["personeelsnummer"] == personeelsnummer) &
                (df_personeel["controle"] == persoonlijke_code)
            ]
            if not match.empty:
                naam_gevonden = match.iloc[0]["naam"]
                coach_gevonden = match.iloc[0]["teamcoach"]
                st.success(f"👋 Welkom terug, **{naam_gevonden}**!")
            else:
                st.warning("⚠️ Combinatie van personeelsnummer en code niet gevonden.")

    if not personeelsnummer or not persoonlijke_code or not personeelsnummer.isdigit() or match.empty:
        st.stop()

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
            voorkeur_string = bestaande_data.get("Voorkeuren", "")
            eerder_voorkeuren = [v.strip() for v in voorkeur_string.split(",") if v.strip()]
            st.info("Eerdere inzending gevonden. Je kan nu bewerken.")
    except Exception as e:
        st.error(f"❌ Fout bij ophalen gegevens: {e}")

    with st.expander("👤 Jouw gegevens"):
        naam = st.text_input("Naam", value=naam_gevonden or bestaande_data.get("Naam", "") if bestaande_data else "").strip()
        teamcoach = st.text_input("Teamcoach", value=coach_gevonden or bestaande_data.get("Teamcoach", "") if bestaande_data else "").strip()

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

    with st.expander("✅ Bevestiging"):
        bevestigd = st.checkbox("Ik bevestig mijn voorkeur en ga akkoord met automatische toewijzing bij wijzigingen.")

    if st.button("Verzend je antwoorden"):
        if not bevestigd:
            st.error("Bevestig je voorkeur eerst.")
        elif not personeelsnummer or not naam or not teamcoach or not volgorde:
            st.error("Vul alle verplichte velden in.")
        else:
            resultaat = {
                "Personeelsnummer": personeelsnummer,
                "Naam": naam,
                "Teamcoach": teamcoach,
                "Voorkeuren": ", ".join(volgorde),
                "Bevestiging plaatsvoorkeur": "True",
                "Ingevuld op": bestaande_data.get("Ingevuld op", datetime.now().strftime("%d/%m/%Y %H:%M:%S")),
                "Laatste aanpassing": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
            try:
                with st.spinner("Gegevens worden verwerkt..."):
                    if bestaande_data:
                        response = requests.put(f"{sheetdb_url}/Personeelsnummer/{personeelsnummer}", json={"data": resultaat})
                    else:
                        response = requests.post(sheetdb_url, json={"data": resultaat})
                    response.raise_for_status()
                    st.success(f"Bedankt {naam}, je voorkeuren zijn opgeslagen!")
                    verzend_email(naam, personeelsnummer, teamcoach, volgorde, resultaat["Laatste aanpassing"])
                    with st.expander("Bekijk je ingediende gegevens"):
                        st.json(resultaat)
            except Exception as e:
                st.error(f"❌ Fout bij verzenden: {e}")
