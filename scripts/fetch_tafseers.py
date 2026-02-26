#!/usr/bin/env python3
"""جلب التفاسير السبعة من quran.com API v4.

المصادر المتاحة على quran.com:
- ابن كثير (العربي)     → resource_id: 169
- الطبري                → resource_id: 15
- القرطبي               → resource_id: 90
- السعدي (الميسر)       → resource_id: 170
- البغوي (بديل الرازي)  → resource_id: 94
- ابن عاشور             → resource_id: غير متاح مباشرة

بديل: quran-tafseer API (quran-tafseer.web.app):
- ابن كثير   → tafseer_id: 1
- الطبري     → tafseer_id: 2
- القرطبي    → tafseer_id: 3
- المحرر الوجيز (ابن عطية) → tafseer_id: 4
- البغوي     → tafseer_id: 5
- السعدي     → tafseer_id: 6
- الوسيط     → tafseer_id: 7

الاستخدام:
    python scripts/fetch_tafseers.py
    python scripts/fetch_tafseers.py --source quran-tafseer
    python scripts/fetch_tafseers.py --source quran-com
    python scripts/fetch_tafseers.py --surah 1 --surah 2  # سور محددة
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

import httpx

# ── المسارات ──────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "tafseers"


# ── تعريف التفاسير المتاحة ──────────────────────────

# quran-tafseer.web.app API
QURAN_TAFSEER_API = "https://quran-tafseer.web.app/tafseer"
QURAN_TAFSEER_BOOKS = {
    "ibn-katheer": {"api_id": 1, "name_ar": "تفسير ابن كثير", "priority": 1},
    "al-tabari": {"api_id": 2, "name_ar": "جامع البيان (الطبري)", "priority": 2},
    "al-qurtubi": {"api_id": 3, "name_ar": "الجامع لأحكام القرآن", "priority": 6},
    "al-baghawi": {"api_id": 5, "name_ar": "تفسير البغوي", "priority": 7},
    "al-saadi": {"api_id": 6, "name_ar": "تفسير السعدي", "priority": 4},
    "al-waseet": {"api_id": 7, "name_ar": "التفسير الوسيط", "priority": 8},
}

# quran.com API v4
QURAN_COM_API = "https://api.quran.com/api/v4"
QURAN_COM_BOOKS = {
    "ibn-katheer": {"resource_id": 169, "name_ar": "تفسير ابن كثير", "priority": 1},
    "al-tabari": {"resource_id": 15, "name_ar": "جامع البيان (الطبري)", "priority": 2},
    "al-qurtubi": {"resource_id": 90, "name_ar": "الجامع لأحكام القرآن", "priority": 6},
    "al-saadi": {"resource_id": 170, "name_ar": "تفسير السعدي", "priority": 4},
    "al-baghawi": {"resource_id": 94, "name_ar": "تفسير البغوي", "priority": 7},
}

# عدد آيات كل سورة (114 سورة)
SURAH_VERSE_COUNTS = [
    7, 286, 200, 176, 120, 165, 206, 75, 129, 109,
    123, 111, 43, 52, 99, 128, 111, 110, 98, 135,
    112, 78, 118, 64, 77, 227, 93, 88, 69, 60,
    34, 30, 73, 54, 45, 83, 182, 88, 75, 85,
    54, 53, 89, 59, 37, 35, 38, 29, 18, 45,
    60, 49, 62, 55, 78, 96, 29, 22, 24, 13,
    14, 11, 11, 18, 12, 12, 30, 52, 52, 44,
    28, 28, 20, 56, 40, 31, 50, 40, 46, 42,
    29, 19, 36, 25, 22, 17, 19, 26, 30, 20,
    15, 21, 11, 8, 8, 19, 5, 8, 8, 11,
    11, 8, 3, 9, 5, 4, 7, 3, 6, 3,
    5, 4, 5, 6,
]


async def fetch_from_quran_tafseer(
    client: httpx.AsyncClient,
    book_slug: str,
    book_info: dict,
    surahs: list[int] | None = None,
) -> dict:
    """جلب تفسير كامل من quran-tafseer API.

    API: GET /tafseer/{tafseer_id}/{surah_number}/{verse_number}
    """
    tafseer_id = book_info["api_id"]
    all_entries = {}
    target_surahs = surahs or list(range(1, 115))

    for surah_num in target_surahs:
        verse_count = SURAH_VERSE_COUNTS[surah_num - 1]
        surah_entries = []

        for verse_num in range(1, verse_count + 1):
            url = f"{QURAN_TAFSEER_API}/{tafseer_id}/{surah_num}/{verse_num}"
            for attempt in range(4):
                try:
                    resp = await client.get(url, timeout=15)
                    if resp.status_code == 200:
                        data = resp.json()
                        text = data.get("text", "")
                        if text:
                            surah_entries.append({
                                "surah_number": surah_num,
                                "verse_number": verse_num,
                                "verse_key": f"{surah_num}:{verse_num}",
                                "text": text.strip(),
                            })
                        break
                    elif resp.status_code == 429:
                        wait = 2 ** (attempt + 1)
                        print(f"  ⏳ Rate limit — waiting {wait}s...")
                        await asyncio.sleep(wait)
                    else:
                        break
                except httpx.TimeoutException:
                    if attempt < 3:
                        await asyncio.sleep(2 ** attempt)
                    continue
                except Exception as e:
                    print(f"  ⚠️ Error {surah_num}:{verse_num}: {e}")
                    break

            # Rate limiting
            await asyncio.sleep(0.1)

        all_entries[str(surah_num)] = surah_entries
        done = len(surah_entries)
        total = verse_count
        print(f"  ✅ سورة {surah_num}: {done}/{total} آية")

    return {
        "book_slug": book_slug,
        "book_name": book_info["name_ar"],
        "priority": book_info["priority"],
        "source": "quran-tafseer.web.app",
        "surahs": all_entries,
    }


async def fetch_from_quran_com(
    client: httpx.AsyncClient,
    book_slug: str,
    book_info: dict,
    surahs: list[int] | None = None,
) -> dict:
    """جلب تفسير من quran.com API v4.

    API: GET /quran/tafsirs/{resource_id}?chapter_number={surah}
    """
    resource_id = book_info["resource_id"]
    all_entries = {}
    target_surahs = surahs or list(range(1, 115))

    for surah_num in target_surahs:
        url = f"{QURAN_COM_API}/quran/tafsirs/{resource_id}"
        params = {"chapter_number": surah_num}

        for attempt in range(4):
            try:
                resp = await client.get(url, params=params, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    tafsirs = data.get("tafsirs", [])
                    surah_entries = []
                    for t in tafsirs:
                        verse_key = t.get("verse_key", "")
                        text = t.get("text", "")
                        if verse_key and text:
                            parts = verse_key.split(":")
                            surah_entries.append({
                                "surah_number": int(parts[0]),
                                "verse_number": int(parts[1]),
                                "verse_key": verse_key,
                                "text": _clean_html(text),
                            })
                    all_entries[str(surah_num)] = surah_entries
                    print(f"  ✅ سورة {surah_num}: {len(surah_entries)} آية")
                    break
                elif resp.status_code == 429:
                    wait = 2 ** (attempt + 1)
                    print(f"  ⏳ Rate limit — waiting {wait}s...")
                    await asyncio.sleep(wait)
                else:
                    print(f"  ⚠️ HTTP {resp.status_code} for surah {surah_num}")
                    all_entries[str(surah_num)] = []
                    break
            except httpx.TimeoutException:
                if attempt < 3:
                    await asyncio.sleep(2 ** attempt)
                continue

        await asyncio.sleep(0.5)  # Rate limiting

    return {
        "book_slug": book_slug,
        "book_name": book_info["name_ar"],
        "priority": book_info["priority"],
        "source": "quran.com",
        "surahs": all_entries,
    }


def _clean_html(text: str) -> str:
    """إزالة HTML tags من النص."""
    import re
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


async def main():
    parser = argparse.ArgumentParser(
        description="جلب التفاسير السبعة من APIs مفتوحة"
    )
    parser.add_argument(
        "--source",
        choices=["quran-tafseer", "quran-com", "both"],
        default="quran-tafseer",
        help="مصدر البيانات (default: quran-tafseer)",
    )
    parser.add_argument(
        "--surah",
        type=int,
        action="append",
        help="سور محددة (يمكن تكرارها)",
    )
    parser.add_argument(
        "--books",
        nargs="*",
        help="تفاسير محددة (slugs)",
    )
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    surahs = args.surah  # None = all

    async with httpx.AsyncClient(
        headers={"Accept": "application/json"},
        follow_redirects=True,
    ) as client:

        if args.source in ("quran-tafseer", "both"):
            books = QURAN_TAFSEER_BOOKS
            if args.books:
                books = {k: v for k, v in books.items() if k in args.books}

            for slug, info in books.items():
                print(f"\n📖 جلب {info['name_ar']} من quran-tafseer API...")
                start = time.time()
                result = await fetch_from_quran_tafseer(
                    client, slug, info, surahs
                )
                elapsed = time.time() - start

                out_path = DATA_DIR / f"{slug}.json"
                out_path.write_text(
                    json.dumps(result, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                total_verses = sum(
                    len(entries) for entries in result["surahs"].values()
                )
                print(
                    f"  💾 حُفظ: {out_path.name} "
                    f"({total_verses} آية — {elapsed:.1f}s)"
                )

        if args.source in ("quran-com", "both"):
            books = QURAN_COM_BOOKS
            if args.books:
                books = {k: v for k, v in books.items() if k in args.books}

            for slug, info in books.items():
                print(f"\n📖 جلب {info['name_ar']} من quran.com API...")
                start = time.time()
                result = await fetch_from_quran_com(
                    client, slug, info, surahs
                )
                elapsed = time.time() - start

                out_path = DATA_DIR / f"{slug}_qurancom.json"
                out_path.write_text(
                    json.dumps(result, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                total_verses = sum(
                    len(entries) for entries in result["surahs"].values()
                )
                print(
                    f"  💾 حُفظ: {out_path.name} "
                    f"({total_verses} آية — {elapsed:.1f}s)"
                )

    print("\n✅ اكتمل جلب التفاسير!")


if __name__ == "__main__":
    asyncio.run(main())
