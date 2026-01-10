from __future__ import annotations

from typing import Literal, Optional, Dict, Any
from pydantic import BaseModel, Field


ProjectKind = Literal["webapp", "api", "component", "image", "mixed"]


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=5, max_length=8000)
    kind: ProjectKind = "webapp"
    project_id: Optional[str] = None
    title: Optional[str] = Field(default=None, max_length=120)


class GenerateEvent(BaseModel):
    event: str
    node: str | None = None
    message: str | None = None
    data: Dict[str, Any] = Field(default_factory=dict)
