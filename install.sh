#!/bin/bash

# Script d'installation pour LoRa Control Pro
echo "Installation de LoRa Control Pro..."

# Vérification des privilèges
if [ "$(id -u)" -ne 0 ]; then
   echo "Ce script doit être exécuté en tant que root" 
   exit 1
fi

# Création du fichier service systemd
echo "Configuration du service systemd..."
cp /home/pi/lorareplay/lorareplay.service /etc/systemd/system/
chmod 644 /etc/systemd/system/lorareplay.service

# Attribution des permissions
echo "Configuration des permissions..."
chown -R pi:pi /home/pi/lorareplay
chmod +x /home/pi/lorareplay/server.py

# Activation et démarrage du service
echo "Activation du service..."
systemctl daemon-reload
systemctl enable lorareplay.service
systemctl start lorareplay.service

# Vérification du statut
echo "Vérification du statut du service..."
systemctl status lorareplay.service

echo ""
echo "Installation terminée!"
echo "L'interface LoRa Control Pro démarrera automatiquement au démarrage."
echo "Vous pouvez accéder à l'interface à l'adresse: http://[IP_RASPBERRY]:80"
echo "Redémarrez pour tester le démarrage automatique avec: sudo reboot"
