import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ----------------------------------------------------
# 1. Configuration générale de la page
# ----------------------------------------------------
st.set_page_config(
    page_title="SOC Dashboard",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ SOC Dashboard")
st.markdown("Interface de supervision de sécurité (exemple pédagogique).")

# ----------------------------------------------------
# 2. Génération de données fictives (à remplacer par tes vraies données)
# ----------------------------------------------------

@st.cache_data
def generate_fake_logs(n_rows: int = 500) -> pd.DataFrame:
    np.random.seed(42)

    now = datetime.now()
    times = [now - timedelta(minutes=np.random.randint(0, 60*24)) for _ in range(n_rows)]

    severities = ["Low", "Medium", "High", "Critical"]
    sources = ["Firewall", "EDR", "Proxy", "WAF"]
    actions = ["Allowed", "Blocked", "Quarantined", "Alerted"]

    data = {
        "timestamp": times,
        "source": np.random.choice(sources, size=n_rows),
        "severity": np.random.choice(severities, size=n_rows, p=[0.4, 0.3, 0.2, 0.1]),
        "src_ip": [f"10.0.{np.random.randint(0, 10)}.{np.random.randint(1, 255)}" for _ in range(n_rows)],
        "dst_ip": [f"192.168.{np.random.randint(0, 10)}.{np.random.randint(1, 255)}" for _ in range(n_rows)],
        "action": np.random.choice(actions, size=n_rows),
        "event": np.random.choice(
            [
                "Brute force SSH",
                "Scan de port",
                "Suspicious DNS query",
                "Malware détecté",
                "Connexion RDP anormale",
                "Exfiltration potentielle"
            ],
            size=n_rows
        )
    }

    df = pd.DataFrame(data)
    df.sort_values("timestamp", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

logs_df = generate_fake_logs()

# ----------------------------------------------------
# 3. Sidebar : filtres
# ----------------------------------------------------
st.sidebar.header("🔧 Filtres")

# Filtre sur la source
all_sources = ["(Toutes)"] + sorted(logs_df["source"].unique().tolist())
selected_source = st.sidebar.selectbox("Source", all_sources)

# Filtre sur la sévérité
all_severities = logs_df["severity"].unique().tolist()
selected_severities = st.sidebar.multiselect(
    "Sévérité",
    options=all_severities,
    default=all_severities
)

# Filtre sur la plage de dates
min_date = logs_df["timestamp"].min().date()
max_date = logs_df["timestamp"].max().date()

date_range = st.sidebar.date_input(
    "Plage de dates",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(date_range, tuple):
    start_date, end_date = date_range
else:
    # Si l'utilisateur ne choisit qu'une seule date
    start_date = date_range
    end_date = date_range

# ----------------------------------------------------
# 4. Application des filtres
# ----------------------------------------------------
filtered_df = logs_df.copy()

# Filtre dates
filtered_df = filtered_df[
    (filtered_df["timestamp"].dt.date >= start_date) &
    (filtered_df["timestamp"].dt.date <= end_date)
]

# Filtre source
if selected_source != "(Toutes)":
    filtered_df = filtered_df[filtered_df["source"] == selected_source]

# Filtre sévérité
if selected_severities:
    filtered_df = filtered_df[filtered_df["severity"].isin(selected_severities)]
else:
    filtered_df = filtered_df.iloc[0:0]  # DataFrame vide si aucune sévérité sélectionnée

# ----------------------------------------------------
# 5. KPIs principaux
# ----------------------------------------------------
st.subheader("📊 Indicateurs principaux")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Alertes totales (filtrées)",
        value=len(filtered_df)
    )

with col2:
    critical_count = (filtered_df["severity"] == "Critical").sum()
    st.metric(
        label="Alertes critiques",
        value=int(critical_count)
    )

with col3:
    high_count = (filtered_df["severity"] == "High").sum()
    st.metric(
        label="Alertes élevées",
        value=int(high_count)
    )

with col4:
    distinct_src_ips = filtered_df["src_ip"].nunique()
    st.metric(
        label="IP sources distinctes",
        value=int(distinct_src_ips)
    )

# ----------------------------------------------------
# 6. Graphiques
# ----------------------------------------------------
st.subheader("📈 Visualisation des alertes")

col_left, col_right = st.columns(2)

# Alertes par sévérité
with col_left:
    st.markdown("**Répartition par sévérité**")
    if not filtered_df.empty:
        severity_counts = filtered_df["severity"].value_counts().reset_index()
        severity_counts.columns = ["severity", "count"]
        st.bar_chart(data=severity_counts, x="severity", y="count")
    else:
        st.info("Aucune donnée à afficher pour les filtres actuels.")

# Alertes dans le temps
with col_right:
    st.markdown("**Alertes dans le temps (agrégées par heure)**")
    if not filtered_df.empty:
        time_series = filtered_df.copy()
        time_series["hour"] = time_series["timestamp"].dt.floor("H")
        ts_counts = time_series.groupby("hour").size().reset_index(name="count")
        ts_counts.set_index("hour", inplace=True)
        st.line_chart(ts_counts["count"])
    else:
        st.info("Aucune donnée à afficher pour les filtres actuels.")

# ----------------------------------------------------
# 7. Top IP sources
# ----------------------------------------------------
st.subheader("🌐 Top IP sources")

if not filtered_df.empty:
    top_ips = (
        filtered_df.groupby("src_ip")
        .size()
        .reset_index(name="count")
        .sort_values("count", ascending=False)
        .head(10)
    )
    st.table(top_ips)
else:
    st.info("Aucune IP à afficher pour les filtres actuels.")

# ----------------------------------------------------
# 8. Tableau détaillé des événements
# ----------------------------------------------------
st.subheader("📜 Détails des événements")

st.caption("Les données ci-dessous sont fictives. Remplace-les par tes logs réels (SIEM, firewall, EDR...).")

if not filtered_df.empty:
    # On affiche seulement quelques colonnes pour rester lisible
    columns_to_show = ["timestamp", "source", "severity", "src_ip", "dst_ip", "action", "event"]
    st.dataframe(filtered_df[columns_to_show].sort_values("timestamp", ascending=False), use_container_width=True)
else:
    st.warning("Aucun événement ne correspond aux filtres sélectionnés.")
