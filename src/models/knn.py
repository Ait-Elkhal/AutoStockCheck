"""
KNN - K-Nearest Neighbors from scratch
AutoStockCheck - ECU Worldwide
"""

import numpy as np
import time
from typing import Dict, Any, List, Tuple
from collections import Counter
from .base_model import BaseModel


class KNN(BaseModel):
    """
    K-Nearest Neighbors implémenté from scratch pour la classification binaire
    
    Paramètres:
        k: Nombre de voisins à considérer
        distance_metric: Métrique de distance ('euclidean', 'manhattan', 'minkowski')
        weights: Type de pondération ('uniform', 'distance')
        p: Paramètre pour la distance de Minkowski (si distance_metric='minkowski')
    """
    
    def __init__(self, k: int = 5, distance_metric: str = 'euclidean', 
                 weights: str = 'uniform', p: int = 2):
        """
        Initialisation du KNN
        """
        super().__init__(name="KNN")
        
        self.k = k
        self.distance_metric = distance_metric
        self.weights = weights
        self.p = p
        
        self.X_train = None
        self.y_train = None
        
        # Enregistrement des paramètres
        self.params = {
            'k': k,
            'distance_metric': distance_metric,
            'weights': weights,
            'p': p
        }
        
        # Pour optimisations futures (KD-Tree)
        self.use_kdtree = False
        self.kdtree = None
    
    def _euclidean_distance(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Calcule la distance euclidienne entre deux points
        
        Formule: d = √(∑(a_i - b_i)²)
        
        Args:
            a: Premier point
            b: Deuxième point
            
        Returns:
            Distance euclidienne
        """
        return np.sqrt(np.sum((a - b) ** 2))
    
    def _manhattan_distance(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Calcule la distance de Manhattan entre deux points
        
        Formule: d = ∑|a_i - b_i|
        
        Args:
            a: Premier point
            b: Deuxième point
            
        Returns:
            Distance de Manhattan
        """
        return np.sum(np.abs(a - b))
    
    def _minkowski_distance(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Calcule la distance de Minkowski entre deux points
        
        Formule: d = (∑|a_i - b_i|^p)^(1/p)
        
        Args:
            a: Premier point
            b: Deuxième point
            
        Returns:
            Distance de Minkowski
        """
        return np.power(np.sum(np.abs(a - b) ** self.p), 1 / self.p)
    
    def _cosine_distance(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Calcule la distance cosinus entre deux points
        
        Formule: d = 1 - (a·b)/(||a||·||b||)
        
        Args:
            a: Premier point
            b: Deuxième point
            
        Returns:
            Distance cosinus
        """
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 1.0
        
        cosine_similarity = dot_product / (norm_a * norm_b)
        return 1 - cosine_similarity
    
    def _calculate_distance(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Calcule la distance selon la métrique choisie
        
        Args:
            a: Premier point
            b: Deuxième point
            
        Returns:
            Distance calculée
        """
        if self.distance_metric == 'euclidean':
            return self._euclidean_distance(a, b)
        elif self.distance_metric == 'manhattan':
            return self._manhattan_distance(a, b)
        elif self.distance_metric == 'minkowski':
            return self._minkowski_distance(a, b)
        elif self.distance_metric == 'cosine':
            return self._cosine_distance(a, b)
        else:
            raise ValueError(f"Métrique de distance inconnue: {self.distance_metric}")
    
    def _find_neighbors(self, x: np.ndarray) -> List[Tuple[float, int]]:
        """
        Trouve les k plus proches voisins pour un point
        
        Args:
            x: Point à classifier
            
        Returns:
            Liste des (distance, index) des k plus proches voisins
        """
        # Calculer les distances avec tous les points d'entraînement
        distances = []
        for i, x_train in enumerate(self.X_train):
            dist = self._calculate_distance(x, x_train)
            distances.append((dist, i))
        
        # Trier par distance
        distances.sort(key=lambda tup: tup[0])
        
        # Retourner les k plus proches
        return distances[:self.k]
    
    def _get_neighbor_labels(self, neighbors: List[Tuple[float, int]]) -> np.ndarray:
        """
        Récupère les labels des voisins
        
        Args:
            neighbors: Liste des (distance, index) des voisins
            
        Returns:
            Labels des voisins
        """
        return np.array([self.y_train[idx] for _, idx in neighbors])
    
    def _get_weights(self, neighbors: List[Tuple[float, int]]) -> np.ndarray:
        """
        Calcule les poids pour chaque voisin selon la méthode choisie
        
        Args:
            neighbors: Liste des (distance, index) des voisins
            
        Returns:
            Poids pour chaque voisin
        """
        distances = np.array([dist for dist, _ in neighbors])
        
        if self.weights == 'uniform':
            # Poids uniformes
            return np.ones(len(neighbors))
        
        elif self.weights == 'distance':
            # Poids inversement proportionnels à la distance
            # Éviter la division par zéro
            with np.errstate(divide='ignore', invalid='ignore'):
                weights = 1 / (distances + 1e-10)
                weights = np.nan_to_num(weights, nan=0.0, posinf=1.0, neginf=0.0)
            return weights
        
        else:
            raise ValueError(f"Méthode de pondération inconnue: {self.weights}")
    
    def _predict_one(self, x: np.ndarray) -> int:
        """
        Prédit la classe pour un seul point
        
        Args:
            x: Point à classifier
            
        Returns:
            Classe prédite
        """
        # Trouver les k plus proches voisins
        neighbors = self._find_neighbors(x)
        
        # Récupérer les labels et les poids
        labels = self._get_neighbor_labels(neighbors)
        weights = self._get_weights(neighbors)
        
        # Calculer les votes pondérés
        class_votes = {}
        for label, weight in zip(labels, weights):
            class_votes[label] = class_votes.get(label, 0) + weight
        
        # Retourner la classe avec le plus de votes
        return max(class_votes.items(), key=lambda x: x[1])[0]
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'KNN':
        """
        Entraîne le KNN (stockage des données)
        
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
        
        if len(X) < self.k:
            raise ValueError(f"k={self.k} ne peut pas être supérieur au nombre d'échantillons={len(X)}")
        
        # Stocker les données d'entraînement
        self.X_train = X
        self.y_train = y
        
        self.n_features = X.shape[1]
        self.classes_ = np.unique(y)
        self.n_classes = len(self.classes_)
        self.is_trained = True
        
        self.training_time = time.time() - start_time
        
        return self
    
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
        predictions = np.array([self._predict_one(x) for x in X])
        self.prediction_time = time.time() - start_time
        
        return predictions
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Prédit les probabilités pour les données fournies
        (Basé sur la proportion des classes parmi les k plus proches voisins)
        
        Args:
            X: Features (n_samples, n_features)
            
        Returns:
            Probabilités (n_samples, n_classes)
        """
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné. Appelez fit() d'abord.")
        
        X = np.array(X)
        probas = np.zeros((len(X), self.n_classes))
        
        for i, x in enumerate(X):
            neighbors = self._find_neighbors(x)
            labels = self._get_neighbor_labels(neighbors)
            weights = self._get_weights(neighbors)
            
            # Calculer la distribution pondérée
            for label, weight in zip(labels, weights):
                probas[i, label] += weight
            
            # Normaliser
            probas[i] = probas[i] / np.sum(probas[i])
        
        return probas
    
    def get_best_k(self, X_val: np.ndarray, y_val: np.ndarray, 
                   k_range: range = range(1, 31)) -> Tuple[int, float]:
        """
        Trouve la meilleure valeur de k par validation croisée
        
        Args:
            X_val: Données de validation
            y_val: Labels de validation
            k_range: Plage de valeurs de k à tester
            
        Returns:
            Tuple (meilleur_k, meilleure_accuracy)
        """
        best_k = self.k
        best_accuracy = 0
        
        for k in k_range:
            knn = KNN(k=k, distance_metric=self.distance_metric, weights=self.weights)
            knn.fit(self.X_train, self.y_train)
            metrics = knn.evaluate(X_val, y_val)
            
            if metrics['accuracy'] > best_accuracy:
                best_accuracy = metrics['accuracy']
                best_k = k
        
        return best_k, best_accuracy
    
    def get_distance_distribution(self, X: np.ndarray) -> Dict[str, float]:
        """
        Calcule la distribution des distances pour les données
        
        Args:
            X: Données d'entraînement
            
        Returns:
            Dictionnaire des statistiques de distance
        """
        distances = []
        
        for i, x in enumerate(X):
            # Calculer la distance avec tous les autres points
            for j, x_other in enumerate(X):
                if i != j:
                    dist = self._calculate_distance(x, x_other)
                    distances.append(dist)
        
        return {
            'min': np.min(distances),
            'max': np.max(distances),
            'mean': np.mean(distances),
            'std': np.std(distances),
            'median': np.median(distances)
        }
    
    def get_neighbors_analysis(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        Analyse la composition des voisinages
        
        Args:
            X: Données
            y: Labels
            
        Returns:
            Statistiques sur les voisinages
        """
        same_class_count = 0
        total_count = 0
        
        for i, x in enumerate(X):
            neighbors = self._find_neighbors(x)
            labels = self._get_neighbor_labels(neighbors)
            
            # Compter combien de voisins sont de la même classe
            same_class = np.sum(labels == y[i])
            same_class_count += same_class
            total_count += len(neighbors)
        
        return {
            'same_class_ratio': same_class_count / total_count if total_count > 0 else 0,
            'avg_same_class': same_class_count / len(X) if len(X) > 0 else 0
        }
    
    def __str__(self) -> str:
        """
        Représentation textuelle du KNN
        """
        return f"KNN(k={self.k}, metric={self.distance_metric}, weights={self.weights})"