"""
Script de test pour la Régression Logistique
AutoStockCheck - ECU Worldwide
"""

import sys
import os
import pandas as pd

# Ajouter le chemin src pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from src.models.logistic_regression import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def test_logistic_regression():
    """Test complet de la régression logistique"""
    
    print("=" * 60)
    print("TEST DE LA RÉGRESSION LOGISTIQUE")
    print("=" * 60)
    
    # ==================== 1. TEST SUR DONNÉES SYNTHÉTIQUES ====================
    print("\n📊 1. Test sur données synthétiques...")
    
    # Générer des données synthétiques
    np.random.seed(42)
    n_samples = 500
    
    # Créer une relation linéaire avec du bruit
    X = np.random.randn(n_samples, 2)
    y = (X[:, 0] + X[:, 1] + np.random.randn(n_samples) * 0.5 > 0).astype(int)
    
    # Diviser en train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    print(f"   Données d'entraînement: {X_train.shape}")
    print(f"   Données de test: {X_test.shape}")
    
    # Test avec différentes configurations
    print("\n🚀 Test avec différentes configurations...")
    
    # Batch Gradient Descent
    print("\n   Batch Gradient Descent:")
    lr = LogisticRegression(learning_rate=0.1, n_iterations=1000, 
                            regularization='l2', C=1.0, verbose=False)
    lr.fit(X_train, y_train)
    metrics = lr.evaluate(X_test, y_test)
    print(f"     Accuracy: {metrics['accuracy']:.4f}, F1: {metrics['f1_score']:.4f}")
    print(f"     Temps entraînement: {lr.training_time:.4f}s")
    
    # SGD avec minibatch
    print("\n   Stochastic Gradient Descent (batch_size=32):")
    lr_sgd = LogisticRegression(learning_rate=0.01, n_iterations=500,
                                 regularization='l2', C=1.0, batch_size=32, verbose=False)
    lr_sgd.fit(X_train, y_train)
    metrics_sgd = lr_sgd.evaluate(X_test, y_test)
    print(f"     Accuracy: {metrics_sgd['accuracy']:.4f}, F1: {metrics_sgd['f1_score']:.4f}")
    print(f"     Temps entraînement: {lr_sgd.training_time:.4f}s")
    
    # ==================== 2. TEST AVEC DIFFÉRENTES RÉGULARISATIONS ====================
    print("\n📊 2. Test avec différentes régularisations...")
    
    for reg in ['none', 'l1', 'l2']:
        lr_reg = LogisticRegression(learning_rate=0.1, n_iterations=500,
                                     regularization=reg, C=1.0, verbose=False)
        lr_reg.fit(X_train, y_train)
        metrics_reg = lr_reg.evaluate(X_test, y_test)
        print(f"   {reg}: Accuracy={metrics_reg['accuracy']:.4f}, F1={metrics_reg['f1_score']:.4f}")
    
    # ==================== 3. TEST AVEC LES DONNÉES RÉELLES ====================
    print("\n📊 3. Test avec les données du dataset AutoStockCheck...")
    
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
        
        # Normaliser les données (important pour la régression logistique)
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Entraîner
        print("\n🚀 Entraînement...")
        lr_real = LogisticRegression(learning_rate=0.1, n_iterations=1000,
                                      regularization='l2', C=1.0, verbose=True)
        lr_real.fit(X_train_scaled, y_train)
        
        print(f"\n   Temps d'entraînement: {lr_real.training_time:.4f} secondes")
        
        # Évaluer
        metrics_real = lr_real.evaluate(X_test_scaled, y_test)
        
        print(f"\n📈 Performances sur données réelles:")
        print(f"   Accuracy:  {metrics_real['accuracy']:.4f}")
        print(f"   Precision: {metrics_real['precision']:.4f}")
        print(f"   Recall:    {metrics_real['recall']:.4f}")
        print(f"   F1-Score:  {metrics_real['f1_score']:.4f}")
        
        # Afficher les coefficients
        coeff = lr_real.get_coefficients()
        print(f"\n📊 Coefficients du modèle:")
        for i, feat in enumerate(feature_cols):
            print(f"   {feat}: {coeff['weights'][i]:.4f}")
        print(f"   Bias (intercept): {coeff['bias']:.4f}")
        
        # ==================== 4. TEST DE SAUVEGARDE ====================
        print("\n💾 4. Test de sauvegarde et chargement...")
        
        lr_real.save("models_saved/logistic_regression.pkl")
        
        loaded_lr = LogisticRegression.load("models_saved/logistic_regression.pkl")
        
        y_pred_original = lr_real.predict(X_test_scaled)
        y_pred_loaded = loaded_lr.predict(X_test_scaled)
        
        if np.array_equal(y_pred_original, y_pred_loaded):
            print("   ✅ Sauvegarde et chargement OK")
        else:
            print("   ❌ Erreur: Les prédictions ne correspondent pas")
        
        # ==================== 5. COURBE DE PERTE ====================
        print("\n📈 5. Courbe de perte:")
        print(f"   Loss initiale: {lr_real.loss_history[0]:.6f}")
        print(f"   Loss finale: {lr_real.loss_history[-1]:.6f}")
        print(f"   Réduction: {lr_real.loss_history[0] - lr_real.loss_history[-1]:.6f}")
        
        # Sauvegarder la courbe de perte
        try:
            import matplotlib.pyplot as plt
            plt.figure(figsize=(10, 6))
            plt.plot(lr_real.loss_history)
            plt.title('Courbe de perte - Régression Logistique')
            plt.xlabel('Itération')
            plt.ylabel('Perte (Cross-Entropy)')
            plt.grid(True, alpha=0.3)
            plt.savefig('reports/logistic_regression_loss_curve.png')
            print("   ✅ Courbe de perte sauvegardée: reports/logistic_regression_loss_curve.png")
        except Exception as e:
            print(f"   ⚠️ Sauvegarde de la courbe impossible: {e}")
        
    else:
        print(f"   ❌ Dataset non trouvé: {dataset_path}")
        print("   Exécutez d'abord: python scripts/generate_synthetic_data.py")
    
    # ==================== 6. TEST DES CAS LIMITES ====================
    print("\n" + "=" * 60)
    print("TEST DES CAS LIMITES")
    print("=" * 60)
    
    # Test avec des données parfaitement séparables
    print("\n📊 Test avec données parfaitement séparables:")
    X_perfect = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
    y_perfect = np.array([0, 0, 1, 1])
    
    lr_perfect = LogisticRegression(learning_rate=0.1, n_iterations=500, C=10.0)
    lr_perfect.fit(X_perfect, y_perfect)
    y_pred_perfect = lr_perfect.predict(X_perfect)
    
    if np.array_equal(y_pred_perfect, y_perfect):
        print("   ✅ OK: Classification parfaite")
    else:
        print(f"   ⚠️ Prédictions: {y_pred_perfect}, Attendu: {y_perfect}")
    
    # Test avec des données déséquilibrées
    print("\n📊 Test avec données déséquilibrées (90% classe 0):")
    X_imbalanced = np.random.randn(500, 2)
    y_imbalanced = np.zeros(500)
    y_imbalanced[:50] = 1  # 10% de classe 1
    
    X_train_imb, X_test_imb, y_train_imb, y_test_imb = train_test_split(
        X_imbalanced, y_imbalanced, test_size=0.2, random_state=42
    )
    
    lr_imb = LogisticRegression(learning_rate=0.1, n_iterations=500, C=1.0)
    lr_imb.fit(X_train_imb, y_train_imb)
    metrics_imb = lr_imb.evaluate(X_test_imb, y_test_imb)
    
    print(f"   Accuracy: {metrics_imb['accuracy']:.4f}")
    print(f"   Precision: {metrics_imb['precision']:.4f}")
    print(f"   Recall: {metrics_imb['recall']:.4f}")
    print(f"   F1-Score: {metrics_imb['f1_score']:.4f}")
    
    # ==================== 7. RÉSUMÉ ====================
    print("\n" + "=" * 60)
    print("✅ TEST TERMINÉ AVEC SUCCÈS !")
    print("=" * 60)
    
    if 'lr_real' in locals():
        print(lr_real.summary())


def test_decision_boundary():
    """Test de la frontière de décision (visualisation)"""
    print("\n" + "=" * 60)
    print("ANALYSE DE LA FRONTIÈRE DE DÉCISION")
    print("=" * 60)
    
    try:
        import matplotlib.pyplot as plt
        
        # Générer des données 2D
        np.random.seed(42)
        X = np.random.randn(300, 2)
        y = (X[:, 0] + X[:, 1] > 0).astype(int)
        
        # Entraîner
        lr = LogisticRegression(learning_rate=0.1, n_iterations=500)
        lr.fit(X, y)
        
        # Créer une grille
        x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
        y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1
        xx, yy = np.meshgrid(np.linspace(x_min, x_max, 100),
                             np.linspace(y_min, y_max, 100))
        
        # Prédire sur la grille
        Z = lr.predict(np.c_[xx.ravel(), yy.ravel()])
        Z = Z.reshape(xx.shape)
        
        print("   ✅ Frontière de décision calculée")
        
        # Visualisation
        plt.figure(figsize=(10, 8))
        plt.contourf(xx, yy, Z, alpha=0.3, cmap='RdYlBu')
        plt.scatter(X[:, 0], X[:, 1], c=y, cmap='RdYlBu', edgecolors='black')
        plt.title('Régression Logistique - Frontière de décision')
        plt.xlabel('Feature 1')
        plt.ylabel('Feature 2')
        plt.savefig('reports/logistic_regression_decision_boundary.png')
        print("   ✅ Figure sauvegardée: reports/logistic_regression_decision_boundary.png")
        
    except ImportError:
        print("   ⚠️ Matplotlib non installé, saut de la visualisation")
    except Exception as e:
        print(f"   ⚠️ Erreur lors de la visualisation: {e}")


if __name__ == "__main__":
    test_logistic_regression()
    test_decision_boundary()