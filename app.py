#!/usr/bin/env python3
"""
StormCore Unified - Cloud Optimized
Quantum-linked AI development platform
Optimized for Render.com deployment
"""

import os
import asyncio
import time
import json
import sqlite3
import httpx
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, EmailStr, field_validator

import jwt
import bcrypt
import uuid

# ============================================================================
# CONFIGURATION - Using Environment Variables for Cloud
# ============================================================================

SECRET_KEY = os.getenv("SECRET_KEY", os.urandom(32).hex())
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

# API Keys from environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Database path - use /tmp on ephemeral systems like Render
# This ensures we have write permissions
DATABASE_PATH = os.getenv("DATABASE_PATH", "/tmp/stormcore.db")

# Ensure the database directory exists
Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)

# ============================================================================
# QUANTUM RESONANCE LATTICE
# ============================================================================

class QuantumLattice:
    def __init__(self, nodes=16, dimensions=4):
        self.nodes = nodes
        self.dimensions = dimensions
        self.state = [[0.0] * dimensions for _ in range(nodes)]
        self.history = []
    
    def excite(self, index: int, amplitude: float, dimension: int = 0):
        if 0 <= index < self.nodes and 0 <= dimension < self.dimensions:
            self.state[index][dimension] += amplitude
            self.state[index][dimension] = max(-10.0, min(10.0, self.state[index][dimension]))
    
    def propagate(self, damping: float = 0.95):
        new_state = [row[:] for row in self.state]
        for i in range(self.nodes):
            for d in range(self.dimensions):
                left = self.state[(i - 1) % self.nodes][d]
                right = self.state[(i + 1) % self.nodes][d]
                current = self.state[i][d]
                new_state[i][d] = (current * 0.4 + left * 0.3 + right * 0.3) * damping
        self.state = new_state
        self.history.append([row[:] for row in self.state])
        if len(self.history) > 100:
            self.history.pop(0)
    
    def get_energy(self) -> float:
        total = sum(sum(abs(v) for v in node) for node in self.state)
        return max(0.0, min(1.0, total / (self.nodes * self.dimensions * 10.0)))
    
    def snapshot(self) -> dict:
        return {
            "state": self.state,
            "energy": self.get_energy(),
            "nodes": self.nodes
        }

quantum_lattice = QuantumLattice()

# ============================================================================
# HYBRID AI SWARM
# ============================================================================

class HybridSwarm:
    def __init__(self, lattice):
        self.lattice = lattice
        self.groq_key = GROQ_API_KEY
        self.openrouter_key = OPENROUTER_API_KEY
        self.google_key = GOOGLE_API_KEY
    
    def _route(self, user_tier: str, swarm_mode: str) -> str:
        if user_tier == "free":
            return "gemini"
        if swarm_mode == "quality":
            return "swarm"
        
        energy = self.lattice.get_energy()
        if energy > 0.7:
            return "groq"
        elif energy < 0.3:
            return "openrouter"
        return "gemini"
    
    async def vibe(self, prompt: str, code: str, user_tier: str = "free", swarm_mode: str = "auto") -> dict:
        provider = self._route(user_tier, swarm_mode)
        
        if provider == "swarm":
            return await self._swarm(prompt, code)
        return await self._single(provider, prompt, code)
    
    async def _single(self, provider: str, prompt: str, code: str) -> dict:
        if provider == "gemini" and self.google_key:
            return await self._call_gemini(prompt, code)
        elif provider == "groq" and self.groq_key:
            return await self._call_groq(prompt, code)
        elif provider == "openrouter" and self.openrouter_key:
            return await self._call_openrouter(prompt, code)
        
        # Fallback
        if self.google_key:
            return await self._call_gemini(prompt, code)
        return {"error": "No API keys configured"}
    
    async def _swarm(self, prompt: str, code: str) -> dict:
        tasks = []
        if self.groq_key:
            tasks.append(self._call_groq(prompt, code))
        if self.openrouter_key:
            tasks.append(self._call_openrouter(prompt, code))
        if self.google_key:
            tasks.append(self._call_gemini(prompt, code))
        
        if not tasks:
            return {"error": "No providers available"}
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        valid = [r for r in results if not isinstance(r, Exception) and "error" not in r]
        
        if not valid:
            return {"error": "All providers failed"}
        
        winner = valid[0]
        winner["swarm_mode"] = True
        winner["candidates"] = len(valid)
        return winner
    
    async def _call_gemini(self, prompt: str, code: str) -> dict:
        if not self.google_key:
            return {"error": "Gemini key missing"}
        
        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                response = await client.post(
                    "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent",
                    headers={"x-goog-api-key": self.google_key},
                    json={
                        "contents": [{
                            "parts": [{"text": f"Code editing mode.\n\nRequest: {prompt}\n\nCode:\n{code}\n\nReturn format:\n```python\n[modified code]\n```\n---\n[explanation]"}]
                        }]
                    }
                )
                
                if response.status_code != 200:
                    return {"error": f"Gemini error {response.status_code}"}
                
                result = response.json()
                content = result["candidates"][0]["content"]["parts"][0]["text"]
                new_code, explanation = self._parse(content)
                
                return {
                    "new_code": new_code,
                    "explanation": explanation,
                    "provider": "gemini",
                    "cost": 0.0001,
                    "quantum_energy": self.lattice.get_energy()
                }
        except Exception as e:
            return {"error": str(e)}
    
    async def _call_groq(self, prompt: str, code: str) -> dict:
        if not self.groq_key:
            return {"error": "Groq key missing"}
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.groq_key}"},
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "system", "content": "You edit code. Return format: ```python\n[code]\n```\n---\n[explanation]"},
                            {"role": "user", "content": f"{prompt}\n\n{code}"}
                        ],
                        "temperature": 0.3
                    }
                )
                
                if response.status_code != 200:
                    return {"error": f"Groq error {response.status_code}"}
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                new_code, explanation = self._parse(content)
                
                return {
                    "new_code": new_code,
                    "explanation": explanation,
                    "provider": "groq",
                    "cost": 0.0003,
                    "quantum_energy": self.lattice.get_energy()
                }
        except Exception as e:
            return {"error": str(e)}
    
    async def _call_openrouter(self, prompt: str, code: str) -> dict:
        if not self.openrouter_key:
            return {"error": "OpenRouter key missing"}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.openrouter_key}",
                        "HTTP-Referer": "https://stormcore.app"
                    },
                    json={
                        "model": "anthropic/claude-3.5-sonnet",
                        "messages": [
                            {"role": "user", "content": f"{prompt}\n\n{code}"}
                        ]
                    }
                )
                
                if response.status_code != 200:
                    return {"error": f"OpenRouter error {response.status_code}"}
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                new_code, explanation = self._parse(content)
                
                return {
                    "new_code": new_code,
                    "explanation": explanation,
                    "provider": "openrouter",
                    "cost": 0.0002,
                    "quantum_energy": self.lattice.get_energy()
                }
        except Exception as e:
            return {"error": str(e)}
    
    def _parse(self, content: str) -> tuple:
        if "---" in content:
            code_part, explanation = content.split("---", 1)
        else:
            code_part, explanation = content, "Code modified"
        
        code_match = re.search(r'```(?:python)?\n(.*?)\n```', code_part, re.DOTALL)
        if code_match:
            new_code = code_match.group(1).strip()
        else:
            new_code = code_part.strip()
        
        return new_code, explanation.strip()

hybrid_swarm = HybridSwarm(quantum_lattice)

# ============================================================================
# DATABASE
# ============================================================================

def init_db():
    """Initialize SQLite database with proper error handling"""
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                subscription_tier TEXT DEFAULT 'free',
                is_active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                ai_requests_used INTEGER DEFAULT 0
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vibe_history (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                prompt TEXT NOT NULL,
                old_code TEXT,
                new_code TEXT,
                provider TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
        print(f"✅ Database initialized at {DATABASE_PATH}")
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")
        print("   App will continue but persistence may be limited")

def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="StormCore Unified",
    description="Quantum-linked AI development platform",
    version="4.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# ============================================================================
# MODELS
# ============================================================================

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be 8+ characters')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class VibeRequest(BaseModel):
    prompt: str
    current_code: str
    mode: str = "edit"
    swarm_mode: Optional[str] = "auto"

# ============================================================================
# AUTH
# ============================================================================

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = decode_token(token)
    user_id = payload.get("sub")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=401, detail="User not found")
    
    return dict(row)

# ============================================================================
# BACKGROUND QUANTUM LOOP
# ============================================================================

async def quantum_loop():
    """Background task that keeps the quantum lattice alive"""
    while True:
        try:
            quantum_lattice.propagate()
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"⚠️  Quantum loop error: {e}")
            await asyncio.sleep(1)

@app.on_event("startup")
async def startup():
    print("⚡ StormCore Unified Starting...")
    print(f"🌐 Port: {os.getenv('PORT', '8001')}")
    print(f"🔑 API Keys: Groq={bool(GROQ_API_KEY)}, OpenRouter={bool(OPENROUTER_API_KEY)}, Gemini={bool(GOOGLE_API_KEY)}")
    print(f"💾 Database: {DATABASE_PATH}")
    init_db()
    asyncio.create_task(quantum_loop())
    print("✅ StormCore Ready!")

# ============================================================================
# ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {
        "service": "StormCore Unified",
        "version": "4.0.0",
        "status": "operational",
        "quantum_energy": quantum_lattice.get_energy(),
        "providers_active": {
            "groq": bool(GROQ_API_KEY),
            "openrouter": bool(OPENROUTER_API_KEY),
            "gemini": bool(GOOGLE_API_KEY)
        },
        "endpoints": {
            "health": "/health",
            "quantum": "/quantum/status",
            "demo": "/demo",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "quantum": "resonating",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected"
    }

@app.get("/quantum/status")
async def quantum_status():
    return quantum_lattice.snapshot()

@app.post("/quantum/excite")
async def excite(node: int, amplitude: float):
    quantum_lattice.excite(node, amplitude)
    return {"status": "excited", "node": node, "energy": quantum_lattice.get_energy()}

@app.post("/auth/register")
async def register(user: UserRegister):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE email = ?", (user.email,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Email exists")
    
    user_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, user.email, user.name, hash_password(user.password),
        "user", "free", 1, datetime.utcnow().isoformat(), 0
    ))
    
    conn.commit()
    conn.close()
    
    token = create_token({"sub": user_id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user_id, "email": user.email, "name": user.name, "tier": "free"}
    }

@app.post("/auth/login")
async def login(credentials: UserLogin):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = ?", (credentials.email,))
    row = cursor.fetchone()
    conn.close()
    
    if not row or not verify_password(credentials.password, dict(row)["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = dict(row)
    token = create_token({"sub": user["id"]})
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {k: v for k, v in user.items() if k != "password_hash"}
    }

@app.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {k: v for k, v in current_user.items() if k != "password_hash"}

@app.post("/ai/vibe")
async def vibe_endpoint(
    request: VibeRequest,
    current_user: dict = Depends(get_current_user)
):
    tier = current_user["subscription_tier"]
    
    if request.swarm_mode == "quality" and tier not in ["pro", "team"]:
        raise HTTPException(status_code=403, detail="Swarm mode requires PRO tier")
    
    result = await hybrid_swarm.vibe(
        request.prompt,
        request.current_code,
        tier,
        request.swarm_mode
    )
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    # Log vibe
    conn = get_db()
    cursor = conn.cursor()
    
    vibe_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO vibe_history VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        vibe_id, current_user["id"], request.prompt,
        request.current_code, result.get("new_code"),
        result.get("provider"), datetime.utcnow().isoformat()
    ))
    
    cursor.execute(
        "UPDATE users SET ai_requests_used = ai_requests_used + 1 WHERE id = ?",
        (current_user["id"],)
    )
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "changes": {
            "new_code": result.get("new_code"),
            "explanation": result.get("explanation")
        },
        "provider": result.get("provider"),
        "quantum_energy": result.get("quantum_energy"),
        "swarm_mode": result.get("swarm_mode", False),
        "cost": result.get("cost", 0)
    }

@app.websocket("/quantum/stream")
async def quantum_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(quantum_lattice.snapshot())
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        pass

# ============================================================================
# SIMPLE WEB UI
# ============================================================================

@app.get("/demo", response_class=HTMLResponse)
async def demo():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>StormCore Demo</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Courier New', monospace;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                min-height: 100vh;
            }
            .container { max-width: 900px; margin: 0 auto; }
            h1 { 
                text-align: center; 
                font-size: 2.5em;
                margin: 20px 0;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            .panel {
                background: rgba(0,0,0,0.3);
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            }
            h3 { margin-bottom: 15px; color: #fff; }
            button {
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 16px;
                font-weight: bold;
                transition: all 0.3s;
                margin: 5px;
            }
            button:hover { 
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            }
            #status { color: #0f0; font-weight: bold; }
            #energy { 
                color: #ffd700; 
                font-weight: bold;
                font-size: 1.2em;
            }
            pre { 
                background: rgba(0,0,0,0.5);
                padding: 15px;
                border-radius: 5px;
                overflow-x: auto;
                margin-top: 10px;
                font-size: 12px;
            }
            .grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 10px;
                margin: 20px 0;
            }
            .stat {
                background: rgba(255,255,255,0.1);
                padding: 15px;
                border-radius: 8px;
                text-align: center;
            }
            .stat-label {
                font-size: 0.9em;
                opacity: 0.8;
                margin-bottom: 5px;
            }
            .stat-value {
                font-size: 1.5em;
                font-weight: bold;
                color: #ffd700;
            }
            @media (max-width: 600px) {
                h1 { font-size: 1.8em; }
                .panel { padding: 15px; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>⚡ StormCore Unified ⚡</h1>
            
            <div class="panel">
                <h3>System Status</h3>
                <div class="grid">
                    <div class="stat">
                        <div class="stat-label">Status</div>
                        <div class="stat-value" id="status">Checking...</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Quantum Energy</div>
                        <div class="stat-value" id="energy">0.000</div>
                    </div>
                    <div class="stat">
                        <div class="stat-label">Uptime</div>
                        <div class="stat-value" id="uptime">--</div>
                    </div>
                </div>
            </div>
            
            <div class="panel">
                <h3>Quick Actions</h3>
                <button onclick="testAPI()">🔍 Test API</button>
                <button onclick="exciteQuantum()">⚡ Excite Quantum Field</button>
                <button onclick="window.location.href='/docs'">📚 API Documentation</button>
                <pre id="result"></pre>
            </div>
            
            <div class="panel">
                <h3>API Endpoints</h3>
                <pre>GET  /health         - Health check
GET  /quantum/status - Quantum lattice state
POST /auth/register  - Create account
POST /auth/login     - Authenticate
POST /ai/vibe        - AI code generation
GET  /docs           - Full API documentation</pre>
            </div>
        </div>
        
        <script>
            let startTime = Date.now();
            
            async function testAPI() {
                try {
                    document.getElementById('result').textContent = 'Testing...';
                    const res = await fetch('/quantum/status');
                    const data = await res.json();
                    document.getElementById('result').textContent = JSON.stringify(data, null, 2);
                    document.getElementById('energy').textContent = data.energy.toFixed(3);
                } catch (e) {
                    document.getElementById('result').textContent = 'Error: ' + e.message;
                }
            }
            
            async function exciteQuantum() {
                try {
                    const node = Math.floor(Math.random() * 16);
                    const amplitude = (Math.random() * 4) - 2;
                    const res = await fetch('/quantum/excite', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({node, amplitude})
                    });
                    const data = await res.json();
                    document.getElementById('result').textContent = `Excited node ${node} with amplitude ${amplitude.toFixed(2)}\\n\\n${JSON.stringify(data, null, 2)}`;
                } catch (e) {
                    document.getElementById('result').textContent = 'Error: ' + e.message;
                }
            }
            
            async function checkStatus() {
                try {
                    const res = await fetch('/health');
                    if (res.ok) {
                        document.getElementById('status').textContent = 'Online';
                        document.getElementById('status').style.color = '#0f0';
                    }
                } catch (e) {
                    document.getElementById('status').textContent = 'Offline';
                    document.getElementById('status').style.color = '#f00';
                }
            }
            
            function updateUptime() {
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                const minutes = Math.floor(elapsed / 60);
                const seconds = elapsed % 60;
                document.getElementById('uptime').textContent = `${minutes}m ${seconds}s`;
            }
            
            // Initialize
            checkStatus();
            testAPI();
            
            // Update loops
            setInterval(() => {
                fetch('/quantum/status')
                    .then(r => r.json())
                    .then(d => document.getElementById('energy').textContent = d.energy.toFixed(3))
                    .catch(e => console.error('Energy update failed:', e));
            }, 1000);
            
            setInterval(updateUptime, 1000);
            setInterval(checkStatus, 5000);
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8001"))
    print(f"🚀 Starting StormCore on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
