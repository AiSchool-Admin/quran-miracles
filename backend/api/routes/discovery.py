"""Discovery engine API routes with SSE streaming."""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Literal

from fastapi import APIRouter
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


@router.post("/stream")
async def stream_discovery(request: DiscoveryRequest) -> StreamingResponse:
    """Launch a discovery exploration and stream results via SSE.

    SSE stages:
      1. route_query    — query routed
      2. quran_rag      — verses retrieved
      3. linguistic     — morphological analysis done
      4. science        — scientific correlations found
      5. tafseer        — tafseer comparison done
      6. humanities     — humanities connections found
      7. synthesis      — synthesis generated
      8. quality_review — quality reviewed
      9. complete       — final results
    """
    session_id = str(uuid.uuid4())

    initial_state: DiscoveryState = {
        "query": request.query,
        "disciplines": request.disciplines,
        "mode": request.mode,
        "iteration_count": 0,
        "streaming_updates": [],
    }

    async def event_generator():
        # Send session start
        yield _sse_event("session_start", {"session_id": session_id})

        try:
            graph = build_discovery_graph()
            config = {"configurable": {"thread_id": session_id}}

            # Track which stages we've sent
            sent_stages: set[str] = set()

            # Run graph with streaming if available
            if hasattr(graph, "astream"):
                async for chunk in graph.astream(initial_state, config=config):
                    # Each chunk is a dict of node_name → partial state
                    for _node_name, node_state in chunk.items():
                        updates = node_state.get("streaming_updates", [])
                        for update in updates:
                            stage = update.get("stage", "")
                            if stage and stage not in sent_stages:
                                sent_stages.add(stage)
                                yield _sse_event(stage, update)
                                await asyncio.sleep(0.01)

                # Get final state
                final_state = await graph.aget_state(config)
                state_values = (
                    final_state.values
                    if hasattr(final_state, "values")
                    else final_state
                )
            else:
                # Fallback: run ainvoke and send updates from result
                state_values = await graph.ainvoke(initial_state, config=config)

                for update in state_values.get("streaming_updates", []):
                    stage = update.get("stage", "")
                    if stage:
                        yield _sse_event(stage, update)
                        await asyncio.sleep(0.01)

            # Send final result
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
async def explore(request: DiscoveryRequest) -> DiscoveryResponse:
    """Non-streaming discovery exploration (returns full result)."""
    session_id = str(uuid.uuid4())

    initial_state: DiscoveryState = {
        "query": request.query,
        "disciplines": request.disciplines,
        "mode": request.mode,
        "iteration_count": 0,
        "streaming_updates": [],
    }

    graph = build_discovery_graph()
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
    )


@router.get("/discoveries")
async def list_discoveries(tier: str | None = None) -> dict:
    """List verified discoveries, optionally filtered by tier."""
    # TODO: query from database
    return {"discoveries": [], "filter": tier}


def _sse_event(event: str, data: dict) -> str:
    """Format a Server-Sent Event."""
    json_data = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {json_data}\n\n"
