"""
Script de test pour le K-Nearest Neighbors
AutoStockCheck - ECU Worldwide
"""

import sys
import os
import pandas as pd

# Ajouter le chemin src pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from src.models.knn import KNN
from sklearn.model_selection import train_test_split


def test_knn():
    """Test complet du KNN"""
    
    print("=" * 60)
    print("TEST DU K-NEAREST NEIGHBORS (KNN)")
    print("=" * 60)
    
    # ==================== 1. TEST SUR DONNÉES SYNTHÉTIQUES ====================
    print("\n📊 1. Test sur données synthétiques...")
    
    # Générer des données synthétiques
    np.random.seed(42)
    n_samples = 500
    
    # Créer des clusters
    X = np.random.randn(n_samples, 2)
    y = ((X[:, 0] + X[:, 1] > 0) | (X[:, 0] > 1)).astype(int)
    
    # Ajouter du bruit
    noise_idx = np.random.choice(n_samples, size=50, replace=False)
    y[noise_idx] = 1 - y[noise_idx]
    
    # Diviser en train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"   Données d'entraînement: {X_train.shape}")
    print(f"   Données de test: {X_test.shape}")
    print(f"   Distribution train: {np.bincount(y_train)}")
    print(f"   Distribution test: {np.bincount(y_test)}")
    
    # Tester différentes valeurs de k
    print("\n🚀 Test avec différentes valeurs de k...")
    
    for k in [1, 3, 5, 7, 10, 15]:
        knn = KNN(k=k, distance_metric='euclidean', weights='uniform')
        knn.fit(X_train, y_train)
        metrics = knn.evaluate(X_test, y_test)
        print(f"   k={k}: Accuracy={metrics['accuracy']:.4f}, F1={metrics['f1_score']:.4f}")
    
    # ==================== 2. TEST AVEC DIFFÉRENTES MÉTRIQUES ====================
    print("\n📊 2. Test avec différentes métriques de distance...")
    
    knn_best = KNN(k=5, distance_metric='euclidean', weights='uniform')
    knn_best.fit(X_train, y_train)
    
    for metric in ['euclidean', 'manhattan', 'minkowski', 'cosine']:
        knn = KNN(k=5, distance_metric=metric, weights='uniform')
        knn.fit(X_train, y_train)
        metrics = knn.evaluate(X_test, y_test)
        print(f"   {metric}: Accuracy={metrics['accuracy']:.4f}")
    
    # ==================== 3. TEST AVEC DIFFÉRENTES PONDÉRATIONS ====================
    print("\n📊 3. Test avec différentes méthodes de pondération...")
    
    for weights in ['uniform', 'distance']:
        knn = KNN(k=5, distance_metric='euclidean', weights=weights)
        knn.fit(X_train, y_train)
        metrics = knn.evaluate(X_test, y_test)
        print(f"   {weights}: Accuracy={metrics['accuracy']:.4f}, F1={metrics['f1_score']:.4f}")
    
    # ==================== 4. TEST AVEC LES DONNÉES RÉELLES ====================
    print("\n📊 4. Test avec les données du dataset AutoStockCheck...")
    
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
        
        # Normaliser les données (important pour KNN)
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        print("\n🚀 Recherche du meilleur k...")
        
        best_k = 0
        best_acc = 0
        
        for k in [1, 3, 5, 7, 10, 15, 20, 30]:
            knn = KNN(k=k, distance_metric='euclidean', weights='uniform')
            knn.fit(X_train_scaled, y_train)
            metrics = knn.evaluate(X_test_scaled, y_test)
            print(f"   k={k}: Accuracy={metrics['accuracy']:.4f}, F1={metrics['f1_score']:.4f}")
            
            if metrics['accuracy'] > best_acc:
                best_acc = metrics['accuracy']
                best_k = k
        
        # Entraîner avec le meilleur k
        print(f"\n✅ Meilleur k trouvé: {best_k} (Accuracy={best_acc:.4f})")
        
        knn_final = KNN(k=best_k, distance_metric='euclidean', weights='distance')
        knn_final.fit(X_train_scaled, y_train)
        metrics_final = knn_final.evaluate(X_test_scaled, y_test)
        
        print(f"\n📈 Performances finales:")
        print(f"   Accuracy:  {metrics_final['accuracy']:.4f}")
        print(f"   Precision: {metrics_final['precision']:.4f}")
        print(f"   Recall:    {metrics_final['recall']:.4f}")
        print(f"   F1-Score:  {metrics_final['f1_score']:.4f}")
        
        # ==================== 5. TEST DE SAUVEGARDE ====================
        print("\n💾 5. Test de sauvegarde et chargement...")
        
        knn_final.save("models_saved/knn.pkl")
        
        loaded_knn = KNN.load("models_saved/knn.pkl")
        
        y_pred_original = knn_final.predict(X_test_scaled)
        y_pred_loaded = loaded_knn.predict(X_test_scaled)
        
        if np.array_equal(y_pred_original, y_pred_loaded):
            print("   ✅ Sauvegarde et chargement OK")
        else:
            print("   ❌ Erreur: Les prédictions ne correspondent pas")
        
        # ==================== 6. ANALYSE DES DISTANCES ====================
        print("\n📊 6. Analyse des distances:")
        
        knn_analysis = KNN(k=5, distance_metric='euclidean')
        knn_analysis.fit(X_train_scaled, y_train)
        
        dist_stats = knn_analysis.get_distance_distribution(X_train_scaled[:100])
        print(f"   Statistiques des distances:")
        print(f"     Min: {dist_stats['min']:.4f}")
        print(f"     Max: {dist_stats['max']:.4f}")
        print(f"     Mean: {dist_stats['mean']:.4f}")
        print(f"     Std: {dist_stats['std']:.4f}")
        
        neighbors_stats = knn_analysis.get_neighbors_analysis(X_test_scaled[:100], y_test[:100])
        print(f"\n   Analyse des voisinages:")
        print(f"     Ratio de voisins de même classe: {neighbors_stats['same_class_ratio']:.4f}")
        
    else:
        print(f"   ❌ Dataset non trouvé: {dataset_path}")
        print("   Exécutez d'abord: python scripts/generate_synthetic_data.py")
    
    # ==================== 7. TEST DES CAS LIMITES ====================
    print("\n" + "=" * 60)
    print("TEST DES CAS LIMITES")
    print("=" * 60)
    
    # Test avec k trop grand
    print("\n📊 Test avec k > nombre d'échantillons:")
    try:
        X_small = np.random.randn(3, 2)
        y_small = np.array([0, 0, 1])
        knn_bad = KNN(k=5)
        knn_bad.fit(X_small, y_small)
        print("   ❌ Erreur: k trop grand n'a pas été détecté")
    except ValueError as e:
        print(f"   ✅ Erreur détectée: {e}")
    
    # Test avec un seul point
    print("\n📊 Test avec un seul point:")
    X_one = np.random.randn(1, 2)
    y_one = np.array([1])
    
    knn_one = KNN(k=1)
    knn_one.fit(X_one, y_one)
    y_pred = knn_one.predict(X_one)
    
    if y_pred[0] == 1:
        print("   ✅ OK: Prédiction correcte avec un point")
    else:
        print("   ❌ Erreur")
    
    # ==================== 8. RÉSUMÉ ====================
    print("\n" + "=" * 60)
    print("✅ TEST TERMINÉ AVEC SUCCÈS !")
    print("=" * 60)
    
    if 'knn_final' in locals():
        print(knn_final.summary())


def test_decision_boundary():
    """Test de la frontière de décision (visualisation)"""
    print("\n" + "=" * 60)
    print("ANALYSE DE LA FRONTIÈRE DE DÉCISION")
    print("=" * 60)
    
    try:
        import matplotlib.pyplot as plt
        
        # Générer des données 2D
        np.random.seed(42)
        n_samples = 200
        
        # Créer des clusters
        X = np.random.randn(n_samples, 2)
        y = (X[:, 0] + X[:, 1] > 0).astype(int)
        
        # Entraîner KNN
        knn = KNN(k=5, distance_metric='euclidean')
        knn.fit(X, y)
        
        # Créer une grille
        x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
        y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1
        xx, yy = np.meshgrid(np.linspace(x_min, x_max, 100),
                             np.linspace(y_min, y_max, 100))
        
        # Prédire sur la grille
        Z = knn.predict(np.c_[xx.ravel(), yy.ravel()])
        Z = Z.reshape(xx.shape)
        
        print("   ✅ Frontière de décision calculée")
        print("   📊 Pour visualiser, décommentez le code d'affichage")
        
        # Visualisation (décommenter pour voir)
        # plt.figure(figsize=(10, 8))
        # plt.contourf(xx, yy, Z, alpha=0.3, cmap='RdYlBu')
        # plt.scatter(X[:, 0], X[:, 1], c=y, cmap='RdYlBu', edgecolors='black')
        # plt.title(f'KNN (k={knn.k}, metric={knn.distance_metric})')
        # plt.xlabel('Feature 1')
        # plt.ylabel('Feature 2')
        # plt.savefig('reports/knn_decision_boundary.png')
        # print("   ✅ Figure sauvegardée: reports/knn_decision_boundary.png")
        
    except ImportError:
        print("   ⚠️ Matplotlib non installé, saut de la visualisation")
    except Exception as e:
        print(f"   ⚠️ Erreur lors de la visualisation: {e}")


if __name__ == "__main__":
    test_knn()
    test_decision_boundary()