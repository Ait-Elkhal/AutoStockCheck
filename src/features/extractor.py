"""
Feature Extractor - Extraction des features pour les modèles ML
AutoStockCheck - ECU Worldwide
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
import os


class FeatureExtractor:
    """
    Extracteur de features enrichies pour les données de facture et stock
    """
    
    def __init__(self):
        self.feature_names = []
        self.scaler_params = {}
        self.category_encoders = {}
    
    def extract_from_dataframes(self, df_facture: pd.DataFrame, 
                                 df_stock: pd.DataFrame) -> pd.DataFrame:
        """
        Extrait toutes les features à partir des DataFrames
        """
        # Fusionner les DataFrames
        merged = pd.merge(
            df_facture, df_stock, 
            on='reference', 
            how='outer',
            suffixes=('_facture', '_stock')
        )
        
        # Remplacer les NaN
        merged['quantite_facture'] = merged['quantite_facture'].fillna(0)
        merged['quantite_stock'] = merged['quantite_stock'].fillna(0)
        
        # ========== FEATURES DE BASE ==========
        merged['diff_quantite'] = merged['quantite_facture'] - merged['quantite_stock']
        merged['produit_absent'] = (merged['quantite_stock'] == 0).astype(int)
        merged['quantite_insuffisante'] = (merged['diff_quantite'] > 0).astype(int)
        merged['ratio_stock'] = merged['quantite_stock'] / (merged['quantite_facture'] + 1)
        
        # ========== FEATURES PRODUIT ==========
        # État du produit (si disponible)
        if 'etat_produit' in merged.columns:
            merged['etat_produit'] = merged['etat_produit'].fillna(0.95)
        else:
            merged['etat_produit'] = 0.95
        
        # Fiabilité fournisseur (si disponible)
        if 'fournisseur' in merged.columns:
            fournisseur_fiabilite = {
                'Dell': 0.95, 'Logitech': 0.98, 'Corsair': 0.97, 'Samsung': 0.99,
                'Belkin': 0.92, 'Sony': 0.96, 'Wacom': 0.94, 'HP': 0.93,
                'Generic': 0.85, 'Blue': 0.95, 'TP-Link': 0.96, 'Netgear': 0.94,
                'APC': 0.97, 'Seagate': 0.95
            }
            merged['fiabilite_fournisseur'] = merged['fournisseur'].map(fournisseur_fiabilite).fillna(0.90)
        else:
            merged['fiabilite_fournisseur'] = 0.95
        
        # Popularité (si disponible)
        if 'popularite' in merged.columns:
            merged['popularite'] = merged['popularite'].fillna(0.6)
        else:
            merged['popularite'] = 0.6
        
        # ========== FEATURES TEMPORELLES ==========
        # Date de commande
        if 'date_commande' in merged.columns:
            merged['date_commande'] = pd.to_datetime(merged['date_commande'])
            merged['mois'] = merged['date_commande'].dt.month
            merged['trimestre'] = merged['date_commande'].dt.quarter
            merged['jour_semaine'] = merged['date_commande'].dt.dayofweek
            merged['est_weekend'] = (merged['jour_semaine'] >= 5).astype(int)
            
            # Saisonnalité
            merged['saisonnalite'] = 1.0
            merged.loc[merged['mois'].isin([11, 12]), 'saisonnalite'] = 1.3
            merged.loc[merged['mois'].isin([9, 10]), 'saisonnalite'] = 1.2
            merged.loc[merged['mois'].isin([1, 2]), 'saisonnalite'] = 0.8
        else:
            merged['mois'] = 6
            merged['trimestre'] = 2
            merged['jour_semaine'] = 3
            merged['est_weekend'] = 0
            merged['saisonnalite'] = 1.0
        
        # ========== FEATURES PRIX ET VALEUR ==========
        if 'prix_unitaire' in merged.columns:
            merged['prix'] = merged['prix_unitaire'].fillna(0)
            merged['valeur_ligne'] = merged['quantite_facture'] * merged['prix']
            merged['produit_cher'] = (merged['prix'] > 100).astype(int)
        else:
            merged['prix'] = 0
            merged['valeur_ligne'] = 0
            merged['produit_cher'] = 0
        
        # ========== FEATURES PRIORITÉ ==========
        if 'priorite' in merged.columns:
            priorite_mapping = {'basse': 0, 'moyenne': 1, 'haute': 2, 'urgente': 3}
            merged['priorite_encoded'] = merged['priorite'].map(priorite_mapping).fillna(1)
        else:
            merged['priorite_encoded'] = 1
        
        # ========== FEATURES D'INTERACTION ==========
        merged['diff_x_prix'] = merged['diff_quantite'] * merged['prix']
        merged['absent_x_prix'] = merged['produit_absent'] * merged['prix']
        merged['etat_x_popularite'] = merged['etat_produit'] * merged['popularite']
        merged['fiabilite_x_prix'] = merged['fiabilite_fournisseur'] * merged['prix']
        
        # ========== FEATURES CATÉGORIELLES ==========
        if 'categorie' in merged.columns:
            # Encodage des catégories
            categories = merged['categorie'].unique()
            cat_mapping = {cat: i for i, cat in enumerate(categories)}
            merged['categorie_encoded'] = merged['categorie'].map(cat_mapping).fillna(0)
        else:
            merged['categorie_encoded'] = 0
        
        # ========== FEATURES ANOMALIES ==========
        merged['quantite_anormale'] = (merged['quantite_facture'] > merged['quantite_facture'].quantile(0.95)).astype(int)
        merged['prix_anormal'] = (merged['prix'] > merged['prix'].quantile(0.95)).astype(int)
        
        # ========== LISTE FINALE DES FEATURES ==========
        feature_cols = [
            # Base
            'diff_quantite', 'produit_absent', 'quantite_insuffisante', 'ratio_stock',
            # Produit
            'etat_produit', 'fiabilite_fournisseur', 'popularite',
            # Temporel
            'mois', 'trimestre', 'jour_semaine', 'est_weekend', 'saisonnalite',
            # Valeur
            'prix', 'valeur_ligne', 'produit_cher',
            # Priorité
            'priorite_encoded',
            # Interactions
            'diff_x_prix', 'absent_x_prix', 'etat_x_popularite', 'fiabilite_x_prix',
            # Catégorie
            'categorie_encoded',
            # Anomalies
            'quantite_anormale', 'prix_anormal'
        ]
        
        self.feature_names = feature_cols
        
        # Retourner uniquement les colonnes sélectionnées
        return merged[feature_cols]
    
    def get_feature_names(self) -> List[str]:
        """Retourne la liste des noms des features"""
        return self.feature_names
    
    def get_feature_count(self) -> int:
        """Retourne le nombre de features"""
        return len(self.feature_names)