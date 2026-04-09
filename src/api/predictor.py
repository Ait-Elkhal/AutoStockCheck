"""
Classe de prédiction simple (sans dépendance du modèle original)
AutoStockCheck - ECU Worldwide
"""

import numpy as np
import pickle


class SimplePredictor:
    """
    Prédicteur simple utilisant les paramètres du modèle sauvegardé
    """
    
    def __init__(self, model_params_path, scaler_path, features_path):
        """
        Charge les paramètres du modèle
        """
        # Charger les paramètres
        with open(model_params_path, 'rb') as f:
            params = pickle.load(f)
        
        self.weights = params['weights']
        self.bias = params['bias']
        self.kernel = params['kernel']
        self.features = params['features']
        
        # Charger le scaler
        with open(scaler_path, 'rb') as f:
            self.scaler = pickle.load(f)
        
        print(f"✅ Prédicteur chargé avec {len(self.features)} features")
    
    def predict(self, X):
        """
        Prédiction simple: sign(w·x + b)
        """
        scores = np.dot(X, self.weights) + self.bias
        predictions = np.where(scores >= 0, 1, -1)
        return np.where(predictions == -1, 0, 1)
    
    def predict_proba(self, X):
        """
        Probabilité approximative
        """
        scores = np.dot(X, self.weights) + self.bias
        proba_1 = 1 / (1 + np.exp(-scores))
        proba_0 = 1 - proba_1
        return np.column_stack([proba_0, proba_1])
    
    def extract_features(self, facture, stock):
        """
        Extrait les features à partir des données
        """
        features_dict = {}
        
        quantite_facture = facture.get('quantite', 0)
        quantite_stock = stock.get('quantite', 0)
        
        features_dict['diff_quantite'] = quantite_facture - quantite_stock
        features_dict['produit_absent'] = 1 if quantite_stock == 0 else 0
        features_dict['quantite_insuffisante'] = 1 if features_dict['diff_quantite'] > 0 else 0
        features_dict['ratio_stock'] = quantite_stock / (quantite_facture + 1)
        
        features_dict['etat_produit'] = stock.get('etat_produit', 0.95)
        features_dict['fiabilite_fournisseur'] = stock.get('fiabilite_fournisseur', 0.95)
        features_dict['popularite'] = facture.get('popularite', 0.6)
        features_dict['saisonnalite'] = facture.get('saisonnalite', 1.0)
        
        prix = facture.get('prix', 0)
        features_dict['prix'] = prix
        features_dict['valeur_ligne'] = quantite_facture * prix
        features_dict['produit_cher'] = 1 if prix > 100 else 0
        
        features_dict['diff_x_prix'] = features_dict['diff_quantite'] * prix
        features_dict['absent_x_prix'] = features_dict['produit_absent'] * prix
        features_dict['etat_x_popularite'] = features_dict['etat_produit'] * features_dict['popularite']
        
        # Retourner dans l'ordre
        return [features_dict.get(f, 0) for f in self.features]