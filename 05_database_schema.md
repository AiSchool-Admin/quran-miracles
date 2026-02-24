# 🗄️ القسم الخامس: قاعدة البيانات الشاملة
> المرجع: CLAUDE.md → docs/05_database_schema.md
> ⚠️ قراءة إلزامية قبل أي تعديل على Schema أو migrations

---

## ⭐ تحديث مهم — إضافة تفسير الشعراوي

```sql
-- إضافة الشعراوي لجدول tafseer_books
INSERT INTO tafseer_books
    (slug, name_ar, author_ar, author_death_year, methodology, priority_order, use_cases)
VALUES
    ('al-shaarawy',
     'تفسير الشعراوي — خواطر حول القرآن الكريم',
     'محمد متولى الشعراوي',
     1998,
     'بياني-لغوي-اجتماعي',
     3,
     ARRAY[
       'تحليل دقائق الألفاظ القرآنية',
       'الأثر النفسي والاجتماعي للآيات',
       'مقارنة الكلمات المتشابهة',
       'ربط النص القرآني بالواقع المعاصر'
     ]
    );
```

## Pipeline استيراد تفسير الشعراوي من PDF

```python
# data/pipelines/shaarawy_pdf_pipeline.py

import re
import json
from pathlib import Path
from typing import Generator
import pdfplumber
from camel_tools.utils.normalize import normalize_unicode

class ShaarawyPDFPipeline:
    """
    تحويل مجلدات تفسير الشعراوي (17 مجلداً PDF)
    إلى نصوص مُرتبطة بالآيات في قاعدة البيانات
    
    مصادر PDF:
    - shamela.ws (مكتبة الشاملة) — الأكثر موثوقية
    - المكتبة الرقمية الإسلامية
    
    ملاحظة مهمة:
    التفسير منقول من شرح شفهي (محاضرات مسجلة) —
    يُنسَب دائماً بصيغة: "قال الشعراوي في خواطره..."
    وليس بصيغة: "قال الشعراوي في كتابه..."
    """
    
    VERSE_PATTERNS = [
        r'قوله تعالى[:\s]+[﴿«"](.*?)[﴾»"]',
        r'﴿(.*?)﴾',
        r'الآية\s+\((\d+)\)\s+من سورة\s+(.+)',
        r'(\d+)[\-–](\d+)\s*[|:]',  # رقم السورة-رقم الآية
    ]
    
    def __init__(self, pdf_dir: str, quran_db, output_dir: str):
        self.pdf_dir   = Path(pdf_dir)
        self.quran_db  = quran_db
        self.output_dir = Path(output_dir)
    
    def process_all_volumes(self) -> dict:
        """معالجة جميع المجلدات السبعة عشر"""
        results = {"processed": 0, "failed": 0, "verses_linked": 0}
        
        for pdf_path in sorted(self.pdf_dir.glob("shaarawy_vol_*.pdf")):
            volume_num = self._extract_volume_number(pdf_path)
            print(f"📖 معالجة المجلد {volume_num}...")
            
            try:
                chunks = list(self._extract_chunks(pdf_path))
                linked = self._link_to_verses(chunks)
                self._save_to_db(linked, volume_num)
                
                results["processed"] += 1
                results["verses_linked"] += len(linked)
            except Exception as e:
                print(f"⚠️ خطأ في المجلد {volume_num}: {e}")
                results["failed"] += 1
        
        return results
    
    def _extract_chunks(self, pdf_path: Path) -> Generator:
        """
        استخراج مقاطع التفسير من PDF
        كل مقطع = تعليق الشعراوي على آية أو مجموعة آيات
        """
        with pdfplumber.open(pdf_path) as pdf:
            current_chunk = {"text": "", "page_refs": [], "raw_verse_hint": ""}
            
            for page in pdf.pages:
                text = page.extract_text(x_tolerance=2, y_tolerance=2)
                if not text:
                    continue
                
                # تطبيع النص العربي
                text = normalize_unicode(text)
                text = self._clean_ocr_artifacts(text)
                
                lines = text.split('\n')
                for line in lines:
                    # هل هذا بداية تعليق على آية جديدة؟
                    if self._is_verse_reference(line):
                        if current_chunk["text"].strip():
                            yield current_chunk
                        current_chunk = {
                            "text": line + "\n",
                            "page_refs": [page.page_number],
                            "raw_verse_hint": line
                        }
                    else:
                        current_chunk["text"] += line + "\n"
                        if page.page_number not in current_chunk["page_refs"]:
                            current_chunk["page_refs"].append(page.page_number)
            
            if current_chunk["text"].strip():
                yield current_chunk
    
    def _link_to_verses(self, chunks: list) -> list:
        """ربط كل مقطع بالآية المقابلة في قاعدة البيانات"""
        linked = []
        
        for chunk in chunks:
            verse_id = self._resolve_verse_id(chunk["raw_verse_hint"])
            
            if verse_id:
                linked.append({
                    "verse_id":    verse_id,
                    "book_id":     self._get_shaarawy_book_id(),
                    "text":        chunk["text"].strip(),
                    "page_ref":    f"ص{chunk['page_refs'][0]}",
                    "source_note": "منقول من الشرح الشفهي — خواطر حول القرآن الكريم",
                    "citation_format": "شفهي-محاضرة"
                })
            else:
                # احفظ بدون ربط للمراجعة اليدوية
                self._save_unlinked(chunk)
        
        return linked
    
    def _is_verse_reference(self, line: str) -> bool:
        """هل هذا السطر يشير لبداية تفسير آية؟"""
        return any(re.search(pattern, line) for pattern in self.VERSE_PATTERNS)
    
    def _clean_ocr_artifacts(self, text: str) -> str:
        """تنظيف أخطاء OCR الشائعة في النصوص العربية"""
        # إزالة الأحرف اللاتينية المتطفلة
        text = re.sub(r'[a-zA-Z]{1,2}(?=\s|$)', '', text)
        # توحيد المسافات
        text = re.sub(r'\s+', ' ', text)
        # إصلاح الهمزات الشائعة في OCR
        text = text.replace('ا', 'ا')
        return text.strip()
    
    async def _save_to_db(self, linked_chunks: list, volume_num: int):
        """حفظ المقاطع المرتبطة في جدول tafseers"""
        async with self.quran_db.transaction():
            for chunk in linked_chunks:
                await self.quran_db.execute("""
                    INSERT INTO tafseers (verse_id, book_id, text, page_ref, metadata)
                    VALUES ($1, $2, $3, $4, $5)
                    ON CONFLICT (verse_id, book_id) DO UPDATE
                    SET text = EXCLUDED.text
                """, 
                chunk["verse_id"], chunk["book_id"], chunk["text"],
                chunk["page_ref"],
                json.dumps({
                    "volume": volume_num,
                    "source_note": chunk["source_note"],
                    "citation_format": chunk["citation_format"]
                }))
```

---
# ═══════════════════════════════════════════
# القسم الرابع: قاعدة البيانات الشاملة
# ═══════════════════════════════════════════

## 4.1 مخطط قاعدة البيانات الكامل

```sql
-- ══════════════════════════════════════════
-- تفعيل الامتدادات
-- ══════════════════════════════════════════
CREATE EXTENSION IF NOT EXISTS vector;        -- للبحث الدلالي
CREATE EXTENSION IF NOT EXISTS pg_trgm;       -- للبحث بالنص
CREATE EXTENSION IF NOT EXISTS unaccent;      -- للعربية
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";   -- للمعرّفات

-- ══════════════════════════════════════════
-- السور والآيات (النواة الأساسية)
-- ══════════════════════════════════════════

CREATE TABLE surahs (
    id                  SERIAL PRIMARY KEY,
    number              SMALLINT UNIQUE NOT NULL CHECK (number BETWEEN 1 AND 114),
    name_arabic         VARCHAR(50)  NOT NULL,
    name_english        VARCHAR(100) NOT NULL,
    name_transliteration VARCHAR(100),
    revelation_type     VARCHAR(10)  NOT NULL CHECK (revelation_type IN ('makki', 'madani')),
    revelation_order    SMALLINT     NOT NULL,
    verse_count         SMALLINT     NOT NULL,
    word_count          INTEGER,
    letter_count        INTEGER,
    muqattaat           VARCHAR(20),
    juz_start           SMALLINT,
    page_start          SMALLINT,
    themes_ar           TEXT[],
    themes_en           TEXT[],
    summary_ar          TEXT,
    summary_en          TEXT,
    -- تحليلات مسبقة الحساب
    prime_verse_count   BOOLEAN GENERATED ALWAYS AS (
        -- هل عدد الآيات عدد أولي؟
        verse_count IN (2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,
                        61,67,71,73,79,83,89,97,101,103,107,109,113,127,
                        131,137,139,149,151,157,163,167,173,179,181,191,
                        193,197,199,211,223,227)
    ) STORED,
    fibonacci_verse_count BOOLEAN GENERATED ALWAYS AS (
        verse_count IN (1,2,3,5,8,13,21,34,55,89,144,233)
    ) STORED,
    created_at          TIMESTAMP DEFAULT NOW()
);

CREATE TABLE verses (
    id                  SERIAL PRIMARY KEY,
    surah_number        SMALLINT    NOT NULL REFERENCES surahs(number),
    verse_number        SMALLINT    NOT NULL,
    
    -- النصوص
    text_uthmani        TEXT        NOT NULL,  -- رسم عثماني كامل
    text_uthmani_tajweed TEXT,                  -- مع علامات التجويد HTML
    text_simple         TEXT        NOT NULL,  -- مبسّط
    text_clean          TEXT,                  -- بدون تشكيل
    
    -- الموقع
    juz                 SMALLINT    NOT NULL,
    hizb                SMALLINT,
    rub_el_hizb         SMALLINT,
    page_number         SMALLINT,
    
    -- خصائص
    sajda               BOOLEAN     DEFAULT FALSE,
    sajda_type          VARCHAR(20) CHECK (sajda_type IN ('wajib', 'mustahab')),
    has_waqf_mandatory  BOOLEAN     DEFAULT FALSE,
    has_waqf_prohibited BOOLEAN     DEFAULT FALSE,
    revelation_order    INTEGER,
    
    -- تصنيف
    themes_ar           TEXT[],
    themes_en           TEXT[],
    
    -- إحصاءات
    word_count          SMALLINT,
    letter_count        SMALLINT,
    unique_word_count   SMALLINT,
    
    -- تضمينات الذكاء الاصطناعي
    embedding_precise    vector(1536),  -- text-embedding-3-large
    embedding_broad      vector(1536),
    embedding_multilingual vector(1536),
    
    -- بحث نصي كامل
    search_vector       tsvector GENERATED ALWAYS AS (
        to_tsvector('simple', text_clean)
    ) STORED,
    
    UNIQUE(surah_number, verse_number)
);

-- فهارس الأداء
CREATE INDEX idx_verses_search     ON verses USING GIN(search_vector);
CREATE INDEX idx_verses_embedding  ON verses USING ivfflat(embedding_precise vector_cosine_ops)
    WITH (lists = 100);
CREATE INDEX idx_verses_surah      ON verses(surah_number);
CREATE INDEX idx_verses_juz        ON verses(juz);

-- ══════════════════════════════════════════
-- التحليل الصرفي للكلمات
-- ══════════════════════════════════════════

CREATE TABLE words (
    id                  SERIAL PRIMARY KEY,
    verse_id            INTEGER     NOT NULL REFERENCES verses(id),
    word_position       SMALLINT    NOT NULL,
    
    -- النصوص
    arabic_text         VARCHAR(100) NOT NULL,
    arabic_normalized   VARCHAR(100),           -- بعد التطبيع
    arabic_clean        VARCHAR(100),           -- بدون تشكيل
    
    -- التحليل الصرفي (من Quranic Arabic Corpus + MASAQ)
    root                VARCHAR(20),            -- الجذر
    lemma               VARCHAR(100),           -- أصل الكلمة
    pattern             VARCHAR(50),            -- الوزن الصرفي
    pos_tag             VARCHAR(50),            -- Part of Speech
    
    -- التحليل التفصيلي (JSONB للمرونة)
    morphology          JSONB,
    /*
    مثال:
    {
      "type": "verb",
      "tense": "perfect",
      "voice": "active",
      "person": "third",
      "gender": "masculine",
      "number": "singular",
      "form": "IV",
      "derived_from": "ك-ت-ب"
    }
    */
    
    -- الترجمة
    english_gloss       VARCHAR(200),
    arabic_gloss        TEXT,
    
    -- إحصاءات
    frequency_in_quran  INTEGER,    -- تكرار هذه الكلمة في القرآن كله
    frequency_in_surah  SMALLINT,   -- تكرارها في هذه السورة
    
    embedding           vector(768), -- AraBERT embedding للكلمة
    
    UNIQUE(verse_id, word_position)
);

CREATE INDEX idx_words_root   ON words(root);
CREATE INDEX idx_words_clean  ON words(arabic_clean);
CREATE INDEX idx_words_lemma  ON words(lemma);

-- ══════════════════════════════════════════
-- التفاسير والترجمات
-- ══════════════════════════════════════════

CREATE TABLE tafseer_books (
    id              SERIAL PRIMARY KEY,
    slug            VARCHAR(50) UNIQUE,
    name_ar         VARCHAR(200),
    name_en         VARCHAR(200),
    author_ar       VARCHAR(200),
    author_death_year INTEGER,      -- هجري
    methodology     VARCHAR(100),   -- أثري/عقلي/علمي/اجتماعي/إصلاحي
    is_available    BOOLEAN DEFAULT TRUE,
    priority_order  SMALLINT        -- ترتيب الأولوية للعرض
);

INSERT INTO tafseer_books (slug, name_ar, author_ar, author_death_year, methodology, priority_order) VALUES
    ('ibn-katheer',  'تفسير ابن كثير',         'إسماعيل بن كثير',  774, 'أثري',      1),
    ('al-tabari',    'جامع البيان (الطبري)',    'ابن جرير الطبري',  310, 'أثري',      2),
    ('al-razi',      'مفاتيح الغيب (الرازي)',   'فخر الدين الرازي', 606, 'عقلي',      3),
    ('al-saadi',     'تفسير السعدي',            'عبد الرحمن السعدي',1376,'تيسيري',   4),
    ('ibn-ashour',   'التحرير والتنوير',        'ابن عاشور',        1393,'إصلاحي',   5),
    ('al-qurtubi',   'الجامع لأحكام القرآن',    'القرطبي',          671, 'فقهي',      6);

CREATE TABLE tafseers (
    id          SERIAL PRIMARY KEY,
    verse_id    INTEGER REFERENCES verses(id),
    book_id     INTEGER REFERENCES tafseer_books(id),
    text        TEXT    NOT NULL,
    page_ref    VARCHAR(50),
    embedding   vector(1536),
    UNIQUE(verse_id, book_id)
);

CREATE TABLE translations (
    id              SERIAL PRIMARY KEY,
    verse_id        INTEGER     NOT NULL REFERENCES verses(id),
    language        VARCHAR(10) NOT NULL,
    translator      VARCHAR(200),
    text            TEXT        NOT NULL,
    embedding       vector(1536),
    INDEX idx_trans_verse_lang (verse_id, language)
);

-- ══════════════════════════════════════════
-- نظام الاكتشافات والأنماط
-- ══════════════════════════════════════════

CREATE TABLE discoveries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- المحتوى
    title_ar        TEXT NOT NULL,
    title_en        TEXT,
    description_ar  TEXT NOT NULL,
    description_en  TEXT,
    
    -- التصنيف
    category        VARCHAR(100),  -- numerical/linguistic/scientific/humanities
    discipline      VARCHAR(100),  -- physics/medicine/psychology/economics/...
    
    -- الآيات المرتبطة
    verse_ids       INTEGER[],
    
    -- درجة الثقة (نظام الثلاثة مستويات)
    confidence_tier VARCHAR(10)  NOT NULL CHECK (confidence_tier IN ('tier_1', 'tier_2', 'tier_3')),
    confidence_score DECIMAL(4,3) CHECK (confidence_score BETWEEN 0 AND 1),
    
    -- التحقق
    verification_status VARCHAR(20) DEFAULT 'pending'
        CHECK (verification_status IN ('pending', 'verified', 'disputed', 'rejected')),
    
    -- الأدلة
    evidence        JSONB,
    counter_arguments JSONB,
    sources         TEXT[],
    
    -- الإحصاء
    p_value         DECIMAL(8,6),      -- من Monte Carlo
    effect_size     DECIMAL(8,4),
    
    -- المصدر
    discovery_source VARCHAR(50)       -- 'ai_autonomous' | 'user' | 'researcher'
        DEFAULT 'ai_autonomous',
    discovered_by   UUID REFERENCES users(id),
    
    -- التفاعل
    upvotes         INTEGER DEFAULT 0,
    expert_reviews  JSONB,
    
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- الارتباطات العلمية (مفصّلة)
CREATE TABLE scientific_correlations (
    id              SERIAL PRIMARY KEY,
    verse_id        INTEGER REFERENCES verses(id),
    
    -- العلم
    field           VARCHAR(100),      -- physics, chemistry, medicine, ...
    subfield        VARCHAR(200),
    topic           VARCHAR(300),
    
    -- الاكتشاف العلمي
    scientific_claim TEXT NOT NULL,
    discovery_year  INTEGER,
    doi_reference   VARCHAR(200),
    
    -- التقييم
    confidence_tier VARCHAR(10)  CHECK (confidence_tier IN ('tier_1', 'tier_2', 'tier_3')),
    
    -- معايير التقييم السبعة
    linguistic_clarity      SMALLINT CHECK (linguistic_clarity BETWEEN 0 AND 10),
    historical_independence SMALLINT CHECK (historical_independence BETWEEN 0 AND 10),
    premodern_tafseer_support SMALLINT CHECK (premodern_tafseer_support BETWEEN 0 AND 10),
    specificity             SMALLINT CHECK (specificity BETWEEN 0 AND 10),
    falsifiability          SMALLINT CHECK (falsifiability BETWEEN 0 AND 10),
    translational_consensus SMALLINT CHECK (translational_consensus BETWEEN 0 AND 10),
    contextual_coherence    SMALLINT CHECK (contextual_coherence BETWEEN 0 AND 10),
    
    -- إجمالي النقاط
    total_score INTEGER GENERATED ALWAYS AS (
        linguistic_clarity + historical_independence + premodern_tafseer_support +
        specificity + falsifiability + translational_consensus + contextual_coherence
    ) STORED,
    
    -- اعتراضات مهمة
    main_objection  TEXT,
    ancient_knowledge_available BOOLEAN DEFAULT FALSE,
    
    verified        BOOLEAN DEFAULT FALSE,
    verified_by     VARCHAR(200)
);

-- التوازن اللغوي (الكلمات المتضادة)
CREATE TABLE word_balance (
    id              SERIAL PRIMARY KEY,
    word1_ar        VARCHAR(100) NOT NULL,
    word2_ar        VARCHAR(100) NOT NULL,
    count1          INTEGER     NOT NULL,
    count2          INTEGER     NOT NULL,
    is_equal        BOOLEAN GENERATED ALWAYS AS (count1 = count2) STORED,
    ratio           DECIMAL(10,4) GENERATED ALWAYS AS (
        CASE WHEN count2 > 0 THEN count1::DECIMAL/count2 ELSE NULL END
    ) STORED,
    significance    TEXT,
    p_value_montecarlo DECIMAL(8,6),
    effect_size     DECIMAL(8,4),
    verified        BOOLEAN DEFAULT FALSE,
    source          TEXT
);

-- ══════════════════════════════════════════
-- نظام المستخدمين والمجتمع
-- ══════════════════════════════════════════

CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    username        VARCHAR(100) UNIQUE,
    display_name    VARCHAR(200),
    
    -- التخصص والدور
    role            VARCHAR(30) DEFAULT 'user'
        CHECK (role IN ('user', 'contributor', 'scholar', 'admin')),
    specialty       VARCHAR(100),
    institution     VARCHAR(200),
    credentials     TEXT,
    
    -- التفضيلات
    preferred_tafseer VARCHAR(50) DEFAULT 'ibn-katheer',
    preferred_lang    VARCHAR(10) DEFAULT 'ar',
    expertise_areas   TEXT[],
    
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE bookmarks (
    id          SERIAL PRIMARY KEY,
    user_id     UUID REFERENCES users(id),
    verse_id    INTEGER REFERENCES verses(id),
    collection  VARCHAR(100) DEFAULT 'العامة',
    note        TEXT,
    tags        TEXT[],
    created_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, verse_id, collection)
);

CREATE TABLE research_notes (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id),
    title       VARCHAR(300),
    content     TEXT,
    verse_refs  INTEGER[],
    discovery_refs UUID[],
    is_public   BOOLEAN DEFAULT FALSE,
    tags        TEXT[],
    created_at  TIMESTAMP DEFAULT NOW(),
    updated_at  TIMESTAMP DEFAULT NOW()
);

-- جلسات الاستكشاف المحفوظة
CREATE TABLE discovery_sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id),
    title       VARCHAR(300),
    query       TEXT,
    mode        VARCHAR(30),
    disciplines TEXT[],
    results     JSONB,
    is_public   BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMP DEFAULT NOW()
);
```

---

