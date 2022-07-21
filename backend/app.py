import json
from models.run import infer


def lambda_handler(event, context):
    body = json.loads(event["body"])
    if not "msg" in body:
        return {"statusCode": 400, "body": {"error": "A message is required", "event": event}}
    return {
        "statusCode": 200,
        "body": prompt(**body),
    }

def prompt(msg="Why was the message missing?", **kwargs):
    infer(msg, **kwargs)[0]
