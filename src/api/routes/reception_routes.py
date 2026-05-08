import json
import os
from flask import request, jsonify
from datetime import datetime
from database import get_db
from auth import require_auth
from config import FACTURES_FOLDER, RECEPTIONS_FOLDER

def register_reception_routes(app):
    
    @app.route('/api/commandes-recues', methods=['GET', 'POST', 'PUT', 'DELETE'])
    @require_auth
    def api_commandes_recues():
        conn = get_db()
        cursor = conn.cursor()
        
        if request.method == 'GET':
            cursor.execute('SELECT * FROM commandes_recues WHERE user_id = ? ORDER BY date_ajout DESC', (request.user_id,))
            rows = cursor.fetchall()
            conn.close()
            commandes = [dict(r) for r in rows]
            for c in commandes:
                if c.get('produits'):
                    c['produits'] = json.loads(c['produits'])
            return jsonify({'status': 'success', 'commandes': commandes})
        
        elif request.method == 'POST':
            data = request.get_json()
            cursor.execute('''
                INSERT INTO commandes_recues (user_id, nom, reference, client, fournisseur, produits, statut, date_reception, ajoute_par)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (request.user_id, data.get('nom'), data.get('reference'), data.get('client'), data.get('fournisseur'),
                  json.dumps(data.get('produits', [])), data.get('statut', 'en_attente'), data.get('date_reception'), data.get('ajoute_par')))
            conn.commit()
            conn.close()
            return jsonify({'status': 'success', 'message': 'Commande enregistrée'})
        
        elif request.method == 'PUT':
            data = request.get_json()
            commande_id = data.get('id')
            cursor.execute('''
                UPDATE commandes_recues SET produits = ?, statut = ?, client = ? WHERE id = ? AND user_id = ?
            ''', (json.dumps(data.get('produits', [])), data.get('statut'), data.get('client'), commande_id, request.user_id))
            conn.commit()
            conn.close()
            return jsonify({'status': 'success', 'message': 'Commande mise à jour'})
        
        else:
            commande_id = request.args.get('id')
            cursor.execute('DELETE FROM commandes_recues WHERE id = ? AND user_id = ?', (commande_id, request.user_id))
            conn.commit()
            conn.close()
            return jsonify({'status': 'success', 'message': 'Commande supprimée'})
    
    @app.route('/api/factures-recues', methods=['GET', 'POST', 'DELETE'])
    @require_auth
    def api_factures_recues():
        conn = get_db()
        cursor = conn.cursor()
        
        if request.method == 'GET':
            cursor.execute('SELECT * FROM factures_recues ORDER BY date_ajout DESC')
            rows = cursor.fetchall()
            conn.close()
            factures = []
            for r in rows:
                f = dict(r)
                if f.get('contenu'):
                    f['contenu'] = json.loads(f['contenu'])
                factures.append(f)
            return jsonify({'status': 'success', 'factures': factures})
        
        elif request.method == 'POST':
            if 'fichier' not in request.files:
                return jsonify({'status': 'error', 'message': 'Aucun fichier'}), 400
            
            fichier = request.files['fichier']
            reference = request.form.get('reference', '')
            informations = request.form.get('informations', '')
            contenu_json = request.form.get('contenu', '{}')
            
            # Sauvegarder le fichier
            year = datetime.now().strftime('%Y')
            month = datetime.now().strftime('%m')
            folder = os.path.join(FACTURES_FOLDER, year, month)
            os.makedirs(folder, exist_ok=True)
            filename = f"facture_{reference}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            filepath = os.path.join(folder, filename)
            fichier.save(filepath)
            
            cursor.execute('''
                INSERT INTO factures_recues (user_id, nom, reference_reception, informations, statut, contenu, chemin_fichier, nom_fichier, date_ajout, ajoute_par)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (request.user_id, filename, reference, informations, 'en-attente', contenu_json, filepath, filename, datetime.now().isoformat(), request.user_id))
            conn.commit()
            conn.close()
            return jsonify({'status': 'success', 'message': 'Facture ajoutée'})
        
        else:
            facture_id = request.args.get('id')
            cursor.execute('DELETE FROM factures_recues WHERE id = ?', (facture_id,))
            conn.commit()
            conn.close()
            return jsonify({'status': 'success', 'message': 'Facture supprimée'})
        