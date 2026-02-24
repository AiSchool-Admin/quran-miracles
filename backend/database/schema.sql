-- ══════════════════════════════════════════════════════════════════
-- معجزات القرآن الكريم — Database Schema
-- المرجع: CLAUDE.md → docs/05_database_schema.md
-- ══════════════════════════════════════════════════════════════════

-- ══════════════════════════════════════════
-- تفعيل الامتدادات
-- ══════════════════════════════════════════
CREATE EXTENSION IF NOT EXISTS vector;        -- pgvector: البحث الدلالي
CREATE EXTENSION IF NOT EXISTS pg_trgm;       -- البحث بالتشابه النصي
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";   -- توليد UUID

-- ══════════════════════════════════════════
-- 1. السور (surahs) — 114 سورة
-- ══════════════════════════════════════════
CREATE TABLE surahs (
    id                    SERIAL PRIMARY KEY,
    number                SMALLINT UNIQUE NOT NULL CHECK (number BETWEEN 1 AND 114),
    name_arabic           VARCHAR(50)  NOT NULL,
    name_english          VARCHAR(100) NOT NULL,
    name_transliteration  VARCHAR(100),
    revelation_type       VARCHAR(10)  NOT NULL CHECK (revelation_type IN ('makki', 'madani')),
    revelation_order      SMALLINT     NOT NULL,
    verse_count           SMALLINT     NOT NULL,
    word_count            INTEGER,
    letter_count          INTEGER,
    muqattaat             VARCHAR(20),
    juz_start             SMALLINT,
    page_start            SMALLINT,
    themes_ar             TEXT[],
    themes_en             TEXT[],
    summary_ar            TEXT,
    summary_en            TEXT,

    -- تحليلات مسبقة الحساب
    prime_verse_count     BOOLEAN GENERATED ALWAYS AS (
        verse_count IN (2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,
                        61,67,71,73,79,83,89,97,101,103,107,109,113,127,
                        131,137,139,149,151,157,163,167,173,179,181,191,
                        193,197,199,211,223,227)
    ) STORED,
    fibonacci_verse_count BOOLEAN GENERATED ALWAYS AS (
        verse_count IN (1,2,3,5,8,13,21,34,55,89,144,233)
    ) STORED,

    created_at            TIMESTAMP DEFAULT NOW()
);

-- ══════════════════════════════════════════
-- 2. الآيات (verses) — 6,236 آية
--    3 أعمدة vector بأبعاد 1536 (text-embedding-3-large)
-- ══════════════════════════════════════════
CREATE TABLE verses (
    id                     SERIAL PRIMARY KEY,
    surah_number           SMALLINT    NOT NULL REFERENCES surahs(number),
    verse_number           SMALLINT    NOT NULL,

    -- النصوص الثلاثة (القاعدة الذهبية 1)
    text_uthmani           TEXT        NOT NULL,   -- رسم عثماني كامل من tanzil.net
    text_uthmani_tajweed   TEXT,                    -- مع علامات التجويد HTML
    text_simple            TEXT        NOT NULL,   -- مبسّط
    text_clean             TEXT,                    -- بدون تشكيل

    -- الموقع
    juz                    SMALLINT    NOT NULL,
    hizb                   SMALLINT,
    rub_el_hizb            SMALLINT,
    page_number            SMALLINT,

    -- خصائص
    sajda                  BOOLEAN     DEFAULT FALSE,
    sajda_type             VARCHAR(20) CHECK (sajda_type IN ('wajib', 'mustahab')),
    has_waqf_mandatory     BOOLEAN     DEFAULT FALSE,
    has_waqf_prohibited    BOOLEAN     DEFAULT FALSE,
    revelation_order       INTEGER,

    -- تصنيف
    themes_ar              TEXT[],
    themes_en              TEXT[],

    -- إحصاءات
    word_count             SMALLINT,
    letter_count           SMALLINT,
    unique_word_count      SMALLINT,

    -- تضمينات الذكاء الاصطناعي — 3 أعمدة vector(1536)
    embedding_precise      vector(1536),   -- text-embedding-3-large (دقيق)
    embedding_broad        vector(1536),   -- text-embedding-3-large (عام)
    embedding_multilingual vector(1536),   -- text-embedding-3-large (متعدد اللغات)

    -- بحث نصي كامل (يُحدَّث تلقائياً عبر trigger)
    search_vector          tsvector,

    UNIQUE(surah_number, verse_number)
);

-- Trigger لتحديث search_vector تلقائياً عند INSERT/UPDATE
CREATE OR REPLACE FUNCTION verses_search_vector_update() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('simple', COALESCE(NEW.text_clean, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_verses_search_vector
    BEFORE INSERT OR UPDATE ON verses
    FOR EACH ROW EXECUTE FUNCTION verses_search_vector_update();

-- فهارس الأداء للآيات
CREATE INDEX idx_verses_search       ON verses USING GIN(search_vector);
CREATE INDEX idx_verses_embedding    ON verses USING hnsw(embedding_precise vector_cosine_ops);
CREATE INDEX idx_verses_surah        ON verses(surah_number);
CREATE INDEX idx_verses_juz          ON verses(juz);

-- ══════════════════════════════════════════
-- 3. الكلمات (words) — 77,430 كلمة
--    AraBERT embedding بأبعاد 768
-- ══════════════════════════════════════════
CREATE TABLE words (
    id                  SERIAL PRIMARY KEY,
    verse_id            INTEGER      NOT NULL REFERENCES verses(id),
    word_position       SMALLINT     NOT NULL,

    -- النصوص
    arabic_text         VARCHAR(100) NOT NULL,
    arabic_normalized   VARCHAR(100),            -- بعد التطبيع
    arabic_clean        VARCHAR(100),            -- بدون تشكيل

    -- التحليل الصرفي (من Quranic Arabic Corpus + CAMeL Tools)
    root                VARCHAR(20),             -- الجذر
    lemma               VARCHAR(100),            -- أصل الكلمة
    pattern             VARCHAR(50),             -- الوزن الصرفي
    pos_tag             VARCHAR(50),             -- Part of Speech

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
    frequency_in_quran  INTEGER,     -- تكرار هذه الكلمة في القرآن كله
    frequency_in_surah  SMALLINT,    -- تكرارها في هذه السورة

    -- AraBERT embedding (768 بُعد)
    embedding           vector(768),

    UNIQUE(verse_id, word_position)
);

-- فهارس الأداء للكلمات
CREATE INDEX idx_words_root          ON words(root);
CREATE INDEX idx_words_clean         ON words(arabic_clean);
CREATE INDEX idx_words_lemma         ON words(lemma);

-- ══════════════════════════════════════════
-- 4. كتب التفسير (tafseer_books) — 7 مراجع
-- ══════════════════════════════════════════
CREATE TABLE tafseer_books (
    id                SERIAL PRIMARY KEY,
    slug              VARCHAR(50) UNIQUE NOT NULL,
    name_ar           VARCHAR(200) NOT NULL,
    name_en           VARCHAR(200),
    author_ar         VARCHAR(200) NOT NULL,
    author_death_year INTEGER,           -- هجري (أو ميلادي للمعاصرين)
    methodology       VARCHAR(100) NOT NULL,
    is_available      BOOLEAN DEFAULT TRUE,
    priority_order    SMALLINT NOT NULL,  -- ترتيب الأولوية للعرض
    use_cases         TEXT[],
    created_at        TIMESTAMP DEFAULT NOW()
);

-- إدراج التفاسير السبعة بالترتيب المطلوب
INSERT INTO tafseer_books (slug, name_ar, name_en, author_ar, author_death_year, methodology, priority_order, use_cases) VALUES
    ('ibn-katheer',
     'تفسير ابن كثير',
     'Tafsir Ibn Kathir',
     'إسماعيل بن كثير',
     774,
     'أثري',
     1,
     ARRAY['المرجع الرئيسي', 'التفسير بالمأثور', 'أسباب النزول']
    ),
    ('al-tabari',
     'جامع البيان (الطبري)',
     'Jami al-Bayan (al-Tabari)',
     'ابن جرير الطبري',
     310,
     'أثري',
     2,
     ARRAY['الجمع والترجيح', 'الأقوال المتعددة', 'التفسير اللغوي المبكر']
    ),
    ('al-shaarawy',
     'تفسير الشعراوي — خواطر حول القرآن الكريم',
     'Tafsir al-Shaarawy — Reflections on the Quran',
     'محمد متولى الشعراوي',
     1998,
     'بياني-لغوي-اجتماعي',
     3,
     ARRAY['تحليل دقائق الألفاظ القرآنية', 'الأثر النفسي والاجتماعي للآيات', 'مقارنة الكلمات المتشابهة', 'ربط النص القرآني بالواقع المعاصر']
    ),
    ('al-razi',
     'مفاتيح الغيب (الرازي)',
     'Mafatih al-Ghayb (al-Razi)',
     'فخر الدين الرازي',
     606,
     'عقلي',
     4,
     ARRAY['التحليل المنطقي', 'الحجج العقلية', 'الفلسفة الإسلامية']
    ),
    ('al-saadi',
     'تفسير السعدي',
     'Tafsir al-Saadi',
     'عبد الرحمن السعدي',
     1376,
     'تيسيري',
     5,
     ARRAY['الفوائد والأحكام', 'التفسير الميسر', 'الدروس المستفادة']
    ),
    ('ibn-ashour',
     'التحرير والتنوير',
     'al-Tahrir wa al-Tanwir (Ibn Ashour)',
     'ابن عاشور',
     1393,
     'إصلاحي',
     6,
     ARRAY['التحليل اللغوي الحديث', 'مقاصد الشريعة', 'البلاغة القرآنية']
    ),
    ('al-qurtubi',
     'الجامع لأحكام القرآن',
     'al-Jami li-Ahkam al-Quran (al-Qurtubi)',
     'القرطبي',
     671,
     'فقهي',
     7,
     ARRAY['أحكام القرآن', 'الفقه المقارن', 'أسباب النزول']
    );

-- ══════════════════════════════════════════
-- 5. التفاسير (tafseers) — نصوص التفسير
-- ══════════════════════════════════════════
CREATE TABLE tafseers (
    id          SERIAL PRIMARY KEY,
    verse_id    INTEGER NOT NULL REFERENCES verses(id),
    book_id     INTEGER NOT NULL REFERENCES tafseer_books(id),
    text        TEXT    NOT NULL,
    page_ref    VARCHAR(50),
    metadata    JSONB,
    embedding   vector(1536),
    created_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE(verse_id, book_id)
);

CREATE INDEX idx_tafseers_verse  ON tafseers(verse_id);
CREATE INDEX idx_tafseers_book   ON tafseers(book_id);

-- ══════════════════════════════════════════
-- 6. الترجمات (translations)
-- ══════════════════════════════════════════
CREATE TABLE translations (
    id              SERIAL PRIMARY KEY,
    verse_id        INTEGER     NOT NULL REFERENCES verses(id),
    language        VARCHAR(10) NOT NULL,
    translator      VARCHAR(200),
    text            TEXT        NOT NULL,
    embedding       vector(1536),
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_translations_verse_lang ON translations(verse_id, language);

-- ══════════════════════════════════════════
-- 7. المستخدمون (users)
-- ══════════════════════════════════════════
CREATE TABLE users (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email             VARCHAR(255) UNIQUE NOT NULL,
    username          VARCHAR(100) UNIQUE,
    display_name      VARCHAR(200),

    -- التخصص والدور
    role              VARCHAR(30) DEFAULT 'user'
        CHECK (role IN ('user', 'contributor', 'scholar', 'admin')),
    specialty         VARCHAR(100),
    institution       VARCHAR(200),
    credentials       TEXT,

    -- التفضيلات
    preferred_tafseer VARCHAR(50) DEFAULT 'ibn-katheer',
    preferred_lang    VARCHAR(10) DEFAULT 'ar',
    expertise_areas   TEXT[],

    created_at        TIMESTAMP DEFAULT NOW()
);

-- ══════════════════════════════════════════
-- 8. الاكتشافات (discoveries)
--    confidence_tier: tier_0 إلى tier_4 (القاعدة الذهبية 2)
-- ══════════════════════════════════════════
CREATE TABLE discoveries (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- المحتوى
    title_ar            TEXT NOT NULL,
    title_en            TEXT,
    description_ar      TEXT NOT NULL,
    description_en      TEXT,

    -- التصنيف
    category            VARCHAR(100),   -- numerical/linguistic/scientific/humanities
    discipline          VARCHAR(100),   -- physics/medicine/psychology/economics/...

    -- الآيات المرتبطة
    verse_ids           INTEGER[],

    -- درجة الثقة (tier_0 إلى tier_4 — القاعدة الذهبية 2)
    confidence_tier     VARCHAR(10) NOT NULL DEFAULT 'tier_0'
        CHECK (confidence_tier IN ('tier_0', 'tier_1', 'tier_2', 'tier_3', 'tier_4')),
    confidence_score    DECIMAL(4,3) CHECK (confidence_score BETWEEN 0 AND 1),

    -- التحقق
    verification_status VARCHAR(20) DEFAULT 'pending'
        CHECK (verification_status IN ('pending', 'verified', 'disputed', 'rejected')),

    -- الأدلة والاعتراضات (الاعتراضات لا تُحذف — القاعدة الذهبية 2)
    evidence            JSONB,
    counter_arguments   JSONB,
    sources             TEXT[],

    -- الإحصاء
    p_value             DECIMAL(8,6),
    effect_size         DECIMAL(8,4),

    -- المصدر
    discovery_source    VARCHAR(50) DEFAULT 'ai_autonomous'
        CHECK (discovery_source IN ('ai_autonomous', 'user', 'researcher')),
    discovered_by       UUID REFERENCES users(id),

    -- التفاعل
    upvotes             INTEGER DEFAULT 0,
    expert_reviews      JSONB,

    created_at          TIMESTAMP DEFAULT NOW(),
    updated_at          TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_discoveries_tier     ON discoveries(confidence_tier);
CREATE INDEX idx_discoveries_category ON discoveries(category);

-- ══════════════════════════════════════════
-- 9. الارتباطات العلمية (scientific_correlations)
--    7 معايير تقييم (0-10 لكل معيار)
-- ══════════════════════════════════════════
CREATE TABLE scientific_correlations (
    id                         SERIAL PRIMARY KEY,
    verse_id                   INTEGER REFERENCES verses(id),

    -- العلم
    field                      VARCHAR(100),       -- physics, chemistry, medicine, ...
    subfield                   VARCHAR(200),
    topic                      VARCHAR(300),

    -- الاكتشاف العلمي
    scientific_claim           TEXT NOT NULL,
    discovery_year             INTEGER,
    doi_reference              VARCHAR(200),

    -- التقييم العام
    confidence_tier            VARCHAR(10) CHECK (confidence_tier IN ('tier_1', 'tier_2', 'tier_3')),

    -- المعايير السبعة (0-10 لكل معيار — المجموع من 70)
    linguistic_clarity         SMALLINT CHECK (linguistic_clarity BETWEEN 0 AND 10),
    historical_independence    SMALLINT CHECK (historical_independence BETWEEN 0 AND 10),
    premodern_tafseer_support  SMALLINT CHECK (premodern_tafseer_support BETWEEN 0 AND 10),
    specificity                SMALLINT CHECK (specificity BETWEEN 0 AND 10),
    falsifiability             SMALLINT CHECK (falsifiability BETWEEN 0 AND 10),
    translational_consensus    SMALLINT CHECK (translational_consensus BETWEEN 0 AND 10),
    contextual_coherence       SMALLINT CHECK (contextual_coherence BETWEEN 0 AND 10),

    -- إجمالي النقاط (محسوب تلقائياً)
    total_score                INTEGER GENERATED ALWAYS AS (
        COALESCE(linguistic_clarity, 0) +
        COALESCE(historical_independence, 0) +
        COALESCE(premodern_tafseer_support, 0) +
        COALESCE(specificity, 0) +
        COALESCE(falsifiability, 0) +
        COALESCE(translational_consensus, 0) +
        COALESCE(contextual_coherence, 0)
    ) STORED,

    -- اعتراضات (لا تُحذف — القاعدة الذهبية 2)
    main_objection             TEXT,
    ancient_knowledge_available BOOLEAN DEFAULT FALSE,

    verified                   BOOLEAN DEFAULT FALSE,
    verified_by                VARCHAR(200),

    created_at                 TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_correlations_verse ON scientific_correlations(verse_id);
CREATE INDEX idx_correlations_tier  ON scientific_correlations(confidence_tier);

-- ══════════════════════════════════════════
-- 10. التوازن اللغوي (word_balance)
-- ══════════════════════════════════════════
CREATE TABLE word_balance (
    id                  SERIAL PRIMARY KEY,
    word1_ar            VARCHAR(100) NOT NULL,
    word2_ar            VARCHAR(100) NOT NULL,
    count1              INTEGER      NOT NULL,
    count2              INTEGER      NOT NULL,
    is_equal            BOOLEAN GENERATED ALWAYS AS (count1 = count2) STORED,
    ratio               DECIMAL(10,4) GENERATED ALWAYS AS (
        CASE WHEN count2 > 0 THEN count1::DECIMAL / count2 ELSE NULL END
    ) STORED,
    significance        TEXT,
    p_value_montecarlo  DECIMAL(8,6),
    effect_size         DECIMAL(8,4),
    verified            BOOLEAN DEFAULT FALSE,
    source              TEXT,
    created_at          TIMESTAMP DEFAULT NOW()
);

-- ══════════════════════════════════════════
-- 11. المفضلات (bookmarks)
-- ══════════════════════════════════════════
CREATE TABLE bookmarks (
    id          SERIAL PRIMARY KEY,
    user_id     UUID    NOT NULL REFERENCES users(id),
    verse_id    INTEGER NOT NULL REFERENCES verses(id),
    collection  VARCHAR(100) DEFAULT 'العامة',
    note        TEXT,
    tags        TEXT[],
    created_at  TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, verse_id, collection)
);

-- ══════════════════════════════════════════
-- 12. ملاحظات البحث (research_notes)
-- ══════════════════════════════════════════
CREATE TABLE research_notes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id),
    title           VARCHAR(300),
    content         TEXT,
    verse_refs      INTEGER[],
    discovery_refs  UUID[],
    is_public       BOOLEAN DEFAULT FALSE,
    tags            TEXT[],
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

-- ══════════════════════════════════════════
-- 13. جلسات الاستكشاف (discovery_sessions)
-- ══════════════════════════════════════════
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
