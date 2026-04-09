"""
Neural Network - Réseau de neurones from scratch
AutoStockCheck - ECU Worldwide
"""

import numpy as np
import time
from typing import Dict, Any, Optional, List, Tuple
from .base_model import BaseModel


class Layer:
    """
    Couche d'un réseau de neurones
    """
    def __init__(self, n_inputs: int, n_neurons: int, activation: str = 'relu'):
        self.n_inputs = n_inputs
        self.n_neurons = n_neurons
        self.activation = activation
        
        # Initialisation des poids (He initialization)
        self.weights = np.random.randn(n_inputs, n_neurons) * np.sqrt(2.0 / n_inputs)
        self.bias = np.zeros((1, n_neurons))
        
        # Pour la rétropropagation
        self.z = None
        self.a = None
        self.dw = None
        self.db = None
        self.X = None
    
    def forward(self, X: np.ndarray) -> np.ndarray:
        """Propagation avant"""
        self.X = X
        self.z = np.dot(X, self.weights) + self.bias
        
        if self.activation == 'relu':
            self.a = np.maximum(0, self.z)
        elif self.activation == 'sigmoid':
            self.a = 1 / (1 + np.exp(-self.z))
        elif self.activation == 'tanh':
            self.a = np.tanh(self.z)
        else:  # linear
            self.a = self.z
        
        return self.a
    
    def backward(self, da: np.ndarray) -> np.ndarray:
        """Propagation arrière"""
        n_samples = self.X.shape[0]
        
        # Gradient de l'activation
        if self.activation == 'relu':
            dz = da.copy()
            dz[self.z <= 0] = 0
        elif self.activation == 'sigmoid':
            dz = da * self.a * (1 - self.a)
        elif self.activation == 'tanh':
            dz = da * (1 - self.a ** 2)
        else:
            dz = da
        
        # Gradients des poids et biais
        self.dw = np.dot(self.X.T, dz) / n_samples
        self.db = np.sum(dz, axis=0, keepdims=True) / n_samples
        
        # Gradient pour la couche précédente
        dX = np.dot(dz, self.weights.T)
        
        return dX
    
    def update(self, learning_rate: float):
        """Mise à jour des paramètres"""
        self.weights -= learning_rate * self.dw
        self.bias -= learning_rate * self.db


class NeuralNetwork(BaseModel):
    """
    Réseau de neurones implémenté from scratch
    
    Paramètres:
        hidden_layers: Liste du nombre de neurones par couche cachée
        activation: Fonction d'activation ('relu', 'tanh', 'sigmoid')
        output_activation: Activation de sortie ('sigmoid' pour binaire)
        learning_rate: Taux d'apprentissage
        n_iterations: Nombre d'itérations d'entraînement
        batch_size: Taille du batch pour SGD
        verbose: Afficher la progression
    """
    
    def __init__(self, hidden_layers: List[int] = [32, 16], 
                 activation: str = 'relu', output_activation: str = 'sigmoid',
                 learning_rate: float = 0.001, n_iterations: int = 1000,
                 batch_size: int = 32, verbose: bool = False):
        """
        Initialisation du réseau de neurones
        """
        super().__init__(name="NeuralNetwork")
        
        self.hidden_layers = hidden_layers
        self.activation = activation
        self.output_activation = output_activation
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations
        self.batch_size = batch_size
        self.verbose = verbose
        
        self.layers = []
        self.loss_history = []
        
        # Enregistrement des paramètres
        self.params = {
            'hidden_layers': hidden_layers,
            'activation': activation,
            'learning_rate': learning_rate,
            'n_iterations': n_iterations,
            'batch_size': batch_size
        }
    
    def _build_layers(self, n_inputs: int, n_outputs: int):
        """Construit l'architecture du réseau"""
        self.layers = []
        
        # Couches cachées
        prev_neurons = n_inputs
        for n_neurons in self.hidden_layers:
            self.layers.append(Layer(prev_neurons, n_neurons, self.activation))
            prev_neurons = n_neurons
        
        # Couche de sortie
        self.layers.append(Layer(prev_neurons, n_outputs, self.output_activation))
    
    def _binary_cross_entropy(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        """Perte de cross-entropie binaire"""
        epsilon = 1e-10
        y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
        return -np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))
    
    def _compute_loss_gradient(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """Calcule le gradient de la perte"""
        epsilon = 1e-10
        y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
        return -(y_true / y_pred - (1 - y_true) / (1 - y_pred))
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'NeuralNetwork':
        """
        Entraîne le réseau de neurones
        """
        start_time = time.time()
        
        X = np.array(X)
        y = np.array(y).reshape(-1, 1)
        
        n_samples, n_features = X.shape
        n_outputs = 1
        
        # Construire l'architecture
        self._build_layers(n_features, n_outputs)
        
        self.classes_ = np.unique(y.flatten())
        self.n_classes = len(self.classes_)
        self.n_features = n_features
        
        # Entraînement
        for epoch in range(self.n_iterations):
            # Mélanger les données
            indices = np.random.permutation(n_samples)
            X_shuffled = X[indices]
            y_shuffled = y[indices]
            
            epoch_loss = 0
            
            # Mini-batch SGD
            for i in range(0, n_samples, self.batch_size):
                X_batch = X_shuffled[i:i + self.batch_size]
                y_batch = y_shuffled[i:i + self.batch_size]
                
                # Forward pass
                a = X_batch
                for layer in self.layers:
                    a = layer.forward(a)
                y_pred = a
                
                # Calcul de la perte
                loss = self._binary_cross_entropy(y_batch, y_pred)
                epoch_loss += loss * len(X_batch)
                
                # Backward pass - gradient de la perte
                da = self._compute_loss_gradient(y_batch, y_pred)
                
                # Propager à travers les couches (de la sortie vers l'entrée)
                for layer in reversed(self.layers):
                    da = layer.backward(da)
                
                # Mise à jour des paramètres
                for layer in self.layers:
                    layer.update(self.learning_rate)
            
            # Enregistrer la perte
            avg_loss = epoch_loss / n_samples
            self.loss_history.append(avg_loss)
            
            # Vérifier la convergence
            if epoch > 10 and abs(self.loss_history[-2] - avg_loss) < 1e-6:
                if self.verbose:
                    print(f"Convergence à l'époque {epoch}")
                break
            
            # Afficher la progression
            if self.verbose and (epoch + 1) % 100 == 0:
                print(f"Époque {epoch+1}/{self.n_iterations}, Loss: {avg_loss:.6f}")
        
        self.is_trained = True
        self.training_time = time.time() - start_time
        
        return self
    
    def forward(self, X: np.ndarray) -> np.ndarray:
        """Propagation avant complète"""
        a = X
        for layer in self.layers:
            a = layer.forward(a)
        return a
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Prédit les probabilités
        """
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné")
        
        X = np.array(X)
        
        start_time = time.time()
        proba_1 = self.forward(X).flatten()
        proba_0 = 1 - proba_1
        self.prediction_time = time.time() - start_time
        
        return np.column_stack([proba_0, proba_1])
    
    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        """
        Prédit les labels
        """
        proba = self.predict_proba(X)
        return (proba[:, 1] >= threshold).astype(int)
    
    def get_loss_history(self) -> list:
        """Retourne l'historique des pertes"""
        return self.loss_history
    
    def __str__(self) -> str:
        return f"NeuralNetwork(layers={self.hidden_layers}, lr={self.learning_rate})"