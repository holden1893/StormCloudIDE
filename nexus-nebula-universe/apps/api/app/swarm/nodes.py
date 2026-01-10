from __future__ import annotations

import json
from typing import Any, Dict, List, AsyncIterator, Tuple

from litellm import acompletion  # type: ignore

from .models import SwarmState
from .prompts import (
    SYSTEM_BASE,
    RESEARCH_PROMPT,
    PLANNER_PROMPT,
    CODER_PROMPT,
    DESIGNER_PROMPT,
    REVIEWER_PROMPT,
)


def _safe_json_loads(s: str) -> Any:
    s = s.strip()
    if s.startswith("{") and s.endswith("}"):
        return json.loads(s)
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(s[start : end + 1])
    return json.loads(s)


async def _stream_completion(
    model: str,
    messages: List[Dict[str, str]],
    api_keys_env: Dict[str, str | None],
) -> AsyncIterator[str]:
    api_key = None
    if model.startswith("groq/"):
        api_key = api_keys_env.get("GROQ_API_KEY")
    elif model.startswith("openrouter/"):
        api_key = api_keys_env.get("OPENROUTER_API_KEY")
    elif model.startswith("gemini/"):
        api_key = api_keys_env.get("GOOGLE_API_KEY")
    elif model.startswith("ollama/"):
        api_key = None

    resp = await acompletion(
        model=model,
        messages=messages,
        stream=True,
        api_key=api_key,
    )

    async for chunk in resp:
        try:
            delta = chunk["choices"][0]["delta"].get("content")  # type: ignore[index]
        except Exception:
            delta = None
        if delta:
            yield delta


async def _one_shot_completion(
    model: str,
    messages: List[Dict[str, str]],
    api_keys_env: Dict[str, str | None],
) -> str:
    api_key = None
    if model.startswith("groq/"):
        api_key = api_keys_env.get("GROQ_API_KEY")
    elif model.startswith("openrouter/"):
        api_key = api_keys_env.get("OPENROUTER_API_KEY")
    elif model.startswith("gemini/"):
        api_key = api_keys_env.get("GOOGLE_API_KEY")

    resp = await acompletion(
        model=model,
        messages=messages,
        stream=False,
        api_key=api_key,
    )
    return resp["choices"][0]["message"]["content"]  # type: ignore[index]


async def _try_models_one_shot(
    models: List[str],
    messages: List[Dict[str, str]],
    api_keys_env: Dict[str, str | None],
) -> Tuple[str, str]:
    last_err: Exception | None = None
    for m in models:
        try:
            out = await _one_shot_completion(m, messages, api_keys_env)
            return m, out
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"All models failed. Last error: {last_err!r}")


async def node_research(state: SwarmState, *, model_chain: List[str], api_keys_env: Dict[str, str | None]) -> SwarmState:
    messages = [
        {"role": "system", "content": SYSTEM_BASE},
        {"role": "user", "content": f"{RESEARCH_PROMPT}\n\nUSER PROMPT:\n{state['prompt']}"},
    ]
    _, text = await _try_models_one_shot(model_chain, messages, api_keys_env)
    state["timeline"].append({"node": "Researcher", "event": "done"})
    state["plan"] = f"[Research Notes]\n{text}\n\n"
    return state


async def node_plan(state: SwarmState, *, model_chain: List[str], api_keys_env: Dict[str, str | None]) -> SwarmState:
    messages = [
        {"role": "system", "content": SYSTEM_BASE},
        {"role": "user", "content": f"{PLANNER_PROMPT}\n\nKIND={state['kind']}\nPROMPT:\n{state['prompt']}"},
    ]
    _, text = await _try_models_one_shot(model_chain, messages, api_keys_env)
    state["timeline"].append({"node": "Planner", "event": "done"})
    state["plan"] = state.get("plan", "") + f"[Plan]\n{text}\n"
    return state


async def node_code(state: SwarmState, *, model_chain: List[str], api_keys_env: Dict[str, str | None]) -> SwarmState:
    messages = [
        {"role": "system", "content": SYSTEM_BASE},
        {"role": "user", "content": f"{CODER_PROMPT}\n\nKIND={state['kind']}\nPROMPT:\n{state['prompt']}\n\nPLAN:\n{state.get('plan','')}"},
    ]
    _, raw = await _try_models_one_shot(model_chain, messages, api_keys_env)
    data = _safe_json_loads(raw)
    files = {}
    for f in data.get("files", []):
        if isinstance(f, dict) and "path" in f and "content" in f:
            files[str(f["path"])] = str(f["content"])
    if not files:
        raise RuntimeError("Coder returned no files.")
    state["code_files"] = files
    state["timeline"].append({"node": "Coder", "event": "done", "files": len(files)})
    return state


async def node_design(state: SwarmState, *, model_chain: List[str], api_keys_env: Dict[str, str | None]) -> SwarmState:
    messages = [
        {"role": "system", "content": SYSTEM_BASE},
        {"role": "user", "content": f"{DESIGNER_PROMPT}\n\nPROMPT:\n{state['prompt']}\nPLAN:\n{state.get('plan','')}"},
    ]
    _, raw = await _try_models_one_shot(model_chain, messages, api_keys_env)
    data = _safe_json_loads(raw)
    prompts = data.get("image_prompts") or []
    prompts = [str(p) for p in prompts][:3]
    state["image_prompts"] = prompts
    state["timeline"].append({"node": "Designer", "event": "done", "count": len(prompts)})
    return state


async def node_review(state: SwarmState, *, model_chain: List[str], api_keys_env: Dict[str, str | None]) -> SwarmState:
    files = state.get("code_files", {})
    missing_readme = "README.md" not in files

    notes = []
    passed = True

    if missing_readme:
        passed = False
        notes.append("Missing README.md")

    joined = "\n".join(files.values())
    if "SUPABASE_SERVICE_ROLE_KEY" in joined or "STRIPE_SECRET_KEY" in joined:
        passed = False
        notes.append("Hardcoded secret-looking env var name found. Use .env, never inline secrets.")

    messages = [
        {"role": "system", "content": SYSTEM_BASE},
        {"role": "user", "content": f"{REVIEWER_PROMPT}\n\nFILES:\n{list(files.keys())}\n\nREADME PREVIEW:\n{files.get('README.md','(missing)')[:1200]}"},
    ]
    try:
        _, raw = await _try_models_one_shot(model_chain, messages, api_keys_env)
        data = _safe_json_loads(raw)
        llm_pass = bool(data.get("pass", True))
        llm_notes = str(data.get("notes", "")).strip()
        if not llm_pass:
            passed = False
        if llm_notes:
            notes.append(llm_notes)
    except Exception:
        pass

    state["review_passed"] = passed
    state["review_notes"] = "; ".join([n for n in notes if n]) or ("OK" if passed else "Needs fixes")
    state["timeline"].append({"node": "Reviewer", "event": "done", "pass": passed})
    return state
