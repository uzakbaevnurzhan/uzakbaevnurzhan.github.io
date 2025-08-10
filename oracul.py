#!/usr/bin/env python3
# oracul_improved.py — Single-file OraculAi improved (UI, admin, password-change, models list)
# Dependencies:
# pip install flask requests flask-session werkzeug python-multipart

import os
import sqlite3
import uuid
import json
import requests
import time
from datetime import datetime
from flask import (
    Flask, request, jsonify, g, session, redirect, url_for,
    send_from_directory, render_template_string, Response
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session
from werkzeug.utils import secure_filename

# ---------------- CONFIG ----------------
APP_PORT = int(os.environ.get("PORT", 8000))
APP_HOST = "0.0.0.0"
DATABASE = os.environ.get("ORACUL_DB", "oracul_improved.db")
UPLOAD_DIR = os.environ.get("ORACUL_UPLOADS", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# IMPORTANT: Put sensitive keys into environment variables in production.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or ""
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME") or "admin"
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD") or "adminpass"  # change this in env!
SECRET_KEY = os.environ.get("ORACUL_SECRET") or "change_this_secret"

ALLOWED_EXTENSIONS = None  # None => allow everything (you may restrict in production)
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB

# Predefined model options (server-driven so frontend can ask for them)
MODEL_OPTIONS = [
    "gemini-pro", "gemini-1.5", "gpt-4o", "gpt-4o-mini", "llama-2-13b", "openai-gpt-3.5-turbo"
]

# ----------------------------------------

app = Flask(__name__)
app.config.update(
    SECRET_KEY=SECRET_KEY,
    SESSION_TYPE="filesystem",
    SESSION_PERMANENT=False,
    MAX_CONTENT_LENGTH=MAX_CONTENT_LENGTH,
)
Session(app)

# ---------------- DB ----------------
def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE, check_same_thread=False)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    cur = db.cursor()
    # users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
      id TEXT PRIMARY KEY,
      username TEXT UNIQUE,
      email TEXT,
      password_hash TEXT,
      is_admin INTEGER DEFAULT 0,
      created_at TEXT
    );
    """)
    # chats, messages
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chats (
      id TEXT PRIMARY KEY,
      user_id TEXT,
      title TEXT,
      model TEXT,
      system_prompt TEXT,
      created_at TEXT
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
      id TEXT PRIMARY KEY,
      chat_id TEXT,
      role TEXT,
      content TEXT,
      created_at TEXT,
      attachment TEXT
    );
    """)
    # pinned chats and user settings (were missing)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pinned_chats (
      user_id TEXT,
      chat_id TEXT,
      pinned_at TEXT,
      PRIMARY KEY (user_id, chat_id)
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_settings (
      user_id TEXT PRIMARY KEY,
      settings_json TEXT,
      updated_at TEXT
    );
    """)
    db.commit()

    # create admin user if not exists (use env vars)
    cur.execute("SELECT id FROM users WHERE username = ?", (ADMIN_USERNAME,))
    if not cur.fetchone():
        admin_id = str(uuid.uuid4())
        ph = generate_password_hash(ADMIN_PASSWORD)
        now = datetime.utcnow().isoformat()
        cur.execute("INSERT INTO users (id,username,email,password_hash,is_admin,created_at) VALUES (?,?,?,?,?,?)",
                    (admin_id, ADMIN_USERNAME, None, ph, 1, now))
        db.commit()

@app.teardown_appcontext
def close_db(exc):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()

# ---------------- Helpers ----------------
def allowed_file(filename):
    if ALLOWED_EXTENSIONS is None:
        return True
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def now_iso():
    return datetime.utcnow().isoformat()

# ---------------- Auth endpoints ----------------
@app.route("/api/register", methods=["POST"])
def register():
    data = request.json or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip() or None
    password = data.get("password") or ""
    if not username or not password:
        return jsonify({"error":"username and password required"}), 400
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cur.fetchone():
        return jsonify({"error":"user exists"}), 400
    uid = str(uuid.uuid4())
    ph = generate_password_hash(password)
    cur.execute("INSERT INTO users (id,username,email,password_hash,created_at) VALUES (?,?,?,?,?)",
                (uid, username, email, ph, now_iso()))
    db.commit()
    session["user_id"] = uid
    session["username"] = username
    session["is_admin"] = False
    return jsonify({"ok":True, "user":{"id":uid,"username":username}})

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT id, password_hash, is_admin FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    if not row or not check_password_hash(row["password_hash"], password):
        return jsonify({"error":"invalid credentials"}), 401
    session["user_id"] = row["id"]
    session["username"] = username
    session["is_admin"] = bool(row["is_admin"])
    return jsonify({"ok":True, "user":{"id":row["id"], "username":username, "is_admin": bool(row["is_admin"])}})

@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok":True})

@app.route("/api/whoami")
def whoami():
    if "user_id" in session:
        return jsonify({"user":{"id":session["user_id"], "username":session.get("username"), "is_admin": session.get("is_admin", False)}})
    return jsonify({"user":None})

# ---------------- Account endpoints ----------------
@app.route("/api/account", methods=["GET"])
def account_info():
    if "user_id" not in session:
        return jsonify({"error":"not_authenticated"}), 401
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT id, username, email, is_admin, created_at FROM users WHERE id = ?", (session["user_id"],))
    r = cur.fetchone()
    if not r:
        return jsonify({"error":"not_found"}), 404
    return jsonify({"account": dict(r)})

@app.route("/api/account/password", methods=["PUT"])
def change_password():
    if "user_id" not in session:
        return jsonify({"error":"not_authenticated"}), 401
    data = request.json or {}
    old = data.get("old_password") or ""
    new = data.get("new_password") or ""
    if not new:
        return jsonify({"error":"new password required"}), 400
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT password_hash FROM users WHERE id = ?", (session["user_id"],))
    row = cur.fetchone()
    if not row or not check_password_hash(row["password_hash"], old):
        return jsonify({"error":"invalid_old_password"}), 401
    cur.execute("UPDATE users SET password_hash = ? WHERE id = ?", (generate_password_hash(new), session["user_id"]))
    db.commit()
    return jsonify({"ok": True})

# ---------------- Admin endpoints ----------------
@app.route("/api/admin/users", methods=["GET"])
def admin_users():
    if not session.get("is_admin"):
        return jsonify({"error":"forbidden"}), 403
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT id, username, email, is_admin, created_at FROM users ORDER BY created_at DESC")
    rows = [dict(r) for r in cur.fetchall()]
    return jsonify({"users": rows})

@app.route("/api/admin/user/<user_id>", methods=["PUT","DELETE"])
def admin_user_ops(user_id):
    if not session.get("is_admin"):
        return jsonify({"error":"forbidden"}), 403
    db = get_db(); cur = db.cursor()
    if request.method == "DELETE":
        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))
        db.commit()
        return jsonify({"ok": True})
    data = request.json or {}
    # allowed actions: promote/demote, reset_password
    if "promote" in data:
        cur.execute("UPDATE users SET is_admin = 1 WHERE id = ?", (user_id,))
    if "demote" in data:
        cur.execute("UPDATE users SET is_admin = 0 WHERE id = ?", (user_id,))
    if "reset_password" in data and data.get("reset_password"):
        ph = generate_password_hash(data.get("reset_password"))
        cur.execute("UPDATE users SET password_hash = ? WHERE id = ?", (ph, user_id))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/admin/export_db", methods=["GET"])
def admin_export_db():
    if not session.get("is_admin"):
        return jsonify({"error":"forbidden"}), 403
    def generate():
        with open(DATABASE, "rb") as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                yield chunk
    return Response(generate(), mimetype="application/octet-stream", headers={"Content-Disposition":"attachment;filename="+DATABASE})

# ---------------- Chats and messages ----------------
@app.route("/api/chats", methods=["GET","POST"])
def chats():
    if "user_id" not in session:
        return jsonify({"error":"not_authenticated"}), 401
    db = get_db(); cur = db.cursor()
    if request.method == "POST":
        data = request.json or {}
        title = data.get("title") or "New chat"
        model = data.get("model") or MODEL_OPTIONS[0]
        system_prompt = data.get("system_prompt") or "You are OraculAi, helpful assistant."
        cid = str(uuid.uuid4()); now = now_iso()
        cur.execute("INSERT INTO chats (id,user_id,title,model,system_prompt,created_at) VALUES (?,?,?,?,?,?)",
                    (cid, session["user_id"], title, model, system_prompt, now))
        db.commit()
        return jsonify({"ok":True, "chat":{"id":cid, "title":title, "model":model, "system_prompt":system_prompt}})
    else:
        cur.execute("SELECT id,title,model,system_prompt,created_at FROM chats WHERE user_id = ? ORDER BY created_at DESC", (session["user_id"],))
        rows = [dict(r) for r in cur.fetchall()]
        return jsonify({"chats": rows})

@app.route("/api/chats/<chat_id>", methods=["GET","PUT","DELETE"])
def chat_ops(chat_id):
    if "user_id" not in session:
        return jsonify({"error":"not_authenticated"}), 401
    db = get_db(); cur = db.cursor()
    if request.method == "GET":
        cur.execute("SELECT id,title,model,system_prompt,created_at FROM chats WHERE id = ? AND (user_id = ? OR ?)", (chat_id, session["user_id"], session.get("is_admin", False)))
        r = cur.fetchone()
        if not r: return jsonify({"error":"not_found"}), 404
        return jsonify({"chat": dict(r)})
    if request.method == "PUT":
        data = request.json or {}
        title = data.get("title")
        system_prompt = data.get("system_prompt")
        model = data.get("model")
        # admins can update any chat, users only their own
        owner_cond = "user_id = ?" if not session.get("is_admin") else "1=1"
        params = []
        if title:
            cur.execute(f"UPDATE chats SET title = ? WHERE id = ? AND {owner_cond}", (title, chat_id, session["user_id"] if not session.get("is_admin") else None)[:2])
        if system_prompt is not None:
            cur.execute(f"UPDATE chats SET system_prompt = ? WHERE id = ? AND {owner_cond}", (system_prompt, chat_id, session["user_id"] if not session.get("is_admin") else None)[:2])
        if model:
            cur.execute(f"UPDATE chats SET model = ? WHERE id = ? AND {owner_cond}", (model, chat_id, session["user_id"] if not session.get("is_admin") else None)[:2])
        db.commit()
        return jsonify({"ok":True})
    if request.method == "DELETE":
        cur.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        cur.execute("DELETE FROM chats WHERE id = ? AND (user_id = ? OR ?)", (chat_id, session["user_id"], session.get("is_admin", False)))
        db.commit()
        return jsonify({"ok":True})

@app.route("/api/chats/<chat_id>/messages", methods=["GET","POST"])
def chat_messages(chat_id):
    if "user_id" not in session:
        return jsonify({"error":"not_authenticated"}), 401
    db = get_db(); cur = db.cursor()
    if request.method == "GET":
        cur.execute("SELECT id,role,content,created_at,attachment FROM messages WHERE chat_id = ? ORDER BY created_at", (chat_id,))
        rows = [dict(r) for r in cur.fetchall()]
        return jsonify({"messages": rows})
    else:
        data = request.json or {}
        role = data.get("role", "user")
        content = data.get("content", "") or ""
        attachment = data.get("attachment")
        mid = str(uuid.uuid4()); now = now_iso()
        cur.execute("INSERT INTO messages (id,chat_id,role,content,created_at,attachment) VALUES (?,?,?,?,?,?)",
                    (mid, chat_id, role, content, now, attachment))
        db.commit()
        return jsonify({"ok":True, "message": {"id": mid, "role": role, "content": content, "created_at": now, "attachment": attachment}})

# ---------------- uploads ----------------
@app.route("/api/upload", methods=["POST"])
def upload():
    if "user_id" not in session:
        return jsonify({"error":"not_authenticated"}), 401
    if "file" not in request.files:
        return jsonify({"error":"no_file"}), 400
    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error":"empty_name"}), 400
    if not allowed_file(f.filename):
        return jsonify({"error":"disallowed_file"}), 400
    filename = secure_filename(f.filename)
    uid = str(uuid.uuid4()); saved = f"{uid}_{filename}"
    path = os.path.join(UPLOAD_DIR, saved)
    f.save(path)
    return jsonify({"ok":True, "path": f"/uploads/{saved}", "name": filename})

@app.route("/uploads/<path:fn>")
def serve_upload(fn):
    return send_from_directory(UPLOAD_DIR, fn)

# ---------------- Gemini proxy & streaming ----------------
def call_gemini_once(messages, model="gemini-pro", temperature=0.2, max_output_tokens=512):
    if not GEMINI_API_KEY:
        return "GEMINI_API_KEY not set on server"
    conv = "\n".join([f"{m.get('role')}: {m.get('content')}" for m in messages])
    endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents":[{"parts":[{"text": conv}]}]}
    try:
        r = requests.post(endpoint, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        # extract text robustly
        text = None
        if isinstance(data.get("candidates"), list) and data["candidates"]:
            try:
                text = data["candidates"][0]["content"]["parts"][0]["text"]
            except Exception:
                text = None
        if not text:
            out = data.get("output") or []
            if out and isinstance(out, list) and out[0].get("content"):
                try:
                    text = out[0]["content"]["parts"][0].get("text")
                except Exception:
                    text = None
        if not text:
            text = data.get("reply") or json.dumps(data)[:1000]
        return text
    except Exception as e:
        return f"Error calling Gemini: {str(e)}"

def stream_text_chunks(text, delay=0.02):
    chunk_size = 80
    for i in range(0, len(text), chunk_size):
        chunk = text[i:i+chunk_size]
        yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        time.sleep(delay)
    yield f"data: {json.dumps({'done': True})}\n\n"

@app.route("/api/generate", methods=["POST"])
def generate():
    if "user_id" not in session:
        return jsonify({"error":"not_authenticated"}), 401
    data = request.json or {}
    chat_id = data.get("chat_id")
    temperature = float(data.get("temperature", 0.2))
    maxTokens = int(data.get("maxTokens", 512))
    model = data.get("model", MODEL_OPTIONS[0])

    db = get_db(); cur = db.cursor()
    cur.execute("SELECT system_prompt FROM chats WHERE id = ?", (chat_id,))
    row = cur.fetchone()
    messages = []
    if row and row["system_prompt"]:
        messages.append({"role":"system", "content": row["system_prompt"]})
    cur.execute("SELECT role,content FROM messages WHERE chat_id = ? ORDER BY created_at", (chat_id,))
    for r in cur.fetchall():
        messages.append({"role": r["role"], "content": r["content"]})

    text = call_gemini_once(messages, model=model, temperature=temperature, max_output_tokens=maxTokens)

    mid = str(uuid.uuid4()); now = now_iso()
    cur.execute("INSERT INTO messages (id,chat_id,role,content,created_at,attachment) VALUES (?,?,?,?,?,?)",
                (mid, chat_id, "assistant", text, now, None))
    db.commit()

    return jsonify({"text": text})

@app.route("/api/generate/stream", methods=["POST"])
def generate_stream():
    if "user_id" not in session:
        return jsonify({"error":"not_authenticated"}), 401
    data = request.json or {}
    chat_id = data.get("chat_id")
    temperature = float(data.get("temperature", 0.2))
    maxTokens = int(data.get("maxTokens", 512))
    model = data.get("model", MODEL_OPTIONS[0])

    db = get_db(); cur = db.cursor()
    cur.execute("SELECT system_prompt FROM chats WHERE id = ?", (chat_id,))
    row = cur.fetchone()
    messages = []
    if row and row["system_prompt"]:
        messages.append({"role":"system", "content": row["system_prompt"]})
    cur.execute("SELECT role,content FROM messages WHERE chat_id = ? ORDER BY created_at", (chat_id,))
    for r in cur.fetchall():
        messages.append({"role": r["role"], "content": r["content"]})

    text = call_gemini_once(messages, model=model, temperature=temperature, max_output_tokens=maxTokens)

    mid = str(uuid.uuid4()); now = now_iso()
    cur.execute("INSERT INTO messages (id,chat_id,role,content,created_at,attachment) VALUES (?,?,?,?,?,?)",
                (mid, chat_id, "assistant", text, now, None))
    db.commit()

    return Response(stream_text_chunks(text), content_type='text/event-stream')

# ---------------- Extra features endpoints ----------------
@app.route("/api/pin", methods=["POST"])
def pin_chat():
    if "user_id" not in session:
        return jsonify({"error":"not_authenticated"}), 401
    data = request.json or {}
    chat_id = data.get("chat_id")
    action = data.get("action","pin")
    db = get_db(); cur = db.cursor()
    if action == "pin":
        cur.execute("INSERT OR REPLACE INTO pinned_chats (user_id, chat_id, pinned_at) VALUES (?,?,?)", (session["user_id"], chat_id, now_iso()))
    else:
        cur.execute("DELETE FROM pinned_chats WHERE user_id = ? AND chat_id = ?", (session["user_id"], chat_id))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/chats/<chat_id>/search")
def search_messages(chat_id):
    if "user_id" not in session:
        return jsonify({"error":"not_authenticated"}), 401
    q = (request.args.get("q") or "").strip()
    db = get_db(); cur = db.cursor()
    if not q:
        return jsonify({"results": []})
    cur.execute("SELECT id, role, content, created_at FROM messages WHERE chat_id = ? AND content LIKE ? ORDER BY created_at", (chat_id, f"%{q}%"))
    rows = [dict(r) for r in cur.fetchall()]
    return jsonify({"results": rows})

@app.route("/api/chats/<chat_id>/export_md")
def export_chat_md(chat_id):
    if "user_id" not in session:
        return jsonify({"error":"not_authenticated"}), 401
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT title FROM chats WHERE id = ? AND (user_id = ? OR ?)", (chat_id, session["user_id"], session.get("is_admin", False)))
    r = cur.fetchone()
    if not r:
        return jsonify({"error":"not_found"}), 404
    title = r["title"] or "chat"
    cur.execute("SELECT role, content, created_at FROM messages WHERE chat_id = ? ORDER BY created_at", (chat_id,))
    parts = []
    for m in cur.fetchall():
        role = m["role"]
        t = m["created_at"] or ""
        content = m["content"] or ""
        if role == "user":
            parts.append(f"**User ({t}):**\n\n{content}\n\n---\n")
        elif role == "assistant":
            parts.append(f"**Assistant ({t}):**\n\n{content}\n\n---\n")
        else:
            parts.append(f"**{role} ({t}):**\n\n{content}\n\n---\n")
    md = f"# Chat export: {title}\n\n" + "\n".join(parts)
    return Response(md, mimetype="text/markdown", headers={"Content-Disposition": f"attachment; filename={secure_filename(title)}.md"})

@app.route("/api/export_all", methods=["GET"])
def export_all_chats():
    if "user_id" not in session:
        return jsonify({"error":"not_authenticated"}), 401
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT id, title, model, system_prompt, created_at FROM chats WHERE user_id = ?", (session["user_id"],))
    chats = [dict(r) for r in cur.fetchall()]
    out = []
    for c in chats:
        cur.execute("SELECT role,content,created_at,attachment FROM messages WHERE chat_id = ? ORDER BY created_at", (c["id"],))
        msgs = [dict(m) for m in cur.fetchall()]
        out.append({"chat": c, "messages": msgs})
    return Response(json.dumps(out, indent=2, ensure_ascii=False), mimetype="application/json", headers={"Content-Disposition":"attachment; filename=all_chats.json"})

@app.route("/api/clear_all", methods=["POST"])
def clear_all():
    if "user_id" not in session:
        return jsonify({"error":"not_authenticated"}), 401
    db = get_db(); cur = db.cursor()
    cur.execute("DELETE FROM messages WHERE chat_id IN (SELECT id FROM chats WHERE user_id = ?)", (session["user_id"],))
    cur.execute("DELETE FROM chats WHERE user_id = ?", (session["user_id"],))
    cur.execute("DELETE FROM pinned_chats WHERE user_id = ?", (session["user_id"],))
    db.commit()
    return jsonify({"ok": True})

@app.route("/api/pin_list", methods=["GET"])
def pin_list():
    if "user_id" not in session:
        return jsonify({"pinned": []})
    db = get_db(); cur = db.cursor()
    cur.execute("SELECT chat_id, pinned_at FROM pinned_chats WHERE user_id = ? ORDER BY pinned_at DESC", (session["user_id"],))
    rows = [dict(r) for r in cur.fetchall()]
    return jsonify({"pinned": rows})

@app.route("/api/models", methods=["GET"])
def models_list():
    # Return server-side model options for frontend to populate
    return jsonify({"models": MODEL_OPTIONS})

@app.route("/api/settings", methods=["GET","PUT"])
def user_settings_auto():
    if "user_id" not in session:
        return jsonify({"error":"not_authenticated"}), 401
    db = get_db(); cur = db.cursor()
    uid = session["user_id"]
    if request.method == "GET":
        cur.execute("SELECT settings_json FROM user_settings WHERE user_id = ?", (uid,))
        row = cur.fetchone()
        if not row:
            return jsonify({"settings": {}})
        try:
            return jsonify({"settings": json.loads(row["settings_json"])})
        except Exception:
            return jsonify({"settings": {}})
    else:
        data = request.json or {}
        settings_obj = data.get("settings", data)
        js = json.dumps(settings_obj)
        now = now_iso()
        cur.execute("INSERT INTO user_settings (user_id,settings_json,updated_at) VALUES (?,?,?) ON CONFLICT(user_id) DO UPDATE SET settings_json = excluded.settings_json, updated_at = excluded.updated_at", (uid, js, now))
        db.commit()
        return jsonify({"ok": True})

# ---------------- Frontend HTML (single page app) ----------------
INDEX_HTML = r"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>OraculAi — Improved</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <style>
    body { -webkit-font-smoothing:antialiased; -moz-osx-font-smoothing:grayscale; }
    .scroll { max-height: 60vh; overflow:auto; }
    .msg { max-width: 78%; word-wrap: break-word; padding: .5rem 0.75rem; border-radius: .75rem; }
    .hidden { display:none !important; }
    .sidebar { background:#fff; }
    /* ChatGPT-like two-column feel */
    .left-col { min-width: 260px; max-width: 360px; }
    .right-col { min-width: 360px; }
  </style>
</head>
<body class="bg-[#0b1020] text-white min-h-screen">
  <!-- Landing -->
  <div id="landing" class="min-h-screen flex items-center justify-center p-4">
    <div class="bg-[#0f1724] rounded-xl shadow p-6 w-full max-w-3xl border border-gray-800">
      <div class="flex items-center gap-4">
        <div class="w-12 h-12 rounded-full bg-indigo-500 text-white flex items-center justify-center font-bold">OA</div>
        <div>
          <h1 class="text-xl font-semibold">OraculAi</h1>
          <div class="text-sm text-gray-400">Login or register to start</div>
        </div>
      </div>

      <div class="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="p-4 border rounded border-gray-800">
          <h3 class="font-semibold mb-2">Login</h3>
          <input id="loginUser" placeholder="username" class="w-full p-2 bg-[#0b1220] border border-gray-700 rounded mb-2" />
          <input id="loginPass" placeholder="password" type="password" class="w-full p-2 bg-[#0b1220] border border-gray-700 rounded mb-2" />
          <div class="flex gap-2">
            <button id="btnLogin" class="px-3 py-2 bg-indigo-600 text-white rounded">Login</button>
            <button id="btnGuest" class="px-3 py-2 border border-gray-700 rounded">Guest</button>
          </div>
        </div>

        <div class="p-4 border rounded border-gray-800">
          <h3 class="font-semibold mb-2">Register</h3>
          <input id="regUser" placeholder="username" class="w-full p-2 bg-[#0b1220] border border-gray-700 rounded mb-2" />
          <input id="regPass" placeholder="password" type="password" class="w-full p-2 bg-[#0b1220] border border-gray-700 rounded mb-2" />
          <input id="regEmail" placeholder="email (optional)" class="w-full p-2 bg-[#0b1220] border border-gray-700 rounded mb-2" />
          <button id="btnReg" class="px-3 py-2 bg-green-500 text-white rounded">Register</button>
        </div>
      </div>
      <div class="mt-4 text-xs text-gray-400">Improved UI, admin tools and account features.</div>
    </div>
  </div>

  <!-- App -->
  <div id="app" class="hidden max-w-7xl mx-auto p-4">
    <div class="grid grid-cols-1 md:grid-cols-12 gap-4">
      <div id="sidebar" class="left-col md:col-span-3 sidebar p-4 rounded-lg shadow-sm bg-[#071028] border border-gray-800">
        <div class="flex items-center justify-between mb-3">
          <div><div class="font-semibold">OraculAi</div><div id="userTag" class="text-xs text-gray-400">-</div></div>
          <button id="newChat" class="px-2 py-1 bg-green-500 text-black rounded text-sm">New</button>
        </div>
        <input id="searchChats" placeholder="Search chats..." class="w-full p-2 bg-[#071428] border border-gray-800 rounded mb-3" />
        <div id="chats" class="space-y-2 scroll"></div>
        <div class="mt-4 space-y-2">
          <button id="loadChats" class="w-full px-2 py-1 border rounded border-gray-800">Load chats</button>
          <button id="exportAllBtn" class="w-full px-2 py-1 border rounded border-gray-800">Export All</button>
          <button id="clearAllBtn" class="w-full px-2 py-1 border rounded text-red-400 border-gray-800">Clear All</button>
          <button id="settingsBtn" class="w-full px-2 py-1 border rounded border-gray-800">Settings</button>
          <button id="accountBtn" class="w-full px-2 py-1 border rounded border-gray-800">Account</button>
          <button id="adminBtn" class="w-full px-2 py-1 border rounded border-gray-800 hidden">Admin</button>
          <button id="logoutBtn" class="w-full px-2 py-1 bg-red-500 text-white rounded">Logout</button>
        </div>
      </div>

      <div id="main" class="right-col md:col-span-6 p-4 bg-[#061028] rounded-lg shadow-sm flex flex-col border border-gray-800">
        <div class="flex items-center justify-between mb-2">
          <div>
            <div id="chatTitle" class="font-semibold text-lg">No chat selected</div>
            <div id="chatInfo" class="text-xs text-gray-400"></div>
          </div>
          <div class="flex items-center gap-2">
            <select id="modelSelect" class="p-1 bg-[#081428] border border-gray-800 rounded text-sm"></select>
            <button id="rename" class="px-2 py-1 border rounded text-sm border-gray-800">Rename</button>
          </div>
        </div>

        <div id="messages" class="flex-1 overflow-auto p-3 bg-[#071428] rounded mb-3"></div>

        <div class="mt-2">
          <textarea id="input" rows="3" class="w-full p-2 bg-[#071428] border rounded" placeholder="Type your message..."></textarea>
          <div class="flex items-center gap-2 mt-2">
            <input id="file" type="file" class="text-xs" />
            <button id="send" class="px-4 py-2 bg-indigo-600 text-white rounded">Send</button>
            <button id="stream" class="px-3 py-1 border rounded">Stream</button>
            <button id="exportChat" class="px-3 py-1 border rounded">Export</button>
            <button id="saveChat" class="px-3 py-1 bg-green-500 text-white rounded">Save</button>
            <button id="clearChat" class="px-3 py-1 border rounded">Clear</button>
            <div id="tokenEstimate" class="text-xs text-gray-400 ml-2"></div>
          </div>
        </div>
      </div>

      <div class="md:col-span-3 p-4 bg-[#071428] rounded-lg shadow-sm border border-gray-800">
        <div id="quickAuth" class="mb-4"></div>
        <div class="p-2 border rounded mb-3 border-gray-800">
          <div class="font-semibold">Quick actions</div>
          <div class="mt-2 flex flex-col gap-2">
            <button id="importBtn" class="px-2 py-1 border rounded border-gray-800">Import JSON</button>
            <button id="pinListBtn" class="px-2 py-1 border rounded border-gray-800">Pinned</button>
            <button id="downloadDbBtn" class="px-2 py-1 border rounded border-gray-800 hidden">Download DB (admin)</button>
          </div>
        </div>
        <div class="p-2 border rounded border-gray-800">
          <div class="font-semibold">Info</div>
          <div class="text-xs text-gray-400 mt-2">Admin account is created from environment variables.</div>
        </div>
      </div>
    </div>
  </div>

  <!-- Settings modal -->
  <div id="settingsModal" class="hidden fixed inset-0 flex items-center justify-center bg-black bg-opacity-50">
    <div class="bg-[#0b1220] p-4 rounded w-full max-w-2xl border border-gray-800">
      <div class="flex justify-between items-center mb-2">
        <div class="font-semibold">Settings</div>
        <div>
          <button id="saveSettingsBtn" class="px-2 py-1 bg-indigo-600 text-white rounded">Save</button>
          <button id="closeSettingsBtn" class="px-2 py-1 border rounded border-gray-800">Close</button>
        </div>
      </div>
      <div>
        <label class="flex items-center gap-2"><input id="darkTheme" type="checkbox" /> Dark theme</label>
        <div class="mt-3 text-sm text-gray-400">Feature toggles</div>
      </div>
    </div>
  </div>

  <!-- Account modal (with password change) -->
  <div id="accountModal" class="hidden fixed inset-0 flex items-center justify-center bg-black bg-opacity-50">
    <div class="bg-[#0b1220] p-4 rounded w-full max-w-md border border-gray-800">
      <div class="flex justify-between items-center mb-2">
        <div class="font-semibold">Account</div>
        <button id="closeAccountBtn" class="px-2 py-1 border rounded border-gray-800">Close</button>
      </div>
      <div id="accountInfo"></div>
      <div class="mt-4">
        <div class="font-semibold text-sm mb-2">Change password</div>
        <input id="oldPass" type="password" placeholder="Old password" class="w-full p-2 bg-[#071428] border border-gray-800 rounded mb-2"/>
        <input id="newPass" type="password" placeholder="New password" class="w-full p-2 bg-[#071428] border border-gray-800 rounded mb-2"/>
        <button id="changePassBtn" class="px-3 py-2 bg-indigo-600 rounded">Change password</button>
      </div>
    </div>
  </div>

  <!-- Admin modal -->
  <div id="adminModal" class="hidden fixed inset-0 flex items-center justify-center bg-black bg-opacity-50">
    <div class="bg-[#0b1220] p-4 rounded w-full max-w-3xl border border-gray-800">
      <div class="flex justify-between items-center mb-2">
        <div class="font-semibold">Admin panel</div>
        <button id="closeAdminBtn" class="px-2 py-1 border rounded border-gray-800">Close</button>
      </div>
      <div id="adminUsers" class="space-y-2 max-h-60 overflow:auto"></div>
    </div>
  </div>

<script>
async function api(path, opts={}){ try{ const r = await fetch(path, opts); if(r.headers.get('content-type') && r.headers.get('content-type').includes('application/json')) return await r.json(); return r; }catch(e){ return {error: e.message}; } }

let currentChat = null;
let chats = [];

function escapeHtml(s){ return (s||'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;'); }
function showLanding(show){ document.getElementById('landing').style.display = show ? 'flex' : 'none'; document.getElementById('app').classList.toggle('hidden', show); }

async function refreshAuth(){
  const j = await api('/api/whoami');
  if(j.user){
    document.getElementById('userTag').textContent = j.user.username + (j.user.is_admin ? ' (admin)' : '');
    document.getElementById('quickAuth').innerHTML = '<div>' + escapeHtml(j.user.username) + '</div>';
    // show admin button if admin
    document.getElementById('adminBtn').classList.toggle('hidden', !j.user.is_admin);
    document.getElementById('downloadDbBtn').classList.toggle('hidden', !j.user.is_admin);
    showLanding(false);
    await loadModels();
    await loadChats();
  } else {
    showLanding(true);
  }
}

document.getElementById('btnLogin').onclick = async ()=>{
  const username = document.getElementById('loginUser').value.trim();
  const password = document.getElementById('loginPass').value;
  const r = await api('/api/login', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({username,password})});
  if(r.error) alert(r.error); else { alert('Logged in'); await refreshAuth(); }
};
document.getElementById('btnReg').onclick = async ()=>{
  const username = document.getElementById('regUser').value.trim();
  const password = document.getElementById('regPass').value;
  const email = document.getElementById('regEmail').value.trim();
  const r = await api('/api/register', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({username,password,email})});
  if(r.error) alert(r.error); else { alert('Registered'); await refreshAuth(); }
};
document.getElementById('btnGuest').onclick = ()=>{ showLanding(false); };

document.getElementById('logoutBtn').onclick = async ()=>{ await api('/api/logout', {method:'POST'}); location.reload(); };
document.getElementById('newChat').onclick = async ()=>{ const title = prompt('Chat title','New chat'); const model = document.getElementById('modelSelect').value; await api('/api/chats', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({title, model})}); await loadChats(); };
document.getElementById('loadChats').onclick = loadChats;
document.getElementById('settingsBtn').onclick = ()=>{ document.getElementById('settingsModal').classList.remove('hidden'); };
document.getElementById('closeSettingsBtn').onclick = ()=>{ document.getElementById('settingsModal').classList.add('hidden'); };
document.getElementById('saveSettingsBtn').onclick = async ()=>{ const settings = {dark_theme: document.getElementById('darkTheme').checked}; const r = await api('/api/settings', {method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify({settings})}); if(r.ok) { alert('Saved'); document.getElementById('settingsModal').classList.add('hidden'); } else alert(JSON.stringify(r)); };
document.getElementById('accountBtn').onclick = async ()=>{ const r = await api('/api/account'); if(r.account){ document.getElementById('accountInfo').innerHTML = `<div><b>Username:</b> ${escapeHtml(r.account.username)}</div><div><b>Email:</b> ${escapeHtml(r.account.email||'')}</div><div><b>Created:</b> ${escapeHtml(r.account.created_at||'')}</div>`; document.getElementById('accountModal').classList.remove('hidden'); } else alert(JSON.stringify(r)); };
document.getElementById('closeAccountBtn').onclick = ()=>{ document.getElementById('accountModal').classList.add('hidden'); };

document.getElementById('changePassBtn').onclick = async ()=>{
  const oldp = document.getElementById('oldPass').value;
  const newp = document.getElementById('newPass').value;
  if(!oldp || !newp) return alert('Fill both fields');
  const r = await api('/api/account/password', {method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify({old_password: oldp, new_password: newp})});
  if(r.ok) { alert('Password changed'); document.getElementById('accountModal').classList.add('hidden'); }
  else alert(JSON.stringify(r));
};

document.getElementById('adminBtn').onclick = async ()=>{
  document.getElementById('adminModal').classList.remove('hidden');
  const r = await api('/api/admin/users');
  const wrap = document.getElementById('adminUsers');
  wrap.innerHTML = '';
  if(r.users) for(const u of r.users){
    const div = document.createElement('div'); div.className='p-2 border rounded border-gray-800 flex items-center justify-between';
    div.innerHTML = `<div><b>${escapeHtml(u.username)}</b> <span class="text-xs text-gray-400">(${u.email||''})</span><div class="text-xs text-gray-400">created: ${new Date(u.created_at).toLocaleString()}</div></div>`;
    const actions = document.createElement('div');
    const promote = document.createElement('button'); promote.textContent = u.is_admin ? 'Demote' : 'Promote'; promote.className='px-2 py-1 border rounded mr-1';
    promote.onclick = async ()=>{ await api('/api/admin/user/'+u.id, {method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify(u.is_admin?{demote:true}:{promote:true})}); alert('Done'); document.getElementById('adminBtn').click(); };
    const reset = document.createElement('button'); reset.textContent='Reset PW'; reset.className='px-2 py-1 border rounded mr-1';
    reset.onclick = async ()=>{ const np = prompt('New password for '+u.username); if(!np) return; await api('/api/admin/user/'+u.id, {method:'PUT', headers:{'Content-Type':'application/json'}, body: JSON.stringify({reset_password: np})}); alert('Reset'); document.getElementById('adminBtn').click(); };
    const del = document.createElement('button'); del.textContent='Delete'; del.className='px-2 py-1 border rounded text-red-400';
    del.onclick = async ()=>{ if(!confirm('Delete user '+u.username+'?')) return; await api('/api/admin/user/'+u.id, {method:'DELETE'}); alert('Deleted'); document.getElementById('adminBtn').click(); };
    actions.appendChild(promote); actions.appendChild(reset); actions.appendChild(del); div.appendChild(actions); wrap.appendChild(div);
  }
};
document.getElementById('closeAdminBtn').onclick = ()=>{ document.getElementById('adminModal').classList.add('hidden'); };

// load models from server and populate select
async function loadModels(){
  const r = await api('/api/models');
  const sel = document.getElementById('modelSelect');
  sel.innerHTML = '';
  if(r.models) for(const m of r.models){ const o = document.createElement('option'); o.value = m; o.textContent = m; sel.appendChild(o); }
}

// Chat functions
async function loadChats(){
  const j = await api('/api/chats');
  chats = j.chats || [];
  const p = await api('/api/pin_list'); let pinnedMap = {}; if(p.pinned) for(let pc of p.pinned) pinnedMap[pc.chat_id] = pc.pinned_at;
  chats.sort((a,b)=>{ const pa = pinnedMap[a.id]?1:0; const pb = pinnedMap[b.id]?1:0; if(pa!==pb) return pb-pa; return new Date(b.created_at)-new Date(a.created_at); });
  const el = document.getElementById('chats'); el.innerHTML='';
  for(let c of chats){
    const d = document.createElement('div'); d.className='p-2 border rounded cursor-pointer flex items-center justify-between border-gray-800';
    d.innerHTML = `<div><div class="font-semibold">${escapeHtml(c.title)}</div><div class="text-xs text-gray-400">${new Date(c.created_at).toLocaleString()}</div></div><div><button data-id="${c.id}" class="pinBtn px-2 py-1 text-sm border rounded">${pinnedMap[c.id] ? 'Unpin' : 'Pin'}</button></div>`;
    d.onclick = ()=> openChat(c.id);
    el.appendChild(d);
    d.querySelector('.pinBtn').addEventListener('click', async (ev)=>{ ev.stopPropagation(); const id = ev.target.getAttribute('data-id'); const act = pinnedMap[id] ? 'unpin' : 'pin'; await api('/api/pin', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({chat_id:id, action: act})}); await loadChats(); });
  }
}

async function openChat(id){
  currentChat = id;
  const js = await api(`/api/chats/${id}`);
  if(!js.chat) return alert('Chat not found');
  document.getElementById('chatTitle').textContent = js.chat.title;
  document.getElementById('chatInfo').textContent = 'Model: ' + js.chat.model;
  document.getElementById('modelSelect').value = js.chat.model;
  await reloadMessages();
}

async function reloadMessages(){
  if(!currentChat) return;
  const j = await api(`/api/chats/${currentChat}/messages`);
  const ms = j.messages || [];
  const box = document.getElementById('messages'); box.innerHTML='';
  for(let m of ms){
    const d = document.createElement('div');
    if(m.role === 'user'){ d.className='self-end msg bg-indigo-600 text-white p-2 rounded ml-auto max-w-[80%]'; d.textContent = m.content; }
    else if(m.role === 'assistant'){ d.className='self-start msg bg-gray-900 text-white p-2 rounded max-w-[80%]'; d.innerHTML = marked.parse(m.content || ''); }
    else { d.className='self-center msg bg-yellow-600 text-black p-2 rounded mx-auto'; d.textContent = m.content; }
    box.appendChild(d);
  }
  box.scrollTop = box.scrollHeight;
}

document.getElementById('send').onclick = async ()=>{
  if(!currentChat) return alert('Open a chat first');
  const txt = document.getElementById('input').value.trim(); if(!txt) return;
  await api(`/api/chats/${currentChat}/messages`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({role:'user', content: txt})});
  document.getElementById('input').value='';
  await reloadMessages();
  const model = document.getElementById('modelSelect').value;
  await api('/api/generate', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({chat_id: currentChat, temperature: 0.2, maxTokens: 512, model})});
  await reloadMessages();
};

document.getElementById('stream').onclick = async ()=>{
  if(!currentChat) return alert('Open a chat first');
  const txt = document.getElementById('input').value.trim(); if(!txt) return;
  await api(`/api/chats/${currentChat}/messages`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({role:'user', content: txt})});
  document.getElementById('input').value='';
  const evt = new EventSourcePolyfill('/api/generate/stream', {method:'POST', body: JSON.stringify({chat_id: currentChat, temperature:0.2, maxTokens:512, model: document.getElementById('modelSelect').value}), headers:{'Content-Type':'application/json'}});
  const box = document.getElementById('messages');
  const bubble = document.createElement('div'); bubble.className='self-start msg bg-gray-900 text-white p-2 rounded max-w-[80%]'; bubble.textContent='...'; box.appendChild(bubble); box.scrollTop = box.scrollHeight;
  let full = '';
  evt.onmessage = (e)=>{ try{ const d = JSON.parse(e.data); if(d.chunk){ full += d.chunk; bubble.innerHTML = marked.parse(full); box.scrollTop = box.scrollHeight; } if(d.done){ evt.close(); setTimeout(()=>reloadMessages(), 300); } } catch(err){ console.error(err); } };
  evt.onerror = (e)=>{ console.error('SSE error', e); evt.close(); setTimeout(()=>reloadMessages(),200); };
};

document.getElementById('file').addEventListener('change', async (ev)=>{
  if(!currentChat) return alert('Open chat first');
  const f = ev.target.files[0]; if(!f) return;
  const fd = new FormData(); fd.append('file', f);
  const r = await fetch('/api/upload', {method:'POST', body: fd});
  const j = await r.json();
  if(j.ok){ await api(`/api/chats/${currentChat}/messages`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({role:'user', content:`[file] ${j.name}`, attachment: j.path})}); await reloadMessages(); } else alert('Upload error: '+JSON.stringify(j));
});

document.getElementById('exportChat').onclick = async ()=>{ if(!currentChat) return alert('Open chat'); window.location = '/api/chats/'+currentChat+'/export_md'; };
document.getElementById('exportAllBtn').onclick = ()=>{ window.location = '/api/export_all'; };
document.getElementById('clearChat').onclick = async ()=>{ if(!currentChat) return alert('Open chat'); if(!confirm('Clear chat messages?')) return; await api(`/api/chats/${currentChat}`, {method:'DELETE'}); await loadChats(); document.getElementById('messages').innerHTML=''; document.getElementById('chatTitle').textContent='No chat selected'; };
document.getElementById('clearAllBtn').onclick = async ()=>{ if(!confirm('Clear ALL chats?')) return; const r = await api('/api/clear_all',{method:'POST'}); if(r.ok){ alert('Cleared'); await loadChats(); document.getElementById('messages').innerHTML=''; document.getElementById('chatTitle').textContent='No chat selected'; } else alert(JSON.stringify(r)); };

document.getElementById('searchChats').addEventListener('input', (e)=>{
  const q = e.target.value.toLowerCase();
  const el = document.getElementById('chats'); el.innerHTML='';
  for(let c of chats){ if((c.title||'').toLowerCase().includes(q)) { const d = document.createElement('div'); d.className='p-2 border rounded cursor-pointer border-gray-800'; d.innerHTML = `<div class="font-semibold">${escapeHtml(c.title)}</div><div class="text-xs text-gray-400">${new Date(c.created_at).toLocaleString()}</div>`; d.onclick = ()=> openChat(c.id); el.appendChild(d); } }
});

document.getElementById('settingsBtn').addEventListener('click', async ()=>{
  const r = await api('/api/settings');
  if(r.settings){
    document.getElementById('darkTheme').checked = !!r.settings.dark_theme;
  }
});

document.getElementById('pinListBtn').onclick = async ()=>{ const r = await api('/api/pin_list'); alert('Pinned: ' + JSON.stringify(r.pinned || [])); };

document.getElementById('downloadDbBtn').onclick = ()=>{ window.location = '/api/admin/export_db'; };

function EventSourcePolyfill(url, opts){
  const controller = new AbortController();
  const evt = { onmessage:null, onerror:null, close: ()=> controller.abort() };
  (async ()=>{
    try{
      const resp = await fetch(url, {method: opts.method||'GET', body: opts.body, headers: opts.headers||{}, signal: controller.signal});
      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buf = '';
      while(true){
        const {done, value} = await reader.read();
        if(done) break;
        buf += decoder.decode(value, {stream:true});
        let parts = buf.split("\\n\\n");
        buf = parts.pop();
        for(let p of parts){
          if(p.startsWith("data: ")){ const raw = p.slice(6).trim(); if(evt.onmessage) evt.onmessage({data: raw}); }
        }
      }
      if(evt.onmessage) evt.onmessage({data: JSON.stringify({done:true})});
    }catch(e){ if(evt.onerror) evt.onerror(e); }
  })();
  return evt;
}

(async ()=>{ await refreshAuth(); })();
</script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    init_db()
    return render_template_string(INDEX_HTML)

if __name__ == "__main__":
    with app.app_context():
        init_db()
    print(f"Starting OraculAi improved on http://{APP_HOST}:{APP_PORT}")
    app.run(host=APP_HOST, port=APP_PORT)
