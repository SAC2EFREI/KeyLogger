# ultimate_tracker_with_clean_log.py
# → Affichage live + fichier log PROPRE et lisible automatiquement
import os
import tkinter as tk
from tkinter import scrolledtext
import pyperclip
from pynput import keyboard, mouse
from threading import Thread
import datetime

# ==================== CHEMINS DES FICHIERS ====================
HOME = os.path.expanduser("~")
DOSSIER = os.path.join(HOME, "TrackerLogs")
os.makedirs(DOSSIER, exist_ok=True)  # crée le dossier s'il n'existe pas

FICHIER_BRUT = os.path.join(DOSSIER, "live_brut.txt")        # tout ce que tu vois dans la fenêtre
FICHIER_PROPRE = os.path.join(DOSSIER, "journal_propre.txt") # version lisible, sans les [MOUSE MOVE] toutes les ms

# ==================== TKINTER ====================
root = tk.Tk()
root.title("ULTIMATE TRACKER 2025 - Live + Logs propres")
root.geometry("1250x800")
root.configure(bg="#0a0a0a")

tk.Label(root, text="TOUT EST ENREGISTRÉ", font=("Hack", 26, "bold"),
         fg="#ff0066", bg="#0a0a0a").pack(pady=15)

zone = scrolledtext.ScrolledText(root, font=("Consolas", 11), bg="#000000",
                                 fg="#00ffaa", insertbackground="#00ffaa")
zone.pack(fill="both", expand=True, padx=16, pady=10)

status = tk.Label(root, text="Démarrage...", fg="#00ffaa", bg="#0a0a0a", font=12)
status.pack(side="bottom", pady=12)

# ==================== DÉBUT SESSION ====================
debut = datetime.datetime.now()
zone.insert(tk.END, "╔" + "═"*96 + "╗\n")
zone.insert(tk.END, f"   ULTIMATE TRACKER DÉMARRÉ → {debut:%Y-%m-%d %H:%M:%S}\n")
zone.insert(tk.END, f"   Dossier logs : {DOSSIER}\n")
zone.insert(tk.END, "╚" + "═"*96 + "╝\n\n")
zone.see(tk.END)

# Écriture d'en-tête dans les deux fichiers
with open(FICHIER_BRUT, "a", encoding="utf-8") as f:
    f.write(f"\n\n=== NOUVELLE SESSION : {debut} ===\n")
with open(FICHIER_PROPRE, "a", encoding="utf-8") as f:
    f.write(f"\n\n═════ NOUVELLE SESSION ═════\n")
    f.write(f"Début : {debut:%d/%m/%Y à %H:%M:%S}\n")
    f.write(f"════════════════{'═'*len(str(debut))}\n\n")

# ==================== FONCTIONS D'ÉCRITURE ====================
def ecrire_brut(texte):
    zone.insert(tk.END, texte)
    zone.see(tk.END)
    with open(FICHIER_BRUT, "a", encoding="utf-8") as f:
        f.write(texte)

def ecrire_propre(texte):
    with open(FICHIER_PROPRE, "a", encoding="utf-8") as f:
        f.write(texte + "\n")

# ==================== CLAVIER ====================
def on_press(key):
    try:
        if hasattr(key, 'char') and key.char:
            char = key.char
            ecrire_brut(char)
            ecrire_propre(char)
        else:
            mapping = {
                keyboard.Key.space: (" ", " "),
                keyboard.Key.enter: ("\n", "\n"),
                keyboard.Key.tab: ("    ", "    "),
                keyboard.Key.backspace: (" [BACKSPACE] ", "[BACKSPACE]"),
                keyboard.Key.delete: (" [SUPPR] ", "[SUPPR]"),
                keyboard.Key.esc: (" [ESC] ", " [ESC]"),
            }
            brut, propre = mapping.get(key, (f" [{str(key).split('.')[-1].upper()}] ", f" [{str(key).split('.')[-1].upper()}]"))
            ecrire_brut(brut)
            if propre.strip():
                ecrire_propre(propre)
    except: pass

# ==================== SOURIS ====================
dernier_move = None
def on_move(x, y):
    global dernier_move
    # On n'enregistre les mouvements que toutes les 15 pixels pour éviter le spam
    if dernier_move is None or abs(x - dernier_move[0]) > 15 or abs(y - dernier_move[1]) > 15:
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        msg = f" [MOUSE → ({x}, {y})]"
        ecrire_brut(msg)
        dernier_move = (x, y)

def on_click(x, y, button, pressed):
    if not pressed: return  # on ne garde que les clics pressés
    btn = {mouse.Button.left: "GAUCHE", mouse.Button.right: "DROIT", mouse.Button.middle: "MILIEU"}.get(button, button)
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    msg = f"\n[CLIC {btn} @ ({x},{y}) - {ts}]\n"
    ecrire_brut(msg)
    ecrire_propre(f"→ Clic {btn} en ({x}, {y}) à {ts}")

def on_scroll(x, y, dx, dy):
    direction = "↑" if dy > 0 else "↓" if dy < 0 else "horizontal"
    msg = f" [SCROLL {direction} @ ({x},{y})]"
    ecrire_brut(msg)
    ecrire_propre(f"→ Molette {direction} en ({x}, {y})")

# ==================== PRESSE-PAPIERS ====================
dernier_clip = ""
def clipboard_loop():
    global dernier_clip
    while True:
        try:
            actuel = pyperclip.paste()
            if actuel != dernier_clip and actuel and len(actuel) < 10000:
                ts = datetime.datetime.now().strftime("%H:%M:%S")
                sep = "─"*80
                msg = f"\n\n[CLIPBOARD {ts}]\n┌{sep}\n{actuel}\n└{sep}\n\n"
                ecrire_brut(msg)
                ecrire_propre(f"\n[CLIPBOARD copié à {ts}]")
                ecrire_propre(actuel.strip()[:500])  # on limite pour la lisibilité
                if len(actuel) > 500:
                    ecrire_propre(" [...]")
                dernier_clip = actuel
        except: pass
        time.sleep(2)

# ==================== LANCEMENT ====================
Thread(target=clipboard_loop, daemon=True).start()

mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll).start()
keyboard.Listener(on_press=on_press).start()

def on_close():
    fin = datetime.datetime.now()
    duree = fin - debut
    summary = f"\nSession terminée à {fin:%H:%M:%S} (durée : {duree})\n"
    ecrire_brut(summary)
    with open(FICHIER_BRUT, "a", encoding="utf-8") as f:
        f.write(summary + "═"*100 + "\n\n")
    with open(FICHIER_PROPRE, "a", encoding="utf-8") as f:
        f.write(f"\nFin de session : {fin:%d/%m/%Y à %H:%M:%S}\n")
        f.write(f"Durée totale : {duree}\n{'═'*50}\n\n")
    status.config(text=f"Terminé • Logs → {DOSSIER}")
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
status.config(text=f"TOUT EST ENREGISTRÉ → {DOSSIER}")

root.mainloop()
