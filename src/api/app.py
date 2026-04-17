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
from datetime import datetime, timedelta
from functools import wraps
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

# Créer les dossiers s'ils n'existent pas
os.makedirs(FACTURES_FOLDER, exist_ok=True)
os.makedirs(RECEPTIONS_FOLDER, exist_ok=True)

print(f"📁 Dossier uploads: {UPLOAD_FOLDER}")
print(f"📁 Dossier factures: {FACTURES_FOLDER}")
print(f"📁 Dossier réceptions: {RECEPTIONS_FOLDER}")

# Stockage des tokens (à remplacer par Redis en production)
tokens = {}

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
        
        # Récupérer le rôle de l'utilisateur
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
        
        # Générer le chemin de sauvegarde
        filepath, filename = get_upload_path('facture', reference)
        
        # Sauvegarder le fichier
        fichier.save(filepath)
        
        # Enregistrer dans la base de données
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
        
        # Générer le chemin de sauvegarde
        filepath, filename = get_upload_path('reception', reference)
        
        # Sauvegarder le fichier
        fichier.save(filepath)
        
        # Enregistrer dans la base de données
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
        
        # Mettre à jour la commande reçue avec le chemin du fichier
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

@app.route('/api/list/factures', methods=['GET'])
@require_auth
def list_factures_upload():
    """Liste toutes les factures sauvegardées"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM fichiers_upload 
            WHERE user_id = ? AND type = 'facture'
            ORDER BY date_upload DESC
        ''', (request.user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        fichiers = []
        for row in rows:
            fichiers.append({
                'id': row['id'],
                'nom': row['nom_fichier'],
                'reference': row['reference'],
                'chemin': row['chemin'],
                'taille': row['taille'],
                'date': row['date_upload']
            })
        
        return jsonify({'status': 'success', 'fichiers': fichiers})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/list/receptions', methods=['GET'])
@require_auth
def list_receptions_upload():
    """Liste toutes les réceptions sauvegardées"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM fichiers_upload 
            WHERE user_id = ? AND type = 'reception'
            ORDER BY date_upload DESC
        ''', (request.user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        fichiers = []
        for row in rows:
            fichiers.append({
                'id': row['id'],
                'nom': row['nom_fichier'],
                'reference': row['reference'],
                'client': row['client'],
                'chemin': row['chemin'],
                'taille': row['taille'],
                'date': row['date_upload']
            })
        
        return jsonify({'status': 'success', 'fichiers': fichiers})
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/download/<int:fichier_id>', methods=['GET'])
@require_auth
def download_fichier(fichier_id):
    """Télécharge un fichier sauvegardé"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT chemin, nom_fichier FROM fichiers_upload 
            WHERE id = ? AND user_id = ?
        ''', (fichier_id, request.user_id))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'status': 'error', 'message': 'Fichier non trouvé'}), 404
        
        if not os.path.exists(row['chemin']):
            return jsonify({'status': 'error', 'message': 'Fichier introuvable sur le serveur'}), 404
        
        return send_file(row['chemin'], as_attachment=True, download_name=row['nom_fichier'])
        
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
        'admin': ['dashboard', 'reception', 'reception_reelle', 'matching', 'historique', 'guide', 'stock', 'livraison', 'date-livraison', 'gestion-utilisateurs', 'stats'],
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
        'gestion-utilisateurs': 'dashboard/sections/gestion-utilisateurs.html',
        'stats': 'dashboard/sections/stats.html'
    }
    
    template = templates.get(section, 'dashboard/sections/dashboard.html')
    return render_template(template, role=request.user_role)

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

# ==================== ROUTES GESTION UTILISATEURS ====================

@app.route('/api/users', methods=['GET', 'POST', 'DELETE'])
@require_auth
def api_users():
    if request.user_role != 'admin':
        return jsonify({'status': 'error', 'message': 'Accès non autorisé'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('SELECT id, username, email, company, storage_type, role FROM users')
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
                'role': row['role']
            })
        
        return jsonify({'status': 'success', 'users': users})
    
    elif request.method == 'POST':
        data = request.get_json()
        
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
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Utilisateur ajouté'})
    
    else:
        user_id = request.args.get('id')
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success', 'message': 'Utilisateur supprimé'})

# ==================== DÉMARRAGE ====================

if __name__ == '__main__':
    # Initialiser la base de données
    try:
        from src.database.init_db import init_database, create_default_admin
        init_database()
        create_default_admin()
        
        # Ajouter la table fichiers_upload si elle n'existe pas
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
        
        # Ajouter les colonnes chemin_fichier et nom_fichier à commandes_recues si elles n'existent pas
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
    print("   - Dashboard: http://localhost:5000/dashboard (après connexion)")
    print("\n   📁 Dossiers de stockage:")
    print(f"   - Factures: {FACTURES_FOLDER}")
    print(f"   - Réceptions: {RECEPTIONS_FOLDER}")
    print("=" * 60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)