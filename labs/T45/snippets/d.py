import os
import requests

TOKEN = os.environ["TOKEN"]
url = "https://webexapis.com/v1/messages"
headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
body = {"roomId": os.environ["ROOM_ID"], "markdown": "**2 devices unreachable**"}
resp = requests.post(url, headers=headers, json=body, timeout=10)
resp.raise_for_status()
print(resp.json()["id"])
