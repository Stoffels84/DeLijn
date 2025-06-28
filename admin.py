import streamlit as st
import pandas as pd
import requests
import io
import matplotlib.pyplot as plt

# ====== Configuratie ======
sheetdb_url = "https://sheetdb.io/api/v1/r0nrllqfrw8v6"
geheime_url = "OT03PlanningGent"  # ← Pas dit aan voor je eigen beveiliging

# ====== Toegang controleren ======
query_params = st.experimental_get_query_params()
if query_params.get("admin_toegang", [""])[0] != geheime_url:
    st.error("❌ Toegang geweigerd. Deze pagina is beveiligd.")
    st.stop()

# ====== Titel ======
st.markdown("<h1 style='color: #DAA520;'>🔐 Adminoverzicht: Dienstvoorkeuren</h1>", unsafe_allow_html=True)

# ====== Gegevens ophalen ======
with st.spinner("Gegevens ophalen van SheetDB..."):
    try:
        response = requests.get(sheetdb_url)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
    except Exception as e:
        st.error(f"❌ Fout bij ophalen gegevens: {e}")
        st.stop()

# ====== Preprocessing ======
if not df.empty:
    df["Ingevuld op"] = pd.to_datetime(df["Ingevuld op"], dayfirst=True, errors="coerce")
    df["Aantal voorkeuren"] = df["Voorkeuren"].apply(lambda x: len(str(x).split(",")))

    # ====== Filters ======
    st.sidebar.header("🔎 Filters")
    coaches = sorted(df["Teamcoach"].dropna().unique())
    gekozen_coach = st.sidebar.multiselect("Filter op teamcoach", coaches, default=coaches)

    df_filtered = df[df["Teamcoach"].isin(gekozen_coach)]

    # ====== Tabelweergave ======
    st.subheader("📋 Overzicht van inzendingen")
    st.dataframe(df_filtered.sort_values("Ingevuld op", ascending=False), use_container_width=True)

    # ====== Samenvatting per dienst ======
    st.subheader("📊 Populairste voorkeuren")
    alle_voorkeuren = df_filtered["Voorkeuren"].dropna().str.cat(sep=",").split(",")
    telling = pd.Series([v.strip() for v in alle_voorkeuren if v.strip()]).value_counts()

    fig, ax = plt.subplots()
    telling.head(15).plot(kind="barh", ax=ax)
    ax.invert_yaxis()
    ax.set_xlabel("Aantal voorkeuren")
    ax.set_ylabel("Dienst")
    st.pyplot(fig)

    # ====== Exportfunctie ======
    st.subheader("📤 Exporteer overzicht")
    csv = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button("Download als CSV", data=csv, file_name="dienstvoorkeuren_adminoverzicht.csv", mime="text/csv")
else:
    st.info("Er zijn nog geen inzendingen beschikbaar.")
s