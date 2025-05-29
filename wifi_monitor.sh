#!/bin/bash

PREV_SSID=""

while true; do
    # Obtenir le SSID actuel
    CURRENT_SSID=$(iwgetid -r)
    
    # Si le SSID a changé
    if [ "$CURRENT_SSID" != "$PREV_SSID" ]; then
        echo "WiFi network changed from '$PREV_SSID' to '$CURRENT_SSID'"
        
        # Attendre que la connexion soit stable
        sleep 5
        
        # Redémarrer le service lorareplay
        sudo systemctl restart lorareplay.service
        
        # Mettre à jour le SSID précédent
        PREV_SSID="$CURRENT_SSID"
    fi
    
    # Vérifier toutes les 10 secondes
    sleep 10
done
