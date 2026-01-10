from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import httpx
from fastapi import Header, HTTPException

from .config import settings


@dataclass(frozen=True)
class AuthUser:
    id: str
    email: Optional[str]


async def get_current_user(authorization: str | None = Header(default=None)) -> AuthUser:
    """
    Validates Supabase access token by calling Supabase Auth endpoint.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    url = f"{settings.supabase_url}/auth/v1/user"
    headers = {
        "Authorization": f"Bearer {token}",
        "apikey": settings.supabase_anon_key,
    }

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(url, headers=headers)

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid token")

    data = resp.json()
    return AuthUser(id=data["id"], email=data.get("email"))
