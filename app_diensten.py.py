import streamlit as st
from streamlit_sortables import sort_items
import pandas as pd
import requests
from datetime import datetime
import matplotlib.pyplot as plt
import hashlib
import io
from openpyxl import Workbook
from fpdf import FPDF

# ====== Configuratie ======
sheetdb_url = "https://sheetdb.io/api/v1/r0nrllqfrw8v6"

try:
    wachtwoord_admin = st.secrets["ADMIN_WACHTWOORD"]
except KeyError:
    st.error("ADMIN_WACHTWOORD ontbreekt in je secrets.toml. Voeg dit toe.")
    st.stop()

# ====== Functies ======
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

class DienstPDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Overzicht per dienst", ln=True, align="C")

    def dienst_titel(self, dienst):
        self.ln(10)
        self.set_font("Arial", "B", 11)
        self.cell(0, 10, dienst[:50], ln=True)  # Max 50 tekens

    def dienst_tabel(self, personen):
        self.set_font("Arial", "", 10)
        self.cell(50, 8, "Personeelsnummer", border=1)
        self.cell(100, 8, "Naam", border=1, ln=True)
        for p in personen:
            self.cell(50, 8, str(p["Personeelsnummer"]), border=1)
            self.cell(100, 8, p["Naam"], border=1, ln=True)

# ====== CSS ======
st.markdown("""
    <style>
    .block-container {padding-left: 1rem !important; padding-right: 1rem !important;}
    div.stButton > button {width: 100% !important; padding: 0.75rem; font-size: 1rem;}
    @media screen and (max-width: 768px) {
        div[data-testid="stSidebar"] {display: none;}
        .block-container {padding: 0.5rem !important;}
        div.stButton > button {font-size: 0.9rem;}
        h1, h2, h3 {font-size: 1.25rem;}
    }
    </style>
""", unsafe_allow_html=True)

# ====== Admin login ======
is_admin = False
st.sidebar.header("🔐 Admin login")
password_input = st.sidebar.text_input("Admin wachtwoord", type="password")
if hash_password(password_input) == hash_password(wachtwoord_admin):
    is_admin = True

# ====== GEBRUIKERSPAGINA ======
if not is_admin:
    st.markdown("<h1 style='color: #1E90FF;'>📋 Keuzeformulier Dienstvoorkeur</h1>", unsafe_allow_html=True)

    st.info("Gelieve hieronder je voorkeuren in te vullen. De inzending wordt automatisch opgeslagen.")

    naam = st.text_input("Naam")
    personeelsnummer = st.text_input("Personeelsnummer")
    bevestiging = st.checkbox("Ik bevestig dat ik deze keuzes vrijwillig heb ingevuld")

    response = requests.get(sheetdb_url)
    response.raise_for_status()
    df = pd.DataFrame(response.json())

    try:
    alle_voorkeuren = df["Voorkeuren"].str.cat(sep=", ").split(",")
    unieke_diensten = sorted(set(v.strip() for v in alle_voorkeuren if v.strip()))
    if not unieke_diensten:
        raise ValueError
except:
    unieke_diensten = [
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

    geselecteerde_voorkeuren, _ = sort_items(unieke_diensten, direction="vertical", label="📌 Rangschik je voorkeuren")

    if st.button("✅ Verzenden"):
        if not naam or not personeelsnummer or not bevestiging or not geselecteerde_voorkeuren:
            st.warning("⚠️ Gelieve alle velden in te vullen en je voorkeuren te rangschikken.")
        else:
            payload = {
                "data": {
                    "Naam": naam,
                    "Personeelsnummer": personeelsnummer,
                    "Voorkeuren": ", ".join(geselecteerde_voorkeuren),
                    "Bevestiging plaatsvoorkeur": str(bevestiging),
                    "Ingevuld op": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                }
            }
            r = requests.post(sheetdb_url, json=payload)
            if r.status_code == 201:
                st.success("✅ Je voorkeuren werden succesvol doorgestuurd!")
            else:
                st.error("❌ Er ging iets mis bij het verzenden. Probeer opnieuw.")

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

        foutieve_datums = df[df["Ingevuld op"].isna()]
        if not foutieve_datums.empty:
            st.warning(f"⚠️ {len(foutieve_datums)} inzending(en) met foutieve of ontbrekende datum worden genegeerd in de sortering.")

        df["Aantal voorkeuren"] = df["Voorkeuren"].apply(lambda x: len(str(x).split(",")))
        df["Bevestigd"] = df["Bevestiging plaatsvoorkeur"].map({"True": "✅", "False": "❌"})

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

        pdf = DienstPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        for dienst in diensten_uniek:
            df_dienst = df[df["Voorkeuren"].apply(lambda x: dienst in [v.strip() for v in str(x).split(",")])].copy()
            df_dienst = df_dienst[["Personeelsnummer", "Naam"]].dropna()
            df_dienst["Personeelsnummer"] = pd.to_numeric(df_dienst["Personeelsnummer"], errors="coerce")
            df_dienst = df_dienst.dropna(subset=["Personeelsnummer"])
            df_dienst["Personeelsnummer"] = df_dienst["Personeelsnummer"].astype(int)
            df_dienst = df_dienst.sort_values("Personeelsnummer")

            st.markdown(f"### 🚌 {dienst}")
            if df_dienst.empty:
                st.info("⚠️ Geen geldige inschrijvingen gevonden.")
            else:
                st.dataframe(df_dienst, use_container_width=True)

                if ws_first:
                    ws = wb.active
                    ws.title = dienst[:31]
                    ws_first = False
                else:
                    ws = wb.create_sheet(title=dienst[:31])

                ws.append(["Personeelsnummer", "Naam"])
                for _, row in df_dienst.iterrows():
                    ws.append([row["Personeelsnummer"], row["Naam"]])

            pdf.dienst_titel(dienst)
            pdf.dienst_tabel(df_dienst.to_dict(orient="records"))

        wb.save(excel_output)
        st.download_button(
            label="📥 Download Excel-overzicht per dienst",
            data=excel_output.getvalue(),
            file_name="Overzicht_per_dienst.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        pdf_output = io.BytesIO()
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        pdf_output.write(pdf_bytes)
        pdf_output.seek(0)

        st.download_button(
            label="📄 Download PDF per dienst",
            data=pdf_output.getvalue(),
            file_name="Overzicht_per_dienst.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"❌ Fout bij ophalen of verwerken gegevens: {e}")
