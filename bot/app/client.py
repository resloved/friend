import asyncio
import requests
import os, random

from nio import AsyncClient, MatrixRoom, RoomMessageText, InviteEvent
from nio.exceptions import OlmUnverifiedDeviceError


os.makedirs("./store/", exist_ok=True)
client = AsyncClient(
    f"https://{os.environ['MATRIX_FRIEND_INSTANCE']}",
    f"@{os.environ['MATRIX_FRIEND_USER']}:{os.environ['MATRIX_FRIEND_INSTANCE']}",
    store_path="./store/",
)

recent_messages = {}
ctx_len = 5


async def message_callback(room, event):
    print(f"{room.user_name(event.sender)} - {event.body}")

    if not room.room_id in recent_messages:
        recent_messages[room.room_id] = [{"user": event.sender, "body": event.body}]
    else:
        recent_messages[room.room_id].append({"user": event.sender, "body": event.body})
        if len(recent_messages[room.room_id]) > ctx_len:
            recent_messages[room.room_id].pop(0)

    interact = random.randrange(100) < 1
    if interact or "friend" in event.body and event.sender != client.user:
        await client.room_typing(room.room_id, True)
        result = prompt(
            recent_messages[room.room_id], seperators=["\n"], temperature=0.1
        )
        while result:
            try:
                await client.room_send(
                    room_id=room.room_id,
                    message_type="m.room.message",
                    content={"msgtype": "m.text", "body": result},
                )
                break
            except OlmUnverifiedDeviceError as e:
                print(e)
                client.verify_device(e.device)
        await client.room_typing(room.room_id, False)


async def autojoin_room(room, event):
    print(f"Joining room {room.room_id}")
    await client.join(room.room_id)


def prompt(messages, **kwargs):
    user = messages[-1]["user"]
    agents = {user: "agent_1", client.user: "agent_2"}

    text = "********************"
    for message in messages:
        if not message["user"] in agents:
            agents[message["user"]] = f"agent_{str(len(agents.keys()) + 1)}"
        text += f"\n{agents[message['user']]} <Positive>: {message['body']}"
    text += f"\n{agents[client.user]} <Positive>:"

    text = text.replace("@friend", "friend")

    kwargs["msg"] = text
    try:
        r = requests.post(
            os.getenv("MATRIX_FRIEND_INFERENCE_API", "localhost:8080"),
            json=kwargs,
        )
        return r.text.strip()
    except Exception as e:
        print(e)
        return ""


async def main():
    await client.login(os.environ["MATRIX_FRIEND_PASS"])
    client.load_store()
    client.add_event_callback(autojoin_room, InviteEvent)
    if client.should_upload_keys:
        await client.keys_upload()
    await client.sync(30000)
    client.add_event_callback(message_callback, RoomMessageText)
    await client.sync_forever(30000, full_state=True)


asyncio.get_event_loop().run_until_complete(main())
