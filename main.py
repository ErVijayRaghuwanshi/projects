
"""
Single-file FastAPI app with:
 - Signup (form)
 - Login (form)
 - SQLite user storage with per-user salt + PBKDF2-HMAC-SHA256 password hashing
 - JWT access token (HS256) returned and set as cookie
 - Protected endpoint example

Dependencies:
    pip install fastapi "uvicorn[standard]" PyJWT
Run:
    uvicorn main:app --reload
"""

from fastapi import FastAPI, Request, Form, HTTPException, Depends, Response
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import sqlite3
import os
import hashlib
import binascii
import time
import jwt  # PyJWT
import hmac
from typing import Optional

# ---------- Configuration ----------
DB_PATH = "users.db"
# In production, set this via environment variable and keep secret
JWT_SECRET = os.environ.get("JWT_SECRET", "change-me-to-a-random-secret")
JWT_ALGORITHM = "HS256"
JWT_EXP_SECONDS = 60 * 30  # 30 minutes

# PBKDF2 settings
HASH_NAME = "sha256"
PBKDF2_ITERATIONS = 100_000
SALT_SIZE = 16  # bytes

app = FastAPI(title="FastAPI JWT Auth (single-file)")

# ---------- Database helpers ----------
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    # make rows accessible by name
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            salt TEXT NOT NULL,
            pwd_hash TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()

init_db()

# ---------- Password hashing ----------
def gen_salt() -> bytes:
    return os.urandom(SALT_SIZE)

def hash_password(password: str, salt: bytes) -> bytes:
    """Return raw bytes of derived key."""
    dk = hashlib.pbkdf2_hmac(HASH_NAME, password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return dk

def encode_hex(b: bytes) -> str:
    return binascii.hexlify(b).decode("ascii")

def decode_hex(s: str) -> bytes:
    return binascii.unhexlify(s.encode("ascii"))

# ---------- User DB operations ----------
def create_user(username: str, password: str) -> None:
    salt = gen_salt()
    pwd_hash = hash_password(password, salt)
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, salt, pwd_hash, created_at) VALUES (?, ?, ?, ?)",
            (username, encode_hex(salt), encode_hex(pwd_hash), int(time.time())),
        )
        conn.commit()
    except sqlite3.IntegrityError as e:
        raise ValueError("username already exists") from e
    finally:
        conn.close()

def get_user_by_username(username: str) -> Optional[sqlite3.Row]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return row

def verify_password(stored_hash_hex: str, stored_salt_hex: str, provided_password: str) -> bool:
    stored_hash = decode_hex(stored_hash_hex)
    salt = decode_hex(stored_salt_hex)
    computed = hash_password(provided_password, salt)
    # use constant-time comparison
    return hmac.compare_digest(stored_hash, computed)

# ---------- JWT helpers ----------
def create_access_token(username: str, expires_in: int = JWT_EXP_SECONDS) -> str:
    payload = {
        "sub": username,
        "exp": int(time.time()) + int(expires_in),
        "iat": int(time.time()),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    # PyJWT in v2 returns string
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token

def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ---------- Security dependency ----------
bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)):
    """
    Resolves current user from either Authorization: Bearer <token> header
    or from cookie 'access_token'.
    """
    token = None
    # 1) header
    if credentials and credentials.scheme.lower() == "bearer":
        token = credentials.credentials
    # 2) cookie fallback
    if token is None:
        token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_access_token(token)
    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    user = get_user_by_username(username)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    # return a small dict
    return {"id": user["id"], "username": user["username"], "created_at": user["created_at"]}

# ---------- HTML helpers (simple inline forms) ----------
INDEX_HTML = """
<!doctype html>
<title>FastAPI JWT Auth (single-file)</title>
<h2>Welcome</h2>
<ul>
  <li><a href="/signup">Sign up</a></li>
  <li><a href="/login">Login</a></li>
  <li><a href="/protected">Protected (requires login)</a></li>
  <li><a href="/me">/me (returns current user JSON)</a></li>
</ul>
"""

SIGNUP_FORM = """
<!doctype html>
<title>Sign up</title>
<h2>Sign up</h2>
<form method="post" action="/signup">
  <label>Username: <input type="text" name="username" required></label><br>
  <label>Password: <input type="password" name="password" required></label><br>
  <button type="submit">Sign up</button>
</form>
<p><a href="/">Home</a></p>
"""

LOGIN_FORM = """
<!doctype html>
<title>Login</title>
<h2>Login</h2>
<form method="post" action="/login">
  <label>Username: <input type="text" name="username" required></label><br>
  <label>Password: <input type="password" name="password" required></label><br>
  <button type="submit">Login</button>
</form>
<p><a href="/">Home</a></p>
"""

# ---------- Routes ----------
@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(INDEX_HTML)

@app.get("/signup", response_class=HTMLResponse)
async def signup_form():
    return HTMLResponse(SIGNUP_FORM)

@app.post("/signup", response_class=HTMLResponse)
async def signup(username: str = Form(...), password: str = Form(...)):
    username = username.strip()
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")
    try:
        create_user(username, password)
    except ValueError:
        return HTMLResponse(f"<p>Username <strong>{username}</strong> already exists. <a href='/signup'>Try another</a>.</p>", status_code=400)
    # on success redirect to login
    resp = RedirectResponse(url="/login", status_code=303)
    return resp

@app.get("/login", response_class=HTMLResponse)
async def login_form():
    return HTMLResponse(LOGIN_FORM)

@app.post("/login")
async def login(response: Response, username: str = Form(...), password: str = Form(...)):
    username = username.strip()
    user = get_user_by_username(username)
    if not user:
        return HTMLResponse("<p>Invalid credentials. <a href='/login'>Try again</a></p>", status_code=401)
    if not verify_password(user["pwd_hash"], user["salt"], password):
        return HTMLResponse("<p>Invalid credentials. <a href='/login'>Try again</a></p>", status_code=401)
    token = create_access_token(username)
    # Set token as httpOnly cookie so browser forms can use it later
    # In production: secure=True, samesite, domain, etc.
    response = RedirectResponse(url="/protected", status_code=303)
    response.set_cookie("access_token", token, httponly=True, max_age=JWT_EXP_SECONDS)
    return response

@app.post("/login/json")
async def login_json(payload: dict):
    """Alternative JSON login endpoint (username/password) -> returns token"""
    username = payload.get("username", "").strip()
    password = payload.get("password", "")
    user = get_user_by_username(username)
    if not user or not verify_password(user["pwd_hash"], user["salt"], password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(username)
    return {"access_token": token, "token_type": "bearer", "expires_in": JWT_EXP_SECONDS}

@app.get("/protected", response_class=HTMLResponse)
async def protected_page(user=Depends(get_current_user)):
    return HTMLResponse(f"""
    <h2>Protected page</h2>
    <p>Hi <strong>{user['username']}</strong> — you're authenticated.</p>
    <p><a href="/me">View JSON /me</a></p>
    <p><a href="/logout">Logout</a></p>
    <p><a href="/">Home</a></p>
    """)

@app.get("/me")
async def me(user=Depends(get_current_user)):
    return JSONResponse(user)

@app.get("/logout")
async def logout():
    # clear cookie
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response

# A small open endpoint for checking username availability
@app.get("/available/{username}")
async def available(username: str):
    user = get_user_by_username(username)
    return {"available": user is None}

# ---------- Startup info ----------
@app.on_event("startup")
async def startup_event():
    # print a friendly message to server logs
    print("FastAPI JWT single-file app started. Signup at /signup, login at /login")

# ---------- Minimal API example to create a user programmatically ----------
@app.post("/users/create")
async def api_create_user(payload: dict):
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""
    if not username or not password:
        raise HTTPException(status_code=400, detail="username and password required")
    try:
        create_user(username, password)
    except ValueError:
        raise HTTPException(status_code=400, detail="username already exists")
    return {"status": "created", "username": username}

# ---------- Error handlers ----------
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    # default behavior but keep JSON for API calls, simple HTML for form flows
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return HTMLResponse(f"<h3>Error {exc.status_code}</h3><p>{exc.detail}</p><p><a href='/'>Home</a></p>", status_code=exc.status_code)
    return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)