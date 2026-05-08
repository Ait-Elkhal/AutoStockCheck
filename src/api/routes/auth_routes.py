from flask import request, jsonify, make_response
from datetime import datetime, timedelta
from database import get_db, hash_password, update_user_last_login, create_audit_log, get_user_by_id
from auth import generate_token, tokens, require_auth, get_user_from_token

def register_auth_routes(app):
    
    @app.route('/api/login', methods=['POST'])
    def api_login():
        try:
            data = request.get_json()
            
            # Version sans base de données pour tester
            if data['username'] == 'admin' and data['password'] == 'Admin@123':
                token = generate_token()
                tokens[token] = 1
                
                response = make_response(jsonify({
                    'status': 'success',
                    'user': {
                        'id': 1,
                        'username': 'admin',
                        'email': 'admin@autostockcheck.com',
                        'role': 'admin'
                    },
                    'redirect_url': '/admin'
                }))
                
                response.set_cookie('token', token, httponly=True, secure=False, samesite='Lax')
                return response
            
            return jsonify({'status': 'error', 'message': 'Identifiants invalides'}), 401
            
        except Exception as e:
            print(f"Erreur login: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 500
    
    @app.route('/api/logout', methods=['POST'])
    def api_logout():
        token = request.cookies.get('token')
        if token and token in tokens:
            # Mettre à jour session
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute('UPDATE user_sessions SET logout_at = ? WHERE token = ?', (datetime.now().isoformat(), token))
            conn.commit()
            conn.close()
            
            del tokens[token]
        
        response = make_response(jsonify({'status': 'success'}))
        response.set_cookie('token', '', expires=0, httponly=True)
        return response
    
    @app.route('/api/me', methods=['GET'])
    @require_auth
    def api_me():
        user = get_user_from_token()
        if user:
            return jsonify({'status': 'success', 'user': user})
        return jsonify({'status': 'error', 'message': 'Non authentifié'}), 401
    
    @app.route('/api/check-auth', methods=['GET'])
    def check_auth():
        token = request.cookies.get('token')
        if token and token in tokens:
            return jsonify({'status': 'success', 'authenticated': True})
        return jsonify({'status': 'success', 'authenticated': False})