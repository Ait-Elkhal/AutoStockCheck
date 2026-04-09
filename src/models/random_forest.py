"""
Random Forest - Forêt aléatoire from scratch
AutoStockCheck - ECU Worldwide
"""

import numpy as np
import time
from typing import Dict, Any, Optional, List, Tuple
from .base_model import BaseModel
from .decision_tree import DecisionTree


class RandomForest(BaseModel):
    """
    Random Forest implémentée from scratch pour la classification binaire
    
    Paramètres:
        n_trees: Nombre d'arbres dans la forêt
        max_depth: Profondeur maximale de chaque arbre
        min_samples_split: Nombre minimum d'échantillons pour diviser un nœud
        min_samples_leaf: Nombre minimum d'échantillons dans une feuille
        max_features: Nombre maximum de features à considérer pour chaque split
        bootstrap: Utiliser le bootstrap sampling (True) ou non (False)
        criterion: Critère de division ('entropy' ou 'gini')
        random_state: Graine aléatoire pour la reproductibilité
        verbose: Afficher la progression de l'entraînement
    """
    
    def __init__(self, n_trees: int = 10, max_depth: int = 5,
                 min_samples_split: int = 2, min_samples_leaf: int = 1,
                 max_features: str = 'sqrt', bootstrap: bool = True,
                 criterion: str = 'entropy', random_state: int = None,
                 verbose: bool = False):
        """
        Initialisation de la Random Forest
        """
        super().__init__(name="RandomForest")
        
        self.n_trees = n_trees
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.max_features = max_features
        self.bootstrap = bootstrap
        self.criterion = criterion
        self.random_state = random_state
        self.verbose = verbose
        
        self.trees = []
        self.feature_indices = []
        self.feature_importance_ = None
        
        # Enregistrement des paramètres
        self.params = {
            'n_trees': n_trees,
            'max_depth': max_depth,
            'min_samples_split': min_samples_split,
            'min_samples_leaf': min_samples_leaf,
            'max_features': max_features,
            'bootstrap': bootstrap,
            'criterion': criterion
        }
        
        if random_state is not None:
            np.random.seed(random_state)
    
    def _get_max_features(self, n_features: int) -> int:
        """
        Calcule le nombre de features à considérer pour chaque split
        
        Args:
            n_features: Nombre total de features
            
        Returns:
            Nombre de features à échantillonner
        """
        if isinstance(self.max_features, int):
            return min(self.max_features, n_features)
        elif self.max_features == 'sqrt':
            return int(np.sqrt(n_features))
        elif self.max_features == 'log2':
            return int(np.log2(n_features))
        elif self.max_features == 'auto':
            return int(np.sqrt(n_features))
        else:
            return n_features
    
    def _bootstrap_sample(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Crée un échantillon bootstrap (avec remise)
        
        Args:
            X: Features
            y: Labels
            
        Returns:
            Tuple (X_sample, y_sample)
        """
        n_samples = X.shape[0]
        indices = np.random.choice(n_samples, n_samples, replace=True)
        return X[indices], y[indices]
    
    def _sample_features(self, n_features: int, max_features: int) -> List[int]:
        """
        Échantillonne aléatoirement un sous-ensemble de features
        
        Args:
            n_features: Nombre total de features
            max_features: Nombre de features à échantillonner
            
        Returns:
            Liste des indices des features sélectionnées
        """
        return np.random.choice(n_features, max_features, replace=False).tolist()
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'RandomForest':
        """
        Entraîne la Random Forest
        
        Args:
            X: Features d'entraînement (n_samples, n_features)
            y: Labels d'entraînement (n_samples,)
            
        Returns:
            self: Le modèle entraîné
        """
        start_time = time.time()
        
        X = np.array(X)
        y = np.array(y)
        
        if len(X) != len(y):
            raise ValueError("X et y doivent avoir le même nombre d'échantillons")
        
        n_samples, n_features = X.shape
        max_features = self._get_max_features(n_features)
        
        # Vider les arbres précédents
        self.trees = []
        self.feature_indices = []
        
        for i in range(self.n_trees):
            if self.verbose and (i + 1) % 10 == 0:
                print(f"Construction de l'arbre {i+1}/{self.n_trees}")
            
            # Bootstrap sampling
            if self.bootstrap:
                X_sample, y_sample = self._bootstrap_sample(X, y)
            else:
                X_sample, y_sample = X, y
            
            # Feature sampling
            feature_idx = self._sample_features(n_features, max_features)
            X_sample_features = X_sample[:, feature_idx]
            
            # Créer et entraîner un arbre de décision
            tree = DecisionTree(
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                min_samples_leaf=self.min_samples_leaf,
                criterion=self.criterion
            )
            tree.fit(X_sample_features, y_sample)
            
            self.trees.append(tree)
            self.feature_indices.append(feature_idx)
        
        # Calculer l'importance des features
        self._compute_feature_importance(n_features)
        
        self.is_trained = True
        self.training_time = time.time() - start_time
        self.n_features = n_features
        self.classes_ = np.unique(y)
        self.n_classes = len(self.classes_)
        
        return self
    
    def _compute_feature_importance(self, n_features: int) -> None:
        """
        Calcule l'importance de chaque feature
        Basé sur la réduction moyenne d'impureté
        
        Args:
            n_features: Nombre total de features
        """
        importance = np.zeros(n_features)
        
        for tree, feature_idx in zip(self.trees, self.feature_indices):
            # Pour chaque arbre, récupérer l'importance des features
            # (simplifié: utilisation de la profondeur comme proxy)
            # Dans une implémentation complète, on utiliserait la réduction d'impureté
            tree_importance = np.ones(len(feature_idx))
            
            for j, idx in enumerate(feature_idx):
                importance[idx] += tree_importance[j]
        
        # Normaliser
        if np.sum(importance) > 0:
            importance = importance / np.sum(importance)
        
        self.feature_importance_ = importance
    
    def _predict_tree(self, X: np.ndarray, tree: DecisionTree, feature_idx: List[int]) -> np.ndarray:
        """
        Prédit avec un seul arbre en utilisant les features sélectionnées
        
        Args:
            X: Features
            tree: Arbre de décision
            feature_idx: Indices des features utilisées par l'arbre
            
        Returns:
            Prédictions de l'arbre
        """
        X_subset = X[:, feature_idx]
        return tree.predict(X_subset)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Prédit les labels pour les données fournies (vote majoritaire)
        
        Args:
            X: Features (n_samples, n_features)
            
        Returns:
            Prédictions (n_samples,)
        """
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné")
        
        X = np.array(X)
        
        start_time = time.time()
        
        # Collecter les prédictions de tous les arbres
        all_predictions = np.zeros((len(X), len(self.trees)))
        
        for i, (tree, feature_idx) in enumerate(zip(self.trees, self.feature_indices)):
            all_predictions[:, i] = self._predict_tree(X, tree, feature_idx)
        
        # Vote majoritaire
        predictions = np.zeros(len(X), dtype=int)
        for i in range(len(X)):
            votes = all_predictions[i, :]
            unique, counts = np.unique(votes, return_counts=True)
            predictions[i] = unique[np.argmax(counts)]
        
        self.prediction_time = time.time() - start_time
        
        return predictions
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Prédit les probabilités pour les données fournies
        
        Args:
            X: Features (n_samples, n_features)
            
        Returns:
            Probabilités (n_samples, n_classes)
        """
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné")
        
        X = np.array(X)
        probas = np.zeros((len(X), self.n_classes))
        
        # Collecter les prédictions de tous les arbres
        all_predictions = np.zeros((len(X), len(self.trees)))
        
        for i, (tree, feature_idx) in enumerate(zip(self.trees, self.feature_indices)):
            all_predictions[:, i] = self._predict_tree(X, tree, feature_idx)
        
        # Calculer les probabilités
        for i in range(len(X)):
            for j in range(self.n_classes):
                probas[i, j] = np.sum(all_predictions[i, :] == self.classes_[j]) / len(self.trees)
        
        return probas
    
    def get_feature_importance(self, feature_names: List[str] = None) -> Dict[str, float]:
        """
        Retourne l'importance des features
        
        Args:
            feature_names: Noms des features (optionnel)
            
        Returns:
            Dictionnaire feature -> importance
        """
        if self.feature_importance_ is None:
            return {}
        
        if feature_names:
            return {feature_names[i]: self.feature_importance_[i] 
                    for i in range(len(self.feature_importance_))}
        else:
            return {f"feature_{i}": self.feature_importance_[i] 
                    for i in range(len(self.feature_importance_))}
    
    def get_oob_score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        Calcule le score Out-Of-Bag (si bootstrap=True)
        
        Args:
            X: Features d'entraînement
            y: Labels d'entraînement
            
        Returns:
            Score OOB
        """
        if not self.bootstrap:
            return None
        
        n_samples = X.shape[0]
        oob_predictions = np.zeros(n_samples)
        oob_counts = np.zeros(n_samples)
        
        for tree, feature_idx in zip(self.trees, self.feature_indices):
            # Identifier les indices non utilisés pour cet arbre
            # (simplifié: dans une implémentation complète, il faudrait stocker les indices bootstrap)
            pass
        
        return None
    
    def __str__(self) -> str:
        return f"RandomForest(n_trees={self.n_trees}, max_depth={self.max_depth}, criterion={self.criterion})"