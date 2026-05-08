from flask import request, jsonify
from database import get_db
from auth import require_auth

def register_admin_routes(app):
    
    @app.route('/api/admin/users', methods=['GET'])
    @require_auth
    def admin_users():
        if request.user_role != 'admin':
            return jsonify({'status': 'error', 'message': 'Accès non autorisé'}), 403
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, email, company, role, statut, last_login, created_at FROM users')
        rows = cursor.fetchall()
        conn.close()
        users = [dict(r) for r in rows]
        return jsonify({'status': 'success', 'users': users})
    
    @app.route('/api/admin/users/<int:user_id>', methods=['PUT', 'DELETE'])
    @require_auth
    def admin_user_detail(user_id):
        if request.user_role != 'admin':
            return jsonify({'status': 'error', 'message': 'Accès non autorisé'}), 403
        
        conn = get_db()
        cursor = conn.cursor()
        
        if request.method == 'PUT':
            data = request.get_json()
            updates = []
            params = []
            for key in ['username', 'email', 'company', 'role', 'statut']:
                if key in data:
                    updates.append(f"{key} = ?")
                    params.append(data[key])
            if updates:
                params.append(user_id)
                cursor.execute(f'UPDATE users SET {", ".join(updates)} WHERE id = ?', params)
            conn.commit()
            conn.close()
            return jsonify({'status': 'success', 'message': 'Utilisateur modifié'})
        
        else:
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            conn.commit()
            conn.close()
            return jsonify({'status': 'success', 'message': 'Utilisateur supprimé'})
    
    @app.route('/api/admin/logs', methods=['GET'])
    @require_auth
    def admin_logs():
        if request.user_role != 'admin':
            return jsonify({'status': 'error', 'message': 'Accès non autorisé'}), 403
        
        limit = request.args.get('limit', 100, type=int)
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return jsonify({'status': 'success', 'logs': [dict(r) for r in rows]})
    
    @app.route('/api/admin/stats', methods=['GET'])
    @require_auth
    def admin_stats():
        if request.user_role != 'admin':
            return jsonify({'status': 'error', 'message': 'Accès non autorisé'}), 403
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as total FROM users')
        total_users = cursor.fetchone()['total']
        cursor.execute('SELECT COUNT(*) as total FROM commandes_recues')
        total_receptions = cursor.fetchone()['total']
        cursor.execute('SELECT COUNT(*) as total FROM factures_recues')
        total_factures = cursor.fetchone()['total']
        conn.close()
        
        return jsonify({'status': 'success', 'stats': {
            'total_users': total_users, 'total_receptions': total_receptions,
            'total_factures': total_factures, 'actions_last_24h': 0
        }})