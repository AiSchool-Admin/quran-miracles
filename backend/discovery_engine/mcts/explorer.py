"""MCTS Explorer — واجهة مبسطة لمحرك استكشاف الفرضيات.

يغلّف MCTSHypothesisExplorer بواجهة أبسط ويضيف:
- استكشاف متعدد المواضيع بالتوازي
- تصفية وترتيب النتائج
- حفظ في قاعدة البيانات
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from .hypothesis_explorer import MCTSHypothesisExplorer


class MCTSExplorer:
    """واجهة عالية المستوى لاستكشاف MCTS.

    تستخدم MCTSHypothesisExplorer داخلياً وتضيف:
    - استكشاف متوازٍ لمواضيع متعددة
    - تجميع وترتيب النتائج
    - حفظ تلقائي للاكتشافات الواعدة
    """

    DEFAULT_TOPICS = [
        {"topic": "نسبية الزمن في القرآن", "discipline": "physics"},
        {"topic": "الأجنة والتطور في القرآن", "discipline": "biology"},
        {"topic": "الصحة النفسية والذكر", "discipline": "psychology"},
        {"topic": "العدالة الاقتصادية القرآنية", "discipline": "economics"},
        {"topic": "الأنظمة الاجتماعية في القرآن", "discipline": "sociology"},
        {"topic": "الكونيات والفيزياء الفلكية", "discipline": "astrophysics"},
        {"topic": "الطب الوقائي في القرآن", "discipline": "medicine"},
        {"topic": "القيادة والإدارة القرآنية", "discipline": "management"},
        {"topic": "الماء والحياة في القرآن", "discipline": "biology"},
        {"topic": "الجبال والتوازن الأرضي", "discipline": "geology"},
        {"topic": "النوم والراحة في القرآن", "discipline": "neuroscience"},
        {"topic": "الأخلاق والسلوك الإنساني", "discipline": "ethics"},
    ]

    def __init__(self, llm_client: Any, db: Any = None, validator: Any = None):
        self.llm = llm_client
        self.db = db
        self.validator = validator

    async def explore(
        self,
        root_hypothesis: str,
        discipline: str = "general",
        n_iterations: int = 20,
    ) -> dict:
        """استكشاف فرضية واحدة باستخدام MCTS.

        Args:
            root_hypothesis: الفرضية الجذرية للاستكشاف
            discipline: التخصص العلمي
            n_iterations: عدد دورات MCTS

        Returns:
            Dict with best_hypotheses, stats, hypothesis_count
        """
        explorer = MCTSHypothesisExplorer(
            self.llm, self.db, self.validator
        )
        results = await explorer.run_exploration(
            root_hypothesis, discipline, n_iterations
        )

        return {
            "root_hypothesis": root_hypothesis,
            "discipline": discipline,
            "n_iterations": n_iterations,
            "best_hypotheses": results,
            "hypothesis_count": len(results),
            "top_score": results[0]["score"] if results else 0.0,
        }

    async def explore_multiple(
        self,
        topics: list[dict] | None = None,
        n_iterations: int = 15,
        max_concurrent: int = 3,
    ) -> list[dict]:
        """استكشاف مواضيع متعددة بالتوازي.

        Args:
            topics: قائمة المواضيع [{topic, discipline}, ...]
            n_iterations: عدد دورات MCTS لكل موضوع
            max_concurrent: أقصى عدد من الاستكشافات المتزامنة

        Returns:
            قائمة النتائج مرتبة بأفضل الدرجات
        """
        targets = topics or self.DEFAULT_TOPICS
        semaphore = asyncio.Semaphore(max_concurrent)
        all_results: list[dict] = []

        async def _explore_one(topic_info: dict) -> dict | None:
            async with semaphore:
                try:
                    return await self.explore(
                        topic_info["topic"],
                        topic_info.get("discipline", "general"),
                        n_iterations,
                    )
                except Exception as e:
                    print(f"⚠️ MCTS failed for '{topic_info['topic']}': {e}")
                    return None

        tasks = [_explore_one(t) for t in targets]
        results = await asyncio.gather(*tasks)

        for r in results:
            if r and r["hypothesis_count"] > 0:
                all_results.append(r)

        all_results.sort(key=lambda x: x["top_score"], reverse=True)
        return all_results

    async def explore_and_save(
        self,
        topic: str,
        discipline: str,
        n_iterations: int = 20,
        min_score: float = 0.7,
    ) -> dict:
        """استكشاف وحفظ النتائج الجيدة في قاعدة البيانات.

        Args:
            topic: الموضوع
            discipline: التخصص
            n_iterations: عدد الدورات
            min_score: الحد الأدنى للحفظ

        Returns:
            Dict with results and saved_count
        """
        result = await self.explore(topic, discipline, n_iterations)

        saved_count = 0
        if self.db and hasattr(self.db, "save_discovery"):
            for h in result["best_hypotheses"]:
                if h["score"] >= min_score:
                    try:
                        await self.db.save_discovery({
                            "title_ar": h["hypothesis"].get(
                                "hypothesis_ar",
                                h["hypothesis"].get("topic", topic),
                            ),
                            "description_ar": json.dumps(
                                h["hypothesis"], ensure_ascii=False
                            ),
                            "category": "prediction",
                            "discipline": discipline,
                            "confidence_tier": "tier_1",
                            "confidence_score": h["score"],
                            "verification_status": "pending",
                            "evidence": h["hypothesis"],
                        })
                        saved_count += 1
                    except Exception as e:
                        print(f"⚠️ Save failed: {e}")

        result["saved_count"] = saved_count
        return result
