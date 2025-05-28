from flask import Flask, request, jsonify, render_template
import subprocess
import os
import time
import socket
import re
import json

app = Flask(__name__, static_folder='static')
BASE_PATH = "/home/pi/lorareplay/signals/frequences"
CLICK_COUNT_FILE = "/home/pi/lorareplay/click_count.txt"

def read_click_count():
    if os.path.exists(CLICK_COUNT_FILE):
        with open(CLICK_COUNT_FILE, "r") as f:
            return int(f.read())
    return 0

def write_click_count(count):
    with open(CLICK_COUNT_FILE, "w") as f:
        f.write(str(count))

def get_folders():
    folders = [
        f for f in os.listdir(BASE_PATH)
        if os.path.isdir(os.path.join(BASE_PATH, f)) and f.isdigit()
    ]
    return sorted(folders, key=lambda x: int(x))

def get_files(folder):
    folder_path = os.path.join(BASE_PATH, folder)
    return sorted([f for f in os.listdir(folder_path) if f.endswith(".C16")])

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

@app.before_request
def detect_device():
    user_agent = request.headers.get('User-Agent', '').lower()
    if 'android' in user_agent or 'iphone' in user_agent or 'ipad' in user_agent:
        request.is_mobile = True
    else:
        request.is_mobile = False

@app.route("/")
def index():
    return render_template("index.html", folders=get_folders())

@app.route("/wifi.html")
def wifi():
    return render_template("wifi.html")

@app.route("/files")
def files():
    folder = request.args.get("folder")
    if not folder:
        return jsonify([])
    return jsonify(get_files(folder))

@app.route("/send")
def send():
    folder = request.args.get("folder")
    letter = request.args.get("letter")
    file_path = os.path.join(BASE_PATH, folder, f"{letter}.C16")
    
    # Gérer le cas particulier des noms de fichiers avec espaces
    if not os.path.exists(file_path):
        # Essayer avec un espace après la lettre (comme dans le dossier 2)
        file_path = os.path.join(BASE_PATH, folder, f"{letter} .C16")
        if not os.path.exists(file_path):
            return jsonify({"status": "error", "message": f"❌ Fichier {letter}.C16 introuvable"})
    
    # Trouver le fichier .TXT correspondant
    txt_file_path = file_path.replace(".C16", ".TXT")
    if not os.path.exists(txt_file_path):
        txt_file_path = file_path.replace(".C16", ".txt")  # Essayer avec une extension en minuscules
    
    # Lire les paramètres
    params = read_signal_params(txt_file_path)
    
    # Afficher les paramètres utilisés pour le débogage
    print(f"Envoi du signal {file_path} avec:")
    print(f"- Fréquence: {params['center_frequency']} Hz")
    print(f"- Taux d'échantillonnage: {params['sample_rate']} Hz")
    
    # Déterminer si le taux d'échantillonnage a été ajusté
    original_sample_rate = None
    try:
        with open(txt_file_path, 'r') as f:
            for line in f:
                if 'sample_rate=' in line:
                    value = line.split('=')[1].strip()
                    original_sample_rate = int(value)
                    break
    except:
        pass
    
    if original_sample_rate and original_sample_rate < 2000000 and params['sample_rate'] >= 2000000:
        print(f"⚠️ Taux d'échantillonnage ajusté de {original_sample_rate} à {params['sample_rate']} Hz (minimum requis)")

    # Vérifier si HackRF est connecté
    try:
        hackrf_check = subprocess.run(["hackrf_info"], capture_output=True, text=True, timeout=2)
        if "hackrf_info version" not in hackrf_check.stdout:
            return jsonify({"status": "error", "message": "❌ HackRF non détecté"})
    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
        return jsonify({"status": "error", "message": "❌ HackRF non détecté"})

    try:
        subprocess.run([
            "hackrf_transfer",
            "-t", file_path,
            "-f", str(params['center_frequency']),
            "-s", str(params['sample_rate']),
            "-x", "47",
            "-F"  # Force l'utilisation de paramètres hors plage
        ], check=True)

        count = read_click_count()
        write_click_count(count + 1)

        return jsonify({
            "status": "success", 
            "message": f"✅ Envoyé : {letter}.C16 (dossier {folder})",
            "details": f"Fréquence: {params['center_frequency']/1000000} MHz, Sample rate: {params['sample_rate']/1000000} MHz",
        })
    except subprocess.CalledProcessError:
        return jsonify({"status": "error", "message": "❌ Erreur lors de l'envoi"})

@app.route("/click-count")
def get_click_count():
    return jsonify({"count": read_click_count()})

@app.route("/reset-count", methods=["POST"])
def reset_click_count():
    write_click_count(0)
    return jsonify({"status": "success", "message": "Compteur remis à zéro."})

@app.route("/hackrf-status")
def hackrf_status():
    try:
        # Méthode plus fiable pour vérifier si le HackRF est vraiment connecté
        # Exécuter une commande qui nécessite un accès réel au matériel
        result = subprocess.run(
            ["hackrf_info"], 
            capture_output=True, 
            text=True, 
            timeout=1
        )
        
        # Vérifier si le résultat contient les informations du matériel
        if "hackrf_info version" in result.stdout and "Serial number:" in result.stdout:
            # Extraire les informations utiles
            serial_number = None
            board_id = None
            firmware_version = None
            part_id = None
            
            for line in result.stdout.splitlines():
                if "Serial number:" in line:
                    serial_number = line.strip()
                elif "Board ID Number:" in line:
                    board_id = line.strip()
                elif "Firmware Version:" in line:
                    firmware_version = line.strip()
                elif "Part ID Number:" in line:
                    part_id = line.strip()
            
            # Préparer les informations détaillées
            details = []
            if serial_number:
                details.append(serial_number)
            if firmware_version:
                details.append(firmware_version)
            if board_id:
                details.append(board_id)
                
            # Créer le message avec les détails
            details_str = ", ".join(details) if details else ""
            
            return jsonify({
                "status": "connected", 
                "message": "HackRF connecté ✅",
                "details": details_str,
                "timestamp": int(time.time())
            })
        else:
            # Cas où la commande s'exécute mais ne retourne pas les informations attendues
            return jsonify({
                "status": "disconnected", 
                "message": "HackRF non détecté ❌",
                "timestamp": int(time.time())
            })
    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
        # En cas d'erreur d'exécution de la commande
        return jsonify({
            "status": "disconnected", 
            "message": "HackRF non détecté ❌",
            "timestamp": int(time.time())
        })

@app.route("/shutdown", methods=["POST"])
def shutdown():
    os.system("sudo shutdown now")
    return jsonify({"status": "success", "message": "Extinction en cours..."})

@app.route("/get-ip")
def get_ip():
    """Récupère l'adresse IP du Raspberry Pi"""
    try:
        # Récupérer les adresses IP
        ip_info = {}
        interfaces = ["wlan0", "eth0"]
        
        for interface in interfaces:
            cmd = f"ip addr show {interface} 2>/dev/null | grep 'inet ' | awk '{{print $2}}' | cut -d/ -f1"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            ip = result.stdout.strip()
            if ip:
                ip_info[interface] = ip
        
        # Vérifier si nous avons au moins une adresse IP
        if not ip_info:
            # Essayer d'obtenir l'adresse IP de manière alternative
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(("8.8.8.8", 80))
                ip_info["default"] = s.getsockname()[0]
            except:
                ip_info["default"] = "127.0.0.1"
            finally:
                s.close()
        
        return jsonify({"status": "success", "ip_info": ip_info})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/wifi-scan")
def wifi_scan():
    """Scanne les réseaux WiFi disponibles"""
    try:
        # Utiliser nmcli pour scanner les réseaux WiFi
        cmd = "nmcli -t -f SSID,SIGNAL,SECURITY device wifi list"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        networks = []
        for line in result.stdout.splitlines():
            if line:
                parts = line.split(':')
                if len(parts) >= 3:
                    ssid = parts[0]
                    signal = parts[1]
                    security = parts[2]
                    
                    # Éviter les duplicatas (trier par force du signal)
                    found = False
                    for net in networks:
                        if net['ssid'] == ssid:
                            found = True
                            if int(signal) > int(net['signal']):
                                net['signal'] = signal
                            break
                    
                    if not found and ssid:
                        networks.append({
                            'ssid': ssid,
                            'signal': signal,
                            'security': security
                        })
        
        # Trier par force de signal
        networks.sort(key=lambda x: int(x['signal']), reverse=True)
        
        return jsonify({"status": "success", "networks": networks})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/wifi-status")
def wifi_status():
    """Récupère le statut actuel de la connexion WiFi"""
    try:
        # Vérifier si le WiFi est connecté
        cmd = "nmcli -t -f NAME,DEVICE connection show --active | grep wlan0"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            # Si connecté, obtenir les détails
            ssid = result.stdout.split(':')[0]
            
            # Récupérer la force du signal
            cmd = "nmcli -f IN-USE,SIGNAL device wifi | grep '*'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            signal = "0"
            if result.stdout:
                match = re.search(r'\*\s+(\d+)', result.stdout)
                if match:
                    signal = match.group(1)
            
            return jsonify({
                "status": "success",
                "connected": True,
                "ssid": ssid,
                "signal": signal
            })
        else:
            return jsonify({
                "status": "success",
                "connected": False
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/wifi-connect", methods=["POST"])
def wifi_connect():
    """Connecte le Raspberry Pi à un réseau WiFi"""
    try:
        data = request.get_json()
        ssid = data.get('ssid')
        password = data.get('password')
        
        if not ssid:
            return jsonify({"status": "error", "message": "SSID manquant"})
        
        # Créer une nouvelle connexion
        if password:
            cmd = f'nmcli device wifi connect "{ssid}" password "{password}"'
        else:
            cmd = f'nmcli device wifi connect "{ssid}"'
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if "successfully activated" in result.stdout or "activée avec succès" in result.stdout:
            return jsonify({"status": "success", "message": f"Connecté à {ssid}"})
        else:
            error_msg = result.stderr.strip() or "Échec de connexion"
            return jsonify({"status": "error", "message": error_msg})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/wifi-disconnect", methods=["POST"])
def wifi_disconnect():
    """Déconnecte le WiFi"""
    try:
        # Obtenir la connexion active
        cmd = "nmcli -t -f NAME connection show --active | grep -v 'lo:'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            connection_name = result.stdout.strip().split(':')[0]
            # Déconnecter
            cmd = f'nmcli connection down "{connection_name}"'
            subprocess.run(cmd, shell=True)
            return jsonify({"status": "success", "message": "WiFi déconnecté"})
        else:
            return jsonify({"status": "error", "message": "Aucune connexion active"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/device-type")
def device_type():
    user_agent = request.headers.get('User-Agent', '').lower()
    if 'android' in user_agent or 'iphone' in user_agent or 'ipad' in user_agent:
        return jsonify({'device': 'mobile'})
    elif 'raspbian' in user_agent or 'linux' in user_agent or 'raspberry' in user_agent:
        return jsonify({'device': 'raspberry'})
    else:
        return jsonify({'device': 'desktop'})

if __name__ == "__main__":
    print("🌐 Serveur en ligne : http://<IP_RPI>:5000")
    app.run(host="0.0.0.0", port=5000)
