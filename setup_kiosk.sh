#!/bin/bash

# Script pour configurer le mode kiosque (écran plein) sur Raspberry Pi
echo "Configuration du mode kiosque pour LoRa Control Pro..."

# Vérification des privilèges
if [ "$(id -u)" -ne 0 ]; then
   echo "Ce script doit être exécuté en tant que root" 
   exit 1
fi

# Installer les paquets nécessaires
echo "Installation des paquets nécessaires..."
apt-get update
apt-get install -y chromium-browser x11-xserver-utils unclutter

# Créer le répertoire autostart s'il n'existe pas
mkdir -p /home/pi/.config/autostart

# Créer le fichier de configuration pour lancer Chromium en mode kiosque au démarrage
echo "Configuration du démarrage automatique de Chromium..."
cat > /home/pi/.config/autostart/kiosk.desktop << EOF
[Desktop Entry]
Type=Application
Name=Kiosk Mode
Exec=bash -c 'sleep 10 && /usr/bin/chromium-browser --noerrdialogs --kiosk --disable-infobars --start-fullscreen http://localhost:5000/wifi.html'
EOF

# Désactiver l'économiseur d'écran et la mise en veille de l'écran
echo "Désactivation de l'économiseur d'écran..."
cat > /home/pi/.config/autostart/disable-screensaver.desktop << EOF
[Desktop Entry]
Type=Application
Name=Disable Screensaver
Exec=xset s off -dpms
EOF

# Masquer le curseur de la souris lorsqu'inactif
echo "Configuration du curseur de la souris..."
cat > /home/pi/.config/autostart/unclutter.desktop << EOF
[Desktop Entry]
Type=Application
Name=Unclutter
Exec=unclutter -idle 0.1
EOF

# Configurer l'orientation de l'écran si nécessaire (décommenter et ajuster si besoin)
#echo "Configuring screen orientation..."
#echo "display_rotate=1" >> /boot/config.txt  # 1=90°, 2=180°, 3=270°

# Donner les bonnes permissions
chown -R pi:pi /home/pi/.config/autostart
chmod +x /home/pi/.config/autostart/kiosk.desktop
chmod +x /home/pi/.config/autostart/disable-screensaver.desktop
chmod +x /home/pi/.config/autostart/unclutter.desktop

echo ""
echo "Configuration du mode kiosque terminée!"
echo "Redémarrez le Raspberry Pi pour appliquer les changements: sudo reboot"
echo "L'interface LoRa Control Pro démarrera automatiquement en plein écran."
