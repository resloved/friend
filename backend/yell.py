import requests, json, sys

payload = {
    "body": json.dumps(
        {
            "msg": sys.argv[1],
        }
    )
}

r = requests.post(
    "http://localhost:9000/2015-03-31/functions/function/invocations", json=payload
)
print(json.dumps(r.json(), indent=4))
