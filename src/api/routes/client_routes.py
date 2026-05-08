import os
import json
import shutil
from flask import request, jsonify
from datetime import datetime
from database import get_db
from auth import require_auth
from config import CLIENTS_ROOT

def register_client_routes(app):
    
    @app.route('/api/clients', methods=['GET', 'POST'])
    @require_auth
    def api_clients():
        conn = get_db()
        cursor = conn.cursor()
        
        if request.method == 'GET':
            cursor.execute('SELECT * FROM clients_externes ORDER BY date_inscription DESC')
            rows = cursor.fetchall()
            conn.close()
            return jsonify({'status': 'success', 'clients': [dict(r) for r in rows]})
        
        else:
            data = request.get_json()
            cursor.execute('SELECT id FROM clients_externes WHERE email = ?', (data.get('email'),))
            if cursor.fetchone():
                conn.close()
                return jsonify({'status': 'error', 'message': 'Email déjà existant'}), 400
            
            # Créer dossier client
            safe_email = data['email'].replace('@', '_at_').replace('.', '_dot_')
            client_folder = os.path.join(CLIENTS_ROOT, safe_email)
            os.makedirs(client_folder, exist_ok=True)
            
            cursor.execute('''
                INSERT INTO clients_externes (email, nom, prenom, sexe, nationalite, telephone, adresse, dossier_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (data.get('email'), data.get('nom'), data.get('prenom'), data.get('sexe'),
                  data.get('nationalite'), data.get('telephone'), data.get('adresse'), client_folder))
            conn.commit()
            conn.close()
            return jsonify({'status': 'success', 'message': 'Client ajouté'})
    
    @app.route('/api/clients/<int:client_id>', methods=['GET', 'PUT', 'DELETE'])
    @require_auth
    def api_client_detail(client_id):
        conn = get_db()
        cursor = conn.cursor()
        
        if request.method == 'GET':
            cursor.execute('SELECT * FROM clients_externes WHERE id = ?', (client_id,))
            row = cursor.fetchone()
            conn.close()
            return jsonify({'status': 'success', 'client': dict(row)}) if row else jsonify({'status': 'error', 'message': 'Non trouvé'}), 404
        
        elif request.method == 'PUT':
            data = request.get_json()
            cursor.execute('''
                UPDATE clients_externes SET nom = ?, prenom = ?, sexe = ?, nationalite = ?, telephone = ?, adresse = ?
                WHERE id = ?
            ''', (data.get('nom'), data.get('prenom'), data.get('sexe'), data.get('nationalite'),
                  data.get('telephone'), data.get('adresse'), client_id))
            conn.commit()
            conn.close()
            return jsonify({'status': 'success', 'message': 'Client modifié'})
        
        else:
            cursor.execute('SELECT dossier_path FROM clients_externes WHERE id = ?', (client_id,))
            row = cursor.fetchone()
            if row and row['dossier_path'] and os.path.exists(row['dossier_path']):
                shutil.rmtree(row['dossier_path'])
            cursor.execute('DELETE FROM clients_externes WHERE id = ?', (client_id,))
            conn.commit()
            conn.close()
            return jsonify({'status': 'success', 'message': 'Client supprimé'})
    
    @app.route('/api/clients/<int:client_id>/emails', methods=['GET'])
    @require_auth
    def api_client_emails(client_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM emails_clients WHERE client_id = ? ORDER BY date_envoi DESC', (client_id,))
        rows = cursor.fetchall()
        conn.close()
        return jsonify({'status': 'success', 'emails': [dict(r) for r in rows]})
    
    @app.route('/api/clients/<int:client_id>/factures', methods=['GET'])
    @require_auth
    def api_client_factures(client_id):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM factures_clients WHERE client_id = ? ORDER BY date_reception DESC', (client_id,))
        rows = cursor.fetchall()
        conn.close()
        factures = []
        for r in rows:
            f = dict(r)
            if f.get('contenu_extraie'):
                f['produits'] = json.loads(f['contenu_extraie'])
            factures.append(f)
        return jsonify({'status': 'success', 'factures': factures})