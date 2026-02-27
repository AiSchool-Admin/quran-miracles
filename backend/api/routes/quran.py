"""Quran text and tafseer API routes.

Strategy for each endpoint:
  1. Try the local PostgreSQL database (fast, full features)
  2. Fall back to alquran.cloud CDN (basic, always available)

Endpoints:
  GET /surahs                         — all 114 surahs
  GET /surahs/{number}                — single surah metadata
  GET /surahs/{number}/verses         — all verses in a surah
  GET /verses/{surah}/{verse}         — single verse + tafseers
  GET /search?q=...                   — hybrid text search
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Query, Request

router = APIRouter()

_CDN_TIMEOUT = 10.0


def _get_db(request: Request):
    """Extract DatabaseService from app state — returns None if unavailable."""
    return getattr(request.app.state, "db", None)


# ── Surahs ─────────────────────────────────────────────────


@router.get("/surahs")
async def list_surahs(request: Request) -> dict:
    """List all 114 surahs with metadata."""
    db = _get_db(request)

    if db is not None:
        try:
            surahs = await db.list_surahs()
            if surahs:
                return {"surahs": surahs, "total": len(surahs)}
        except Exception:
            pass

    # Fallback: alquran.cloud
    async with httpx.AsyncClient(timeout=_CDN_TIMEOUT) as client:
        res = await client.get("https://api.alquran.cloud/v1/surah")
        if res.status_code != 200:
            raise HTTPException(502, "فشل الاتصال بمصادر البيانات")
        data = res.json().get("data", [])

    surahs = [
        {
            "number": s["number"],
            "name_arabic": s["name"],
            "name_english": s.get("englishName", ""),
            "name_transliteration": s.get("englishNameTranslation", ""),
            "revelation_type": s.get("revelationType", "").lower(),
            "verse_count": s.get("numberOfAyahs", 0),
        }
        for s in data
    ]
    return {"surahs": surahs, "total": len(surahs), "source": "alquran.cloud"}


@router.get("/surahs/{surah_number}")
async def get_surah(surah_number: int, request: Request) -> dict:
    """Get a single surah's metadata."""
    if not 1 <= surah_number <= 114:
        raise HTTPException(400, "رقم السورة يجب أن يكون بين 1 و 114")

    db = _get_db(request)

    if db is not None:
        try:
            surah = await db.get_surah(surah_number)
            if surah is not None:
                return {"surah": surah}
        except Exception:
            pass

    # Fallback
    async with httpx.AsyncClient(timeout=_CDN_TIMEOUT) as client:
        res = await client.get(f"https://api.alquran.cloud/v1/surah/{surah_number}")
        if res.status_code != 200:
            raise HTTPException(404, f"السورة رقم {surah_number} غير موجودة")
        s = res.json().get("data", {})

    return {
        "surah": {
            "number": s["number"],
            "name_arabic": s["name"],
            "name_english": s.get("englishName", ""),
            "name_transliteration": s.get("englishNameTranslation", ""),
            "revelation_type": s.get("revelationType", "").lower(),
            "verse_count": s.get("numberOfAyahs", 0),
        },
        "source": "alquran.cloud",
    }


# ── Verses ─────────────────────────────────────────────────


@router.get("/surahs/{surah_number}/verses")
async def get_verses(surah_number: int, request: Request) -> dict:
    """Get all verses for a specific surah."""
    if not 1 <= surah_number <= 114:
        raise HTTPException(400, "رقم السورة يجب أن يكون بين 1 و 114")

    db = _get_db(request)

    if db is not None:
        try:
            verses = await db.get_verses_by_surah(surah_number)
            if verses:
                return {"surah": surah_number, "verses": verses, "total": len(verses)}
        except Exception:
            pass

    # Fallback: alquran.cloud — quran-uthmani edition
    async with httpx.AsyncClient(timeout=_CDN_TIMEOUT) as client:
        res = await client.get(
            f"https://api.alquran.cloud/v1/surah/{surah_number}/quran-uthmani"
        )
        if res.status_code != 200:
            raise HTTPException(404, f"السورة رقم {surah_number} غير موجودة")
        data = res.json().get("data", {})

    ayahs = data.get("ayahs", [])
    verses = [
        {
            "id": a["number"],
            "surah_number": surah_number,
            "verse_number": a["numberInSurah"],
            "text_uthmani": a["text"],
            "text_simple": a["text"],
            "text_clean": "",
            "juz": a.get("juz", 0),
            "page_number": a.get("page", 0),
        }
        for a in ayahs
    ]
    return {
        "surah": surah_number,
        "verses": verses,
        "total": len(verses),
        "source": "alquran.cloud",
    }


@router.get("/verses/{surah_number}/{verse_number}")
async def get_verse(
    surah_number: int, verse_number: int, request: Request
) -> dict:
    """Get a specific verse with its tafseer entries."""
    db = _get_db(request)

    if db is not None:
        try:
            verse = await db.get_verse_detail(surah_number, verse_number)
            if verse is not None:
                tafseers = await db.get_tafseers_for_verse(verse["id"])
                return {"verse": verse, "tafseers": tafseers}
        except Exception:
            pass

    # Fallback: alquran.cloud
    async with httpx.AsyncClient(timeout=_CDN_TIMEOUT) as client:
        res = await client.get(
            f"https://api.alquran.cloud/v1/ayah/{surah_number}:{verse_number}/quran-uthmani"
        )
        if res.status_code != 200:
            raise HTTPException(
                404, f"الآية {surah_number}:{verse_number} غير موجودة"
            )
        a = res.json().get("data", {})

    return {
        "verse": {
            "id": a.get("number", 0),
            "surah_number": surah_number,
            "verse_number": verse_number,
            "text_uthmani": a.get("text", ""),
            "text_simple": a.get("text", ""),
            "text_clean": "",
            "juz": a.get("juz", 0),
            "page_number": a.get("page", 0),
        },
        "tafseers": [],
        "source": "alquran.cloud",
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

    if db is not None:
        try:
            results = await db.search_verses_by_text(q, limit=limit)
            if results:
                return {"query": q, "results": results, "total": len(results)}
        except Exception:
            pass

    # Fallback: alquran.cloud keyword search
    async with httpx.AsyncClient(timeout=_CDN_TIMEOUT) as client:
        res = await client.get(
            f"https://api.alquran.cloud/v1/search/{q}/all/quran-uthmani"
        )
        if res.status_code != 200:
            return {"query": q, "results": [], "total": 0}
        data = res.json().get("data", {})

    matches = data.get("matches", [])[:limit]
    results = [
        {
            "id": m["number"],
            "surah_number": m["surah"]["number"],
            "verse_number": m["numberInSurah"],
            "verse_key": f"{m['surah']['number']}:{m['numberInSurah']}",
            "text_uthmani": m["text"],
            "text_simple": m["text"],
            "text_clean": "",
            "similarity": 0.9,
        }
        for m in matches
    ]
    return {
        "query": q,
        "results": results,
        "total": len(results),
        "source": "alquran.cloud",
    }
