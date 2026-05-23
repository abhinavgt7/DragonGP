from flask import Flask, request, jsonify
from flask_cors import CORS
from ai_router import smart_ask
from memory import build_prompt, add_to_history, get_history, clear_history
from knowledge_base import add_knowledge, get_knowledge_context, get_image_entries, clear_knowledge, list_knowledge
from behaviour import add_writing_sample, get_behaviour_prompt, toggle_behaviour, clear_behaviour, get_status as behaviour_status
from feature_engine import process_feature_request, get_all_requests
import json, os, hashlib

app = Flask(__name__)
CORS(app)

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

def _load_users():
    if os.path.exists(USERS_FILE):
        try: return json.load(open(USERS_FILE))
        except: pass
    return {}

def _save_users(u): json.dump(u, open(USERS_FILE,"w"), indent=2)
def _hash(p): return hashlib.sha256(p.encode()).hexdigest()

# ── Chat ──────────────────────────────────────────────────────────
@app.route("/ask", methods=["POST"])
def ask():
    # Handle both JSON and FormData
    if request.is_json:
        data     = request.get_json(silent=True) or {}
        question = data.get("question", "").strip()
        history  = data.get("history", [])
        about_me = data.get("about_me", "")
    else:
        question = request.form.get("question", "").strip()
        about_me = request.form.get("about_me", "")
        try:
            history = json.loads(request.form.get("history", "[]"))
        except:
            history = []

    if not question:
        return jsonify({"error": "No question"}), 400

    knowledge_ctx = get_knowledge_context()
    behaviour_ctx = get_behaviour_prompt()
    prompt  = build_prompt(question, history, knowledge_ctx, behaviour_ctx, about_me)
    images  = get_image_entries()
    result  = smart_ask(prompt, images if images else None, user_question=question)
    add_to_history(question, result["answer"])
    return jsonify({
        "answer":   result["answer"],
        "ai_used":  result["ai_used"],
        "status":   result["status"]
    })

# ── Register / Login ──────────────────────────────────────────────
@app.route("/register", methods=["POST"])
def register():
    data  = request.get_json(silent=True) or {}
    email = data.get("email","").strip().lower()
    name  = data.get("name","").strip()
    pw    = data.get("password","")
    keys  = data.get("api_keys", {})   # {"gemini":"key","groq":"key",...}

    if not email or not pw:
        return jsonify({"error":"Email and password required"}), 400

    users = _load_users()
    if email in users:
        return jsonify({"error":"Email already registered"}), 409

    users[email] = {"name": name, "pw": _hash(pw), "keys_donated": list(keys.keys())}
    _save_users(users)

    # Auto-inject donated keys into the live pool
    from keys import add_user_key
    added = []
    for provider, key in keys.items():
        if key and key.strip():
            if add_user_key(provider, key):
                added.append(provider)

    return jsonify({"message": "Registered successfully", "keys_added": added, "name": name})

@app.route("/login", methods=["POST"])
def login():
    data  = request.get_json(silent=True) or {}
    email = data.get("email","").strip().lower()
    pw    = data.get("password","")
    users = _load_users()
    u = users.get(email)
    if not u or u["pw"] != _hash(pw):
        return jsonify({"error":"Invalid email or password"}), 401
    return jsonify({"message":"Login successful", "name": u.get("name","User"), "email": email})

# ── Key stats ─────────────────────────────────────────────────────
@app.route("/keystats", methods=["GET"])
def keystats():
    from keys import get_key_counts
    return jsonify(get_key_counts())

# ── Knowledge Base ────────────────────────────────────────────────
@app.route("/knowledge/upload", methods=["POST"])
def upload_knowledge():
    file = request.files.get("file")
    if not file: return jsonify({"error":"No file"}), 400
    entry = add_knowledge(file.filename, file.read())
    return jsonify({"message": f"Added {file.filename}", "name": entry["name"], "type": entry["type"]})

@app.route("/knowledge/list", methods=["GET"])
def list_knowledge_route(): return jsonify({"files": list_knowledge()})

@app.route("/knowledge/clear", methods=["POST"])
def clear_knowledge_route():
    clear_knowledge(); return jsonify({"message":"Cleared"})

# ── Behaviour ─────────────────────────────────────────────────────
@app.route("/behaviour/upload", methods=["POST"])
def upload_behaviour():
    file = request.files.get("file")
    if not file: return jsonify({"error":"No file"}), 400
    add_writing_sample(file.filename, file.read()); toggle_behaviour(True)
    return jsonify({"message": f"Style learned from {file.filename}"})

@app.route("/behaviour/toggle", methods=["POST"])
def toggle_behaviour_route():
    active = (request.get_json(silent=True) or {}).get("active", True)
    toggle_behaviour(active); return jsonify({"active": active})

@app.route("/behaviour/status", methods=["GET"])
def behaviour_status_route(): return jsonify(behaviour_status())

@app.route("/behaviour/clear", methods=["POST"])
def clear_behaviour_route():
    clear_behaviour(); return jsonify({"message":"Cleared"})

# ── Feature ───────────────────────────────────────────────────────
@app.route("/feature/request", methods=["POST"])
def feature_request():
    data = request.get_json(silent=True) or {}
    req  = data.get("request",""); email = data.get("email","")
    if not req: return jsonify({"error":"No request"}), 400
    return jsonify(process_feature_request(req, email))

@app.route("/feature/list", methods=["GET"])
def feature_list(): return jsonify({"requests": get_all_requests()})

# ── General ───────────────────────────────────────────────────────
from flask import send_from_directory

@app.route("/")
def serve_html():
    return send_from_directory(".", "DragonGP.html")
@app.route("/history", methods=["GET"])
def history(): return jsonify({"history": get_history()})

@app.route("/clear", methods=["POST"])
def clear():
    clear_history(); return jsonify({"message":"Cleared"})

@app.route("/health", methods=["GET"])
def health():
    from ai_router import get_provider_status
    from keys import get_key_counts
    return jsonify({"status":"running","providers":get_provider_status(),"key_counts":get_key_counts()})

if __name__ == "__main__":
    print("=" * 45)
    print("   DragonGP Server Starting...")
    print("   Open: http://localhost:5500")
    print("=" * 45)
    app.run(host="0.0.0.0", port=5000, debug=True)
