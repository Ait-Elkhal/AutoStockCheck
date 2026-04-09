"""
Benchmark Avancé - Visualisations complètes des modèles ML
AutoStockCheck - ECU Worldwide
"""

import sys
import os
import time
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, StratifiedKFold
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             confusion_matrix, roc_curve, auc, classification_report,
                             roc_auc_score, matthews_corrcoef, cohen_kappa_score)

# Ajouter le chemin src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.decision_tree import DecisionTree
from models.logistic_regression import LogisticRegression
from models.svm import SVM
from models.isolation_forest import IsolationForest
from models.random_forest import RandomForest
from models.neural_network_regularized import RegularizedNeuralNetwork

# Configuration des graphiques
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")
plt.rcParams['figure.figsize'] = (12, 10)
plt.rcParams['font.size'] = 12


class AdvancedBenchmark:
    """
    Benchmark avancé avec visualisations complètes
    """
    
    def __init__(self, test_size: float = 0.2, cv_folds: int = 3, random_state: int = 42):
        self.test_size = test_size
        self.cv_folds = cv_folds
        self.random_state = random_state
        self.results = []
        self.models = {}
        self.scaler = StandardScaler()
        self.colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E', '#BC4A6C', '#FF6B6B']
    
    def load_data(self, filepath: str):
        """Charge les données avec toutes les features"""
        df = pd.read_csv(filepath)
        
        # Liste des features disponibles
        feature_cols = [
            'diff_quantite', 'produit_absent', 'quantite_insuffisante', 'ratio_stock',
            'etat_produit', 'fiabilite_fournisseur', 'popularite',
            'saisonnalite', 'prix', 'valeur_ligne', 'produit_cher',
            'diff_x_prix', 'absent_x_prix', 'etat_x_popularite'
        ]
        
        # Garder uniquement les colonnes qui existent
        existing_cols = [col for col in feature_cols if col in df.columns]
        
        # Si pas assez de features, utiliser les features de base
        if len(existing_cols) < 4:
            existing_cols = ['diff_quantite', 'produit_absent', 'quantite_insuffisante', 'prix']
        
        X = df[existing_cols].values
        y = df['label'].values
        self.feature_names = existing_cols
        
        print(f"   Features utilisées: {len(existing_cols)} features")
        for feat in existing_cols:
            print(f"     - {feat}")
        
        return X, y
    
    def prepare_models(self):
        """Prépare tous les modèles - avec Neural Network"""
        self.models = {
            'Decision Tree': DecisionTree(max_depth=7, min_samples_split=5, min_samples_leaf=2, criterion='gini'),
            'Neural Network (Reg)': RegularizedNeuralNetwork(
                hidden_layers=[16, 8],  # Petit réseau pour éviter overfitting
                activation='relu',
                learning_rate=0.01,
                n_iterations=200,
                batch_size=64,
                dropout_rate=0.3,
                lambda_reg=0.01,
                verbose=False
            ),
            'Random Forest': RandomForest(n_trees=20, max_depth=7, min_samples_split=5, criterion='gini'),
            'SVM (Linear)': SVM(learning_rate=0.001, lambda_param=0.001, n_iterations=500, kernel='linear'),
            'Logistic Regression': LogisticRegression(learning_rate=0.1, n_iterations=500, regularization='l2'),
            'Isolation Forest': IsolationForest(n_trees=50, contamination=0.2, random_state=42, verbose=False)
        }
        
        print("   📊 Modèles utilisés:")
        print("      - Decision Tree")
        print("      - Neural Network (avec régularisation)")
        print("      - Random Forest")
        print("      - SVM (Linear)")
        print("      - Logistic Regression")
        print("      - Isolation Forest")
        print("   ⚠️ KNN désactivé (trop lent pour > 10k échantillons)")
        
        return self.models
    
    def run_benchmark(self, X, y):
        """Exécute le benchmark complet"""
        print("=" * 70)
        print("BENCHMARK AVANCÉ DES MODÈLES ML")
        print("=" * 70)
        
        # Division des données
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=self.test_size, random_state=self.random_state, stratify=y
        )
        
        # Sous-division pour validation (Neural Network)
        X_train, X_val, y_train, y_val = train_test_split(
            X_train, y_train, test_size=0.2, random_state=self.random_state, stratify=y_train
        )
        
        print(f"\n📊 Distribution des données:")
        print(f"   Total: {len(X)} échantillons")
        print(f"   Train: {len(X_train)} (Classe 0: {np.sum(y_train==0)}, Classe 1: {np.sum(y_train==1)})")
        print(f"   Val:   {len(X_val)} (Classe 0: {np.sum(y_val==0)}, Classe 1: {np.sum(y_val==1)})")
        print(f"   Test:  {len(X_test)} (Classe 0: {np.sum(y_test==0)}, Classe 1: {np.sum(y_test==1)})")
        
        # Normalisation
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Préparer les modèles
        models = self.prepare_models()
        
        results = []
        all_predictions = {}
        all_probabilities = {}
        
        for idx, (name, model) in enumerate(models.items()):
            print(f"\n🚀 {name}")
            print("-" * 50)
            
            try:
                # Entraînement
                start_train = time.time()
                
                # Pour le Neural Network, utiliser la validation
                if 'Neural Network' in name:
                    model.fit(X_train_scaled, y_train, X_val_scaled, y_val)
                else:
                    model.fit(X_train_scaled, y_train)
                
                train_time = time.time() - start_train
                
                # Prédiction
                start_pred = time.time()
                y_pred = model.predict(X_test_scaled)
                pred_time = time.time() - start_pred
                
                # Probabilités (si disponible)
                try:
                    y_proba = model.predict_proba(X_test_scaled)
                    y_proba_positive = y_proba[:, 1]
                except:
                    y_proba_positive = None
                
                # Métriques
                metrics = self._calculate_all_metrics(y_test, y_pred, y_proba_positive)
                
                # Validation croisée (sur sous-échantillon pour accélérer)
                try:
                    n_cv = min(2000, len(X_train_scaled))
                    X_cv = X_train_scaled[:n_cv]
                    y_cv = y_train[:n_cv]
                    cv_scores = self._cross_validate(model, X_cv, y_cv)
                    cv_mean = np.mean(cv_scores)
                    cv_std = np.std(cv_scores)
                except Exception as e:
                    cv_mean = 0
                    cv_std = 0
                
                result = {
                    'modèle': name,
                    'accuracy': metrics['accuracy'],
                    'precision': metrics['precision'],
                    'recall': metrics['recall'],
                    'f1_score': metrics['f1_score'],
                    'specificity': metrics['specificity'],
                    'mcc': metrics['mcc'],
                    'kappa': metrics['kappa'],
                    'auc': metrics['auc'],
                    'train_time': train_time,
                    'pred_time': pred_time,
                    'cv_mean': cv_mean,
                    'cv_std': cv_std
                }
                
                results.append(result)
                all_predictions[name] = y_pred
                all_probabilities[name] = y_proba_positive
                
                print(f"   ✅ Accuracy: {metrics['accuracy']:.4f}")
                print(f"   ✅ Precision: {metrics['precision']:.4f}")
                print(f"   ✅ Recall: {metrics['recall']:.4f}")
                print(f"   ✅ F1-Score: {metrics['f1_score']:.4f}")
                if y_proba_positive is not None:
                    print(f"   ✅ AUC: {metrics['auc']:.4f}")
                print(f"   ⏱️  Train: {train_time:.4f}s, Predict: {pred_time:.4f}s")
                if cv_mean > 0:
                    print(f"   📊 CV: {cv_mean:.4f} ± {cv_std:.4f}")
                
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
                result = {
                    'modèle': name,
                    'accuracy': 0, 'precision': 0, 'recall': 0, 'f1_score': 0,
                    'specificity': 0, 'mcc': 0, 'kappa': 0, 'auc': 0,
                    'train_time': 0, 'pred_time': 0, 'cv_mean': 0, 'cv_std': 0
                }
                results.append(result)
                all_predictions[name] = None
                all_probabilities[name] = None
        
        self.results = results
        self.all_predictions = all_predictions
        self.all_probabilities = all_probabilities
        self.y_test = y_test
        
        return pd.DataFrame(results)
    
    def _calculate_all_metrics(self, y_true, y_pred, y_proba=None):
        """Calcule toutes les métriques"""
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)
        
        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel()
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        
        mcc = matthews_corrcoef(y_true, y_pred)
        kappa = cohen_kappa_score(y_true, y_pred)
        
        auc_score = 0
        if y_proba is not None:
            try:
                auc_score = roc_auc_score(y_true, y_proba)
            except:
                pass
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'specificity': specificity,
            'mcc': mcc,
            'kappa': kappa,
            'auc': auc_score
        }
    
    def _cross_validate(self, model, X, y):
        """Validation croisée simplifiée"""
        skf = StratifiedKFold(n_splits=min(self.cv_folds, len(np.unique(y))), 
                              shuffle=True, random_state=self.random_state)
        scores = []
        
        for train_idx, val_idx in skf.split(X, y):
            X_train_cv, X_val_cv = X[train_idx], X[val_idx]
            y_train_cv, y_val_cv = y[train_idx], y[val_idx]
            
            model_copy = self._clone_model(model)
            model_copy.fit(X_train_cv, y_train_cv)
            y_pred_cv = model_copy.predict(X_val_cv)
            scores.append(accuracy_score(y_val_cv, y_pred_cv))
        
        return np.array(scores)
    
    def _clone_model(self, model):
        """Clone un modèle"""
        model_name = model.__class__.__name__
        
        if model_name == 'DecisionTree':
            return DecisionTree(max_depth=model.max_depth, criterion=model.criterion)
        elif model_name == 'LogisticRegression':
            return LogisticRegression(learning_rate=model.learning_rate, n_iterations=200)
        elif model_name == 'SVM':
            return SVM(learning_rate=model.learning_rate, lambda_param=model.lambda_param,
                       n_iterations=200, kernel=model.kernel)
        elif model_name == 'IsolationForest':
            return IsolationForest(n_trees=50, contamination=model.contamination)
        elif model_name == 'RandomForest':
            return RandomForest(n_trees=model.n_trees, max_depth=model.max_depth)
        elif model_name == 'RegularizedNeuralNetwork':
            return RegularizedNeuralNetwork(
                hidden_layers=model.hidden_layers,
                dropout_rate=model.dropout_rate,
                lambda_reg=model.lambda_reg
            )
        return model
    
    def plot_confusion_matrices(self, save_path=None):
        """Affiche les matrices de confusion"""
        n_models = len(self.all_predictions)
        n_cols = 2
        n_rows = (n_models + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(6*n_cols, 5*n_rows))
        if n_models == 1:
            axes = [axes]
        else:
            axes = axes.flatten()
        
        for idx, (name, y_pred) in enumerate(self.all_predictions.items()):
            if y_pred is not None and idx < len(axes):
                cm = confusion_matrix(self.y_test, y_pred)
                
                sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[idx],
                            xticklabels=['Conforme', 'Manque'],
                            yticklabels=['Conforme', 'Manque'])
                axes[idx].set_title(f'{name}')
                axes[idx].set_xlabel('Prédit')
                axes[idx].set_ylabel('Réel')
        
        for i in range(len(self.all_predictions), len(axes)):
            axes[i].set_visible(False)
        
        plt.suptitle('Matrices de Confusion', fontsize=14, y=1.02)
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"✅ Matrices de confusion sauvegardées: {save_path}")
        
        plt.show()
    
    def plot_roc_curves(self, save_path=None):
        """Affiche les courbes ROC"""
        plt.figure(figsize=(10, 8))
        
        for idx, (name, y_proba) in enumerate(self.all_probabilities.items()):
            if y_proba is not None:
                fpr, tpr, _ = roc_curve(self.y_test, y_proba)
                auc_score = self.results[idx]['auc'] if idx < len(self.results) else 0
                plt.plot(fpr, tpr, lw=2, label=f'{name} (AUC = {auc_score:.3f})', 
                         color=self.colors[idx % len(self.colors)])
        
        plt.plot([0, 1], [0, 1], 'k--', lw=1, label='Aléatoire')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('Taux de Faux Positifs (FPR)')
        plt.ylabel('Taux de Vrais Positifs (TPR)')
        plt.title('Courbes ROC')
        plt.legend(loc='lower right')
        plt.grid(alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"✅ Courbes ROC sauvegardées: {save_path}")
        
        plt.show()
    
    def plot_metrics_barplot(self, save_path=None):
        """Affiche les barplots des métriques"""
        df = pd.DataFrame(self.results)
        df_sorted = df.sort_values('f1_score', ascending=True)
        
        metrics = ['accuracy', 'precision', 'recall', 'f1_score', 'specificity', 'mcc']
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        y_pos = np.arange(len(df_sorted))
        bar_width = 0.12
        
        for i, metric in enumerate(metrics):
            values = df_sorted[metric].values
            ax.barh(y_pos + i * bar_width, values, bar_width, label=metric.capitalize())
        
        ax.set_yticks(y_pos + bar_width * 2.5)
        ax.set_yticklabels(df_sorted['modèle'])
        ax.set_xlabel('Score')
        ax.set_title('Comparaison des Métriques')
        ax.legend(loc='lower right')
        ax.set_xlim(0, 1)
        ax.grid(alpha=0.3, axis='x')
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"✅ Graphique des métriques sauvegardé: {save_path}")
        
        plt.show()
    
    def plot_timing_comparison(self, save_path=None):
        """Affiche la comparaison des temps d'exécution"""
        df = pd.DataFrame(self.results)
        df_sorted = df.sort_values('train_time', ascending=False)
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        bars1 = ax1.barh(df_sorted['modèle'], df_sorted['train_time'], color='steelblue')
        ax1.set_xlabel('Temps (secondes)')
        ax1.set_title('Temps d\'entraînement')
        
        for bar, val in zip(bars1, df_sorted['train_time']):
            ax1.text(val + 0.01, bar.get_y() + bar.get_height()/2, f'{val:.3f}s', va='center')
        
        bars2 = ax2.barh(df_sorted['modèle'], df_sorted['pred_time'], color='coral')
        ax2.set_xlabel('Temps (secondes)')
        ax2.set_title('Temps de prédiction')
        
        for bar, val in zip(bars2, df_sorted['pred_time']):
            ax2.text(val + 0.001, bar.get_y() + bar.get_height()/2, f'{val:.4f}s', va='center')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"✅ Graphique des temps sauvegardé: {save_path}")
        
        plt.show()
    
    def print_detailed_report(self):
        """Affiche un rapport détaillé"""
        df = pd.DataFrame(self.results)
        
        print("\n" + "=" * 100)
        print("RAPPORT DÉTAILLÉ DU BENCHMARK")
        print("=" * 100)
        
        print("\n📊 TABLEAU COMPARATIF DES MODÈLES:")
        print("-" * 110)
        print(f"{'Modèle':<25} {'Acc':<8} {'Prec':<8} {'Recall':<8} {'F1':<8} {'AUC':<8} {'Train(s)':<10} {'Pred(s)':<10}")
        print("-" * 110)
        
        for _, row in df.iterrows():
            auc_val = row['auc'] if row['auc'] > 0 else 0
            print(f"{row['modèle']:<25} {row['accuracy']:<8.4f} {row['precision']:<8.4f} "
                  f"{row['recall']:<8.4f} {row['f1_score']:<8.4f} {auc_val:<8.4f} "
                  f"{row['train_time']:<10.4f} {row['pred_time']:<10.4f}")
        
        print("-" * 110)
        
        if len(df) > 0:
            best_idx = df['f1_score'].idxmax()
            best = df.loc[best_idx]
            
            print(f"\n🏆 MEILLEUR MODÈLE (F1-Score): {best['modèle']}")
            print(f"   F1-Score: {best['f1_score']:.4f}")
            print(f"   Accuracy: {best['accuracy']:.4f}")
            print(f"   Precision: {best['precision']:.4f}")
            print(f"   Recall: {best['recall']:.4f}")
            print(f"   AUC: {best['auc']:.4f}")
            print(f"   Temps entraînement: {best['train_time']:.4f}s")
            print(f"   Temps prédiction: {best['pred_time']:.4f}s")
        
        good_models = df[df['f1_score'] > 0.8]
        if len(good_models) > 0:
            fastest_idx = good_models['pred_time'].idxmin()
            fastest = df.loc[fastest_idx]
            
            print(f"\n⚡ MODÈLE LE PLUS RAPIDE: {fastest['modèle']}")
            print(f"   Temps prédiction: {fastest['pred_time']:.4f}s")
            print(f"   F1-Score: {fastest['f1_score']:.4f}")


def main():
    """Fonction principale"""
    print("=" * 100)
    print("BENCHMARK AVANCÉ - AUTOStockCheck")
    print("=" * 100)
    
    dataset_path = "data/datasets/dataset_entrainement.csv"
    
    if not os.path.exists(dataset_path):
        print(f"❌ Dataset non trouvé: {dataset_path}")
        print("   Exécutez d'abord: python scripts/generate_synthetic_data_advanced.py")
        return
    
    benchmark = AdvancedBenchmark(test_size=0.2, random_state=42, cv_folds=3)
    
    print("\n📂 Chargement des données...")
    X, y = benchmark.load_data(dataset_path)
    print(f"   Features: {X.shape[1]} features")
    print(f"   Échantillons: {len(X)}")
    print(f"   Distribution: Classe 0={np.sum(y==0)}, Classe 1={np.sum(y==1)}")
    
    results_df = benchmark.run_benchmark(X, y)
    
    benchmark.print_detailed_report()
    
    os.makedirs("reports/benchmark", exist_ok=True)
    
    try:
        benchmark.plot_confusion_matrices("reports/benchmark/confusion_matrices.png")
    except Exception as e:
        print(f"⚠️ Erreur matrices confusion: {e}")
    
    try:
        benchmark.plot_roc_curves("reports/benchmark/roc_curves.png")
    except Exception as e:
        print(f"⚠️ Erreur courbes ROC: {e}")
    
    try:
        benchmark.plot_metrics_barplot("reports/benchmark/metrics_barplot.png")
    except Exception as e:
        print(f"⚠️ Erreur barplot: {e}")
    
    try:
        benchmark.plot_timing_comparison("reports/benchmark/timing_comparison.png")
    except Exception as e:
        print(f"⚠️ Erreur timing: {e}")
    
    results_df.to_csv("reports/benchmark/results_detailed.csv", index=False)
    print("\n✅ Résultats sauvegardés: reports/benchmark/results_detailed.csv")
    
    print("\n" + "=" * 100)
    print("✅ BENCHMARK TERMINÉ AVEC SUCCÈS !")
    print("=" * 100)


if __name__ == "__main__":
    main()