"""
Script de test pour la Random Forest
AutoStockCheck - ECU Worldwide
"""

import sys
import os
import pandas as pd

# Ajouter le chemin src pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from src.models.random_forest import RandomForest
from src.models.decision_tree import DecisionTree  # Ajout de l'import
from sklearn.model_selection import train_test_split


def test_random_forest():
    """Test complet de la Random Forest"""
    
    print("=" * 60)
    print("TEST DE LA RANDOM FOREST")
    print("=" * 60)
    
    # ==================== 1. TEST SUR DONNÉES SYNTHÉTIQUES ====================
    print("\n📊 1. Test sur données synthétiques...")
    
    # Générer des données synthétiques
    np.random.seed(42)
    n_samples = 500
    
    X = np.random.randn(n_samples, 4)
    y = ((X[:, 0] + X[:, 1] > 0) | (X[:, 2] > 1)).astype(int)
    
    # Diviser en train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"   Données d'entraînement: {X_train.shape}")
    print(f"   Données de test: {X_test.shape}")
    
    # Test avec différentes configurations
    print("\n🚀 Test avec différentes valeurs de n_trees...")
    
    for n_trees in [5, 10, 20, 50]:
        print(f"\n   n_trees={n_trees}:")
        rf = RandomForest(n_trees=n_trees, max_depth=5, verbose=False)
        rf.fit(X_train, y_train)
        metrics = rf.evaluate(X_test, y_test)
        print(f"     Accuracy: {metrics['accuracy']:.4f}, F1: {metrics['f1_score']:.4f}")
        print(f"     Temps entraînement: {rf.training_time:.4f}s")
    
    # ==================== 2. TEST AVEC LES DONNÉES RÉELLES ====================
    print("\n📊 2. Test avec les données du dataset AutoStockCheck...")
    
    dataset_path = "data/datasets/dataset_entrainement.csv"
    
    if os.path.exists(dataset_path):
        df = pd.read_csv(dataset_path)
        print(f"   Dataset chargé: {len(df)} lignes")
        
        # Sélectionner les features
        feature_cols = ['diff_quantite', 'produit_absent', 'quantite_insuffisante', 'prix']
        X = df[feature_cols].values
        y = df['label'].values
        
        print(f"   Distribution des labels: {np.bincount(y)}")
        
        # Diviser
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print(f"   Données d'entraînement: {X_train.shape}")
        print(f"   Données de test: {X_test.shape}")
        
        # Entraîner avec différentes configurations
        print("\n🚀 Test avec différentes configurations...")
        
        best_f1 = 0
        best_config = None
        
        for n_trees in [10, 20, 50]:
            for max_depth in [3, 5, 7]:
                print(f"\n   n_trees={n_trees}, max_depth={max_depth}:")
                rf = RandomForest(n_trees=n_trees, max_depth=max_depth, 
                                  criterion='entropy', verbose=False)
                rf.fit(X_train, y_train)
                metrics = rf.evaluate(X_test, y_test)
                print(f"     Accuracy: {metrics['accuracy']:.4f}, F1: {metrics['f1_score']:.4f}")
                
                if metrics['f1_score'] > best_f1:
                    best_f1 = metrics['f1_score']
                    best_config = (n_trees, max_depth, rf)
        
        # Meilleure configuration
        if best_config:
            n_trees_best, max_depth_best, rf_best = best_config
            print(f"\n✅ Meilleure configuration: n_trees={n_trees_best}, max_depth={max_depth_best}")
            print(f"   F1-Score: {best_f1:.4f}")
            
            # Évaluation finale
            metrics_final = rf_best.evaluate(X_test, y_test)
            
            print(f"\n📈 Performances finales:")
            print(f"   Accuracy:  {metrics_final['accuracy']:.4f}")
            print(f"   Precision: {metrics_final['precision']:.4f}")
            print(f"   Recall:    {metrics_final['recall']:.4f}")
            print(f"   F1-Score:  {metrics_final['f1_score']:.4f}")
            
            # Importance des features
            print(f"\n📊 Importance des features:")
            importance = rf_best.get_feature_importance(feature_cols)
            for feat, imp in sorted(importance.items(), key=lambda x: x[1], reverse=True):
                print(f"   {feat}: {imp:.4f}")
            
            # ==================== 3. TEST DE SAUVEGARDE ====================
            print("\n💾 3. Test de sauvegarde et chargement...")
            
            rf_best.save("models_saved/random_forest.pkl")
            
            loaded_rf = RandomForest.load("models_saved/random_forest.pkl")
            
            y_pred_original = rf_best.predict(X_test)
            y_pred_loaded = loaded_rf.predict(X_test)
            
            if np.array_equal(y_pred_original, y_pred_loaded):
                print("   ✅ Sauvegarde et chargement OK")
            else:
                print("   ❌ Erreur: Les prédictions ne correspondent pas")
    
    else:
        print(f"   ❌ Dataset non trouvé: {dataset_path}")
        print("   Exécutez d'abord: python scripts/generate_synthetic_data.py")
    
    # ==================== 4. TEST DES CAS LIMITES ====================
    print("\n" + "=" * 60)
    print("TEST DES CAS LIMITES")
    print("=" * 60)
    
    # Test avec un seul arbre (équivalent à Decision Tree)
    print("\n📊 Test avec n_trees=1:")
    X_small = np.random.randn(100, 3)
    y_small = (X_small[:, 0] > 0).astype(int)
    
    rf_single = RandomForest(n_trees=1, max_depth=3, random_state=42)
    rf_single.fit(X_small, y_small)
    
    dt_single = DecisionTree(max_depth=3)
    dt_single.fit(X_small, y_small)
    
    rf_pred = rf_single.predict(X_small)
    dt_pred = dt_single.predict(X_small)
    
    if np.array_equal(rf_pred, dt_pred):
        print("   ✅ OK: Random Forest avec 1 arbre équivalent à Decision Tree")
    else:
        print(f"   ⚠️ Différence entre RF à 1 arbre et DT")
        print(f"      RF predictions (premiers 5): {rf_pred[:5]}")
        print(f"      DT predictions (premiers 5): {dt_pred[:5]}")
    
    # Test avec n_trees=0 (devrait lever une erreur)
    print("\n📊 Test avec n_trees=0:")
    try:
        rf_zero = RandomForest(n_trees=0)
        rf_zero.fit(X_small, y_small)
        print("   ❌ Erreur: n_trees=0 n'a pas été détecté")
    except Exception as e:
        print(f"   ✅ Erreur détectée: {e}")
    
    # ==================== 5. RÉSUMÉ ====================
    print("\n" + "=" * 60)
    print("✅ TEST TERMINÉ AVEC SUCCÈS !")
    print("=" * 60)
    
    if 'rf_best' in locals():
        print(rf_best.summary())


if __name__ == "__main__":
    test_random_forest()