"""Quran text and tafseer API routes.

Endpoints:
  GET /surahs                         — all 114 surahs
  GET /surahs/{number}                — single surah metadata
  GET /surahs/{number}/verses         — all verses in a surah
  GET /verses/{surah}/{verse}         — single verse + tafseers
  GET /search?q=...                   — hybrid text search
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter()


def _get_db(request: Request):
    """Extract DatabaseService from app state or raise 503."""
    db = getattr(request.app.state, "db", None)
    if db is None:
        raise HTTPException(
            status_code=503,
            detail="قاعدة البيانات غير متوفرة حالياً",
        )
    return db


# ── Surahs ─────────────────────────────────────────────────


@router.get("/surahs")
async def list_surahs(request: Request) -> dict:
    """List all 114 surahs with metadata."""
    db = _get_db(request)
    surahs = await db.list_surahs()
    return {"surahs": surahs, "total": len(surahs)}


@router.get("/surahs/{surah_number}")
async def get_surah(surah_number: int, request: Request) -> dict:
    """Get a single surah's metadata."""
    db = _get_db(request)

    if not 1 <= surah_number <= 114:
        raise HTTPException(400, "رقم السورة يجب أن يكون بين 1 و 114")

    surah = await db.get_surah(surah_number)
    if surah is None:
        raise HTTPException(404, f"السورة رقم {surah_number} غير موجودة")
    return {"surah": surah}


# ── Verses ─────────────────────────────────────────────────


@router.get("/surahs/{surah_number}/verses")
async def get_verses(surah_number: int, request: Request) -> dict:
    """Get all verses for a specific surah."""
    db = _get_db(request)

    if not 1 <= surah_number <= 114:
        raise HTTPException(400, "رقم السورة يجب أن يكون بين 1 و 114")

    verses = await db.get_verses_by_surah(surah_number)
    if not verses:
        raise HTTPException(404, f"السورة رقم {surah_number} غير موجودة")

    return {
        "surah": surah_number,
        "verses": verses,
        "total": len(verses),
    }


@router.get("/verses/{surah_number}/{verse_number}")
async def get_verse(
    surah_number: int, verse_number: int, request: Request
) -> dict:
    """Get a specific verse with its tafseer entries."""
    db = _get_db(request)

    verse = await db.get_verse_detail(surah_number, verse_number)
    if verse is None:
        raise HTTPException(
            404, f"الآية {surah_number}:{verse_number} غير موجودة"
        )

    # Fetch tafseers using the verse's primary key
    tafseers = await db.get_tafseers_for_verse(verse["id"])

    return {
        "verse": verse,
        "tafseers": tafseers,
    }


# ── Search ─────────────────────────────────────────────────


@router.get("/search")
async def search_quran(
    request: Request,
    q: str = Query(..., min_length=2, description="نص البحث"),
    limit: int = Query(20, ge=1, le=100),
) -> dict:
    """Search Quranic text using hybrid search (tsvector + LIKE fallback)."""
    db = _get_db(request)

    results = await db.search_verses_by_text(q, limit=limit)

    return {
        "query": q,
        "results": results,
        "total": len(results),
    }
