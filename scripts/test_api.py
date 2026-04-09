"""
Test de l'API AutoStockCheck
"""

import requests
import json

API_URL = "http://localhost:5000"

def test_health():
    """Test de l'endpoint health"""
    response = requests.get(f"{API_URL}/health")
    print(f"Health: {response.json()}")

def test_predict():
    """Test de prédiction simple"""
    
    # Cas 1: Conforme (pas de manque)
    data_conforme = {
        "facture": {"quantite": 5, "prix": 100},
        "stock": {"quantite": 5, "etat_produit": 0.95}
    }
    
    # Cas 2: Manque
    data_manque = {
        "facture": {"quantite": 5, "prix": 100},
        "stock": {"quantite": 2, "etat_produit": 0.95}
    }
    
    print("=" * 50)
    print("TEST DE L'API")
    print("=" * 50)
    
    print("\n📊 Cas 1: Commande conforme")
    response = requests.post(f"{API_URL}/predict", json=data_conforme)
    print(f"   Réponse: {response.json()}")
    
    print("\n📊 Cas 2: Manque détecté")
    response = requests.post(f"{API_URL}/predict", json=data_manque)
    print(f"   Réponse: {response.json()}")
    
    print("\n✅ Test terminé")

if __name__ == "__main__":
    test_health()
    test_predict()