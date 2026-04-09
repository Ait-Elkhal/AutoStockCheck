import requests
import json

url = "http://localhost:5678/webhook/api"

data = {
    "facture": {"quantite": 5, "prix": 100},
    "stock": {"quantite": 5}
}

print("=" * 50)
print("Test mode production - n8n")
print("=" * 50)
print(f"URL: {url}")
print(f"Data: {json.dumps(data, indent=2)}")
print()

try:
    response = requests.post(url, json=data, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"Erreur: {e}")
