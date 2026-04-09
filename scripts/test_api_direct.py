import requests
import json

# URL de l'API
url = "http://localhost:5000/predict"

# Test 1 : Commande conforme
data_conforme = {
    "facture": {"quantite": 5, "prix": 100},
    "stock": {"quantite": 5}
}

print("=" * 50)
print("Test 1: Commande conforme")
print("=" * 50)
response = requests.post(url, json=data_conforme)
print(json.dumps(response.json(), indent=2, ensure_ascii=False))

# Test 2 : Manque détecté
data_manque = {
    "facture": {"quantite": 10, "prix": 50},
    "stock": {"quantite": 3}
}

print("\n" + "=" * 50)
print("Test 2: Manque détecté")
print("=" * 50)
response = requests.post(url, json=data_manque)
print(json.dumps(response.json(), indent=2, ensure_ascii=False))