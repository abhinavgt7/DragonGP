import json
from datetime import datetime

feature_requests = []

try:
    import anthropic
    _client = None
    def _get_client():
        global _client
        if not _client:
            from keys import GEMINI_KEYS
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_KEYS[0] if GEMINI_KEYS else "")
        return None
    HAS_AI = True
except:
    HAS_AI = False


def _try_build_with_gemini(request_text):
    try:
        from keys import GEMINI_KEYS
        import google.generativeai as genai
        if not GEMINI_KEYS or GEMINI_KEYS[0].startswith("your-"):
            return None
        genai.configure(api_key=GEMINI_KEYS[0])
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = f"""You are a web developer. A user wants this feature: "{request_text}"

Decide if this can be built as a simple self-contained HTML+CSS+JS widget.

Reply ONLY in this exact JSON format, no markdown, no extra text:
{{
  "can_build": true or false,
  "reason": "short reason",
  "html_code": "complete working HTML if can_build is true, else null",
  "message": "friendly message to user"
}}

You CAN build: calculators, timers, text tools, games, converters, generators, quizzes, color pickers, clocks, counters.
You CANNOT build: payment systems, camera access, real-time data, mobile apps, backend features."""

        r = model.generate_content(prompt)
        text = r.text.strip()
        text = text.replace("```json","").replace("```","").strip()
        return json.loads(text)
    except Exception as e:
        print(f"Feature build error: {e}")
        return None


def process_feature_request(request_text, user_email=None):
    feature_requests.append({
        "request": request_text,
        "email":   user_email,
        "time":    datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status":  "processing"
    })

    result = _try_build_with_gemini(request_text)

    if result and result.get("can_build") and result.get("html_code"):
        feature_requests[-1]["status"] = "built"
        return {
            "status":    "built",
            "message":   result.get("message", "Your feature is ready!"),
            "html_code": result.get("html_code", "")
        }
    else:
        feature_requests[-1]["status"] = "pending"
        _notify_developer(request_text, user_email)
        return {
            "status":  "pending",
            "message": result.get("message", "This feature needs to be built manually. You will be notified when ready.") if result else "Feature sent to developer. You will be notified when ready.",
            "notified": True
        }


def _notify_developer(request_text, user_email):
    print(f"\n[NEW FEATURE REQUEST]")
    print(f"Request: {request_text}")
    print(f"User email: {user_email or 'not provided'}")
    print(f"Time: {datetime.now()}\n")


def get_all_requests():
    return feature_requests
