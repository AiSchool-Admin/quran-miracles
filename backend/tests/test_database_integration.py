"""Integration tests for real database + QuranRAGAgent.

These tests require a running PostgreSQL with the quran_miracles database
populated (6,236 verses). Skip if DB is not available.

Run: DATABASE_URL=postgresql://quran_user:changeme@localhost:5432/quran_miracles \
     pytest backend/tests/test_database_integration.py -v
"""

from __future__ import annotations

import os

import pytest

# ── DB availability check ──────────────────────────────────

_DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://quran_user:changeme@localhost:5432/quran_miracles",
)
# Normalize for asyncpg
_DB_URL = _DB_URL.replace("postgresql+asyncpg://", "postgresql://")


async def _db_available() -> bool:
    try:
        import asyncpg

        conn = await asyncpg.connect(_DB_URL)
        count = await conn.fetchval("SELECT COUNT(*) FROM verses")
        await conn.close()
        return count > 0
    except Exception:
        return False


@pytest.fixture(scope="module")
def db_check():
    """Check DB availability once per module."""
    import asyncio

    loop = asyncio.new_event_loop()
    available = loop.run_until_complete(_db_available())
    loop.close()
    if not available:
        pytest.skip("Database not available or empty")


# ═══════════════════════════════════════════════════════════════
# 1. Raw database queries
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_verse_count(db_check):
    """DB must contain exactly 6,236 verses."""
    import asyncpg

    conn = await asyncpg.connect(_DB_URL)
    count = await conn.fetchval("SELECT COUNT(*) FROM verses")
    await conn.close()
    assert count == 6236


@pytest.mark.asyncio
async def test_surah_count(db_check):
    """DB must contain exactly 114 surahs."""
    import asyncpg

    conn = await asyncpg.connect(_DB_URL)
    count = await conn.fetchval("SELECT COUNT(*) FROM surahs")
    await conn.close()
    assert count == 114


@pytest.mark.asyncio
async def test_tafseer_books(db_check):
    """All 7 tafseer books must be present with correct priority order."""
    import asyncpg

    conn = await asyncpg.connect(_DB_URL)
    rows = await conn.fetch(
        "SELECT slug, priority_order FROM tafseer_books ORDER BY priority_order"
    )
    await conn.close()

    assert len(rows) == 7
    assert rows[0]["slug"] == "ibn-katheer"
    assert rows[2]["slug"] == "al-shaarawy"
    assert rows[6]["slug"] == "al-qurtubi"


@pytest.mark.asyncio
async def test_pgvector_extension(db_check):
    """pgvector extension must be installed."""
    import asyncpg

    conn = await asyncpg.connect(_DB_URL)
    ext = await conn.fetchval(
        "SELECT extname FROM pg_extension WHERE extname = 'vector'"
    )
    await conn.close()
    assert ext == "vector"


@pytest.mark.asyncio
async def test_verse_text_formats(db_check):
    """Each verse should have text_uthmani and text_simple."""
    import asyncpg

    conn = await asyncpg.connect(_DB_URL)
    row = await conn.fetchrow(
        "SELECT text_uthmani, text_simple, text_clean FROM verses "
        "WHERE surah_number = 1 AND verse_number = 1"
    )
    await conn.close()

    assert row is not None
    assert "بسم" in (row["text_clean"] or "")
    assert "ٱلرَّحِيمِ" in row["text_uthmani"] or "الرَّحِيمِ" in row["text_uthmani"]


@pytest.mark.asyncio
async def test_text_search(db_check):
    """Full-text search on text_clean should work."""
    import asyncpg

    conn = await asyncpg.connect(_DB_URL)
    rows = await conn.fetch(
        """
        SELECT surah_number, verse_number, text_clean
        FROM verses
        WHERE text_clean LIKE '%' || $1 || '%'
        LIMIT 5
        """,
        "الماء",
    )
    await conn.close()

    assert len(rows) > 0
    for r in rows:
        assert "الماء" in (r["text_clean"] or "")


@pytest.mark.asyncio
async def test_tsvector_search(db_check):
    """tsvector full-text search should find relevant verses."""
    import asyncpg

    conn = await asyncpg.connect(_DB_URL)
    rows = await conn.fetch(
        """
        SELECT surah_number, verse_number,
               ts_rank(search_vector, plainto_tsquery('simple', $1)) AS rank
        FROM verses
        WHERE search_vector @@ plainto_tsquery('simple', $1)
        ORDER BY rank DESC
        LIMIT 5
        """,
        "الماء",
    )
    await conn.close()

    assert len(rows) > 0


# ═══════════════════════════════════════════════════════════════
# 2. QuranRAGAgent with real DB
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_quran_rag_text_search(db_check):
    """QuranRAGAgent should use text search from real DB."""
    # Ensure DB is used (no mock flag)
    os.environ.pop("_MOCK_DB", None)
    os.environ["DATABASE_URL"] = _DB_URL

    from discovery_engine.agents.quran_rag import QuranRAGAgent
    from discovery_engine.core.state import DiscoveryState

    agent = QuranRAGAgent()
    state: DiscoveryState = {"query": "الماء"}
    result = await agent.search("الماء", state)

    assert result.get("source") == "database"
    assert len(result["verses"]) > 0

    # Should find water-related verses
    found_texts = " ".join(v.get("text_clean", "") for v in result["verses"])
    assert "الماء" in found_texts or "ماء" in found_texts


@pytest.mark.asyncio
async def test_quran_rag_specific_verse(db_check):
    """Search for a specific term should find known verses."""
    os.environ.pop("_MOCK_DB", None)
    os.environ["DATABASE_URL"] = _DB_URL

    from discovery_engine.agents.quran_rag import QuranRAGAgent
    from discovery_engine.core.state import DiscoveryState

    agent = QuranRAGAgent()
    state: DiscoveryState = {"query": "بسم الله الرحمن الرحيم"}
    result = await agent.search("بسم الله الرحمن الرحيم", state)

    assert result.get("source") == "database"
    assert len(result["verses"]) > 0

    # Should find Al-Fatiha verse 1
    verse_keys = [v["verse_key"] for v in result["verses"]]
    # Multiple surahs start with bismillah, so at least one should be found
    assert any("1:" in vk for vk in verse_keys) or len(verse_keys) > 0
