import streamlit as st
import pandas as pd
import os
from collections import Counter
import re
from datetime import datetime

from login import require_auth
require_auth()

# -----------------------------
# PARAMÈTRES
# -----------------------------
DOC_FOLDER = "documents"    # Ton dossier de documents
REFRESH_EVERY = 3           # Auto-refresh toutes les 3 secondes

st.set_page_config(page_title="SOC - Documents", layout="wide")

st.title("📄 Suivi dynamique des documents envoyés par les PC")

# Auto-refresh
st.experimental_set_query_params(t=str(datetime.now()))
st.experimental_rerun() if "refresh" in st.session_state else st.session_state.update(refresh=True)
st_autorefresh = st.experimental_data_editor if False else None
st_autorefresh = st.empty()
st_autorefresh.empty()
st_autorefresh = st_autorefresh  # hack

# Rafraîchissement automatique
st_autorefresh = st.experimental_rerun if False else None
st_autorefresh = st.empty()
st_autorefresh.empty()

st.write(f"🔄 Rafraîchissement automatique toutes les **{REFRESH_EVERY} secondes**.")

# -----------------------------
# CHARGER LES DOCUMENTS
# -----------------------------
files = os.listdir(DOC_FOLDER)

data = []
all_words = []

for f in files:
    path = os.path.join(DOC_FOLDER, f)
    if os.path.isfile(path):
        # Extraire le nom du PC → PC01, PC02...
        pc_name = f.split("_")[0]

        # Lire contenu pour analyse des mots
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as doc:
                content = doc.read().lower()
                words = re.findall(r"\b[a-zA-Z0-9]+\b", content)
                all_words.extend(words)
        except:
            pass

        data.append({"file": f, "pc": pc_name})

df = pd.DataFrame(data)

# KPI principal
st.metric("📄 Nombre total de documents", len(df))

# -----------------------------
# GRAPHE 1 : Nombre de documents par PC
# -----------------------------
st.subheader("🖥️ Nombre de documents envoyés par PC")

if not df.empty:
    docs_by_pc = df.groupby("pc")["file"].count().reset_index().rename(columns={"file": "count"})
    st.bar_chart(docs_by_pc.set_index("pc"))
else:
    st.info("Aucun document reçu.")

# -----------------------------
# GRAPHE 2 : Mots les plus fréquents
# -----------------------------
st.subheader("🔤 Mots les plus fréquents dans les documents")

if len(all_words) > 0:
    # Compter les mots + retirer les mots vides (stop words)
    stop_words = {"le", "la", "les", "de", "du", "des", "et", "un", "une", "à", "que", "qui", "en"}
    words_filtered = [w for w in all_words if w not in stop_words and len(w) > 2]

    counter = Counter(words_filtered).most_common(10)
    words_df = pd.DataFrame(counter, columns=["mot", "count"])

    st.bar_chart(words_df.set_index("mot"))
else:
    st.info("Aucun mot analysable dans les documents.")
