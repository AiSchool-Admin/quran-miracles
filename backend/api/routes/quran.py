"""Quran text and tafseer API routes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/surahs")
async def list_surahs() -> dict:
    """List all 114 surahs with metadata."""
    return {"surahs": []}


@router.get("/surahs/{surah_number}/verses")
async def get_verses(surah_number: int) -> dict:
    """Get all verses for a specific surah."""
    return {"surah": surah_number, "verses": []}


@router.get("/verses/{surah_number}/{verse_number}")
async def get_verse(surah_number: int, verse_number: int) -> dict:
    """Get a specific verse with its tafseer entries."""
    return {"surah": surah_number, "verse": verse_number}


@router.get("/search")
async def search_quran(q: str) -> dict:
    """Search Quranic text using hybrid search (BM25 + semantic)."""
    return {"query": q, "results": []}
