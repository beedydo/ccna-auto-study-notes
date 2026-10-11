import os
import requests

API_KEY = os.environ["API_KEY"]
url = "https://api.meraki.com/api/v1/organizations"
headers = {"Authorization": f"Bearer {API_KEY}", "Accept": "application/json"}
orgs = requests.get(url, headers=headers, timeout=10).json()
for org in orgs:
    print(org["id"], org["name"])
