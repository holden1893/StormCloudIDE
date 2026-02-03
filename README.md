# NEXUS NEBULA UNIVERSE

**The AI development swarm that turns ideas into reality through parallel agent orchestration.**

---

## 🧠 What the fuck is this?

Nexus Nebula is a full-stack AI code generation platform where you describe what you want to build, and a swarm of specialist AI agents (Architect, Coder, Auditor) collaborates in real-time to:

1. **Analyze** your intent
2. **Architect** the system design
3. **Code** the implementation
4. **Review** for security & quality
5. **Package** the artifacts

All streamed live over WebSockets to a slick React UI with progress bars, terminal logs, and artifact downloads.

---

## 🚀 Stack

### Backend
- **FastAPI** — HTTP + WebSocket server
- **Python 3.10+** — Async/await everywhere
- **SQLAlchemy** — Async ORM (SQLite local, Postgres prod)
- **Nebula Swarm** — Parallel multi-agent LLM orchestration
- **Mooncake Cache** — KV-cache simulation for context prefill

### Frontend
- **React 18** — Component-driven UI
- **Vite** — Lightning-fast dev server + build
- **TailwindCSS** — Utility-first styling
- **React Router** — Client-side routing
- **Axios** — HTTP client
- **Lucide React** — Icon library

---

## ⚡ Quick Start

### 1. Clone & Enter

```bash
cd nexus
```

### 2. Run Everything

```bash
bash start.sh
```

This script:
- Creates a Python venv in `backend/.venv`
- Installs backend deps from `requirements.txt`
- Starts FastAPI on `:4000`
- Installs frontend deps with `npm install`
- Starts Vite on `:3000`

### 3. Open Browser

- **Frontend UI**: [http://localhost:3000](http://localhost:3000)
- **Backend API**: [http://localhost:4000/health](http://localhost:4000/health)
- **API Docs**: [http://localhost:4000/docs](http://localhost:4000/docs)

---

## 🎮 How to Use

1. **Open** [http://localhost:3000](http://localhost:3000)
2. **Type** your intent (e.g., "Build a real-time chat app with Redis pub/sub")
3. **Hit EXECUTE** — the swarm spawns and begins
4. **Watch** the terminal logs and progress bar fill in real-time
5. **Download** artifacts when complete

---

## 🧬 Project Structure

```
nexus/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI server + WebSocket
│   │   ├── database.py          # SQLAlchemy async DB
│   │   ├── marketplace_models.py # ORM models
│   │   ├── marketplace.py       # Marketplace API router
│   │   └── auth.py              # Auth stub (replace with real JWT)
│   ├── requirements.txt
│   └── .env
│
├── nebula/
│   └── core/
│       ├── swarm.py             # Multi-agent orchestrator
│       └── mooncake_cache.py    # KV-cache simulation
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── HomePage.jsx     # Landing + intent submission
│   │   │   └── ProjectPage.jsx  # Live progress stream
│   │   ├── App.jsx              # Router setup
│   │   ├── main.jsx             # React entry
│   │   └── index.css            # Tailwind directives
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── .env
│
├── artifacts/                    # Generated outputs land here
├── start.sh                      # Master run script
└── README.md                     # You are here
```

---

## 🔌 API Endpoints

### Health
```bash
GET /health
```

Returns service status + active projects count.

### Create Project
```bash
POST /api/projects
Content-Type: application/json

{
  "intent": "Build a multiplayer tic-tac-toe game",
  "user_id": "anonymous"
}
```

Returns:
```json
{
  "project_id": "neb-abc123def456",
  "status": "queued",
  "message": "Swarm spawned. Connect to /ws/{project_id} for live updates.",
  "ws_url": "/ws/neb-abc123def456"
}
```

### Get Project
```bash
GET /api/projects/{project_id}
```

Returns project status, phase, progress.

### WebSocket
```
ws://localhost:4000/ws/{project_id}
```

Streams events:
- `connected` — Initial handshake
- `system` — Boot messages
- `phase` — Phase transitions (analyzing, architecting, coding, etc.)
- `agent` — Agent outputs
- `artifact` — File generation events
- `complete` — Final success
- `error` — Crash events

---

## 🤖 Swarm Architecture

```
User Intent
    ↓
FastAPI (/api/projects POST)
    ↓
Spawn Background Task
    ↓
NebulaSwarm.dispatch(intent)
    ↓
┌──────────────────────────────────┐
│   Architect  (Planning)          │
│   Coder      (Implementation)    │
│   Auditor    (Security Review)   │
└──────────────────────────────────┘
    ↓
Synthesize Results
    ↓
Broadcast over WebSocket (phase, progress, artifacts)
    ↓
Frontend updates UI in real-time
```

---

## 🔐 Environment Variables

### Backend (`backend/.env`)

```bash
# Server
PORT=4000
LOG_LEVEL=INFO

# CORS
CORS_ALLOW_ORIGINS=http://localhost:3000

# Database (swap to postgres:// for prod)
DATABASE_URL=sqlite+aiosqlite:///./nebula_marketplace.db

# AI Provider Keys (optional — swarm runs in stub mode if missing)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GROQ_API_KEY=
OPENROUTER_API_KEY=
GOOGLE_API_KEY=

# Artifacts
ARTIFACTS_DIR=./artifacts
```

### Frontend (`frontend/.env`)

```bash
VITE_API_URL=http://localhost:4000
VITE_WS_URL=ws://localhost:4000
```

---

## 🛠️ Development

### Backend Only

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 4000
```

### Frontend Only

```bash
cd frontend
npm run dev
```

### Install Dependencies Manually

```bash
# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

---

## 📦 Production Deployment

1. **Swap database** from SQLite to Postgres:
   ```bash
   DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
   ```

2. **Add real AI keys** in `backend/.env`:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-...
   GROQ_API_KEY=gsk_...
   ```

3. **Build frontend**:
   ```bash
   cd frontend
   npm run build
   ```
   Outputs to `frontend/dist/` — serve with Nginx or Caddy.

4. **Run backend** with Gunicorn + Uvicorn workers:
   ```bash
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:4000
   ```

5. **Reverse proxy** with Nginx or Caddy for HTTPS.

---

## 🧪 Testing

### Test Backend

```bash
curl http://localhost:4000/health
```

Expected:
```json
{
  "ok": true,
  "service": "nexus-nebula-universe",
  "version": "3.0.0",
  "active_projects": 0,
  "ws_connections": 0,
  "timestamp": "2025-02-03T12:34:56.789Z"
}
```

### Test WebSocket

```bash
websocat ws://localhost:4000/ws/test-project-id
```

Or use the frontend UI — it's already wired.

---

## 🚨 Known Issues & Fixes

### "Module not found" errors

Run:
```bash
cd backend && source .venv/bin/activate && pip install -r requirements.txt
cd ../frontend && npm install
```

### Port 4000 or 3000 already in use

Kill existing processes:
```bash
lsof -ti:4000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

### WebSocket connection refused

Make sure backend is running first. Frontend proxies `/ws` to `localhost:4000`.

---

## 📜 License

MIT — Build whatever the fuck you want with this.

---

## 🔥 Final Notes

- **Mooncake Cache** is a KV-cache simulator. In a real LLM setup, this would store precomputed key-value tensors to skip redundant context prefills.
- **Swarm agents** are currently stubs that simulate LLM calls. Wire in real APIs (Anthropic, OpenAI, Groq) by filling the `.env` keys.
- **Marketplace module** is included but dormant. Enable it by wiring Stripe + user auth.
- **Real-time progress** is powered by WebSocket broadcast. Every phase transition triggers an event that updates the frontend UI instantly.

Built with chaos, caffeine, and a complete disregard for sleep schedules.

**Now go build something fucking legendary.**
