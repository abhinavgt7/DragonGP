from ai_providers import ALL_PROVIDERS

test = "Say hello in one word"

for p in ALL_PROVIDERS:
    try:
        result = p["fn"](test, p["key"], None)
        print("OK -", p["name"], ":", result[:60])
    except Exception as e:
        print("FAIL -", p["name"], ":", str(e))