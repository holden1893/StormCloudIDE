# Vultr Deployment (Docker + Caddy)

This deploys:
- Next.js web (apps/web)
- FastAPI api (apps/api)
- Redis
- Qdrant
- Caddy reverse proxy + HTTPS

## Steps (Vultr Ubuntu)
1) Install Docker + Compose plugin
2) Copy this repo to the VPS
3) Edit:
- `deploy/vultr/Caddyfile` (set YOUR_DOMAIN, email)
- `deploy/vultr/.env` from `.env.example`

4) Run:
```bash
cd deploy/vultr
cp .env.example .env
docker compose up -d --build
```

## Notes
- Caddy terminates TLS automatically.
- Ensure your DNS A-record points to the Vultr public IP.
- For Supabase, use your hosted project; set the keys in `.env`.
