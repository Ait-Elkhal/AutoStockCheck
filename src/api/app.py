from flask import Flask, render_template, jsonify, request, make_response, redirect, send_from_directory
from flask_cors import CORS
import secrets
import os
import json
import re
import uuid
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import pandas as pd
from logger import log_action, get_logs, export_logs_to_csv, log_error

from config import BASE_DIR, FACTURES_FOLDER, RECEPTIONS_FOLDER, CLIENTS_ROOT, ANOMALIES_FOLDER, COMPARAISONS_FOLDER, USERS_FOLDER
from database import init_db, get_db, hash_password
from auth import generate_token, tokens, require_auth

app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'src/web/templates'),
            static_folder=os.path.join(BASE_DIR, 'src/web/static'))
app.secret_key = secrets.token_hex(32)
CORS(app)

# Configuration upload
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv', 'pdf', 'png', 'jpg', 'jpeg'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

init_db()

# ==================== PAGES ====================

@app.route('/')
def accueil():
    return render_template('public/accueil.html')

@app.route('/models')
def models():
    return render_template('public/models.html')

@app.route('/contact')
def contact():
    return render_template('public/contact.html')

@app.route('/login')
def login_page():
    return render_template('public/login.html')

@app.route('/dashboard')
@require_auth
def dashboard():
    if request.user_role == 'admin':
        return redirect('/admin')
    elif request.user_role == 'stock':
        return redirect('/stock/dashboard')
    elif request.user_role == 'qualite':
        return redirect('/qualite')
    elif request.user_role == 'reception':
        return redirect('/reception')
    return render_template('app/dashboard.html')

# ==================== PAGES RESPONSABLE STOCK ====================

@app.route('/stock/dashboard')
@require_auth
def stock_dashboard():
    if request.user_role not in ['stock', 'admin']:
        return redirect('/dashboard')
    return render_template('modules/stock/dashboard.html', now=datetime.now())

@app.route('/stock/gestion')
@require_auth
def stock_gestion():
    if request.user_role not in ['stock', 'admin']:
        return redirect('/dashboard')
    return render_template('modules/stock/index.html')

@app.route('/stock/mouvements')
@require_auth
def stock_mouvements():
    if request.user_role not in ['stock', 'admin']:
        return redirect('/dashboard')
    return render_template('modules/stock/mouvements.html')

@app.route('/stock/receptions')
@require_auth
def stock_receptions():
    if request.user_role not in ['stock', 'admin']:
        return redirect('/dashboard')
    return render_template('modules/stock/receptions.html')

@app.route('/stock/comparaisons')
@require_auth
def stock_comparaisons():
    if request.user_role not in ['stock', 'admin']:
        return redirect('/dashboard')
    return render_template('modules/stock/comparaisons.html')

@app.route('/stock/historique')
@require_auth
def stock_historique():
    if request.user_role not in ['stock', 'admin']:
        return redirect('/dashboard')
    return render_template('modules/stock/historique.html')

@app.route('/stock/alertes')
@require_auth
def stock_alertes():
    if request.user_role not in ['stock', 'admin']:
        return redirect('/dashboard')
    return render_template('modules/stock/alertes.html')

# ==================== AUTRES PAGES ====================

@app.route('/stock')
@require_auth
def stock_page():
    return redirect('/stock/gestion')

@app.route('/reception')
@require_auth
def reception_page():
    return render_template('modules/reception/index.html')

@app.route('/reception/reelle')
@require_auth
def reception_reelle_page():
    if request.user_role not in ['reception', 'admin', 'stock']:
        return redirect('/dashboard')
    return render_template('modules/reception/reception_reelle.html')

@app.route('/reception/matching')
@require_auth
def reception_matching_page():
    if request.user_role not in ['reception', 'admin', 'stock', 'qualite']:
        return redirect('/dashboard')
    return render_template('modules/reception/matching.html')

# ==================== ROUTES STOCK AVEC RÉCEPTION ====================

@app.route('/stock/factures')
@require_auth
def stock_factures():
    if request.user_role not in ['stock', 'admin']:
        return redirect('/dashboard')
    return render_template('modules/reception/factures.html')

@app.route('/stock/reception-reelle')
@require_auth
def stock_reception_reelle():
    if request.user_role not in ['stock', 'admin']:
        return redirect('/dashboard')
    return render_template('modules/reception/reception_reelle.html')

@app.route('/stock/matching')
@require_auth
def stock_matching():
    if request.user_role not in ['stock', 'admin']:
        return redirect('/dashboard')
    return render_template('modules/reception/matching.html')

@app.route('/qualite')
@require_auth
def qualite_page():
    return render_template('modules/qualite/index.html')

# ==================== API AUTH ====================

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
            
            # Mettre à jour last_login
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET last_login = ? WHERE id = ?', 
                          (datetime.now().isoformat(), user['id']))
            conn.commit()
            conn.close()
            
            log_action(
                user_id=user['id'],
                user_name=user['username'],
                user_role=user['role'],
                action='login',
                details=f"Connexion réussie de {user['username']}",
                ip_address=request.remote_addr,
                entity_type='user',
                entity_id=str(user['id'])
            )
            
            # Redirection selon le rôle
            redirect_url = {
                'admin': '/admin',
                'stock': '/stock/dashboard',
                'qualite': '/qualite',
                'reception': '/reception',
                'user': '/dashboard'
            }.get(user['role'], '/dashboard')
            
            response = make_response(jsonify({
                'status': 'success',
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'role': user['role']
                },
                'redirect_url': redirect_url
            }))
            response.set_cookie('token', token, httponly=True, max_age=timedelta(days=7))
            return response
        
        return jsonify({'status': 'error', 'message': 'Identifiants invalides'}), 401
    except Exception as e:
        log_error(str(e), {'route': 'login'})
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/admin')
@require_auth
def admin_page():
    if request.user_role != 'admin':
        return redirect('/dashboard')
    return render_template('admin/index.html')

@app.route('/api/logout', methods=['POST'])
def api_logout():
    token = request.cookies.get('token')
    
    user_id = tokens.get(token)
    if user_id:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT username, role FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            log_action(
                user_id=user_id,
                user_name=user['username'],
                user_role=user['role'],
                action='logout',
                details=f"Déconnexion de {user['username']}",
                ip_address=request.remote_addr
            )
    
    if token in tokens:
        del tokens[token]
    
    response = make_response(jsonify({'status': 'success'}))
    response.set_cookie('token', '', expires=0)
    return response

@app.route('/api/me', methods=['GET'])
@require_auth
def api_me():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, role FROM users WHERE id = ?', (request.user_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return jsonify({
            'status': 'success',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role']
            }
        })
    return jsonify({'status': 'error', 'message': 'Utilisateur non trouvé'}), 404

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    token = request.cookies.get('token')
    if token and token in tokens:
        return jsonify({'status': 'success', 'authenticated': True})
    return jsonify({'status': 'success', 'authenticated': False})

# ==================== ADMIN ROUTES ====================

@app.route('/admin/user/add')
@require_auth
def admin_user_add():
    if request.user_role != 'admin':
        return redirect('/dashboard')
    return render_template('admin/user_form.html', title='➕ Ajouter un utilisateur', user=None)

@app.route('/admin/user/edit/<int:user_id>')
@require_auth
def admin_user_edit(user_id):
    if request.user_role != 'admin':
        return redirect('/dashboard')
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, role, statut, fullname, sexe, nationalite, birthdate, telephone, adresse, hire_date, departement FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return redirect('/admin?section=users')
    
    return render_template('admin/user_form.html', title='✏️ Modifier un utilisateur', user=dict(user))

@app.route('/api/admin/users', methods=['GET'])
@require_auth
def api_admin_users_list():
    if request.user_role != 'admin':
        return jsonify({'error': 'Non autorisé'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, email, role, statut, last_login, created_at FROM users ORDER BY created_at DESC')
    users = []
    for row in cursor.fetchall():
        users.append({
            'id': row['id'],
            'username': row['username'],
            'email': row['email'],
            'role': row['role'],
            'statut': row['statut'],
            'last_login': row['last_login'],
            'created_at': row['created_at']
        })
    conn.close()
    return jsonify({'status': 'success', 'users': users})

@app.route('/api/admin/users', methods=['POST'])
@require_auth
def api_admin_users_create():
    if request.user_role != 'admin':
        return jsonify({'error': 'Non autorisé'}), 403
    
    data = request.get_json()
    
    email = data.get('email')
    password = data.get('password')
    username = data.get('username')
    role = data.get('role', 'user')
    statut = data.get('statut', 'pending')
    
    if not email:
        return jsonify({'error': 'Email requis'}), 400
    
    from database import validate_email, generate_random_password, hash_password
    
    valid, msg = validate_email(email)
    if not valid:
        return jsonify({'error': msg}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({'error': 'Email déjà utilisé'}), 400
    
    if not username:
        username = email.split('@')[0]
    
    if not password:
        password = generate_random_password()
    
    hashed = hash_password(password)
    
    cursor.execute('''
        INSERT INTO users (username, password, email, role, statut, created_at, fullname, telephone)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (username, hashed, email, role, statut, datetime.now().isoformat(), 
          data.get('fullname', ''), data.get('telephone', '')))
    
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    log_action(
        user_id=request.user_id,
        user_name=get_user_name(request.user_id),
        user_role='admin',
        action='create',
        details=f"Création de l'utilisateur {username} (rôle: {role})",
        ip_address=request.remote_addr,
        entity_type='user',
        entity_id=str(user_id)
    )
    
    return jsonify({
        'status': 'success',
        'id': user_id,
        'password': password
    })

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
@require_auth
def api_admin_users_update(user_id):
    if request.user_role != 'admin':
        return jsonify({'error': 'Non autorisé'}), 403
    
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    old_user = cursor.fetchone()
    
    updates = []
    params = []
    
    if data.get('username'):
        updates.append('username = ?')
        params.append(data['username'])
    if data.get('email'):
        updates.append('email = ?')
        params.append(data['email'])
    if data.get('role'):
        updates.append('role = ?')
        params.append(data['role'])
    if data.get('statut'):
        updates.append('statut = ?')
        params.append(data['statut'])
    if data.get('fullname'):
        updates.append('fullname = ?')
        params.append(data['fullname'])
    if data.get('telephone'):
        updates.append('telephone = ?')
        params.append(data['telephone'])
    
    if updates:
        params.append(user_id)
        cursor.execute(f'UPDATE users SET {", ".join(updates)} WHERE id = ?', params)
        
        log_action(
            user_id=request.user_id,
            user_name=get_user_name(request.user_id),
            user_role='admin',
            action='update',
            details=f"Modification de l'utilisateur {old_user['username']}",
            ip_address=request.remote_addr,
            entity_type='user',
            entity_id=str(user_id)
        )
    
    if data.get('password'):
        from database import validate_password, hash_password
        valid, msg = validate_password(data['password'], is_new_user=True)
        if not valid:
            conn.close()
            return jsonify({'error': msg}), 400
        hashed = hash_password(data['password'])
        cursor.execute('UPDATE users SET password = ? WHERE id = ?', (hashed, user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success'})

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@require_auth
def api_admin_users_delete(user_id):
    if request.user_role != 'admin':
        return jsonify({'error': 'Non autorisé'}), 403
    
    if user_id == request.user_id:
        return jsonify({'error': 'Vous ne pouvez pas supprimer votre propre compte'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    
    log_action(
        user_id=request.user_id,
        user_name=get_user_name(request.user_id),
        user_role='admin',
        action='delete',
        details=f"Suppression de l'utilisateur {user['username']}",
        ip_address=request.remote_addr,
        entity_type='user',
        entity_id=str(user_id)
    )
    
    conn.commit()
    conn.close()
    
    return jsonify({'status': 'success'})

@app.route('/api/admin/users/<int:user_id>/status', methods=['PUT'])
@require_auth
def admin_user_status(user_id):
    if request.user_role != 'admin':
        return jsonify({'error': 'Non autorisé'}), 403
    
    data = request.get_json()
    new_status = data.get('statut')
    
    if new_status not in ['actif', 'inactif', 'pending']:
        return jsonify({'error': 'Statut invalide'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    cursor.execute('UPDATE users SET statut = ? WHERE id = ?', (new_status, user_id))
    conn.commit()
    conn.close()
    
    log_action(
        user_id=request.user_id,
        user_name=get_user_name(request.user_id),
        user_role='admin',
        action='update',
        details=f"Changement de statut de l'utilisateur {user['username']} vers {new_status}",
        ip_address=request.remote_addr,
        entity_type='user',
        entity_id=str(user_id)
    )
    
    return jsonify({'status': 'success'})

@app.route('/api/admin/users/<int:user_id>/reset-password', methods=['POST'])
@require_auth
def admin_reset_password(user_id):
    if request.user_role != 'admin':
        return jsonify({'error': 'Non autorisé'}), 403
    
    from database import generate_random_password, hash_password
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    
    new_password = generate_random_password()
    hashed = hash_password(new_password)
    
    cursor.execute('UPDATE users SET password = ? WHERE id = ?', (hashed, user_id))
    conn.commit()
    conn.close()
    
    log_action(
        user_id=request.user_id,
        user_name=get_user_name(request.user_id),
        user_role='admin',
        action='reset_password',
        details=f"Réinitialisation du mot de passe de l'utilisateur {user['username']}",
        ip_address=request.remote_addr,
        entity_type='user',
        entity_id=str(user_id)
    )
    
    return jsonify({'status': 'success', 'new_password': new_password})

@app.route('/api/admin/stats', methods=['GET'])
@require_auth
def api_admin_stats():
    if request.user_role != 'admin':
        return jsonify({'error': 'Non autorisé'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as total FROM users')
    total_users = cursor.fetchone()['total']
    
    cursor.execute('SELECT COUNT(*) as total FROM users WHERE statut = "actif"')
    active_users = cursor.fetchone()['total']
    
    cursor.execute('SELECT COUNT(*) as total FROM users WHERE statut = "inactif"')
    inactive_users = cursor.fetchone()['total']
    
    cursor.execute('SELECT COUNT(*) as total FROM users WHERE statut = "pending"')
    pending_activation = cursor.fetchone()['total']
    
    # Sessions actives (basées sur les tokens)
    active_sessions = len(tokens)
    
    # Actions 24h depuis les logs
    actions_24h = 0
    log_path = os.path.join(BASE_DIR, 'data', 'logs', f'audit_{datetime.now().strftime("%Y-%m-%d")}.log')
    if os.path.exists(log_path):
        with open(log_path, 'r', encoding='utf-8') as f:
            actions_24h = sum(1 for _ in f)
    
    conn.close()
    
    return jsonify({
        'status': 'success',
        'stats': {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'pending_activation': pending_activation,
            'active_sessions': active_sessions,
            'actions_last_24h': actions_24h
        }
    })

@app.route('/api/admin/section/<section>', methods=['GET'])
@require_auth
def admin_section(section):
    if request.user_role != 'admin':
        return "Accès non autorisé", 403
    
    templates = {
        'dashboard': 'admin/sections/dashboard.html',
        'users': 'admin/sections/users.html',
        'logs': 'admin/sections/logs.html',
        'sessions': 'admin/sections/sessions.html',
        'config': 'admin/sections/config.html',
        'stats': 'admin/sections/stats.html'
    }
    
    template = templates.get(section)
    if not template:
        return "Section non trouvée", 404
    
    try:
        return render_template(template, role=request.user_role)
    except Exception as e:
        return f"<div class='alert alert-danger'>Erreur: {str(e)}</div>", 500

@app.route('/api/admin/logs', methods=['GET'])
@require_auth
def api_admin_logs():
    if request.user_role != 'admin':
        return jsonify({'error': 'Non autorisé'}), 403
    
    days = request.args.get('days', 7, type=int)
    limit = request.args.get('limit', 500, type=int)
    
    logs = []
    logs_folder = os.path.join(BASE_DIR, 'data', 'logs')
    
    if not os.path.exists(logs_folder):
        return jsonify({'status': 'success', 'logs': [], 'message': 'Aucun log trouvé'})
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        log_path = os.path.join(logs_folder, f'audit_{date}.log')
        
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    logs.append(line.strip())
                    if len(logs) >= limit:
                        break
            if len(logs) >= limit:
                break
    
    parsed_logs = []
    pattern = r'\[(.*?)\]\s+\[(.*?)\]\s+\[(.*?)\]\s+\[(.*?)\]\s+(.*?)\s+\(IP:\s*(.*?)\)'
    
    for line in logs:
        try:
            match = re.search(pattern, line)
            if match:
                parsed_logs.append({
                    'created_at': match.group(1),
                    'user_name': match.group(2),
                    'user_role': match.group(3),
                    'action': match.group(4),
                    'details': match.group(5).strip(),
                    'ip_address': match.group(6)
                })
        except Exception as e:
            continue
    
    return jsonify({'status': 'success', 'logs': parsed_logs})

@app.route('/api/admin/logs/export', methods=['GET'])
@require_auth
def api_admin_logs_export():
    if request.user_role != 'admin':
        return jsonify({'error': 'Non autorisé'}), 403
    
    days = request.args.get('days', 30, type=int)
    csv_data = export_logs_to_csv('audit', days)
    
    return jsonify({
        'status': 'success',
        'csv': csv_data,
        'filename': f'audit_logs_{datetime.now().strftime("%Y%m%d")}.csv'
    })

# ==================== API RESPONSABLE STOCK ====================

@app.route('/api/stock/dashboard-stats', methods=['GET'])
@require_auth
def api_stock_dashboard_stats():
    if request.user_role not in ['stock', 'admin']:
        return jsonify({'error': 'Non autorisé'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as total FROM stock_items')
    totalProduits = cursor.fetchone()['total'] or 0
    
    cursor.execute('SELECT COUNT(*) as total FROM stock_items WHERE quantite > 0 AND quantite <= stock_min')
    stockBas = cursor.fetchone()['total'] or 0
    
    cursor.execute('SELECT COUNT(*) as total FROM stock_items WHERE quantite = 0')
    rupture = cursor.fetchone()['total'] or 0
    
    cursor.execute('SELECT SUM(quantite * prix) as valeur FROM stock_items')
    valeurStock = cursor.fetchone()['valeur'] or 0
    
    conn.close()
    
    return jsonify({
        'status': 'success',
        'totalProduits': totalProduits,
        'stockBas': stockBas,
        'rupture': rupture,
        'valeurStock': round(valeurStock, 2)
    })

@app.route('/api/stock/alertes', methods=['GET'])
@require_auth
def api_stock_alertes():
    if request.user_role not in ['stock', 'admin']:
        return jsonify({'error': 'Non autorisé'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM stock_items 
        WHERE quantite <= stock_min 
        ORDER BY quantite ASC
    ''')
    
    alertes = []
    for row in cursor.fetchall():
        alertes.append({
            'reference': row['reference'],
            'nom': row['nom'],
            'quantite': row['quantite'],
            'stockMin': row['stock_min'],
            'type': 'rupture' if row['quantite'] == 0 else 'alerte'
        })
    
    conn.close()
    return jsonify({'status': 'success', 'alertes': alertes})

@app.route('/api/stock/mouvements/recent', methods=['GET'])
@require_auth
def api_stock_mouvements_recent():
    if request.user_role not in ['stock', 'admin']:
        return jsonify({'error': 'Non autorisé'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Correction: utiliser les bons noms de colonnes
    try:
        cursor.execute('''
            SELECT sm.*, si.reference, si.nom as produit_nom
            FROM stock_mouvements sm
            JOIN stock_items si ON sm.produit_id = si.id
            ORDER BY sm.date DESC LIMIT 20
        ''')
        
        mouvements = []
        for row in cursor.fetchall():
            mouvements.append({
                'reference': row['reference'],
                'nom': row['produit_nom'] if 'produit_nom' in row.keys() else row['nom'] if 'nom' in row.keys() else 'Produit',
                'type': row['type'],
                'quantite': abs(row['quantite']),
                'date': row['date']
            })
    except Exception as e:
        print(f"Erreur requête mouvements: {e}")
        mouvements = []
    
    conn.close()
    return jsonify({'status': 'success', 'mouvements': mouvements})

# ==================== API STOCK ====================

@app.route('/api/stock', methods=['GET', 'POST'])
@require_auth
def api_stock():
    if request.user_role not in ['stock', 'admin']:
        return jsonify({'error': 'Non autorisé'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        cursor.execute('SELECT * FROM stock_items ORDER BY emplacement')
        items = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({'status': 'success', 'items': items})
    
    elif request.method == 'POST':
        data = request.get_json()
        
        # Vérifier si l'emplacement existe déjà
        cursor.execute('SELECT id FROM stock_items WHERE emplacement = ?', (data.get('emplacement'),))
        if cursor.fetchone():
            conn.close()
            return jsonify({'error': 'Cet emplacement est déjà utilisé'}), 400
        
        cursor.execute('''
            INSERT INTO stock_items (emplacement, reference, nom, categorie, quantite, stock_min, prix, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (data.get('emplacement'), data.get('reference'), data.get('nom'), 
              data.get('categorie'), data.get('quantite', 0), data.get('stock_min', 5), 
              data.get('prix', 0), request.user_id))
        
        conn.commit()
        item_id = cursor.lastrowid
        conn.close()
        
        log_action(
            user_id=request.user_id,
            user_name=get_user_name(request.user_id),
            user_role=request.user_role,
            action='create',
            details=f"Ajout d'un produit: {data.get('reference')} - {data.get('nom')}",
            ip_address=request.remote_addr,
            entity_type='stock',
            entity_id=str(item_id)
        )
        
        return jsonify({'status': 'success', 'id': item_id})

@app.route('/api/stock/<int:id>', methods=['PUT', 'DELETE'])
@require_auth
def api_stock_item(id):
    if request.user_role not in ['stock', 'admin']:
        return jsonify({'error': 'Non autorisé'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    
    if request.method == 'PUT':
        data = request.get_json()
        
        updates = []
        params = []
        
        for key in ['emplacement', 'reference', 'nom', 'categorie', 'quantite', 'stock_min', 'prix']:
            if key in data:
                updates.append(f'{key} = ?')
                params.append(data[key])
        
        if updates:
            params.append(id)
            cursor.execute(f'UPDATE stock_items SET {", ".join(updates)} WHERE id = ?', params)
            
            # Enregistrer le mouvement si quantité modifiée
            if 'quantite' in data:
                cursor.execute('SELECT reference, nom FROM stock_items WHERE id = ?', (id,))
                item = cursor.fetchone()
                if item:
                    log_action(
                        user_id=request.user_id,
                        user_name=get_user_name(request.user_id),
                        user_role=request.user_role,
                        action='update',
                        details=f"Modification quantité du produit {item['reference']}: {data['quantite']}",
                        ip_address=request.remote_addr,
                        entity_type='stock',
                        entity_id=str(id)
                    )
            
            conn.commit()
    
    elif request.method == 'DELETE':
        cursor.execute('SELECT reference, nom FROM stock_items WHERE id = ?', (id,))
        item = cursor.fetchone()
        
        cursor.execute('DELETE FROM stock_items WHERE id = ?', (id,))
        conn.commit()
        
        if item:
            log_action(
                user_id=request.user_id,
                user_name=get_user_name(request.user_id),
                user_role=request.user_role,
                action='delete',
                details=f"Suppression du produit {item['reference']} - {item['nom']}",
                ip_address=request.remote_addr,
                entity_type='stock',
                entity_id=str(id)
            )
    
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/stock/mouvement', methods=['POST'])
@require_auth
def api_stock_mouvement():
    if request.user_role not in ['stock', 'admin']:
        return jsonify({'error': 'Non autorisé'}), 403
    
    data = request.get_json()
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT quantite, reference, nom FROM stock_items WHERE id = ?', (data['produit_id'],))
    item = cursor.fetchone()
    
    if not item:
        conn.close()
        return jsonify({'error': 'Produit non trouvé'}), 404
    
    nouvelle_quantite = item['quantite'] + data['quantite']
    if nouvelle_quantite < 0:
        conn.close()
        return jsonify({'error': 'Stock insuffisant'}), 400
    
    cursor.execute('UPDATE stock_items SET quantite = ? WHERE id = ?', (nouvelle_quantite, data['produit_id']))
    cursor.execute('''
        INSERT INTO stock_mouvements (produit_id, type, quantite, commentaire, user_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (data['produit_id'], 'entree' if data['quantite'] > 0 else 'sortie', 
          data['quantite'], data.get('commentaire'), request.user_id))
    
    conn.commit()
    conn.close()
    
    log_action(
        user_id=request.user_id,
        user_name=get_user_name(request.user_id),
        user_role=request.user_role,
        action='mouvement',
        details=f"Mouvement stock {item['reference']}: {data['quantite']} unités",
        ip_address=request.remote_addr,
        entity_type='stock',
        entity_id=str(data['produit_id'])
    )
    
    return jsonify({'status': 'success'})

# ==================== API FACTURES & RECEPTIONS ====================

@app.route('/api/factures-recues', methods=['GET'])
@require_auth
def api_factures_get():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT f.*, u.username as ajoute_par 
        FROM factures_recues f
        LEFT JOIN users u ON f.user_id = u.id
        ORDER BY f.id DESC
    ''')
    factures = []
    for row in cursor.fetchall():
        facture = dict(row)
        if facture.get('contenu'):
            try:
                facture['contenu'] = json.loads(facture['contenu'])
            except:
                facture['contenu'] = None
        factures.append(facture)
    conn.close()
    return jsonify({'status': 'success', 'factures': factures})

@app.route('/api/factures-recues', methods=['POST'])
@require_auth
def api_factures_post():
    if 'fichier' not in request.files:
        return jsonify({'error': 'Aucun fichier'}), 400
    
    file = request.files['fichier']
    if file.filename == '':
        return jsonify({'error': 'Nom de fichier vide'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Format non supporté'}), 400
    
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    saved_filename = f"{timestamp}_{filename}"
    filepath = os.path.join(FACTURES_FOLDER, saved_filename)
    file.save(filepath)
    
    # Lire le fichier Excel
    try:
        df = pd.read_excel(filepath)
        headers = df.columns.tolist()
        lignes = df.values.tolist()
        contenu = {
            'en_tete': headers,
            'lignes': [[str(cell) if pd.notna(cell) else '' for cell in row] for row in lignes]
        }
    except Exception as e:
        return jsonify({'error': f'Erreur lecture Excel: {str(e)}'}), 400
    
    reference = request.form.get('reference', '')
    informations = request.form.get('informations', '')
    
    conn = get_db()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    # Important: Enregistrer request.user_name dans la colonne ajoute_par
    cursor.execute('''
        INSERT INTO factures_recues (nom, chemin_fichier, reference_reception, informations, contenu, statut, user_id, ajoute_par, created_at, date_ajout)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (saved_filename, filepath, reference, informations, json.dumps(contenu), 'en-attente', 
          request.user_id, request.user_name, now, now))
    
    conn.commit()
    facture_id = cursor.lastrowid
    conn.close()
    
    log_action(
        user_id=request.user_id,
        user_name=request.user_name,
        user_role=request.user_role,
        action='create',
        details=f"Ajout d'une facture: {saved_filename} (réf: {reference})",
        ip_address=request.remote_addr,
        entity_type='facture',
        entity_id=str(facture_id)
    )
    
    return jsonify({'status': 'success', 'id': facture_id})

@app.route('/api/factures-recues/<int:facture_id>', methods=['DELETE'])
@require_auth
def api_factures_delete(facture_id):
    if request.user_role not in ['stock', 'admin']:
        return jsonify({'error': 'Non autorisé'}), 403
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT nom, chemin_fichier FROM factures_recues WHERE id = ?', (facture_id,))
    facture = cursor.fetchone()
    
    if not facture:
        conn.close()
        return jsonify({'error': 'Facture non trouvée'}), 404
    
    # Supprimer le fichier
    if os.path.exists(facture['chemin_fichier']):
        os.remove(facture['chemin_fichier'])
    
    cursor.execute('DELETE FROM factures_recues WHERE id = ?', (facture_id,))
    conn.commit()
    
    log_action(
        user_id=request.user_id,
        user_name=get_user_name(request.user_id),
        user_role=request.user_role,
        action='delete',
        details=f"Suppression de la facture {facture['nom']}",
        ip_address=request.remote_addr,
        entity_type='facture',
        entity_id=str(facture_id)
    )
    
    conn.close()
    return jsonify({'status': 'success'})

@app.route('/api/commandes-recues', methods=['GET', 'POST', 'PUT', 'DELETE'])
@require_auth
def api_commandes():
    if request.method == 'GET':
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.*, u.username as ajoute_par 
            FROM commandes_recues c
            LEFT JOIN users u ON c.user_id = u.id
            ORDER BY c.id DESC
        ''')
        commandes = []
        for row in cursor.fetchall():
            commande = dict(row)
            if commande.get('produits'):
                try:
                    commande['produits'] = json.loads(commande['produits'])
                except:
                    commande['produits'] = []
            commandes.append(commande)
        conn.close()
        return jsonify({'status': 'success', 'commandes': commandes})
    
    elif request.method == 'POST':
        data = request.get_json()
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO commandes_recues (nom, reference, client, date_reception, produits, statut, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (data.get('nom'), data.get('reference'), data.get('client'), 
              data.get('date_reception'), json.dumps(data.get('produits', [])), 
              data.get('statut', 'valide'), request.user_id))
        
        conn.commit()
        commande_id = cursor.lastrowid
        conn.close()
        
        log_action(
            user_id=request.user_id,
            user_name=get_user_name(request.user_id),
            user_role=request.user_role,
            action='create',
            details=f"Ajout d'une réception: {data.get('reference')}",
            ip_address=request.remote_addr,
            entity_type='reception',
            entity_id=str(commande_id)
        )
        
        return jsonify({'status': 'success', 'id': commande_id})
    
    elif request.method == 'PUT':
        data = request.get_json()
        commande_id = data.get('id')
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE commandes_recues 
            SET reference = ?, client = ?, date_reception = ?, produits = ?, statut = ?
            WHERE id = ?
        ''', (data.get('reference'), data.get('client'), data.get('date_reception'),
              json.dumps(data.get('produits', [])), data.get('statut'), commande_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success'})
    
    elif request.method == 'DELETE':
        commande_id = request.args.get('id') or request.json.get('id') if request.json else None
        
        if not commande_id:
            return jsonify({'error': 'ID requis'}), 400
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM commandes_recues WHERE id = ?', (commande_id,))
        conn.commit()
        conn.close()
        
        return jsonify({'status': 'success'})

# ==================== API DASHBOARD ====================

@app.route('/api/dashboard/stats', methods=['GET'])
@require_auth
def api_dashboard_stats():
    conn = get_db()
    cursor = conn.cursor()
    
    # Stock total
    cursor.execute('SELECT SUM(quantite) as total FROM stock_items')
    total_stock = cursor.fetchone()['total'] or 0
    
    # Alertes stock bas
    cursor.execute('SELECT COUNT(*) as count FROM stock_items WHERE quantite <= stock_min')
    alertes = cursor.fetchone()['count'] or 0
    
    # Entrées du mois
    debut_mois = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT SUM(quantite) as total FROM stock_mouvements 
        WHERE type = 'entree' AND date >= ?
    ''', (debut_mois,))
    entries = cursor.fetchone()['total'] or 0
    
    # Sorties du mois
    cursor.execute('''
        SELECT SUM(quantite) as total FROM stock_mouvements 
        WHERE type = 'sortie' AND date >= ?
    ''', (debut_mois,))
    exits = abs(cursor.fetchone()['total'] or 0)
    
    conn.close()
    
    return jsonify({
        'status': 'success',
        'stockTotal': total_stock,
        'alerts': alertes,
        'entries': entries,
        'exits': exits,
        'chartLabels': ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin'],
        'chartData': [120, 135, 142, 138, 145, 150]
    })

@app.route('/api/activities', methods=['GET'])
@require_auth
def api_activities():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT sm.*, si.nom as product_name, si.reference
        FROM stock_mouvements sm
        JOIN stock_items si ON sm.produit_id = si.id
        ORDER BY sm.date DESC LIMIT 10
    ''')
    
    activities = []
    for row in cursor.fetchall():
        activities.append({
            'product': row['product_name'],
            'reference': row['reference'],
            'action': 'Entrée' if row['quantite'] > 0 else 'Sortie',
            'quantity': abs(row['quantite']),
            'date': row['date'][:16] if row['date'] else '-'
        })
    
    conn.close()
    return jsonify({'status': 'success', 'activities': activities})

# ==================== STATIC FILES & ERROR HANDLERS ====================

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': 'Route non trouvée'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'status': 'error', 'message': 'Erreur interne du serveur'}), 500

# ==================== FONCTION UTILITAIRE ====================

def get_user_name(user_id):
    """Récupère le nom d'utilisateur par ID"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user['username'] if user else 'unknown'

@app.route('/api/upload-reception', methods=['POST'])
@require_auth
def api_upload_reception():
    if 'fichier' not in request.files:
        return jsonify({'error': 'Aucun fichier'}), 400
    
    file = request.files['fichier']
    if file.filename == '':
        return jsonify({'error': 'Nom de fichier vide'}), 400
    
    # Utiliser le nom exact envoyé par le frontend (sans ajouter de timestamp)
    filename = secure_filename(file.filename)
    filepath = os.path.join(RECEPTIONS_FOLDER, filename)
    
    # Sauvegarder le fichier
    file.save(filepath)
    
    # Retourner le nom exact du fichier
    return jsonify({
        'status': 'success', 
        'filename': filename,
        'path': filepath
    })
# ==================== ROUTES QUALITÉ ====================

@app.route('/stock/qualite/anomalies')
@require_auth
def stock_qualite_anomalies():
    if request.user_role not in ['stock', 'qualite', 'admin']:
        return redirect('/dashboard')
    return render_template('modules/qualite/anomalies.html')

@app.route('/stock/qualite/corrections')
@require_auth
def stock_qualite_corrections():
    if request.user_role not in ['stock', 'qualite', 'admin']:
        return redirect('/dashboard')
    return render_template('modules/qualite/corrections.html')

@app.route('/stock/qualite/historique')
@require_auth
def stock_qualite_historique():
    if request.user_role not in ['stock', 'qualite', 'admin']:
        return redirect('/dashboard')
    return render_template('modules/qualite/historique.html')


# ==================== API QUALITÉ ====================
@app.route('/api/matching/generate-anomalies', methods=['POST'])
@require_auth
def generate_anomalies():
    """Génère un fichier JSON des anomalies pour le responsable qualité"""
    data = request.get_json()
    
    facture_id = data.get('facture_id')
    reception_id = data.get('reception_id')
    produits_manquants = data.get('produits_manquants', [])
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Récupérer les informations de la facture
    cursor.execute('SELECT reference_reception, nom, informations FROM factures_recues WHERE id = ?', (facture_id,))
    facture = cursor.fetchone()
    
    # Récupérer les informations de la réception AVEC le chemin du fichier
    cursor.execute('SELECT reference, client, nom, chemin_fichier FROM commandes_recues WHERE id = ?', (reception_id,))
    reception = cursor.fetchone()
    
    # Déterminer le chemin réel du fichier
    reception_path = None
    reception_filename = reception['nom'] if reception else None
    
    if reception_filename:
        # Chercher le fichier dans le dossier receptions
        receptions_folder = os.path.join(BASE_DIR, 'data', 'uploads', 'receptions')
        possible_path = os.path.join(receptions_folder, reception_filename)
        
        if os.path.exists(possible_path):
            reception_path = possible_path
        else:
            # Chercher le fichier qui contient la référence
            for f in os.listdir(receptions_folder):
                if reception['reference'] in f and f.endswith('.xlsx'):
                    reception_path = os.path.join(receptions_folder, f)
                    reception_filename = f
                    break
    
    # Créer la structure du fichier JSON avec le chemin du fichier
    anomalies = {
        "id": f"anomalie_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "date_creation": datetime.now().isoformat(),
        "statut": "en_attente",
        "facture": {
            "id": facture_id,
            "reference": facture['reference_reception'] if facture else 'N/A',
            "nom": facture['nom'] if facture else 'N/A'
        },
        "reception": {
            "id": reception_id,
            "reference": reception['reference'] if reception else 'N/A',
            "client": reception['client'] if reception else 'N/A',
            "fichier_original": reception_filename,
            "chemin_fichier": reception_path  # ← AJOUT DU CHEMIN COMPLET
        },
        "produits_manquants": produits_manquants,
        "corrections": []
    }
    
    conn.close()
    
    # Sauvegarder le fichier JSON
    anomalies_folder = os.path.join(BASE_DIR, 'data', 'anomalies')
    os.makedirs(anomalies_folder, exist_ok=True)
    
    filename = f"anomalie_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(anomalies_folder, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(anomalies, f, indent=4, ensure_ascii=False)
    
    return jsonify({
        'status': 'success',
        'filename': filename,
        'filepath': filepath,
        'reception_path': reception_path
    })
    
@app.route('/api/qualite/anomalies', methods=['GET'])
@require_auth
def api_qualite_anomalies():
    if request.user_role not in ['stock', 'qualite', 'admin']:
        return jsonify({'error': 'Non autorisé'}), 403
    
    anomalies_folder = os.path.join(BASE_DIR, 'data', 'anomalies')
    anomalies = []
    
    if os.path.exists(anomalies_folder):
        for filename in os.listdir(anomalies_folder):
            if filename.endswith('.json'):
                filepath = os.path.join(anomalies_folder, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        anomaly = json.load(f)
                        anomaly['id'] = filename.replace('.json', '')
                        anomalies.append(anomaly)
                except:
                    pass
    
    anomalies.sort(key=lambda x: x.get('date_creation', ''), reverse=True)
    return jsonify({'status': 'success', 'anomalies': anomalies})

@app.route('/api/qualite/corrections', methods=['GET'])
@require_auth
def api_qualite_corrections():
    if request.user_role not in ['stock', 'qualite', 'admin']:
        return jsonify({'error': 'Non autorisé'}), 403
    
    anomalies_folder = os.path.join(BASE_DIR, 'data', 'anomalies')
    corrections = []
    
    if os.path.exists(anomalies_folder):
        for filename in os.listdir(anomalies_folder):
            if filename.endswith('.json'):
                filepath = os.path.join(anomalies_folder, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        anomaly = json.load(f)
                        if anomaly.get('statut') == 'en_attente':
                            anomaly['id'] = filename.replace('.json', '')
                            corrections.append(anomaly)
                except:
                    pass
    
    corrections.sort(key=lambda x: x.get('date_creation', ''), reverse=True)
    return jsonify({'status': 'success', 'corrections': corrections})

@app.route('/api/qualite/historique', methods=['GET'])
@require_auth
def api_qualite_historique():
    if request.user_role not in ['stock', 'qualite', 'admin']:
        return jsonify({'error': 'Non autorisé'}), 403
    
    anomalies_folder = os.path.join(BASE_DIR, 'data', 'anomalies')
    historique = []
    
    if os.path.exists(anomalies_folder):
        for filename in os.listdir(anomalies_folder):
            if filename.endswith('.json'):
                filepath = os.path.join(anomalies_folder, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        anomaly = json.load(f)
                        historique.append({
                            'id': filename.replace('.json', ''),
                            'type': 'anomalie',
                            'date': anomaly.get('date_creation', ''),
                            'facture_reference': anomaly.get('facture', {}).get('reference', ''),
                            'reception_reference': anomaly.get('reception', {}).get('reference', ''),
                            'client': anomaly.get('reception', {}).get('client', ''),
                            'nb_produits': len(anomaly.get('produits_manquants', [])),
                            'statut': anomaly.get('statut', 'en_attente')
                        })
                except:
                    pass
    
    historique.sort(key=lambda x: x.get('date', ''), reverse=True)
    return jsonify({'status': 'success', 'historique': historique})

@app.route('/api/qualite/appliquer-corrections', methods=['POST'])
@require_auth
def api_qualite_appliquer_corrections():
    """Applique les corrections et modifie le fichier Excel de réception"""
    if request.user_role not in ['stock', 'qualite', 'admin']:
        return jsonify({'error': 'Non autorisé'}), 403
    
    data = request.get_json()
    anomalie_id = data.get('anomalie_id')
    corrections = data.get('corrections', [])
    commentaire = data.get('commentaire', '')
    
    # Récupérer le fichier d'anomalies
    anomalies_folder = os.path.join(BASE_DIR, 'data', 'anomalies')
    anomalies_file = os.path.join(anomalies_folder, f"{anomalie_id}.json")
    
    if not os.path.exists(anomalies_file):
        return jsonify({'error': 'Fichier d\'anomalies non trouvé'}), 404
    
    with open(anomalies_file, 'r', encoding='utf-8') as f:
        anomaly = json.load(f)
    
    # Récupérer le chemin du fichier de réception depuis l'anomalie
    reception_path = anomaly.get('reception', {}).get('chemin_fichier')
    reception_id = anomaly.get('reception', {}).get('id')
    reception_filename = anomaly.get('reception', {}).get('fichier_original')
    
    # Si le chemin n'est pas dans l'anomalie, le reconstruire
    if not reception_path or not os.path.exists(reception_path):
        receptions_folder = os.path.join(BASE_DIR, 'data', 'uploads', 'receptions')
        reception_path = os.path.join(receptions_folder, reception_filename)
    
    modification_appliquee = False
    modified_filename = None
    
    if os.path.exists(reception_path):
        try:
            # Lire le fichier Excel existant
            df = pd.read_excel(reception_path)
            print(f"📄 Fichier Excel lu: {reception_path}")
            
            # Appliquer les corrections
            for correction in corrections:
                reference = correction.get('reference')
                nouvelle_quantite = correction.get('nouvelle_quantite')
                nouvel_etat = correction.get('nouvel_etat')
                
                if 'Référence' in df.columns:
                    mask = df['Référence'] == reference
                    if mask.any():
                        if nouvelle_quantite is not None:
                            df.loc[mask, 'Qté reçue'] = nouvelle_quantite
                            print(f"   ✅ Référence {reference}: Qté → {nouvelle_quantite}")
                        if nouvel_etat is not None:
                            df.loc[mask, 'État'] = nouvel_etat
                            print(f"   ✅ Référence {reference}: État → {nouvel_etat}")
            
            # Créer le fichier modifié
            modified_filename = reception_filename.replace('.xlsx', '_modifie.xlsx')
            modified_path = os.path.join(os.path.dirname(reception_path), modified_filename)
            df.to_excel(modified_path, index=False)
            print(f"📁 Fichier modifié sauvegardé: {modified_path}")
            modification_appliquee = True
            
            # Mettre à jour la base de données
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE commandes_recues 
                SET nom = ?, statut = 'corrige', updated_at = ?, chemin_fichier = ?
                WHERE id = ?
            ''', (modified_filename, datetime.now().isoformat(), modified_path, reception_id))
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Erreur lors de la modification: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"❌ Fichier Excel non trouvé: {reception_path}")
    
    # Mettre à jour le fichier d'anomalies
    anomaly['statut'] = 'corrige'
    anomaly['date_correction'] = datetime.now().isoformat()
    anomaly['corrections'] = corrections
    anomaly['commentaire'] = commentaire
    if modification_appliquee:
        anomaly['reception']['fichier_modifie'] = modified_filename
        anomaly['reception']['chemin_fichier_modifie'] = modified_path
    
    with open(anomalies_file, 'w', encoding='utf-8') as f:
        json.dump(anomaly, f, indent=4, ensure_ascii=False)
    
    return jsonify({
        'status': 'success',
        'message': 'Corrections appliquées avec succès',
        'modified_file': modified_filename
    })
    
@app.route('/api/commandes-recues', methods=['POST'])
@require_auth
def api_commandes_post():
    data = request.get_json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Construire le chemin du fichier
    filename = data.get('nom')
    filepath = os.path.join(RECEPTIONS_FOLDER, filename) if filename else None
    
    cursor.execute('''
        INSERT INTO commandes_recues (nom, reference, client, date_reception, produits, statut, user_id, chemin_fichier)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (filename, data.get('reference'), data.get('client'), 
          data.get('date_reception'), json.dumps(data.get('produits', [])), 
          data.get('statut', 'valide'), request.user_id, filepath))
    
    conn.commit()
    commande_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'status': 'success', 'id': commande_id})
    
# ==================== LANCEMENT ====================

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 AutoStockCheck - Serveur démarré")
    print("=" * 60)
    print("🌐 http://localhost:5000")
    print("📝 Comptes par défaut:")
    print("   - Admin: admin / Admin@123")
    print("   - Stock: stock_manager / Stock@123")
    print("📁 Logs: data/logs/")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)