import asyncio
import os
import requests

from nio import AsyncClient, MatrixRoom, RoomMessageText, InviteEvent
from nio.exceptions import OlmUnverifiedDeviceError

# STORE_FOLDER = "store/"
# SESSION_DETAILS_FILE = "credentials.json"

client = AsyncClient(
    os.environ['MATRIX_FRIEND_INSTANCE'],
    f"@{os.environ['MATRIX_FRIEND_USER']}:{os.environ['MATRIX_FRIEND_INSTANCE']}",
    store_path="./store",
    device_id="bot"
)

async def message_callback(room, event):
    print(f"{room.user_name(event.sender)} - {event.body}")
    trust_all_devices(room.users)
    if "friend" in event.body and event.sender != client.user:
        input = f"{room.user_name(event.sender)} - {event.body}\n@friend - "
        await client.room_typing(room.room_id, True)
        try:
            if output:
                await client.room_send(
                    # Watch out! If you join an old room you'll see lots of old messages
                    room_id=room.room_id,
                    message_type="m.room.message",
                    content = {
                        "msgtype": "m.text",
                        "body": "I'm here!"
                    }
                )
        except OlmUnverifiedDeviceError as e:
            print(e)
        await client.room_typing(room.room_id, False)

async def autojoin_room(room, event):
    await client.join(room.room_id)

def trust_all_devices(users):
    for key in users.keys():
        print(f"TRUSTING {key}")
        trust_devices(key)

def trust_devices(user_id):
        for device_id, olm_device in client.device_store[user_id].items():
            if user_id == client.user_id and device_id == client.device_id:
                continue
            client.verify_device(olm_device)
            print(f"Trusting {device_id} from user {user_id}")

async def main():
    await client.login(os.environ['MATRIX_FRIEND_PASS'])
    client.add_event_callback(autojoin_room, InviteEvent)
    if client.should_upload_keys:
        await client.keys_upload()
    await client.sync(30000)
    client.add_event_callback(message_callback, RoomMessageText)
    await client.sync_forever(30000, full_state=True)

asyncio.get_event_loop().run_until_complete(main())
