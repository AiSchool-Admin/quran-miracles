"""Database bootstrap — auto-initialize schema and load Quran data.

Run on Railway startup BEFORE uvicorn. Idempotent — safe to run multiple times.

Steps:
  1. Connect to PostgreSQL (retry with backoff)
  2. Check if schema exists (surahs table)
  3. If not: apply schema.sql
  4. Check if Quran data loaded (verse count)
  5. If not: load from local JSON files (data/quran/)
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
from pathlib import Path

import asyncpg

# Quran JSON files — copied into Docker image at /data/quran/
_DATA_PATHS = [
    Path("/data/quran"),               # Docker
    Path(__file__).parent.parent / "data" / "quran",  # Local dev
]

_DIACRITICS_RE = re.compile(
    "["
    "\u0610-\u061A"
    "\u064B-\u065F"
    "\u0670"
    "\u06D6-\u06DC"
    "\u06DF-\u06E4"
    "\u06E7\u06E8"
    "\u06EA-\u06ED"
    "\u08D3-\u08E1"
    "\u08E3-\u08FF"
    "\uFE70-\uFE7F"
    "]"
)

# Surah metadata (number, name_arabic, name_english, transliteration, revelation_type, revelation_order)
_SURAH_META = [
    (1, "الفاتحة", "The Opening", "Al-Fatihah", "makki", 5),
    (2, "البقرة", "The Cow", "Al-Baqarah", "madani", 87),
    (3, "آل عمران", "Family of Imran", "Ali 'Imran", "madani", 89),
    (4, "النساء", "The Women", "An-Nisa", "madani", 92),
    (5, "المائدة", "The Table Spread", "Al-Ma'idah", "madani", 112),
    (6, "الأنعام", "The Cattle", "Al-An'am", "makki", 55),
    (7, "الأعراف", "The Heights", "Al-A'raf", "makki", 39),
    (8, "الأنفال", "The Spoils of War", "Al-Anfal", "madani", 88),
    (9, "التوبة", "The Repentance", "At-Tawbah", "madani", 113),
    (10, "يونس", "Jonah", "Yunus", "makki", 51),
    (11, "هود", "Hud", "Hud", "makki", 52),
    (12, "يوسف", "Joseph", "Yusuf", "makki", 53),
    (13, "الرعد", "The Thunder", "Ar-Ra'd", "madani", 96),
    (14, "إبراهيم", "Abraham", "Ibrahim", "makki", 72),
    (15, "الحجر", "The Rocky Tract", "Al-Hijr", "makki", 54),
    (16, "النحل", "The Bee", "An-Nahl", "makki", 70),
    (17, "الإسراء", "The Night Journey", "Al-Isra", "makki", 50),
    (18, "الكهف", "The Cave", "Al-Kahf", "makki", 69),
    (19, "مريم", "Mary", "Maryam", "makki", 44),
    (20, "طه", "Ta-Ha", "Taha", "makki", 45),
    (21, "الأنبياء", "The Prophets", "Al-Anbya", "makki", 73),
    (22, "الحج", "The Pilgrimage", "Al-Hajj", "madani", 103),
    (23, "المؤمنون", "The Believers", "Al-Mu'minun", "makki", 74),
    (24, "النور", "The Light", "An-Nur", "madani", 102),
    (25, "الفرقان", "The Criterion", "Al-Furqan", "makki", 42),
    (26, "الشعراء", "The Poets", "Ash-Shu'ara", "makki", 47),
    (27, "النمل", "The Ant", "An-Naml", "makki", 48),
    (28, "القصص", "The Stories", "Al-Qasas", "makki", 49),
    (29, "العنكبوت", "The Spider", "Al-'Ankabut", "makki", 85),
    (30, "الروم", "The Romans", "Ar-Rum", "makki", 84),
    (31, "لقمان", "Luqman", "Luqman", "makki", 57),
    (32, "السجدة", "The Prostration", "As-Sajdah", "makki", 75),
    (33, "الأحزاب", "The Combined Forces", "Al-Ahzab", "madani", 90),
    (34, "سبأ", "Sheba", "Saba", "makki", 58),
    (35, "فاطر", "Originator", "Fatir", "makki", 43),
    (36, "يس", "Ya-Sin", "Ya-Sin", "makki", 41),
    (37, "الصافات", "Those Ranged in Ranks", "As-Saffat", "makki", 56),
    (38, "ص", "The Letter Sad", "Sad", "makki", 38),
    (39, "الزمر", "The Troops", "Az-Zumar", "makki", 59),
    (40, "غافر", "The Forgiver", "Ghafir", "makki", 60),
    (41, "فصلت", "Explained in Detail", "Fussilat", "makki", 61),
    (42, "الشورى", "The Consultation", "Ash-Shuraa", "makki", 62),
    (43, "الزخرف", "The Ornaments of Gold", "Az-Zukhruf", "makki", 63),
    (44, "الدخان", "The Smoke", "Ad-Dukhan", "makki", 64),
    (45, "الجاثية", "The Crouching", "Al-Jathiyah", "makki", 65),
    (46, "الأحقاف", "The Wind-Curved Sandhills", "Al-Ahqaf", "makki", 66),
    (47, "محمد", "Muhammad", "Muhammad", "madani", 95),
    (48, "الفتح", "The Victory", "Al-Fath", "madani", 111),
    (49, "الحجرات", "The Rooms", "Al-Hujurat", "madani", 106),
    (50, "ق", "The Letter Qaf", "Qaf", "makki", 34),
    (51, "الذاريات", "The Winnowing Winds", "Adh-Dhariyat", "makki", 67),
    (52, "الطور", "The Mount", "At-Tur", "makki", 76),
    (53, "النجم", "The Star", "An-Najm", "makki", 23),
    (54, "القمر", "The Moon", "Al-Qamar", "makki", 37),
    (55, "الرحمن", "The Beneficent", "Ar-Rahman", "madani", 97),
    (56, "الواقعة", "The Inevitable", "Al-Waqi'ah", "makki", 46),
    (57, "الحديد", "The Iron", "Al-Hadid", "madani", 94),
    (58, "المجادلة", "The Pleading Woman", "Al-Mujadila", "madani", 105),
    (59, "الحشر", "The Exile", "Al-Hashr", "madani", 101),
    (60, "الممتحنة", "She That is to Be Examined", "Al-Mumtahanah", "madani", 91),
    (61, "الصف", "The Ranks", "As-Saf", "madani", 109),
    (62, "الجمعة", "The Congregation", "Al-Jumu'ah", "madani", 110),
    (63, "المنافقون", "The Hypocrites", "Al-Munafiqun", "madani", 104),
    (64, "التغابن", "The Mutual Disillusion", "At-Taghabun", "madani", 108),
    (65, "الطلاق", "The Divorce", "At-Talaq", "madani", 99),
    (66, "التحريم", "The Prohibition", "At-Tahrim", "madani", 107),
    (67, "الملك", "The Sovereignty", "Al-Mulk", "makki", 77),
    (68, "القلم", "The Pen", "Al-Qalam", "makki", 2),
    (69, "الحاقة", "The Reality", "Al-Haqqah", "makki", 78),
    (70, "المعارج", "The Ascending Stairways", "Al-Ma'arij", "makki", 79),
    (71, "نوح", "Noah", "Nuh", "makki", 71),
    (72, "الجن", "The Jinn", "Al-Jinn", "makki", 40),
    (73, "المزمل", "The Enshrouded One", "Al-Muzzammil", "makki", 3),
    (74, "المدثر", "The Cloaked One", "Al-Muddaththir", "makki", 4),
    (75, "القيامة", "The Resurrection", "Al-Qiyamah", "makki", 31),
    (76, "الإنسان", "The Human", "Al-Insan", "madani", 98),
    (77, "المرسلات", "The Emissaries", "Al-Mursalat", "makki", 33),
    (78, "النبأ", "The Tidings", "An-Naba", "makki", 80),
    (79, "النازعات", "Those Who Drag Forth", "An-Nazi'at", "makki", 81),
    (80, "عبس", "He Frowned", "Abasa", "makki", 24),
    (81, "التكوير", "The Overthrowing", "At-Takwir", "makki", 7),
    (82, "الانفطار", "The Cleaving", "Al-Infitar", "makki", 82),
    (83, "المطففين", "The Defrauding", "Al-Mutaffifin", "makki", 86),
    (84, "الانشقاق", "The Sundering", "Al-Inshiqaq", "makki", 83),
    (85, "البروج", "The Mansions of the Stars", "Al-Buruj", "makki", 27),
    (86, "الطارق", "The Nightcomer", "At-Tariq", "makki", 36),
    (87, "الأعلى", "The Most High", "Al-A'la", "makki", 8),
    (88, "الغاشية", "The Overwhelming", "Al-Ghashiyah", "makki", 68),
    (89, "الفجر", "The Dawn", "Al-Fajr", "makki", 10),
    (90, "البلد", "The City", "Al-Balad", "makki", 35),
    (91, "الشمس", "The Sun", "Ash-Shams", "makki", 26),
    (92, "الليل", "The Night", "Al-Layl", "makki", 9),
    (93, "الضحى", "The Morning Hours", "Ad-Duhaa", "makki", 11),
    (94, "الشرح", "The Relief", "Ash-Sharh", "makki", 12),
    (95, "التين", "The Fig", "At-Tin", "makki", 28),
    (96, "العلق", "The Clot", "Al-'Alaq", "makki", 1),
    (97, "القدر", "The Power", "Al-Qadr", "makki", 25),
    (98, "البينة", "The Clear Proof", "Al-Bayyinah", "madani", 100),
    (99, "الزلزلة", "The Earthquake", "Az-Zalzalah", "madani", 93),
    (100, "العاديات", "The Courser", "Al-'Adiyat", "makki", 14),
    (101, "القارعة", "The Calamity", "Al-Qari'ah", "makki", 30),
    (102, "التكاثر", "The Rivalry in World Increase", "At-Takathur", "makki", 16),
    (103, "العصر", "The Declining Day", "Al-'Asr", "makki", 13),
    (104, "الهمزة", "The Traducer", "Al-Humazah", "makki", 32),
    (105, "الفيل", "The Elephant", "Al-Fil", "makki", 19),
    (106, "قريش", "Quraysh", "Quraysh", "makki", 29),
    (107, "الماعون", "The Small Kindnesses", "Al-Ma'un", "makki", 17),
    (108, "الكوثر", "The Abundance", "Al-Kawthar", "makki", 15),
    (109, "الكافرون", "The Disbelievers", "Al-Kafirun", "makki", 18),
    (110, "النصر", "The Divine Support", "An-Nasr", "madani", 114),
    (111, "المسد", "The Palm Fiber", "Al-Masad", "makki", 6),
    (112, "الإخلاص", "The Sincerity", "Al-Ikhlas", "makki", 22),
    (113, "الفلق", "The Daybreak", "Al-Falaq", "makki", 20),
    (114, "الناس", "The Mankind", "An-Nas", "makki", 21),
]


def _strip_diacritics(text: str) -> str:
    return _DIACRITICS_RE.sub("", text)


def _find_data_dir() -> Path | None:
    for p in _DATA_PATHS:
        if p.exists() and list(p.glob("surah_*.json")):
            return p
    return None


async def bootstrap(max_retries: int = 5) -> bool:
    """Bootstrap the database. Returns True if DB is ready, False otherwise."""
    database_url = os.environ.get("DATABASE_URL", "")
    if not database_url:
        print("⚠️ DATABASE_URL not set — skipping bootstrap", flush=True)
        return False

    # Normalize URL for asyncpg
    database_url = database_url.replace("postgresql+asyncpg://", "postgresql://")

    # ── 1. Connect with retry ──
    conn: asyncpg.Connection | None = None
    for attempt in range(1, max_retries + 1):
        try:
            conn = await asyncio.wait_for(asyncpg.connect(database_url), timeout=10)
            print(f"✅ Database connected (attempt {attempt})", flush=True)
            break
        except Exception as exc:
            if attempt == max_retries:
                print(f"❌ Cannot connect to database after {max_retries} attempts: {exc}", flush=True)
                return False
            delay = 2.0 * (2 ** (attempt - 1))
            print(f"⏳ DB connection attempt {attempt} failed: {exc}. Retrying in {delay}s...", flush=True)
            await asyncio.sleep(delay)

    assert conn is not None

    try:
        # ── 2. Check if schema exists ──
        table_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'surahs')"
        )

        if not table_exists:
            print("📋 Applying database schema...", flush=True)
            schema_path = Path(__file__).parent / "database" / "schema.sql"
            if not schema_path.exists():
                print(f"❌ Schema file not found: {schema_path}", flush=True)
                return False

            sql = schema_path.read_text(encoding="utf-8")
            await conn.execute(sql)
            print("✅ Schema applied", flush=True)
        else:
            print("✅ Schema already exists", flush=True)

        # ── 3. Check if Quran data loaded ──
        verse_count = await conn.fetchval("SELECT COUNT(*) FROM verses")
        print(f"📊 Current verse count: {verse_count}", flush=True)

        if verse_count >= 6200:
            print("✅ Quran data already loaded — bootstrap complete", flush=True)
            return True

        # ── 4. Load Quran data from JSON files ──
        data_dir = _find_data_dir()
        if data_dir is None:
            print("⚠️ No Quran JSON files found — skipping data load", flush=True)
            return True  # Schema exists, just no data yet

        print(f"📖 Loading Quran data from {data_dir}...", flush=True)

        # Insert surahs first
        surah_count = 0
        for num, name_ar, name_en, translit, rev_type, rev_order in _SURAH_META:
            json_path = data_dir / f"surah_{num:03d}.json"
            vc = 0
            if json_path.exists():
                verses_data = json.loads(json_path.read_text(encoding="utf-8"))
                vc = len(verses_data)

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
                num, name_ar, name_en, translit, rev_type, rev_order, vc,
            )
            surah_count += 1

        print(f"  ✅ {surah_count} surahs loaded", flush=True)

        # Insert verses
        total_verses = 0
        for surah_num in range(1, 115):
            json_path = data_dir / f"surah_{surah_num:03d}.json"
            if not json_path.exists():
                continue

            verses_data = json.loads(json_path.read_text(encoding="utf-8"))
            for v in verses_data:
                text_clean = v.get("text_clean") or _strip_diacritics(
                    v.get("text_simple") or v.get("text_uthmani", "")
                )

                sajda_type = v.get("sajda_type")
                if sajda_type == "recommended":
                    sajda_type = "mustahab"
                elif sajda_type == "obligatory":
                    sajda_type = "wajib"
                elif sajda_type not in ("wajib", "mustahab"):
                    sajda_type = None

                await conn.execute(
                    """
                    INSERT INTO verses (surah_number, verse_number, text_uthmani,
                                        text_simple, text_clean, juz,
                                        page_number, sajda, sajda_type)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (surah_number, verse_number) DO UPDATE SET
                        text_uthmani = EXCLUDED.text_uthmani,
                        text_simple = EXCLUDED.text_simple,
                        text_clean = EXCLUDED.text_clean
                    """,
                    v["surah_number"],
                    v["verse_number"],
                    v.get("text_uthmani", ""),
                    v.get("text_simple", ""),
                    text_clean,
                    v.get("juz", 1),
                    v.get("page"),
                    v.get("sajda", False),
                    sajda_type,
                )
                total_verses += 1

            if surah_num % 10 == 0:
                print(f"  📖 {surah_num}/114 surahs processed...", flush=True)

        print(f"  ✅ {total_verses} verses loaded", flush=True)

        # Final count
        final_count = await conn.fetchval("SELECT COUNT(*) FROM verses")
        print(f"✅ Bootstrap complete — {final_count} verses in database", flush=True)
        return True

    except Exception as exc:
        print(f"❌ Bootstrap error: {exc}", flush=True)
        import traceback
        traceback.print_exc()
        return False
    finally:
        await conn.close()


if __name__ == "__main__":
    success = asyncio.run(bootstrap())
    sys.exit(0 if success else 1)
