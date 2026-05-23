import base64

try:
    import fitz
    PDF_OK = True
except:
    PDF_OK = False

try:
    from docx import Document as DocxDoc
    DOCX_OK = True
except:
    DOCX_OK = False

knowledge_store = []


def extract_pdf(b, name):
    if not PDF_OK:
        return f"[PDF: {name} — run: pip install pymupdf]"
    try:
        import fitz
        doc = fitz.open(stream=b, filetype="pdf")
        return "".join(page.get_text() for page in doc)[:8000]
    except Exception as e:
        return f"[PDF error: {e}]"


def extract_docx(b, name):
    if not DOCX_OK:
        return f"[Word: {name} — run: pip install python-docx]"
    try:
        import io
        doc = DocxDoc(io.BytesIO(b))
        return "\n".join(p.text for p in doc.paragraphs)[:8000]
    except Exception as e:
        return f"[Word error: {e}]"


def add_knowledge(filename, file_bytes):
    ext = filename.split(".")[-1].lower()
    entry = {"name": filename, "type": ext}

    if ext == "pdf":
        entry["content"] = extract_pdf(file_bytes, filename)
        entry["b64"] = None
    elif ext in ["docx", "doc"]:
        entry["content"] = extract_docx(file_bytes, filename)
        entry["b64"] = None
    elif ext == "txt":
        entry["content"] = file_bytes.decode("utf-8", errors="ignore")[:8000]
        entry["b64"] = None
    elif ext in ["jpg", "jpeg", "png", "gif", "webp"]:
        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                "gif": "image/gif", "webp": "image/webp"}.get(ext, "image/png")
        entry["content"] = f"[Image: {filename}]"
        entry["b64"] = base64.b64encode(file_bytes).decode()
        entry["mime"] = mime
    else:
        entry["content"] = f"[Unsupported: {filename}]"
        entry["b64"] = None

    knowledge_store.append(entry)
    return entry


def get_knowledge_context():
    if not knowledge_store:
        return ""
    ctx = "\n\n--- KNOWLEDGE BASE ---\n"
    for k in knowledge_store:
        ctx += f"\nFile: {k['name']}\n{k['content']}\n"
    ctx += "--- END KNOWLEDGE BASE ---\n"
    return ctx


def get_image_entries():
    return [k for k in knowledge_store if k.get("b64")]


def clear_knowledge():
    knowledge_store.clear()


def list_knowledge():
    return [{"name": k["name"], "type": k["type"]} for k in knowledge_store]
