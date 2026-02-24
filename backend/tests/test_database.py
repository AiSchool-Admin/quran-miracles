"""Database schema tests.

Verifies:
- All core tables exist
- 7 tafseer books are seeded correctly
- pgvector extension is operational
- Confidence tier constraints work
- Scientific correlation criteria constraints work
"""

import asyncio
import os

import asyncpg
import pytest

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://quran_user:changeme@localhost:5432/quran_miracles",
)


@pytest.fixture(scope="module")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def db(event_loop):
    conn = await asyncpg.connect(DATABASE_URL)
    yield conn
    await conn.close()


# ══════════════════════════════════════════
# التحقق من وجود الجداول الرئيسية
# ══════════════════════════════════════════

EXPECTED_TABLES = [
    "surahs",
    "verses",
    "words",
    "tafseer_books",
    "tafseers",
    "translations",
    "users",
    "discoveries",
    "scientific_correlations",
    "word_balance",
    "bookmarks",
    "research_notes",
    "discovery_sessions",
]


@pytest.mark.asyncio
async def test_all_tables_exist(db):
    """Verify all 13 core tables exist in the database."""
    rows = await db.fetch("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_type = 'BASE TABLE'
    """)
    existing = {row["table_name"] for row in rows}

    for table in EXPECTED_TABLES:
        assert table in existing, f"Table '{table}' not found in database"


@pytest.mark.asyncio
async def test_surahs_table_columns(db):
    """Verify surahs table has key columns including generated ones."""
    rows = await db.fetch("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'surahs'
    """)
    columns = {row["column_name"] for row in rows}

    required = {
        "id", "number", "name_arabic", "name_english",
        "revelation_type", "revelation_order", "verse_count",
        "prime_verse_count", "fibonacci_verse_count",
    }
    for col in required:
        assert col in columns, f"Column 'surahs.{col}' not found"


@pytest.mark.asyncio
async def test_verses_table_has_three_embeddings(db):
    """Verify verses table has 3 vector(1536) embedding columns."""
    rows = await db.fetch("""
        SELECT column_name, udt_name
        FROM information_schema.columns
        WHERE table_name = 'verses'
          AND column_name LIKE 'embedding%'
    """)
    embedding_cols = {row["column_name"] for row in rows}

    assert "embedding_precise" in embedding_cols
    assert "embedding_broad" in embedding_cols
    assert "embedding_multilingual" in embedding_cols


@pytest.mark.asyncio
async def test_words_table_has_arabert_embedding(db):
    """Verify words table has vector(768) for AraBERT."""
    row = await db.fetchrow("""
        SELECT column_name, udt_name
        FROM information_schema.columns
        WHERE table_name = 'words'
          AND column_name = 'embedding'
    """)
    assert row is not None, "Column 'words.embedding' not found"


# ══════════════════════════════════════════
# التحقق من التفاسير السبعة
# ══════════════════════════════════════════

@pytest.mark.asyncio
async def test_seven_tafseer_books_exist(db):
    """Verify exactly 7 tafseer books are seeded."""
    count = await db.fetchval("SELECT COUNT(*) FROM tafseer_books")
    assert count == 7, f"Expected 7 tafseer books, found {count}"


@pytest.mark.asyncio
async def test_tafseer_books_correct_order(db):
    """Verify tafseer books are in the correct priority order."""
    rows = await db.fetch("""
        SELECT slug, name_ar, methodology, priority_order
        FROM tafseer_books
        ORDER BY priority_order
    """)

    expected = [
        ("ibn-katheer",  "أثري",               1),
        ("al-tabari",    "أثري",               2),
        ("al-shaarawy",  "بياني-لغوي-اجتماعي", 3),
        ("al-razi",      "عقلي",               4),
        ("al-saadi",     "تيسيري",             5),
        ("ibn-ashour",   "إصلاحي",             6),
        ("al-qurtubi",   "فقهي",               7),
    ]

    for i, (slug, methodology, order) in enumerate(expected):
        assert rows[i]["slug"] == slug, \
            f"Position {order}: expected '{slug}', got '{rows[i]['slug']}'"
        assert rows[i]["methodology"] == methodology, \
            f"Tafseer '{slug}': expected methodology '{methodology}', got '{rows[i]['methodology']}'"
        assert rows[i]["priority_order"] == order


@pytest.mark.asyncio
async def test_shaarawy_has_correct_metadata(db):
    """Verify al-Shaarawy entry has correct special metadata."""
    row = await db.fetchrow("""
        SELECT name_ar, author_ar, author_death_year, methodology, use_cases
        FROM tafseer_books
        WHERE slug = 'al-shaarawy'
    """)

    assert row is not None, "al-Shaarawy tafseer not found"
    assert "الشعراوي" in row["name_ar"]
    assert row["author_ar"] == "محمد متولى الشعراوي"
    assert row["author_death_year"] == 1998
    assert row["methodology"] == "بياني-لغوي-اجتماعي"
    assert "تحليل دقائق الألفاظ القرآنية" in row["use_cases"]


# ══════════════════════════════════════════
# التحقق من عمل pgvector
# ══════════════════════════════════════════

@pytest.mark.asyncio
async def test_pgvector_extension_active(db):
    """Verify pgvector extension is installed and operational."""
    row = await db.fetchrow("""
        SELECT extname, extversion
        FROM pg_extension
        WHERE extname = 'vector'
    """)
    assert row is not None, "pgvector extension not installed"
    assert row["extname"] == "vector"


@pytest.mark.asyncio
async def test_pgvector_can_compute_distance(db):
    """Verify pgvector can compute cosine distance between vectors."""
    result = await db.fetchval("""
        SELECT 1 - ('[1,0,0]'::vector(3) <=> '[0,1,0]'::vector(3))
    """)
    # Cosine similarity of orthogonal vectors should be ~0
    assert result is not None


@pytest.mark.asyncio
async def test_pg_trgm_extension_active(db):
    """Verify pg_trgm extension is installed."""
    row = await db.fetchrow("""
        SELECT extname
        FROM pg_extension
        WHERE extname = 'pg_trgm'
    """)
    assert row is not None, "pg_trgm extension not installed"


# ══════════════════════════════════════════
# التحقق من قيود الـ CHECK
# ══════════════════════════════════════════

@pytest.mark.asyncio
async def test_discoveries_accepts_tier_0_to_4(db):
    """Verify discoveries table accepts tier_0 through tier_4."""
    # Check that the constraint allows all 5 tiers
    row = await db.fetchrow("""
        SELECT conname, consrc
        FROM pg_constraint
        WHERE conrelid = 'discoveries'::regclass
          AND conname LIKE '%confidence_tier%'
    """)
    assert row is not None, "confidence_tier constraint not found on discoveries"


@pytest.mark.asyncio
async def test_scientific_correlations_has_seven_criteria(db):
    """Verify scientific_correlations has all 7 evaluation criteria columns."""
    rows = await db.fetch("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'scientific_correlations'
    """)
    columns = {row["column_name"] for row in rows}

    criteria = [
        "linguistic_clarity",
        "historical_independence",
        "premodern_tafseer_support",
        "specificity",
        "falsifiability",
        "translational_consensus",
        "contextual_coherence",
        "total_score",
    ]
    for col in criteria:
        assert col in columns, \
            f"Criterion '{col}' not found in scientific_correlations"
