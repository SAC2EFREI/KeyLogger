import streamlit as st

# --- CONFIGURATION DES IDENTIFIANTS ---
USERNAME = "admin"
PASSWORD = "password123"

def login():
    st.title("🔐 Connexion")

    username = st.text_input("Identifiant")
    password = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        if username == USERNAME and password == PASSWORD:
            st.session_state["logged_in"] = True
        else:
            st.error("Identifiants incorrects")

def require_auth():
    if "logged_in" not in st.session_state or not st.session_state["logged_in"]:
        login()
        st.stop()   # IMPORTANT : empêche d’afficher la suite si non connecté
