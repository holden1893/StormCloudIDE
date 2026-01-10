from __future__ import annotations

from typing import TypedDict, Dict, Any, List


class SwarmState(TypedDict, total=False):
    project_id: str
    owner_id: str
    title: str
    kind: str
    prompt: str

    iterations: int
    max_iterations: int

    plan: str
    code_files: Dict[str, str]
    image_prompts: List[str]
    image_urls: List[str]

    review_passed: bool
    review_notes: str

    artifact_storage_path: str
    artifact_signed_url: str
    artifact_id: str

    timeline: List[Dict[str, Any]]
