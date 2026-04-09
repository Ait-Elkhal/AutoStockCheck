"""
Script de test pour le SVM
AutoStockCheck - ECU Worldwide
"""

import sys
import os
import pandas as pd

# Ajouter le chemin src pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from src.models.svm import SVM
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def test_svm():
    """Test complet du SVM"""
    
    print("=" * 60)
    print("TEST DU SUPPORT VECTOR MACHINE (SVM)")
    print("=" * 60)
    
    # ==================== 1. TEST SUR DONNÉES SYNTHÉTIQUES ====================
    print("\n📊 1. Test sur données synthétiques...")
    
    # Générer des données synthétiques
    np.random.seed(42)
    n_samples = 500
    
    # Créer des données linéairement séparables
    X1 = np.random.randn(n_samples // 2, 2) + [2, 2]
    X2 = np.random.randn(n_samples // 2, 2) + [-2, -2]
    X = np.vstack([X1, X2])
    y = np.hstack([np.ones(n_samples // 2), np.zeros(n_samples // 2)])
    
    # Diviser en train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"   Données d'entraînement: {X_train.shape}")
    print(f"   Données de test: {X_test.shape}")
    
    # Test avec différentes configurations
    print("\n🚀 Test avec différents noyaux...")
    
    for kernel in ['linear', 'rbf', 'poly']:
        print(f"\n   Noyau {kernel}:")
        svm = SVM(learning_rate=0.001, lambda_param=0.01, n_iterations=500,
                  kernel=kernel, degree=2, verbose=False)
        svm.fit(X_train, y_train)
        metrics = svm.evaluate(X_test, y_test)
        print(f"     Accuracy: {metrics['accuracy']:.4f}, F1: {metrics['f1_score']:.4f}")
        print(f"     Temps entraînement: {svm.training_time:.4f}s")
    
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
        
        # Diviser
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print(f"   Données d'entraînement: {X_train.shape}")
        print(f"   Données de test: {X_test.shape}")
        
        # Normaliser les données (important pour SVM)
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Entraîner avec noyau linéaire
        print("\n🚀 Entraînement avec noyau linéaire...")
        svm_linear = SVM(learning_rate=0.001, lambda_param=0.01, n_iterations=500,
                         kernel='linear', verbose=False)
        svm_linear.fit(X_train_scaled, y_train)
        
        metrics_linear = svm_linear.evaluate(X_test_scaled, y_test)
        
        print(f"\n📈 Performances (noyau linéaire):")
        print(f"   Accuracy:  {metrics_linear['accuracy']:.4f}")
        print(f"   Precision: {metrics_linear['precision']:.4f}")
        print(f"   Recall:    {metrics_linear['recall']:.4f}")
        print(f"   F1-Score:  {metrics_linear['f1_score']:.4f}")
        
        # Afficher les poids (noyau linéaire)
        try:
            weights = svm_linear.get_weights()
            bias = svm_linear.get_bias()
            print(f"\n📊 Poids du modèle:")
            for i, feat in enumerate(feature_cols):
                print(f"   {feat}: {weights[i]:.4f}")
            print(f"   Bias: {bias:.4f}")
        except:
            pass
        
        # Entraîner avec noyau RBF
        print("\n🚀 Entraînement avec noyau RBF...")
        svm_rbf = SVM(learning_rate=0.001, lambda_param=0.01, n_iterations=500,
                      kernel='rbf', gamma=0.1, verbose=False)
        svm_rbf.fit(X_train_scaled, y_train)
        
        metrics_rbf = svm_rbf.evaluate(X_test_scaled, y_test)
        
        print(f"\n📈 Performances (noyau RBF):")
        print(f"   Accuracy:  {metrics_rbf['accuracy']:.4f}")
        print(f"   Precision: {metrics_rbf['precision']:.4f}")
        print(f"   Recall:    {metrics_rbf['recall']:.4f}")
        print(f"   F1-Score:  {metrics_rbf['f1_score']:.4f}")
        
        # Afficher les vecteurs supports
        support_vectors = svm_rbf.get_support_vectors()
        if support_vectors is not None:
            print(f"\n   Nombre de vecteurs supports: {len(support_vectors)}")
        
        # ==================== 3. TEST DE SAUVEGARDE ====================
        print("\n💾 3. Test de sauvegarde et chargement...")
        
        svm_rbf.save("models_saved/svm.pkl")
        
        loaded_svm = SVM.load("models_saved/svm.pkl")
        
        y_pred_original = svm_rbf.predict(X_test_scaled)
        y_pred_loaded = loaded_svm.predict(X_test_scaled)
        
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
    
    # Test avec des données parfaitement séparables
    print("\n📊 Test avec données parfaitement séparables:")
    X_perfect = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
    y_perfect = np.array([0, 0, 1, 1])
    
    svm_perfect = SVM(learning_rate=0.001, lambda_param=0.001, n_iterations=500,
                      kernel='linear')
    svm_perfect.fit(X_perfect, y_perfect)
    y_pred_perfect = svm_perfect.predict(X_perfect)
    
    if np.array_equal(y_pred_perfect, y_perfect):
        print("   ✅ OK: Classification parfaite")
    else:
        print(f"   ⚠️ Prédictions: {y_pred_perfect}, Attendu: {y_perfect}")
    
    # ==================== 5. RÉSUMÉ ====================
    print("\n" + "=" * 60)
    print("✅ TEST TERMINÉ AVEC SUCCÈS !")
    print("=" * 60)
    
    if 'svm_rbf' in locals():
        print(svm_rbf.summary())


if __name__ == "__main__":
    test_svm()