import os
import sys
import time
import json
import zipfile
import hashlib
import threading
import sqlite3
import datetime
import traceback
from urllib.parse import urljoin, urlparse, urlsplit

from flask import (
    Flask, render_template_string, request, redirect, url_for, session,
    send_file, jsonify, abort, flash
)
from werkzeug.security import generate_password_hash, check_password_hash

# external libs (try/except to provide a clear message)
try:
    import requests
    from bs4 import BeautifulSoup
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.common.exceptions import WebDriverException
    from webdriver_manager.chrome import ChromeDriverManager
except Exception as e:
    print("Missing packages or Selenium/driver. Install requirements:")
    print("pip install flask selenium webdriver-manager requests beautifulsoup4 lxml werkzeug cryptography")
    raise

# Optional encryption
USE_FERNET = False
FERNET = None
try:
    from cryptography.fernet import Fernet
    USE_FERNET = True
except Exception:
    USE_FERNET = False

# -------- CONFIG --------
BASE_SITE = "https://sites.google.com/view/uzakbaevnurzhan"
DATA_DIR = os.path.join(os.getcwd(), "data")
SITE_COPY_DIR = os.path.join(DATA_DIR, "site_copy")
DB_PATH = os.path.join(DATA_DIR, "app.db")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
SECRET_KEY_FILE = os.path.join(DATA_DIR, "secret.key")
FERNET_KEY_FILE = os.path.join(DATA_DIR, "fernet.key")

AUTO_CHECK_INTERVAL = 60 * 60  # 1 
hour
MAX_VERSIONS_DAYS = 30
MAX_VERSIONS_KEEP = 10
BACKGROUND_THREAD = True

DEFAULT_ADMIN = {
    "username": "uzakbaevnurzhan",
    "password": "ad951qu1",
    "role": "admin",
}

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SITE_COPY_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

# Flask app and secret
if os.path.exists(SECRET_KEY_FILE):
    with open(SECRET_KEY_FILE, "rb") as f:
        secret_bytes = f.read()
else:
    secret_bytes = os.urandom(32)
    with open(SECRET_KEY_FILE, "wb") as f:
        f.write(secret_bytes)

app = Flask(__name__)
app.secret_key = secret_bytes

# Fernet init
if USE_FERNET:
    if os.path.exists(FERNET_KEY_FILE):
        with open(FERNET_KEY_FILE, "rb") as f:
            key = f.read()
    else:
        key = Fernet.generate_key()
        with open(FERNET_KEY_FILE, "wb") as f:
            f.write(key)
    FERNET = Fernet(key)
else:
    FERNET = None

# -------- DB helpers --------
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT,
            role TEXT,
            created_at TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY,
            url TEXT UNIQUE,
            local_path TEXT,
            hash TEXT,
            last_checked TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS versions (
            id INTEGER PRIMARY KEY,
            page_id INTEGER,
            saved_at TEXT,
            content_path TEXT,
            checksum TEXT,
            FOREIGN KEY(page_id) REFERENCES pages(id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit (
            id INTEGER PRIMARY KEY,
            user TEXT,
            action TEXT,
            details TEXT,
            ts TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat (
            id INTEGER PRIMARY KEY,
            user TEXT,
            message TEXT,
            ts TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()

    cur.execute("SELECT * FROM users WHERE username = ?", (DEFAULT_ADMIN["username"],))
    if not cur.fetchone():
        pw_hash = generate_password_hash(DEFAULT_ADMIN["password"])
        cur.execute("INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                    (DEFAULT_ADMIN["username"], pw_hash, DEFAULT_ADMIN["role"], datetime.datetime.utcnow().isoformat()))
        conn.commit()
        log_action(DEFAULT_ADMIN["username"], "create_user", "default admin created")
    conn.close()

def log_action(user, action, details=""):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO audit (user, action, details, ts) VALUES (?, ?, ?, ?)",
                (user or "system", action, details, datetime.datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

init_db()

# -------- utilities --------
def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def save_file(path, content_bytes):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(content_bytes)

def read_file(path):
    with open(path, "rb") as f:
        return f.read()

def encrypt_bytes(b: bytes) -> bytes:
    if FERNET:
        return FERNET.encrypt(b)
    return b

def decrypt_bytes(b: bytes) -> bytes:
    if FERNET:
        return FERNET.decrypt(b)
    return b

# -------- Selenium crawler --------
CHROME_OPTIONS = None

def make_chrome_options():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    # avoid detection (light)
    opts.add_argument("--disable-blink-features=AutomationControlled")
    return opts

def start_selenium_driver():
    global CHROME_OPTIONS
    CHROME_OPTIONS = make_chrome_options()
    try:
        # webdriver-manager auto-downloads compatible chromedriver
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=CHROME_OPTIONS)
        return driver
    except WebDriverException as e:
        print("Selenium Chrome driver start failed:", e)
        raise

def is_same_domain(url):
    try:
        base = urlparse(BASE_SITE).netloc
        target = urlparse(url).netloc
        return (target == base) or (target == "")
    except:
        return False

def normalize_url(url, base=BASE_SITE):
    return urljoin(base, url)

def crawl_with_selenium(start_url=BASE_SITE, max_pages=1000, timeout_per_page=20):
    """
    Use Selenium to visit pages, render JS, and save HTML + inline linked static resources.
    Saves files under SITE_COPY_DIR/<netloc>/<path...>
    """
    print("Starting Selenium crawl (this can take a while)...")
    try:
        driver = start_selenium_driver()
    except Exception as e:
        print("Selenium unavailable:", e)
        return []

    to_visit = [start_url]
    visited = set()
    saved = []
    conn = get_db()
    cur = conn.cursor()

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)
        try:
            driver.set_page_load_timeout(timeout_per_page)
            driver.get(url)
            time.sleep(1.0)  # allow some JS to run; adjust if needed
            html = driver.page_source.encode("utf-8")
            checksum = sha256_bytes(html)

            parsed = urlparse(url)
            # choose filename
            if parsed.path.endswith("/") or parsed.path == "":
                filename = "index.html"
                local_dir = os.path.join(SITE_COPY_DIR, parsed.netloc, parsed.path.lstrip("/"))
            else:
                basefn = os.path.basename(parsed.path)
                if "." not in basefn:
                    filename = basefn + ".html"
                else:
                    filename = basefn
                local_dir = os.path.join(SITE_COPY_DIR, parsed.netloc, os.path.dirname(parsed.path.lstrip("/")))
            os.makedirs(local_dir, exist_ok=True)
            local_path = os.path.join(local_dir, filename)
            save_file(local_path, encrypt_bytes(html))

            # db update
            cur.execute("SELECT id, hash FROM pages WHERE url = ?", (url,))
            row = cur.fetchone()
            now = datetime.datetime.utcnow().isoformat()
            if row:
                page_id = row["id"]
                old_hash = row["hash"]
                if old_hash != checksum:
                    cur.execute("INSERT INTO versions (page_id, saved_at, content_path, checksum) VALUES (?, ?, ?, ?)",
                                (page_id, now, local_path, checksum))
                    cur.execute("UPDATE pages SET local_path = ?, hash = ?, last_checked = ? WHERE id = ?",
                                (local_path, checksum, now, page_id))
                    log_action("system", "page_changed", url)
                else:
                    cur.execute("UPDATE pages SET last_checked = ? WHERE id = ?", (now, page_id))
            else:
                cur.execute("INSERT INTO pages (url, local_path, hash, last_checked) VALUES (?, ?, ?, ?)",
                            (url, local_path, checksum, now))
                log_action("system", "page_saved", url)
            conn.commit()
            saved.append(url)

            # parse links via BeautifulSoup on rendered html
            soup = BeautifulSoup(html, "html.parser")
            # resources (img, script, link)
            for tag, attr in (("img", "src"), ("script", "src"), ("link", "href")):
                for t in soup.find_all(tag):
                    if not t.has_attr(attr):
                        continue
                    link = t[attr]
                    if link.startswith("data:"):
                        continue
                    absolute = normalize_url(link, url)
                    parsed_link = urlparse(absolute)
                    # save static resources same-domain
                    if is_same_domain(absolute):
                        # get resource
                        try:
                            rr = requests.get(absolute, timeout=15)
                            if rr.status_code == 200:
                                pth = os.path.join(SITE_COPY_DIR, parsed_link.netloc, parsed_link.path.lstrip("/"))
                                if parsed_link.path.endswith("/"):
                                    pth = os.path.join(pth, "index")
                                os.makedirs(os.path.dirname(pth), exist_ok=True)
                                save_file(pth, rr.content)
                        except Exception:
                            pass
                    # enqueue same-domain pages (naive)
                    if is_same_domain(absolute):
                        if parsed_link.path and not any(parsed_link.path.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".css", ".js", ".pdf", ".docx", ".zip", ".rar"]):
                            if absolute not in visited and absolute not in to_visit:
                                to_visit.append(absolute)

        except Exception as e:
            print("Error crawling", url, e)
            # continue; don't break whole crawl
            continue

    driver.quit()
    conn.close()
    return saved

# Fallback requests-based crawl (if Selenium fails)
def crawl_with_requests(start_url=BASE_SITE, max_pages=500):
    print("Starting requests-based crawl")
    s = requests.Session()
    s.headers.update({"User-Agent": "SiteMirrorBot/1.0"})
    to_visit = [start_url]
    visited = set()
    conn = get_db()
    cur = conn.cursor()
    saved = []
    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)
        try:
            r = s.get(url, timeout=15)
            if r.status_code != 200:
                continue
            if "text/html" not in r.headers.get("Content-Type",""):
                continue
            html = r.content
            checksum = sha256_bytes(html)
            parsed = urlparse(url)
            if parsed.path.endswith("/") or parsed.path == "":
                filename = "index.html"
                local_dir = os.path.join(SITE_COPY_DIR, parsed.netloc, parsed.path.lstrip("/"))
            else:
                basefn = os.path.basename(parsed.path)
                if "." not in basefn:
                    filename = basefn + ".html"
                else:
                    filename = basefn
                local_dir = os.path.join(SITE_COPY_DIR, parsed.netloc, os.path.dirname(parsed.path.lstrip("/")))
            os.makedirs(local_dir, exist_ok=True)
            local_path = os.path.join(local_dir, filename)
            save_file(local_path, encrypt_bytes(html))
            cur.execute("SELECT id, hash FROM pages WHERE url = ?", (url,))
            row = cur.fetchone()
            now = datetime.datetime.utcnow().isoformat()
            if row:
                page_id = row["id"]
                old_hash = row["hash"]
                if old_hash != checksum:
                    cur.execute("INSERT INTO versions (page_id, saved_at, content_path, checksum) VALUES (?, ?, ?, ?)",
                                (page_id, now, local_path, checksum))
                    cur.execute("UPDATE pages SET local_path = ?, hash = ?, last_checked = ? WHERE id = ?",
                                (local_path, checksum, now, page_id))
                    log_action("system", "page_changed", url)
                else:
                    cur.execute("UPDATE pages SET last_checked = ? WHERE id = ?", (now, page_id))
            else:
                cur.execute("INSERT INTO pages (url, local_path, hash, last_checked) VALUES (?, ?, ?, ?)",
                            (url, local_path, checksum, now))
                log_action("system", "page_saved", url)
            conn.commit()
            saved.append(url)
            soup = BeautifulSoup(html, "lxml")
            for a in soup.find_all("a", href=True):
                href = normalize_url(a["href"], url)
                if is_same_domain(href) and href not in visited and href not in to_visit:
                    to_visit.append(href)
            # resources
            for tag, attr in (("img", "src"), ("script", "src"), ("link", "href")):
                for t in soup.find_all(tag):
                    if not t.has_attr(attr):
                        continue
                    link = t[attr]
                    if link.startswith("data:"):
                        continue
                    absolute = normalize_url(link, url)
                    if is_same_domain(absolute):
                        parsed_link = urlparse(absolute)
                        if any(parsed_link.path.lower().endswith(ext) for ext in [".png",".jpg",".jpeg",".gif",".webp",".svg",".css",".js",".pdf"]):
                            try:
                                rr = s.get(absolute, timeout=15)
                                if rr.status_code == 200:
                                    pth = os.path.join(SITE_COPY_DIR, parsed_link.netloc, parsed_link.path.lstrip("/"))
                                    os.makedirs(os.path.dirname(pth), exist_ok=True)
                                    save_file(pth, rr.content)
                            except:
                                pass
        except Exception as e:
            print("Request crawl error", e)
            continue
    conn.close()
    return saved

def crawl_site(best_effort=True):
    """
    Try Selenium first; if fails and best_effort True, fallback to requests-based crawl.
    """
    try:
        saved = crawl_with_selenium(BASE_SITE)
        if saved:
            return saved
    except Exception as e:
        print("Selenium crawl failed:", e)
    if best_effort:
        return crawl_with_requests(BASE_SITE)
    return []

# -------- update/check --------
def check_for_updates():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT url, hash FROM pages")
    existing = {r["url"]: r["hash"] for r in cur.fetchall()}
    # perform a light check via requests (faster than full selenium)
    s = requests.Session()
    s.headers.update({"User-Agent": "SiteMirrorBot/1.0"})
    to_visit = [BASE_SITE]
    visited = set()
    found = {}
    while to_visit:
        url = to_visit.pop(0)
        if url in visited:
            continue
        visited.add(url)
        try:
            r = s.get(url, timeout=20)
            if r.status_code != 200:
                continue
            if "text/html" not in r.headers.get("Content-Type",""):
                continue
            checksum = sha256_bytes(r.content)
            found[url] = checksum
            soup = BeautifulSoup(r.content, "lxml")
            for a in soup.find_all("a", href=True):
                href = normalize_url(a["href"], url)
                if is_same_domain(href) and href not in visited and href not in to_visit:
                    to_visit.append(href)
        except Exception:
            continue

    changed = []
    new = []
    removed = []
    for url, newhash in found.items():
        if url in existing:
            if existing[url] != newhash:
                changed.append(url)
        else:
            new.append(url)
    for url in existing.keys():
        if url not in found:
            removed.append(url)
    conn.close()
    return {"changed": changed, "new": new, "removed": removed}

# -------- housekeeping & backups --------
def cleanup_old_versions():
    conn = get_db()
    cur = conn.cursor()
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=MAX_VERSIONS_DAYS)
    cutoff_iso = cutoff.isoformat()
    cur.execute("SELECT id, content_path FROM versions WHERE saved_at < ?", (cutoff_iso,))
    rows = cur.fetchall()
    for r in rows:
        try:
            if r["content_path"] and os.path.exists(r["content_path"]):
                os.remove(r["content_path"])
        except:
            pass
    cur.execute("DELETE FROM versions WHERE saved_at < ?", (cutoff_iso,))
    # ensure keep last N per page
    cur.execute("SELECT page_id, COUNT(*) as c FROM versions GROUP BY page_id")
    for r in cur.fetchall():
        pid = r["page_id"]
        cnt = r["c"]
        if cnt > MAX_VERSIONS_KEEP:
            extras = cnt - MAX_VERSIONS_KEEP
            cur2 = conn.cursor()
            cur2.execute("SELECT id, content_path FROM versions WHERE page_id = ? ORDER BY saved_at ASC LIMIT ?", (pid, extras))
            for rem in cur2.fetchall():
                try:
                    if rem["content_path"] and os.path.exists(rem["content_path"]):
                        os.remove(rem["content_path"])
                except:
                    pass
                cur.execute("DELETE FROM versions WHERE id = ?", (rem["id"],))
    conn.commit()
    conn.close()

def make_backup():
    ts = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    backup_name = os.path.join(BACKUP_DIR, f"backup_{ts}.zip")
    with zipfile.ZipFile(backup_name, "w", zipfile.ZIP_DEFLATED) as zf:
        if os.path.exists(DB_PATH):
            zf.write(DB_PATH, arcname="app.db")
        for root, dirs, files in os.walk(SITE_COPY_DIR):
            for f in files:
                full = os.path.join(root, f)
                arc = os.path.relpath(full, DATA_DIR)
                zf.write(full, arcname=arc)
    log_action("system", "backup", backup_name)
    return backup_name

# -------- auth helpers --------
def current_user():
    return session.get("user")

def login_user(username):
    session["user"] = username

def logout_user():
    session.pop("user", None)

def require_login(f):
    from functools import wraps
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user():
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return wrapped

def require_admin(f):
    from functools import wraps
    @wraps(f)
    def wrapped(*args, **kwargs):
        u = current_user()
        if not u:
            return redirect(url_for("login"))
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT role FROM users WHERE username = ?", (u,))
        r = cur.fetchone()
        conn.close()
        if not r or r["role"] != "admin":
            abort(403)
        return f(*args, **kwargs)
    return wrapped

# -------- Templates (stylish UI) --------
BASE_HTML = """
<!doctype html>
<html lang="ru" data-theme="{{ theme }}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mirror • {{ base_site }}</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css">
  <style>
    :root[data-theme='dark']{
      --bg: #0b1220; --card: #0f1724; --muted:#98a0b3; --accent:#60a5fa; --text:#e6eef8;
    }
    :root[data-theme='light']{
      --bg: #f4f6fb; --card:#ffffff; --muted:#6b7280; --accent:#0ea5e9; --text:#0f1724;
    }
    body { background: linear-gradient(180deg, var(--bg), rgba(0,0,0,0.02)); color:var(--text); }
    .card { background: var(--card); color:var(--text); border: none; box-shadow: 0 6px 18px rgba(2,6,23,0.2); }
    .nav-link, .navbar-brand { color: var(--text) !important; }
    .small-muted { color: var(--muted); }
    .btn-accent { background: linear-gradient(90deg,var(--accent), #4f46e5); color: white; border: none; }
    .site-iframe { width: 100%; height: 70vh; border-radius: 8px; border: none; }
    @media (max-width: 768px){
      .site-iframe { height: 55vh; }
    }
  </style>
</head>
<body>
<nav class="navbar navbar-expand-lg py-2" style="background:transparent">
  <div class="container">
    <a class="navbar-brand fw-bold" href="/">Mirror</a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#mynav">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="mynav">
      <ul class="navbar-nav me-auto mb-2 mb-lg-0">
        <li class="nav-item"><a class="nav-link" href="/">Главная</a></li>
        <li class="nav-item"><a class="nav-link" href="/pages">Страницы</a></li>
        <li class="nav-item"><a class="nav-link" href="/audit">Журнал</a></li>
        <li class="nav-item"><a class="nav-link" href="/chat">Чат</a></li>
        {% if is_admin %}
        <li class="nav-item"><a class="nav-link" href="/admin">Админ</a></li>
        {% endif %}
      </ul>
      <div class="d-flex align-items-center">
        <button class="btn btn-sm me-2" onclick="toggleTheme()" title="Toggle theme"><i class="fa fa-moon"></i></button>
        {% if user %}
          <div class="me-2 small-muted">Привет, <b>{{ user }}</b></div>
          <a class="btn btn-outline-light btn-sm me-2" href="/change_password">Сменить пароль</a>
          <a class="btn btn-sm btn-outline-light" href="/logout">Выйти</a>
        {% else %}
          <a class="btn btn-sm btn-primary" href="/login">Войти</a>
        {% endif %}
      </div>
    </div>
  </div>
</nav>

<div class="container py-4">
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <div class="alert alert-info">
        {% for m in messages %}<div>{{m}}</div>{% endfor %}
      </div>
    {% endif %}
  {% endwith %}
  {{ body | safe }}
  <footer class="mt-4 small-muted text-center">Mirror • локальная копия <a href="{{ base_site }}" style="color:inherit">{{ base_site }}</a></footer>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
<script>
  const themeKey = "sm_theme";
  function applyTheme(){
    const t = localStorage.getItem(themeKey) || "{{ theme }}";
    document.documentElement.setAttribute("data-theme", t);
  }
  function toggleTheme(){
    const cur = localStorage.getItem(themeKey) || "{{ theme }}";
    const next = cur === "light" ? "dark" : "light";
    localStorage.setItem(themeKey, next);
    applyTheme();
  }
  applyTheme();
</script>
</body>
</html>
"""

INDEX_BODY = """
<div class="row g-3">
  <div class="col-lg-8">
    <div class="card p-4">
      <div class="d-flex justify-content-between align-items-start">
        <div>
          <h4 class="mb-1">Локальная копия</h4>
          <div class="small-muted">Сайт: <b>{{ base_site }}</b></div>
          <div class="small-muted">Страниц: {{ pages_count }}</div>
        </div>
        <div class="text-end">
          <button class="btn btn-accent mb-2" onclick="checkUpdates()"><i class="fa fa-sync"></i> Проверить обновления</button>
          <button class="btn btn-outline-light mb-2" onclick="fetch('/do_update',{method:'POST'}).then(r=>r.json()).then(j=>alert(j.msg))">Обновить локально</button>
          <a class="btn btn-light mb-2" href="/download_backup">Скачать бекап</a>
        </div>
      </div>
      <hr class="my-3">
      <div id="status_box" class="mb-3 small-muted"></div>
      <h6>Страницы (последние)</h6>
      <div style="max-height:45vh; overflow:auto;">
        <ul class="list-unstyled">
          {% for p in pages %}
            <li class="py-1"><i class="fa fa-file-lines me-2"></i><a href="/view?page={{p|urlencode}}">{{p}}</a></li>
          {% endfor %}
        </ul>
      </div>
    </div>
  </div>
  <div class="col-lg-4">
    <div class="card p-3">
      <h6>Панель</h6>
      <div class="small-muted">Быстрые действия</div>
      <ul class="mt-2">
        <li>Журнал: <a href="/audit">Открыть</a></li>
        <li>Чат: <a href="/chat">Открыть</a></li>
        {% if is_admin %}<li>Админ: <a href="/admin">Панель</a></li>{% endif %}
      </ul>
    </div>
    <div class="card p-3 mt-3">
      <h6>Настройки</h6>
      <div class="small-muted">Текущая тема: <b id="cur_theme"></b></div>
      <script>document.getElementById('cur_theme').innerText = localStorage.getItem('sm_theme') || '{{ theme }}';</script>
    </div>
  </div>
</div>

<script>
function checkUpdates(){
  const box = document.getElementById('status_box');
  box.innerHTML = 'Проверка...';
  fetch('/check_updates').then(r=>r.json()).then(j=>{
    box.innerHTML = '<pre>' + JSON.stringify(j, null, 2) + '</pre>';
    if ((j.changed && j.changed.length) || (j.new && j.new.length)) {
      if (confirm("Обнаружены изменения. Обновить локальную копию?")) {
        fetch('/do_update', {method:'POST'}).then(r=>r.json()).then(x=>alert(x.msg));
      }
    } else {
      alert("Изменений не найдено");
    }
  }).catch(e=>{box.innerText='Ошибка: '+e});
}
</script>
"""

LOGIN_BODY = """
<div class="row justify-content-center">
  <div class="col-md-6">
    <div class="card p-4">
      <h4>Вход</h4>
      <form method="post" action="/login">
        <div class="mb-3"><label class="form-label">Логин</label><input name="username" class="form-control" required></div>
        <div class="mb-3"><label class="form-label">Пароль</label><input name="password" type="password" class="form-control" required></div>
        <div class="d-flex justify-content-between">
          <button class="btn btn-accent">Войти</button>
          <a class="btn btn-outline-light" href="/">Отмена</a>
        </div>
      </form>
      <div class="small-muted mt-3">Админ: uzakbaevnurzhan (поменяй пароль после входа)</div>
    </div>
  </div>
</div>
"""

PAGES_BODY = """
<div class="card p-3">
  <h4>Страницы ({{ pages_count }})</h4>
  <ul>
    {% for p in pages %}
      <li class="py-1"><a href="/view?page={{p|urlencode}}">{{p}}</a> — <a href="/download_page?url={{p|urlencode}}">скачать</a></li>
    {% endfor %}
  </ul>
</div>
"""

VIEW_BODY = """
<div class="card p-3">
  <h5>Просмотр</h5>
  <div class="small-muted mb-2">Страница: {{ page }}</div>
  <iframe id="iframe" class="site-iframe"></iframe>
  <div class="mt-2">
    <a class="btn btn-outline-light" href="/raw?page={{page|urlencode}}">Исходник</a>
    <a class="btn btn-outline-light" href="/download_page?url={{page|urlencode}}">Скачать файл</a>
  </div>
</div>
<script>
fetch('/raw?page={{page|urlencode}}').then(r=>r.text()).then(html=>{
  const ifr = document.getElementById('iframe');
  const doc = ifr.contentWindow.document;
  doc.open();
  doc.write(html);
  doc.close();
});
</script>
"""

AUDIT_BODY = """
<div class="card p-3">
  <h4>Журнал</h4>
  <ul>
    {% for a in audit %}
      <li><b>{{a.user}}</b> — {{a.action}} <small class="small-muted">({{a.ts}})</small><div class="small-muted">{{a.details}}</div></li>
    {% endfor %}
  </ul>
</div>
"""

CHAT_BODY = """
<div class="card p-3">
  <h4>Чат</h4>
  <div id="messages" style="max-height:40vh; overflow:auto; padding:8px; background:rgba(255,255,255,0.02); border-radius:6px;">
    {% for m in messages %}
      <div class="mb-2"><b>{{m.user}}</b> <small class="small-muted">({{m.ts}})</small>: {{m.message}}</div>
    {% endfor %}
  </div>
  <form id="chatform" onsubmit="event.preventDefault(); sendMsg();">
    <div class="input-group mt-2">
      <input id="chatmsg" class="form-control" placeholder="Сообщение">
      <button class="btn btn-accent">Отправить</button>
    </div>
  </form>
</div>
<script>
function sendMsg(){
  const txt = document.getElementById('chatmsg').value;
  if(!txt) return;
  fetch('/chat_send', {method:'POST', body: JSON.stringify({message: txt}), headers: {'Content-Type':'application/json'}})
    .then(r=>r.json()).then(j=>{ if(j.ok) location.reload(); else alert('Ошибка'); });
}
</script>
"""

ADMIN_BODY = """
<div class="card p-3">
  <h4>Админ-панель</h4>
  <div class="row">
    <div class="col-md-6">
      <h6>Статистика</h6>
      <ul>
        <li>Страниц: {{ pages_count }}</li>
        <li>Версий: {{ versions_count }}</li>
        <li>Размер копии: {{ site_size_mb }} MB</li>
      </ul>
      <hr>
      <h6>Пользователи</h6>
      <ul>
        {% for u in users %}
          <li>{{u.username}} — {{u.role}} — {{u.created_at}}</li>
        {% endfor %}
      </ul>
    </div>
    <div class="col-md-6">
      <h6>Действия</h6>
      <form method="post" action="/admin/create_user" class="mb-3">
        <input name="username" class="form-control mb-1" placeholder="username">
        <input name="password" class="form-control mb-1" placeholder="password">
        <select name="role" class="form-control mb-2"><option value="user">user</option><option value="admin">admin</option></select>
        <button class="btn btn-accent">Создать</button>
      </form>
      <form method="post" action="/admin/cleanup" onsubmit="return confirm('Очистить старые версии?')">
        <button class="btn btn-warning">Очистить старые версии</button>
      </form>
      <form method="post" action="/admin/force_crawl" class="mt-2">
        <button class="btn btn-outline-light">Принудительный crawl (Selenium)</button>
      </form>
    </div>
  </div>
</div>
"""

CHANGE_PW_BODY = """
<div class="card p-3">
  <h4>Сменить пароль</h4>
  <form method="post" action="/change_password">
    <div class="mb-2"><label>Старый пароль</label><input name="old" type="password" class="form-control"></div>
    <div class="mb-2"><label>Новый пароль</label><input name="new" type="password" class="form-control"></div>
    <button class="btn btn-accent">Сменить</button>
  </form>
</div>
"""

# -------- Routes --------
@app.route("/")
def index():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT url FROM pages ORDER BY last_checked DESC LIMIT 200")
    pages = [r["url"] for r in cur.fetchall()]
    cur.execute("SELECT COUNT(*) as c FROM pages")
    pages_count = cur.fetchone()["c"]
    conn.close()
    return render_template_string(BASE_HTML, body=render_template_string(INDEX_BODY, pages=pages, pages_count=pages_count, base_site=BASE_SITE), user=current_user(), is_admin=is_admin_user(), base_site=BASE_SITE, theme=get_theme())

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "GET":
        return render_template_string(BASE_HTML, body=LOGIN_BODY, user=current_user(), is_admin=is_admin_user(), theme=get_theme(), base_site=BASE_SITE)
    username = request.form.get("username")
    password = request.form.get("password")
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT username, password_hash FROM users WHERE username = ?", (username,))
    r = cur.fetchone()
    conn.close()
    if not r or not check_password_hash(r["password_hash"], password):
        flash("Неверные учётные данные")
        return redirect(url_for("login"))
    login_user(username)
    log_action(username, "login", "successful")
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    u = current_user()
    logout_user()
    if u:
        log_action(u, "logout", "")
    return redirect(url_for("index"))

@app.route("/pages")
@require_login
def pages():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT url FROM pages ORDER BY last_checked DESC")
    pages = [r["url"] for r in cur.fetchall()]
    conn.close()
    return render_template_string(BASE_HTML, body=render_template_string(PAGES_BODY, pages=pages, pages_count=len(pages)), user=current_user(), is_admin=is_admin_user(), theme=get_theme(), base_site=BASE_SITE)

@app.route("/view")
@require_login
def view_page():
    page = request.args.get("page")
    if not page:
        return redirect(url_for("pages"))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT local_path FROM pages WHERE url = ?", (page,))
    r = cur.fetchone()
    conn.close()
    if not r:
        flash("Страница не найдена")
        return redirect(url_for("pages"))
    local_path = r["local_path"]
    return render_template_string(BASE_HTML, body=render_template_string(VIEW_BODY, page=page, local_path=local_path), user=current_user(), is_admin=is_admin_user(), theme=get_theme(), base_site=BASE_SITE)

@app.route("/raw")
@require_login
def raw():
    page = request.args.get("page")
    if not page:
        abort(400)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT local_path FROM pages WHERE url = ?", (page,))
    r = cur.fetchone()
    conn.close()
    if not r:
        abort(404)
    p = r["local_path"]
    if not os.path.exists(p):
        abort(404)
    data = read_file(p)
    try:
        data = decrypt_bytes(data)
    except Exception:
        pass
    try:
        text = data.decode("utf-8", errors="ignore")
    except:
        text = "<pre>binary</pre>"
    return text

@app.route("/download_page")
@require_login
def download_page():
    url = request.args.get("url")
    if not url:
        abort(400)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT local_path FROM pages WHERE url = ?", (url,))
    r = cur.fetchone()
    conn.close()
    if not r:
        abort(404)
    p = r["local_path"]
    if not os.path.exists(p):
        abort(404)
    return send_file(p, as_attachment=True, download_name=os.path.basename(p))

@app.route("/check_updates")
@require_login
def route_check_updates():
    res = check_for_updates()
    return jsonify(res)

@app.route("/do_update", methods=["POST"])
@require_login
def route_do_update():
    try:
        saved = crawl_site(best_effort=True)
        cleanup_old_versions()
        msg = f"Обновлено {len(saved)} элементов."
        log_action(current_user(), "manual_update", msg)
        return jsonify({"ok": True, "msg": msg, "saved": saved})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "msg": str(e)}), 500

@app.route("/download_backup")
@require_login
def download_backup():
    backup = make_backup()
    return send_file(backup, as_attachment=True, download_name=os.path.basename(backup))

@app.route("/audit")
@require_login
def audit():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT user, action, details, ts FROM audit ORDER BY ts DESC LIMIT 300")
    rows = cur.fetchall()
    conn.close()
    return render_template_string(BASE_HTML, body=render_template_string(AUDIT_BODY, audit=rows), user=current_user(), is_admin=is_admin_user(), theme=get_theme(), base_site=BASE_SITE)

@app.route("/chat")
@require_login
def chat():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT user, message, ts FROM chat ORDER BY ts DESC LIMIT 200")
    rows = cur.fetchall()
    conn.close()
    messages = list(reversed(rows))
    return render_template_string(BASE_HTML, body=render_template_string(CHAT_BODY, messages=messages), user=current_user(), is_admin=is_admin_user(), theme=get_theme(), base_site=BASE_SITE)

@app.route("/chat_send", methods=["POST"])
@require_login
def chat_send():
    data = request.json or {}
    msg = data.get("message", "").strip()
    if not msg:
        return jsonify({"ok": False, "err": "empty"})
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO chat (user, message, ts) VALUES (?, ?, ?)",
                (current_user(), msg, datetime.datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    log_action(current_user(), "chat_send", msg[:200])
    return jsonify({"ok": True})

@app.route("/admin")
@require_login
@require_admin
def admin():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM pages")
    pages_count = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) as c FROM versions")
    versions_count = cur.fetchone()["c"]
    size = 0
    for root, dirs, files in os.walk(SITE_COPY_DIR):
        for f in files:
            size += os.path.getsize(os.path.join(root, f))
    site_size_mb = round(size / (1024*1024), 2)
    cur.execute("SELECT username, role, created_at FROM users")
    users = cur.fetchall()
    conn.close()
    return render_template_string(BASE_HTML, body=render_template_string(ADMIN_BODY, pages_count=pages_count, versions_count=versions_count, site_size_mb=site_size_mb, users=users), user=current_user(), is_admin=True, theme=get_theme(), base_site=BASE_SITE)

@app.route("/admin/create_user", methods=["POST"])
@require_login
@require_admin
def admin_create_user():
    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role", "user")
    if not username or not password:
        flash("Заполните поля")
        return redirect(url_for("admin"))
    pw_hash = generate_password_hash(password)
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (username, password_hash, role, created_at) VALUES (?, ?, ?, ?)",
                    (username, pw_hash, role, datetime.datetime.utcnow().isoformat()))
        conn.commit()
        log_action(current_user(), "create_user", username)
        flash("Пользователь создан")
    except Exception as e:
        flash("Ошибка: " + str(e))
    conn.close()
    return redirect(url_for("admin"))

@app.route("/admin/cleanup", methods=["POST"])
@require_login
@require_admin
def admin_cleanup():
    cleanup_old_versions()
    flash("Очистка выполнена")
    return redirect(url_for("admin"))

@app.route("/admin/force_crawl", methods=["POST"])
@require_login
@require_admin
def admin_force_crawl():
    try:
        saved = crawl_site(best_effort=True)
        cleanup_old_versions()
        flash(f"Принудительное обновление: {len(saved)} элементов.")
    except Exception as e:
        flash("Ошибка при crawl: " + str(e))
    return redirect(url_for("admin"))

@app.route("/change_password", methods=["GET","POST"])
@require_login
def change_password():
    if request.method == "GET":
        return render_template_string(BASE_HTML, body=CHANGE_PW_BODY, user=current_user(), is_admin=is_admin_user(), theme=get_theme(), base_site=BASE_SITE)
    old = request.form.get("old")
    new = request.form.get("new")
    if not old or not new:
        flash("Заполните поля")
        return redirect(url_for("change_password"))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE username = ?", (current_user(),))
    r = cur.fetchone()
    if not r or not check_password_hash(r["password_hash"], old):
        flash("Неверный старый пароль")
        conn.close()
        return redirect(url_for("change_password"))
    cur.execute("UPDATE users SET password_hash = ? WHERE username = ?", (generate_password_hash(new), current_user()))
    conn.commit()
    conn.close()
    log_action(current_user(), "change_password", "user changed their password")
    flash("Пароль изменён")
    return redirect(url_for("index"))

@app.route("/search")
@require_login
def search():
    q = request.args.get("q", "").strip().lower()
    if not q:
        return redirect(url_for("index"))
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT url FROM pages")
    results = []
    for r in cur.fetchall():
        p = r["url"]
        if q in p.lower():
            results.append(p)
        else:
            curpath = conn.execute("SELECT local_path FROM pages WHERE url = ?", (p,)).fetchone()
            if curpath:
                lp = curpath["local_path"]
                try:
                    data = read_file(lp)
                    data = decrypt_bytes(data)
                    if q in data.decode("utf-8", errors="ignore").lower():
                        results.append(p)
                except:
                    pass
    conn.close()
    return render_template_string(BASE_HTML, body=render_template_string(PAGES_BODY, pages=results, pages_count=len(results)), user=current_user(), is_admin=is_admin_user(), theme=get_theme(), base_site=BASE_SITE)

# -------- helpers --------
def is_admin_user():
    u = current_user()
    if not u:
        return False
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT role FROM users WHERE username = ?", (u,))
    r = cur.fetchone()
    conn.close()
    return bool(r and r["role"] == "admin")

def get_theme():
    return "dark"  # default theme on server (client can toggle via localStorage)

# -------- background worker --------
def background_worker():
    while True:
        try:
            print("[bg] periodic update check")
            res = check_for_updates()
            if res["changed"] or res["new"]:
                log_action("system", "auto_updates_found", json.dumps(res))
                # Do not auto-apply; admin decides.
            cleanup_old_versions()
        except Exception as e:
            print("bg error", e)
        time.sleep(AUTO_CHECK_INTERVAL)

if BACKGROUND_THREAD:
    t = threading.Thread(target=background_worker, daemon=True)
    t.start()

# initial seed crawl if DB empty
def initial_seed():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as c FROM pages")
    if cur.fetchone()["c"] == 0:
        print("DB empty — initial crawl running (Selenium preferred)...")
        try:
            crawl_site(best_effort=True)
        except Exception as e:
            print("Initial crawl error:", e)
    conn.close()

initial_seed()

if __name__ == "__main__":
    print("Starting app. Base site:", BASE_SITE)
    app.run(debug=True, host="0.0.0.0", port=5000)
