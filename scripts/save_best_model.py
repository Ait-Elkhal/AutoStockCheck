"""
Sauvegarde du meilleur modèle (SVM) pour production
AutoStockCheck - ECU Worldwide
"""

import sys
import os
import pickle
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.models.svm import SVM

print("=" * 60)
print("SAUVEGARDE DU MODÈLE FINAL")
print("=" * 60)

# 1. Charger les données
print("\n📂 Chargement des données...")
df = pd.read_csv("data/datasets/dataset_entrainement.csv")

# Features utilisées
feature_cols = [
    'diff_quantite', 'produit_absent', 'quantite_insuffisante', 
    'ratio_stock', 'etat_produit', 'fiabilite_fournisseur', 
    'popularite', 'saisonnalite', 'prix', 'valeur_ligne',
    'produit_cher', 'diff_x_prix', 'absent_x_prix', 'etat_x_popularite'
]

# Garder les colonnes existantes
existing_cols = [col for col in feature_cols if col in df.columns]
X = df[existing_cols].values
y = df['label'].values

print(f"   Features: {len(existing_cols)}")
print(f"   Échantillons: {len(X)}")
print(f"   Distribution: {np.bincount(y)}")

# 2. Division et normalisation
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)

# 3. Entraînement du modèle final (SVM)
print("\n🚀 Entraînement du modèle final...")

best_model = SVM(
    learning_rate=0.001,
    lambda_param=0.001,
    n_iterations=500,
    kernel='linear'
)

best_model.fit(X_train_scaled, y_train)

print(f"   ✅ Modèle entraîné en {best_model.training_time:.4f}s")

# 4. Sauvegarde - Extraire les paramètres importants
print("\n💾 Sauvegarde...")

# Créer le dossier models_saved
os.makedirs("models_saved", exist_ok=True)

# Sauvegarder les paramètres du modèle (au lieu du modèle complet)
model_params = {
    'weights': best_model.weights,
    'bias': best_model.bias,
    'kernel': best_model.kernel,
    'lambda_param': best_model.lambda_param,
    'learning_rate': best_model.learning_rate,
    'features': existing_cols
}

with open("models_saved/best_model_params.pkl", "wb") as f:
    pickle.dump(model_params, f)
print("   ✅ Paramètres du modèle sauvegardés: models_saved/best_model_params.pkl")

# Sauvegarder le scaler
with open("models_saved/scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)
print("   ✅ Scaler sauvegardé: models_saved/scaler.pkl")

# Sauvegarder les features
with open("models_saved/features.pkl", "wb") as f:
    pickle.dump(existing_cols, f)
print("   ✅ Features sauvegardées: models_saved/features.pkl")

# 5. Test de chargement
print("\n📂 Test de chargement...")

with open("models_saved/best_model_params.pkl", "rb") as f:
    loaded_params = pickle.load(f)

print("   ✅ Paramètres chargés avec succès")

print("\n" + "=" * 60)
print("✅ MODÈLE FINAL SAUVEGARDÉ AVEC SUCCÈS !")
print("=" * 60)