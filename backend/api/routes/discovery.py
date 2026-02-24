"""Discovery engine API routes with SSE streaming."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class DiscoveryRequest(BaseModel):
    query: str
    surah: int | None = None
    verse: int | None = None
    analysis_types: list[str] = ["scientific", "linguistic", "numerical"]


@router.post("/explore")
async def explore(request: DiscoveryRequest) -> dict:
    """Launch a discovery exploration via LangGraph."""
    return {"session_id": "", "status": "pending"}


@router.get("/explore/{session_id}/stream")
async def stream_results(session_id: str) -> dict:
    """SSE stream for real-time discovery results."""
    return {"session_id": session_id}


@router.get("/discoveries")
async def list_discoveries(tier: str | None = None) -> dict:
    """List verified discoveries, optionally filtered by tier."""
    return {"discoveries": []}
