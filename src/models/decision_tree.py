"""
Decision Tree - Arbre de décision from scratch
AutoStockCheck - ECU Worldwide
"""

import numpy as np
import time
from typing import Dict, Any, Optional, List, Tuple
from .base_model import BaseModel


class Node:
    """
    Classe représentant un nœud dans l'arbre de décision
    """
    def __init__(self, feature: int = None, threshold: float = None, 
                 left: 'Node' = None, right: 'Node' = None, 
                 value: int = None):
        """
        Initialisation d'un nœud
        
        Args:
            feature: Index de la feature utilisée pour la séparation
            threshold: Valeur seuil pour la séparation
            left: Sous-arbre gauche (feature <= threshold)
            right: Sous-arbre droit (feature > threshold)
            value: Valeur de prédiction pour une feuille
        """
        self.feature = feature
        self.threshold = threshold
        self.left = left
        self.right = right
        self.value = value
        self.is_leaf = value is not None


class DecisionTree(BaseModel):
    """
    Arbre de décision implémenté from scratch pour la classification binaire
    
    Paramètres:
        max_depth: Profondeur maximale de l'arbre
        min_samples_split: Nombre minimum d'échantillons pour diviser un nœud
        min_samples_leaf: Nombre minimum d'échantillons dans une feuille
        criterion: Critère de division ('entropy' ou 'gini')
    """
    
    def __init__(self, max_depth: int = 5, min_samples_split: int = 2, 
                 min_samples_leaf: int = 1, criterion: str = 'entropy'):
        """
        Initialisation de l'arbre de décision
        """
        super().__init__(name="DecisionTree")
        
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.min_samples_leaf = min_samples_leaf
        self.criterion = criterion
        self.tree = None
        self.n_features = None
        
        # Enregistrement des paramètres
        self.params = {
            'max_depth': max_depth,
            'min_samples_split': min_samples_split,
            'min_samples_leaf': min_samples_leaf,
            'criterion': criterion
        }
    
    def _entropy(self, y: np.ndarray) -> float:
        """
        Calcule l'entropie d'un ensemble d'échantillons
        
        Formule: H(Y) = -∑ p(y) * log2(p(y))
        
        Args:
            y: Labels des échantillons
            
        Returns:
            Valeur de l'entropie
        """
        if len(y) == 0:
            return 0.0
        
        # Compter les occurrences de chaque classe
        classes, counts = np.unique(y, return_counts=True)
        probabilities = counts / len(y)
        
        # Calcul de l'entropie
        entropy = -np.sum(probabilities * np.log2(probabilities + 1e-10))
        
        return entropy
    
    def _gini(self, y: np.ndarray) -> float:
        """
        Calcule l'indice de Gini d'un ensemble d'échantillons
        
        Formule: G = 1 - ∑ p(y)²
        
        Args:
            y: Labels des échantillons
            
        Returns:
            Valeur de l'indice de Gini
        """
        if len(y) == 0:
            return 0.0
        
        # Compter les occurrences de chaque classe
        classes, counts = np.unique(y, return_counts=True)
        probabilities = counts / len(y)
        
        # Calcul de l'indice de Gini
        gini = 1 - np.sum(probabilities ** 2)
        
        return gini
    
    def _impurity(self, y: np.ndarray) -> float:
        """
        Calcule l'impureté selon le critère choisi
        
        Args:
            y: Labels des échantillons
            
        Returns:
            Valeur de l'impureté
        """
        if self.criterion == 'entropy':
            return self._entropy(y)
        elif self.criterion == 'gini':
            return self._gini(y)
        else:
            raise ValueError(f"Critère inconnu: {self.criterion}")
    
    def _information_gain(self, y: np.ndarray, y_left: np.ndarray, y_right: np.ndarray) -> float:
        """
        Calcule le gain d'information après une division
        
        Formule: IG = Impurity(parent) - (n_left/n) * Impurity(left) - (n_right/n) * Impurity(right)
        
        Args:
            y: Labels parent
            y_left: Labels enfant gauche
            y_right: Labels enfant droit
            
        Returns:
            Gain d'information
        """
        n = len(y)
        n_left = len(y_left)
        n_right = len(y_right)
        
        if n_left == 0 or n_right == 0:
            return 0.0
        
        impurity_parent = self._impurity(y)
        impurity_left = self._impurity(y_left)
        impurity_right = self._impurity(y_right)
        
        weighted_impurity = (n_left / n) * impurity_left + (n_right / n) * impurity_right
        
        gain = impurity_parent - weighted_impurity
        
        return gain
    
    def _best_split(self, X: np.ndarray, y: np.ndarray) -> Tuple[Optional[int], Optional[float]]:
        """
        Trouve le meilleur attribut et seuil pour la division
        
        Args:
            X: Features
            y: Labels
            
        Returns:
            Tuple (feature_index, threshold)
        """
        best_gain = -1
        best_feature = None
        best_threshold = None
        
        n_samples, n_features = X.shape
        
        # Pour chaque feature
        for feature_idx in range(n_features):
            feature_values = X[:, feature_idx]
            
            # Obtenir les valeurs uniques triées
            unique_values = np.unique(feature_values)
            
            # Essayer chaque seuil possible (milieu entre valeurs consécutives)
            for i in range(len(unique_values) - 1):
                threshold = (unique_values[i] + unique_values[i + 1]) / 2
                
                # Diviser les données
                left_idx = feature_values <= threshold
                right_idx = feature_values > threshold
                
                # Vérifier les conditions minimales
                if (np.sum(left_idx) < self.min_samples_leaf or 
                    np.sum(right_idx) < self.min_samples_leaf):
                    continue
                
                # Calculer le gain d'information
                gain = self._information_gain(y, y[left_idx], y[right_idx])
                
                if gain > best_gain:
                    best_gain = gain
                    best_feature = feature_idx
                    best_threshold = threshold
        
        return best_feature, best_threshold
    
    def _build_tree(self, X: np.ndarray, y: np.ndarray, depth: int = 0) -> Node:
        """
        Construit récursivement l'arbre de décision
        
        Args:
            X: Features
            y: Labels
            depth: Profondeur actuelle
            
        Returns:
            Nœud de l'arbre
        """
        n_samples, n_features = X.shape
        n_classes = len(np.unique(y))
        
        # Conditions d'arrêt
        if (depth >= self.max_depth or 
            n_samples < self.min_samples_split or 
            n_classes == 1):
            # Créer une feuille avec la classe majoritaire
            unique, counts = np.unique(y, return_counts=True)
            leaf_value = unique[np.argmax(counts)]
            return Node(value=leaf_value)
        
        # Trouver la meilleure division
        best_feature, best_threshold = self._best_split(X, y)
        
        # Si aucune division n'améliore, créer une feuille
        if best_feature is None:
            unique, counts = np.unique(y, return_counts=True)
            leaf_value = unique[np.argmax(counts)]
            return Node(value=leaf_value)
        
        # Diviser les données
        left_idx = X[:, best_feature] <= best_threshold
        right_idx = X[:, best_feature] > best_threshold
        
        # Construire récursivement les sous-arbres
        left_subtree = self._build_tree(X[left_idx], y[left_idx], depth + 1)
        right_subtree = self._build_tree(X[right_idx], y[right_idx], depth + 1)
        
        # Créer le nœud de décision
        return Node(
            feature=best_feature,
            threshold=best_threshold,
            left=left_subtree,
            right=right_subtree
        )
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'DecisionTree':
        """
        Entraîne l'arbre de décision
        
        Args:
            X: Features d'entraînement (n_samples, n_features)
            y: Labels d'entraînement (n_samples,)
            
        Returns:
            self: Le modèle entraîné
        """
        start_time = time.time()
        
        # Vérifier les données
        X = np.array(X)
        y = np.array(y)
        
        if len(X) != len(y):
            raise ValueError("X et y doivent avoir le même nombre d'échantillons")
        
        # Convertir les labels en entiers
        self.classes_ = np.unique(y)
        self.n_classes = len(self.classes_)
        self.n_features = X.shape[1]
        
        # Construire l'arbre
        self.tree = self._build_tree(X, y)
        self.is_trained = True
        
        self.training_time = time.time() - start_time
        
        return self
    
    def _predict_one(self, x: np.ndarray, node: Node) -> int:
        """
        Prédit pour un seul échantillon en parcourant l'arbre
        
        Args:
            x: Un échantillon
            node: Nœud actuel
            
        Returns:
            Classe prédite
        """
        if node.is_leaf:
            return node.value
        
        if x[node.feature] <= node.threshold:
            return self._predict_one(x, node.left)
        else:
            return self._predict_one(x, node.right)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Prédit les labels pour les données fournies
        
        Args:
            X: Features (n_samples, n_features)
            
        Returns:
            Prédictions (n_samples,)
        """
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné. Appelez fit() d'abord.")
        
        X = np.array(X)
        
        start_time = time.time()
        predictions = np.array([self._predict_one(x, self.tree) for x in X])
        self.prediction_time = time.time() - start_time
        
        return predictions
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Prédit les probabilités pour les données fournies
        (Basé sur la distribution des classes dans la feuille)
        
        Args:
            X: Features (n_samples, n_features)
            
        Returns:
            Probabilités (n_samples, n_classes)
        """
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné. Appelez fit() d'abord.")
        
        # Pour un arbre de décision, la probabilité est basée sur la distribution
        # des classes dans la feuille. Cette implémentation est simplifiée.
        predictions = self.predict(X)
        proba = np.zeros((len(X), self.n_classes))
        
        for i, pred in enumerate(predictions):
            proba[i, pred] = 1.0
        
        return proba
    
    def get_feature_importance(self, feature_names: List[str] = None) -> Dict[str, float]:
        """
        Calcule l'importance des features basée sur la réduction d'impureté
        
        Returns:
            Dictionnaire feature -> importance
        """
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné")
        
        importance = np.zeros(self.n_features)
        
        def _compute_importance(node: Node, parent_impurity: float = None, parent_samples: int = None):
            if node.is_leaf:
                return
            
            # Récupérer les données pour calculer l'impureté
            # (Cette partie nécessite de stocker les données pendant l'entraînement)
            # Pour simplifier, nous utilisons une approximation
            # Dans une implémentation complète, il faudrait stocker les statistiques
            
            # Approximation : plus la feature est utilisée près de la racine, plus elle est importante
            importance[node.feature] += 1
            
            if node.left:
                _compute_importance(node.left)
            if node.right:
                _compute_importance(node.right)
        
        _compute_importance(self.tree)
        
        # Normaliser les importances
        if np.sum(importance) > 0:
            importance = importance / np.sum(importance)
        
        if feature_names:
            return {feature_names[i]: importance[i] for i in range(self.n_features)}
        else:
            return {f"feature_{i}": importance[i] for i in range(self.n_features)}
    
    def print_tree(self, node: Node = None, depth: int = 0):
        """
        Affiche la structure de l'arbre de décision
        
        Args:
            node: Nœud courant
            depth: Profondeur actuelle
        """
        if node is None:
            node = self.tree
        
        indent = "  " * depth
        
        if node.is_leaf:
            print(f"{indent}└── Feuille: Classe = {node.value}")
        else:
            print(f"{indent}├── Feature {node.feature} <= {node.threshold:.4f}")
            self.print_tree(node.left, depth + 1)
            print(f"{indent}└── Feature {node.feature} > {node.threshold:.4f}")
            self.print_tree(node.right, depth + 1)