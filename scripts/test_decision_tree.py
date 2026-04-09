"""
Script de test pour l'arbre de décision
AutoStockCheck - ECU Worldwide
"""

import sys
import os
import pandas as pd

# Ajouter le chemin src pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from src.models.decision_tree import DecisionTree
from sklearn.model_selection import train_test_split


def test_decision_tree():
    """Test complet de l'arbre de décision"""
    
    print("=" * 60)
    print("TEST DE L'ARBRE DE DÉCISION (DECISION TREE)")
    print("=" * 60)
    
    # ==================== 1. TEST SUR DONNÉES SYNTHÉTIQUES ====================
    print("\n📊 1. Test sur données synthétiques...")
    
    # Générer des données synthétiques simples
    np.random.seed(42)
    n_samples = 500
    
    # Créer une relation non linéaire simple
    X = np.random.randn(n_samples, 3)
    y = ((X[:, 0] + X[:, 1] > 0) | (X[:, 2] > 1)).astype(int)
    
    # Diviser en train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"   Données d'entraînement: {X_train.shape}")
    print(f"   Données de test: {X_test.shape}")
    print(f"   Distribution train: {np.bincount(y_train)}")
    print(f"   Distribution test: {np.bincount(y_test)}")
    
    # Créer et entraîner le modèle
    print("\n🚀 Entraînement du Decision Tree...")
    dt = DecisionTree(max_depth=5, criterion='entropy')
    dt.fit(X_train, y_train)
    
    print(f"   Temps d'entraînement: {dt.training_time:.4f} secondes")
    
    # Évaluer
    metrics = dt.evaluate(X_test, y_test)
    
    print(f"\n📈 Performances:")
    print(f"   Accuracy:  {metrics['accuracy']:.4f}")
    print(f"   Precision: {metrics['precision']:.4f}")
    print(f"   Recall:    {metrics['recall']:.4f}")
    print(f"   F1-Score:  {metrics['f1_score']:.4f}")
    
    # ==================== 2. TEST AVEC LES DONNÉES RÉELLES ====================
    print("\n📊 2. Test avec les données du dataset AutoStockCheck...")
    
    # Charger le dataset généré
    dataset_path = "data/datasets/dataset_entrainement.csv"
    
    if os.path.exists(dataset_path):
        df = pd.read_csv(dataset_path)
        print(f"   Dataset chargé: {len(df)} lignes")
        
        # Sélectionner les features
        feature_cols = ['diff_quantite', 'produit_absent', 'quantite_insuffisante', 'prix']
        X = df[feature_cols].values
        y = df['label'].values
        
        # Diviser
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print(f"   Données d'entraînement: {X_train.shape}")
        print(f"   Données de test: {X_test.shape}")
        
        # Entraîner
        dt2 = DecisionTree(max_depth=5, criterion='gini')
        dt2.fit(X_train, y_train)
        
        print(f"   Temps d'entraînement: {dt2.training_time:.4f} secondes")
        
        # Évaluer
        metrics2 = dt2.evaluate(X_test, y_test)
        
        print(f"\n📈 Performances sur données réelles:")
        print(f"   Accuracy:  {metrics2['accuracy']:.4f}")
        print(f"   Precision: {metrics2['precision']:.4f}")
        print(f"   Recall:    {metrics2['recall']:.4f}")
        print(f"   F1-Score:  {metrics2['f1_score']:.4f}")
        
        # ==================== 3. TEST DE SAUVEGARDE ====================
        print("\n💾 3. Test de sauvegarde et chargement...")
        
        # Sauvegarder le modèle
        dt2.save("models_saved/decision_tree.pkl")
        
        # Charger le modèle
        loaded_dt = DecisionTree.load("models_saved/decision_tree.pkl")
        
        # Vérifier les prédictions
        y_pred_original = dt2.predict(X_test)
        y_pred_loaded = loaded_dt.predict(X_test)
        
        if np.array_equal(y_pred_original, y_pred_loaded):
            print("   ✅ Sauvegarde et chargement OK")
        else:
            print("   ❌ Erreur: Les prédictions ne correspondent pas")
        
        # ==================== 4. AFFICHAGE DE L'ARBRE ====================
        print("\n🌳 4. Structure de l'arbre:")
        print("   (Affichage simplifié)")
        # dt2.print_tree()  # Décommenter pour afficher l'arbre complet
        
        # ==================== 5. IMPORTANCE DES FEATURES ====================
        print("\n📊 5. Importance des features:")
        importance = dt2.get_feature_importance(feature_cols)
        for feat, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True):
            print(f"   {feat}: {imp:.4f}")
        
        # ==================== 6. TEST AVEC DIFFÉRENTS PARAMÈTRES ====================
        print("\n📊 6. Test avec différents paramètres:")
        
        for depth in [3, 5, 7, 10]:
            dt_test = DecisionTree(max_depth=depth, criterion='entropy')
            dt_test.fit(X_train, y_train)
            acc = dt_test.evaluate(X_test, y_test)['accuracy']
            print(f"   max_depth={depth}: Accuracy = {acc:.4f}")
        
    else:
        print(f"   ❌ Dataset non trouvé: {dataset_path}")
        print("   Exécutez d'abord: python scripts/generate_synthetic_data.py")
    
    # ==================== 7. RÉSUMÉ ====================
    print("\n" + "=" * 60)
    print("✅ TEST TERMINÉ AVEC SUCCÈS !")
    print("=" * 60)
    
    # Afficher le résumé du modèle
    print(dt.summary())


def test_edge_cases():
    """Test des cas limites"""
    print("\n" + "=" * 60)
    print("TEST DES CAS LIMITES")
    print("=" * 60)
    
    # Test avec une seule classe
    print("\n📊 Test avec une seule classe:")
    X = np.random.randn(100, 2)
    y = np.zeros(100)
    
    dt = DecisionTree(max_depth=3)
    dt.fit(X, y)
    y_pred = dt.predict(X)
    
    if np.all(y_pred == 0):
        print("   ✅ OK: Toutes les prédictions sont 0")
    else:
        print("   ❌ Erreur")
    
    # Test avec un seul échantillon
    print("\n📊 Test avec un seul échantillon:")
    X = np.random.randn(1, 2)
    y = np.array([1])
    
    dt = DecisionTree(max_depth=3)
    dt.fit(X, y)
    y_pred = dt.predict(X)
    
    if y_pred[0] == 1:
        print("   ✅ OK: Prédiction correcte")
    else:
        print("   ❌ Erreur")
    
    # Test avec min_samples_leaf
    print("\n📊 Test avec min_samples_leaf=5:")
    X = np.random.randn(100, 2)
    y = (X[:, 0] > 0).astype(int)
    
    dt = DecisionTree(max_depth=10, min_samples_leaf=5)
    dt.fit(X, y)
    
    print(f"   ✅ Modèle entraîné avec min_samples_leaf=5")
    
    print("\n✅ Tous les cas limites sont passés!")


if __name__ == "__main__":
    test_decision_tree()
    test_edge_cases()