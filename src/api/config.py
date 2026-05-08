import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))

# ==================== BASE DE DONNÉES ====================
DB_PATH = os.path.join(BASE_DIR, 'data/database/autostockcheck.db')

# ==================== MODÈLES IA ====================
MODEL_PATH = os.path.join(BASE_DIR, "models_saved/best_model_params.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "models_saved/scaler.pkl")
FEATURES_PATH = os.path.join(BASE_DIR, "models_saved/features.pkl")


# ==================== DOSSIERS UPLOAD ====================
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'data', 'uploads')
FACTURES_FOLDER = os.path.join(UPLOAD_FOLDER, 'factures')
RECEPTIONS_FOLDER = os.path.join(UPLOAD_FOLDER, 'receptions')
RECEPTIONS_FOLDER = os.path.join(UPLOAD_FOLDER, 'receptions')
USERS_FOLDER = os.path.join(BASE_DIR, 'data', 'users')
# ==================== DOSSIERS MÉTIER ====================
COMPARAISONS_FOLDER = os.path.join(BASE_DIR, 'data', 'comparaisons')
CLIENTS_ROOT = os.path.join(BASE_DIR, 'data', 'clients')
ANOMALIES_FOLDER = os.path.join(BASE_DIR, 'data', 'anomalies')

# ==================== CRÉATION DES DOSSIERS ====================
os.makedirs(FACTURES_FOLDER, exist_ok=True)
os.makedirs(RECEPTIONS_FOLDER, exist_ok=True)
os.makedirs(CLIENTS_ROOT, exist_ok=True)
os.makedirs(ANOMALIES_FOLDER, exist_ok=True)
os.makedirs(COMPARAISONS_FOLDER, exist_ok=True)
os.makedirs(USERS_FOLDER, exist_ok=True)
os.makedirs(USERS_FOLDER, exist_ok=True)
# ==================== AFFICHAGE ====================
print("=" * 50)
print("📁 Configuration des dossiers:")
print(f"   - Base de données: {DB_PATH}")
print(f"   - Factures: {FACTURES_FOLDER}")
print(f"   - Réceptions: {RECEPTIONS_FOLDER}")
print(f"   - Clients: {CLIENTS_ROOT}")
print(f"   - Anomalies: {ANOMALIES_FOLDER}")
print(f"   - Comparaisons: {COMPARAISONS_FOLDER}")
print(f"📁 Dossier users: {USERS_FOLDER}")
print("=" * 50)