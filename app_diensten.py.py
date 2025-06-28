# ====== GEBRUIKERSPAGINA ======
if not is_admin:
    st.markdown("<h1 style='color: #DAA520;'>Maak je keuze: dienstrollen</h1>", unsafe_allow_html=True)
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

    personeelsnummer = st.text_input("Personeelsnummer", placeholder="Vul hier je personeelsnummer in").strip()
    persoonlijke_code = st.text_input("Persoonlijke code (4 cijfers)", max_chars=4).strip()

    if not all([personeelsnummer.isdigit(), persoonlijke_code.isdigit(), len(persoonlijke_code) == 4]):
        st.warning("⚠️ Zorg dat je personeelsnummer en code correct zijn ingevuld (code = 4 cijfers).")
        st.stop()

    match = df_personeel[(df_personeel["personeelsnummer"] == personeelsnummer) &
                         (df_personeel["controle"] == persoonlijke_code)]
    if match.empty:
        st.warning("⚠️ Combinatie van personeelsnummer en code niet gevonden.")
        st.stop()

    naam_gevonden = match.iloc[0]["naam"]
    coach_gevonden = match.iloc[0]["teamcoach"]
    st.success(f"👋 Welkom terug, **{naam_gevonden}**!")

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
            laatst = bestaande_data.get("Laatste aanpassing", "onbekend")
            st.info(f"Eerdere inzending gevonden. Laatste wijziging op: **{laatst}**")
    except Exception as e:
        st.error(f"❌ Fout bij ophalen gegevens: {e}")

    naam = st.text_input("Naam", value=naam_gevonden or (bestaande_data.get("Naam") if bestaande_data else ""), disabled=True)
    teamcoach = st.text_input("Teamcoach", value=coach_gevonden or (bestaande_data.get("Teamcoach") if bestaande_data else ""), disabled=True)

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

    if len(set(volgorde)) != len(volgorde):
        st.error("⚠️ Elke dienst mag slechts één keer gekozen worden.")
        st.stop()

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
                "Teamcoach": teamcoach,
                "Voorkeuren": ", ".join(volgorde),
                "Bevestiging plaatsvoorkeur": "True",
                "Ingevuld op": bestaande_data.get("Ingevuld op", datetime.now().strftime("%d/%m/%Y %H:%M:%S")) if bestaande_data else datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Laatste aanpassing": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            }
            try:
                with st.spinner("Gegevens worden verwerkt..."):
                    if bestaande_data:
                        response = requests.put(f"{sheetdb_url}/Personeelsnummer/{personeelsnummer}", json={"data": resultaat})
                        st.success(f"✅ Voorkeuren van {naam} succesvol bijgewerkt.")
                    else:
                        response = requests.post(sheetdb_url, json={"data": resultaat})
                        st.success(f"✅ Bedankt {naam}, je voorkeuren zijn succesvol ingediend.")
                    response.raise_for_status()
                    with st.expander("Bekijk je ingediende gegevens"):
                        st.json(resultaat)
            except Exception as e:
                st.error(f"❌ Fout bij verzenden: {e}")
