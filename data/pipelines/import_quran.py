"""Quran Data Import Pipeline.

Downloads all 114 surahs (6,236 verses) from Quran Foundation API v4
and saves them as JSON in data/quran/.

For each verse:
  - text_uthmani  (Uthmani script with full diacritics)
  - text_simple   (Imla'i simplified spelling)
  - text_clean    (stripped of all diacritical marks)
  - surah_number, verse_number, juz, page, sajda

Usage:
    python data/pipelines/import_quran.py           # Download & save JSON
    python data/pipelines/import_quran.py --db       # Also insert into PostgreSQL
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path

import httpx

# ── Configuration ──────────────────────────────────────────────────────

API_BASE = "https://api.quran.foundation/api/v4"
TOTAL_SURAHS = 114
EXPECTED_VERSES = 6236
PER_PAGE = 50  # API maximum per request
CONCURRENT_REQUESTS = 5  # Respect API rate limits
RETRY_ATTEMPTS = 3
RETRY_BACKOFF = 2.0  # seconds, doubles each retry

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "quran"

# Arabic diacritical marks (tashkeel) — comprehensive Unicode ranges
_DIACRITICS_RE = re.compile(
    "["
    "\u0610-\u061A"  # Quran annotation signs
    "\u064B-\u065F"  # Arabic tashkeel (fathatan..hamza below)
    "\u0670"         # Superscript alef
    "\u06D6-\u06DC"  # Quran recitation marks
    "\u06DF-\u06E4"  # Arabic small high ligatures
    "\u06E7\u06E8"   # Arabic small high
    "\u06EA-\u06ED"  # Arabic small low
    "\u08D3-\u08E1"  # Extended Arabic diacritics
    "\u08E3-\u08FF"  # Extended Arabic combining marks
    "\uFE70-\uFE7F"  # Arabic presentation forms
    "]"
)


def strip_diacritics(text: str) -> str:
    """Remove all Arabic diacritical marks (tashkeel) from text."""
    return _DIACRITICS_RE.sub("", text)


# ── API Fetchers ───────────────────────────────────────────────────────


async def _request_with_retry(
    client: httpx.AsyncClient,
    url: str,
    params: dict,
) -> dict:
    """GET request with exponential-backoff retry."""
    last_exc: Exception | None = None
    for attempt in range(RETRY_ATTEMPTS):
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            last_exc = exc
            if attempt < RETRY_ATTEMPTS - 1:
                wait = RETRY_BACKOFF * (2 ** attempt)
                await asyncio.sleep(wait)
    raise last_exc  # type: ignore[misc]


async def fetch_chapters_metadata(
    client: httpx.AsyncClient,
) -> dict[int, dict]:
    """Fetch all 114 surahs metadata from /chapters endpoint."""
    data = await _request_with_retry(
        client,
        f"{API_BASE}/chapters",
        {"language": "ar"},
    )
    metadata: dict[int, dict] = {}
    for ch in data["chapters"]:
        metadata[ch["id"]] = {
            "number": ch["id"],
            "name_arabic": ch["name_arabic"],
            "name_english": ch["name_simple"],
            "name_transliteration": ch.get("name_complex", ch["name_simple"]),
            "revelation_type": ch["revelation_place"],
            "revelation_order": ch["revelation_order"],
            "verse_count": ch["verses_count"],
        }
    return metadata


async def fetch_chapter_verses(
    client: httpx.AsyncClient,
    chapter: int,
    semaphore: asyncio.Semaphore,
) -> list[dict]:
    """Fetch all verses for a chapter, handling pagination."""
    verses: list[dict] = []
    page = 1

    async with semaphore:
        while True:
            data = await _request_with_retry(
                client,
                f"{API_BASE}/verses/by_chapter/{chapter}",
                {
                    "language": "ar",
                    "words": "false",
                    "per_page": PER_PAGE,
                    "page": page,
                    "fields": ",".join([
                        "text_uthmani",
                        "text_imlaei",
                        "verse_key",
                        "juz_number",
                        "hizb_number",
                        "rub_el_hizb_number",
                        "page_number",
                        "sajdah_type",
                        "sajdah_number",
                    ]),
                },
            )

            for v in data["verses"]:
                text_uthmani = v.get("text_uthmani", "")
                text_imlaei = v.get("text_imlaei", "")

                verses.append({
                    "surah_number": chapter,
                    "verse_number": v["verse_number"],
                    "verse_key": v.get("verse_key", f"{chapter}:{v['verse_number']}"),
                    "text_uthmani": text_uthmani,
                    "text_simple": text_imlaei,
                    "text_clean": strip_diacritics(text_imlaei),
                    "juz": v.get("juz_number"),
                    "hizb": v.get("hizb_number"),
                    "rub_el_hizb": v.get("rub_el_hizb_number"),
                    "page": v.get("page_number"),
                    "sajda": v.get("sajdah_type") is not None,
                    "sajda_type": v.get("sajdah_type"),
                })

            pagination = data.get("pagination", {})
            if pagination.get("next_page") is None:
                break
            page = pagination["next_page"]
            await asyncio.sleep(0.2)

    return verses


# ── Database Insertion ─────────────────────────────────────────────────


async def insert_into_db(
    surahs_meta: dict[int, dict],
    all_verses: list[dict],
) -> tuple[int, int]:
    """Insert surahs and verses into PostgreSQL via asyncpg.

    Returns (surahs_inserted, verses_inserted).
    """
    import asyncpg

    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://localhost:5432/quran_miracles",
    )
    conn = await asyncpg.connect(database_url)

    try:
        surah_count = 0
        for _num, meta in sorted(surahs_meta.items()):
            rev_type = "makki" if meta["revelation_type"] == "makkah" else "madani"
            await conn.execute(
                """
                INSERT INTO surahs (number, name_arabic, name_english,
                                    name_transliteration, revelation_type,
                                    revelation_order, verse_count)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (number) DO UPDATE SET
                    name_arabic = EXCLUDED.name_arabic,
                    name_english = EXCLUDED.name_english,
                    verse_count = EXCLUDED.verse_count
                """,
                meta["number"],
                meta["name_arabic"],
                meta["name_english"],
                meta["name_transliteration"],
                rev_type,
                meta["revelation_order"],
                meta["verse_count"],
            )
            surah_count += 1

        verse_count = 0
        for v in all_verses:
            sajda_type_db = None
            if v["sajda_type"] == "recommended":
                sajda_type_db = "mustahab"
            elif v["sajda_type"] == "obligatory":
                sajda_type_db = "wajib"

            await conn.execute(
                """
                INSERT INTO verses (surah_number, verse_number, text_uthmani,
                                    text_simple, text_clean, juz, hizb,
                                    rub_el_hizb, page_number, sajda, sajda_type)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (surah_number, verse_number) DO UPDATE SET
                    text_uthmani = EXCLUDED.text_uthmani,
                    text_simple = EXCLUDED.text_simple,
                    text_clean = EXCLUDED.text_clean,
                    juz = EXCLUDED.juz,
                    page_number = EXCLUDED.page_number,
                    sajda = EXCLUDED.sajda,
                    sajda_type = EXCLUDED.sajda_type
                """,
                v["surah_number"],
                v["verse_number"],
                v["text_uthmani"],
                v["text_simple"],
                v["text_clean"],
                v["juz"],
                v.get("hizb"),
                v.get("rub_el_hizb"),
                v["page"],
                v["sajda"],
                sajda_type_db,
            )
            verse_count += 1

        return surah_count, verse_count
    finally:
        await conn.close()


# ── Helpers ────────────────────────────────────────────────────────────


def _save_json(path: Path, data: object) -> None:
    """Write JSON file with Arabic-safe encoding."""
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


# ── Main Pipeline ──────────────────────────────────────────────────────


async def main() -> None:
    """Run the full Quran import pipeline."""
    insert_db = "--db" in sys.argv

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []
    all_verses: list[dict] = []
    surahs_imported = 0
    surahs_meta: dict[int, dict] = {}

    print("=" * 60)
    print("  Quran Data Import Pipeline")
    print("  Source: Quran Foundation API v4")
    print("=" * 60)

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(30.0, connect=10.0),
        follow_redirects=True,
    ) as client:

        # ── Step 1: Fetch surah metadata ──
        print("\n  Fetching surah metadata...")
        try:
            surahs_meta = await fetch_chapters_metadata(client)
            print(f"  Loaded metadata for {len(surahs_meta)} surahs")
        except Exception as exc:
            errors.append(f"Chapter metadata: {exc}")
            print(f"  ERROR fetching metadata: {exc}")

        # ── Step 2: Fetch verses per surah ──
        print("\n  Downloading verses...\n")
        semaphore = asyncio.Semaphore(CONCURRENT_REQUESTS)

        for chapter in range(1, TOTAL_SURAHS + 1):
            name = surahs_meta.get(chapter, {}).get(
                "name_arabic", f"Surah {chapter}"
            )
            try:
                verses = await fetch_chapter_verses(client, chapter, semaphore)
                all_verses.extend(verses)
                surahs_imported += 1

                _save_json(OUTPUT_DIR / f"surah_{chapter:03d}.json", verses)

                print(f"   [{chapter:3d}/114] {name} -- {len(verses)} verses")

            except Exception as exc:
                errors.append(f"Surah {chapter} ({name}): {exc}")
                print(f"   [{chapter:3d}/114] {name} -- ERROR: {exc}")

    # ── Step 3: Save combined file ──
    _save_json(
        OUTPUT_DIR / "quran_complete.json",
        {
            "source": "Quran Foundation API v4",
            "total_surahs": surahs_imported,
            "total_verses": len(all_verses),
            "surahs_metadata": {str(k): v for k, v in surahs_meta.items()},
            "verses": all_verses,
        },
    )

    # ── Step 4: Optionally insert into DB ──
    if insert_db:
        print("\n  Inserting into database...")
        try:
            s_count, v_count = await insert_into_db(surahs_meta, all_verses)
            print(f"  DB: inserted {s_count} surahs + {v_count} verses")
        except Exception as exc:
            errors.append(f"Database: {exc}")
            print(f"  DB ERROR: {exc}")

    # ── Step 5: Summary report ──
    print("\n" + "=" * 60)
    print("  تقرير الاستيراد | Import Report")
    print("=" * 60)
    print(f"  ✅ السور المستوردة: {surahs_imported}/{TOTAL_SURAHS}")
    print(f"  ✅ الآيات: {len(all_verses):,}/{EXPECTED_VERSES:,}")
    print(f"  📁 المخرجات: {OUTPUT_DIR}/")

    if errors:
        print(f"\n  ⚠️ أخطاء في الاستيراد ({len(errors)}):")
        for err in errors:
            print(f"     - {err}")
    else:
        print("\n  ✅ لا أخطاء — الاستيراد مكتمل بنجاح")

    print("=" * 60)

    if surahs_imported < TOTAL_SURAHS:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
