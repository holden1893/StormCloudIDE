# Nexus Nebula Universe 🌌

A universal AI-powered creation platform with:
- Supabase Auth + Postgres + Storage
- LangGraph multi-agent swarm
- LiteLLM provider cascade (Groq → OpenRouter → Gemini → Ollama)
- Marketplace listings + Supabase Realtime

## 1) Supabase
1. Run `supabase/schema.sql` in the SQL editor.
2. Create a private bucket: `nexus-nebula-artifacts`

## 2) API
```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## 3) Web
```bash
cd apps/web
npm install
npm run dev -- --port 3000
```

## 4) Use it
- Open http://localhost:3000
- Login via magic link
- Dashboard → Run Swarm → Download artifact zip

## Notes
- `/generate` streams SSE events.
- Artifacts are uploaded to Supabase Storage and returned as signed URLs (expire).
- Stripe endpoint is a stub: `POST /payments/stripe/checkout`


## Live Preview Studio
- Open a project in `/studio/:id` for a Replit-style editor + live preview.


## WebContainer Live Preview (Option A)
- The Studio preview supports running full Node projects (Next.js) *in the browser* using StackBlitz WebContainers.
- This requires cross‑origin isolation headers (COOP/COEP). This repo sets them via `apps/web/next.config.mjs`.
- Production must be served over HTTPS (localhost is OK for dev).
