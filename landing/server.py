"""Minimal landing page server with email signup persistence."""
from __future__ import annotations

import os
import re
import sqlite3
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

DB_PATH = os.environ.get("DB_PATH", "/data/signups.db")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "script-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "connect-src 'self'"
        )
        return response


app.add_middleware(SecurityHeadersMiddleware)


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
    conn.commit()
    return conn


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
        return {"status": "ok", "message": "You're on the list."}
    except sqlite3.IntegrityError:
        return {"status": "ok", "message": "You're already on the list."}
    finally:
        conn.close()


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


@app.get("/health")
async def health():
    return PlainTextResponse("ok")


@app.get("/")
async def index():
    return FileResponse("/app/index.html", media_type="text/html")
