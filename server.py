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

# Cache pour les réseaux WiFi
last_scan_time = 0
cached_networks = None
SCAN_CACHE_DURATION = 10  # durée de validité du cache en secondes

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

def get_wifi_status():
    try:
        # Vérifier si l'interface wlan0 est connectée
        result = subprocess.run(['iwgetid', 'wlan0', '-r'], capture_output=True, text=True)
        if result.returncode == 0:
            ssid = result.stdout.strip()
            # Obtenir l'adresse IP
            ip_result = subprocess.run(['ip', 'addr', 'show', 'wlan0'], capture_output=True, text=True)
            ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', ip_result.stdout)
            ip = ip_match.group(1) if ip_match else None
            return {"connected": True, "ssid": ssid, "ip": ip}
        return {"connected": False, "ssid": None, "ip": None}
    except Exception as e:
        return {"connected": False, "ssid": None, "ip": None, "error": str(e)}

def get_current_wifi():
    """Obtient le réseau WiFi actuellement connecté"""
    try:
        result = subprocess.run(['sudo', 'nmcli', '-t', '-f', 'NAME,TYPE,DEVICE,STATE', 'connection', 'show', '--active'],
            capture_output=True,
            text=True
        )
        for line in result.stdout.splitlines():
            if 'wireless' in line and 'wlan0' in line and 'activated' in line:
                return line.split(':')[0]
        return None
    except Exception:
        return None

def check_wifi_state():
    """Vérifie l'état de l'interface WiFi"""
    try:
        result = subprocess.run(['sudo', 'nmcli', 'radio', 'wifi'],
            capture_output=True,
            text=True
        )
        return 'enabled' in result.stdout
    except Exception:
        return False

def ensure_wifi_enabled():
    """S'assure que le WiFi est activé"""
    if not check_wifi_state():
        subprocess.run(['sudo', 'nmcli', 'radio', 'wifi', 'on'], capture_output=True)
        time.sleep(1)

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
    status = get_wifi_status()
    return jsonify({"ip": status.get("ip")})

@app.route("/wifi-scan")
def wifi_scan():
    """Scanne les réseaux WiFi disponibles avec mise en cache"""
    global last_scan_time, cached_networks
    current_time = time.time()
    
    try:
        # Utiliser le cache si disponible et récent
        if cached_networks and (current_time - last_scan_time) < SCAN_CACHE_DURATION:
            return jsonify(cached_networks)

        ensure_wifi_enabled()
        
        # Lance le scan en arrière-plan
        subprocess.run(['sudo', 'nmcli', 'device', 'wifi', 'rescan'], capture_output=True)
        
        # Attente optimisée avec vérification progressive
        for _ in range(3):  # 3 tentatives maximum
            time.sleep(1)
            result = subprocess.run(
                ['sudo', 'nmcli', '--fields', 'SSID,SIGNAL,SECURITY', '--terse', 'device', 'wifi', 'list'],
                capture_output=True,
                text=True
            )
            if result.stdout.strip():  # Si on a des résultats, on arrête d'attendre
                break
        
        networks = []
        current_network = get_current_wifi()
        
        for line in result.stdout.splitlines():
            if line:
                ssid, signal, security = line.split(':')
                if ssid and ssid.strip():  # Ignorer les SSID vides
                    networks.append({
                        'ssid': ssid,
                        'signal': int(signal) if signal.isdigit() else 0,
                        'security': bool(security)
                    })
        
        # Trier par force du signal
        networks.sort(key=lambda x: x['signal'], reverse=True)
        
        # Mise à jour du cache
        cached_networks = {'networks': networks, 'current_network': current_network}
        last_scan_time = current_time
        
        return jsonify(cached_networks)
    except Exception as e:
        print("Erreur scan wifi:", str(e))
        return jsonify({'error': str(e)})

@app.route("/wifi-status")
def wifi_status():
    status = get_wifi_status()
    return jsonify(status)

@app.route("/connect_wifi", methods=["POST"])
def wifi_connect():
    """Connexion à un réseau WiFi avec gestion optimisée"""
    try:
        data = request.get_json()
        ssid = data.get('ssid')
        password = data.get('password')

        if not ssid or not password:
            return jsonify({'success': False, 'error': 'SSID et mot de passe requis'})

        ensure_wifi_enabled()
        current_network = get_current_wifi()

        if current_network == ssid:
            # Déjà connecté à ce réseau
            return jsonify({'success': True, 'message': 'Déjà connecté à ce réseau'})

        # Déconnexion du réseau actuel si nécessaire
        if current_network:
            subprocess.run(['sudo', 'nmcli', 'device', 'disconnect', 'wlan0'], capture_output=True)
            time.sleep(0.5)

        # Tentative de connexion avec timeout
        try:
            result = subprocess.run(
                ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid, 'password', password],
                capture_output=True,
                text=True,
                timeout=10  # Timeout de 10 secondes
            )

            if result.returncode == 0:
                # Vider le cache pour forcer un nouveau scan
                global cached_networks, last_scan_time
                cached_networks = None
                last_scan_time = 0
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': result.stderr})

        except subprocess.TimeoutExpired:
            return jsonify({'success': False, 'error': 'Timeout de connexion'})

    except Exception as e:
        print("Exception connexion wifi:", str(e))
        return jsonify({'success': False, 'error': str(e)})

@app.route("/wifi-disconnect", methods=["POST"])
def wifi_disconnect():
    """Déconnecte le WiFi"""
    try:
        # Désactiver l'interface wlan0
        subprocess.run(['sudo', 'ifconfig', 'wlan0', 'down'])
        time.sleep(1)
        subprocess.run(['sudo', 'ifconfig', 'wlan0', 'up'])
        
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route("/check_wifi_credentials", methods=["POST"])
def check_wifi_credentials():
    data = request.get_json()
    ssid = data.get('ssid')
    
    try:
        with open('wifi_credentials.txt', 'r') as f:
            for line in f:
                if line.startswith('//') or not line.strip():
                    continue
                stored_ssid, stored_password = line.strip().split(':')
                if stored_ssid == ssid:
                    return jsonify({
                        'hasCredentials': True,
                        'password': stored_password
                    })
    except FileNotFoundError:
        pass
    
    return jsonify({
        'hasCredentials': False,
        'password': None
    })

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
