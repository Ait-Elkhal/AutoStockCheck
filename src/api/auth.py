import secrets
from functools import wraps
from flask import request, jsonify
from database import get_db

# Stockage des tokens
tokens = {}

def generate_token():
    return secrets.token_urlsafe(32)

def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('token')
        if not token or token not in tokens:
            return jsonify({'status': 'error', 'message': 'Non authentifié'}), 401
        
        user_id = tokens[token]
        request.user_id = user_id
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, role FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return jsonify({'status': 'error', 'message': 'Utilisateur non trouvé'}), 401
        
        # Convertir l'objet Row en dictionnaire si nécessaire
        if hasattr(user, 'keys'):
            # C'est un objet Row
            request.user_role = user['role']
            request.user_name = user['username']
        else:
            # C'est un tuple
            request.user_role = user[3]
            request.user_name = user[1]
        
        return f(*args, **kwargs)
    return decorated

def get_user_from_token():
    token = request.cookies.get('token')
    if token and token in tokens:
        user_id = tokens[token]
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, role FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        if user:
            if hasattr(user, 'keys'):
                return dict(user)
            else:
                return {'id': user[0], 'username': user[1], 'email': user[2], 'role': user[3]}
    return None