import time
from ai_providers import ALL_PROVIDERS

current_index = 0
fail_counts   = {}
cooldowns     = {}

CODE_KEYWORDS = [
    "code", "write a", "function", "python", "javascript",
    "html", "css", "java", "c++", "debug", "fix this",
    "error", "script", "program", "api", "sql", "database",
    "flutter", "react", "node", "django", "flask", "algorithm",
    "class", "array", "loop", "syntax", "compile", "import",
    "def ", "print(", "return", "variable", "string", "integer"
]

IDENTITY_KEYWORDS = [
    "who are you", "what are you", "your name", "who made you",
    "are you gpt", "are you gemini", "are you llama", "are you claude",
    "what ai", "which ai", "tell me about yourself", "introduce yourself",
    "who created you", "what is dragongp", "about dragongp"
]

MATH_KEYWORDS = [
    "calculate", "how much is", "equation", "solve",
    "formula", "convert", "percentage", "square root",
    "multiply", "divide", "algebra", "geometry"
]


def is_code_question(p):
    return any(k in p.lower() for k in CODE_KEYWORDS)

def is_identity_question(p):
    return any(k in p.lower() for k in IDENTITY_KEYWORDS)

def is_math_question(p):
    return any(k in p.lower() for k in MATH_KEYWORDS)


def handle_identity():
    return {
        "answer": (
            "I am DragonGP — a smart AI assistant powered by multiple AI engines working together.\n\n"
            "How I work:\n"
            "• For general questions — I ask multiple AIs and blend the best answer\n"
            "• For code questions — I use the fastest most accurate engine\n"
            "• For math — I use the most precise engine\n\n"
            "I am built to give you better answers than any single AI alone. How can I help you?"
        ),
        "ai_used": "DragonGP",
        "status": "success"
    }


def call_single(prompt, images=None, preferred=None):
    global current_index
    total = len(ALL_PROVIDERS)

    if preferred:
        for name in preferred:
            p = next((x for x in ALL_PROVIDERS if x["name"] == name), None)
            if p:
                in_cd = name in cooldowns and cooldowns[name] > time.time()
                if not in_cd:
                    try:
                        ans = p["fn"](prompt, p["key"], images)
                        if ans and ans.strip():
                            fail_counts[name] = 0
                            return {"answer": ans.strip(), "ai_used": name, "status": "success"}
                    except Exception as e:
                        print(f"  [{name}] failed: {e}")
                        fail_counts[name] = fail_counts.get(name, 0) + 1

    for _ in range(total):
        provider = ALL_PROVIDERS[current_index % total]
        current_index = (current_index + 1) % total
        name = provider["name"]
        in_cd = name in cooldowns and cooldowns[name] > time.time()
        if in_cd:
            continue
        try:
            ans = provider["fn"](prompt, provider["key"], images)
            if ans and ans.strip():
                fail_counts[name] = 0
                return {"answer": ans.strip(), "ai_used": name, "status": "success"}
        except Exception as e:
            print(f"  [{name}] failed: {e}")
            fail_counts[name] = fail_counts.get(name, 0) + 1
            if fail_counts[name] >= 3:
                cooldowns[name] = time.time() + 60

    return {"answer": "All AI engines are busy. Please try again.", "ai_used": "none", "status": "failed"}

# Use one from each company for true diversity
BLEND_POOL = [
    ["Puter-1"],
    ["HuggingFace-1"],
    ["GitHub-1"],

    ["Groq-1", "Groq-2", "Groq-3"],      # pick 1 groq
    ["Cohere-1"],                          # pick 1 cohere  
    ["OpenRouter-1", "OpenRouter-2", "OpenRouter-3"],  # pick 1 openrouter
]

def call_multiple_and_mix(prompt, images=None):
    collected = []

    for group in BLEND_POOL:
        for name in group:
            p = next((x for x in ALL_PROVIDERS if x["name"] == name), None)
            if not p:
                continue
            in_cd = name in cooldowns and cooldowns[name] > time.time()
            if in_cd:
                continue
            try:
                print(f"  Asking {name}...")
                ans = p["fn"](prompt, p["key"], images)
                if ans and ans.strip():
                    fail_counts[name] = 0
                    collected.append({"name": name, "answer": ans.strip()})
                    print(f"  Got answer from {name}")
                    break  # got one from this group, move to next
            except Exception as e:
                print(f"  [{name}] failed: {e}")
                fail_counts[name] = fail_counts.get(name, 0) + 1
                if fail_counts[name] >= 3:
                    cooldowns[name] = time.time() + 60

    if not collected:
        return {"answer": "All AI engines are refreshing. Please try again.", "ai_used": "none", "status": "all_failed"}

    if len(collected) == 1:
        return {"answer": collected[0]["answer"], "ai_used": collected[0]["name"], "status": "success"}

    blended = blend_answers(prompt, collected)
    names   = " + ".join(c["name"] for c in collected)
    return {"answer": blended, "ai_used": names, "status": "success"}

def blend_answers(question, collected):
    combined = ""
    for i, c in enumerate(collected):
        combined += f"\n[Brain {i+1} — {c['name']}]:\n{c['answer']}\n"

    blend_prompt = f"""You are DragonGP, a Master Synthesizer AI.
You received answers from {len(collected)} different AI brains for this question:
"{question}"

Answers:
{combined}

Your task:
1. Extract the best and most accurate points from each answer
2. Remove repetition
3. Combine into ONE perfect complete answer
4. Write naturally — never say "Brain 1 said" or "According to AI 2"
5. Just give the final best answer directly

Final blended answer:"""

    global current_index
    total = len(ALL_PROVIDERS)

    for _ in range(total):
        provider = ALL_PROVIDERS[current_index % total]
        current_index = (current_index + 1) % total
        name = provider["name"]
        in_cd = name in cooldowns and cooldowns[name] > time.time()
        if in_cd:
            continue
        try:
            blended = provider["fn"](blend_prompt, provider["key"], None)
            if blended and blended.strip():
                print(f"  Blended by {name}")
                return blended.strip()
        except Exception as e:
            print(f"  Blend failed on {name}: {e}")

    best = max(collected, key=lambda x: len(x["answer"]))
    return best["answer"]


def smart_ask(prompt, images=None, user_question=""):
    # Check only the last user question, not the whole prompt
    check = user_question.lower() if user_question else prompt.split("User:")[-1].split("DragonGP:")[0].lower()

    if is_identity_question(check):
        print("  Routing: IDENTITY")
        return handle_identity()

    if is_code_question(check):
        print("  Routing: CODE → single AI")
        return call_single(prompt, images, preferred=["Groq-1", "Groq-2", "Gemini-1", "Gemini-2"])

    if is_math_question(check):
        print("  Routing: MATH → single AI")
        return call_single(prompt, images, preferred=["Gemini-1", "Gemini-2", "Groq-1"])

    print("  Routing: GENERAL → multi-AI blend")
    return call_multiple_and_mix(prompt, images)


def get_provider_status():
    return [
        {
            "name":   p["name"],
            "fails":  fail_counts.get(p["name"], 0),
            "status": "cooldown" if (p["name"] in cooldowns and cooldowns[p["name"]] > time.time()) else "active"
        }
        for p in ALL_PROVIDERS
    ]
