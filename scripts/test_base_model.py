"""
Script de test pour la BaseModel
AutoStockCheck - ECU Worldwide
"""

import sys
import os

# Ajouter le chemin src pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from src.models.base_model import BaseModel


# Créer une classe de test qui hérite de BaseModel
class TestModel(BaseModel):
    """Modèle de test pour vérifier l'implémentation"""
    
    def __init__(self):
        super().__init__(name="TestModel")
        self.weights = None
    
    def fit(self, X, y):
        """Simule l'entraînement"""
        start_time = __import__('time').time()
        
        # Simuler un entraînement simple
        self.weights = np.random.randn(X.shape[1])
        self.is_trained = True
        
        self.training_time = __import__('time').time() - start_time
        return self
    
    def predict(self, X):
        """Prédit selon un seuil"""
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné")
        
        scores = np.dot(X, self.weights)
        return (scores > 0).astype(int)
    
    def predict_proba(self, X):
        """Retourne des probabilités simulées"""
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné")
        
        scores = np.dot(X, self.weights)
        proba = 1 / (1 + np.exp(-scores))
        return np.column_stack([1 - proba, proba])


# ==================== TEST ====================

print("=" * 50)
print("TEST DE LA BASE MODEL")
print("=" * 50)

# 1. Créer des données de test
print("\n📊 Création des données de test...")
np.random.seed(42)
X_train = np.random.randn(100, 5)
y_train = (X_train[:, 0] + X_train[:, 1] > 0).astype(int)

X_test = np.random.randn(30, 5)
y_test = (X_test[:, 0] + X_test[:, 1] > 0).astype(int)

print(f"   Données d'entraînement : {X_train.shape}")
print(f"   Données de test : {X_test.shape}")

# 2. Créer et entraîner le modèle
print("\n🚀 Entraînement du modèle...")
model = TestModel()
model.fit(X_train, y_train)

# 3. Évaluer le modèle
print("\n📈 Évaluation du modèle...")
metrics = model.evaluate(X_test, y_test)

# 4. Afficher le résumé
print(model.summary())

# 5. Tester la sauvegarde
print("\n💾 Test de sauvegarde...")
model.save("models_saved/test_model.pkl")

# 6. Tester le chargement
print("\n📂 Test de chargement...")
loaded_model = BaseModel.load("models_saved/test_model.pkl")
print(loaded_model.summary())

print("\n✅ Tous les tests sont passés avec succès !")