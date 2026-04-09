"""
Script de test pour le Neural Network
AutoStockCheck - ECU Worldwide
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from src.models.neural_network import NeuralNetwork
from src.models.decision_tree import DecisionTree

print("=" * 70)
print("TEST DU RÉSEAU DE NEURONES (DEEP LEARNING)")
print("=" * 70)

# Charger les données
dataset_path = "data/datasets/dataset_entrainement.csv"
if not os.path.exists(dataset_path):
    print(f"❌ Dataset non trouvé: {dataset_path}")
    sys.exit(1)

df = pd.read_csv(dataset_path)
print(f"\n📂 Dataset chargé: {len(df)} lignes")

# Features
feature_cols = ['diff_quantite', 'produit_absent', 'quantite_insuffisante', 'prix']
X = df[feature_cols].values
y = df['label'].values

print(f"   Features: {feature_cols}")
print(f"   Distribution: Classe 0={np.sum(y==0)}, Classe 1={np.sum(y==1)}")

# Division
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Normalisation
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print(f"\n📊 Division:")
print(f"   Train: {len(X_train)} (Classe 0={np.sum(y_train==0)}, Classe 1={np.sum(y_train==1)})")
print(f"   Test: {len(X_test)} (Classe 0={np.sum(y_test==0)}, Classe 1={np.sum(y_test==1)})")

# ==================== TEST DU NEURAL NETWORK ====================
print("\n" + "=" * 70)
print("🚀 ENTRAÎNEMENT DU RÉSEAU DE NEURONES")
print("=" * 70)

# Différentes architectures
architectures = [
    {'name': 'Petit réseau', 'layers': [16, 8], 'iterations': 300},
    {'name': 'Moyen réseau', 'layers': [32, 16, 8], 'iterations': 500},
    {'name': 'Grand réseau', 'layers': [64, 32, 16, 8], 'iterations': 500},
]

results = []

for arch in architectures:
    print(f"\n📈 {arch['name']} - Couches: {arch['layers']}")
    print("-" * 50)
    
    nn = NeuralNetwork(
        hidden_layers=arch['layers'],
        activation='relu',
        learning_rate=0.001,
        n_iterations=arch['iterations'],
        batch_size=32,
        verbose=True
    )
    
    nn.fit(X_train_scaled, y_train)
    
    y_pred = nn.predict(X_test_scaled)
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    
    results.append({
        'Modèle': arch['name'],
        'Accuracy': acc,
        'Precision': prec,
        'Recall': rec,
        'F1-Score': f1,
        'Train Time': nn.training_time,
        'Predict Time': nn.prediction_time
    })
    
    print(f"\n   ✅ Accuracy:  {acc:.4f}")
    print(f"   ✅ Precision: {prec:.4f}")
    print(f"   ✅ Recall:    {rec:.4f}")
    print(f"   ✅ F1-Score:  {f1:.4f}")
    print(f"   ⏱️  Train: {nn.training_time:.4f}s, Predict: {nn.prediction_time:.4f}s")

# ==================== COMPARAISON AVEC DECISION TREE ====================
print("\n" + "=" * 70)
print("📊 COMPARAISON AVEC DECISION TREE")
print("=" * 70)

dt = DecisionTree(max_depth=7, min_samples_split=5, min_samples_leaf=2, criterion='gini')
dt.fit(X_train_scaled, y_train)
y_pred_dt = dt.predict(X_test_scaled)

print(f"\nDecision Tree:")
print(f"   Accuracy:  {accuracy_score(y_test, y_pred_dt):.4f}")
print(f"   Precision: {precision_score(y_test, y_pred_dt, zero_division=0):.4f}")
print(f"   Recall:    {recall_score(y_test, y_pred_dt, zero_division=0):.4f}")
print(f"   F1-Score:  {f1_score(y_test, y_pred_dt, zero_division=0):.4f}")

# ==================== MEILLEUR MODÈLE ====================
print("\n" + "=" * 70)
print("🏆 MEILLEUR MODÈLE")
print("=" * 70)

best = max(results, key=lambda x: x['F1-Score'])
print(f"\nMeilleur réseau: {best['Modèle']}")
print(f"   F1-Score: {best['F1-Score']:.4f}")
print(f"   Temps entraînement: {best['Train Time']:.4f}s")
print(f"   Temps prédiction: {best['Predict Time']:.4f}s")

# ==================== VISUALISATION ====================
print("\n📈 Génération de la courbe de perte...")

# Entraîner le meilleur réseau pour la courbe
best_nn = NeuralNetwork(
    hidden_layers=[32, 16, 8],
    activation='relu',
    learning_rate=0.001,
    n_iterations=300,
    batch_size=32,
    verbose=False
)
best_nn.fit(X_train_scaled, y_train)

plt.figure(figsize=(10, 6))
plt.plot(best_nn.loss_history)
plt.title('Courbe de perte - Réseau de Neurones')
plt.xlabel('Époque')
plt.ylabel('Perte (Cross-Entropy)')
plt.grid(True, alpha=0.3)
plt.savefig('reports/neural_network_loss_curve.png')
print("   ✅ Courbe sauvegardée: reports/neural_network_loss_curve.png")

# ==================== RÉSUMÉ ====================
print("\n" + "=" * 70)
print("✅ TEST TERMINÉ AVEC SUCCÈS !")
print("=" * 70)

results_df = pd.DataFrame(results)
print("\n" + results_df.to_string(index=False))