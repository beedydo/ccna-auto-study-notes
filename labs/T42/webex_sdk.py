"""T42 SDK version: the core of webex_bot.py with webexpythonsdk (formerly webexteamssdk).

pip install webexpythonsdk      (already in the lab image: labs/requirements.txt)
Run against the mock:   bash labs/T42/run_lab.sh labs/T42/webex_sdk.py
Against real Webex: unset WEBEX_BASE; the SDK defaults to https://webexapis.com/v1/
and reads the token from the WEBEX_ACCESS_TOKEN env var if access_token is not passed.
"""
import os

from webexpythonsdk import WebexAPI
from webexpythonsdk.exceptions import ApiError

api = WebexAPI(access_token=os.environ.get("WEBEX_TOKEN", "T42-mock-bot-token"),
               base_url=os.environ.get("WEBEX_BASE", "http://127.0.0.1:18042/v1") + "/")

me = api.people.me()
print(f"me: {me.displayName} {me.emails} type={me.type}")

for room in api.rooms.list(type="group", max=2):        # generator: follows Link rel="next" for you
    print(f"room: {room.title}")

room = api.rooms.create(title="T42-SDK-Test")
print(f"created: {room.title} type={room.type}")
api.memberships.create(roomId=room.id, personEmail="bob@example.com")
msg = api.messages.create(roomId=room.id, markdown="**SDK** says hi")
print(f"posted: {msg.text!r} to {msg.roomType} room")

try:
    api.memberships.create(roomId=room.id, personEmail="bob@example.com")
except ApiError as err:
    print(f"ApiError: {err.status_code} {err.message}")

api.rooms.delete(room.id)
print("deleted room")
