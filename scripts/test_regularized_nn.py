"""
Test comparatif : Réseau simple vs Réseau régularisé
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
from src.models.neural_network_regularized import RegularizedNeuralNetwork

print("=" * 70)
print("COMPARAISON : RÉSEAU SIMPLE vs RÉSEAU RÉGULARISÉ")
print("=" * 70)

# Charger les données
df = pd.read_csv("data/datasets/dataset_entrainement.csv")
feature_cols = ['diff_quantite', 'produit_absent', 'quantite_insuffisante', 'prix']
X = df[feature_cols].values
y = df['label'].values

# Division
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
X_train, X_val, y_train, y_val = train_test_split(X_train, y_train, test_size=0.2, random_state=42, stratify=y_train)

# Normalisation
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

print(f"\n📊 Données:")
print(f"   Train: {len(X_train)}")
print(f"   Validation: {len(X_val)}")
print(f"   Test: {len(X_test)}")

# ==================== 1. RÉSEAU SIMPLE (SANS RÉGULARISATION) ====================
print("\n" + "=" * 70)
print("1. RÉSEAU SIMPLE (sans régularisation)")
print("=" * 70)

simple_nn = NeuralNetwork(
    hidden_layers=[32, 16, 8],
    activation='relu',
    learning_rate=0.001,
    n_iterations=300,
    batch_size=32,
    verbose=True
)
simple_nn.fit(X_train_scaled, y_train)

y_pred_simple = simple_nn.predict(X_test_scaled)
y_pred_train_simple = simple_nn.predict(X_train_scaled)

print(f"\n📈 Résultats:")
print(f"   Train Accuracy: {accuracy_score(y_train, y_pred_train_simple):.4f}")
print(f"   Test Accuracy:  {accuracy_score(y_test, y_pred_simple):.4f}")
print(f"   Écart (Train-Test): {accuracy_score(y_train, y_pred_train_simple) - accuracy_score(y_test, y_pred_simple):.4f}")

# ==================== 2. RÉSEAU RÉGULARISÉ ====================
print("\n" + "=" * 70)
print("2. RÉSEAU RÉGULARISÉ (L2 + Dropout)")
print("=" * 70)

reg_nn = RegularizedNeuralNetwork(
    hidden_layers=[16, 8],  # Moins de neurones
    activation='relu',
    learning_rate=0.01,
    n_iterations=200,
    batch_size=64,
    dropout_rate=0.3,
    lambda_reg=0.01,
    verbose=True
)
reg_nn.fit(X_train_scaled, y_train, X_val_scaled, y_val)

y_pred_reg = reg_nn.predict(X_test_scaled)
y_pred_train_reg = reg_nn.predict(X_train_scaled)

print(f"\n📈 Résultats:")
print(f"   Train Accuracy: {accuracy_score(y_train, y_pred_train_reg):.4f}")
print(f"   Test Accuracy:  {accuracy_score(y_test, y_pred_reg):.4f}")
print(f"   Écart (Train-Test): {accuracy_score(y_train, y_pred_train_reg) - accuracy_score(y_test, y_pred_reg):.4f}")

# ==================== 3. COMPARAISON ====================
print("\n" + "=" * 70)
print("📊 COMPARAISON FINALE")
print("=" * 70)

results = pd.DataFrame([
    {
        'Modèle': 'Réseau Simple',
        'Train Acc': accuracy_score(y_train, y_pred_train_simple),
        'Test Acc': accuracy_score(y_test, y_pred_simple),
        'Écart': accuracy_score(y_train, y_pred_train_simple) - accuracy_score(y_test, y_pred_simple),
        'F1-Score': f1_score(y_test, y_pred_simple),
        'Temps Train': simple_nn.training_time
    },
    {
        'Modèle': 'Réseau Régularisé',
        'Train Acc': accuracy_score(y_train, y_pred_train_reg),
        'Test Acc': accuracy_score(y_test, y_pred_reg),
        'Écart': accuracy_score(y_train, y_pred_train_reg) - accuracy_score(y_test, y_pred_reg),
        'F1-Score': f1_score(y_test, y_pred_reg),
        'Temps Train': reg_nn.training_time
    }
])

print("\n" + results.to_string(index=False))

# ==================== 4. COURBES DE PERTE ====================
print("\n📈 Génération des courbes de perte...")

fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Courbe du réseau simple
axes[0].plot(simple_nn.loss_history)
axes[0].set_title('Réseau Simple - Perte')
axes[0].set_xlabel('Époque')
axes[0].set_ylabel('Perte')
axes[0].grid(True, alpha=0.3)

# Courbe du réseau régularisé
losses = reg_nn.get_loss_history()
axes[1].plot(losses['train'], label='Train')
if losses['val']:
    axes[1].plot(np.linspace(0, len(losses['train'])-1, len(losses['val'])), 
                 losses['val'], label='Validation')
axes[1].set_title('Réseau Régularisé - Perte')
axes[1].set_xlabel('Époque')
axes[1].set_ylabel('Perte')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('reports/nn_comparison_loss.png')
print("   ✅ Sauvegardé: reports/nn_comparison_loss.png")

print("\n" + "=" * 70)
print("✅ TEST TERMINÉ")
print("=" * 70)

# Recommandation
print("\n💡 RECOMMANDATION:")
if results.iloc[1]['Écart'] < results.iloc[0]['Écart']:
    print("   ✅ Le réseau régularisé généralise mieux (écart plus faible)")
else:
    print("   ⚠️ Le réseau simple a un écart plus important, risque d'overfitting")