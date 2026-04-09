"""
Benchmark Runner - Comparaison des modèles ML
AutoStockCheck - ECU Worldwide
"""

import sys
import os
import time
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Ajouter le chemin src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.decision_tree import DecisionTree
from models.knn import KNN
from models.logistic_regression import LogisticRegression
from models.svm import SVM
from models.isolation_forest import IsolationForest
from models.random_forest import RandomForest


class BenchmarkRunner:
    """
    Classe pour exécuter et comparer les modèles ML
    """
    
    def __init__(self, test_size: float = 0.2, random_state: int = 42):
        """
        Initialisation du benchmark
        
        Args:
            test_size: Proportion des données de test
            random_state: Graine aléatoire
        """
        self.test_size = test_size
        self.random_state = random_state
        self.results = []
        self.models = {}
        self.scaler = StandardScaler()
    
    def load_data(self, filepath: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Charge les données depuis un fichier CSV
        
        Args:
            filepath: Chemin du fichier CSV
            
        Returns:
            Tuple (X, y)
        """
        df = pd.read_csv(filepath)
        
        # Sélectionner les features
        feature_cols = ['diff_quantite', 'produit_absent', 'quantite_insuffisante', 'prix']
        X = df[feature_cols].values
        y = df['label'].values
        
        return X, y
    
    def prepare_models(self) -> Dict[str, Any]:
        """
        Prépare tous les modèles à tester
        
        Returns:
            Dictionnaire des modèles
        """
        models = {
            'Decision Tree': DecisionTree(max_depth=5, criterion='entropy'),
            'KNN': KNN(k=5, distance_metric='euclidean'),
            'Logistic Regression': LogisticRegression(learning_rate=0.1, n_iterations=500),
            'SVM': SVM(learning_rate=0.001, lambda_param=0.01, n_iterations=500, kernel='linear'),
            'Isolation Forest': IsolationForest(n_trees=100, contamination=0.2, random_state=42),
            'Random Forest': RandomForest(n_trees=20, max_depth=5, criterion='entropy')
        }
        
        return models
    
    def run_benchmark(self, X: np.ndarray, y: np.ndarray) -> pd.DataFrame:
        """
        Exécute le benchmark complet
        
        Args:
            X: Features
            y: Labels
            
        Returns:
            DataFrame des résultats
        """
        print("=" * 60)
        print("BENCHMARK DES MODÈLES ML")
        print("=" * 60)
        
        # Diviser les données
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.test_size, random_state=self.random_state
        )
        
        print(f"\n📊 Taille du dataset:")
        print(f"   Total: {len(X)} échantillons")
        print(f"   Train: {len(X_train)}")
        print(f"   Test: {len(X_test)}")
        print(f"   Distribution: {np.bincount(y)}")
        
        # Normaliser les données
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Préparer les modèles
        models = self.prepare_models()
        
        results = []
        
        for name, model in models.items():
            print(f"\n🚀 Test du modèle: {name}")
            
            try:
                # Entraînement
                start_time = time.time()
                model.fit(X_train_scaled, y_train)
                train_time = time.time() - start_time
                
                # Prédiction
                start_time = time.time()
                y_pred = model.predict(X_test_scaled)
                predict_time = time.time() - start_time
                
                # Évaluation
                from models.base_model import BaseModel
                if isinstance(model, BaseModel):
                    metrics = model.evaluate(X_test_scaled, y_test)
                else:
                    metrics = self._calculate_metrics(y_test, y_pred)
                
                results.append({
                    'modèle': name,
                    'accuracy': metrics['accuracy'],
                    'precision': metrics['precision'],
                    'recall': metrics['recall'],
                    'f1_score': metrics['f1_score'],
                    'train_time': train_time,
                    'predict_time': predict_time,
                    'status': 'OK'
                })
                
                print(f"   ✅ Accuracy: {metrics['accuracy']:.4f}")
                print(f"   ✅ F1-Score: {metrics['f1_score']:.4f}")
                print(f"   ⏱️  Train: {train_time:.4f}s, Predict: {predict_time:.4f}s")
                
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                results.append({
                    'modèle': name,
                    'accuracy': 0,
                    'precision': 0,
                    'recall': 0,
                    'f1_score': 0,
                    'train_time': 0,
                    'predict_time': 0,
                    'status': f'Erreur: {e}'
                })
        
        self.results = results
        return pd.DataFrame(results)
    
    def _calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Calcule les métriques de performance
        """
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        return {
            'accuracy': accuracy_score(y_true, y_pred),
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1_score': f1_score(y_true, y_pred, zero_division=0)
        }
    
    def display_results(self) -> None:
        """
        Affiche les résultats du benchmark
        """
        if not self.results:
            print("Aucun résultat à afficher")
            return
        
        df = pd.DataFrame(self.results)
        
        print("\n" + "=" * 60)
        print("RÉSULTATS DU BENCHMARK")
        print("=" * 60)
        
        # Trier par F1-score
        df_sorted = df.sort_values('f1_score', ascending=False)
        
        print("\n📊 Classement par F1-score:")
        for i, row in df_sorted.iterrows():
            print(f"   {row['modèle']}: {row['f1_score']:.4f} (Accuracy: {row['accuracy']:.4f})")
        
        print("\n⏱️  Temps d'exécution:")
        for i, row in df_sorted.iterrows():
            print(f"   {row['modèle']}: Train={row['train_time']:.4f}s, Predict={row['predict_time']:.4f}s")
        
        return df_sorted
    
    def plot_results(self, save_path: str = None) -> None:
        """
        Génère les graphiques de comparaison
        
        Args:
            save_path: Chemin pour sauvegarder les graphiques
        """
        if not self.results:
            print("Aucun résultat à afficher")
            return
        
        df = pd.DataFrame(self.results)
        df_sorted = df.sort_values('f1_score', ascending=True)
        
        # Créer une figure avec 2 sous-graphiques
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        # Graphique 1: F1-Score
        axes[0].barh(df_sorted['modèle'], df_sorted['f1_score'], color='steelblue')
        axes[0].set_xlabel('F1-Score')
        axes[0].set_title('Comparaison des modèles - F1-Score')
        axes[0].set_xlim(0, 1)
        
        # Ajouter les valeurs
        for i, (idx, row) in enumerate(df_sorted.iterrows()):
            axes[0].text(row['f1_score'] + 0.01, i, f"{row['f1_score']:.3f}", va='center')
        
        # Graphique 2: Temps d'entraînement
        axes[1].barh(df_sorted['modèle'], df_sorted['train_time'], color='coral')
        axes[1].set_xlabel('Temps d\'entraînement (secondes)')
        axes[1].set_title('Comparaison des modèles - Temps d\'entraînement')
        
        # Ajouter les valeurs
        for i, (idx, row) in enumerate(df_sorted.iterrows()):
            axes[1].text(row['train_time'] + 0.05, i, f"{row['train_time']:.2f}s", va='center')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"✅ Graphique sauvegardé: {save_path}")
        
        plt.show()
    
    def get_best_model(self) -> Tuple[str, float, Dict]:
        """
        Retourne le meilleur modèle selon le F1-score
        
        Returns:
            Tuple (nom_modèle, f1_score, métriques)
        """
        if not self.results:
            return None, 0, {}
        
        best = max(self.results, key=lambda x: x['f1_score'])
        return best['modèle'], best['f1_score'], best
    
    def save_results(self, filepath: str) -> None:
        """
        Sauvegarde les résultats dans un fichier CSV
        
        Args:
            filepath: Chemin du fichier
        """
        if not self.results:
            print("Aucun résultat à sauvegarder")
            return
        
        df = pd.DataFrame(self.results)
        df.to_csv(filepath, index=False)
        print(f"✅ Résultats sauvegardés: {filepath}")


def main():
    """
    Fonction principale pour exécuter le benchmark
    """
    print("=" * 60)
    print("BENCHMARK DES MODÈLES ML - AUTOSTOCKCHECK")
    print("=" * 60)
    
    # Chemin du dataset
    dataset_path = "data/datasets/dataset_entrainement.csv"
    
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset non trouvé: {dataset_path}")
        print("   Exécutez d'abord: python scripts/generate_synthetic_data.py")
        return
    
    # Créer le benchmark runner
    benchmark = BenchmarkRunner(test_size=0.2, random_state=42)
    
    # Charger les données
    print("\n📂 Chargement des données...")
    X, y = benchmark.load_data(dataset_path)
    print(f"   Features: {X.shape}")
    print(f"   Labels: {y.shape}")
    print(f"   Distribution: {np.bincount(y)}")
    
    # Exécuter le benchmark
    results_df = benchmark.run_benchmark(X, y)
    
    # Afficher les résultats
    sorted_results = benchmark.display_results()
    
    # Sauvegarder les résultats
    os.makedirs("reports/benchmark", exist_ok=True)
    benchmark.save_results("reports/benchmark/results.csv")
    
    # Générer les graphiques
    benchmark.plot_results("reports/benchmark/comparison.png")
    
    # Afficher le meilleur modèle
    best_name, best_f1, best_metrics = benchmark.get_best_model()
    print("\n" + "=" * 60)
    print(f"🏆 MEILLEUR MODÈLE: {best_name}")
    print(f"   F1-Score: {best_f1:.4f}")
    print(f"   Accuracy: {best_metrics.get('accuracy', 0):.4f}")
    print(f"   Precision: {best_metrics.get('precision', 0):.4f}")
    print(f"   Recall: {best_metrics.get('recall', 0):.4f}")
    print("=" * 60)


if __name__ == "__main__":
    main()