# LoRa Control Pro

Interface de contrôle tactile pour Raspberry Pi permettant de gérer le WiFi et d'envoyer des signaux avec HackRF.

## Fonctionnalités

- Interface tactile moderne avec animations et effets visuels
- Affichage de l'adresse IP du Raspberry Pi
- Gestion des connexions WiFi (scan, connexion, déconnexion)
- Envoi de signaux avec HackRF
- Démarrage automatique au boot en mode kiosque
- Compatible avec les écrans tactiles

## Installation

1. Clonez ce dépôt dans le répertoire home de votre Raspberry Pi:

   ```
   git clone https://github.com/votre-utilisateur/lorareplay.git
   ```

2. Installez les dépendances:

   ```
   sudo apt-get update
   sudo apt-get install python3-flask
   ```

3. Exécutez le script d'installation pour configurer le service:

   ```
   cd /home/pi/lorareplay
   sudo ./install.sh
   ```

4. (Optionnel) Pour configurer le mode kiosque en plein écran:

   ```
   sudo ./setup_kiosk.sh
   ```

5. Redémarrez votre Raspberry Pi:
   ```
   sudo reboot
   ```

## Utilisation

Une fois installé, l'application démarrera automatiquement et sera accessible:

- Localement sur le Raspberry Pi à l'adresse: http://localhost
- Depuis un autre appareil sur le réseau à l'adresse: http://[IP_DU_RASPBERRY]

L'interface offre deux écrans principaux:

- **Contrôle LoRa**: Pour envoyer des signaux avec HackRF
- **Gestion WiFi**: Pour gérer les connexions sans fil

## Structure des fichiers

- `server.py` - Serveur Flask principal
- `templates/` - Fichiers HTML des pages
- `static/` - Fichiers CSS et JavaScript
- `install.sh` - Script d'installation du service
- `setup_kiosk.sh` - Script de configuration du mode kiosque
- `lorareplay.service` - Fichier de configuration du service systemd

## Crédits

Développé par [Votre Nom] pour le contrôle de dispositifs LoRa avec HackRF.

## Licence

[Spécifiez votre licence ici]
# HackRFTools
