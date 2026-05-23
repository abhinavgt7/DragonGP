import requests
from groq import Groq
import cohere
import openai
from keys import (
    GEMINI_KEYS, GROQ_KEYS, COHERE_KEYS, MISTRAL_KEYS,
    TOGETHER_KEYS, CLOUDFLARE_KEYS, CLOUDFLARE_ACCOUNT_ID,
    CEREBRAS_KEYS, SAMBANOVA_KEYS, OPENROUTER_KEYS
)


def _get_gemini_client(key):
    try:
        import google.genai as google_genai
        return "genai", google_genai.Client(api_key=key)
    except Exception:
        import google.generativeai as google_genai
        google_genai.configure(api_key=key)
        return "generativeai", google_genai


def call_gemini(prompt, key, images=None):
    model_name = "gemini-2.5-flash"
    client_type, client = _get_gemini_client(key)
    if client_type == "genai":
        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )
        return response.text
    model = client.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    return response.text


def call_groq(prompt, key, images=None):
    client = Groq(api_key=key)
    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1000
    )
    return r.choices[0].message.content


def call_cohere(prompt, key, images=None):
    client = cohere.ClientV2(api_key=key)
    r = client.chat(
        model="command-a-03-2025",
        messages=[{"role": "user", "content": prompt}]
    )
    return r.message.content[0].text


def call_mistral(prompt, key, images=None):
    try:
        import mistralai
        client = mistralai.Mistral(api_key=key)
        r = client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}]
        )
        return r.choices[0].message.content
    except:
        raise Exception("Mistral not available")


def call_together(prompt, key, images=None):
    r = requests.post(
        "https://api.together.xyz/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": "meta-llama/Llama-3-70b-chat-hf",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        },
        timeout=30
    )
    return r.json()["choices"][0]["message"]["content"]


def call_cloudflare(prompt, key, images=None):
    r = requests.post(
        f"https://api.cloudflare.com/client/v4/accounts/{CLOUDFLARE_ACCOUNT_ID}/ai/run/@cf/meta/llama-3-8b-instruct",
        headers={"Authorization": f"Bearer {key}"},
        json={"messages": [{"role": "user", "content": prompt}]},
        timeout=30
    )
    return r.json()["result"]["response"]


def call_cerebras(prompt, key, images=None):
    r = requests.post(
        "https://api.cerebras.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": "llama3.1-70b",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        },
        timeout=30
    )
    return r.json()["choices"][0]["message"]["content"]


def call_sambanova(prompt, key, images=None):
    r = requests.post(
        "https://api.sambanova.ai/v1/chat/completions",
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": "Meta-Llama-3.1-70B-Instruct",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        },
        timeout=30
    )
    return r.json()["choices"][0]["message"]["content"]


def call_openrouter(prompt, key, images=None):
    r = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {key}",
            "HTTP-Referer": "https://dragongp.app",
            "X-Title": "DragonGP"
        },
        json={
            "model": "baidu/cobuddy:free",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        },
        timeout=30
    )
    data = r.json()
    if r.status_code != 200:
        raise Exception(f"OpenRouter error {r.status_code}: {data.get('error', data)}")
    if "choices" not in data or not data["choices"]:
        raise Exception(f"OpenRouter response missing choices: {data}")
    return data["choices"][0]["message"]["content"]


def build_providers():
    providers = []
    for i, k in enumerate(GEMINI_KEYS):
        providers.append({"name": f"Gemini-{i+1}", "key": k, "fn": call_gemini, "vision": True})
    for i, k in enumerate(GROQ_KEYS):
        providers.append({"name": f"Groq-{i+1}",  "key": k, "fn": call_groq,   "vision": False})
    for i, k in enumerate(COHERE_KEYS):
        providers.append({"name": f"Cohere-{i+1}", "key": k, "fn": call_cohere, "vision": False})
    for i, k in enumerate(MISTRAL_KEYS):
        providers.append({"name": f"Mistral-{i+1}",    "key": k, "fn": call_mistral,    "vision": False})
    for i, k in enumerate(TOGETHER_KEYS):
        providers.append({"name": f"Together-{i+1}",   "key": k, "fn": call_together,   "vision": False})
    for i, k in enumerate(CLOUDFLARE_KEYS):
        providers.append({"name": f"Cloudflare-{i+1}", "key": k, "fn": call_cloudflare, "vision": False})
    for i, k in enumerate(CEREBRAS_KEYS):
        providers.append({"name": f"Cerebras-{i+1}",   "key": k, "fn": call_cerebras,   "vision": False})
    for i, k in enumerate(SAMBANOVA_KEYS):
        providers.append({"name": f"Sambanova-{i+1}",  "key": k, "fn": call_sambanova,  "vision": False})
    for i, k in enumerate(OPENROUTER_KEYS):
        providers.append({"name": f"OpenRouter-{i+1}", "key": k, "fn": call_openrouter, "vision": False})
    return providers


ALL_PROVIDERS = build_providers()
