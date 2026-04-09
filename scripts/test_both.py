import requests
import json

print("=" * 50)
print("Test 1: API directe (127.0.0.1)")
print("=" * 50)

try:
    r1 = requests.post(
        "http://127.0.0.1:5000/predict",
        json={"facture": {"quantite": 5, "prix": 100}, "stock": {"quantite": 5}},
        timeout=5
    )
    print(f"Status: {r1.status_code}")
    print(f"Response: {json.dumps(r1.json(), indent=2, ensure_ascii=False)}")
except Exception as e:
    print(f"Erreur: {e}")

print("\n" + "=" * 50)
print("Test 2: n8n webhook")
print("=" * 50)

try:
    r2 = requests.post(
        "http://localhost:5678/webhook/api",
        json={"facture": {"quantite": 5, "prix": 100}, "stock": {"quantite": 5}},
        timeout=5
    )
    print(f"Status: {r2.status_code}")
    try:
        print(f"Response: {json.dumps(r2.json(), indent=2, ensure_ascii=False)}")
    except:
        print(f"Response text: {r2.text}")
except Exception as e:
    print(f"Erreur: {e}")
