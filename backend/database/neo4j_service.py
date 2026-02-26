"""Neo4j Knowledge Graph Service — شبكة المعرفة القرآنية.

يبني ويدير رسم بياني يربط:
- السور والآيات (علاقات ترتيبية وموضوعية)
- الكلمات والجذور (علاقات صرفية)
- التفاسير (علاقات مرجعية)
- الاكتشافات (علاقات علمية)
- الموضوعات (علاقات دلالية)

التشغيل يتطلب Neo4j 5.x:
    docker run -d --name neo4j -p 7474:7474 -p 7687:7687 neo4j:5

الاستخدام:
    service = Neo4jService()
    await service.connect()
    await service.populate_from_db(postgres_db)
"""

from __future__ import annotations

import os
from typing import Any

from neo4j import AsyncGraphDatabase


class Neo4jService:
    """خدمة Neo4j لشبكة المعرفة القرآنية."""

    def __init__(self, uri: str | None = None, auth: tuple | None = None):
        self.uri = uri or os.environ.get("NEO4J_URI", "bolt://localhost:7687")
        self.auth = auth or (
            os.environ.get("NEO4J_USER", "neo4j"),
            os.environ.get("NEO4J_PASSWORD", "changeme"),
        )
        self.driver = None

    async def connect(self) -> None:
        """إنشاء اتصال بقاعدة Neo4j."""
        self.driver = AsyncGraphDatabase.driver(self.uri, auth=self.auth)
        # اختبار الاتصال
        async with self.driver.session() as session:
            await session.run("RETURN 1")
        print("✅ Neo4j connected")

    async def close(self) -> None:
        """إغلاق الاتصال."""
        if self.driver:
            await self.driver.close()

    # ── إنشاء المخطط ──────────────────────────────────

    async def create_schema(self) -> None:
        """إنشاء الفهارس والقيود."""
        constraints = [
            "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Surah) REQUIRE s.number IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (v:Verse) REQUIRE v.verse_key IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (w:Root) REQUIRE w.root IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Topic) REQUIRE t.name IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Discovery) REQUIRE d.id IS UNIQUE",
            "CREATE CONSTRAINT IF NOT EXISTS FOR (b:TafseerBook) REQUIRE b.slug IS UNIQUE",
        ]

        indexes = [
            "CREATE INDEX IF NOT EXISTS FOR (v:Verse) ON (v.surah_number)",
            "CREATE INDEX IF NOT EXISTS FOR (v:Verse) ON (v.text_clean)",
            "CREATE INDEX IF NOT EXISTS FOR (d:Discovery) ON (d.discipline)",
            "CREATE INDEX IF NOT EXISTS FOR (d:Discovery) ON (d.confidence_tier)",
        ]

        async with self.driver.session() as session:
            for stmt in constraints + indexes:
                await session.run(stmt)

        print("✅ Neo4j schema created")

    # ── ملء البيانات من PostgreSQL ─────────────────────

    async def populate_from_db(self, pg_db: Any) -> dict:
        """ملء شبكة المعرفة من قاعدة PostgreSQL.

        Args:
            pg_db: DatabaseService instance (asyncpg pool)

        Returns:
            Dict with counts of created nodes/relationships
        """
        stats = {"surahs": 0, "verses": 0, "relationships": 0}

        pool = pg_db.pool
        if not pool:
            return {"error": "PostgreSQL not connected"}

        async with self.driver.session() as session:
            # 1. السور
            surahs = await pool.fetch(
                "SELECT number, name_arabic, name_english, revelation_type, verse_count FROM surahs ORDER BY number"
            )
            for s in surahs:
                await session.run(
                    """
                    MERGE (s:Surah {number: $number})
                    SET s.name_arabic = $name_arabic,
                        s.name_english = $name_english,
                        s.revelation_type = $revelation_type,
                        s.verse_count = $verse_count
                    """,
                    number=s["number"],
                    name_arabic=s["name_arabic"],
                    name_english=s["name_english"],
                    revelation_type=s["revelation_type"],
                    verse_count=s["verse_count"],
                )
                stats["surahs"] += 1

            # علاقات الترتيب بين السور
            for i in range(len(surahs) - 1):
                await session.run(
                    """
                    MATCH (s1:Surah {number: $n1}), (s2:Surah {number: $n2})
                    MERGE (s1)-[:FOLLOWED_BY]->(s2)
                    """,
                    n1=surahs[i]["number"],
                    n2=surahs[i + 1]["number"],
                )
                stats["relationships"] += 1

            # 2. الآيات (بدفعات)
            total_verses = await pool.fetchval("SELECT COUNT(*) FROM verses")
            batch_size = 500
            offset = 0

            while offset < total_verses:
                verses = await pool.fetch(
                    """
                    SELECT surah_number, verse_number, text_clean, themes_ar
                    FROM verses
                    ORDER BY surah_number, verse_number
                    LIMIT $1 OFFSET $2
                    """,
                    batch_size,
                    offset,
                )

                for v in verses:
                    verse_key = f"{v['surah_number']}:{v['verse_number']}"
                    await session.run(
                        """
                        MERGE (v:Verse {verse_key: $verse_key})
                        SET v.surah_number = $surah_number,
                            v.verse_number = $verse_number,
                            v.text_clean = $text_clean
                        WITH v
                        MATCH (s:Surah {number: $surah_number})
                        MERGE (s)-[:CONTAINS]->(v)
                        """,
                        verse_key=verse_key,
                        surah_number=v["surah_number"],
                        verse_number=v["verse_number"],
                        text_clean=v["text_clean"] or "",
                    )
                    stats["verses"] += 1
                    stats["relationships"] += 1

                    # ربط الموضوعات
                    themes = v.get("themes_ar") or []
                    for theme in themes:
                        await session.run(
                            """
                            MERGE (t:Topic {name: $theme})
                            WITH t
                            MATCH (v:Verse {verse_key: $verse_key})
                            MERGE (v)-[:HAS_TOPIC]->(t)
                            """,
                            theme=theme,
                            verse_key=verse_key,
                        )
                        stats["relationships"] += 1

                offset += batch_size
                print(f"  📊 {min(offset, total_verses)}/{total_verses} آية")

            # 3. الاكتشافات
            discoveries = await pool.fetch(
                """
                SELECT id::text, title_ar, discipline, confidence_tier,
                       confidence_score, verse_ids
                FROM discoveries
                LIMIT 1000
                """
            )
            for d in discoveries:
                await session.run(
                    """
                    MERGE (disc:Discovery {id: $id})
                    SET disc.title = $title,
                        disc.discipline = $discipline,
                        disc.confidence_tier = $tier,
                        disc.confidence_score = $score
                    """,
                    id=d["id"],
                    title=d["title_ar"],
                    discipline=d["discipline"],
                    tier=d["confidence_tier"],
                    score=float(d["confidence_score"]) if d["confidence_score"] else 0,
                )

                # ربط بالآيات
                verse_ids = d.get("verse_ids") or []
                for vid in verse_ids:
                    verse_row = await pool.fetchrow(
                        "SELECT surah_number, verse_number FROM verses WHERE id = $1",
                        vid,
                    )
                    if verse_row:
                        verse_key = f"{verse_row['surah_number']}:{verse_row['verse_number']}"
                        await session.run(
                            """
                            MATCH (disc:Discovery {id: $disc_id}),
                                  (v:Verse {verse_key: $verse_key})
                            MERGE (disc)-[:RELATES_TO]->(v)
                            """,
                            disc_id=d["id"],
                            verse_key=verse_key,
                        )
                        stats["relationships"] += 1

        print(f"✅ Neo4j populated: {stats}")
        return stats

    # ── استعلامات ──────────────────────────────────────

    async def find_related_verses(
        self, verse_key: str, max_depth: int = 2
    ) -> list[dict]:
        """البحث عن آيات مرتبطة عبر شبكة المعرفة."""
        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (v:Verse {verse_key: $verse_key})-[:HAS_TOPIC]->(t:Topic)
                    <-[:HAS_TOPIC]-(related:Verse)
                WHERE related.verse_key <> $verse_key
                RETURN DISTINCT related.verse_key AS verse_key,
                       related.text_clean AS text,
                       COLLECT(t.name) AS shared_topics
                LIMIT 20
                """,
                verse_key=verse_key,
            )
            return [dict(r) async for r in result]

    async def find_discoveries_for_verse(
        self, verse_key: str
    ) -> list[dict]:
        """البحث عن اكتشافات مرتبطة بآية."""
        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (v:Verse {verse_key: $verse_key})<-[:RELATES_TO]-(d:Discovery)
                RETURN d.id AS id, d.title AS title,
                       d.discipline AS discipline,
                       d.confidence_tier AS tier
                ORDER BY d.confidence_score DESC
                LIMIT 10
                """,
                verse_key=verse_key,
            )
            return [dict(r) async for r in result]

    async def get_topic_network(self, topic: str) -> dict:
        """شبكة موضوع — الآيات والاكتشافات المرتبطة."""
        async with self.driver.session() as session:
            result = await session.run(
                """
                MATCH (t:Topic {name: $topic})<-[:HAS_TOPIC]-(v:Verse)
                OPTIONAL MATCH (v)<-[:RELATES_TO]-(d:Discovery)
                RETURN v.verse_key AS verse_key,
                       v.text_clean AS text,
                       COLLECT(DISTINCT {id: d.id, title: d.title}) AS discoveries
                LIMIT 50
                """,
                topic=topic,
            )
            verses = [dict(r) async for r in result]
            return {
                "topic": topic,
                "verse_count": len(verses),
                "verses": verses,
            }

    async def get_graph_stats(self) -> dict:
        """إحصائيات شبكة المعرفة."""
        async with self.driver.session() as session:
            counts = {}
            for label in ["Surah", "Verse", "Topic", "Discovery", "Root"]:
                result = await session.run(
                    f"MATCH (n:{label}) RETURN COUNT(n) AS count"
                )
                record = await result.single()
                counts[label.lower() + "s"] = record["count"] if record else 0

            rel_result = await session.run(
                "MATCH ()-[r]->() RETURN COUNT(r) AS count"
            )
            rel_record = await rel_result.single()
            counts["relationships"] = rel_record["count"] if rel_record else 0

            return counts
