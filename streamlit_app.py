import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Mini SOC", page_icon="🛡️", layout="wide")

st.title("🛡️ Mini SOC Dashboard")
st.write("Exemple très simple pour un projet scolaire.")

# -----------------------------
# 1. Générer un petit jeu de données fictives
# -----------------------------
now = datetime.now()
data = [
    {
        "timestamp": now - timedelta(minutes=5),
        "source": "Firewall",
        "severity": "High",
        "src_ip": "10.0.0.5",
        "dst_ip": "192.168.1.10",
        "event": "Port scan détecté"
    },
    {
        "timestamp": now - timedelta(minutes=15),
        "source": "EDR",
        "severity": "Critical",
        "src_ip": "10.0.0.8",
        "dst_ip": "192.168.1.15",
        "event": "Malware détecté"
    },
    {
        "timestamp": now - timedelta(minutes=30),
        "source": "Proxy",
        "severity": "Medium",
        "src_ip": "10.0.0.12",
        "dst_ip": "8.8.8.8",
        "event": "Requête HTTP suspecte"
    },
    {
        "timestamp": now - timedelta(hours=1),
        "source": "WAF",
        "severity": "Low",
        "src_ip": "10.0.0.20",
        "dst_ip": "192.168.1.20",
        "event": "Tentative d'accès bloquée"
    },
]

df = pd.DataFrame(data)

# -----------------------------
# 2. Filtres simples
# -----------------------------
st.sidebar.header("Filtres")

severities = ["All"] + sorted(df["severity"].unique().tolist())
selected_severity = st.sidebar.selectbox("Sévérité", severities)

if selected_severity != "All":
    df_filtered = df[df["severity"] == selected_severity]
else:
    df_filtered = df

# -----------------------------
# 3. Petits KPI
# -----------------------------
st.subheader("📊 Indicateurs")

col1, col2 = st.columns(2)

with col1:
    st.metric("Nombre d'alertes", len(df_filtered))

with col2:
    st.metric("Critiques", int((df_filtered["severity"] == "Critical").sum()))

# -----------------------------
# 4. Tableau des événements
# -----------------------------
st.subheader("📜 Détails des alertes")

st.dataframe(
    df_filtered.sort_values("timestamp", ascending=False),
    use_container_width=True
)
