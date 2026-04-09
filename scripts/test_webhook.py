import requests
import json

# Test du webhook simple
print("=" * 50)
print("Test 1: Webhook simple")
print("=" * 50)

try:
    response = requests.post(
        "http://localhost:5678/webhook-test/test",
        json={"test": "hello"},
        timeout=5
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Erreur: {e}")

# Test avec l'API
print("\n" + "=" * 50)
print("Test 2: Appel API via n8n")
print("=" * 50)

data = {
    "facture": {"quantite": 5, "prix": 100},
    "stock": {"quantite": 5}
}

try:
    response = requests.post(
        "http://localhost:5678/webhook-test/test",
        json=data,
        timeout=5
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"Erreur: {e}")
