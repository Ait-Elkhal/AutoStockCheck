import requests
import json

# URL du webhook
url = "http://localhost:5678/webhook-test/test"

# Donn?es
data = {
    "facture": {"quantite": 5, "prix": 100},
    "stock": {"quantite": 5}
}

# Envoyer la requ?te
response = requests.post(url, json=data)

print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
