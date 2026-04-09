"""
Logistic Regression - Régression Logistique from scratch
AutoStockCheck - ECU Worldwide
"""

import numpy as np
import time
from typing import Dict, Any, Optional, Tuple
from .base_model import BaseModel


class LogisticRegression(BaseModel):
    """
    Régression Logistique implémentée from scratch pour la classification binaire
    
    Paramètres:
        learning_rate: Taux d'apprentissage pour la descente de gradient
        n_iterations: Nombre d'itérations d'entraînement
        regularization: Type de régularisation ('l1', 'l2', 'none')
        C: Inverse de la force de régularisation (1/lambda)
        tol: Tolérance pour la convergence
        batch_size: Taille du batch pour la descente de gradient stochastique
        verbose: Afficher la progression de l'entraînement
    """
    
    def __init__(self, learning_rate: float = 0.01, n_iterations: int = 1000,
                 regularization: str = 'l2', C: float = 1.0, tol: float = 1e-4,
                 batch_size: int = None, verbose: bool = False):
        """
        Initialisation de la régression logistique
        """
        super().__init__(name="LogisticRegression")
        
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations
        self.regularization = regularization
        self.C = C
        self.tol = tol
        self.batch_size = batch_size
        self.verbose = verbose
        
        self.weights = None
        self.bias = None
        self.loss_history = []
        
        # Enregistrement des paramètres
        self.params = {
            'learning_rate': learning_rate,
            'n_iterations': n_iterations,
            'regularization': regularization,
            'C': C,
            'tol': tol,
            'batch_size': batch_size
        }
    
    def _sigmoid(self, z: np.ndarray) -> np.ndarray:
        """
        Fonction sigmoïde
        
        Formule: σ(z) = 1 / (1 + e^(-z))
        
        Args:
            z: Valeurs d'entrée
            
        Returns:
            Valeurs après sigmoïde (entre 0 et 1)
        """
        # Éviter les overflow
        z = np.clip(z, -500, 500)
        return 1 / (1 + np.exp(-z))
    
    def _binary_cross_entropy(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """
        Calcule la perte de cross-entropy binaire
        
        Formule: L = -1/n * ∑ [y * log(ŷ) + (1-y) * log(1-ŷ)]
        
        Args:
            y_true: Labels réels (0 ou 1)
            y_pred: Probabilités prédites
            
        Returns:
            Valeur de la perte
        """
        # Ajouter un petit epsilon pour éviter log(0)
        epsilon = 1e-10
        y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
        
        n = len(y_true)
        loss = -1/n * np.sum(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))
        
        return loss
    
    def _regularization_loss(self, weights: np.ndarray) -> float:
        """
        Calcule le terme de régularisation
        
        Args:
            weights: Poids du modèle
            
        Returns:
            Valeur de la régularisation
        """
        lambda_reg = 1 / self.C if self.C > 0 else 0
        
        if self.regularization == 'l2':
            # L2: λ * ||w||²
            return lambda_reg * np.sum(weights ** 2)
        
        elif self.regularization == 'l1':
            # L1: λ * |w|
            return lambda_reg * np.sum(np.abs(weights))
        
        else:
            return 0.0
    
    def _gradient(self, X: np.ndarray, y_true: np.ndarray, y_pred: np.ndarray) -> Tuple[np.ndarray, float]:
        """
        Calcule le gradient des poids et du biais
        
        Args:
            X: Features
            y_true: Labels réels
            y_pred: Probabilités prédites
            
        Returns:
            Tuple (gradient_weights, gradient_bias)
        """
        n = len(X)
        error = y_pred - y_true
        
        # Gradient du biais
        gradient_bias = np.sum(error) / n
        
        # Gradient des poids
        gradient_weights = np.dot(X.T, error) / n
        
        # Ajouter la régularisation
        lambda_reg = 1 / self.C if self.C > 0 else 0
        
        if self.regularization == 'l2':
            gradient_weights += 2 * lambda_reg * self.weights
        
        elif self.regularization == 'l1':
            gradient_weights += lambda_reg * np.sign(self.weights)
        
        return gradient_weights, gradient_bias
    
    def _compute_loss(self, X: np.ndarray, y_true: np.ndarray) -> float:
        """
        Calcule la perte totale (cross-entropy + régularisation)
        
        Args:
            X: Features
            y_true: Labels réels
            
        Returns:
            Valeur de la perte
        """
        z = np.dot(X, self.weights) + self.bias
        y_pred = self._sigmoid(z)
        
        loss = self._binary_cross_entropy(y_true, y_pred)
        loss += self._regularization_loss(self.weights)
        
        return loss
    
    def _gradient_descent(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Descente de gradient classique (batch)
        
        Args:
            X: Features d'entraînement
            y: Labels d'entraînement
        """
        n = len(X)
        
        for i in range(self.n_iterations):
            # Forward pass
            z = np.dot(X, self.weights) + self.bias
            y_pred = self._sigmoid(z)
            
            # Calculer la perte
            loss = self._compute_loss(X, y)
            self.loss_history.append(loss)
            
            # Vérifier la convergence
            if i > 0 and abs(self.loss_history[-2] - loss) < self.tol:
                if self.verbose:
                    print(f"Convergence atteinte à l'itération {i}")
                break
            
            # Gradient descent
            gradient_weights, gradient_bias = self._gradient(X, y, y_pred)
            
            # Mise à jour des paramètres
            self.weights -= self.learning_rate * gradient_weights
            self.bias -= self.learning_rate * gradient_bias
            
            # Afficher la progression
            if self.verbose and (i + 1) % 100 == 0:
                print(f"Itération {i+1}/{self.n_iterations}, Loss: {loss:.6f}")
    
    def _stochastic_gradient_descent(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Descente de gradient stochastique (SGD)
        
        Args:
            X: Features d'entraînement
            y: Labels d'entraînement
        """
        n = len(X)
        
        # Déterminer la taille du batch
        batch_size = self.batch_size if self.batch_size else 32
        
        for i in range(self.n_iterations):
            # Mélanger les données
            indices = np.random.permutation(n)
            X_shuffled = X[indices]
            y_shuffled = y[indices]
            
            # Minibatch SGD
            for j in range(0, n, batch_size):
                X_batch = X_shuffled[j:j + batch_size]
                y_batch = y_shuffled[j:j + batch_size]
                
                # Forward pass
                z = np.dot(X_batch, self.weights) + self.bias
                y_pred = self._sigmoid(z)
                
                # Gradient descent
                gradient_weights, gradient_bias = self._gradient(X_batch, y_batch, y_pred)
                
                # Mise à jour des paramètres
                self.weights -= self.learning_rate * gradient_weights
                self.bias -= self.learning_rate * gradient_bias
            
            # Calculer la perte pour le suivi
            loss = self._compute_loss(X, y)
            self.loss_history.append(loss)
            
            # Vérifier la convergence
            if i > 0 and abs(self.loss_history[-2] - loss) < self.tol:
                if self.verbose:
                    print(f"Convergence atteinte à l'itération {i}")
                break
            
            # Afficher la progression
            if self.verbose and (i + 1) % 100 == 0:
                print(f"Itération {i+1}/{self.n_iterations}, Loss: {loss:.6f}")
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'LogisticRegression':
        """
        Entraîne la régression logistique
        
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
        
        # Initialiser les paramètres
        n_samples, n_features = X.shape
        self.weights = np.zeros(n_features)
        self.bias = 0.0
        
        self.classes_ = np.unique(y)
        self.n_classes = len(self.classes_)
        self.n_features = n_features
        
        # Convertir les labels en 0/1 si nécessaire
        if set(y) == {0, 1}:
            pass
        elif set(y) == {-1, 1}:
            y = (y + 1) / 2
        else:
            # Réencoder les labels
            y = (y == self.classes_[1]).astype(int)
        
        # Choix de la méthode d'optimisation
        if self.batch_size is not None:
            # Utiliser SGD
            self._stochastic_gradient_descent(X, y)
        else:
            # Utiliser batch gradient descent
            self._gradient_descent(X, y)
        
        self.is_trained = True
        self.training_time = time.time() - start_time
        
        return self
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Prédit les probabilités pour les données fournies
        
        Args:
            X: Features (n_samples, n_features)
            
        Returns:
            Probabilités (n_samples, 2)
        """
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné. Appelez fit() d'abord.")
        
        X = np.array(X)
        
        start_time = time.time()
        z = np.dot(X, self.weights) + self.bias
        proba_1 = self._sigmoid(z)
        proba_0 = 1 - proba_1
        self.prediction_time = time.time() - start_time
        
        return np.column_stack([proba_0, proba_1])
    
    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """
        Prédit les labels pour les données fournies
        
        Args:
            X: Features (n_samples, n_features)
            threshold: Seuil de classification
            
        Returns:
            Prédictions (n_samples,)
        """
        proba = self.predict_proba(X)
        return (proba[:, 1] >= threshold).astype(int)
    
    def predict_log_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Prédit les log-probabilités
        
        Args:
            X: Features (n_samples, n_features)
            
        Returns:
            Log-probabilités (n_samples, 2)
        """
        proba = self.predict_proba(X)
        return np.log(proba + 1e-10)
    
    def decision_function(self, X: np.ndarray) -> np.ndarray:
        """
        Retourne la fonction de décision (z = w·x + b)
        
        Args:
            X: Features (n_samples, n_features)
            
        Returns:
            Scores de décision (n_samples,)
        """
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné")
        
        return np.dot(X, self.weights) + self.bias
    
    def get_coefficients(self) -> Dict[str, Any]:
        """
        Retourne les coefficients du modèle
        
        Returns:
            Dictionnaire contenant les poids et le biais
        """
        return {
            'weights': self.weights,
            'bias': self.bias,
            'intercept': self.bias
        }
    
    def get_loss_history(self) -> list:
        """
        Retourne l'historique des pertes pendant l'entraînement
        
        Returns:
            Liste des pertes
        """
        return self.loss_history
    
    def plot_loss_curve(self, save_path: str = None):
        """
        Affiche la courbe de perte pendant l'entraînement
        
        Args:
            save_path: Chemin pour sauvegarder la figure
        """
        try:
            import matplotlib.pyplot as plt
            
            plt.figure(figsize=(10, 6))
            plt.plot(self.loss_history)
            plt.title(f'Courbe de perte - {self.name}')
            plt.xlabel('Itération')
            plt.ylabel('Perte (Cross-Entropy)')
            plt.grid(True, alpha=0.3)
            
            if save_path:
                plt.savefig(save_path)
                print(f"✅ Figure sauvegardée: {save_path}")
            else:
                plt.show()
                
        except ImportError:
            print("⚠️ Matplotlib non installé")
    
    def __str__(self) -> str:
        """
        Représentation textuelle du modèle
        """
        return f"LogisticRegression(lr={self.learning_rate}, reg={self.regularization})"