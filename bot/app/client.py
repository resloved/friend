import asyncio
import requests
import os, random

import logging

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from nio import AsyncClient, MatrixRoom, RoomMessageText, InviteEvent
from nio.exceptions import OlmUnverifiedDeviceError

logging.basicConfig(
    format='%(asctime)s [%(name)s] %(levelname)s >> %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=getattr(logging, os.getenv("MATRIX_FRIEND_LOGGING_LEVEL", "DEBUG").upper())
)

MATRIX_FRIEND_INSTANCE = os.getenv("MATRIX_FRIEND_INSTANCE", "localhost:8080")
MATRIX_FRIEND_USER = os.environ["MATRIX_FRIEND_USER"]
MATRIX_FRIEND_PASS = os.environ["MATRIX_FRIEND_PASS"]
MATRIX_FRIEND_INFERENCE_API = os.environ["MATRIX_FRIEND_INFERENCE_API"]
MATRIX_FRIEND_DEVICE = os.getenv("MATRIX_FRIEND_DEVICE", "Bot_Friend")

for key in os.environ.keys():
    if "MATRIX_FRIEND_" in key and key != "MATRIX_FRIEND_PASS":
        logging.debug(f"{key}={os.environ[key]}")

os.makedirs("./store/", exist_ok=True)
client = AsyncClient(
    f"{MATRIX_FRIEND_INSTANCE}",
    f"{MATRIX_FRIEND_USER}",
    store_path="./store/",
)

recent_messages = {}
message_window = 7

analyzer = SentimentIntensityAnalyzer()

async def message_callback(room, event):

    message = parsed_message(event)

    if not room.room_id in recent_messages:
        recent_messages[room.room_id] = [message]
    else:
        recent_messages[room.room_id].append(message)
        if len(recent_messages[room.room_id]) > message_window:
            recent_messages[room.room_id].pop(0)

    logging.info(f"[{room.display_name}] {room.user_name(event.sender)} <{message['sentiment']}>: {event.body}")

    interact = random.randrange(100) < 1
    if interact or "friend" in event.body.lower() and event.sender != client.user:
        await client.room_typing(room.room_id, True)
        result = prompt(
            recent_messages[room.room_id],
            seperators=["\n"],
            temperature=os.getenv("MATRIX_FRIEND_TEMP", 1.0),
            top_p=os.getenv("MATRIX_FRIEND_TOP_P", 0.7),
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
                logging.debug(f"Attempting to verify {e.device}")
                client.verify_device(e.device)
        await client.room_typing(room.room_id, False)


async def autojoin_room(room, event):
    logging.info(f"Joining room {room.room_id}")
    await client.join(room.room_id)


def parsed_message(event):
    return {
        "user": event.sender,
        "body": event.body,
        "sentiment": sentiment(event.body),
    }


def sentiment(text):
    compound = analyzer.polarity_scores(text)["compound"]
    if compound > 0.05:
        return "Positive"
    elif compound < -0.05:
        return "Negative"
    return "Neutral"


def prompt(messages, **kwargs):
    user = messages[-1]["user"]
    agents = {user: "agent_1", client.user: "agent_2"}

    text = os.getenv("MATRIX_FRIEND_PROMPT", "")
    mood = {
        "Positive": 0,
        "Neutral": 0,
        "Negative": 0,
    }

    for message in messages:
        if not message["user"] in agents:
            agents[message["user"]] = f"agent_{str(len(agents.keys()) + 1)}"
        text += (
            f"\n{agents[message['user']]} <{message['sentiment']}>: {message['body']}"
        )
        mood[message["sentiment"]] += 1

    text += f"\n{agents[client.user]} <{max(mood, key=mood.get)}>:"
    text = " ".join(text.split())

    kwargs["msg"] = text
    try:
        logging.debug(f"Infering `{text}`")
        r = requests.post(
            MATRIX_FRIEND_INFERENCE_API,
            json=kwargs,
        )
        if r.ok:
            return " ".join(r.text.split())
        else:
            logging.error(f"Error [{r.status_code}]: {r.text}")
            return "Can you repeat that?"
    except Exception as e:
        logging.error(e)
        return ""


async def main():
    logging.info(f"Attempting to login to {MATRIX_FRIEND_INSTANCE} as {MATRIX_FRIEND_USER}")
    await client.login(password=MATRIX_FRIEND_PASS, device_name=MATRIX_FRIEND_DEVICE)
    client.load_store()
    client.add_event_callback(autojoin_room, InviteEvent)
    if client.should_upload_keys:
        await client.keys_upload()
    logging.info("Initial Sync")
    await client.sync(30000)
    client.add_event_callback(message_callback, RoomMessageText)
    logging.info("Continually Syncing")
    await client.sync_forever(30000, full_state=True)


asyncio.get_event_loop().run_until_complete(main())
