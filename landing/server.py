"""Landing page server with email signup and Auth0 social login."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import sqlite3
import time
from base64 import urlsafe_b64decode, urlsafe_b64encode
from datetime import UTC, datetime
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    PlainTextResponse,
    RedirectResponse,
)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

# --- Structured Logging ---
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
LOG_FORMAT = os.environ.get("LOG_FORMAT", "json")

logger = logging.getLogger("redeemflow.landing")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

if not logger.handlers:
    handler = logging.StreamHandler()
    if LOG_FORMAT == "json":

        class JSONFormatter(logging.Formatter):
            def format(self, record: logging.LogRecord) -> str:
                log_entry = {
                    "timestamp": datetime.now(UTC).isoformat(),
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                }
                if hasattr(record, "extra_data"):
                    log_entry.update(record.extra_data)
                if record.exc_info and record.exc_info[1]:
                    log_entry["exception"] = str(record.exc_info[1])
                return json.dumps(log_entry)

        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logger.addHandler(handler)


def log_event(level: str, message: str, **kwargs: object) -> None:
    """Emit a structured log event with arbitrary key-value context."""
    record = logger.makeRecord(logger.name, getattr(logging, level.upper(), logging.INFO), "", 0, message, (), None)
    record.extra_data = kwargs  # type: ignore[attr-defined]
    logger.handle(record)


# --- OTEL (optional, graceful degradation) ---
_otel_enabled = False
try:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    otel_endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
    if otel_endpoint:
        resource = Resource.create({"service.name": "redeemflow-landing", "service.version": "0.2.0"})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=otel_endpoint)))
        trace.set_tracer_provider(provider)
        _otel_enabled = True
        log_event("info", "OpenTelemetry tracing enabled", endpoint=otel_endpoint)
except ImportError:
    log_event("info", "OpenTelemetry not installed, tracing disabled")

VERSION_FILE = Path(__file__).resolve().parent / "VERSION"
APP_VERSION = VERSION_FILE.read_text().strip() if VERSION_FILE.exists() else "0.0.0"

# --- Config ---
DB_PATH = os.environ.get("DB_PATH", "/data/signups.db")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

AUTH0_DOMAIN = os.environ.get("AUTH0_DOMAIN", "")
AUTH0_CLIENT_ID = os.environ.get("AUTH0_CLIENT_ID", "")
AUTH0_CLIENT_SECRET = os.environ.get("AUTH0_CLIENT_SECRET", "")
AUTH0_CALLBACK_URL = os.environ.get("AUTH0_CALLBACK_URL", "")
SESSION_SECRET = os.environ.get("SESSION_SECRET", "")

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

if _otel_enabled:
    FastAPIInstrumentor.instrument_app(app)

IMG_DIR = Path(__file__).resolve().parent / "img"
if IMG_DIR.is_dir():
    app.mount("/img", StaticFiles(directory=str(IMG_DIR)), name="images")

log_event("info", "Landing server starting", version=APP_VERSION)


# --- Session helpers (signed cookie, no external deps) ---
def _sign(payload: bytes) -> str:
    sig = hmac.new(SESSION_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    return urlsafe_b64encode(payload).decode() + "." + sig


def _verify(token: str) -> dict | None:
    try:
        parts = token.split(".", 1)
        if len(parts) != 2:
            return None
        payload_b64, sig = parts
        payload = urlsafe_b64decode(payload_b64 + "==")
        expected = hmac.new(SESSION_SECRET.encode(), payload, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        data = json.loads(payload)
        if data.get("exp", 0) < time.time():
            return None
        return data
    except Exception:
        return None


def _get_session(request: Request) -> dict | None:
    token = request.cookies.get("session")
    if not token:
        return None
    return _verify(token)


def _make_session_cookie(user: dict, max_age: int = 86400 * 7) -> str:
    payload = {
        "sub": user.get("sub", ""),
        "email": user.get("email", ""),
        "name": user.get("name", ""),
        "picture": user.get("picture", ""),
        "provider": user.get("provider", ""),
        "exp": int(time.time()) + max_age,
    }
    return _sign(json.dumps(payload, separators=(",", ":")).encode())


# PKCE state storage (in-memory, single-machine is fine for landing page)
_pending_states: dict[str, dict] = {}


# --- Security headers middleware ---
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        csp = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "script-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https://lh3.googleusercontent.com "
            "https://media.licdn.com https://*.amazonaws.com https://*.auth0.com; "
            "connect-src 'self'"
        )
        response.headers["Content-Security-Policy"] = csp
        return response


app.add_middleware(SecurityHeadersMiddleware)


# --- Database ---
def _get_db() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS signups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            ip TEXT,
            user_agent TEXT
        )"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sub TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            name TEXT,
            picture TEXT,
            provider TEXT,
            created_at TEXT NOT NULL,
            last_login TEXT NOT NULL
        )"""
    )
    conn.commit()
    return conn


def _upsert_user(user: dict) -> None:
    conn = _get_db()
    now = datetime.now(UTC).isoformat()
    try:
        conn.execute(
            """INSERT INTO users (sub, email, name, picture, provider, created_at, last_login)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(sub) DO UPDATE SET
                 email=excluded.email, name=excluded.name, picture=excluded.picture,
                 last_login=excluded.last_login""",
            (
                user.get("sub", ""),
                user.get("email", ""),
                user.get("name", ""),
                user.get("picture", ""),
                user.get("provider", ""),
                now,
                now,
            ),
        )
        conn.commit()
    finally:
        conn.close()


# --- Email signup ---
class SignupRequest(BaseModel):
    email: str


@app.post("/api/signup")
async def signup(req: SignupRequest, request: Request):
    email = req.email.strip().lower()
    if not email or not EMAIL_RE.match(email):
        return JSONResponse(status_code=400, content={"error": "Invalid email"})

    ip = request.headers.get("fly-client-ip", request.client.host if request.client else "unknown")
    ua = request.headers.get("user-agent", "")

    conn = _get_db()
    try:
        conn.execute(
            "INSERT INTO signups (email, created_at, ip, user_agent) VALUES (?, ?, ?, ?)",
            (email, datetime.now(UTC).isoformat(), ip, ua),
        )
        conn.commit()
        log_event("info", "New signup", ip=ip, source="email")
        return {"status": "ok", "message": "You're on the list."}
    except sqlite3.IntegrityError:
        log_event("info", "Duplicate signup attempt", ip=ip)
        return {"status": "ok", "message": "You're already on the list."}
    finally:
        conn.close()


# --- Admin ---
@app.get("/api/signups")
async def list_signups(request: Request):
    if not ADMIN_TOKEN:
        return JSONResponse(status_code=403, content={"error": "Admin access not configured"})

    auth = request.headers.get("authorization", "")
    if auth != f"Bearer {ADMIN_TOKEN}":
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})

    conn = _get_db()
    rows = conn.execute("SELECT email, created_at, ip FROM signups ORDER BY created_at DESC").fetchall()
    conn.close()
    return {
        "count": len(rows),
        "signups": [{"email": r[0], "created_at": r[1], "ip": r[2]} for r in rows],
    }


@app.get("/api/users")
async def list_users(request: Request):
    if not ADMIN_TOKEN:
        return JSONResponse(status_code=403, content={"error": "Admin access not configured"})

    auth = request.headers.get("authorization", "")
    if auth != f"Bearer {ADMIN_TOKEN}":
        return JSONResponse(status_code=401, content={"error": "Unauthorized"})

    conn = _get_db()
    rows = conn.execute(
        "SELECT sub, email, name, provider, created_at, last_login FROM users ORDER BY last_login DESC"
    ).fetchall()
    conn.close()
    return {
        "count": len(rows),
        "users": [
            {"sub": r[0], "email": r[1], "name": r[2], "provider": r[3], "created_at": r[4], "last_login": r[5]}
            for r in rows
        ],
    }


# --- Auth0 OAuth2 OIDC flow ---
@app.get("/login")
async def login(request: Request):
    if not AUTH0_DOMAIN or not AUTH0_CLIENT_ID:
        return JSONResponse(status_code=503, content={"error": "Auth not configured"})

    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    _pending_states[state] = {"nonce": nonce, "ts": time.time()}

    # Clean old states (>10 min)
    cutoff = time.time() - 600
    for k in [k for k, v in _pending_states.items() if v["ts"] < cutoff]:
        _pending_states.pop(k, None)

    params = {
        "response_type": "code",
        "client_id": AUTH0_CLIENT_ID,
        "redirect_uri": AUTH0_CALLBACK_URL,
        "scope": "openid profile email",
        "state": state,
        "nonce": nonce,
    }
    qs = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(f"https://{AUTH0_DOMAIN}/authorize?{qs}")


@app.get("/callback")
async def callback(request: Request):
    error = request.query_params.get("error")
    if error:
        desc = request.query_params.get("error_description", error)
        return HTMLResponse(
            f"<h3>Login failed</h3><p>{desc}</p><p><a href='/'>Back to home</a></p>",
            status_code=400,
        )

    code = request.query_params.get("code", "")
    state = request.query_params.get("state", "")

    if not code or not state or state not in _pending_states:
        return HTMLResponse(
            "<h3>Invalid login attempt</h3><p><a href='/'>Back to home</a></p>",
            status_code=400,
        )

    _pending_states.pop(state, None)

    # Exchange code for tokens
    async with httpx.AsyncClient(timeout=10) as client:
        token_resp = await client.post(
            f"https://{AUTH0_DOMAIN}/oauth/token",
            json={
                "grant_type": "authorization_code",
                "client_id": AUTH0_CLIENT_ID,
                "client_secret": AUTH0_CLIENT_SECRET,
                "code": code,
                "redirect_uri": AUTH0_CALLBACK_URL,
            },
        )

    if token_resp.status_code != 200:
        return HTMLResponse(
            "<h3>Login failed</h3><p>Could not exchange token.</p><p><a href='/'>Back to home</a></p>",
            status_code=400,
        )

    tokens = token_resp.json()
    access_token = tokens.get("access_token", "")

    # Get user profile from Auth0
    async with httpx.AsyncClient(timeout=10) as client:
        profile_resp = await client.get(
            f"https://{AUTH0_DOMAIN}/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if profile_resp.status_code != 200:
        return HTMLResponse(
            "<h3>Login failed</h3><p>Could not fetch profile.</p><p><a href='/'>Back to home</a></p>",
            status_code=400,
        )

    profile = profile_resp.json()
    sub = profile.get("sub", "")
    provider = sub.split("|")[0] if "|" in sub else "unknown"

    user = {
        "sub": sub,
        "email": profile.get("email", ""),
        "name": profile.get("name", ""),
        "picture": profile.get("picture", ""),
        "provider": provider,
    }

    _upsert_user(user)

    # Auto-register as beta signup if they have an email
    if user["email"]:
        conn = _get_db()
        try:
            ip = request.headers.get("fly-client-ip", request.client.host if request.client else "unknown")
            conn.execute(
                "INSERT OR IGNORE INTO signups (email, created_at, ip, user_agent) VALUES (?, ?, ?, ?)",
                (user["email"].lower(), datetime.now(UTC).isoformat(), ip, f"social:{provider}"),
            )
            conn.commit()
        finally:
            conn.close()

    cookie_val = _make_session_cookie(user)
    response = RedirectResponse("/", status_code=302)
    response.set_cookie(
        "session",
        cookie_val,
        max_age=86400 * 7,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )
    return response


@app.get("/logout")
async def logout():
    response = RedirectResponse(
        f"https://{AUTH0_DOMAIN}/v2/logout?client_id={AUTH0_CLIENT_ID}&returnTo=https://redeemflow.io",
        status_code=302,
    )
    response.delete_cookie("session", path="/")
    return response


@app.get("/api/me")
async def me(request: Request):
    session = _get_session(request)
    if not session:
        return {"user": None}
    return {
        "user": {
            "email": session.get("email", ""),
            "name": session.get("name", ""),
            "picture": session.get("picture", ""),
            "provider": session.get("provider", ""),
        }
    }


# --- Static ---
@app.get("/health")
async def health():
    return PlainTextResponse("ok")


@app.get("/api/version")
async def version():
    return {"version": APP_VERSION, "otel": _otel_enabled}


@app.get("/")
async def index():
    html_path = Path(__file__).resolve().parent / "index.html"
    if not html_path.exists():
        html_path = Path("/app/index.html")
    return FileResponse(str(html_path), media_type="text/html")
