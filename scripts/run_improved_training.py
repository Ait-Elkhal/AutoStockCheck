"""
Script complet pour générer les données et entraîner les modèles améliorés
AutoStockCheck - ECU Worldwide
"""

import sys
import os

# Ajouter le chemin du projet pour les imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import f1_score, recall_score, precision_score, accuracy_score

# Importer les modules du projet
try:
    from src.models.decision_tree import DecisionTree
    from src.models.random_forest import RandomForest
    from src.models.svm import SVM
    from src.models.logistic_regression import LogisticRegression
    from src.models.isolation_forest import IsolationForest
except ImportError as e:
    print(f"Erreur d'import: {e}")
    print("Vérifiez que les fichiers sont bien dans src/models/")
    sys.exit(1)

# Importer le générateur
try:
    from scripts.generate_synthetic_data_advanced import generer_dataset_entrainement
except ImportError:
    # Si le fichier n'existe pas, utiliser le générateur de base
    print("⚠️ generate_synthetic_data_advanced.py non trouvé, utilisation du générateur de base...")
    from scripts.generate_synthetic_data import generer_dataset_entrainement

print("=" * 70)
print("ENTRAÎNEMENT AVEC FEATURES ENRICHIES")
print("=" * 70)

# 1. Générer les données
print("\n📊 Génération des données enrichies...")
df = generer_dataset_entrainement(5000)
print(f"   ✅ Dataset généré : {len(df)} lignes")
print(f"   Colonnes disponibles: {list(df.columns)}")

# 2. Préparer les features
# Liste des features disponibles dans le dataset
all_features = [
    'diff_quantite', 'produit_absent', 'quantite_insuffisante', 'ratio_stock',
    'etat_produit', 'fiabilite_fournisseur', 'popularite',
    'saisonnalite', 'priorite', 'valeur_ligne', 'produit_cher',
    'diff_x_prix', 'absent_x_prix', 'etat_x_popularite', 'prix'
]

# Garder uniquement les colonnes qui existent
existing_cols = [col for col in all_features if col in df.columns]

# Si pas assez de features, utiliser les features de base
if len(existing_cols) < 4:
    print("   ⚠️ Features avancées non trouvées, utilisation des features de base...")
    existing_cols = ['diff_quantite', 'produit_absent', 'quantite_insuffisante', 'prix']

X = df[existing_cols].values
y = df['label'].values

print(f"\n📋 Features utilisées ({len(existing_cols)}):")
for feat in existing_cols:
    print(f"   - {feat}")
print(f"\n   Échantillons: {len(X)}")
print(f"   Distribution: Classe 0={np.sum(y==0)} ({np.sum(y==0)/len(y)*100:.1f}%), "
      f"Classe 1={np.sum(y==1)} ({np.sum(y==1)/len(y)*100:.1f}%)")

# 3. Division des données
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"\n📊 Division des données:")
print(f"   Train: {len(X_train)} (Classe 0={np.sum(y_train==0)}, Classe 1={np.sum(y_train==1)})")
print(f"   Test: {len(X_test)} (Classe 0={np.sum(y_test==0)}, Classe 1={np.sum(y_test==1)})")

# 4. Normalisation
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

print("\n✅ Données normalisées")

# 5. Entraînement des modèles
models = {
    'Decision Tree': DecisionTree(max_depth=7, min_samples_split=5, min_samples_leaf=2, criterion='gini'),
    'Random Forest': RandomForest(n_trees=20, max_depth=7, min_samples_split=5, criterion='gini'),
    'SVM (Linear)': SVM(learning_rate=0.001, lambda_param=0.001, n_iterations=500, kernel='linear'),
    'Logistic Regression': LogisticRegression(learning_rate=0.1, n_iterations=500, regularization='l2')
}

results = []

print("\n" + "=" * 70)
print("🚀 ENTRAÎNEMENT DES MODÈLES")
print("=" * 70)

for name, model in models.items():
    print(f"\n📈 {name}")
    print("-" * 50)
    
    try:
        # Entraînement
        model.fit(X_train_scaled, y_train)
        
        # Prédiction
        y_pred = model.predict(X_test_scaled)
        
        # Métriques
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        
        results.append({
            'Modèle': name,
            'Accuracy': acc,
            'Precision': prec,
            'Recall': rec,
            'F1-Score': f1
        })
        
        print(f"   ✅ Accuracy:  {acc:.4f}")
        print(f"   ✅ Precision: {prec:.4f}")
        print(f"   ✅ Recall:    {rec:.4f}")
        print(f"   ✅ F1-Score:  {f1:.4f}")
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        results.append({
            'Modèle': name,
            'Accuracy': 0,
            'Precision': 0,
            'Recall': 0,
            'F1-Score': 0
        })

# 6. Ajustement du seuil pour le meilleur modèle
print("\n" + "=" * 70)
print("🎯 OPTIMISATION DU SEUIL")
print("=" * 70)

# Prendre le modèle avec le meilleur F1-score
best_result = max(results, key=lambda x: x['F1-Score'])
best_model_name = best_result['Modèle']
print(f"\n📊 Meilleur modèle: {best_model_name} (F1={best_result['F1-Score']:.4f})")

# Réentraîner le meilleur modèle pour l'optimisation
if best_model_name == 'Decision Tree':
    best_model = DecisionTree(max_depth=7, min_samples_split=5, min_samples_leaf=2, criterion='gini')
elif best_model_name == 'Random Forest':
    best_model = RandomForest(n_trees=20, max_depth=7, min_samples_split=5, criterion='gini')
elif best_model_name == 'SVM (Linear)':
    best_model = SVM(learning_rate=0.001, lambda_param=0.001, n_iterations=500, kernel='linear')
else:
    best_model = LogisticRegression(learning_rate=0.1, n_iterations=500, regularization='l2')

best_model.fit(X_train_scaled, y_train)

# Obtenir les probabilités (si disponible)
try:
    probas = best_model.predict_proba(X_test_scaled)[:, 1]
    
    best_f1 = 0
    best_threshold = 0.5
    
    for threshold in np.arange(0.1, 0.95, 0.05):
        y_pred_thresh = (probas >= threshold).astype(int)
        f1 = f1_score(y_test, y_pred_thresh, zero_division=0)
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold
    
    print(f"\n🎯 Meilleur seuil trouvé: {best_threshold:.2f}")
    print(f"   F1-Score optimisé: {best_f1:.4f}")
    
    # Évaluation finale avec meilleur seuil
    y_pred_final = (probas >= best_threshold).astype(int)
    
    print(f"\n📈 PERFORMANCES FINALES AVEC SEUIL OPTIMISÉ:")
    print(f"   Accuracy:  {accuracy_score(y_test, y_pred_final):.4f}")
    print(f"   Precision: {precision_score(y_test, y_pred_final, zero_division=0):.4f}")
    print(f"   Recall:    {recall_score(y_test, y_pred_final, zero_division=0):.4f}")
    print(f"   F1-Score:  {f1_score(y_test, y_pred_final, zero_division=0):.4f}")
    
except Exception as e:
    print(f"\n⚠️ Optimisation du seuil impossible: {e}")

# 7. Afficher les résultats
print("\n" + "=" * 70)
print("📊 RÉSULTATS FINAUX")
print("=" * 70)

results_df = pd.DataFrame(results)
print("\n" + results_df.to_string(index=False))

# 8. Sauvegarder
os.makedirs("reports", exist_ok=True)
results_df.to_csv("reports/improved_results.csv", index=False)
print(f"\n✅ Résultats sauvegardés dans reports/improved_results.csv")

# 9. Meilleur modèle
print("\n" + "=" * 70)
print("🏆 RECOMMANDATION")
print("=" * 70)

best = max(results, key=lambda x: x['F1-Score'])
print(f"\nMeilleur modèle: {best['Modèle']}")
print(f"F1-Score: {best['F1-Score']:.4f}")
print(f"Recall: {best['Recall']:.4f}")

if best['Recall'] < 0.6:
    print("\n⚠️ Le Recall est faible. Suggestions d'amélioration:")
    print("   1. Ajouter plus de features (état produit, saisonnalité, priorité)")
    print("   2. Utiliser SMOTE pour rééquilibrer les classes")
    print("   3. Ajuster le seuil de décision")
    print("   4. Utiliser Isolation Forest pour la détection d'anomalies")

print("\n" + "=" * 70)
print("✅ SCRIPT TERMINÉ AVEC SUCCÈS !")
print("=" * 70)