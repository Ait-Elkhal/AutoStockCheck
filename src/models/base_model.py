"""
Base Model - Classe abstraite pour tous les modèles ML
AutoStockCheck - ECU Worldwide
"""

import numpy as np
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple, Optional
import pickle
import os


class BaseModel(ABC):
    """
    Classe abstraite définissant l'interface commune à tous les modèles
    Tous les modèles ML développés from scratch doivent hériter de cette classe
    """
    
    def __init__(self, name: str = "BaseModel"):
        """
        Initialisation du modèle de base
        
        Args:
            name: Nom du modèle
        """
        self.name = name
        self.is_trained = False
        self.training_time = None
        self.prediction_time = None
        self.metrics = {
            'accuracy': None,
            'precision': None,
            'recall': None,
            'f1_score': None,
            'confusion_matrix': None
        }
        self.params = {}
        self.feature_importance = None
        
    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'BaseModel':
        """
        Entraîne le modèle sur les données d'entraînement
        
        Args:
            X: Features d'entraînement (n_samples, n_features)
            y: Labels d'entraînement (n_samples,)
            
        Returns:
            self: Le modèle entraîné
        """
        pass
    
    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Prédit les labels pour les données fournies
        
        Args:
            X: Features (n_samples, n_features)
            
        Returns:
            Prédictions (n_samples,)
        """
        pass
    
    @abstractmethod
    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Prédit les probabilités pour les données fournies
        
        Args:
            X: Features (n_samples, n_features)
            
        Returns:
            Probabilités (n_samples, n_classes)
        """
        pass
    
    def evaluate(self, X: np.ndarray, y: np.ndarray) -> Dict[str, float]:
        """
        Évalue les performances du modèle sur les données de test
        
        Args:
            X: Features de test
            y: Labels de test
            
        Returns:
            Dictionnaire contenant les métriques d'évaluation
        """
        start_time = time.time()
        y_pred = self.predict(X)
        self.prediction_time = time.time() - start_time
        
        # Calcul des métriques
        self.metrics = self._calculate_metrics(y, y_pred)
        
        return self.metrics
    
    def _calculate_metrics(self, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
        """
        Calcule les métriques de classification
        
        Args:
            y_true: Labels réels
            y_pred: Labels prédits
            
        Returns:
            Dictionnaire des métriques
        """
        # Matrice de confusion
        cm = self._confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel()
        
        # Calcul des métriques
        accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'confusion_matrix': cm.tolist()
        }
    
    def _confusion_matrix(self, y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """
        Calcule la matrice de confusion from scratch
        
        Args:
            y_true: Labels réels
            y_pred: Labels prédits
            
        Returns:
            Matrice de confusion 2x2
        """
        # Initialiser la matrice 2x2
        cm = np.zeros((2, 2), dtype=int)
        
        for i in range(len(y_true)):
            cm[int(y_true[i])][int(y_pred[i])] += 1
            
        return cm
    
    def get_params(self) -> Dict[str, Any]:
        """
        Retourne les paramètres du modèle
        
        Returns:
            Dictionnaire des paramètres
        """
        return self.params
    
    def set_params(self, **params):
        """
        Définit les paramètres du modèle
        
        Args:
            **params: Paramètres à définir
        """
        for key, value in params.items():
            if key in self.params:
                self.params[key] = value
        return self
    
    def get_metrics(self) -> Dict[str, float]:
        """
        Retourne les métriques du modèle
        
        Returns:
            Dictionnaire des métriques
        """
        return self.metrics
    
    def get_training_time(self) -> float:
        """
        Retourne le temps d'entraînement
        
        Returns:
            Temps d'entraînement en secondes
        """
        return self.training_time
    
    def get_prediction_time(self) -> float:
        """
        Retourne le temps de prédiction
        
        Returns:
            Temps de prédiction en secondes
        """
        return self.prediction_time
    
    def save(self, filepath: str) -> None:
        """
        Sauvegarde le modèle dans un fichier
        
        Args:
            filepath: Chemin du fichier de sauvegarde
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'wb') as f:
            pickle.dump(self, f)
        print(f"✅ Modèle sauvegardé : {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'BaseModel':
        """
        Charge un modèle depuis un fichier
        
        Args:
            filepath: Chemin du fichier à charger
            
        Returns:
            Modèle chargé
        """
        with open(filepath, 'rb') as f:
            model = pickle.load(f)
        print(f"✅ Modèle chargé : {filepath}")
        return model
    
    def __str__(self) -> str:
        """
        Représentation textuelle du modèle
        """
        return f"{self.name} (entraîné: {self.is_trained})"
    
    def summary(self) -> str:
        """
        Affiche un résumé complet du modèle
        """
        separator = "=" * 50
        summary = f"\n{separator}\n"
        summary += f"📊 RÉSUMÉ DU MODÈLE : {self.name}\n"
        summary += f"{separator}\n"
        summary += f"État          : {'Entraîné' if self.is_trained else 'Non entraîné'}\n"
        
        if self.training_time:
            summary += f"Temps entraînement : {self.training_time:.4f} secondes\n"
        if self.prediction_time:
            summary += f"Temps prédiction   : {self.prediction_time:.4f} secondes\n"
        
        if self.metrics and self.metrics['accuracy'] is not None:
            summary += f"\n📈 PERFORMANCES :\n"
            summary += f"  Accuracy  : {self.metrics['accuracy']:.4f}\n"
            summary += f"  Precision : {self.metrics['precision']:.4f}\n"
            summary += f"  Recall    : {self.metrics['recall']:.4f}\n"
            summary += f"  F1-Score  : {self.metrics['f1_score']:.4f}\n"
            
            cm = self.metrics['confusion_matrix']
            if cm:
                summary += f"\n📊 MATRICE DE CONFUSION :\n"
                summary += f"            Prédit\n"
                summary += f"           Conforme  Manque\n"
                summary += f"  Réel   Conforme   {cm[0][0]:>6}   {cm[0][1]:>6}\n"
                summary += f"        Manque      {cm[1][0]:>6}   {cm[1][1]:>6}\n"
        
        summary += f"{separator}\n"
        return summary