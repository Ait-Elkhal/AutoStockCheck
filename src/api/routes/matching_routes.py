import json
import os
from flask import request, jsonify
from datetime import datetime
from database import get_db
from auth import require_auth
from config import ANOMALIES_FOLDER, COMPARAISONS_FOLDER

def register_matching_routes(app):
    
    @app.route('/api/matching/compare', methods=['POST'])
    @require_auth
    def api_matching_compare():
        data = request.get_json()
        facture_id = data.get('facture_id')
        reception_id = data.get('reception_id')
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM factures_recues WHERE id = ?', (facture_id,))
        facture = cursor.fetchone()
        cursor.execute('SELECT * FROM commandes_recues WHERE id = ?', (reception_id,))
        reception = cursor.fetchone()
        conn.close()
        
        if not facture or not reception:
            return jsonify({'status': 'error', 'message': 'Facture ou réception non trouvée'}), 404
        
        # Extraire les données
        facture_contenu = json.loads(facture['contenu']) if facture['contenu'] else {}
        reception_produits = json.loads(reception['produits']) if reception['produits'] else []
        
        facture_lignes = facture_contenu.get('lignes', [])
        facture_headers = facture_contenu.get('en_tete', [])
        
        # Trouver indices
        ref_idx = next((i for i, h in enumerate(facture_headers) if 'ref' in str(h).lower()), 0)
        qte_idx = next((i for i, h in enumerate(facture_headers) if 'quant' in str(h).lower()), 2)
        
        resultats = []
        reception_map = {p['reference']: p for p in reception_produits}
        
        for ligne in facture_lignes:
            if ref_idx < len(ligne):
                ref = str(ligne[ref_idx])
                qte_facture = float(ligne[qte_idx]) if qte_idx < len(ligne) else 0
                qte_reception = reception_map.get(ref, {}).get('quantite', 0)
                difference = qte_reception - qte_facture
                
                resultats.append({
                    'reference': ref,
                    'produit': ligne[1] if len(ligne) > 1 else ref,
                    'quantite_facture': qte_facture,
                    'quantite_reception': qte_reception,
                    'difference': difference,
                    'statut': 'manque' if difference < 0 else 'conforme'
                })
        
        return jsonify({'status': 'success', 'resultats': resultats})
    
    @app.route('/api/matching/anomalies', methods=['GET', 'POST', 'PUT'])
    @require_auth
    def api_matching_anomalies():
        if request.method == 'GET':
            fichiers = []
            if os.path.exists(ANOMALIES_FOLDER):
                for f in os.listdir(ANOMALIES_FOLDER):
                    if f.endswith('.json'):
                        with open(os.path.join(ANOMALIES_FOLDER, f), 'r', encoding='utf-8') as file:
                            data = json.load(file)
                        fichiers.append({'filename': f, 'id': data.get('id'), 'date_creation': data.get('date_creation'), 
                                        'statut': data.get('statut'), 'produits_count': len(data.get('produits', []))})
            return jsonify({'status': 'success', 'anomalies': sorted(fichiers, key=lambda x: x['date_creation'], reverse=True)})
        
        elif request.method == 'POST':
            data = request.get_json()
            anomalie = {
                'id': datetime.now().strftime('%Y%m%d_%H%M%S'),
                'date_creation': datetime.now().isoformat(),
                'facture_id': data.get('facture_id'),
                'facture_reference': data.get('facture_reference'),
                'reception_id': data.get('reception_id'),
                'reception_reference': data.get('reception_reference'),
                'statut': 'en_attente',
                'produits': data.get('anomalies', [])
            }
            filename = f"anomalie_{anomalie['id']}.json"
            with open(os.path.join(ANOMALIES_FOLDER, filename), 'w', encoding='utf-8') as f:
                json.dump(anomalie, f, indent=2, ensure_ascii=False)
            return jsonify({'status': 'success', 'filename': filename})
        
        else:
            data = request.get_json()
            filename = data.get('filename')
            filepath = os.path.join(ANOMALIES_FOLDER, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                anomalie = json.load(f)
            anomalie['statut'] = data.get('statut', 'corrige')
            anomalie['date_correction'] = datetime.now().isoformat()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(anomalie, f, indent=2, ensure_ascii=False)
            return jsonify({'status': 'success', 'message': 'Anomalie mise à jour'})
    
    @app.route('/api/matching/valider', methods=['POST'])
    @require_auth
    def api_matching_valider():
        data = request.get_json()
        # Logique de validation finale
        return jsonify({'status': 'success', 'message': 'Validation réussie'})