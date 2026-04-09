import requests
import json

# Utiliser l'URL de test (copiée depuis n8n)
webhook_url = "http://localhost:5678/webhook-test/apitest"

data = {
    "facture": {"quantite": 5, "prix": 100},
    "stock": {"quantite": 5}
}

print("=" * 50)
print("Test n8n → API Flask")
print("=" * 50)
print(f"Webhook: {webhook_url}")
print(f"Data: {json.dumps(data, indent=2)}")
print()

try:
    response = requests.post(webhook_url, json=data, timeout=10)
    print(f"Status code: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2, ensure_ascii=False)}")
except requests.exceptions.ConnectionError:
    print("❌ Impossible de se connecter à n8n")
    print("   Vérifiez que n8n est démarré sur http://localhost:5678")
except Exception as e:
    print(f"❌ Erreur: {e}")
