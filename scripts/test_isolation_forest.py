"""
Script de test pour l'Isolation Forest
AutoStockCheck - ECU Worldwide
"""

import sys
import os
import pandas as pd

# Ajouter le chemin src pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from src.models.isolation_forest import IsolationForest
from sklearn.model_selection import train_test_split


def test_isolation_forest():
    """Test complet de l'Isolation Forest"""
    
    print("=" * 60)
    print("TEST DE L'ISOLATION FOREST")
    print("=" * 60)
    
    # ==================== 1. TEST SUR DONNÉES SYNTHÉTIQUES ====================
    print("\n📊 1. Test sur données synthétiques...")
    
    # Générer des données normales et anomalies
    np.random.seed(42)
    n_normal = 400
    n_anomalies = 50
    
    # Données normales
    X_normal = np.random.randn(n_normal, 2) * 0.5
    y_normal = np.zeros(n_normal)
    
    # Anomalies (points éloignés)
    X_anomalies = np.random.randn(n_anomalies, 2) * 2 + [3, 3]
    y_anomalies = np.ones(n_anomalies)
    
    # Combiner
    X = np.vstack([X_normal, X_anomalies])
    y = np.hstack([y_normal, y_anomalies])
    
    # Diviser en train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"   Données d'entraînement: {X_train.shape}")
    print(f"   Données de test: {X_test.shape}")
    print(f"   Anomalies dans test: {np.sum(y_test)}")
    
    # Entraîner
    print("\n🚀 Entraînement de l'Isolation Forest...")
    iso_forest = IsolationForest(n_trees=100, max_depth=10, 
                                  contamination=0.1, random_state=42,
                                  verbose=True)
    iso_forest.fit(X_train)
    
    print(f"   Temps d'entraînement: {iso_forest.training_time:.4f}s")
    
    # Évaluer
    print("\n📈 Évaluation...")
    y_pred = iso_forest.predict(X_test)
    scores = iso_forest.score_samples(X_test)
    
    # Calculer les métriques manuellement
    tp = np.sum((y_pred == 1) & (y_test == 1))
    tn = np.sum((y_pred == 0) & (y_test == 0))
    fp = np.sum((y_pred == 1) & (y_test == 0))
    fn = np.sum((y_pred == 0) & (y_test == 1))
    
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    print(f"\n   Performances de détection d'anomalies:")
    print(f"     Accuracy:  {accuracy:.4f}")
    print(f"     Precision: {precision:.4f}")
    print(f"     Recall:    {recall:.4f}")
    print(f"     F1-Score:  {f1:.4f}")
    print(f"     Seuil:     {iso_forest.get_threshold():.4f}")
    
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
        print(f"   Taux de manques (anomalies): {np.mean(y):.2%}")
        
        # Diviser
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print(f"   Données d'entraînement: {X_train.shape}")
        print(f"   Données de test: {X_test.shape}")
        
        # Entraîner avec différentes configurations
        print("\n🚀 Test avec différentes configurations...")
        
        for n_trees in [50, 100, 200]:
            print(f"\n   n_trees={n_trees}:")
            iso = IsolationForest(n_trees=n_trees, max_depth=10,
                                   contamination=np.mean(y_train),
                                   random_state=42)
            iso.fit(X_train)
            
            y_pred = iso.predict(X_test)
            
            tp = np.sum((y_pred == 1) & (y_test == 1))
            tn = np.sum((y_pred == 0) & (y_test == 0))
            fp = np.sum((y_pred == 1) & (y_test == 0))
            fn = np.sum((y_pred == 0) & (y_test == 1))
            
            accuracy = (tp + tn) / (tp + tn + fp + fn)
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
            
            print(f"     Accuracy: {accuracy:.4f}, F1: {f1:.4f}")
        
        # Meilleure configuration
        print("\n🚀 Meilleure configuration...")
        iso_best = IsolationForest(n_trees=100, max_depth=10,
                                    contamination=np.mean(y_train),
                                    random_state=42, verbose=False)
        iso_best.fit(X_train)
        
        y_pred = iso_best.predict(X_test)
        scores = iso_best.score_samples(X_test)
        
        tp = np.sum((y_pred == 1) & (y_test == 1))
        tn = np.sum((y_pred == 0) & (y_test == 0))
        fp = np.sum((y_pred == 1) & (y_test == 0))
        fn = np.sum((y_pred == 0) & (y_test == 1))
        
        accuracy = (tp + tn) / (tp + tn + fp + fn)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        print(f"\n📈 Performances finales:")
        print(f"   Accuracy:  {accuracy:.4f}")
        print(f"   Precision: {precision:.4f}")
        print(f"   Recall:    {recall:.4f}")
        print(f"   F1-Score:  {f1:.4f}")
        
        # ==================== 3. TEST DE SAUVEGARDE ====================
        print("\n💾 3. Test de sauvegarde et chargement...")
        
        iso_best.save("models_saved/isolation_forest.pkl")
        
        loaded_iso = IsolationForest.load("models_saved/isolation_forest.pkl")
        
        y_pred_original = iso_best.predict(X_test)
        y_pred_loaded = loaded_iso.predict(X_test)
        
        if np.array_equal(y_pred_original, y_pred_loaded):
            print("   ✅ Sauvegarde et chargement OK")
        else:
            print("   ❌ Erreur: Les prédictions ne correspondent pas")
        
        # ==================== 4. ANALYSE DES SCORES ====================
        print("\n📊 4. Analyse des scores d'anomalie:")
        
        scores_normal = scores[y_test == 0]
        scores_anomaly = scores[y_test == 1]
        
        print(f"   Scores des points normaux: min={np.min(scores_normal):.4f}, "
              f"max={np.max(scores_normal):.4f}, mean={np.mean(scores_normal):.4f}")
        print(f"   Scores des anomalies: min={np.min(scores_anomaly):.4f}, "
              f"max={np.max(scores_anomaly):.4f}, mean={np.mean(scores_anomaly):.4f}")
        
        # Statistiques des longueurs de chemin
        path_stats = iso_best.get_path_length_stats(X_test)
        print(f"\n   Statistiques des longueurs de chemin:")
        for key, value in path_stats.items():
            print(f"     {key}: {value:.4f}")
        
    else:
        print(f"   ❌ Dataset non trouvé: {dataset_path}")
        print("   Exécutez d'abord: python scripts/generate_synthetic_data.py")
    
    # ==================== 5. RÉSUMÉ ====================
    print("\n" + "=" * 60)
    print("✅ TEST TERMINÉ AVEC SUCCÈS !")
    print("=" * 60)
    
    if 'iso_best' in locals():
        print(iso_best.summary())


if __name__ == "__main__":
    test_isolation_forest()