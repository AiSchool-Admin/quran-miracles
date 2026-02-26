#!/usr/bin/env python3
"""تحميل التفاسير من ملفات JSON إلى قاعدة البيانات PostgreSQL.

يقرأ ملفات JSON من data/tafseers/ ويدخلها في جداول:
  - tafseer_books (المراجع)
  - tafseers (النصوص مرتبطة بالآيات)

الاستخدام:
    python scripts/load_tafseers_to_db.py
    python scripts/load_tafseers_to_db.py --db-url postgresql://user:pass@host/db
    python scripts/load_tafseers_to_db.py --dry-run  # عرض بدون تنفيذ
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

import asyncpg

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "tafseers"

# تعريف الكتب السبعة المعتمدة
TAFSEER_BOOKS = [
    {
        "slug": "ibn-katheer",
        "name_ar": "تفسير ابن كثير",
        "name_en": "Tafsir Ibn Kathir",
        "author_ar": "إسماعيل بن كثير",
        "author_death_year": 774,
        "methodology": "أثري",
        "priority_order": 1,
    },
    {
        "slug": "al-tabari",
        "name_ar": "جامع البيان (الطبري)",
        "name_en": "Jami al-Bayan (al-Tabari)",
        "author_ar": "ابن جرير الطبري",
        "author_death_year": 310,
        "methodology": "أثري",
        "priority_order": 2,
    },
    {
        "slug": "al-shaarawy",
        "name_ar": "تفسير الشعراوي — خواطر حول القرآن الكريم",
        "name_en": "Tafsir al-Shaarawy",
        "author_ar": "محمد متولى الشعراوي",
        "author_death_year": 1998,
        "methodology": "بياني-لغوي-اجتماعي",
        "priority_order": 3,
    },
    {
        "slug": "al-razi",
        "name_ar": "مفاتيح الغيب (الرازي)",
        "name_en": "Mafatih al-Ghayb (al-Razi)",
        "author_ar": "فخر الدين الرازي",
        "author_death_year": 606,
        "methodology": "عقلي",
        "priority_order": 4,
    },
    {
        "slug": "al-saadi",
        "name_ar": "تفسير السعدي",
        "name_en": "Tafsir al-Saadi",
        "author_ar": "عبد الرحمن السعدي",
        "author_death_year": 1376,
        "methodology": "تيسيري",
        "priority_order": 5,
    },
    {
        "slug": "ibn-ashour",
        "name_ar": "التحرير والتنوير",
        "name_en": "al-Tahrir wal-Tanwir",
        "author_ar": "ابن عاشور",
        "author_death_year": 1393,
        "methodology": "إصلاحي",
        "priority_order": 6,
    },
    {
        "slug": "al-qurtubi",
        "name_ar": "الجامع لأحكام القرآن",
        "name_en": "al-Jami li-Ahkam al-Quran",
        "author_ar": "القرطبي",
        "author_death_year": 671,
        "methodology": "فقهي",
        "priority_order": 7,
    },
]


async def ensure_tafseer_books(conn: asyncpg.Connection) -> dict[str, int]:
    """أدخل كتب التفسير وأعد mapping slug → id."""
    slug_to_id = {}

    for book in TAFSEER_BOOKS:
        row = await conn.fetchrow(
            "SELECT id FROM tafseer_books WHERE slug = $1", book["slug"]
        )
        if row:
            slug_to_id[book["slug"]] = row["id"]
        else:
            book_id = await conn.fetchval(
                """
                INSERT INTO tafseer_books
                    (slug, name_ar, name_en, author_ar,
                     author_death_year, methodology, priority_order)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
                """,
                book["slug"],
                book["name_ar"],
                book["name_en"],
                book["author_ar"],
                book["author_death_year"],
                book["methodology"],
                book["priority_order"],
            )
            slug_to_id[book["slug"]] = book_id
            print(f"  ✅ أُضيف: {book['name_ar']} (id={book_id})")

    return slug_to_id


async def get_verse_id_map(conn: asyncpg.Connection) -> dict[str, int]:
    """بناء mapping من verse_key → verse_id."""
    rows = await conn.fetch(
        "SELECT id, surah_number, verse_number FROM verses"
    )
    return {
        f"{r['surah_number']}:{r['verse_number']}": r["id"]
        for r in rows
    }


async def load_tafseer_file(
    conn: asyncpg.Connection,
    json_path: Path,
    book_id: int,
    verse_map: dict[str, int],
    dry_run: bool = False,
) -> dict:
    """تحميل ملف تفسير JSON واحد إلى قاعدة البيانات."""
    data = json.loads(json_path.read_text(encoding="utf-8"))
    stats = {"loaded": 0, "skipped": 0, "missing_verse": 0}

    surahs = data.get("surahs", {})

    for surah_num, entries in surahs.items():
        for entry in entries:
            verse_key = entry.get("verse_key", "")
            text = entry.get("text", "").strip()

            if not text:
                stats["skipped"] += 1
                continue

            verse_id = verse_map.get(verse_key)
            if not verse_id:
                stats["missing_verse"] += 1
                continue

            if not dry_run:
                await conn.execute(
                    """
                    INSERT INTO tafseers (verse_id, book_id, text)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (verse_id, book_id)
                    DO UPDATE SET text = EXCLUDED.text
                    """,
                    verse_id,
                    book_id,
                    text,
                )

            stats["loaded"] += 1

    return stats


async def main():
    parser = argparse.ArgumentParser(
        description="تحميل التفاسير من JSON إلى PostgreSQL"
    )
    parser.add_argument(
        "--db-url",
        default=os.environ.get(
            "DATABASE_URL",
            "postgresql://quran_user:changeme@localhost:5432/quran_miracles",
        ),
        help="رابط قاعدة البيانات",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="عرض ما سيتم بدون تنفيذ",
    )
    args = parser.parse_args()

    db_url = args.db_url.replace("postgresql+asyncpg://", "postgresql://")

    if not DATA_DIR.exists():
        print(f"❌ مجلد التفاسير غير موجود: {DATA_DIR}")
        print("   شغّل أولاً: python scripts/fetch_tafseers.py")
        sys.exit(1)

    json_files = list(DATA_DIR.glob("*.json"))
    if not json_files:
        print(f"❌ لا ملفات JSON في {DATA_DIR}")
        print("   شغّل أولاً: python scripts/fetch_tafseers.py")
        sys.exit(1)

    print(f"📂 وُجد {len(json_files)} ملف تفسير")
    if args.dry_run:
        print("🔍 وضع المعاينة — لن يتم تعديل قاعدة البيانات")

    conn = await asyncpg.connect(db_url)

    try:
        # 1. تأكد من وجود كتب التفسير
        print("\n📚 إعداد كتب التفسير...")
        slug_to_id = await ensure_tafseer_books(conn)
        print(f"   {len(slug_to_id)} كتاب جاهز")

        # 2. بناء خريطة الآيات
        print("\n🗺️ بناء خريطة الآيات...")
        verse_map = await get_verse_id_map(conn)
        print(f"   {len(verse_map)} آية في قاعدة البيانات")

        if not verse_map:
            print("❌ لا آيات في قاعدة البيانات!")
            print("   شغّل أولاً: python backend/scripts/apply_schema.py")
            return

        # 3. تحميل كل ملف
        total_stats = {"loaded": 0, "skipped": 0, "missing_verse": 0}

        for json_path in sorted(json_files):
            # استخرج slug من اسم الملف
            slug = json_path.stem.replace("_qurancom", "")

            book_id = slug_to_id.get(slug)
            if not book_id:
                print(f"  ⚠️ تخطي {json_path.name} — لا يوجد كتاب بـ slug={slug}")
                continue

            print(f"\n📖 تحميل {json_path.name}...")
            stats = await load_tafseer_file(
                conn, json_path, book_id, verse_map, args.dry_run
            )
            total_stats["loaded"] += stats["loaded"]
            total_stats["skipped"] += stats["skipped"]
            total_stats["missing_verse"] += stats["missing_verse"]
            print(
                f"   ✅ {stats['loaded']} آية محملة"
                f" | ⏭️ {stats['skipped']} فارغة"
                f" | ⚠️ {stats['missing_verse']} آية غير موجودة"
            )

        print(f"\n{'=' * 50}")
        print(f"📊 الإجمالي:")
        print(f"   ✅ {total_stats['loaded']} تفسير محمّل")
        print(f"   ⏭️ {total_stats['skipped']} فارغ")
        print(f"   ⚠️ {total_stats['missing_verse']} آية غير موجودة")

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
