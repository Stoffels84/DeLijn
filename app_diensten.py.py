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

            # Filter op teamcoach
            coaches = sorted(df["Teamcoach"].dropna().unique())
            gekozen_coach = st.sidebar.multiselect("Filter op teamcoach", coaches, default=coaches)

            # Filter op personeelsnummer
            zoeknummer = st.sidebar.text_input("Zoek op personeelsnummer (volledig of gedeeltelijk)")

            # Filter op dienstvoorkeur
            alle_voorkeuren_flat = df["Voorkeuren"].dropna().str.cat(sep=",").split(",")
            diensten_uniek = sorted(set(v.strip() for v in alle_voorkeuren_flat if v.strip()))
            gekozen_diensten = st.sidebar.multiselect("Filter op dienst", diensten_uniek)

            # ========== Filters toepassen ==========
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
            telling.head(15).plot(kind="barh", ax=ax)
            ax.invert_yaxis()
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
