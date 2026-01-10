from __future__ import annotations

from typing import AsyncIterator, Dict, Any

from langgraph.graph import StateGraph, END  # type: ignore

from .models import SwarmState
from .nodes import node_research, node_plan, node_code, node_design, node_review


def build_graph():
    g = StateGraph(SwarmState)

    g.add_node("Researcher", node_research)
    g.add_node("Planner", node_plan)
    g.add_node("Coder", node_code)
    g.add_node("Designer", node_design)
    g.add_node("Reviewer", node_review)

    g.set_entry_point("Researcher")
    g.add_edge("Researcher", "Planner")
    g.add_edge("Planner", "Coder")
    g.add_edge("Coder", "Designer")
    g.add_edge("Designer", "Reviewer")

    def route_after_review(state: SwarmState) -> str:
        iters = int(state.get("iterations", 0))
        max_iters = int(state.get("max_iterations", 2))
        if not state.get("review_passed", False) and iters < max_iters:
            state["iterations"] = iters + 1
            return "Planner"
        return END

    g.add_conditional_edges("Reviewer", route_after_review, {"Planner": "Planner", END: END})

    return g.compile()


async def run_graph(
    initial_state: SwarmState,
    *,
    chains: Dict[str, list[str]],
    api_keys_env: Dict[str, str | None],
) -> AsyncIterator[Dict[str, Any]]:
    app = build_graph()

    node_kwargs = {
        "Researcher": {"model_chain": chains["research"], "api_keys_env": api_keys_env},
        "Planner": {"model_chain": chains["plan"], "api_keys_env": api_keys_env},
        "Coder": {"model_chain": chains["code"], "api_keys_env": api_keys_env},
        "Designer": {"model_chain": chains["design"], "api_keys_env": api_keys_env},
        "Reviewer": {"model_chain": chains["review"], "api_keys_env": api_keys_env},
    }

    async for event in app.astream_events(initial_state, version="v2", config={"configurable": node_kwargs}):
        et = event.get("event")
        name = event.get("name")

        if et == "on_chain_start" and name in node_kwargs:
            yield {"type": "node_start", "node": name}
        elif et == "on_chain_end" and name in node_kwargs:
            out = event.get("data", {}).get("output")
            yield {"type": "node_end", "node": name, "state": out}
