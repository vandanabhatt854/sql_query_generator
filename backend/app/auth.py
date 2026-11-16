"""Local demo accounts, stored separately from the queryable demo database."""
import hashlib
import hmac
import os
from pathlib import Path
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, Field

router = APIRouter(prefix='/auth')
AUTH_DB = Path(os.getenv('DATA_DIR', str(Path(__file__).resolve().parent.parent))) / 'accounts.db'
COOKIE = 'querygenie_session'
TTL = 8 * 60 * 60


@contextmanager
def connect():
    db = sqlite3.connect(AUTH_DB)
    db.row_factory = sqlite3.Row
    db.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, salt TEXT NOT NULL, password_hash TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, user_id INTEGER NOT NULL, expires INTEGER NOT NULL)')
    try:
        with db:
            yield db
    finally:
        db.close()


def allowed_origins():
    origins = [s.strip() for s in os.getenv('ALLOWED_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',') if s.strip()]
    hostname = os.getenv('RENDER_EXTERNAL_HOSTNAME')
    if hostname:
        origins.append('https://' + hostname)
    return origins


def check_origin(request):
    origin = request.headers.get('origin')
    if origin and origin not in allowed_origins():
        raise HTTPException(403, 'Untrusted request origin.')


class Credentials(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)


class Registration(Credentials):
    name: str = Field(min_length=1, max_length=100)


def password_hash(password, salt):
    return hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1).hex()


def create_session(db, user_id, response):
    token = secrets.token_urlsafe(32)
    db.execute('DELETE FROM sessions WHERE expires <= ?', (int(time.time()),))
    db.execute('INSERT INTO sessions VALUES (?, ?, ?)', (hashlib.sha256(token.encode()).hexdigest(), user_id, int(time.time()) + TTL))
    db.commit()
    response.set_cookie(COOKIE, token, max_age=TTL, httponly=True, samesite='strict', secure=os.getenv('COOKIE_SECURE', 'False').lower() == 'true', path='/')


@router.post('/register')
def register(payload: Registration, request: Request, response: Response):
    check_origin(request)
    email = payload.email.strip().lower()
    name = payload.name.strip()
    if not name or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
        raise HTTPException(422, 'Enter a name and valid email address.')
    salt = secrets.token_hex(16)
    with connect() as db:
        try:
            cursor = db.execute('INSERT INTO users(name,email,salt,password_hash) VALUES(?,?,?,?)', (name, email, salt, password_hash(payload.password, salt)))
        except sqlite3.IntegrityError:
            raise HTTPException(409, 'An account with this email already exists.') from None
        create_session(db, cursor.lastrowid, response)
        return {'user': {'id': cursor.lastrowid, 'name': name, 'email': email}}


@router.post('/login')
def login(payload: Credentials, request: Request, response: Response):
    check_origin(request)
    with connect() as db:
        user = db.execute('SELECT * FROM users WHERE email=?', (payload.email.strip().lower(),)).fetchone()
        salt = user['salt'] if user else '00' * 16
        hashed = password_hash(payload.password, salt)
        if not user or not hmac.compare_digest(hashed, user['password_hash']):
            raise HTTPException(401, 'Incorrect email or password.')
        create_session(db, user['id'], response)
        return {'user': {k: user[k] for k in ['id', 'name', 'email']}}


@router.get('/me')
def me(request: Request):
    token = request.cookies.get(COOKIE, '')
    with connect() as db:
        user = db.execute('SELECT u.id,u.name,u.email FROM users u JOIN sessions s ON u.id=s.user_id WHERE s.token_hash=? AND s.expires>?', (hashlib.sha256(token.encode()).hexdigest(), int(time.time()))).fetchone()
        if not user:
            raise HTTPException(401, 'Please sign in.')
        return {'user': dict(user)}


@router.post('/logout')
def logout(request: Request, response: Response):
    check_origin(request)
    token = request.cookies.get(COOKIE, '')
    with connect() as db:
        db.execute('DELETE FROM sessions WHERE token_hash=?', (hashlib.sha256(token.encode()).hexdigest(),))
        db.commit()
    response.delete_cookie(COOKIE, path='/')
    return {'success': True}
