import json
from flask import request, jsonify
from datetime import datetime
from database import get_db
from auth import require_auth

def register_stock_routes(app):
    
    @app.route('/api/stock', methods=['GET', 'POST', 'PUT', 'DELETE'])
    @require_auth
    def api_stock():
        conn = get_db()
        cursor = conn.cursor()
        
        if request.method == 'GET':
            cursor.execute('SELECT * FROM stock_items WHERE user_id = ?', (request.user_id,))
            rows = cursor.fetchall()
            conn.close()
            stock = [{'id': r['id'], 'product_name': r['product_name'], 'reference': r['reference'], 
                      'quantity': r['quantity'], 'location': r['location'], 'price': r.get('price', 0),
                      'stock_min': r.get('stock_min', 5), 'categorie': r.get('categorie', '')} for r in rows]
            return jsonify({'status': 'success', 'stock': stock})
        
        elif request.method == 'POST':
            data = request.get_json()
            cursor.execute('''
                INSERT INTO stock_items (user_id, product_name, reference, quantity, location, price, stock_min, categorie)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (request.user_id, data.get('product_name'), data.get('reference'), data.get('quantity', 0),
                  data.get('location'), data.get('price', 0), data.get('stock_min', 5), data.get('categorie', '')))
            conn.commit()
            conn.close()
            return jsonify({'status': 'success', 'message': 'Stock ajouté'})
        
        elif request.method == 'PUT':
            data = request.get_json()
            cursor.execute('''
                UPDATE stock_items SET product_name = ?, reference = ?, quantity = ?, location = ?, price = ?, stock_min = ?, categorie = ?
                WHERE id = ? AND user_id = ?
            ''', (data.get('product_name'), data.get('reference'), data.get('quantity'), data.get('location'),
                  data.get('price'), data.get('stock_min'), data.get('categorie'), data.get('id'), request.user_id))
            conn.commit()
            conn.close()
            return jsonify({'status': 'success', 'message': 'Stock modifié'})
        
        else:
            stock_id = request.args.get('id')
            cursor.execute('DELETE FROM stock_items WHERE id = ? AND user_id = ?', (stock_id, request.user_id))
            conn.commit()
            conn.close()
            return jsonify({'status': 'success', 'message': 'Stock supprimé'})
    
    @app.route('/api/stock/mouvement', methods=['POST'])
    @require_auth
    def api_stock_mouvement():
        data = request.get_json()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO stock_mouvements (user_id, produit_id, type, quantite, date, commentaire)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (request.user_id, data.get('produit_id'), data.get('type'), data.get('quantite'), 
              datetime.now().isoformat(), data.get('commentaire', '')))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': 'Mouvement enregistré'})