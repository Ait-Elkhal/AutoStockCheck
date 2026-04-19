"""
API Flask complète pour AutoStockCheck
Plateforme de vérification automatique des commandes avec authentification
AutoStockCheck - ECU Worldwide
"""

import sys
import os
import pickle
import json
import sqlite3
import hashlib
import secrets
import base64
import re
from datetime import datetime, timedelta
from functools import wraps
from io import BytesIO
from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
from flask_cors import CORS
import shutil

# Ajouter le chemin
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), '../web/templates'),
            static_folder=os.path.join(os.path.dirname(__file__), '../web/static'))
app.secret_key = secrets.token_hex(32)
CORS(app)

# ==================== CONFIGURATION DOSSIERS UPLOAD ====================

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
DB_PATH = os.path.join(BASE_DIR, 'data/database/autostockcheck.db')
MODEL_PATH = os.path.join(BASE_DIR, "models_saved/best_model_params.pkl")
SCALER_PATH = os.path.join(BASE_DIR, "models_saved/scaler.pkl")
FEATURES_PATH = os.path.join(BASE_DIR, "models_saved/features.pkl")

# Dossiers pour les fichiers uploadés
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'data', 'uploads')
FACTURES_FOLDER = os.path.join(UPLOAD_FOLDER, 'factures')
RECEPTIONS_FOLDER = os.path.join(UPLOAD_FOLDER, 'receptions')

# Dossier racine pour les clients
CLIENTS_ROOT = os.path.join(BASE_DIR, 'data', 'clients')

# Créer les dossiers s'ils n'existent pas
os.makedirs(FACTURES_FOLDER, exist_ok=True)
os.makedirs(RECEPTIONS_FOLDER, exist_ok=True)
os.makedirs(CLIENTS_ROOT, exist_ok=True)

print(f"📁 Dossier uploads: {UPLOAD_FOLDER}")
print(f"📁 Dossier factures: {FACTURES_FOLDER}")
print(f"📁 Dossier réceptions: {RECEPTIONS_FOLDER}")
print(f"📁 Dossier clients: {CLIENTS_ROOT}")

# Stockage des tokens (à remplacer par Redis en production)
tokens = {}

# Stockage des notifications
notifications = []

# ==================== FONCTIONS BASE DE DONNÉES ====================

def get_db():
    """Connexion à la base de données"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Hashage du mot de passe"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token():
    """Génère un token d'authentification"""
    return secrets.token_urlsafe(32)

def get_upload_path(category, reference):
    """Génère le chemin de sauvegarde pour un fichier"""
    now = datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')
    
    if category == 'facture':
        base_folder = FACTURES_FOLDER
        prefix = 'facture'
    else:
        base_folder = RECEPTIONS_FOLDER
        prefix = 'reception'
    
    year_folder = os.path.join(base_folder, year)
    month_folder = os.path.join(year_folder, month)
    os.makedirs(month_folder, exist_ok=True)
    
    timestamp = now.strftime('%Y%m%d_%H%M%S')
    filename = f"{prefix}_{reference}_{timestamp}.xlsx"
    filepath = os.path.join(month_folder, filename)
    
    return filepath, filename

def get_client_folder(email):
    """Retourne le chemin du dossier d'un client"""
    safe_email = email.replace('@', '_at_').replace('.', '_dot_')
    folder = os.path.join(CLIENTS_ROOT, safe_email)
    os.makedirs(folder, exist_ok=True)
    
    # Créer les sous-dossiers
    subdirs = ['identite', 'emails/envoyes', 'emails/recus', 'factures', 'rapports', 'historique', 'agenda']
    for sub in subdirs:
        os.makedirs(os.path.join(folder, sub), exist_ok=True)
    
    return folder

def extract_reference_from_subject(subject):
    """Extrait une référence à partir du sujet de l'email"""
    patterns = [
        r'REF[-\s]*(\d+)',
        r'CMD[-\s]*(\d+)',
        r'FACT[-\s]*(\d+)',
        r'INV[-\s]*(\d+)',
        r'\[REF[-\s]*(\d+)\]',
        r'Réf[^:]*:\s*(\S+)',
        r'Reference[^:]*:\s*(\S+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, subject, re.IGNORECASE)
        if match:
            return f"REF-{match.group(1)}"
    return None

def extract_excel_from_email(file_content, filename):
    """Extrait et valide un fichier Excel depuis une pièce jointe"""
    try:
        import pandas as pd
        df = pd.read_excel(BytesIO(file_content))
        
        # Afficher les colonnes pour déboguer
        columns = df.columns.tolist()
        print(f"📊 Colonnes détectées: {columns}")
        
        # Chercher les colonnes - Support FR et EN
        ref_col = None
        qty_col = None
        product_col = None
        price_col = None
        
        for col in columns:
            col_lower = str(col).lower().strip()
            
            # Référence - FR/EN
            if col_lower in ['ref', 'reference', 'référence', 'code', 'sku', 'id', 'article']:
                ref_col = col
                print(f"   ✅ Colonne référence trouvée: {col}")
            
            # Quantité - FR/EN
            if col_lower in ['qty', 'quantite', 'quantité', 'qté', 'quantity', 'nb', 'nombre']:
                qty_col = col
                print(f"   ✅ Colonne quantité trouvée: {col}")
            
            # Produit/Nom - FR/EN
            if col_lower in ['product', 'produit', 'nom', 'name', 'designation', 'description', 'item']:
                product_col = col
                print(f"   ✅ Colonne produit trouvée: {col}")
            
            # Prix - FR/EN
            if col_lower in ['price', 'prix', 'pu', 'unit_price', 'cost', 'montant']:
                price_col = col
                print(f"   ✅ Colonne prix trouvée: {col}")
        
        # Si aucune colonne trouvée, utiliser la première colonne comme référence
        if ref_col is None and len(columns) > 0:
            ref_col = columns[0]
            print(f"   ⚠️ Utilisation de la première colonne comme référence: {ref_col}")
        
        if qty_col is None and len(columns) > 1:
            qty_col = columns[1]
            print(f"   ⚠️ Utilisation de la deuxième colonne comme quantité: {qty_col}")
        
        # Extraire les données
        produits = []
        for idx, row in df.iterrows():
            try:
                if ref_col and pd.notna(row[ref_col]):
                    reference = str(row[ref_col]).strip()
                    if reference and reference != 'nan':
                        quantite = float(row[qty_col]) if qty_col and pd.notna(row[qty_col]) else 1
                        nom = str(row[product_col]) if product_col and pd.notna(row[product_col]) else f"Produit {reference}"
                        prix = float(row[price_col]) if price_col and pd.notna(row[price_col]) else 0
                        
                        produits.append({
                            'reference': reference,
                            'nom': nom,
                            'quantite': quantite,
                            'prix': prix
                        })
                        print(f"   📦 Produit {idx+1}: {reference} - {nom} - {quantite}")
            except Exception as e:
                print(f"   ⚠️ Erreur ligne {idx}: {e}")
        
        print(f"📊 Total produits extraits: {len(produits)}")
        
        return {
            'success': len(produits) > 0,
            'produits': produits,
            'colonnes': columns,
            'total_produits': len(produits)
        }
    except Exception as e:
        print(f"❌ Erreur extraction Excel: {e}")
        return {'success': False, 'error': str(e), 'produits': [], 'total_produits': 0}

# ==================== DÉCORATEUR AUTHENTIFICATION ====================

def require_auth(f):
    """Décorateur pour protéger les routes API"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '')
        user_id = tokens.get(token)
        if not user_id:
            return jsonify({'status': 'error', 'message': 'Non authentifié'}), 401
        request.user_id = user_id
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT role FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        request.user_role = user['role'] if user else 'user'
        
        return f(*args, **kwargs)
    return decorated

# ==================== CLASSES MODÈLE ====================

class SimplePredictor:
    """Prédicteur simple utilisant les paramètres du modèle sauvegardé"""
    
    def __init__(self, model_params_path, scaler_path, features_path):
        import numpy as np
        self.np = np
        
        with open(model_params_path, 'rb') as f:
            params = pickle.load(f)
        
        self.weights = params['weights']
        self.bias = params['bias']
        self.kernel = params['kernel']
        self.features = params['features']
        
        with open(scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)
        
        print(f"   ✅ Prédicteur chargé avec {len(self.features)} features")
    
    def predict(self, X):
        scores = self.np.dot(X, self.weights) + self.bias
        predictions = self.np.where(scores >= 0, 1, -1)
        return self.np.where(predictions == -1, 0, 1)
    
    def predict_proba(self, X):
        scores = self.np.dot(X, self.weights) + self.bias
        proba_1 = 1 / (1 + self.np.exp(-scores))
        proba_0 = 1 - proba_1
        return self.np.column_stack([proba_0, proba_1])
    
    def extract_features(self, facture, stock):
        features_dict = {}
        
        quantite_facture = facture.get('quantite', 0)
        quantite_stock = stock.get('quantite', 0)
        prix = facture.get('prix', 0)
        
        features_dict['diff_quantite'] = quantite_facture - quantite_stock
        features_dict['produit_absent'] = 1 if quantite_stock == 0 else 0
        features_dict['quantite_insuffisante'] = 1 if features_dict['diff_quantite'] > 0 else 0
        features_dict['ratio_stock'] = quantite_stock / (quantite_facture + 1)
        features_dict['etat_produit'] = stock.get('etat_produit', 0.95)
        features_dict['fiabilite_fournisseur'] = stock.get('fiabilite_fournisseur', 0.95)
        features_dict['popularite'] = facture.get('popularite', 0.6)
        features_dict['saisonnalite'] = facture.get('saisonnalite', 1.0)
        features_dict['prix'] = prix
        features_dict['valeur_ligne'] = quantite_facture * prix
        features_dict['produit_cher'] = 1 if prix > 100 else 0
        features_dict['diff_x_prix'] = features_dict['diff_quantite'] * prix
        features_dict['absent_x_prix'] = features_dict['produit_absent'] * prix
        features_dict['etat_x_popularite'] = features_dict['etat_produit'] * features_dict['popularite']
        
        return [features_dict.get(f, 0) for f in self.features]

# ==================== CHARGEMENT DU MODÈLE ====================

print("=" * 60)
print("🚀 AutoStockCheck API")
print("=" * 60)
print("\n📂 Chargement du modèle...")

predictor = None

try:
    import numpy as np
    predictor = SimplePredictor(MODEL_PATH, SCALER_PATH, FEATURES_PATH)
    print("   ✅ Modèle chargé avec succès")
except Exception as e:
    print(f"   ❌ Erreur: {e}")
    predictor = None

print("=" * 60)

# ==================== ROUTES PAGES ====================

@app.route('/')
def accueil():
    return render_template('pages/accueil.html', active_page='accueil')

@app.route('/models')
def models():
    return render_template('pages/models.html', active_page='models')

@app.route('/contact')
def contact():
    return render_template('pages/contact.html', active_page='contact')

@app.route('/register')
def register_page():
    return render_template('pages/register.html', active_page='register')

@app.route('/login')
def login_page():
    return render_template('pages/login.html', active_page='login')

@app.route('/dashboard')
def dashboard_page():
    return render_template('dashboard/index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.route('/static/data/<path:path>')
def serve_static_data(path):
    return send_from_directory(os.path.join(app.static_folder, 'data'), path)

# ==================== ROUTES API UPLOAD FICHIERS ====================

@app.route('/api/upload/facture', methods=['POST'])
@require_auth
def upload_facture():
    """Sauvegarde une facture sur le serveur"""
    try:
        if 'fichier' not in request.files:
            return jsonify({'status': 'error', 'message': 'Aucun fichier'}), 400
        
        fichier = request.files['fichier']
        reference = request.form.get('reference', 'unknown')
        
        filepath, filename = get_upload_path('facture', reference)
        fichier.save(filepath)
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO fichiers_upload (user_id, type, reference, nom_fichier, chemin, taille, date_upload)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.user_id,
            'facture',
            reference,
            filename,
            filepath,
            os.path.getsize(filepath),
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': f'Facture sauvegardée avec succès',
            'path': filepath,
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/upload/reception', methods=['POST'])
@require_auth
def upload_reception():
    """Sauvegarde une réception générée sur le serveur"""
    try:
        if 'fichier' not in request.files:
            return jsonify({'status': 'error', 'message': 'Aucun fichier'}), 400
        
        fichier = request.files['fichier']
        reference = request.form.get('reference', 'unknown')
        client = request.form.get('client', '')
        
        filepath, filename = get_upload_path('reception', reference)
        fichier.save(filepath)
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO fichiers_upload (user_id, type, reference, nom_fichier, chemin, taille, date_upload, client)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.user_id,
            'reception',
            reference,
            filename,
            filepath,
            os.path.getsize(filepath),
            datetime.now().isoformat(),
            client
        ))
        
        cursor.execute('''
            UPDATE commandes_recues 
            SET chemin_fichier = ?, nom_fichier = ?
            WHERE reference = ? AND user_id = ?
        ''', (filepath, filename, reference, request.user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success',
            'message': f'Réception sauvegardée avec succès',
            'path': filepath,
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ==================== ROUTES API AUTHENTIFICATION ====================

@app.route('/api/register', methods=['POST'])
def api_register():
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password') or not data.get('email'):
            return jsonify({'status': 'error', 'message': 'Champs obligatoires manquants'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM users WHERE username = ?', (data['username'],))
        if cursor.fetchone():
            conn.close()
            return jsonify({'status': 'error', 'message': 'Nom d\'utilisateur déjà existant'}), 400
        
        hashed = hash_password(data['password'])
        cursor.execute('''
            INSERT INTO users (username, password, email, company, storage_type, role)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['username'], hashed, data['email'], data.get('company', ''), 
              data.get('storage_type', ''), 'user'))
        user_id = cursor.lastrowid
        
        cursor.execute('''
            INSERT INTO companies (user_id, company_name, storage_type, email_stock_manager, email_notification)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, data.get('company', ''), data.get('storage_type', ''), 
              data.get('email_stock', ''), data.get('email_notification', '')))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Inscription réussie'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE username = ?', (data['username'],))
        user = cursor.fetchone()
        conn.close()
        
        if user and user['password'] == hash_password(data['password']):
            token = generate_token()
            tokens[token] = user['id']
            
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_sessions (user_id, token, ip_address, user_agent, last_activity)
                VALUES (?, ?, ?, ?, ?)
            ''', (user['id'], token, request.remote_addr, request.headers.get('User-Agent', ''), datetime.now().isoformat()))
            conn.commit()
            conn.close()
            
            return jsonify({
                'status': 'success',
                'token': token,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'company': user['company'],
                    'storage_type': user['storage_type'],
                    'role': user['role']
                }
            })
        
        return jsonify({'status': 'error', 'message': 'Identifiants invalides'}), 401
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
@require_auth
def api_logout():
    auth_header = request.headers.get('Authorization', '')
    token = auth_header.replace('Bearer ', '')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('UPDATE user_sessions SET logout_at = ? WHERE token = ?', (datetime.now().isoformat(), token))
    conn.commit()
    conn.close()
    
    if token in tokens:
        del tokens[token]
    return jsonify({'status': 'success'})

# ==================== ROUTES API CONTACT ====================

@app.route('/api/contact', methods=['POST'])
def api_contact():
    try:
        data = request.get_json()
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO contacts (name, email, subject, message)
            VALUES (?, ?, ?, ?)
        ''', (data.get('nom', ''), data.get('email', ''), data.get('sujet', ''), data.get('message', '')))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Votre message a été envoyé.'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ==================== ROUTES API PRINCIPALES ====================

@app.route('/api/health', methods=['GET'])
def api_health():
    return jsonify({
        'status': 'healthy',
        'model_loaded': predictor is not None,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/predict', methods=['POST'])
@require_auth
def api_predict():
    if predictor is None:
        return jsonify({'status': 'error', 'message': 'Modèle non chargé'}), 500
    
    try:
        data = request.get_json()
        
        facture = data.get('facture', {})
        stock = data.get('stock', {})
        
        features_list = predictor.extract_features(facture, stock)
        X = predictor.np.array(features_list).reshape(1, -1)
        X_scaled = predictor.scaler.transform(X)
        
        prediction = predictor.predict(X_scaled)[0]
        proba = predictor.predict_proba(X_scaled)[0]
        proba_manque = float(proba[1])
        
        features_dict = {f: float(v) for f, v in zip(predictor.features, features_list)}
        
        result = {
            'status': 'success',
            'prediction': int(prediction),
            'resultat': '⚠️ Manque détecté' if prediction == 1 else '✅ Commande conforme',
            'probabilite_manque': proba_manque,
            'features': features_dict
        }
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO orders (user_id, order_reference, product_name, quantity_ordered, quantity_stock, 
                                price, prediction, probability, status, client_email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.user_id,
            data.get('reference', 'UNKNOWN'),
            data.get('produit', 'Produit'),
            facture.get('quantite', 0),
            stock.get('quantite', 0),
            facture.get('prix', 0),
            prediction,
            proba_manque,
            'conforme' if prediction == 0 else 'manque',
            data.get('client_email', '')
        ))
        
        order_id = cursor.lastrowid
        
        cursor.execute('''
            INSERT INTO emails (order_id, direction, recipient, subject, content, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            order_id,
            'out',
            data.get('client_email', ''),
            f"Rapport de commande {data.get('reference', 'UNKNOWN')}",
            f"Votre commande est {result['resultat']}. Probabilité de manque: {proba_manque:.1%}",
            'sent'
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/history', methods=['GET'])
@require_auth
def api_history():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM orders 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 100
        ''', (request.user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        historique = []
        for row in rows:
            historique.append({
                'id': row['id'],
                'date': row['created_at'],
                'reference': row['order_reference'],
                'produit': row['product_name'],
                'quantite_facture': row['quantity_ordered'],
                'quantite_stock': row['quantity_stock'],
                'prix': row['price'],
                'prediction': row['prediction'],
                'probabilite': row['probability'],
                'status': row['status'],
                'client_email': row['client_email']
            })
        
        return jsonify({'status': 'success', 'historique': historique})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/emails', methods=['GET'])
@require_auth
def api_emails():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e.*, o.order_reference 
            FROM emails e
            LEFT JOIN orders o ON e.order_id = o.id
            WHERE o.user_id = ? OR e.order_id = 0
            ORDER BY e.sent_at DESC 
            LIMIT 100
        ''', (request.user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        envoyes = []
        for row in rows:
            envoyes.append({
                'id': row['id'],
                'date': row['sent_at'],
                'destinataire': row['recipient'],
                'objet': row['subject'],
                'contenu': row['content'],
                'statut': row['status'],
                'commande': row['order_reference'] if row['order_reference'] else 'N/A'
            })
        
        return jsonify({'status': 'success', 'recus': [], 'envoyes': envoyes})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/send-email', methods=['POST'])
@require_auth
def api_send_email():
    try:
        data = request.get_json()
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO emails (order_id, direction, recipient, subject, content, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            0,
            'out',
            data.get('destinataire', ''),
            data.get('objet', ''),
            data.get('message', ''),
            'sent'
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Email envoyé'})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/reports', methods=['GET'])
@require_auth
def api_reports():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM orders 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 50
        ''', (request.user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        rapports = []
        for row in rows:
            rapports.append({
                'id': row['id'],
                'date': row['created_at'],
                'type': 'Vérification',
                'reference': row['order_reference'],
                'prediction': row['prediction'],
                'status': row['status'],
                'probabilite': row['probability']
            })
        
        return jsonify({'status': 'success', 'rapports': rapports})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/generate-report', methods=['POST'])
@require_auth
def api_generate_report():
    try:
        data = request.get_json()
        period = data.get('period', 'month')
        
        if period == 'week':
            start_date = datetime.now() - timedelta(days=7)
        elif period == 'month':
            start_date = datetime.now() - timedelta(days=30)
        else:
            start_date = datetime.now() - timedelta(days=365)
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM orders 
            WHERE user_id = ? AND created_at >= ?
            ORDER BY created_at DESC
        ''', (request.user_id, start_date.isoformat()))
        
        rows = cursor.fetchall()
        
        total = len(rows)
        manques = sum(1 for r in rows if r['prediction'] == 1)
        
        report_content = {
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': datetime.now().isoformat(),
            'total_orders': total,
            'manques': manques,
            'taux_manque': manques / total * 100 if total > 0 else 0
        }
        
        conn.close()
        
        return jsonify({'status': 'success', 'report': report_content})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
@require_auth
def api_stats():
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM orders 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT 100
        ''', (request.user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        total = len(rows)
        manques = sum(1 for r in rows if r['prediction'] == 1)
        conformes = total - manques
        
        jours = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
        evolution = [0] * 7
        
        for row in rows:
            try:
                date = datetime.fromisoformat(row['created_at'])
                evolution[date.weekday()] += 1
            except:
                pass
        
        return jsonify({
            'status': 'success',
            'total': total,
            'manques': manques,
            'conformes': conformes,
            'taux': manques / total * 100 if total > 0 else 0,
            'performances': [0.86, 1.0, 0.91, 1.0],
            'evolution': evolution,
            'jours': jours
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/config', methods=['GET', 'POST'])
@require_auth
def api_config():
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('SELECT * FROM companies WHERE user_id = ?', (request.user_id,))
        company = cursor.fetchone()
        conn.close()
        
        if company:
            return jsonify({
                'status': 'success',
                'config': {
                    'company_name': company['company_name'],
                    'storage_type': company['storage_type'],
                    'email_stock_manager': company['email_stock_manager'],
                    'email_notification': company['email_notification']
                }
            })
        return jsonify({'status': 'success', 'config': {}})
    
    else:
        data = request.get_json()
        
        cursor.execute('SELECT id FROM companies WHERE user_id = ?', (request.user_id,))
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute('''
                UPDATE companies 
                SET company_name = ?, storage_type = ?, email_stock_manager = ?, email_notification = ?
                WHERE user_id = ?
            ''', (
                data.get('company_name', ''),
                data.get('storage_type', ''),
                data.get('email_stock_manager', ''),
                data.get('email_notification', ''),
                request.user_id
            ))
        else:
            cursor.execute('''
                INSERT INTO companies (user_id, company_name, storage_type, email_stock_manager, email_notification)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                request.user_id,
                data.get('company_name', ''),
                data.get('storage_type', ''),
                data.get('email_stock_manager', ''),
                data.get('email_notification', '')
            ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Configuration sauvegardée'})

# ==================== ROUTES SECTIONS DASHBOARD ====================

@app.route('/api/dashboard/section/<section>', methods=['GET'])
@require_auth
def dashboard_section(section):
    allowed_sections = {
        'admin': ['dashboard', 'reception', 'reception_reelle', 'matching', 'historique', 'guide', 'stock', 'livraison', 'date-livraison', 'gestion-utilisateurs', 'stats', 'admin-dashboard', 'gestion-clients', 'gestion-emails', 'gestion-factures','gestion-clients-unifie'],
        'stock': ['dashboard', 'reception', 'reception_reelle', 'matching', 'historique', 'guide', 'stock', 'livraison', 'date-livraison'],
        'user': ['dashboard', 'historique', 'guide', 'livraison', 'date-livraison']
    }
    
    if section not in allowed_sections.get(request.user_role, []):
        return "<div class='dashboard-card'><p>⛔ Accès non autorisé</p></div>", 403
    
    templates = {
        'dashboard': 'dashboard/sections/dashboard.html',
        'reception': 'dashboard/sections/reception.html',
        'reception_reelle': 'dashboard/sections/reception_reelle.html',
        'matching': 'dashboard/sections/matching.html', 
        'historique': 'dashboard/sections/historique.html',
        'guide': 'dashboard/sections/guide.html',
        'stock': 'dashboard/sections/stock.html',
        'livraison': 'dashboard/sections/livraison.html',
        'date-livraison': 'dashboard/sections/date-livraison.html',
        'gestion-clients': 'dashboard/sections/gestion-clients.html',
        'stats': 'dashboard/sections/stats.html',
        'gestion-emails': 'dashboard/sections/gestion-emails.html',
        'gestion-clients-unifie': 'dashboard/sections/gestion-clients-unifie.html',
        'gestion-factures': 'dashboard/sections/gestion-factures.html',
        'admin-dashboard': 'dashboard/sections/admin-dashboard.html'
    }
    
    template = templates.get(section, 'dashboard/sections/dashboard.html')
    try:
        return render_template(template, role=request.user_role)
    except Exception as e:
        return f"<div class='dashboard-card'><p>❌ Erreur: {str(e)}</p></div>", 500

# ==================== ROUTES AGENDA (Livraisons) ====================

@app.route('/api/deliveries', methods=['GET', 'POST', 'DELETE'])
@require_auth
def api_deliveries():
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('''
            SELECT * FROM deliveries 
            WHERE user_id = ? 
            ORDER BY delivery_date DESC
        ''', (request.user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        deliveries = []
        for row in rows:
            deliveries.append({
                'id': row['id'],
                'date': row['delivery_date'],
                'time': row['delivery_time'],
                'description': row['description'],
                'facture_name': row['facture_name'],
                'facture_data': row['facture_data'],
                'facture_type': row['facture_type']
            })
        
        return jsonify({'status': 'success', 'deliveries': deliveries})
    
    elif request.method == 'POST':
        data = request.get_json()
        
        cursor.execute('''
            INSERT INTO deliveries (user_id, delivery_date, delivery_time, description, facture_name, facture_data, facture_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.user_id,
            data.get('date', ''),
            data.get('time', ''),
            data.get('description', ''),
            data.get('facture_name', ''),
            data.get('facture_data', ''),
            data.get('facture_type', '')
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Livraison ajoutée'})
    
    else:  # DELETE
        delivery_id = request.args.get('id')
        cursor.execute('DELETE FROM deliveries WHERE id = ? AND user_id = ?', (delivery_id, request.user_id))
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Livraison supprimée'})

# ==================== ROUTES STOCK ====================

@app.route('/api/stock', methods=['GET', 'POST', 'DELETE'])
@require_auth
def api_stock():
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('SELECT * FROM stock_items WHERE user_id = ?', (request.user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        stock = []
        for row in rows:
            stock.append({
                'id': row['id'],
                'product_name': row['product_name'],
                'reference': row['reference'],
                'quantity': row['quantity'],
                'location': row['location']
            })
        
        return jsonify({'status': 'success', 'stock': stock})
    
    elif request.method == 'POST':
        data = request.get_json()
        
        cursor.execute('''
            INSERT INTO stock_items (user_id, product_name, reference, quantity, location)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            request.user_id,
            data.get('product_name', ''),
            data.get('reference', ''),
            data.get('quantity', 0),
            data.get('location', '')
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Stock ajouté'})
    
    else:
        stock_id = request.args.get('id')
        cursor.execute('DELETE FROM stock_items WHERE id = ? AND user_id = ?', (stock_id, request.user_id))
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Stock supprimé'})

# ==================== ROUTES RÉCEPTION RÉELLE ====================

@app.route('/api/commandes-recues', methods=['GET', 'POST', 'DELETE'])
@require_auth
def api_commandes_recues():
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('''
            SELECT * FROM commandes_recues 
            WHERE user_id = ? 
            ORDER BY date_ajout DESC
        ''', (request.user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        commandes = []
        for row in rows:
            commandes.append({
                'id': row['id'],
                'nom': row['nom'],
                'reference': row['reference'],
                'fournisseur': row['fournisseur'],
                'date_reception': row['date_reception'],
                'produits': json.loads(row['produits']) if row['produits'] else [],
                'chemin_fichier': row['chemin_fichier'],
                'nom_fichier': row['nom_fichier'],
                'date_ajout': row['date_ajout'],
                'ajoute_par': row['ajoute_par']
            })
        
        return jsonify({'status': 'success', 'commandes': commandes})
    
    elif request.method == 'POST':
        data = request.get_json()
        
        cursor.execute('''
            INSERT INTO commandes_recues (user_id, nom, reference, fournisseur, date_reception, produits, chemin_fichier, nom_fichier, date_ajout, ajoute_par)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.user_id,
            data.get('nom', ''),
            data.get('reference', ''),
            data.get('fournisseur', ''),
            data.get('date_reception', ''),
            json.dumps(data.get('produits', [])),
            data.get('chemin_fichier', ''),
            data.get('nom_fichier', ''),
            datetime.now().isoformat(),
            data.get('ajoute_par', '')
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Commande enregistrée'})
    
    else:  # DELETE
        commande_id = request.args.get('id')
        cursor.execute('DELETE FROM commandes_recues WHERE id = ? AND user_id = ?', (commande_id, request.user_id))
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Commande supprimée'})

# ==================== ROUTES D'AUDIT ET ADMIN ====================

@app.route('/api/admin/stats', methods=['GET'])
@require_auth
def admin_stats():
    """Statistiques avancées pour l'admin"""
    if request.user_role != 'admin':
        return jsonify({'status': 'error', 'message': 'Accès non autorisé'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as total FROM users')
    total_users = cursor.fetchone()['total'] if cursor.fetchone() else 0
    
    cursor.execute('SELECT COUNT(*) as total FROM commandes_recues')
    total_receptions = cursor.fetchone()['total'] if cursor.fetchone() else 0
    
    cursor.execute('SELECT COUNT(*) as total FROM factures_recues')
    total_factures = cursor.fetchone()['total'] if cursor.fetchone() else 0
    
    cursor.execute('SELECT action, COUNT(*) as count FROM audit_logs GROUP BY action')
    actions_rows = cursor.fetchall()
    actions_stats = {row['action']: row['count'] for row in actions_rows} if actions_rows else {}
    
    cursor.execute('SELECT COUNT(*) as count FROM audit_logs WHERE created_at > datetime("now", "-1 day")')
    last_24h = cursor.fetchone()['count'] if cursor.fetchone() else 0
    
    cursor.execute('''
        SELECT user_name, COUNT(*) as actions 
        FROM audit_logs 
        WHERE created_at > datetime("now", "-7 days")
        GROUP BY user_name 
        ORDER BY actions DESC 
        LIMIT 5
    ''')
    top_users = [{'name': row['user_name'], 'actions': row['actions']} for row in cursor.fetchall()]
    
    conn.close()
    
    return jsonify({
        'status': 'success',
        'stats': {
            'total_users': total_users,
            'total_receptions': total_receptions,
            'total_factures': total_factures,
            'actions_last_24h': last_24h,
            'actions_by_type': actions_stats,
            'top_active_users': top_users
        }
    })

@app.route('/api/admin/logs', methods=['GET'])
@require_auth
def admin_logs():
    """Récupère les logs d'audit avec filtres"""
    if request.user_role != 'admin':
        return jsonify({'status': 'error', 'message': 'Accès non autorisé'}), 403
    
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    action_filter = request.args.get('action', '')
    user_filter = request.args.get('user', '')
    
    conn = get_db()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM audit_logs WHERE 1=1'
    params = []
    
    if action_filter:
        query += ' AND action = ?'
        params.append(action_filter)
    
    if user_filter:
        query += ' AND user_name LIKE ?'
        params.append(f'%{user_filter}%')
    
    query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    
    logs = []
    for row in rows:
        logs.append({
            'id': row['id'],
            'user_name': row['user_name'],
            'user_role': row['user_role'],
            'action': row['action'],
            'entity_type': row['entity_type'],
            'entity_id': row['entity_id'],
            'details': row['details'],
            'ip_address': row['ip_address'],
            'created_at': row['created_at']
        })
    
    cursor.execute('SELECT COUNT(*) as total FROM audit_logs')
    total = cursor.fetchone()['total']
    
    conn.close()
    
    return jsonify({
        'status': 'success',
        'logs': logs,
        'total': total,
        'limit': limit,
        'offset': offset
    })

@app.route('/api/admin/logs/export', methods=['GET'])
@require_auth
def admin_logs_export():
    """Exporte les logs au format CSV"""
    if request.user_role != 'admin':
        return jsonify({'status': 'error', 'message': 'Accès non autorisé'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT created_at, user_name, user_role, action, entity_type, entity_id, details, ip_address
        FROM audit_logs 
        ORDER BY created_at DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Utilisateur', 'Rôle', 'Action', 'Type', 'ID', 'Détails', 'IP'])
    
    for row in rows:
        writer.writerow([
            row['created_at'], row['user_name'], row['user_role'],
            row['action'], row['entity_type'], row['entity_id'],
            row['details'], row['ip_address']
        ])
    
    return jsonify({
        'status': 'success',
        'csv': output.getvalue(),
        'filename': f'audit_logs_{datetime.now().strftime("%Y%m%d")}.csv'
    })

@app.route('/api/admin/sessions', methods=['GET'])
@require_auth
def admin_sessions():
    """Récupère les sessions actives"""
    if request.user_role != 'admin':
        return jsonify({'status': 'error', 'message': 'Accès non autorisé'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.*, u.username, u.role 
        FROM user_sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.logout_at IS NULL
        AND s.last_activity > datetime('now', '-30 minutes')
        ORDER BY s.last_activity DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    sessions = []
    for row in rows:
        sessions.append({
            'id': row['id'],
            'username': row['username'],
            'role': row['role'],
            'ip_address': row['ip_address'],
            'login_at': row['login_at'],
            'last_activity': row['last_activity']
        })
    
    return jsonify({'status': 'success', 'sessions': sessions})

# ==================== ROUTES GESTION UTILISATEURS ====================

@app.route('/api/users', methods=['GET', 'POST'])
@require_auth
def api_users_list():
    """Liste ou ajoute des utilisateurs (admin uniquement)"""
    if request.user_role != 'admin':
        return jsonify({'status': 'error', 'message': 'Accès non autorisé'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('SELECT id, username, email, company, storage_type, role, created_at FROM users')
        rows = cursor.fetchall()
        conn.close()
        
        users = []
        for row in rows:
            users.append({
                'id': row['id'],
                'username': row['username'],
                'email': row['email'],
                'company': row['company'],
                'storage_type': row['storage_type'],
                'role': row['role'],
                'created_at': row['created_at']
            })
        
        return jsonify({'status': 'success', 'users': users})
    
    else:  # POST
        data = request.get_json()
        
        cursor.execute('SELECT id FROM users WHERE username = ?', (data.get('username'),))
        if cursor.fetchone():
            conn.close()
            return jsonify({'status': 'error', 'message': 'Nom d\'utilisateur déjà existant'}), 400
        
        hashed = hash_password(data.get('password', 'password123'))
        cursor.execute('''
            INSERT INTO users (username, password, email, company, storage_type, role)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            data.get('username', ''),
            hashed,
            data.get('email', ''),
            data.get('company', ''),
            data.get('storage_type', ''),
            data.get('role', 'user')
        ))
        
        user_id = cursor.lastrowid
        
        cursor.execute('''
            INSERT INTO companies (user_id, company_name, storage_type, email_stock_manager, email_notification)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, data.get('company', ''), data.get('storage_type', ''), 
              data.get('email_stock', ''), data.get('email_notif', '')))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Utilisateur ajouté'})

@app.route('/api/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
@require_auth
def api_user_detail(user_id):
    """Récupère, modifie ou supprime un utilisateur (admin uniquement)"""
    if request.user_role != 'admin':
        return jsonify({'status': 'error', 'message': 'Accès non autorisé'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('SELECT id, username, email, company, storage_type, role, created_at FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return jsonify({
                'status': 'success',
                'user': {
                    'id': row['id'],
                    'username': row['username'],
                    'email': row['email'],
                    'company': row['company'],
                    'storage_type': row['storage_type'],
                    'role': row['role'],
                    'created_at': row['created_at']
                }
            })
        return jsonify({'status': 'error', 'message': 'Utilisateur non trouvé'}), 404
    
    elif request.method == 'PUT':
        data = request.get_json()
        
        updates = []
        params = []
        
        if 'username' in data:
            updates.append('username = ?')
            params.append(data['username'])
        if 'email' in data:
            updates.append('email = ?')
            params.append(data['email'])
        if 'company' in data:
            updates.append('company = ?')
            params.append(data['company'])
        if 'storage_type' in data:
            updates.append('storage_type = ?')
            params.append(data['storage_type'])
        if 'role' in data:
            updates.append('role = ?')
            params.append(data['role'])
        if 'password' in data and data['password']:
            updates.append('password = ?')
            params.append(hash_password(data['password']))
        
        if updates:
            params.append(user_id)
            cursor.execute(f'UPDATE users SET {", ".join(updates)} WHERE id = ?', params)
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Utilisateur modifié'})
    
    else:  # DELETE
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Utilisateur supprimé'})

@app.route('/api/users/<int:user_id>/reset-password', methods=['POST'])
@require_auth
def api_reset_password(user_id):
    """Réinitialise le mot de passe d'un utilisateur"""
    if request.user_role != 'admin':
        return jsonify({'status': 'error', 'message': 'Accès non autorisé'}), 403
    
    data = request.get_json()
    new_password = data.get('password')
    
    if not new_password or len(new_password) < 4:
        return jsonify({'status': 'error', 'message': 'Mot de passe trop court (minimum 4 caractères)'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    hashed = hash_password(new_password)
    cursor.execute('UPDATE users SET password = ? WHERE id = ?', (hashed, user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success', 'message': 'Mot de passe réinitialisé'})

@app.route('/api/users/me', methods=['GET', 'PUT'])
@require_auth
def api_user_me():
    """Récupère ou modifie le profil de l'utilisateur connecté"""
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('SELECT id, username, email, company, storage_type, role, created_at FROM users WHERE id = ?', (request.user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return jsonify({
                'status': 'success',
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'company': user['company'],
                    'storage_type': user['storage_type'],
                    'role': user['role'],
                    'created_at': user['created_at']
                }
            })
        return jsonify({'status': 'error', 'message': 'Utilisateur non trouvé'}), 404
    
    else:  # PUT
        data = request.get_json()
        
        if 'password' in data and data['password']:
            if len(data['password']) < 4:
                return jsonify({'status': 'error', 'message': 'Mot de passe trop court'}), 400
            hashed = hash_password(data['password'])
            cursor.execute('UPDATE users SET password = ? WHERE id = ?', (hashed, request.user_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Profil mis à jour'})

# ==================== ROUTES POUR LA GESTION DES CLIENTS EXTERNES ====================

@app.route('/api/clients', methods=['GET', 'POST'])
@require_auth
def api_clients_externes():
    """Gère les clients externes (admin uniquement)"""
    if request.user_role != 'admin':
        return jsonify({'status': 'error', 'message': 'Accès non autorisé'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('''
            SELECT id, email, nom, prenom, sexe, nationalite, telephone, 
                   adresse, date_inscription, statut 
            FROM clients_externes 
            ORDER BY date_inscription DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        clients = []
        for row in rows:
            clients.append({
                'id': row['id'],
                'email': row['email'],
                'nom': row['nom'],
                'prenom': row['prenom'],
                'sexe': row['sexe'],
                'nationalite': row['nationalite'],
                'telephone': row['telephone'],
                'adresse': row['adresse'],
                'date_inscription': row['date_inscription'],
                'statut': row['statut']
            })
        
        return jsonify({'status': 'success', 'clients': clients})
    
    else:  # POST
        data = request.get_json()
        
        cursor.execute('SELECT id FROM clients_externes WHERE email = ?', (data.get('email'),))
        if cursor.fetchone():
            conn.close()
            return jsonify({'status': 'error', 'message': 'Email déjà existant'}), 400
        
        client_folder = get_client_folder(data.get('email'))
        
        profil = {
            'email': data.get('email'),
            'nom': data.get('nom'),
            'prenom': data.get('prenom'),
            'sexe': data.get('sexe'),
            'nationalite': data.get('nationalite'),
            'telephone': data.get('telephone'),
            'adresse': data.get('adresse'),
            'date_creation': datetime.now().isoformat()
        }
        
        with open(os.path.join(client_folder, 'identite', 'profil.json'), 'w', encoding='utf-8') as f:
            json.dump(profil, f, indent=2, ensure_ascii=False)
        
        cursor.execute('''
            INSERT INTO clients_externes (email, nom, prenom, sexe, nationalite, telephone, adresse, dossier_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('email'),
            data.get('nom'),
            data.get('prenom'),
            data.get('sexe'),
            data.get('nationalite'),
            data.get('telephone'),
            data.get('adresse'),
            client_folder
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Client ajouté avec succès'})

@app.route('/api/clients/<int:client_id>', methods=['GET', 'PUT', 'DELETE'])
@require_auth
def api_client_detail(client_id):
    """Détail, modification ou suppression d'un client"""
    if request.user_role != 'admin':
        return jsonify({'status': 'error', 'message': 'Accès non autorisé'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('''
            SELECT id, email, nom, prenom, sexe, nationalite, telephone, 
                   adresse, date_inscription, statut, dossier_path
            FROM clients_externes 
            WHERE id = ?
        ''', (client_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return jsonify({
                'status': 'success',
                'client': {
                    'id': row['id'],
                    'email': row['email'],
                    'nom': row['nom'],
                    'prenom': row['prenom'],
                    'sexe': row['sexe'],
                    'nationalite': row['nationalite'],
                    'telephone': row['telephone'],
                    'adresse': row['adresse'],
                    'date_inscription': row['date_inscription'],
                    'statut': row['statut'],
                    'dossier_path': row['dossier_path']
                }
            })
        return jsonify({'status': 'error', 'message': 'Client non trouvé'}), 404
    
    elif request.method == 'PUT':
        data = request.get_json()
        
        cursor.execute('''
            UPDATE clients_externes 
            SET nom = ?, prenom = ?, sexe = ?, nationalite = ?, telephone = ?, adresse = ?
            WHERE id = ?
        ''', (
            data.get('nom'),
            data.get('prenom'),
            data.get('sexe'),
            data.get('nationalite'),
            data.get('telephone'),
            data.get('adresse'),
            client_id
        ))
        
        cursor.execute('SELECT email, dossier_path FROM clients_externes WHERE id = ?', (client_id,))
        row = cursor.fetchone()
        if row:
            profil_path = os.path.join(row['dossier_path'], 'identite', 'profil.json')
            if os.path.exists(profil_path):
                with open(profil_path, 'r', encoding='utf-8') as f:
                    profil = json.load(f)
                profil.update({
                    'nom': data.get('nom'),
                    'prenom': data.get('prenom'),
                    'sexe': data.get('sexe'),
                    'nationalite': data.get('nationalite'),
                    'telephone': data.get('telephone'),
                    'adresse': data.get('adresse')
                })
                with open(profil_path, 'w', encoding='utf-8') as f:
                    json.dump(profil, f, indent=2, ensure_ascii=False)
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Client modifié'})
    
    else:  # DELETE
        cursor.execute('SELECT dossier_path FROM clients_externes WHERE id = ?', (client_id,))
        row = cursor.fetchone()
        if row and row['dossier_path'] and os.path.exists(row['dossier_path']):
            shutil.rmtree(row['dossier_path'])
        
        cursor.execute('DELETE FROM clients_externes WHERE id = ?', (client_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Client supprimé'})

@app.route('/api/clients/<int:client_id>/statistiques', methods=['GET'])
@require_auth
def api_client_statistiques(client_id):
    """Récupère les statistiques d'un client"""
    if request.user_role != 'admin':
        return jsonify({'status': 'error', 'message': 'Accès non autorisé'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as total FROM emails_clients WHERE client_id = ?', (client_id,))
    row = cursor.fetchone()
    total_emails = row['total'] if row else 0
    
    cursor.execute('SELECT COUNT(*) as total FROM factures_clients WHERE client_id = ?', (client_id,))
    row = cursor.fetchone()
    total_factures = row['total'] if row else 0
    
    cursor.execute('SELECT COUNT(*) as total FROM rapports_clients WHERE client_id = ?', (client_id,))
    row = cursor.fetchone()
    total_rapports = row['total'] if row else 0
    
    cursor.execute('''
        SELECT MAX(date_envoi) as last_activity 
        FROM emails_clients 
        WHERE client_id = ?
    ''', (client_id,))
    row = cursor.fetchone()
    last_email = row['last_activity'] if row else None
    
    conn.close()
    
    return jsonify({
        'status': 'success',
        'stats': {
            'total_emails': total_emails,
            'total_factures': total_factures,
            'total_rapports': total_rapports,
            'last_activity': last_email
        }
    })

@app.route('/api/clients/<int:client_id>/dossier/<path:subpath>', methods=['GET'])
@require_auth
def api_client_dossier(client_id, subpath):
    """Récupère un fichier du dossier client"""
    if request.user_role != 'admin':
        return jsonify({'status': 'error', 'message': 'Accès non autorisé'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT dossier_path FROM clients_externes WHERE id = ?', (client_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return jsonify({'status': 'error', 'message': 'Client non trouvé'}), 404
    
    file_path = os.path.join(row['dossier_path'], subpath)
    
    if not os.path.exists(file_path):
        return jsonify({'status': 'error', 'message': 'Fichier non trouvé'}), 404
    
    if file_path.endswith('.json'):
        with open(file_path, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    else:
        return send_file(file_path)

# ==================== WEBHOOKS ====================

@app.route('/api/webhook/email', methods=['POST'])
def webhook_reception_email():
    """Webhook public pour recevoir les emails des clients"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': 'Aucune donnée reçue'}), 400
        
        client_email = data.get('from_email', '')
        sujet = data.get('subject', '')
        contenu = data.get('body', '')
        reference = data.get('reference', '')
        
        if not reference:
            reference = extract_reference_from_subject(sujet)
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, nom, prenom, dossier_path FROM clients_externes WHERE email = ?', (client_email,))
        client = cursor.fetchone()
        
        if not client:
            conn.close()
            return jsonify({
                'status': 'error', 
                'message': f'Client non trouvé: {client_email}. Veuillez d\'abord enregistrer ce client.'
            }), 404
        
        client_id = client['id']
        client_dossier = client['dossier_path']
        
        now = datetime.now()
        email_folder = os.path.join(client_dossier, 'emails', 'recus', now.strftime('%Y/%m'))
        os.makedirs(email_folder, exist_ok=True)
        
        email_filename = f"{now.strftime('%Y%m%d_%H%M%S')}.json"
        email_path = os.path.join(email_folder, email_filename)
        
        email_data = {
            'from': client_email,
            'subject': sujet,
            'body': contenu,
            'reference': reference,
            'date': now.isoformat()
        }
        
        with open(email_path, 'w', encoding='utf-8') as f:
            json.dump(email_data, f, indent=2, ensure_ascii=False)
        
        cursor.execute('''
            INSERT INTO emails_clients (client_id, direction, sujet, contenu, reference_facture, statut)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (client_id, 'recu', sujet, contenu, reference, 'recu'))
        
        email_id = cursor.lastrowid
        
        if reference:
            cursor.execute('''
                INSERT INTO agenda_clients (client_id, date_evenement, type_evenement, reference, statut)
                VALUES (?, ?, ?, ?, ?)
            ''', (client_id, now.isoformat(), 'reception_email', reference, 'traite'))
        
        cursor.execute('''
            INSERT INTO historique_clients (client_id, action, details, utilisateur)
            VALUES (?, ?, ?, ?)
        ''', (client_id, 'reception_email', f'Email reçu: {sujet}', 'systeme'))
        
        conn.commit()
        conn.close()
        
        # Ajouter une notification
        notification = {
            'id': len(notifications) + 1,
            'user_id': request.user_id if hasattr(request, 'user_id') else 1,
            'title': 'Nouvel email reçu',
            'message': f'Email de {client_email} - {sujet[:50]}',
            'type': 'info',
            'read': False,
            'created_at': now.isoformat()
        }
        notifications.append(notification)
        
        return jsonify({
            'status': 'success',
            'message': 'Email traité avec succès',
            'client_id': client_id,
            'email_id': email_id,
            'reference': reference
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ==================== WEBHOOK AVEC PIÈCE JOINTE ====================

@app.route('/api/webhook/email-with-attachment', methods=['POST'])
def webhook_reception_email_with_attachment():
    """Webhook pour recevoir des emails avec pièces jointes (factures Excel)"""
    try:
        print("📧 Webhook appelé avec pièce jointe")
        
        # Récupérer les données
        if 'file' in request.files:
            fichier = request.files['file']
            client_email = request.form.get('email', '')
            sujet = request.form.get('subject', '')
            reference = request.form.get('reference', '')
            file_content = fichier.read()
            filename = fichier.filename
            print(f"   - Fichier reçu: {filename}")
        else:
            data = request.get_json()
            if not data:
                return jsonify({'status': 'error', 'message': 'Aucune donnée'}), 400
            client_email = data.get('from_email', '')
            sujet = data.get('subject', '')
            reference = data.get('reference', '')
            fichier_base64 = data.get('attachment_base64', '')
            filename = data.get('attachment_filename', 'facture.xlsx')
            file_content = base64.b64decode(fichier_base64) if fichier_base64 else None
            print(f"   - Email reçu: {client_email}, Sujet: {sujet}")
        
        if not client_email:
            return jsonify({'status': 'error', 'message': 'Email client requis'}), 400
        
        # Vérifier le client
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, nom, prenom, dossier_path FROM clients_externes WHERE email = ?', (client_email,))
        client = cursor.fetchone()
        
        if not client:
            conn.close()
            return jsonify({'status': 'error', 'message': f'Client non trouvé: {client_email}'}), 404
        
        client_id = client['id']
        client_dossier = client['dossier_path']
        now = datetime.now()
        
        # ==================== GÉNÉRER UNE RÉFÉRENCE UNIQUE ====================
        # Extraire ou générer une référence
        if reference:
            # Utiliser la référence fournie
            pass
        else:
            # Essayer d'extraire du sujet
            reference = extract_reference_from_subject(sujet)
        
        # Si toujours pas de référence, en générer une unique avec timestamp
        if not reference:
            reference = f"EMAIL_{now.strftime('%Y%m%d_%H%M%S')}"
        else:
            # Ajouter un timestamp pour garantir l'unicité
            reference = f"{reference}_{now.strftime('%Y%m%d_%H%M%S')}"
        
        print(f"   - Référence unique générée: {reference}")
        
        # ==================== EXTRAIRE LE CONTENU EXCEL ====================
        extraction_result = {'success': False, 'produits': [], 'total_produits': 0, 'colonnes': []}
        if file_content:
            extraction_result = extract_excel_from_email(file_content, filename)
            print(f"   - Extraction: {extraction_result.get('total_produits', 0)} produits trouvés")
            for p in extraction_result.get('produits', []):
                print(f"      📦 {p.get('reference')} - {p.get('nom')} - {p.get('quantite')}")
        
        # Sauvegarder le fichier Excel
        facture_path = None
        if file_content:
            facture_folder = os.path.join(client_dossier, 'factures', now.strftime('%Y/%m'))
            os.makedirs(facture_folder, exist_ok=True)
            facture_filename = f"facture_{reference}_{now.strftime('%Y%m%d_%H%M%S')}.xlsx"
            facture_path = os.path.join(facture_folder, facture_filename)
            with open(facture_path, 'wb') as f:
                f.write(file_content)
            print(f"   - Facture sauvegardée: {facture_path}")
        
        # Préparer les lignes pour factures_recues
        headers = extraction_result.get('colonnes', ['référence', 'produit', 'quantité', 'prix', 'total'])
        lignes = []
        
        if extraction_result.get('success') and extraction_result.get('produits'):
            for p in extraction_result['produits']:
                lignes.append([
                    p.get('reference', ''),
                    p.get('nom', ''),
                    p.get('quantite', 0),
                    p.get('prix', 0),
                    p.get('quantite', 0) * p.get('prix', 0)
                ])
        
        # 1. Ajouter à factures_recues (section Réception Factures)
        cursor.execute('''
            INSERT INTO factures_recues (user_id, nom, reference_reception, informations, statut, contenu, chemin_fichier, nom_fichier, date_ajout, ajoute_par)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            1,  # user_id admin
            filename,
            reference,  # référence unique
            f"Facture reçue par email de {client_email}",
            'en-attente',
            json.dumps({'en_tete': headers, 'lignes': lignes}),
            facture_path,
            filename,
            now.isoformat(),
            'System (Email)'
        ))
        
        facture_recue_id = cursor.lastrowid
        print(f"   ✅ Facture ajoutée à factures_recues (ID: {facture_recue_id}) avec référence {reference}")
        
        # 2. Ajouter à factures_clients (section Factures clients)
        cursor.execute('''
            INSERT INTO factures_clients (client_id, reference, chemin_fichier, date_reception, statut, contenu_extraie)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (client_id, reference, facture_path, now.isoformat(), 'recue', 
              json.dumps(extraction_result.get('produits', [])) if extraction_result.get('success') else None))
        
        facture_client_id = cursor.lastrowid
        
        # 3. Enregistrer l'email
        cursor.execute('''
            INSERT INTO emails_clients (client_id, direction, sujet, contenu, pieces_jointes, reference_facture, statut)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (client_id, 'recu', sujet, '', json.dumps([filename]), reference, 'recu'))
        
        email_id = cursor.lastrowid
        
        # Sauvegarder l'email
        email_folder = os.path.join(client_dossier, 'emails', 'recus', now.strftime('%Y/%m'))
        os.makedirs(email_folder, exist_ok=True)
        email_file = os.path.join(email_folder, f'{now.strftime("%Y%m%d_%H%M%S")}.json')
        with open(email_file, 'w', encoding='utf-8') as f:
            json.dump({'id': email_id, 'from': client_email, 'subject': sujet, 'reference': reference, 'date': now.isoformat()}, f, indent=2)
        
        conn.commit()
        conn.close()
        
        # Notification
        global notifications
        notification = {
            'id': len(notifications) + 1,
            'user_id': 1,
            'title': '📥 Nouvelle facture reçue',
            'message': f'Facture {reference} reçue de {client_email} - {extraction_result.get("total_produits", 0)} produits',
            'type': 'success',
            'read': False,
            'created_at': now.isoformat()
        }
        notifications.append(notification)
        
        return jsonify({
            'status': 'success',
            'message': 'Facture reçue et traitée',
            'facture_recue_id': facture_recue_id,
            'facture_client_id': facture_client_id,
            'email_id': email_id,
            'reference': reference,
            'produits_extraits': extraction_result.get('total_produits', 0),
            'extraction': extraction_result
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== ROUTES FACTURES CLIENTS ====================

@app.route('/api/clients/<int:client_id>/factures', methods=['GET'])
@require_auth
def api_client_factures(client_id):
    """Récupère toutes les factures d'un client"""
    if request.user_role != 'admin':
        return jsonify({'status': 'error', 'message': 'Accès non autorisé'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, reference, chemin_fichier, date_reception, statut, contenu_extraie
        FROM factures_clients 
        WHERE client_id = ?
        ORDER BY date_reception DESC
    ''', (client_id,))
    rows = cursor.fetchall()
    conn.close()
    
    factures = []
    for row in rows:
        factures.append({
            'id': row['id'],
            'reference': row['reference'],
            'chemin': row['chemin_fichier'],
            'date': row['date_reception'],
            'statut': row['statut'],
            'produits': json.loads(row['contenu_extraie']) if row['contenu_extraie'] else []
        })
    
    return jsonify({'status': 'success', 'factures': factures})

@app.route('/api/clients/<int:client_id>/emails', methods=['GET'])
@require_auth
def api_client_emails(client_id):
    """Récupère tous les emails d'un client"""
    if request.user_role != 'admin':
        return jsonify({'status': 'error', 'message': 'Accès non autorisé'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, direction, sujet, contenu, reference_facture, date_envoi, statut
        FROM emails_clients 
        WHERE client_id = ?
        ORDER BY date_envoi DESC
    ''', (client_id,))
    rows = cursor.fetchall()
    conn.close()
    
    emails = []
    for row in rows:
        emails.append({
            'id': row['id'],
            'direction': row['direction'],
            'sujet': row['sujet'],
            'contenu': row['contenu'],
            'reference': row['reference_facture'],
            'date': row['date_envoi'],
            'statut': row['statut']
        })
    
    return jsonify({'status': 'success', 'emails': emails})

@app.route('/api/factures/<int:facture_id>/download', methods=['GET'])
@require_auth
def api_facture_download(facture_id):
    """Télécharge le fichier Excel d'une facture"""
    if request.user_role != 'admin':
        return jsonify({'status': 'error', 'message': 'Accès non autorisé'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT chemin_fichier, reference FROM factures_clients WHERE id = ?', (facture_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or not os.path.exists(row['chemin_fichier']):
        return jsonify({'status': 'error', 'message': 'Fichier non trouvé'}), 404
    
    return send_file(row['chemin_fichier'], as_attachment=True, download_name=f"facture_{row['reference']}.xlsx")
# ==================== ROUTES FACTURES RECUES ====================

@app.route('/api/factures-recues', methods=['GET'])
@require_auth
def api_factures_recues():
    """Liste toutes les factures reçues"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, nom, reference_reception, informations, statut, 
                   contenu, chemin_fichier, nom_fichier, date_ajout, ajoute_par
            FROM factures_recues 
            ORDER BY date_ajout DESC
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        factures = []
        for row in rows:
            factures.append({
                'id': row['id'],
                'nom': row['nom'],
                'reference_reception': row['reference_reception'],
                'informations': row['informations'],
                'statut': row['statut'],
                'contenu': json.loads(row['contenu']) if row['contenu'] else None,
                'chemin_fichier': row['chemin_fichier'],
                'date_ajout': row['date_ajout'],
                'ajoute_par': row['ajoute_par']
            })
        
        return jsonify({'status': 'success', 'factures': factures})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/factures-recues/<int:facture_id>', methods=['GET'])
@require_auth
def api_facture_recue_detail(facture_id):
    """Détail d'une facture"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, nom, reference_reception, informations, statut, 
                   contenu, chemin_fichier, nom_fichier, date_ajout, ajoute_par
            FROM factures_recues 
            WHERE id = ?
        ''', (facture_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return jsonify({
                'status': 'success',
                'facture': {
                    'id': row['id'],
                    'nom': row['nom'],
                    'reference_reception': row['reference_reception'],
                    'informations': row['informations'],
                    'statut': row['statut'],
                    'contenu': json.loads(row['contenu']) if row['contenu'] else None,
                    'chemin_fichier': row['chemin_fichier'],
                    'date_ajout': row['date_ajout'],
                    'ajoute_par': row['ajoute_par']
                }
            })
        return jsonify({'status': 'error', 'message': 'Facture non trouvée'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/factures-recues', methods=['POST'])
@require_auth
def api_create_facture_recue():
    """Ajoute une facture manuellement"""
    try:
        if 'fichier' not in request.files:
            return jsonify({'status': 'error', 'message': 'Aucun fichier'}), 400
        
        fichier = request.files['fichier']
        reference = request.form.get('reference', '')
        informations = request.form.get('informations', '')
        contenu_json = request.form.get('contenu', '{}')
        
        # Sauvegarder le fichier
        filepath, filename = get_upload_path('facture', reference)
        fichier.save(filepath)
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO factures_recues (user_id, nom, reference_reception, informations, statut, contenu, chemin_fichier, nom_fichier, date_ajout, ajoute_par)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.user_id,
            filename,
            reference,
            informations,
            'en-attente',
            contenu_json,
            filepath,
            filename,
            datetime.now().isoformat(),
            
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Facture ajoutée', 'id': cursor.lastrowid})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/factures-recues/<int:facture_id>', methods=['DELETE'])
@require_auth
def api_delete_facture_recue(facture_id):
    """Supprime une facture"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM factures_recues WHERE id = ?', (facture_id,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': 'Facture supprimée'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/factures-recues/<int:facture_id>/traite', methods=['POST'])
@require_auth
def api_facture_recue_traite(facture_id):
    """Marque une facture comme traitée"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE factures_recues SET statut = "traite" WHERE id = ?', (facture_id,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': 'Facture marquée comme traitée'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/factures-recues/<int:facture_id>/erreur', methods=['POST'])
@require_auth
def api_facture_recue_erreur(facture_id):
    """Marque une facture comme erreur"""
    try:
        data = request.get_json()
        commentaire = data.get('commentaire', '') if data else ''
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('UPDATE factures_recues SET statut = "erreur" WHERE id = ?', (facture_id,))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': 'Erreur signalée'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
# ==================== NOTIFICATIONS ====================

@app.route('/api/notifications', methods=['GET', 'POST'])
@require_auth
def api_notifications():
    global notifications
    
    if request.method == 'GET':
        user_notifications = [n for n in notifications if n.get('user_id') == request.user_id]
        return jsonify({'status': 'success', 'notifications': user_notifications[-50:]})
    
    else:  # POST
        data = request.get_json()
        notification = {
            'id': len(notifications) + 1,
            'user_id': request.user_id,
            'title': data.get('title', ''),
            'message': data.get('message', ''),
            'type': data.get('type', 'info'),
            'read': False,
            'created_at': datetime.now().isoformat()
        }
        notifications.append(notification)
        return jsonify({'status': 'success', 'notification': notification})

@app.route('/api/notifications/<int:notif_id>/read', methods=['POST'])
@require_auth
def api_notification_read(notif_id):
    global notifications
    for n in notifications:
        if n['id'] == notif_id and n['user_id'] == request.user_id:
            n['read'] = True
            break
    return jsonify({'status': 'success'})

# ==================== GÉNÉRATION RAPPORTS PDF ====================

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

@app.route('/api/rapport/client/<int:client_id>/pdf', methods=['GET'])
@require_auth
def generate_client_report_pdf(client_id):
    """Génère un rapport PDF pour un client"""
    if request.user_role != 'admin':
        return jsonify({'status': 'error', 'message': 'Accès non autorisé'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM clients_externes WHERE id = ?', (client_id,))
    client = cursor.fetchone()
    
    if not client:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Client non trouvé'}), 404
    
    cursor.execute('SELECT * FROM factures_clients WHERE client_id = ? ORDER BY date_reception DESC', (client_id,))
    factures = cursor.fetchall()
    
    cursor.execute('SELECT * FROM emails_clients WHERE client_id = ? ORDER BY date_envoi DESC', (client_id,))
    emails = cursor.fetchall()
    
    conn.close()
    
    import tempfile
    
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    doc = SimpleDocTemplate(temp_file.name, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, textColor=colors.HexColor('#4361ee'))
    story.append(Paragraph(f"Rapport d'activité - {client['nom']} {client['prenom'] or ''}", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph(f"<b>Email:</b> {client['email']}", styles['Normal']))
    story.append(Paragraph(f"<b>Téléphone:</b> {client['telephone'] or '-'}", styles['Normal']))
    story.append(Paragraph(f"<b>Date d'inscription:</b> {client['date_inscription']}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("<b>Statistiques</b>", styles['Heading2']))
    stats_data = [
        ['Factures reçues', str(len(factures))],
        ['Emails échangés', str(len(emails))],
    ]
    stats_table = Table(stats_data, colWidths=[4*cm, 4*cm])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4361ee')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
    ]))
    story.append(stats_table)
    story.append(Spacer(1, 0.5*cm))
    
    if factures:
        story.append(Paragraph("<b>Historique des factures</b>", styles['Heading2']))
        factures_data = [['Date', 'Référence', 'Statut']]
        for f in factures:
            factures_data.append([f['date_reception'][:10], f['reference'], f['statut']])
        
        factures_table = Table(factures_data, colWidths=[4*cm, 4*cm, 4*cm])
        factures_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4caf50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ]))
        story.append(factures_table)
    
    doc.build(story)
    temp_file.close()
    
    return send_file(temp_file.name, as_attachment=True, download_name=f"rapport_{client['email']}_{datetime.now().strftime('%Y%m%d')}.pdf")

# ==================== ROUTES COMMANDES RECUES (API PURE) ====================

# Stockage temporaire (à remplacer par base de données)
commandes_recues_db = []
receptions_non_traitees_db = []

@app.route('/api/commandes-recues', methods=['GET'])
@require_auth
def get_commandes_recues():
    """Récupère toutes les réceptions"""
    return jsonify({"status": "success", "commandes": commandes_recues_db})

@app.route('/api/commandes-recues', methods=['POST'])
@require_auth
def ajouter_commande_recue():
    """Ajoute une nouvelle réception"""
    try:
        data = request.get_json()
        nouvelle_commande = {
            "id": len(commandes_recues_db) + 1,
            "nom": data.get("nom", f"reception_{data.get('reference', 'unknown')}.xlsx"),
            "reference": data.get("reference"),
            "client": data.get("client"),
            "dateReception": data.get("dateReception"),
            "produits": data.get("produits", []),
            "statut": data.get("statut", "valide"),
            "dateAjout": datetime.now().isoformat(),
            "ajoutePar": request.user_id
        }
        commandes_recues_db.insert(0, nouvelle_commande)
        return jsonify({"status": "success", "commande": nouvelle_commande})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/commandes-recues/<int:commande_id>', methods=['DELETE'])
@require_auth
def supprimer_commande_recue(commande_id):
    """Supprime une réception"""
    global commandes_recues_db
    commandes_recues_db = [c for c in commandes_recues_db if c.get('id') != commande_id]
    return jsonify({"status": "success"})

@app.route('/api/receptions-non-traitees', methods=['GET', 'POST', 'DELETE'])
@require_auth
def gestion_receptions_non_traitees():
    """Gère les réceptions non traitées"""
    global receptions_non_traitees_db
    
    if request.method == 'GET':
        return jsonify({"status": "success", "receptions": receptions_non_traitees_db})
    
    elif request.method == 'POST':
        data = request.get_json()
        nouvelle = {
            "id": len(receptions_non_traitees_db) + 1,
            "reference": data.get("reference"),
            "client": data.get("client", "Client à définir"),
            "dateCreation": datetime.now().isoformat(),
            "statut": "en_attente",
            "produits": []
        }
        receptions_non_traitees_db.append(nouvelle)
        return jsonify({"status": "success", "reception": nouvelle})
    
    else:  # DELETE
        ref = request.args.get('reference')
        receptions_non_traitees_db = [r for r in receptions_non_traitees_db if r.get('reference') != ref]
        return jsonify({"status": "success"})

# ==================== DÉMARRAGE ====================

if __name__ == '__main__':
    try:
        from src.database.init_db import init_database, create_default_admin
        init_database()
        create_default_admin()
        
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS fichiers_upload (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL,
                reference TEXT NOT NULL,
                nom_fichier TEXT NOT NULL,
                chemin TEXT NOT NULL,
                taille INTEGER DEFAULT 0,
                client TEXT,
                date_upload TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP,
                logout_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                user_name TEXT NOT NULL,
                user_role TEXT NOT NULL,
                action TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT,
                old_data TEXT,
                new_data TEXT,
                ip_address TEXT,
                user_agent TEXT,
                details TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients_externes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                nom TEXT NOT NULL,
                prenom TEXT,
                sexe TEXT,
                nationalite TEXT,
                telephone TEXT,
                adresse TEXT,
                dossier_path TEXT,
                date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                statut TEXT DEFAULT 'actif'
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS emails_clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                direction TEXT NOT NULL,
                sujet TEXT NOT NULL,
                contenu TEXT,
                pieces_jointes TEXT,
                reference_facture TEXT,
                date_envoi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                statut TEXT DEFAULT 'recu',
                FOREIGN KEY (client_id) REFERENCES clients_externes(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS factures_clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                reference TEXT NOT NULL,
                chemin_fichier TEXT NOT NULL,
                date_reception TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                statut TEXT DEFAULT 'recue',
                contenu_extraie TEXT,
                FOREIGN KEY (client_id) REFERENCES clients_externes(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rapports_clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                type_rapport TEXT NOT NULL,
                chemin_fichier TEXT,
                date_envoi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                contenu TEXT,
                statut TEXT DEFAULT 'envoye',
                FOREIGN KEY (client_id) REFERENCES clients_externes(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historique_clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                date_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                utilisateur TEXT,
                FOREIGN KEY (client_id) REFERENCES clients_externes(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agenda_clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                date_evenement TIMESTAMP NOT NULL,
                type_evenement TEXT NOT NULL,
                reference TEXT,
                statut TEXT DEFAULT 'planifie',
                notes TEXT,
                FOREIGN KEY (client_id) REFERENCES clients_externes(id)
            )
        ''')
        
        cursor.execute("PRAGMA table_info(commandes_recues)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'chemin_fichier' not in columns:
            cursor.execute("ALTER TABLE commandes_recues ADD COLUMN chemin_fichier TEXT")
        if 'nom_fichier' not in columns:
            cursor.execute("ALTER TABLE commandes_recues ADD COLUMN nom_fichier TEXT")
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"⚠️ Erreur initialisation: {e}")
    
    print("\n" + "=" * 60)
    print("🌐 Serveur démarré sur http://localhost:5000")
    print("=" * 60)
    print("   Pages:")
    print("   - Accueil: http://localhost:5000/")
    print("   - Modèles: http://localhost:5000/models")
    print("   - Contact: http://localhost:5000/contact")
    print("   - Inscription: http://localhost:5000/register")
    print("   - Connexion: http://localhost:5000/login")
    print("   - Dashboard: http://localhost:5000/dashboard")
    print("\n   📁 Dossiers de stockage:")
    print(f"   - Factures: {FACTURES_FOLDER}")
    print(f"   - Réceptions: {RECEPTIONS_FOLDER}")
    print(f"   - Clients: {CLIENTS_ROOT}")
    print("=" * 60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)