from __future__ import annotations

import os
import json
import uuid
from typing import AsyncIterator, Dict, Any

from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .config import settings
from .rate_limit import rate_limit
from .auth import get_current_user, AuthUser
from .models import GenerateRequest
from .supabase_client import supabase_service
from .utils.sse import sse
from .utils.zipper import make_zip_bytes
from .swarm.graph import run_graph


app = FastAPI(title="Nexus Nebula Universe API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.web_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

sb = supabase_service()

T_PROJECTS = "nexus_projects"
T_ARTIFACTS = "nexus_artifacts"
T_LISTINGS = "nexus_marketplace_listings"


@app.get("/health")
async def health():
    return {"ok": True, "service": "nexus-nebula-api"}


def _env_keys() -> Dict[str, str | None]:
    keys = {
        "GROQ_API_KEY": settings.groq_api_key or os.getenv("GROQ_API_KEY"),
        "OPENROUTER_API_KEY": settings.openrouter_api_key or os.getenv("OPENROUTER_API_KEY"),
        "GOOGLE_API_KEY": settings.google_api_key or os.getenv("GOOGLE_API_KEY"),
    }
    for k, v in keys.items():
        if v:
            os.environ[k] = v
    if settings.ollama_base_url:
        os.environ["OLLAMA_API_BASE"] = settings.ollama_base_url
    return keys


def _model_chains() -> Dict[str, list[str]]:
    return {
        "research": [
            settings.model_gemini,
            settings.model_openrouter_gpt4o,
            settings.model_groq,
            settings.model_ollama,
        ],
        "plan": [
            settings.model_openrouter_claude,
            settings.model_gemini,
            settings.model_groq,
            settings.model_ollama,
        ],
        "code": [
            settings.model_groq,
            settings.model_openrouter_gpt4o,
            settings.model_gemini,
            settings.model_ollama,
        ],
        "design": [
            settings.model_openrouter_gpt4o,
            settings.model_gemini,
            settings.model_groq,
            settings.model_ollama,
        ],
        "review": [
            settings.model_openrouter_claude,
            settings.model_groq,
            settings.model_gemini,
            settings.model_ollama,
        ],
    }


async def _create_or_load_project(req: GenerateRequest, user: AuthUser) -> Dict[str, Any]:
    if req.project_id:
        row = sb.table(T_PROJECTS).select("*").eq("id", req.project_id).eq("owner_id", user.id).maybe_single().execute()
        data = row.data
        if not data:
            raise HTTPException(status_code=404, detail="Project not found")
        return data

    title = req.title or f"{req.kind.upper()} Project"
    ins = sb.table(T_PROJECTS).insert(
        {
            "owner_id": user.id,
            "title": title,
            "prompt": req.prompt,
            "kind": req.kind,
            "status": "running",
            "swarm_state": {},
        }
    ).execute()
    return ins.data[0]


async def _persist_project_state(project_id: str, user_id: str, status: str, swarm_state: Dict[str, Any]) -> None:
    sb.table(T_PROJECTS).update(
        {"status": status, "swarm_state": swarm_state}
    ).eq("id", project_id).eq("owner_id", user_id).execute()


async def _store_artifact(project_id: str, user: AuthUser, zip_bytes: bytes, meta: Dict[str, Any]) -> Dict[str, Any]:
    bucket = settings.supabase_artifacts_bucket
    artifact_id = str(uuid.uuid4())
    storage_path = f"{user.id}/{project_id}/{artifact_id}.zip"

    sb.storage.from_(bucket).upload(
        path=storage_path,
        file=zip_bytes,
        file_options={"content-type": "application/zip", "upsert": "true"},
    )

    signed = sb.storage.from_(bucket).create_signed_url(storage_path, 60 * 60)
    signed_url = signed.get("signedURL") or signed.get("signedUrl") or signed.get("signed_url")

    ins = sb.table(T_ARTIFACTS).insert(
        {
            "project_id": project_id,
            "owner_id": user.id,
            "kind": "zip",
            "storage_path": storage_path,
            "mime_type": "application/zip",
            "meta": meta,
        }
    ).execute()

    return {"artifact": ins.data[0], "signed_url": signed_url}


@app.get("/projects")
async def list_projects(user: AuthUser = Depends(get_current_user)):
    rows = sb.table(T_PROJECTS).select("id,title,kind,status,created_at,updated_at").eq("owner_id", user.id).order("created_at", desc=True).execute()
    return {"projects": rows.data}


@app.get("/projects/{project_id}")
async def get_project(project_id: str, user: AuthUser = Depends(get_current_user)):
    row = sb.table(T_PROJECTS).select("*").eq("id", project_id).eq("owner_id", user.id).maybe_single().execute()
    if not row.data:
        raise HTTPException(status_code=404, detail="Not found")
    return {"project": row.data}


# --- Live Preview + Editor: project files API ---
MAX_FILE_BYTES = 250_000        # per file
MAX_TOTAL_BYTES = 2_000_000     # total payload

def _validate_files_payload(files: dict) -> dict:
    if not isinstance(files, dict):
        raise HTTPException(status_code=400, detail="files must be an object {path: content}")
    total = 0
    cleaned = {}
    for k, v in files.items():
        if not isinstance(k, str) or not isinstance(v, str):
            raise HTTPException(status_code=400, detail="files keys/values must be strings")
        if len(k) > 300 or ".." in k or k.startswith("/"):
            raise HTTPException(status_code=400, detail=f"Invalid path: {k}")
        b = len(v.encode("utf-8"))
        if b > MAX_FILE_BYTES:
            raise HTTPException(status_code=400, detail=f"File too large: {k}")
        total += b
        cleaned[k] = v
    if total > MAX_TOTAL_BYTES:
        raise HTTPException(status_code=400, detail="Total files payload too large")
    return cleaned


@app.get("/projects/{project_id}/files")
async def get_project_files(project_id: str, user: AuthUser = Depends(get_current_user)):
    row = sb.table(T_PROJECTS).select("*").eq("id", project_id).eq("owner_id", user.id).maybe_single().execute()
    if not row.data:
        raise HTTPException(status_code=404, detail="Not found")
    state = row.data.get("swarm_state") or {}
    return {
        "project": {
            "id": row.data["id"],
            "title": row.data["title"],
            "kind": row.data["kind"],
            "status": row.data["status"],
        },
        "files": state.get("code_files") or {},
        "preview": {
            "artifact_id": state.get("artifact_id"),
            "artifact_signed_url": state.get("artifact_signed_url"),
            "image_prompts": state.get("image_prompts") or [],
            "image_urls": state.get("image_urls") or [],
            "review_notes": state.get("review_notes"),
            "review_passed": state.get("review_passed"),
        },
    }


@app.put("/projects/{project_id}/files")
async def put_project_files(project_id: str, payload: dict, user: AuthUser = Depends(get_current_user)):
    files = _validate_files_payload(payload.get("files") or {})
    row = sb.table(T_PROJECTS).select("*").eq("id", project_id).eq("owner_id", user.id).maybe_single().execute()
    if not row.data:
        raise HTTPException(status_code=404, detail="Not found")

    state = row.data.get("swarm_state") or {}
    state["code_files"] = files
    state.setdefault("timeline", []).append({"node": "User", "event": "edited_files", "files": len(files)})

    sb.table(T_PROJECTS).update({"status": "edited", "swarm_state": state}).eq("id", project_id).eq("owner_id", user.id).execute()
    return {"ok": True, "files": files}


@app.get("/marketplace/listings")
async def list_marketplace():
    rows = sb.table(T_LISTINGS).select(
        "id,title,description,price_cents,currency,status,created_at,artifact_id,seller_id"
    ).eq("status", "active").order("created_at", desc=True).execute()
    return {"listings": rows.data}


@app.post("/marketplace/listings")
async def create_listing(payload: dict, user: AuthUser = Depends(get_current_user)):
    artifact_id = payload.get("artifact_id")
    title = (payload.get("title") or "").strip()
    description = (payload.get("description") or "").strip()
    price_cents = int(payload.get("price_cents") or 0)

    if not artifact_id or not title:
        raise HTTPException(status_code=400, detail="artifact_id and title are required")
    if price_cents < 0:
        raise HTTPException(status_code=400, detail="price_cents must be >= 0")

    art = sb.table(T_ARTIFACTS).select("id,owner_id").eq("id", artifact_id).maybe_single().execute().data
    if not art or art["owner_id"] != user.id:
        raise HTTPException(status_code=403, detail="Artifact not owned by user")

    ins = sb.table(T_LISTINGS).insert(
        {
            "artifact_id": artifact_id,
            "seller_id": user.id,
            "title": title,
            "description": description,
            "price_cents": price_cents,
            "currency": payload.get("currency") or "usd",
            "status": "active",
        }
    ).execute()
    return {"listing": ins.data[0]}


@app.post("/generate")
async def generate(req: GenerateRequest, request: Request, user: AuthUser = Depends(get_current_user)):
    rate_limit(request)

    keys = _env_keys()
    chains = _model_chains()

    project = await _create_or_load_project(req, user)
    project_id = project["id"]

    state: Dict[str, Any] = {
        "project_id": project_id,
        "owner_id": user.id,
        "title": project.get("title") or "Untitled Project",
        "kind": req.kind,
        "prompt": req.prompt,
        "iterations": 0,
        "max_iterations": 2,
        "timeline": [],
    }

    async def event_stream() -> AsyncIterator[str]:
        await _persist_project_state(project_id, user.id, "running", state)
        yield sse("status", {"message": "swarm_started", "project_id": project_id})

        try:
            final_state = state

            async for ev in run_graph(final_state, chains=chains, api_keys_env=keys):
                if ev["type"] == "node_start":
                    yield sse("node", {"phase": "start", "node": ev["node"]})
                elif ev["type"] == "node_end":
                    final_state = ev["state"] or final_state
                    await _persist_project_state(project_id, user.id, "running", final_state)
                    yield sse("node", {"phase": "end", "node": ev["node"], "review": final_state.get("review_notes")})

            files = dict(final_state.get("code_files") or {})
            manifest = {
                "project_id": project_id,
                "kind": req.kind,
                "review_passed": bool(final_state.get("review_passed")),
                "review_notes": final_state.get("review_notes"),
                "image_prompts": final_state.get("image_prompts", []),
            }
            files["nexus.manifest.json"] = json.dumps(manifest, indent=2)

            zip_bytes = make_zip_bytes(files)
            stored = await _store_artifact(project_id, user, zip_bytes, meta=manifest)

            final_state["artifact_storage_path"] = stored["artifact"]["storage_path"]
            final_state["artifact_signed_url"] = stored["signed_url"] or ""
            final_state["artifact_id"] = stored["artifact"]["id"]

            await _persist_project_state(project_id, user.id, "completed", final_state)

            yield sse("artifact", {"artifact_id": final_state["artifact_id"], "signed_url": final_state["artifact_signed_url"]})
            yield sse("status", {"message": "completed", "project_id": project_id})
        except Exception as e:
            await _persist_project_state(project_id, user.id, "failed", state)
            yield sse("error", {"message": str(e)})
            yield sse("status", {"message": "failed", "project_id": project_id})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/payments/stripe/checkout")
async def stripe_checkout(payload: dict, user: AuthUser = Depends(get_current_user)):
    if not settings.stripe_secret_key:
        raise HTTPException(status_code=400, detail="STRIPE_SECRET_KEY not configured")
    return {"checkout_url": f"{settings.public_app_url}/marketplace?stripe=TODO"}


# --- Shares (public preview links) ---
class CreateShareRequest(BaseModel):
    project_id: str
    title: str | None = None
    expires_at: str | None = None  # ISO string


@app.post("/shares")
async def create_share(req: CreateShareRequest, user: AuthUser = Depends(get_current_user)):
    row = sb.table(T_PROJECTS).select("*").eq("id", req.project_id).eq("owner_id", user.id).maybe_single().execute()
    if not row.data:
        raise HTTPException(status_code=404, detail="Project not found")

    state = row.data.get("swarm_state") or {}
    files = state.get("code_files") or {}

    payload = {
        "owner_id": user.id,
        "project_id": req.project_id,
        "title": req.title or row.data.get("title") or "Shared Preview",
        "files": files,
    }

    if req.expires_at:
        payload["expires_at"] = req.expires_at

    created = sb.table(T_SHARES).insert(payload).execute()
    share = created.data[0] if created.data else None
    if not share:
        raise HTTPException(status_code=500, detail="Failed to create share")

    return {"share": {"id": share["id"], "title": share.get("title"), "created_at": share.get("created_at"), "expires_at": share.get("expires_at")}}


@app.get("/shares/{share_id}")
async def get_share(share_id: str):
    row = sb.table(T_SHARES).select("*").eq("id", share_id).maybe_single().execute()
    if not row.data:
        raise HTTPException(status_code=404, detail="Not found")

    share = row.data
    # Optional expiry enforcement
    expires_at = share.get("expires_at")
    if expires_at:
        # Supabase returns ISO; compare lexicographically is unsafe. Parse best-effort.
        from datetime import datetime, timezone
        try:
            exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if exp < datetime.now(timezone.utc):
                raise HTTPException(status_code=410, detail="Share expired")
        except ValueError:
            pass

    return {"share": {"id": share["id"], "title": share.get("title"), "project_id": share.get("project_id")}, "files": share.get("files") or {}}

