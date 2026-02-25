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

            source = (
                _stream_from_graph(graph, initial_state, config, session_id)
                if hasattr(graph, "astream")
                else _stream_from_fallback(graph, initial_state, config, session_id)
            )
            async for event in source:
                yield event

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


async def _stream_from_graph(graph, initial_state, config, session_id):
    """Stream events from a LangGraph compiled graph."""
    emitted: set[str] = set()
    accumulated_state: dict = {}

    async for chunk in graph.astream(initial_state, config=config):
        for node_name, node_state in chunk.items():
            accumulated_state.update(node_state)

            for event in _translate_node(node_name, node_state, emitted):
                yield event
                await asyncio.sleep(0.01)

    # Emit final complete event
    yield _complete_event(accumulated_state, session_id)


async def _stream_from_fallback(graph, initial_state, config, session_id):
    """Stream events from the FallbackGraph (runs ainvoke then emits)."""
    state_values = await graph.ainvoke(initial_state, config=config)
    emitted: set[str] = set()

    # Replay updates in the correct frontend order
    for update in state_values.get("streaming_updates", []):
        stage = update.get("stage", "")
        for event in _translate_node(stage, {**update, **_extract(state_values, stage)}, emitted):
            yield event
            await asyncio.sleep(0.01)

    yield _complete_event(state_values, session_id)


def _extract(state: dict, stage: str) -> dict:
    """Extract relevant state data for a given stage."""
    if stage == "quran_rag":
        return {"verses": state.get("verses", [])}
    if stage == "science":
        return {"science_findings": state.get("science_findings", [])}
    if stage == "humanities":
        return {"humanities_findings": state.get("humanities_findings", [])}
    if stage == "synthesis":
        return {"synthesis": state.get("synthesis", "")}
    if stage == "quality_review":
        return {
            "quality_score": state.get("quality_score", 0),
            "quality_issues": state.get("quality_issues", []),
        }
    return {}


def _translate_node(node_name: str, node_state: dict, emitted: set[str]):
    """Translate internal graph node output to frontend SSE events."""

    if node_name == "route_query" and "quran_search" not in emitted:
        emitted.add("quran_search")
        yield _sse_event("quran_search", {"stage": "quran_search"})

    elif node_name == "quran_rag":
        if "quran_search" not in emitted:
            emitted.add("quran_search")
            yield _sse_event("quran_search", {"stage": "quran_search"})

        verses = node_state.get("verses", [])
        if verses and "quran_found" not in emitted:
            emitted.add("quran_found")
            yield _sse_event("quran_found", {
                "stage": "quran_found",
                "verses": verses,
            })

    elif node_name == "linguistic" and "linguistic" not in emitted:
        emitted.add("linguistic")
        yield _sse_event("linguistic", {"stage": "linguistic"})

    elif node_name in ("science", "humanities"):
        findings_key = "science_findings" if node_name == "science" else "humanities_findings"
        findings = node_state.get(findings_key, [])
        for f in findings:
            yield _sse_event("science_finding", {
                "stage": "science_finding",
                "finding": f,
            })

    elif node_name == "tafseer":
        if "tafseer" not in emitted:
            emitted.add("tafseer")
            yield _sse_event("tafseer", {"stage": "tafseer"})

    elif node_name == "synthesis":
        synthesis_text = node_state.get("synthesis", "")
        if synthesis_text and "synthesis" not in emitted:
            emitted.add("synthesis")
            yield _sse_event("synthesis_token", {
                "stage": "synthesis_token",
                "token": synthesis_text,
            })

    elif node_name == "quality_review":
        score = node_state.get("quality_score", 0)
        if "quality_done" not in emitted:
            emitted.add("quality_done")
            yield _sse_event("quality_done", {
                "stage": "quality_done",
                "score": score,
            })


def _complete_event(state: dict, session_id: str) -> str:
    """Build the final 'complete' SSE event."""
    return _sse_event("complete", {
        "stage": "complete",
        "session_id": session_id,
        "synthesis": state.get("synthesis", ""),
        "confidence_tier": state.get("confidence_tier", ""),
        "quality_score": state.get("quality_score", 0.0),
        "quality_issues": state.get("quality_issues", []),
        "verses_count": len(state.get("verses", [])),
        "science_findings_count": len(state.get("science_findings", [])),
        "humanities_findings_count": len(state.get("humanities_findings", [])),
        "discovery_id": state.get("discovery_id"),
    })


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
        for d in discoveries:
            for k, v in d.items():
                if hasattr(v, "hex"):
                    d[k] = str(v)
        return {"discoveries": discoveries, "filter": tier}
    return {"discoveries": [], "filter": tier}


def _sse_event(event: str, data: dict) -> str:
    json_data = json.dumps(data, ensure_ascii=False, default=str)
    return f"event: {event}\ndata: {json_data}\n\n"
