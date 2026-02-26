#!/usr/bin/env python3
"""تحويل مجلدات تفسير الشعراوي (17 مجلداً PDF) إلى نصوص مرتبطة بالآيات.

مصادر PDF:
- shamela.ws (مكتبة الشاملة) — الأكثر موثوقية
- المكتبة الرقمية الإسلامية

ملاحظة مهمة:
التفسير منقول من شرح شفهي (محاضرات مسجلة) —
يُنسَب بصيغة: "قال الشعراوي في خواطره..."

الاستخدام:
    python data/pipelines/shaarawy_pdf_pipeline.py --pdf-dir data/shaarawy/
    python data/pipelines/shaarawy_pdf_pipeline.py --pdf-dir data/shaarawy/ --dry-run
    python data/pipelines/shaarawy_pdf_pipeline.py --pdf-dir data/shaarawy/ --volume 1
"""

import argparse
import asyncio
import json
import re
import unicodedata
from pathlib import Path
from typing import Generator

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from camel_tools.utils.normalize import normalize_unicode
except ImportError:
    def normalize_unicode(text: str) -> str:
        return unicodedata.normalize("NFC", text)


# ── سور القرآن (للربط) ──────────────────────────────
SURAH_NAMES = [
    "الفاتحة", "البقرة", "آل عمران", "النساء", "المائدة",
    "الأنعام", "الأعراف", "الأنفال", "التوبة", "يونس",
    "هود", "يوسف", "الرعد", "إبراهيم", "الحجر",
    "النحل", "الإسراء", "الكهف", "مريم", "طه",
    "الأنبياء", "الحج", "المؤمنون", "النور", "الفرقان",
    "الشعراء", "النمل", "القصص", "العنكبوت", "الروم",
    "لقمان", "السجدة", "الأحزاب", "سبأ", "فاطر",
    "يس", "الصافات", "ص", "الزمر", "غافر",
    "فصلت", "الشورى", "الزخرف", "الدخان", "الجاثية",
    "الأحقاف", "محمد", "الفتح", "الحجرات", "ق",
    "الذاريات", "الطور", "النجم", "القمر", "الرحمن",
    "الواقعة", "الحديد", "المجادلة", "الحشر", "الممتحنة",
    "الصف", "الجمعة", "المنافقون", "التغابن", "الطلاق",
    "التحريم", "الملك", "القلم", "الحاقة", "المعارج",
    "نوح", "الجن", "المزمل", "المدثر", "القيامة",
    "الإنسان", "المرسلات", "النبأ", "النازعات", "عبس",
    "التكوير", "الانفطار", "المطففين", "الانشقاق", "البروج",
    "الطارق", "الأعلى", "الغاشية", "الفجر", "البلد",
    "الشمس", "الليل", "الضحى", "الشرح", "التين",
    "العلق", "القدر", "البينة", "الزلزلة", "العاديات",
    "القارعة", "التكاثر", "العصر", "الهمزة", "الفيل",
    "قريش", "الماعون", "الكوثر", "الكافرون", "النصر",
    "المسد", "الإخلاص", "الفلق", "الناس",
]


class ShaarawyPDFPipeline:
    """تحويل مجلدات تفسير الشعراوي من PDF إلى نصوص مرتبطة بالآيات."""

    VERSE_PATTERNS = [
        r'قوله تعالى[:\s]*[﴿«"](.*?)[﴾»"]',
        r'﴿(.*?)﴾',
        r'الآية\s+\((\d+)\)\s+من\s+سورة\s+(.+)',
        r'سورة\s+([\u0600-\u06FF]+)\s+[\-–:]\s*الآية\s+(\d+)',
        r'\{(.*?)\}',
    ]

    def __init__(
        self,
        pdf_dir: str | Path,
        output_dir: str | Path | None = None,
        quran_data_dir: str | Path | None = None,
    ):
        self.pdf_dir = Path(pdf_dir)
        self.output_dir = Path(output_dir or self.pdf_dir.parent / "shaarawy_extracted")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # تحميل بيانات القرآن للربط
        self.quran_dir = Path(quran_data_dir or self.pdf_dir.parent.parent / "data" / "quran")
        self.verse_index = self._build_verse_index()

    def _build_verse_index(self) -> dict[str, dict]:
        """بناء فهرس للآيات القرآنية من ملفات JSON."""
        index: dict[str, dict] = {}

        complete_file = self.quran_dir / "quran_complete.json"
        if not complete_file.exists():
            print("⚠️ quran_complete.json not found — verse linking will be limited")
            return index

        try:
            verses = json.loads(complete_file.read_text(encoding="utf-8"))
            for v in verses:
                key = f"{v['surah_number']}:{v['verse_number']}"
                index[key] = v
                # فهرسة بالنص النظيف أيضاً (أول 30 حرف)
                clean = v.get("text_clean", "")
                if clean and len(clean) > 10:
                    index[clean[:30]] = v
        except Exception as e:
            print(f"⚠️ Failed to load Quran data: {e}")

        return index

    def process_all_volumes(self, volume: int | None = None) -> dict:
        """معالجة جميع المجلدات (أو مجلد واحد محدد)."""
        if pdfplumber is None:
            return {
                "error": "pdfplumber not installed. Run: pip install pdfplumber",
                "processed": 0,
            }

        results = {"processed": 0, "failed": 0, "total_chunks": 0, "linked": 0}

        if volume:
            pdf_files = list(self.pdf_dir.glob(f"*vol*{volume}*.pdf"))
            if not pdf_files:
                pdf_files = list(self.pdf_dir.glob(f"*{volume}*.pdf"))
        else:
            pdf_files = sorted(self.pdf_dir.glob("*.pdf"))

        if not pdf_files:
            print(f"⚠️ لا ملفات PDF في {self.pdf_dir}")
            return results

        for pdf_path in pdf_files:
            vol_num = self._extract_volume_number(pdf_path)
            print(f"\n📖 معالجة المجلد {vol_num}: {pdf_path.name}")

            try:
                chunks = list(self._extract_chunks(pdf_path))
                linked = self._link_to_verses(chunks)

                # حفظ
                out_path = self.output_dir / f"shaarawy_vol_{vol_num:02d}.json"
                out_path.write_text(
                    json.dumps(
                        {
                            "volume": vol_num,
                            "source_file": pdf_path.name,
                            "total_chunks": len(chunks),
                            "linked_count": len(linked),
                            "chunks": linked,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )

                results["processed"] += 1
                results["total_chunks"] += len(chunks)
                results["linked"] += len(linked)
                print(f"  ✅ {len(chunks)} مقطع → {len(linked)} مرتبط بآيات")

            except Exception as e:
                print(f"  ❌ خطأ: {e}")
                results["failed"] += 1

        return results

    def _extract_chunks(self, pdf_path: Path) -> Generator[dict, None, None]:
        """استخراج مقاطع التفسير من PDF."""
        with pdfplumber.open(pdf_path) as pdf:
            current_chunk: dict = {
                "text": "",
                "page_refs": [],
                "raw_verse_hint": "",
            }

            for page in pdf.pages:
                text = page.extract_text(x_tolerance=2, y_tolerance=2)
                if not text:
                    continue

                text = normalize_unicode(text)
                text = self._clean_ocr_artifacts(text)

                for line in text.split("\n"):
                    if self._is_verse_reference(line):
                        if current_chunk["text"].strip():
                            yield current_chunk
                        current_chunk = {
                            "text": line + "\n",
                            "page_refs": [page.page_number],
                            "raw_verse_hint": line,
                        }
                    else:
                        current_chunk["text"] += line + "\n"
                        if page.page_number not in current_chunk["page_refs"]:
                            current_chunk["page_refs"].append(page.page_number)

            if current_chunk["text"].strip():
                yield current_chunk

    def _link_to_verses(self, chunks: list[dict]) -> list[dict]:
        """ربط كل مقطع بالآية المقابلة."""
        linked = []

        for chunk in chunks:
            verse_info = self._resolve_verse(chunk["raw_verse_hint"])
            entry = {
                "text": chunk["text"].strip(),
                "page_refs": chunk["page_refs"],
                "source_note": "منقول من الشرح الشفهي — خواطر حول القرآن الكريم",
            }

            if verse_info:
                entry["surah_number"] = verse_info.get("surah_number")
                entry["verse_number"] = verse_info.get("verse_number")
                entry["verse_key"] = (
                    f"{verse_info['surah_number']}:{verse_info['verse_number']}"
                )
                entry["linked"] = True
            else:
                entry["linked"] = False

            linked.append(entry)

        return linked

    def _resolve_verse(self, hint: str) -> dict | None:
        """محاولة ربط تلميح النص بآية محددة."""
        # محاولة 1: ﴿...﴾
        match = re.search(r"﴿(.*?)﴾", hint)
        if match:
            verse_text = match.group(1).strip()
            # بحث في الفهرس
            for key, v in self.verse_index.items():
                if isinstance(v, dict) and verse_text[:20] in str(v.get("text_clean", "")):
                    return v

        # محاولة 2: سورة X الآية Y
        match = re.search(r"سورة\s+([\u0600-\u06FF]+)\s*.*?(\d+)", hint)
        if match:
            surah_name = match.group(1)
            verse_num = int(match.group(2))
            for i, name in enumerate(SURAH_NAMES):
                if surah_name in name or name in surah_name:
                    key = f"{i + 1}:{verse_num}"
                    return self.verse_index.get(key)

        # محاولة 3: الآية (N)
        match = re.search(r"الآية\s*\(?(\d+)\)?", hint)
        if match:
            verse_num = int(match.group(1))
            # بدون سورة — لا يمكن الربط بدقة
            return None

        return None

    def _is_verse_reference(self, line: str) -> bool:
        """هل هذا السطر يشير لبداية تفسير آية؟"""
        return any(re.search(p, line) for p in self.VERSE_PATTERNS)

    def _clean_ocr_artifacts(self, text: str) -> str:
        """تنظيف أخطاء OCR الشائعة."""
        # إزالة الأحرف اللاتينية المتطفلة
        text = re.sub(r"[a-zA-Z]{1,2}(?=\s|$)", "", text)
        # توحيد المسافات
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _extract_volume_number(self, pdf_path: Path) -> int:
        """استخراج رقم المجلد من اسم الملف."""
        match = re.search(r"(\d+)", pdf_path.stem)
        return int(match.group(1)) if match else 0


async def load_to_database(
    extracted_dir: Path, db_url: str, book_id: int
) -> dict:
    """تحميل المقاطع المستخرجة إلى قاعدة البيانات."""
    import asyncpg

    conn = await asyncpg.connect(db_url)
    stats = {"loaded": 0, "skipped": 0}

    try:
        # بناء خريطة الآيات
        rows = await conn.fetch(
            "SELECT id, surah_number, verse_number FROM verses"
        )
        verse_map = {
            f"{r['surah_number']}:{r['verse_number']}": r["id"]
            for r in rows
        }

        for json_file in sorted(extracted_dir.glob("shaarawy_vol_*.json")):
            data = json.loads(json_file.read_text(encoding="utf-8"))

            for chunk in data.get("chunks", []):
                if not chunk.get("linked"):
                    stats["skipped"] += 1
                    continue

                verse_key = chunk.get("verse_key", "")
                verse_id = verse_map.get(verse_key)
                if not verse_id:
                    stats["skipped"] += 1
                    continue

                await conn.execute(
                    """
                    INSERT INTO tafseers (verse_id, book_id, text, page_ref, metadata)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (verse_id, book_id)
                    DO UPDATE SET text = EXCLUDED.text
                    """,
                    verse_id,
                    book_id,
                    chunk["text"],
                    f"ص{chunk['page_refs'][0]}" if chunk.get("page_refs") else None,
                    json.dumps({
                        "source_note": chunk.get("source_note", ""),
                        "citation_format": "شفهي-محاضرة",
                    }),
                )
                stats["loaded"] += 1

    finally:
        await conn.close()

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="تحويل تفسير الشعراوي من PDF إلى نصوص مرتبطة بالآيات"
    )
    parser.add_argument(
        "--pdf-dir",
        required=True,
        help="مجلد ملفات PDF",
    )
    parser.add_argument(
        "--output-dir",
        help="مجلد الإخراج (default: data/shaarawy_extracted/)",
    )
    parser.add_argument(
        "--volume",
        type=int,
        help="معالجة مجلد واحد فقط",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="عرض بدون تنفيذ",
    )
    args = parser.parse_args()

    pipeline = ShaarawyPDFPipeline(
        pdf_dir=args.pdf_dir,
        output_dir=args.output_dir,
    )

    if args.dry_run:
        pdf_files = list(Path(args.pdf_dir).glob("*.pdf"))
        print(f"🔍 وُجد {len(pdf_files)} ملف PDF:")
        for f in pdf_files:
            print(f"  - {f.name}")
        return

    results = pipeline.process_all_volumes(volume=args.volume)
    print(f"\n{'=' * 50}")
    print(f"📊 النتائج:")
    print(f"   ✅ {results['processed']} مجلد معالج")
    print(f"   📝 {results['total_chunks']} مقطع إجمالي")
    print(f"   🔗 {results['linked']} مرتبط بآيات")
    print(f"   ❌ {results['failed']} فشل")


if __name__ == "__main__":
    main()
