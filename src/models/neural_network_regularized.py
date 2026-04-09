"""
Neural Network with Regularization - Réseau de neurones avec régularisation
AutoStockCheck - ECU Worldwide
"""

import numpy as np
import time
from typing import Dict, Any, Optional, List, Tuple
from .base_model import BaseModel


class RegularizedLayer:
    """
    Couche avec régularisation L2 et Dropout
    """
    def __init__(self, n_inputs: int, n_neurons: int, activation: str = 'relu',
                 dropout_rate: float = 0.0):
        self.n_inputs = n_inputs
        self.n_neurons = n_neurons
        self.activation = activation
        self.dropout_rate = dropout_rate
        
        # Initialisation des poids (He initialization avec moins d'ampleur)
        self.weights = np.random.randn(n_inputs, n_neurons) * np.sqrt(1.0 / n_inputs)
        self.bias = np.zeros((1, n_neurons))
        
        # Pour la rétropropagation
        self.z = None
        self.a = None
        self.dw = None
        self.db = None
        self.X = None
        self.dropout_mask = None
        self.training = True
    
    def forward(self, X: np.ndarray, training: bool = True) -> np.ndarray:
        """Propagation avant avec Dropout"""
        self.training = training
        self.X = X
        self.z = np.dot(X, self.weights) + self.bias
        
        if self.activation == 'relu':
            self.a = np.maximum(0, self.z)
        elif self.activation == 'sigmoid':
            self.a = 1 / (1 + np.exp(-self.z))
        elif self.activation == 'tanh':
            self.a = np.tanh(self.z)
        else:
            self.a = self.z
        
        # Dropout (uniquement pendant l'entraînement)
        if self.training and self.dropout_rate > 0:
            self.dropout_mask = np.random.binomial(1, 1 - self.dropout_rate, size=self.a.shape)
            self.a *= self.dropout_mask
            self.a /= (1 - self.dropout_rate)  # Scale pour compenser
        
        return self.a
    
    def backward(self, da: np.ndarray, lambda_reg: float = 0.0) -> np.ndarray:
        """Propagation arrière avec régularisation L2"""
        n_samples = self.X.shape[0]
        
        # Appliquer le dropout mask au gradient
        if self.training and self.dropout_rate > 0:
            da *= self.dropout_mask
            da /= (1 - self.dropout_rate)
        
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
        
        # Gradients avec régularisation L2
        self.dw = np.dot(self.X.T, dz) / n_samples + lambda_reg * self.weights
        self.db = np.sum(dz, axis=0, keepdims=True) / n_samples
        
        # Gradient pour la couche précédente
        dX = np.dot(dz, self.weights.T)
        
        return dX
    
    def update(self, learning_rate: float):
        """Mise à jour des paramètres"""
        self.weights -= learning_rate * self.dw
        self.bias -= learning_rate * self.db


class RegularizedNeuralNetwork(BaseModel):
    """
    Réseau de neurones avec régularisation (L2 + Dropout)
    Volontairement moins performant pour meilleure généralisation
    """
    
    def __init__(self, hidden_layers: List[int] = [8, 4],  # Moins de neurones
                 activation: str = 'relu', output_activation: str = 'sigmoid',
                 learning_rate: float = 0.01,  # Taux plus élevé
                 n_iterations: int = 200,      # Moins d'itérations
                 batch_size: int = 64,         # Batch plus grand
                 dropout_rate: float = 0.3,    # Dropout pour éviter overfitting
                 lambda_reg: float = 0.01,     # Régularisation L2
                 verbose: bool = False):
        super().__init__(name="RegularizedNeuralNetwork")
        
        self.hidden_layers = hidden_layers
        self.activation = activation
        self.output_activation = output_activation
        self.learning_rate = learning_rate
        self.n_iterations = n_iterations
        self.batch_size = batch_size
        self.dropout_rate = dropout_rate
        self.lambda_reg = lambda_reg
        self.verbose = verbose
        
        self.layers = []
        self.loss_history = []
        self.val_loss_history = []
        
        self.params = {
            'hidden_layers': hidden_layers,
            'activation': activation,
            'learning_rate': learning_rate,
            'n_iterations': n_iterations,
            'dropout_rate': dropout_rate,
            'lambda_reg': lambda_reg
        }
    
    def _build_layers(self, n_inputs: int, n_outputs: int):
        """Construit l'architecture avec Dropout"""
        self.layers = []
        
        prev_neurons = n_inputs
        for n_neurons in self.hidden_layers:
            self.layers.append(RegularizedLayer(
                prev_neurons, n_neurons, self.activation, self.dropout_rate
            ))
            prev_neurons = n_neurons
        
        # Couche de sortie (pas de dropout)
        self.layers.append(RegularizedLayer(
            prev_neurons, n_outputs, self.output_activation, 0.0
        ))
    
    def _binary_cross_entropy(self, y_true: np.ndarray, y_pred: np.ndarray) -> float:
        epsilon = 1e-10
        y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
        return -np.mean(y_true * np.log(y_pred) + (1 - y_true) * np.log(1 - y_pred))
    
    def _compute_loss_gradient(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        epsilon = 1e-10
        y_pred = np.clip(y_pred, epsilon, 1 - epsilon)
        return -(y_true / y_pred - (1 - y_true) / (1 - y_pred))
    
    def _compute_regularization_loss(self) -> float:
        """Calcule la perte de régularisation L2"""
        reg_loss = 0
        for layer in self.layers:
            reg_loss += np.sum(layer.weights ** 2)
        return self.lambda_reg * reg_loss
    
    def fit(self, X: np.ndarray, y: np.ndarray, X_val: np.ndarray = None, 
            y_val: np.ndarray = None) -> 'RegularizedNeuralNetwork':
        """Entraîne avec validation pour détecter overfitting"""
        start_time = time.time()
        
        X = np.array(X)
        y = np.array(y).reshape(-1, 1)
        
        n_samples, n_features = X.shape
        n_outputs = 1
        
        self._build_layers(n_features, n_outputs)
        
        self.classes_ = np.unique(y.flatten())
        self.n_classes = len(self.classes_)
        self.n_features = n_features
        
        # Validation set
        has_validation = X_val is not None and y_val is not None
        if has_validation:
            X_val = np.array(X_val)
            y_val = np.array(y_val).reshape(-1, 1)
        
        for epoch in range(self.n_iterations):
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
                    a = layer.forward(a, training=True)
                y_pred = a
                
                # Calcul de la perte
                loss = self._binary_cross_entropy(y_batch, y_pred)
                loss += self._compute_regularization_loss()
                epoch_loss += loss * len(X_batch)
                
                # Backward pass
                da = self._compute_loss_gradient(y_batch, y_pred)
                for layer in reversed(self.layers):
                    da = layer.backward(da, self.lambda_reg)
                for layer in self.layers:
                    layer.update(self.learning_rate)
            
            avg_loss = epoch_loss / n_samples
            self.loss_history.append(avg_loss)
            
            # Validation loss
            if has_validation and (epoch + 1) % 10 == 0:
                val_pred = self.forward(X_val, training=False)
                val_loss = self._binary_cross_entropy(y_val, val_pred)
                self.val_loss_history.append(val_loss)
                
                # Détection d'overfitting
                if len(self.val_loss_history) > 10:
                    if val_loss > self.val_loss_history[-5]:
                        if self.verbose:
                            print(f"⚠️ Overfitting détecté à l'époque {epoch}")
                        break
            
            if self.verbose and (epoch + 1) % 50 == 0:
                print(f"Époque {epoch+1}/{self.n_iterations}, Loss: {avg_loss:.6f}")
        
        self.is_trained = True
        self.training_time = time.time() - start_time
        
        return self
    
    def forward(self, X: np.ndarray, training: bool = False) -> np.ndarray:
        """Propagation avant (mode évaluation)"""
        a = X
        for layer in self.layers:
            a = layer.forward(a, training=training)
        return a
    
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        if not self.is_trained:
            raise ValueError("Le modèle n'est pas entraîné")
        
        X = np.array(X)
        start_time = time.time()
        proba_1 = self.forward(X, training=False).flatten()
        proba_0 = 1 - proba_1
        self.prediction_time = time.time() - start_time
        
        return np.column_stack([proba_0, proba_1])
    
    def predict(self, X: np.ndarray, threshold: float = 0.5) -> np.ndarray:
        proba = self.predict_proba(X)
        return (proba[:, 1] >= threshold).astype(int)
    
    def get_loss_history(self) -> dict:
        return {'train': self.loss_history, 'val': self.val_loss_history}
    
    def __str__(self) -> str:
        return f"RegularizedNN(layers={self.hidden_layers}, dropout={self.dropout_rate})"