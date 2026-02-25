"""Discovery engine API routes with SSE streaming."""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Literal

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from discovery_engine.core.graph import build_discovery_graph
from discovery_engine.core.state import DiscoveryState

router = APIRouter()


class DiscoveryRequest(BaseModel):
    """Request body for /api/discovery/stream."""

    query: str
    disciplines: list[str] = ["physics", "biology", "psychology"]
    mode: Literal["guided", "autonomous", "cross_domain"] = "guided"


class DiscoveryResponse(BaseModel):
    """Final response after graph execution."""

    session_id: str
    synthesis: str
    confidence_tier: str
    quality_score: float
    quality_issues: list[str]
    verses_count: int
    science_findings_count: int
    humanities_findings_count: int
    discovery_id: str | None = None


def _get_graph(request: Request):
    """Get the pre-built graph from app state, or build a fresh one."""
    if hasattr(request.app.state, "graph") and request.app.state.graph is not None:
        return request.app.state.graph
    # Fallback: build without services (legacy behaviour)
    return build_discovery_graph()


@router.post("/stream")
async def stream_discovery(
    body: DiscoveryRequest, request: Request
) -> StreamingResponse:
    """Launch a discovery exploration and stream results via SSE."""
    session_id = str(uuid.uuid4())

    initial_state: DiscoveryState = {
        "query": body.query,
        "disciplines": body.disciplines,
        "mode": body.mode,
        "iteration_count": 0,
        "streaming_updates": [],
    }

    async def event_generator():
        yield _sse_event("session_start", {"session_id": session_id})

        try:
            graph = _get_graph(request)
            config = {"configurable": {"thread_id": session_id}}

            sent_stages: set[str] = set()

            if hasattr(graph, "astream"):
                async for chunk in graph.astream(initial_state, config=config):
                    for _node_name, node_state in chunk.items():
                        updates = node_state.get("streaming_updates", [])
                        for update in updates:
                            stage = update.get("stage", "")
                            if stage and stage not in sent_stages:
                                sent_stages.add(stage)
                                yield _sse_event(stage, update)
                                await asyncio.sleep(0.01)

                final_state = await graph.aget_state(config)
                state_values = (
                    final_state.values
                    if hasattr(final_state, "values")
                    else final_state
                )
            else:
                state_values = await graph.ainvoke(initial_state, config=config)
                for update in state_values.get("streaming_updates", []):
                    stage = update.get("stage", "")
                    if stage:
                        yield _sse_event(stage, update)
                        await asyncio.sleep(0.01)

            yield _sse_event(
                "complete",
                {
                    "session_id": session_id,
                    "synthesis": state_values.get("synthesis", ""),
                    "confidence_tier": state_values.get("confidence_tier", ""),
                    "quality_score": state_values.get("quality_score", 0.0),
                    "quality_issues": state_values.get("quality_issues", []),
                    "verses_count": len(state_values.get("verses", [])),
                    "science_findings_count": len(
                        state_values.get("science_findings", [])
                    ),
                    "humanities_findings_count": len(
                        state_values.get("humanities_findings", [])
                    ),
                    "discovery_id": state_values.get("discovery_id"),
                },
            )

        except Exception as exc:
            yield _sse_event("error", {"error": str(exc)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/explore")
async def explore(body: DiscoveryRequest, request: Request) -> DiscoveryResponse:
    """Non-streaming discovery exploration (returns full result)."""
    session_id = str(uuid.uuid4())

    initial_state: DiscoveryState = {
        "query": body.query,
        "disciplines": body.disciplines,
        "mode": body.mode,
        "iteration_count": 0,
        "streaming_updates": [],
    }

    graph = _get_graph(request)
    config = {"configurable": {"thread_id": session_id}}
    result = await graph.ainvoke(initial_state, config=config)

    return DiscoveryResponse(
        session_id=session_id,
        synthesis=result.get("synthesis", ""),
        confidence_tier=result.get("confidence_tier", ""),
        quality_score=result.get("quality_score", 0.0),
        quality_issues=result.get("quality_issues", []),
        verses_count=len(result.get("verses", [])),
        science_findings_count=len(result.get("science_findings", [])),
        humanities_findings_count=len(result.get("humanities_findings", [])),
        discovery_id=result.get("discovery_id"),
    )


@router.get("/discoveries")
async def list_discoveries(request: Request, tier: str | None = None) -> dict:
    """List verified discoveries, optionally filtered by tier."""
    if hasattr(request.app.state, "db") and request.app.state.db is not None:
        discoveries = await request.app.state.db.list_discoveries(tier=tier)
        # Convert UUIDs to strings for JSON serialization
        for d in discoveries:
            for k, v in d.items():
                if hasattr(v, "hex"):
                    d[k] = str(v)
        return {"discoveries": discoveries, "filter": tier}
    return {"discoveries": [], "filter": tier}


def _sse_event(event: str, data: dict) -> str:
    json_data = json.dumps(data, ensure_ascii=False, default=str)
    return f"event: {event}\ndata: {json_data}\n\n"
