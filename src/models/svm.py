"""
SVM - Support Vector Machine from scratch
AutoStockCheck - ECU Worldwide
"""

import numpy as np
import time
from typing import Dict, Any, Optional, Tuple
from .base_model import BaseModel


class SVM(BaseModel):
    """
    Support Vector Machine implémentée from scratch pour la classification binaire
    
    Paramètres:
        learning_rate: Taux d'apprentissage pour la descente de gradient
        lambda_param: Paramètre de régularisation (C = 1/lambda)
        n_iterations: Nombre d'itérations d'entraînement
        kernel: Type de noyau ('linear', 'poly', 'rbf', 'sigmoid')
        degree: Degré pour le noyau polynomial
        gamma: Paramètre gamma pour les noyaux RBF et polynomial
        coef0: Coefficient pour le noyau polynomial et sigmoïde
        tol: Tolérance pour la convergence
        verbose: Afficher la progression de l'entraînement
    """
    
    def __init__(self, learning_rate: float = 0.001, lambda_param: float = 0.01,
                 n_iterations: int = 1000, kernel: str = 'linear',
                 degree: int = 3, gamma: float = None, coef0: float = 0.0,
                 tol: float = 1e-4, verbose: bool = False):
        """
        Initialisation du SVM
        """
        super().__init__(name="SVM")
        
        self.learning_rate = learning_rate
        self.lambda_param = lambda_param
        self.n_iterations = n_iterations
        self.kernel = kernel
        self.degree = degree
        self.gamma = gamma
        self.coef0 = coef0
        self.tol = tol
        self.verbose = verbose
        
        self.weights = None
        self.bias = 0.0  # Initialiser bias à 0
        self.X_train = None
        self.y_train = None
        self.alpha = None
        self.support_vectors = None
        self.support_vector_labels = None
        self.loss_history = []
        
        # Enregistrement des paramètres
        self.params = {
            'learning_rate': learning_rate,
            'lambda_param': lambda_param,
            'n_iterations': n_iterations,
            'kernel': kernel,
            'degree': degree,
            'gamma': gamma,
            'coef0': coef0
        }
    
    def _kernel_function(self, x1: np.ndarray, x2: np.ndarray) -> float:
        """
        Calcule la valeur du noyau entre deux vecteurs
        """
        if self.kernel == 'linear':
            return np.dot(x1, x2)
        
        elif self.kernel == 'poly':
            gamma = self.gamma if self.gamma is not None else 1.0 / x1.shape[0]
            return (gamma * np.dot(x1, x2) + self.coef0) ** self.degree
        
        elif self.kernel == 'rbf':
            gamma = self.gamma if self.gamma is not None else 1.0 / x1.shape[0]
            diff = x1 - x2
            return np.exp(-gamma * np.dot(diff, diff))
        
        elif self.kernel == 'sigmoid':
            gamma = self.gamma if self.gamma is not None else 1.0 / x1.shape[0]
            return np.tanh(gamma * np.dot(x1, x2) + self.coef0)
        
        else:
            raise ValueError(f"Noyau inconnu: {self.kernel}")
    
    def _kernel_matrix(self, X: np.ndarray, Z: np.ndarray = None) -> np.ndarray:
        """
        Calcule la matrice de noyau
        """
        if Z is None:
            Z = X
        
        n_samples_X = X.shape[0]
        n_samples_Z = Z.shape[0]
        K = np.zeros((n_samples_X, n_samples_Z))
        
        for i in range(n_samples_X):
            for j in range(n_samples_Z):
                K[i, j] = self._kernel_function(X[i], Z[j])
        
        return K
    
    def _hinge_loss(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """
        Calcule la perte hinge
        """
        return np.maximum(0, 1 - y_true * y_pred)
    
    def _objective(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        Calcule la fonction objectif du SVM (primal)
        """
        n = len(X)
        predictions = self._decision_function_linear(X)
        hinge = self._hinge_loss(y, predictions)
        
        reg = 0.5 * np.dot(self.weights, self.weights)
        C = 1 / self.lambda_param if self.lambda_param > 0 else 1
        loss = C * np.sum(hinge) / n
        
        return reg + loss
    
    def _gradient(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Calcule le gradient des poids et du biais (primal)
        """
        n = len(X)
        predictions = self._decision_function_linear(X)
        
        margin = y * predictions
        mask = margin < 1
        
        gradient_weights = self.lambda_param * self.weights
        if np.any(mask):
            gradient_weights -= (1 / n) * np.dot(X[mask].T, y[mask])
        
        gradient_bias = 0.0
        if np.any(mask):
            gradient_bias = -(1 / n) * np.sum(y[mask])
        
        return gradient_weights, gradient_bias
    
    def _decision_function_linear(self, X: np.ndarray) -> np.ndarray:
        """
        Fonction de décision pour noyau linéaire
        """
        return np.dot(X, self.weights) + self.bias
    
    def _fit_linear(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Entraîne le SVM avec noyau linéaire (primal)
        """
        n_samples, n_features = X.shape
        self.weights = np.zeros(n_features)
        self.bias = 0.0
        
        for i in range(self.n_iterations):
            # Calculer les prédictions
            predictions = self._decision_function_linear(X)
            
            # Calculer la perte hinge
            hinge_loss = self._hinge_loss(y, predictions)
            current_loss = np.mean(hinge_loss)
            self.loss_history.append(current_loss)
            
            # Vérifier la convergence
            if i > 0 and abs(self.loss_history[-2] - self.loss_history[-1]) < self.tol:
                if self.verbose:
                    print(f"Convergence atteinte à l'itération {i}")
                break
            
            # Calculer le gradient
            gradient_weights, gradient_bias = self._gradient(X, y)
            
            # Mise à jour des paramètres
            self.weights -= self.learning_rate * gradient_weights
            self.bias -= self.learning_rate * gradient_bias
            
            # Afficher la progression
            if self.verbose and (i + 1) % 100 == 0:
                obj = self._objective(X, y)
                print(f"Itération {i+1}/{self.n_iterations}, Objective: {obj:.6f}")
    
    def _decision_function_kernel(self, X: np.ndarray) -> np.ndarray:
        """
        Fonction de décision pour noyau (dual)
        """
        if self.support_vectors is None:
            raise ValueError("Support vectors non initialisés")
        
        K = self._kernel_matrix(self.support_vectors, X)
        return np.dot(self.alpha * self.support_vector_labels, K) + self.bias
    
    def _fit_kernel(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Entraîne le SVM avec noyau (dual)
        """
        n_samples = X.shape[0]
        self.alpha = np.zeros(n_samples)
        self.bias = 0.0  # Initialiser le biais
        self.X_train = X
        self.y_train = y
        
        C = 1 / self.lambda_param if self.lambda_param > 0 else 1
        
        # Calculer la matrice de noyau
        K = self._kernel_matrix(X)
        
        for i in range(self.n_iterations):
            # Calculer les prédictions
            predictions = np.zeros(n_samples)
            for j in range(n_samples):
                predictions[j] = np.sum(self.alpha * y * K[j, :]) + self.bias
            
            # Mise à jour des coefficients alpha
            for j in range(n_samples):
                if y[j] * predictions[j] < 1:
                    self.alpha[j] += self.learning_rate * (1 - y[j] * predictions[j])
                
                # Projection sur la boîte [0, C]
                self.alpha[j] = np.clip(self.alpha[j], 0, C)
            
            # Mise à jour du biais
            self.bias = 0.0
            for j in range(n_samples):
                self.bias += y[j] - np.sum(self.alpha * y * K[j, :])
            self.bias /= n_samples
            
            # Calculer la perte
            loss = np.sum(self._hinge_loss(y, predictions))
            self.loss_history.append(loss / n_samples)
            
            # Vérifier la convergence
            if i > 0 and abs(self.loss_history[-2] - self.loss_history[-1]) < self.tol:
                if self.verbose:
                    print(f"Convergence atteinte à l'itération {i}")
                break
            
            if self.verbose and (i + 1) % 100 == 0:
                print(f"Itération {i+1}/{self.n_iterations}, Loss: {self.loss_history[-1]:.6f}")
        
        # Identifier les vecteurs supports
        support_idx = self.alpha > 1e-5
        self.support_vectors = X[support_idx]
        self.support_vector_labels = y[support_idx]
        self.alpha = self.alpha[support_idx]
        
        if self.verbose:
            print(f"   Nombre de vecteurs supports: {len(self.support_vectors)}")
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'SVM':
        """
        Entraîne le SVM
        """
        start_time = time.time()
        
        X = np.array(X)
        y = np.array(y)
        
        if len(X) != len(y):
            raise ValueError("X et y doivent avoir le même nombre d'échantillons")
        
        # Convertir les labels en -1 et 1
        if set(y) == {0, 1}:
            y = np.where(y == 0, -1, 1)
        elif set(y) == {-1, 1}:
            pass
        else:
            classes = np.unique(y)
            y = np.where(y == classes[0], -1, 1)
        
        self.classes_ = np.unique(y)
        self.n_classes = len(self.classes_)
        self.n_features = X.shape[1]
        
        # Configurer gamma par défaut
        if self.gamma is None:
            self.gamma = 1.0 / X.shape[1]
        
        # Choisir la méthode selon le noyau
        if self.kernel == 'linear':
            self._fit_linear(X, y)
        else:
            self._fit_kernel(X, y)
        
        self.is_trained = True
        self.training_time = time.time() - start_time
        
        return self
    
    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """
        Calcule la fonction de décision
        """
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné")
        
        X = np.array(X)
        
        if self.kernel == 'linear':
            return self._decision_function_linear(X)
        else:
            return self._decision_function_kernel(X)
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Prédit les labels pour les données fournies
        """
        scores = self.decision_function(X)
        predictions = np.where(scores >= 0, 1, -1)
        return np.where(predictions == -1, 0, 1)
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Prédit les probabilités approximatives
        """
        scores = self.decision_function(X)
        proba_1 = 1 / (1 + np.exp(-scores))
        proba_0 = 1 - proba_1
        return np.column_stack([proba_0, proba_1])
    
    def get_support_vectors(self) -> np.ndarray:
        """
        Retourne les vecteurs supports
        """
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné")
        
        if self.kernel == 'linear':
            return None
        else:
            return self.support_vectors
    
    def get_weights(self) -> np.ndarray:
        """
        Retourne les poids du modèle (pour noyau linéaire)
        """
        if self.kernel != 'linear':
            raise ValueError("Les poids sont disponibles uniquement pour le noyau linéaire")
        return self.weights
    
    def get_bias(self) -> float:
        """
        Retourne le biais du modèle
        """
        return self.bias
    
    def get_loss_history(self) -> list:
        """
        Retourne l'historique des pertes
        """
        return self.loss_history
    
    def __str__(self) -> str:
        return f"SVM(kernel={self.kernel}, lambda={self.lambda_param})"