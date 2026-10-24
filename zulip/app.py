"""Zulip - Flask application.

Original Foundev implementation. SQLite via the standard library, server-rendered
Jinja templates, session auth and a small JSON API.
"""
import json
import os
import re
import secrets
import sqlite3
from datetime import date, datetime, timezone
from functools import wraps

from chat import (
    DEFAULT_TOPIC,
    clean_topic,
    is_valid_topic,
    render_markdown,
    search_messages,
    stream_summary,
    thread_summary,
    topic_key,
    unread_counts,
    validate_message,
)

from flask import (Flask, abort, flash, g, jsonify, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(BASE_DIR, "data"))
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.environ.get("APP_DB", os.path.join(DATA_DIR, "app.db"))

with open(os.path.join(BASE_DIR, "config.json"), encoding="utf-8") as fh:
    CONFIG = json.load(fh)

app = Flask(__name__)


def _secret():
    value = os.environ.get("SECRET_KEY")
    if value:
        return value
    path = os.path.join(DATA_DIR, "secret.key")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read().strip()
    value = secrets.token_hex(32)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(value)
    return value


app.secret_key = _secret()
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")

TYPE_SQL = {"text": "TEXT", "int": "INTEGER", "real": "REAL", "bool": "INTEGER"}


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      email TEXT NOT NULL UNIQUE,
      password TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'member',
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS sessions_audit (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL,
      action TEXT NOT NULL,
      created_at TEXT NOT NULL
    );
    """)
    for resource in CONFIG["resources"]:
        cols = []
        for field in resource["fields"]:
            cols.append(f'"{field["name"]}" {TYPE_SQL.get(field.get("type", "text"), "TEXT")}')
        db.execute(f"""CREATE TABLE IF NOT EXISTS "{resource["name"]}" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {", ".join(cols)},
            created_at TEXT NOT NULL
        )""")
        count = db.execute(f'SELECT COUNT(*) FROM "{resource["name"]}"').fetchone()[0]
        rows = CONFIG.get("seed", {}).get(resource["name"], [])
        if count == 0 and rows:
            for row in rows:
                keys = list(row)
                marks = ",".join("?" for _ in keys)
                db.execute(
                    f'INSERT INTO "{resource["name"]}" ({",".join(chr(34)+k+chr(34) for k in keys)}, created_at) '
                    f'VALUES ({marks}, ?)',
                    [row[k] for k in keys] + [datetime.now(timezone.utc).isoformat(timespec="seconds")],
                )
    if CONFIG.get("special") == "chat":
        db.execute("""CREATE TABLE IF NOT EXISTS read_markers (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          stream TEXT NOT NULL,
          topic TEXT NOT NULL,
          user_id INTEGER NOT NULL,
          message_id INTEGER NOT NULL,
          updated_at TEXT NOT NULL
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS topic_subscriptions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          stream TEXT NOT NULL,
          topic TEXT NOT NULL,
          user_id INTEGER NOT NULL,
          created_at TEXT NOT NULL
        )""")
    if CONFIG.get("special") == "commerce":
        db.execute("""CREATE TABLE IF NOT EXISTS order_items (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          order_id INTEGER NOT NULL,
          product_id INTEGER NOT NULL,
          name TEXT NOT NULL,
          quantity INTEGER NOT NULL,
          unit_cents INTEGER NOT NULL
        )""")
    db.commit()
    db.close()


init_db()


def resource_by_name(name):
    return next((r for r in CONFIG["resources"] if r["name"] == name), None)


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(24)
    return session["csrf"]


def check_csrf():
    token = request.form.get("csrf") or request.headers.get("X-CSRF-Token")
    if not token or token != session.get("csrf"):
        abort(400, description="Invalid CSRF token")


@app.template_filter("markdown")
def markdown_filter(text):
    """Render the markdown of a message."""
    return render_markdown(text)


@app.before_request
def load_user():
    g.user = None
    uid = session.get("user_id")
    if uid:
        row = get_db().execute("SELECT id, name, email, role FROM users WHERE id = ?", (uid,)).fetchone()
        g.user = dict(row) if row else None


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not g.user:
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


@app.context_processor
def inject():
    return {"config": CONFIG, "user": g.get("user"), "csrf": csrf_token(),
            "today": date.today().isoformat()}


@app.route("/")
def home():
    db = get_db()
    counts = {r["name"]: db.execute(f'SELECT COUNT(*) FROM "{r["name"]}"').fetchone()[0]
              for r in CONFIG["resources"]}
    labels = {r["name"]: r["label"] for r in CONFIG["resources"]}
    extra = {}
    if CONFIG.get("special") == "commerce":
        extra["revenue_cents"] = db.execute(
            "SELECT COALESCE(SUM(total_cents),0) FROM orders WHERE status != 'cancelled'").fetchone()[0]
        extra["open_orders"] = db.execute(
            "SELECT COUNT(*) FROM orders WHERE status = 'paid'").fetchone()[0]
    return render_template("home.html", counts=counts, labels=labels, extra=extra)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        check_csrf()
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        if not name or "@" not in email or len(password) < 8:
            flash("Name, a valid email and an 8+ character password are required.", "error")
            return redirect(url_for("register"))
        db = get_db()
        first = db.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0
        try:
            cur = db.execute(
                "INSERT INTO users (name, email, password, role, created_at) VALUES (?,?,?,?,?)",
                (name, email, generate_password_hash(password), "owner" if first else "member",
                 datetime.now(timezone.utc).isoformat(timespec="seconds")))
            db.commit()
        except sqlite3.IntegrityError:
            flash("That email is already registered.", "error")
            return redirect(url_for("register"))
        session.clear()
        session["user_id"] = cur.lastrowid
        flash("Account created.")
        return redirect(url_for("home"))
    return render_template("auth.html", mode="register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        check_csrf()
        email = (request.form.get("email") or "").strip().lower()
        row = get_db().execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if row and check_password_hash(row["password"], request.form.get("password") or ""):
            session.clear()
            session["user_id"] = row["id"]
            flash(f"Welcome back, {row['name']}.")
            return redirect(request.args.get("next") or url_for("home"))
        flash("Invalid email or password.", "error")
    return render_template("auth.html", mode="login")


@app.route("/logout", methods=["POST"])
def logout():
    check_csrf()
    session.clear()
    flash("Signed out.")
    return redirect(url_for("home"))


def validate(resource, form):
    values, errors = {}, []
    for field in resource["fields"]:
        raw = form.get(field["name"])
        if field.get("required") and (raw is None or raw == ""):
            errors.append(f'{field.get("label", field["name"])} is required.')
            continue
        if raw is None or raw == "":
            values[field["name"]] = None
            continue
        kind = field.get("type", "text")
        if kind == "int":
            try:
                values[field["name"]] = int(raw)
            except ValueError:
                errors.append(f'{field.get("label", field["name"])} must be a number.')
        elif kind == "real":
            try:
                values[field["name"]] = float(raw)
            except ValueError:
                errors.append(f'{field.get("label", field["name"])} must be a number.')
        elif kind == "bool":
            values[field["name"]] = 1 if raw in ("1", "true", "on", "yes") else 0
        else:
            values[field["name"]] = raw.strip()
    return values, errors


@app.route("/r/<name>")
def resource_list(name):
    resource = resource_by_name(name) or abort(404)
    q = (request.args.get("q") or "").strip()
    sql = f'SELECT * FROM "{name}"'
    params = []
    if q:
        text_fields = [f["name"] for f in resource["fields"] if f.get("type", "text") == "text"]
        if text_fields:
            sql += " WHERE " + " OR ".join(f'"{f}" LIKE ?' for f in text_fields)
            params = [f"%{q}%"] * len(text_fields)
    sql += " ORDER BY id DESC LIMIT 200"
    items = get_db().execute(sql, params).fetchall()
    return render_template("list.html", resource=resource, items=items, q=q)


@app.route("/r/<name>/new", methods=["GET", "POST"])
@login_required
def resource_new(name):
    resource = resource_by_name(name) or abort(404)
    errors = []
    item = {}
    if request.method == "POST":
        check_csrf()
        values, errors = validate(resource, request.form)
        if not errors:
            keys = list(values)
            db = get_db()
            cur = db.execute(
                f'INSERT INTO "{name}" ({",".join(chr(34)+k+chr(34) for k in keys)}, created_at) '
                f'VALUES ({",".join("?" for _ in keys)}, ?)',
                [values[k] for k in keys] + [datetime.now(timezone.utc).isoformat(timespec="seconds")])
            db.commit()
            if CONFIG.get("special") == "wiki" and name == "pages":
                return redirect(url_for("wiki_page", page_id=cur.lastrowid))
            flash(f'{resource["label"]} created.')
            return redirect(url_for("resource_list", name=name))
        item = dict(request.form)
    return render_template("form.html", resource=resource, item=item, errors=errors, editing=False)


@app.route("/r/<name>/<int:item_id>")
def resource_detail(name, item_id):
    resource = resource_by_name(name) or abort(404)
    item = get_db().execute(f'SELECT * FROM "{name}" WHERE id = ?', (item_id,)).fetchone()
    if not item:
        abort(404)
    return render_template("detail.html", resource=resource, item=item)


@app.route("/r/<name>/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def resource_edit(name, item_id):
    resource = resource_by_name(name) or abort(404)
    db = get_db()
    item = db.execute(f'SELECT * FROM "{name}" WHERE id = ?', (item_id,)).fetchone()
    if not item:
        abort(404)
    errors = []
    if request.method == "POST":
        check_csrf()
        values, errors = validate(resource, request.form)
        if not errors:
            if CONFIG.get("special") == "wiki" and name == "pages":
                db.execute(
                    "INSERT INTO page_revisions (page_id, title, body, version, created_at) VALUES (?,?,?,?,?)",
                    (item_id, item["title"], item["body"], item["version"] or 1,
                     datetime.now(timezone.utc).isoformat(timespec="seconds")))
                values["version"] = (item["version"] or 1) + 1
            keys = list(values)
            db.execute(
                f'UPDATE "{name}" SET {", ".join(chr(34)+k+chr(34)+" = ?" for k in keys)} WHERE id = ?',
                [values[k] for k in keys] + [item_id])
            db.commit()
            flash("Changes saved.")
            if CONFIG.get("special") == "wiki" and name == "pages":
                return redirect(url_for("wiki_page", page_id=item_id))
            return redirect(url_for("resource_list", name=name))
        item = dict(item)
        item.update(request.form)
    return render_template("form.html", resource=resource, item=item, errors=errors, editing=True)


@app.route("/r/<name>/<int:item_id>/delete", methods=["POST"])
@login_required
def resource_delete(name, item_id):
    resource_by_name(name) or abort(404)
    check_csrf()
    db = get_db()
    db.execute(f'DELETE FROM "{name}" WHERE id = ?', (item_id,))
    db.commit()
    flash("Record deleted.")
    return redirect(url_for("resource_list", name=name))



# ------------------------------------------------------------------ #
# The chat                                                            #
# ------------------------------------------------------------------ #
def _streams(db):
    return [dict(row) for row in db.execute('SELECT * FROM "channels" ORDER BY name COLLATE NOCASE').fetchall()]


def _messages(db, stream_id=None):
    if stream_id is None:
        rows = db.execute('SELECT * FROM "messages" ORDER BY id ASC').fetchall()
    else:
        rows = db.execute('SELECT * FROM "messages" WHERE channel_id = ? ORDER BY id ASC', (stream_id,)).fetchall()
    streams = {int(s["id"]): s for s in _streams(db)}
    out = []
    for row in rows:
        message = dict(row)
        stream = streams.get(int(message.get("channel_id") or -1))
        message["stream_name"] = stream["name"] if stream else ""
        out.append(message)
    return out


@app.get("/api/streams")
@login_required
def api_streams():
    db = get_db()
    streams = _streams(db)
    messages = _messages(db)
    markers = [dict(r) for r in db.execute("SELECT * FROM read_markers").fetchall()]
    return jsonify({
        "streams": stream_summary(streams, messages),
        "unread": unread_counts(messages, markers),
    })


@app.get("/api/streams/<int:stream_id>")
@login_required
def api_stream(stream_id):
    db = get_db()
    stream = db.execute('SELECT * FROM "channels" WHERE id = ?', (stream_id,)).fetchone()
    if not stream:
        abort(404)
    messages = _messages(db, stream_id)
    markers = [dict(r) for r in db.execute("SELECT * FROM read_markers").fetchall()]
    return jsonify({
        "stream": dict(stream),
        "threads": thread_summary(messages, _streams(db)),
        "unread": unread_counts(messages, markers),
    })


@app.post("/api/messages")
@login_required
def api_send_message():
    check_csrf()
    db = get_db()
    streams = _streams(db)
    values = {
        "channel_id": request.form.get("channel_id"),
        "channel_name": request.form.get("channel_name"),
        "topic": request.form.get("topic") or DEFAULT_TOPIC,
        "body": request.form.get("body") or "",
        "sender": g.user["name"] if g.user else "unknown",
    }
    problem = validate_message(values, streams)
    if problem:
        return jsonify({"error": problem}), 400

    stream_name = clean_topic(values["channel_name"])
    stream = next((s for s in streams if clean_topic(s["name"]).lower() == stream_name.lower()), None)
    if stream is None and values.get("channel_id"):
        stream = next((s for s in streams if int(s["id"]) == int(values["channel_id"])), None)
    if stream is None:
        return jsonify({"error": "The stream does not exist."}), 400

    topic = clean_topic(values["topic"])
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    cursor = db.execute(
        'INSERT INTO "messages" ("channel_id", "sender", "topic", "body", "created_at") VALUES (?,?,?,?,?)',
        (stream["id"], values["sender"], topic, values["body"].strip(), created),
    )
    db.commit()
    return jsonify({
        "id": cursor.lastrowid,
        "channel_id": stream["id"],
        "stream_name": stream["name"],
        "topic": topic,
        "sender": values["sender"],
        "body": values["body"].strip(),
        "created_at": created,
    }), 201


@app.get("/api/search")
@login_required
def api_search():
    query = (request.args.get("q") or "").strip()
    messages = _messages(get_db())
    found = search_messages(messages, query)
    return jsonify({
        "query": query,
        "count": len(found),
        "messages": [
            {
                "id": m["id"],
                "stream_name": m.get("stream_name", ""),
                "topic": m.get("topic", ""),
                "sender": m.get("sender", ""),
                "body": m.get("body", ""),
                "created_at": m.get("created_at", ""),
            }
            for m in found
        ],
    })


@app.post("/api/read")
@login_required
def api_mark_read():
    check_csrf()
    db = get_db()
    stream = clean_topic(request.form.get("stream") or "")
    topic = clean_topic(request.form.get("topic") or DEFAULT_TOPIC)
    user = g.user
    if not stream or not is_valid_topic(topic):
        return jsonify({"error": "A stream and a topic are needed."}), 400

    messages = [
        m for m in _messages(db)
        if topic_key(m.get("stream_name", ""), m.get("topic", "")) == topic_key(stream, topic)
    ]
    last_id = messages[-1]["id"] if messages else 0
    db.execute(
        "INSERT INTO read_markers (stream, topic, user_id, message_id, updated_at) VALUES (?,?,?,?,?)",
        (stream, topic, user["id"], last_id, datetime.now(timezone.utc).isoformat(timespec="seconds")),
    )
    db.commit()
    return jsonify({"stream": stream, "topic": topic, "message_id": last_id})


@app.post("/api/topics/subscribe")
@login_required
def api_subscribe_topic():
    check_csrf()
    db = get_db()
    stream = clean_topic(request.form.get("stream") or "")
    topic = clean_topic(request.form.get("topic") or "")
    user = g.user
    if not stream or not is_valid_topic(topic):
        return jsonify({"error": "A stream and a topic are needed."}), 400
    db.execute(
        "INSERT INTO topic_subscriptions (stream, topic, user_id, created_at) VALUES (?,?,?,?)",
        (stream, topic, user["id"], datetime.now(timezone.utc).isoformat(timespec="seconds")),
    )
    db.commit()
    return jsonify({"stream": stream, "topic": topic}), 201


@app.get("/api/topics")
@login_required
def api_topics():
    db = get_db()
    rows = db.execute("SELECT DISTINCT stream, topic FROM topic_subscriptions ORDER BY stream, topic").fetchall()
    return jsonify({"topics": [dict(row) for row in rows]})


# ------------------------------------------------------------------ #
# JSON API                                                            #
# ------------------------------------------------------------------ #
@app.get("/api/meta")
def api_meta():
    return jsonify({"name": CONFIG["name"], "resources": CONFIG["resources"],
                    "special": CONFIG.get("special"), "features": CONFIG.get("features", [])})


@app.get("/api/<name>")
def api_list(name):
    resource = resource_by_name(name) or abort(404)
    db = get_db()
    items = [dict(r) for r in db.execute(f'SELECT * FROM "{name}" ORDER BY id DESC LIMIT 200')]
    return jsonify({"items": items, "resource": name})


@app.post("/api/<name>")
def api_create(name):
    resource = resource_by_name(name) or abort(404)
    if not g.user:
        return jsonify({"error": "authentication required"}), 401
    body = request.get_json(silent=True) or {}
    values, errors = validate(resource, body)
    if errors:
        return jsonify({"error": " ".join(errors)}), 400
    keys = list(values)
    db = get_db()
    cur = db.execute(
        f'INSERT INTO "{name}" ({",".join(chr(34)+k+chr(34) for k in keys)}, created_at) '
        f'VALUES ({",".join("?" for _ in keys)}, ?)',
        [values[k] for k in keys] + [datetime.now(timezone.utc).isoformat(timespec="seconds")])
    db.commit()
    row = db.execute(f'SELECT * FROM "{name}" WHERE id = ?', (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


# ------------------------------------------------------------------ #
# Domain: commerce                                                    #
# ------------------------------------------------------------------ #
def cart_contents():
    db = get_db()
    cart = session.get("cart", {})
    items, total = [], 0
    for pid, qty in list(cart.items()):
        product = db.execute("SELECT * FROM products WHERE id = ?", (int(pid),)).fetchone()
        if not product:
            cart.pop(pid, None)
            continue
        qty = max(1, min(int(qty), product["stock"]))
        cart[pid] = qty
        line = product["price_cents"] * qty
        total += line
        items.append({"product": dict(product), "quantity": qty, "line_cents": line})
    session["cart"] = cart
    return items, total


@app.get("/store")
def store():
    products = get_db().execute("SELECT * FROM products ORDER BY id").fetchall()
    return render_template("store.html", products=products)


@app.post("/cart/add/<int:product_id>")
def cart_add(product_id):
    check_csrf()
    product = get_db().execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone() or abort(404)
    if product["stock"] < 1:
        flash("That product is out of stock.", "error")
        return redirect(url_for("store"))
    cart = session.get("cart", {})
    cart[str(product_id)] = min(cart.get(str(product_id), 0) + 1, product["stock"])
    session["cart"] = cart
    flash(f'{product["name"]} added to cart.')
    return redirect(url_for("store"))


@app.get("/cart")
def cart():
    items, total = cart_contents()
    return render_template("cart.html", items=items, total=total)


@app.post("/cart/remove/<int:product_id>")
def cart_remove(product_id):
    check_csrf()
    cart = session.get("cart", {})
    cart.pop(str(product_id), None)
    session["cart"] = cart
    return redirect(url_for("cart"))


@app.post("/checkout")
def checkout():
    check_csrf()
    email = (request.form.get("email") or "").strip()
    items, total = cart_contents()
    if not items:
        flash("Your cart is empty.", "error")
        return redirect(url_for("cart"))
    if "@" not in email:
        flash("A valid email is required.", "error")
        return redirect(url_for("cart"))
    db = get_db()
    try:
        for item in items:
            product = db.execute("SELECT stock FROM products WHERE id = ?", (item["product"]["id"],)).fetchone()
            if product["stock"] < item["quantity"]:
                raise ValueError(f'{item["product"]["name"]} no longer has enough stock.')
        cur = db.execute(
            "INSERT INTO orders (customer_email, total_cents, status, created_at) VALUES (?,?,?,?)",
            (email, total, "paid", datetime.now(timezone.utc).isoformat(timespec="seconds")))
        for item in items:
            db.execute(
                "INSERT INTO order_items (order_id, product_id, name, quantity, unit_cents) VALUES (?,?,?,?,?)",
                (cur.lastrowid, item["product"]["id"], item["product"]["name"], item["quantity"],
                 item["product"]["price_cents"]))
            db.execute("UPDATE products SET stock = stock - ? WHERE id = ?",
                       (item["quantity"], item["product"]["id"]))
        db.commit()
    except ValueError as exc:
        db.rollback()
        flash(str(exc), "error")
        return redirect(url_for("cart"))
    session["cart"] = {}
    flash(f"Order #{cur.lastrowid} confirmed for ${total/100:.2f}.")
    return redirect(url_for("home"))


# ------------------------------------------------------------------ #
# Domain: chat                                                        #
# ------------------------------------------------------------------ #
@app.get("/channels")
def channels():
    db = get_db()
    streams = _streams(db)
    messages = _messages(db)
    markers = [dict(r) for r in db.execute("SELECT * FROM read_markers").fetchall()]
    return render_template(
        "channels.html",
        channels=streams,
        summary=stream_summary(streams, messages),
        unread=unread_counts(messages, markers),
    )


@app.get("/channels/<int:channel_id>")
def channel(channel_id):
    db = get_db()
    ch = db.execute("SELECT * FROM channels WHERE id = ?", (channel_id,)).fetchone() or abort(404)
    messages = _messages(db, channel_id)
    markers = [dict(r) for r in db.execute("SELECT * FROM read_markers").fetchall()]
    threads = thread_summary(messages, _streams(db))
    unread = unread_counts(messages, markers)
    return render_template(
        "channel.html",
        channel=ch,
        threads=threads,
        unread=unread,
        messages=messages,
    )


@app.post("/channels/<int:channel_id>/messages")
@login_required
def channel_post(channel_id):
    check_csrf()
    db = get_db()
    stream = db.execute("SELECT * FROM channels WHERE id = ?", (channel_id,)).fetchone() or abort(404)
    body = (request.form.get("body") or "").strip()
    topic = clean_topic(request.form.get("topic") or DEFAULT_TOPIC)
    problem = validate_message(
        {"channel_name": stream["name"], "topic": topic, "body": body}, _streams(db)
    )
    if problem:
        flash(problem, "error")
        return redirect(url_for("channel", channel_id=channel_id))
    db.execute(
        'INSERT INTO messages (channel_id, sender, body, topic, created_at) VALUES (?,?,?,?,?)',
        (channel_id, g.user["name"], body, topic, datetime.now(timezone.utc).isoformat(timespec="seconds")))
    db.commit()
    return redirect(url_for("channel", channel_id=channel_id))


@app.post("/channels/<int:channel_id>/read")
@login_required
def channel_read(channel_id):
    check_csrf()
    db = get_db()
    stream = db.execute("SELECT * FROM channels WHERE id = ?", (channel_id,)).fetchone() or abort(404)
    topic = clean_topic(request.form.get("topic") or DEFAULT_TOPIC)
    if not is_valid_topic(topic):
        flash("That topic cannot be marked as read.", "error")
        return redirect(url_for("channel", channel_id=channel_id))
    messages = [m for m in _messages(db, channel_id) if clean_topic(m.get("topic")) == topic]
    last_id = messages[-1]["id"] if messages else 0
    db.execute(
        "INSERT INTO read_markers (stream, topic, user_id, message_id, updated_at) VALUES (?,?,?,?,?)",
        (stream["name"], topic, g.user["id"], last_id, datetime.now(timezone.utc).isoformat(timespec="seconds")),
    )
    db.commit()
    return redirect(url_for("channel", channel_id=channel_id))


@app.get("/search")
def search():
    query = (request.args.get("q") or "").strip()
    messages = _messages(get_db())
    found = search_messages(messages, query)
    return render_template("search.html", query=query, messages=found)


# ------------------------------------------------------------------ #
# Domain: wiki                                                        #
# ------------------------------------------------------------------ #
@app.get("/pages/<int:page_id>")
def wiki_page(page_id):
    db = get_db()
    page = db.execute("SELECT * FROM pages WHERE id = ?", (page_id,)).fetchone() or abort(404)
    revisions = db.execute(
        "SELECT * FROM page_revisions WHERE page_id = ? ORDER BY id DESC", (page_id,)).fetchall()
    return render_template("page.html", page=page, revisions=revisions)


# ------------------------------------------------------------------ #
# Domain: minimal GraphQL                                             #
# ------------------------------------------------------------------ #
@app.post("/graphql")
def graphql():
    """A deliberately small GraphQL-compatible endpoint.

    Supports `{ products { id name priceCents stock } }`, `{ orders { id totalCents status } }`
    and `{ channels { id name } }` against the configured SQLite schema. It is enough for
    the storefront demo without pulling in a GraphQL server dependency.
    """
    payload = request.get_json(silent=True) or {}
    query = str(payload.get("query") or "")
    db = get_db()
    data = {}
    if re.search(r"\bproducts\b", query):
        data["products"] = [dict(r) for r in db.execute("SELECT * FROM products ORDER BY id")]
    if re.search(r"\borders\b", query):
        data["orders"] = [dict(r) for r in db.execute("SELECT * FROM orders ORDER BY id DESC")]
    if re.search(r"\bchannels\b", query):
        data["channels"] = [dict(r) for r in db.execute("SELECT * FROM channels ORDER BY id")]
    if not data:
        return jsonify({"errors": [{"message": "Unsupported query. Ask for products, orders or channels."}]}), 400
    return jsonify({"data": data})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=False)
