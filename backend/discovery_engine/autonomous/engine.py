"""المحرك المستقل — يعمل 24/7 في الخلفية.

الجدول الزمني:
- كل ساعة: فحص الأبحاث العلمية الجديدة (arXiv, Semantic Scholar)
- كل 6 ساعات: MCTS على موضوع جديد
- يومياً الساعة 2 صباحاً: مسح الأنماط العددية الشامل
- أسبوعياً (الأحد 8 صباحاً): تقرير الاكتشافات الأسبوعي
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from datetime import datetime
from typing import Any

import httpx


class AutonomousEngine:
    """محرك الاستكشاف المستقل — يعمل بدون تدخل بشري.

    يجمع بين:
    - فحص الأبحاث الجديدة من arXiv و Semantic Scholar
    - استكشاف MCTS للفرضيات الجديدة
    - مسح الأنماط العددية في القرآن
    - تقارير أسبوعية بالاكتشافات
    """

    SEARCH_QUERIES = [
        "embryology stages development",
        "water origin life biology",
        "universe expansion cosmology",
        "mountains isostasy geology",
        "deep sea darkness oceanography",
        "iron meteorite origin",
        "fingerprint uniqueness forensics",
        "barrier between seas oceanography",
        "atmospheric pressure altitude",
        "honey antimicrobial properties",
        "sleep neuroscience circadian rhythm",
        "pain receptors skin burn",
    ]

    def __init__(self, db: Any = None, llm: Any = None):
        self.db = db
        self.llm = llm

    # ── فحص الأبحاث العلمية ────────────────────────────

    async def check_new_papers(
        self, queries: list[str] | None = None, max_results: int = 5
    ) -> list[dict]:
        """فحص الأبحاث الجديدة من arXiv و Semantic Scholar."""
        search_queries = queries or self.SEARCH_QUERIES
        all_papers: list[dict] = []

        async with httpx.AsyncClient(timeout=30) as client:
            for query in search_queries[:6]:
                arxiv_papers = await self._search_arxiv(
                    client, query, max_results
                )
                all_papers.extend(arxiv_papers)

                ss_papers = await self._search_semantic_scholar(
                    client, query, max_results
                )
                all_papers.extend(ss_papers)

        seen_titles: set[str] = set()
        unique_papers = []
        for p in all_papers:
            title_lower = p["title"].lower()
            if title_lower not in seen_titles:
                seen_titles.add(title_lower)
                unique_papers.append(p)

        if self.db and unique_papers:
            await self._save_papers_to_db(unique_papers)

        print(f"📄 وُجد {len(unique_papers)} بحث جديد")
        return unique_papers

    async def _search_arxiv(
        self, client: httpx.AsyncClient, query: str, max_results: int
    ) -> list[dict]:
        """البحث في arXiv API."""
        url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        try:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return []

            entries = re.findall(
                r"<entry>(.*?)</entry>", resp.text, re.DOTALL
            )
            papers = []
            for entry in entries:
                title_m = re.search(r"<title>(.*?)</title>", entry, re.DOTALL)
                summary_m = re.search(r"<summary>(.*?)</summary>", entry, re.DOTALL)
                link_m = re.search(r"<id>(.*?)</id>", entry)
                pub_m = re.search(r"<published>(.*?)</published>", entry)

                if title_m and summary_m:
                    papers.append({
                        "title": title_m.group(1).strip().replace("\n", " "),
                        "abstract": summary_m.group(1).strip().replace("\n", " ")[:500],
                        "url": link_m.group(1) if link_m else "",
                        "published": pub_m.group(1) if pub_m else "",
                        "source": "arXiv",
                        "search_query": query,
                    })
            return papers
        except Exception as e:
            print(f"⚠️ arXiv search failed for '{query}': {e}")
            return []

    async def _search_semantic_scholar(
        self, client: httpx.AsyncClient, query: str, max_results: int
    ) -> list[dict]:
        """البحث في Semantic Scholar API."""
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query,
            "limit": max_results,
            "fields": "title,abstract,url,year,citationCount",
        }

        try:
            resp = await client.get(url, params=params)
            if resp.status_code != 200:
                return []

            data = resp.json()
            papers = []
            for p in data.get("data", []):
                if p.get("title") and p.get("abstract"):
                    papers.append({
                        "title": p["title"],
                        "abstract": p["abstract"][:500],
                        "url": p.get("url", ""),
                        "year": p.get("year"),
                        "citations": p.get("citationCount", 0),
                        "source": "Semantic Scholar",
                        "search_query": query,
                    })
            return papers
        except Exception as e:
            print(f"⚠️ Semantic Scholar failed for '{query}': {e}")
            return []

    async def _save_papers_to_db(self, papers: list[dict]) -> None:
        """حفظ الأبحاث في قاعدة البيانات."""
        if not self.db or not hasattr(self.db, "pool") or not self.db.pool:
            return
        for paper in papers[:20]:
            try:
                await self.db.pool.execute(
                    """
                    INSERT INTO scientific_correlations
                        (field, subfield, topic, scientific_claim, doi_reference,
                         confidence_tier)
                    VALUES ($1, $2, $3, $4, $5, 'tier_1')
                    ON CONFLICT DO NOTHING
                    """,
                    paper.get("search_query", "general"),
                    paper.get("source", ""),
                    paper["title"],
                    paper["abstract"],
                    paper.get("url", ""),
                )
            except Exception:
                pass

    # ── استكشاف MCTS ──────────────────────────────────

    async def run_mcts_exploration(
        self, topic: str | None = None, discipline: str | None = None
    ) -> dict:
        """تشغيل جلسة MCTS على موضوع."""
        if not self.llm:
            return {"error": "LLM client not available"}

        from discovery_engine.mcts.explorer import MCTSExplorer
        from discovery_engine.prediction.statistical_safeguards import (
            StatisticalSafeguards,
        )

        explorer = MCTSExplorer(self.llm, self.db, StatisticalSafeguards())

        if topic and discipline:
            result = await explorer.explore_and_save(
                topic, discipline, n_iterations=20, min_score=0.7
            )
        else:
            results = await explorer.explore_multiple(n_iterations=10)
            result = {
                "topics_explored": len(results),
                "total_hypotheses": sum(r["hypothesis_count"] for r in results),
                "results": results[:5],
            }

        print(f"🔍 MCTS: {result.get('hypothesis_count', result.get('topics_explored', 0))} فرضية")
        return result

    # ── مسح الأنماط العددية ────────────────────────────

    async def scan_numerical_patterns(self) -> list[dict]:
        """مسح شامل للأنماط العددية في القرآن.

        يبحث عن:
        1. تكرارات الكلمات المتساوية (يوم/أيام، حياة/موت)
        2. الأعداد الأولية في هيكل السور
        3. أنماط رقم 19
        """
        patterns: list[dict] = []

        if not self.db or not hasattr(self.db, "pool") or not self.db.pool:
            return await self._scan_from_files()

        word_pairs = await self._check_word_balance()
        patterns.extend(word_pairs)

        surah_patterns = await self._check_surah_patterns()
        patterns.extend(surah_patterns)

        number_patterns = await self._check_number_patterns()
        patterns.extend(number_patterns)

        if patterns:
            await self._save_patterns_to_db(patterns)

        print(f"🔢 وُجد {len(patterns)} نمط عددي")
        return patterns

    async def _scan_from_files(self) -> list[dict]:
        """مسح من ملفات JSON المحلية عندما تكون DB غير متاحة."""
        from pathlib import Path

        data_dir = Path(__file__).parent.parent.parent.parent / "data" / "quran"
        patterns: list[dict] = []

        try:
            complete_file = data_dir / "quran_complete.json"
            if not complete_file.exists():
                return patterns

            all_verses = json.loads(complete_file.read_text(encoding="utf-8"))
            all_text = " ".join(
                v.get("text_clean", "") for v in all_verses if v.get("text_clean")
            )
            words = all_text.split()
            word_counts = Counter(words)

            check_pairs = [
                ("حياة", "موت"), ("الدنيا", "الآخرة"),
                ("ملائكة", "شياطين"), ("الجنة", "النار"),
            ]

            for w1, w2 in check_pairs:
                c1 = sum(c for w, c in word_counts.items() if w1 in w)
                c2 = sum(c for w, c in word_counts.items() if w2 in w)
                if c1 > 0 and c2 > 0:
                    patterns.append({
                        "type": "word_balance",
                        "word1": w1, "word2": w2,
                        "count1": c1, "count2": c2,
                        "is_equal": c1 == c2,
                        "ratio": round(c1 / c2, 4) if c2 > 0 else None,
                    })
        except Exception as e:
            print(f"⚠️ File scan error: {e}")

        return patterns

    async def _check_word_balance(self) -> list[dict]:
        """فحص تساوي الكلمات المتقابلة من DB."""
        patterns: list[dict] = []
        pool = self.db.pool

        check_pairs = [
            ("حياة", "موت"), ("الدنيا", "الآخرة"),
            ("ملائكة", "شياطين"), ("الجنة", "النار"),
            ("قل", "قالوا"),
        ]

        for w1, w2 in check_pairs:
            try:
                c1 = await pool.fetchval(
                    "SELECT COUNT(*) FROM verses WHERE text_clean LIKE '%' || $1 || '%'",
                    w1,
                )
                c2 = await pool.fetchval(
                    "SELECT COUNT(*) FROM verses WHERE text_clean LIKE '%' || $1 || '%'",
                    w2,
                )
                if c1 > 0 and c2 > 0:
                    patterns.append({
                        "type": "word_balance",
                        "word1": w1, "word2": w2,
                        "count1": c1, "count2": c2,
                        "is_equal": c1 == c2,
                        "ratio": round(c1 / c2, 4) if c2 > 0 else None,
                    })
            except Exception:
                pass
        return patterns

    async def _check_surah_patterns(self) -> list[dict]:
        """فحص أنماط هيكل السور."""
        patterns: list[dict] = []
        pool = self.db.pool

        try:
            rows = await pool.fetch(
                "SELECT number, verse_count FROM surahs ORDER BY number"
            )
            prime_surahs = [r["number"] for r in rows if _is_prime(r["verse_count"])]
            patterns.append({
                "type": "surah_structure",
                "pattern": "prime_verse_count",
                "surahs": prime_surahs,
                "count": len(prime_surahs),
            })

            total = sum(r["verse_count"] for r in rows)
            patterns.append({
                "type": "surah_structure",
                "pattern": "total_verses",
                "value": total,
            })
        except Exception:
            pass
        return patterns

    async def _check_number_patterns(self) -> list[dict]:
        """فحص أنماط الأرقام."""
        patterns: list[dict] = []
        pool = self.db.pool

        try:
            row = await pool.fetchrow(
                """
                SELECT text_clean, LENGTH(REPLACE(text_clean, ' ', '')) as char_count
                FROM verses WHERE surah_number = 1 AND verse_number = 1
                """
            )
            if row:
                patterns.append({
                    "type": "letter_count",
                    "verse": "1:1",
                    "char_count": row["char_count"],
                })
        except Exception:
            pass
        return patterns

    async def _save_patterns_to_db(self, patterns: list[dict]) -> None:
        """حفظ الأنماط في جدول word_balance."""
        if not self.db or not hasattr(self.db, "pool") or not self.db.pool:
            return
        pool = self.db.pool
        for p in patterns:
            if p.get("type") == "word_balance":
                try:
                    await pool.execute(
                        """
                        INSERT INTO word_balance
                            (word1_ar, word2_ar, count1, count2, significance)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT DO NOTHING
                        """,
                        p["word1"], p["word2"], p["count1"], p["count2"],
                        "متساوي" if p.get("is_equal") else "",
                    )
                except Exception:
                    pass

    # ── التقرير الأسبوعي ──────────────────────────────

    async def generate_weekly_report(self) -> dict:
        """توليد تقرير أسبوعي بالاكتشافات."""
        report: dict[str, Any] = {
            "generated_at": datetime.utcnow().isoformat(),
            "period": "weekly",
        }

        if not self.db or not hasattr(self.db, "pool") or not self.db.pool:
            report["status"] = "database_unavailable"
            return report

        pool = self.db.pool

        try:
            discovery_count = await pool.fetchval(
                "SELECT COUNT(*) FROM discoveries WHERE created_at > NOW() - INTERVAL '7 days'"
            )
            report["new_discoveries"] = discovery_count

            top_discoveries = await pool.fetch(
                """
                SELECT id, title_ar, confidence_tier, confidence_score
                FROM discoveries
                WHERE created_at > NOW() - INTERVAL '7 days'
                ORDER BY confidence_score DESC NULLS LAST LIMIT 5
                """
            )
            report["top_discoveries"] = [dict(r) for r in top_discoveries]

            pattern_count = await pool.fetchval("SELECT COUNT(*) FROM word_balance")
            report["numerical_patterns"] = pattern_count

            report["status"] = "success"
        except Exception as e:
            report["status"] = "partial"
            report["error"] = str(e)

        print(f"📊 التقرير الأسبوعي: {report.get('new_discoveries', 0)} اكتشاف جديد")
        return report


def _is_prime(n: int) -> bool:
    """هل العدد أولي؟"""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True
