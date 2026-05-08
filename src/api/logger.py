import os
import gzip
import shutil
from datetime import datetime, timedelta
from config import BASE_DIR

# Dossier des logs
LOGS_FOLDER = os.path.join(BASE_DIR, 'data', 'logs')
os.makedirs(LOGS_FOLDER, exist_ok=True)

# Configuration
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_LOG_FILES = 30  # Garder 30 jours
COMPRESS_OLD_LOGS = True

def get_log_file_path(log_type='audit'):
    """Retourne le chemin du fichier de log du jour"""
    today = datetime.now().strftime('%Y-%m-%d')
    return os.path.join(LOGS_FOLDER, f"{log_type}_{today}.log")

def rotate_log_if_needed(log_path):
    """Rotation du log si trop gros"""
    if not os.path.exists(log_path):
        return
    
    if os.path.getsize(log_path) > MAX_LOG_SIZE:
        # Renommer le fichier actuel
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        rotated_path = log_path.replace('.log', f'_rotated_{timestamp}.log')
        shutil.move(log_path, rotated_path)
        
        # Compresser si demandé
        if COMPRESS_OLD_LOGS:
            with open(rotated_path, 'rb') as f_in:
                with gzip.open(rotated_path + '.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(rotated_path)
        
        # Nettoyer les anciens logs
        clean_old_logs()

def clean_old_logs():
    """Supprime les logs trop anciens"""
    now = datetime.now()
    for filename in os.listdir(LOGS_FOLDER):
        filepath = os.path.join(LOGS_FOLDER, filename)
        if os.path.isfile(filepath):
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            if (now - mtime).days > MAX_LOG_FILES:
                os.remove(filepath)

def write_log(log_type, data):
    """Écrit un log dans le fichier correspondant"""
    log_path = get_log_file_path(log_type)
    rotate_log_if_needed(log_path)
    
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(data + '\n')

# Dans logger.py, assure-toi que le format est correct
def log_action(user_id, user_name, user_role, action, details, ip_address, entity_type=None, entity_id=None):
    timestamp = datetime.now().isoformat()
    log_line = f"[{timestamp}] [{user_name}] [{user_role}] [{action}] {details} (IP: {ip_address})"
    
    if entity_id:
        log_line += f" [{entity_type}:{entity_id}]"
    
    write_log('audit', log_line)

def log_error(error_msg, context=None):
    """Enregistre une erreur"""
    log_line = f"[{datetime.now().isoformat()}] ERROR: {error_msg}"
    if context:
        log_line += f" | Context: {context}"
    write_log('errors', log_line)

def get_logs(log_type='audit', days=7, limit=1000):
    """Récupère les logs des derniers jours"""
    logs = []
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        log_path = os.path.join(LOGS_FOLDER, f"{log_type}_{date}.log")
        
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    logs.append(line.strip())
                    if len(logs) >= limit:
                        return logs
    
    return logs

def export_logs_to_csv(log_type='audit', days=7):
    """Exporte les logs en CSV"""
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Utilisateur', 'Rôle', 'Action', 'Détails', 'IP'])
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        log_path = os.path.join(LOGS_FOLDER, f"{log_type}_{date}.log")
        
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # Parse line: [2024-12-24T10:30:00] [admin] [admin] [login] Connexion réussie (IP: 127.0.0.1)
                    parts = line.split('] ')
                    if len(parts) >= 5:
                        date_part = parts[0].strip('[')
                        user = parts[1].strip('[')
                        role = parts[2].strip('[')
                        action = parts[3].strip('[')
                        rest = ' '.join(parts[4:])
                        # Extraire IP
                        ip = rest.split('IP: ')[-1] if 'IP: ' in rest else '-'
                        details = rest.split(' (IP:')[0]
                        
                        writer.writerow([date_part, user, role, action, details, ip])
    
    return output.getvalue()