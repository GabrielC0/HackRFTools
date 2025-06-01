# /home/pi/lorareplay/replay.py

import sys
import subprocess
import os

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 replay.py <letter>")
        sys.exit(1)
    letter = sys.argv[1].upper()
    folder = "1"  # Dossier par défaut
    base_path = f"/home/pi/lorareplay/signals/frequences/{folder}/"
    # Recherche stricte du fichier sans gestion d'espaces ou de casse
    filepath = f"{base_path}{letter}.C16"
    if not os.path.exists(filepath):
        print(f"Erreur: Fichier {letter}.C16 introuvable dans le dossier {folder}")
        sys.exit(1)
    sample_rate = 500000
    center_frequency = 434000000
    print(f"Envoi du signal {filepath} avec:")
    print(f"- Fréquence: {center_frequency} Hz")
    print(f"- Taux d'échantillonnage: {sample_rate} Hz")
    try:
        subprocess.run([
            "hackrf_transfer",
            "-t", filepath,
            "-f", str(center_frequency),
            "-s", str(sample_rate),
            "-x", "47",
            "-F"
        ], check=True)
    except Exception as e:
        print("Erreur lors de l'envoi :", e)

if __name__ == "__main__":
    main()
