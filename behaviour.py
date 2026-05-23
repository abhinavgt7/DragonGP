writing_samples  = []
behaviour_active = False
behaviour_desc   = ""


def add_writing_sample(filename, file_bytes):
    try:
        text = file_bytes.decode("utf-8", errors="ignore")[:5000]
    except:
        text = ""
    writing_samples.append({"name": filename, "content": text})
    _analyse()
    return {"name": filename}


def _analyse():
    global behaviour_desc
    if not writing_samples:
        behaviour_desc = ""
        return
    all_text = " ".join(s["content"] for s in writing_samples)
    sentences = [s.strip() for s in all_text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    avg = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
    casual = sum(1 for w in ["gonna","wanna","kinda","hey","cool","btw","lol"] if w in all_text.lower())
    formal = sum(1 for w in ["therefore","furthermore","however","consequently"] if w in all_text.lower())
    parts = []
    parts.append("short sentences" if avg < 12 else "long sentences" if avg > 25 else "medium sentences")
    parts.append("formal tone" if formal > casual else "casual tone" if casual > formal else "neutral tone")
    if "•" in all_text or "- " in all_text:
        parts.append("uses bullet points")
    behaviour_desc = ", ".join(parts)


def get_behaviour_prompt():
    if not behaviour_active or not writing_samples:
        return ""
    samples = "\n\n---\n".join(
        f"Sample ({s['name']}):\n{s['content'][:600]}" for s in writing_samples[:3]
    )
    return f"""
WRITING STYLE INSTRUCTION:
Match the user's writing style. Detected style: {behaviour_desc}
Samples of user's writing:
{samples}
Write all answers in the same style, tone, and vocabulary as above.
"""


def toggle_behaviour(active):
    global behaviour_active
    behaviour_active = active


def clear_behaviour():
    global behaviour_active, behaviour_desc
    writing_samples.clear()
    behaviour_active = False
    behaviour_desc   = ""


def get_status():
    return {
        "active":  behaviour_active,
        "samples": len(writing_samples),
        "style":   behaviour_desc,
        "files":   [s["name"] for s in writing_samples]
    }
