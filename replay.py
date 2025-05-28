# /home/pi/lorareplay/replay.py

import sys
import subprocess
import os

def read_signal_params(txt_file_path):
    """Lit les paramètres sample_rate et center_frequency depuis un fichier .TXT"""
    default_params = {
        "sample_rate": 2000000,  # Minimum requis par HackRF
        "center_frequency": 433920000
    }
    
    if not os.path.exists(txt_file_path):
        return default_params
    
    try:
        params = default_params.copy()
        with open(txt_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    if key == 'sample_rate':
                        # Assurer un minimum de 2 MHz même si le fichier spécifie moins
                        params['sample_rate'] = max(int(value), 2000000)
                    elif key == 'center_frequency':
                        params['center_frequency'] = int(value)
        return params
    except Exception as e:
        print(f"Erreur lors de la lecture des paramètres: {e}")
        return default_params

if len(sys.argv) != 2:
    print("Usage: python3 replay.py <letter>")
    sys.exit(1)

letter = sys.argv[1].upper()
folder = "1"  # Dossier par défaut
filepath = f"/home/pi/lorareplay/signals/frequences/{folder}/{letter}.C16"

# Gérer le cas particulier des noms de fichiers avec espaces
if not os.path.exists(filepath):
    # Essayer avec un espace après la lettre
    filepath = f"/home/pi/lorareplay/signals/frequences/{folder}/{letter} .C16"
    if not os.path.exists(filepath):
        print(f"Erreur: Fichier {letter}.C16 introuvable dans le dossier {folder}")
        sys.exit(1)

# Trouver le fichier .TXT correspondant
txt_filepath = filepath.replace(".C16", ".TXT")
if not os.path.exists(txt_filepath):
    txt_filepath = filepath.replace(".C16", ".txt")  # Essayer avec une extension en minuscules

# Lire les paramètres
params = read_signal_params(txt_filepath)

print(f"Envoi du signal {filepath} avec:")
print(f"- Fréquence: {params['center_frequency']} Hz")
print(f"- Taux d'échantillonnage: {params['sample_rate']} Hz")

try:
    subprocess.run([
        "hackrf_transfer",
        "-t", filepath,
        "-f", str(params['center_frequency']),
        "-s", str(params['sample_rate']),
        "-x", "47",
        "-F"  # Force l'utilisation de paramètres hors plage
    ])
except Exception as e:
    print("Erreur lors de l'envoi :", e)
