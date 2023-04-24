import json
import rwkv_cpp_model
import rwkv_cpp_shared_library

model_path = "release.bin"

model = rwkv_cpp_model.RWKVModel(
    rwkv_cpp_shared_library.load_rwkv_shared_library(), model_path
)

tokenizer_path = pathlib.Path(os.path.abspath(__file__)).parent / "20B_tokenizer.json"
tokenizer = tokenizers.Tokenizer.from_file(str(tokenizer_path))


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


def prompt(
    msg="Why was the message missing?",
    max_tokens=1000,
    seperators=["\n"],
    temperature=1.0,
    top_p=0.7,
):
    logits, state = None, None
    result = ""

    for token in tokenizer.encode(msg).ids:
        logits, state = model.eval(token, state)
        print(f"Output logits: {logits}")
        i = 0
        while i < max_tokens:
            token = sampling.sample_logits(logits, temperature, top_p)
            decoded = tokenizer.decode([token])
            if decoded in seperators:
                return result
            logits, state = model.eval(token, state, state, logits)

    return result
