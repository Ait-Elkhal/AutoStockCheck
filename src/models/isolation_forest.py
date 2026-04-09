"""
Isolation Forest - Détection d'anomalies from scratch
AutoStockCheck - ECU Worldwide
"""

import numpy as np
import time
import math
from typing import Dict, Any, Optional, List, Tuple
from .base_model import BaseModel


class IsolationTreeNode:
    """
    Nœud d'un arbre d'isolation
    """
    def __init__(self, feature: int = None, threshold: float = None,
                 left: 'IsolationTreeNode' = None, right: 'IsolationTreeNode' = None,
                 size: int = None, is_leaf: bool = True):
        self.feature = feature
        self.threshold = threshold
        self.left = left
        self.right = right
        self.size = size
        self.is_leaf = is_leaf


class IsolationTree:
    """
    Arbre d'isolation individuel
    """
    
    def __init__(self, max_depth: int = 10, random_state: int = None):
        """
        Initialisation d'un arbre d'isolation
        
        Args:
            max_depth: Profondeur maximale de l'arbre
            random_state: Graine aléatoire pour la reproductibilité
        """
        self.max_depth = max_depth
        self.random_state = random_state
        self.root = None
        self.sample_size = 0
        
        if random_state is not None:
            np.random.seed(random_state)
    
    def _average_path_length(self, n: int) -> float:
        """
        Calcule la longueur de chemin moyenne pour un arbre
        c(n) = 2H(n-1) - 2(n-1)/n
        
        Args:
            n: Nombre d'échantillons
            
        Returns:
            Longueur de chemin moyenne
        """
        if n <= 1:
            return 0
        
        # Calcul du nombre harmonique H(n-1)
        h = math.log(n - 1) + 0.5772156649  # Constante d'Euler-Mascheroni
        
        return 2 * h - (2 * (n - 1) / n)
    
    def _build_tree(self, X: np.ndarray, current_depth: int) -> IsolationTreeNode:
        """
        Construit récursivement l'arbre d'isolation
        
        Args:
            X: Données à isoler
            current_depth: Profondeur actuelle
            
        Returns:
            Nœud de l'arbre
        """
        n_samples = X.shape[0]
        
        # Condition d'arrêt
        if n_samples <= 1 or current_depth >= self.max_depth:
            return IsolationTreeNode(size=n_samples, is_leaf=True)
        
        n_features = X.shape[1]
        
        # Sélection aléatoire d'une feature
        feature_idx = np.random.randint(0, n_features)
        
        # Trouver min et max de la feature
        min_val = X[:, feature_idx].min()
        max_val = X[:, feature_idx].max()
        
        # Si toutes les valeurs sont identiques
        if min_val == max_val:
            return IsolationTreeNode(size=n_samples, is_leaf=True)
        
        # Sélection aléatoire d'un seuil entre min et max
        threshold = np.random.uniform(min_val, max_val)
        
        # Diviser les données
        left_idx = X[:, feature_idx] < threshold
        right_idx = X[:, feature_idx] >= threshold
        
        # Si une des divisions est vide, créer une feuille
        if np.sum(left_idx) == 0 or np.sum(right_idx) == 0:
            return IsolationTreeNode(size=n_samples, is_leaf=True)
        
        # Construire récursivement les sous-arbres
        left_tree = self._build_tree(X[left_idx], current_depth + 1)
        right_tree = self._build_tree(X[right_idx], current_depth + 1)
        
        return IsolationTreeNode(
            feature=feature_idx,
            threshold=threshold,
            left=left_tree,
            right=right_tree,
            size=n_samples,
            is_leaf=False
        )
    
    def fit(self, X: np.ndarray) -> 'IsolationTree':
        """
        Entraîne l'arbre d'isolation
        
        Args:
            X: Données d'entraînement
            
        Returns:
            self
        """
        self.sample_size = X.shape[0]
        self.root = self._build_tree(X, 0)
        return self
    
    def _path_length(self, x: np.ndarray, node: IsolationTreeNode, current_depth: int) -> float:
        """
        Calcule la longueur de chemin pour un point
        
        Args:
            x: Point à évaluer
            node: Nœud courant
            current_depth: Profondeur actuelle
            
        Returns:
            Longueur de chemin
        """
        if node.is_leaf:
            return current_depth + self._average_path_length(node.size)
        
        if x[node.feature] < node.threshold:
            return self._path_length(x, node.left, current_depth + 1)
        else:
            return self._path_length(x, node.right, current_depth + 1)
    
    def path_length(self, X: np.ndarray) -> np.ndarray:
        """
        Calcule les longueurs de chemin pour tous les points
        
        Args:
            X: Données à évaluer
            
        Returns:
            Longueurs de chemin
        """
        if self.root is None:
            raise ValueError("L'arbre n'est pas entraîné")
        
        path_lengths = np.zeros(len(X))
        for i, x in enumerate(X):
            path_lengths[i] = self._path_length(x, self.root, 0)
        
        return path_lengths


class IsolationForest(BaseModel):
    """
    Isolation Forest pour la détection d'anomalies
    
    Paramètres:
        n_trees: Nombre d'arbres dans la forêt
        max_depth: Profondeur maximale de chaque arbre
        contamination: Proportion estimée d'anomalies (0 à 0.5)
        bootstrap_size: Taille du sous-échantillon pour chaque arbre
        random_state: Graine aléatoire
        verbose: Afficher la progression
    """
    
    def __init__(self, n_trees: int = 100, max_depth: int = 10,
                 contamination: float = 0.1, bootstrap_size: int = 256,
                 random_state: int = None, verbose: bool = False):
        """
        Initialisation de l'Isolation Forest
        """
        super().__init__(name="IsolationForest")
        
        self.n_trees = n_trees
        self.max_depth = max_depth
        self.contamination = contamination
        self.bootstrap_size = bootstrap_size
        self.random_state = random_state
        self.verbose = verbose
        
        self.trees = []
        self.threshold_ = None
        self.train_scores_ = None
        
        # Enregistrement des paramètres
        self.params = {
            'n_trees': n_trees,
            'max_depth': max_depth,
            'contamination': contamination,
            'bootstrap_size': bootstrap_size
        }
    
    def _average_path_length(self, n: int) -> float:
        """
        Calcule la longueur de chemin moyenne pour n échantillons
        
        c(n) = 2H(n-1) - 2(n-1)/n
        """
        if n <= 1:
            return 0
        
        # Calcul du nombre harmonique H(n-1) = ln(n-1) + γ
        h = math.log(n - 1) + 0.5772156649  # Constante d'Euler-Mascheroni
        
        return 2 * h - (2 * (n - 1) / n)
    
    def _anomaly_score(self, path_lengths: np.ndarray, n_samples: int) -> np.ndarray:
        """
        Calcule le score d'anomalie
        
        Formule: s(x, n) = 2^(-E[h(x)] / c(n))
        
        Args:
            path_lengths: Longueurs de chemin moyennes
            n_samples: Nombre d'échantillons d'entraînement
            
        Returns:
            Scores d'anomalie (0 à 1, plus élevé = plus anormal)
        """
        c_n = self._average_path_length(n_samples)
        return 2 ** (-path_lengths / c_n)
    
    def _compute_path_lengths(self, X: np.ndarray) -> np.ndarray:
        """
        Calcule les longueurs de chemin moyennes pour tous les points
        
        Args:
            X: Données à évaluer
            
        Returns:
            Longueurs de chemin moyennes
        """
        X = np.array(X)
        n_samples = X.shape[0]
        path_lengths = np.zeros((n_samples, len(self.trees)))
        
        for i, tree in enumerate(self.trees):
            path_lengths[:, i] = tree.path_length(X)
        
        # Moyenne sur tous les arbres
        return np.mean(path_lengths, axis=1)
    
    def fit(self, X: np.ndarray, y: np.ndarray = None) -> 'IsolationForest':
        """
        Entraîne l'Isolation Forest
        
        Args:
            X: Données d'entraînement
            y: Non utilisé (pour compatibilité avec BaseModel)
            
        Returns:
            self
        """
        start_time = time.time()
        
        X = np.array(X)
        n_samples = X.shape[0]
        
        # Définir la profondeur maximale
        if self.max_depth is None:
            self.max_depth = int(np.ceil(np.log2(self.bootstrap_size)))
        
        # Fixer la graine aléatoire
        if self.random_state is not None:
            np.random.seed(self.random_state)
        
        # Construire les arbres
        self.trees = []
        
        for i in range(self.n_trees):
            if self.verbose and (i + 1) % 10 == 0:
                print(f"Construction de l'arbre {i+1}/{self.n_trees}")
            
            # Sous-échantillonnage aléatoire
            if self.bootstrap_size < n_samples:
                idx = np.random.choice(n_samples, self.bootstrap_size, replace=False)
                X_sample = X[idx]
            else:
                X_sample = X
            
            # Créer et entraîner un arbre
            tree = IsolationTree(max_depth=self.max_depth, random_state=self.random_state)
            tree.fit(X_sample)
            self.trees.append(tree)
        
        # Calculer les scores sur les données d'entraînement pour déterminer le seuil
        if self.contamination is not None:
            # Calculer les longueurs de chemin
            path_lengths = self._compute_path_lengths(X)
            # Utiliser la taille d'échantillon du premier arbre
            n_samples_train = self.trees[0].sample_size if self.trees else self.bootstrap_size
            self.train_scores_ = self._anomaly_score(path_lengths, n_samples_train)
            self.threshold_ = np.percentile(self.train_scores_, 100 * (1 - self.contamination))
        
        self.is_trained = True
        self.training_time = time.time() - start_time
        
        return self
    
    def score_samples(self, X: np.ndarray) -> np.ndarray:
        """
        Calcule les scores d'anomalie pour chaque échantillon
        
        Args:
            X: Données à évaluer
            
        Returns:
            Scores d'anomalie (plus élevé = plus anormal)
        """
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné")
        
        path_lengths = self._compute_path_lengths(X)
        n_samples_train = self.trees[0].sample_size if self.trees else self.bootstrap_size
        scores = self._anomaly_score(path_lengths, n_samples_train)
        
        return scores
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Prédit si les échantillons sont des anomalies (1) ou normaux (0)
        
        Args:
            X: Données à prédire
            
        Returns:
            Labels: 1 pour anomalie, 0 pour normal
        """
        scores = self.score_samples(X)
        
        if self.threshold_ is not None:
            return (scores >= self.threshold_).astype(int)
        else:
            # Par défaut, utiliser la moyenne
            return (scores >= np.mean(scores)).astype(int)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Retourne les probabilités d'être une anomalie
        
        Args:
            X: Données à évaluer
            
        Returns:
            Probabilités (n_samples, 2)
        """
        scores = self.score_samples(X)
        proba_anomaly = scores
        proba_normal = 1 - scores
        
        return np.column_stack([proba_normal, proba_anomaly])
    
    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """
        Retourne le score de décision (plus négatif = plus anormal)
        """
        scores = self.score_samples(X)
        return -scores
    
    def get_threshold(self) -> float:
        """
        Retourne le seuil de détection
        """
        return self.threshold_
    
    def get_path_length_stats(self, X: np.ndarray) -> Dict[str, float]:
        """
        Calcule les statistiques des longueurs de chemin
        
        Args:
            X: Données à évaluer
            
        Returns:
            Statistiques
        """
        path_lengths = self._compute_path_lengths(X)
        
        return {
            'min': np.min(path_lengths),
            'max': np.max(path_lengths),
            'mean': np.mean(path_lengths),
            'std': np.std(path_lengths),
            'median': np.median(path_lengths)
        }
    
    def __str__(self) -> str:
        return f"IsolationForest(n_trees={self.n_trees}, max_depth={self.max_depth})"