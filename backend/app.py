import json, sys, os
import tokenizers

sys.path.append("rwkv")
import rwkv_cpp_model, rwkv_cpp_shared_library, sampling


model_path = "release.bin"

library = rwkv_cpp_shared_library.load_rwkv_shared_library()
model = rwkv_cpp_model.RWKVModel(library, model_path)
tokenizer = tokenizers.Tokenizer.from_file("rwkv/20B_tokenizer.json")


def lambda_handler(event, context):
    body = json.loads(event["body"])
    if not "msg" in body:
        return {
            "statusCode": 400,
            "body": {"error": "A message is required", "event": event},
        }
    return {
        "statusCode": 200,
        "body": prompt(**body),
    }


def prompt(msg="Why was the message missing?", **kwargs):
    return infer(msg, **kwargs)


def infer(
    msg,
    min_tokens=10,
    max_tokens=1000,
    seperators=["\n"],
    temperature=1.0,
    top_p=0.7,
    **kwargs
):
    logits, state = None, None
    result = ""

    for token in tokenizer.encode(msg).ids:
        logits, state = model.eval(token, state)

    i = 0
    while i < max_tokens:
        token = sampling.sample_logits(logits, temperature, top_p)
        decoded = tokenizer.decode([token])
        if i > min_tokens and decoded in seperators:
            return result
        logits, state = model.eval(token, state, state, logits)
        result += decoded
        i += 1

    return result
