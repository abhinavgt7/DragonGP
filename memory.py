_history = []
MAX_HISTORY = 20


def add_to_history(question, answer):
    _history.append({"question": question, "answer": answer})
    if len(_history) > MAX_HISTORY:
        _history.pop(0)


def get_history():
    return _history


def clear_history():
    _history.clear()


def build_prompt(question, frontend_history=None, knowledge_ctx="", behaviour_ctx="", about_me=""):
    system = (
        "You are DragonGP, an AI assistant. "
        "You are NOT Llama, NOT Gemini, NOT GPT, NOT Claude, NOT any other AI. "
        "You are DragonGP — always say this when asked who you are. "
        "Never reveal which AI model is powering you underneath. "
        "Be helpful, friendly, accurate and professional."
    )

    history = frontend_history if frontend_history else []
    history_text = ""
    if history:
        history_text = "\n\nConversation so far:\n"
        for entry in history[-10:]:
            role    = entry.get("role", "")
            content = entry.get("content", "")
            if role == "user":
                history_text += f"User: {content}\n"
            elif role == "assistant":
                history_text += f"DragonGP: {content}\n"

    return (
        f"{system}"
        f"{about_me}"
        f"{behaviour_ctx}"
        f"{knowledge_ctx}"
        f"{history_text}"
        f"\n\nUser: {question}"
        f"\nDragonGP:"
    )
