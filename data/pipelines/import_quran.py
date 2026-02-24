"""Quran Data Import Pipeline.

Downloads all 114 surahs (6,236 verses) and saves them as JSON in data/quran/.

Sources (tries in order):
  1. Quran Foundation API v4  (--source=api)
  2. GitHub static JSON       (--source=github, default fallback)

For each verse:
  - text_uthmani  (Uthmani script with full diacritics)
  - text_simple   (simplified spelling with diacritics)
  - text_clean    (stripped of all diacritical marks)
  - surah_number, verse_number, juz, page, sajda

Usage:
    python data/pipelines/import_quran.py                 # Auto (API then GitHub)
    python data/pipelines/import_quran.py --source=github # GitHub only
    python data/pipelines/import_quran.py --source=api    # API only
    python data/pipelines/import_quran.py --db            # Also insert into PostgreSQL
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

TOTAL_SURAHS = 114
EXPECTED_VERSES = 6236
RETRY_ATTEMPTS = 3
RETRY_BACKOFF = 2.0  # seconds, doubles each retry

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "quran"

# Quran Foundation API
QF_API_BASE = "https://api.quran.foundation/api/v4"
QF_PER_PAGE = 50
QF_CONCURRENT = 5

# GitHub static JSON (fawazahmed0/quran-api)
GH_BASE = "https://raw.githubusercontent.com/fawazahmed0/quran-api/1/editions"
GH_UTHMANI = f"{GH_BASE}/ara-quranuthmanihaf.json"
GH_SIMPLE = f"{GH_BASE}/ara-quransimple.json"
GH_CHAPTERS = (
    "https://raw.githubusercontent.com/risan/quran-json/main/data/chapters/en.json"
)

# Sajda verses — chapter:verse mapping (14 sajda positions in the Quran)
_SAJDA_VERSES: dict[tuple[int, int], str] = {
    (7, 206): "obligatory", (13, 15): "recommended", (16, 50): "recommended",
    (17, 109): "recommended", (19, 58): "recommended", (22, 18): "recommended",
    (22, 77): "recommended", (25, 60): "recommended", (27, 26): "recommended",
    (32, 15): "obligatory", (38, 24): "recommended", (41, 38): "recommended",
    (53, 62): "recommended", (84, 21): "recommended", (96, 19): "obligatory",
}

# Juz boundaries — (surah, verse) where each juz starts
_JUZ_STARTS: list[tuple[int, int]] = [
    (1, 1), (2, 142), (2, 253), (3, 93), (4, 24), (4, 148), (5, 83),
    (6, 111), (7, 88), (8, 41), (9, 93), (11, 6), (12, 53), (15, 1),
    (17, 1), (18, 75), (21, 1), (23, 1), (25, 21), (27, 56), (29, 46),
    (33, 31), (36, 28), (39, 32), (41, 47), (46, 1), (51, 31), (58, 1),
    (66, 1), (67, 1),
]

# Page boundaries — surah:verse → page (Madina Mushaf)
# Full mapping loaded from quran-metadata repo or computed at runtime

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


def _get_juz(surah: int, verse: int) -> int:
    """Compute juz number for a given surah:verse."""
    juz = 1
    for i, (s, v) in enumerate(_JUZ_STARTS):
        if (surah, verse) >= (s, v):
            juz = i + 1
        else:
            break
    return juz


# ── HTTP Helper ────────────────────────────────────────────────────────


async def _get_json(
    client: httpx.AsyncClient,
    url: str,
    params: dict | None = None,
) -> dict | list:
    """GET with exponential-backoff retry."""
    last_exc: Exception | None = None
    for attempt in range(RETRY_ATTEMPTS):
        try:
            resp = await client.get(url, params=params or {})
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            last_exc = exc
            if attempt < RETRY_ATTEMPTS - 1:
                wait = RETRY_BACKOFF * (2 ** attempt)
                await asyncio.sleep(wait)
    raise last_exc  # type: ignore[misc]


# ══════════════════════════════════════════════════════════════════════
#  SOURCE 1: Quran Foundation API v4
# ══════════════════════════════════════════════════════════════════════


async def _qf_fetch_chapters(
    client: httpx.AsyncClient,
) -> dict[int, dict]:
    """Fetch surah metadata from Quran Foundation /chapters."""
    data = await _get_json(client, f"{QF_API_BASE}/chapters", {"language": "ar"})
    meta: dict[int, dict] = {}
    for ch in data["chapters"]:  # type: ignore[index]
        meta[ch["id"]] = {
            "number": ch["id"],
            "name_arabic": ch["name_arabic"],
            "name_english": ch["name_simple"],
            "name_transliteration": ch.get("name_complex", ch["name_simple"]),
            "revelation_type": ch["revelation_place"],
            "revelation_order": ch["revelation_order"],
            "verse_count": ch["verses_count"],
        }
    return meta


async def _qf_fetch_verses(
    client: httpx.AsyncClient,
    chapter: int,
    semaphore: asyncio.Semaphore,
) -> list[dict]:
    """Fetch verses for one chapter from Quran Foundation API."""
    verses: list[dict] = []
    page = 1
    async with semaphore:
        while True:
            data = await _get_json(
                client,
                f"{QF_API_BASE}/verses/by_chapter/{chapter}",
                {
                    "language": "ar",
                    "words": "false",
                    "per_page": QF_PER_PAGE,
                    "page": page,
                    "fields": ",".join([
                        "text_uthmani", "text_imlaei", "verse_key",
                        "juz_number", "hizb_number", "rub_el_hizb_number",
                        "page_number", "sajdah_type", "sajdah_number",
                    ]),
                },
            )
            for v in data["verses"]:  # type: ignore[index]
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
            pagination = data.get("pagination", {})  # type: ignore[union-attr]
            if pagination.get("next_page") is None:
                break
            page = pagination["next_page"]
            await asyncio.sleep(0.2)
    return verses


async def import_from_api(
    client: httpx.AsyncClient,
) -> tuple[dict[int, dict], list[dict], list[str]]:
    """Full import via Quran Foundation API. Returns (meta, verses, errors)."""
    errors: list[str] = []
    all_verses: list[dict] = []
    surahs_meta: dict[int, dict] = {}

    print("\n  [API] Fetching surah metadata...")
    surahs_meta = await _qf_fetch_chapters(client)
    print(f"  [API] Loaded {len(surahs_meta)} surahs")

    print("\n  [API] Downloading verses...\n")
    semaphore = asyncio.Semaphore(QF_CONCURRENT)
    for ch in range(1, TOTAL_SURAHS + 1):
        name = surahs_meta.get(ch, {}).get("name_arabic", f"Surah {ch}")
        try:
            verses = await _qf_fetch_verses(client, ch, semaphore)
            all_verses.extend(verses)
            _save_json(OUTPUT_DIR / f"surah_{ch:03d}.json", verses)
            print(f"   [{ch:3d}/114] {name} — {len(verses)} verses")
        except Exception as exc:
            errors.append(f"Surah {ch} ({name}): {exc}")
            print(f"   [{ch:3d}/114] {name} — ERROR: {exc}")

    return surahs_meta, all_verses, errors


# ══════════════════════════════════════════════════════════════════════
#  SOURCE 2: GitHub Static JSON (fallback)
# ══════════════════════════════════════════════════════════════════════


async def import_from_github(
    client: httpx.AsyncClient,
) -> tuple[dict[int, dict], list[dict], list[str]]:
    """Full import via GitHub static JSON. Returns (meta, verses, errors)."""
    errors: list[str] = []
    all_verses: list[dict] = []
    surahs_meta: dict[int, dict] = {}

    # ── 1. Fetch chapter metadata ──
    print("\n  [GitHub] Fetching surah metadata...")
    chapters_raw = await _get_json(client, GH_CHAPTERS)
    for ch in chapters_raw:  # type: ignore[union-attr]
        rev = "makkah" if ch["type"] == "meccan" else "madinah"
        surahs_meta[ch["id"]] = {
            "number": ch["id"],
            "name_arabic": ch["name"],
            "name_english": ch["translation"],
            "name_transliteration": ch["transliteration"],
            "revelation_type": rev,
            "revelation_order": ch["id"],  # placeholder
            "verse_count": ch["total_verses"],
        }
    print(f"  [GitHub] Loaded {len(surahs_meta)} surahs")

    # ── 2. Fetch Uthmani + Simple texts ──
    print("  [GitHub] Downloading Uthmani text...")
    uthmani_data = await _get_json(client, GH_UTHMANI)
    print("  [GitHub] Downloading Simple text...")
    simple_data = await _get_json(client, GH_SIMPLE)

    uthmani_list: list[dict] = uthmani_data["quran"]  # type: ignore[index]
    simple_list: list[dict] = simple_data["quran"]  # type: ignore[index]

    print(f"  [GitHub] Uthmani: {len(uthmani_list)} verses, "
          f"Simple: {len(simple_list)} verses")

    # Build lookup: (chapter, verse) → simple text
    simple_map: dict[tuple[int, int], str] = {}
    for v in simple_list:
        simple_map[(v["chapter"], v["verse"])] = v["text"]

    # ── 3. Build verse records ──
    print("\n  [GitHub] Building verse records...\n")
    current_surah = 0
    surah_verses: list[dict] = []

    for v in uthmani_list:
        ch = v["chapter"]
        vn = v["verse"]
        text_uthmani = v["text"]
        text_simple = simple_map.get((ch, vn), text_uthmani)
        text_clean = strip_diacritics(text_simple)

        sajda_key = (ch, vn)
        sajda_type = _SAJDA_VERSES.get(sajda_key)

        verse_rec = {
            "surah_number": ch,
            "verse_number": vn,
            "verse_key": f"{ch}:{vn}",
            "text_uthmani": text_uthmani,
            "text_simple": text_simple,
            "text_clean": text_clean,
            "juz": _get_juz(ch, vn),
            "hizb": None,
            "rub_el_hizb": None,
            "page": None,
            "sajda": sajda_type is not None,
            "sajda_type": sajda_type,
        }
        all_verses.append(verse_rec)

        # Group by surah for per-file output
        if ch != current_surah:
            if surah_verses and current_surah > 0:
                _save_json(
                    OUTPUT_DIR / f"surah_{current_surah:03d}.json",
                    surah_verses,
                )
                name = surahs_meta.get(current_surah, {}).get(
                    "name_arabic", f"Surah {current_surah}"
                )
                print(f"   [{current_surah:3d}/114] {name}"
                      f" — {len(surah_verses)} verses")
            current_surah = ch
            surah_verses = []
        surah_verses.append(verse_rec)

    # Save last surah
    if surah_verses and current_surah > 0:
        _save_json(
            OUTPUT_DIR / f"surah_{current_surah:03d}.json",
            surah_verses,
        )
        name = surahs_meta.get(current_surah, {}).get(
            "name_arabic", f"Surah {current_surah}"
        )
        print(f"   [{current_surah:3d}/114] {name}"
              f" — {len(surah_verses)} verses")

    return surahs_meta, all_verses, errors


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


def _parse_source_arg() -> str:
    """Parse --source=api|github from argv. Default: auto."""
    for arg in sys.argv[1:]:
        if arg.startswith("--source="):
            return arg.split("=", 1)[1]
    return "auto"


# ── Main Pipeline ──────────────────────────────────────────────────────


async def main() -> None:
    """Run the full Quran import pipeline."""
    insert_db = "--db" in sys.argv
    source = _parse_source_arg()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  Quran Data Import Pipeline")
    print("=" * 60)

    surahs_meta: dict[int, dict] = {}
    all_verses: list[dict] = []
    errors: list[str] = []

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(30.0, connect=10.0),
        follow_redirects=True,
    ) as client:

        if source == "api":
            print("  Source: Quran Foundation API v4")
            surahs_meta, all_verses, errors = await import_from_api(client)

        elif source == "github":
            print("  Source: GitHub (fawazahmed0/quran-api)")
            surahs_meta, all_verses, errors = await import_from_github(client)

        else:  # auto — try API first, fallback to GitHub
            print("  Source: Auto (API → GitHub fallback)")
            try:
                # Quick probe to see if API is reachable
                probe = await client.get(
                    f"{QF_API_BASE}/chapters",
                    params={"language": "ar"},
                )
                probe.raise_for_status()
                print("  API reachable — using Quran Foundation API v4")
                surahs_meta, all_verses, errors = await import_from_api(client)
            except (httpx.HTTPStatusError, httpx.TransportError) as exc:
                print(f"  API unavailable ({exc}) — falling back to GitHub")
                surahs_meta, all_verses, errors = await import_from_github(
                    client,
                )

    # Count successfully imported surahs
    imported_surahs: set[int] = set()
    for v in all_verses:
        imported_surahs.add(v["surah_number"])
    surahs_imported = len(imported_surahs)

    # ── Save combined file ──
    _save_json(
        OUTPUT_DIR / "quran_complete.json",
        {
            "source": source,
            "total_surahs": surahs_imported,
            "total_verses": len(all_verses),
            "surahs_metadata": {str(k): v for k, v in surahs_meta.items()},
            "verses": all_verses,
        },
    )

    # ── Optionally insert into DB ──
    if insert_db:
        print("\n  Inserting into database...")
        try:
            s_count, v_count = await insert_into_db(surahs_meta, all_verses)
            print(f"  DB: inserted {s_count} surahs + {v_count} verses")
        except Exception as exc:
            errors.append(f"Database: {exc}")
            print(f"  DB ERROR: {exc}")

    # ── Summary report ──
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
