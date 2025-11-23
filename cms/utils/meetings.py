import requests
import yaml

DIRECTUS_URL = "http://localhost:8055"
TOKEN = "YOUR_TOKEN"

# "Authorization": f"Bearer {TOKEN}",
headers = {
    "Content-Type": "application/json"
}

with open("meetings.yaml", "r") as f:
    data = yaml.safe_load(f)

for meeting in data:
    payload = {
        "year": meeting["year"],
        "place": meeting["place"],
        "date": meeting["date"]
    }

    r = requests.post(
        f"{DIRECTUS_URL}/items/meetings",
        headers=headers,
        json=payload
    )

    if r.status_code in [200, 201]:
        print(f"✔ Caricato meeting {meeting['year']}")
    else:
        print(f"❌ Errore meeting {meeting['year']}: {r.text}")
