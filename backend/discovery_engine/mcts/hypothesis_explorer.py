"""MCTS — محرك استكشاف فضاء الفرضيات.

يستخدم Monte Carlo Tree Search لاستكشاف فرضيات بحثية قابلة للاختبار.
يعمل في الخلفية — يولّد فرضيات ويختبرها ويحتفظ بالواعدة.
"""

import json
import math
import random
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HypothesisNode:
    """عقدة في شجرة استكشاف الفرضيات."""

    hypothesis: dict
    parent: Optional["HypothesisNode"] = None
    children: list = field(default_factory=list)
    visits: int = 0
    value: float = 0.0
    verse_ids: list = field(default_factory=list)
    discipline: str = ""
    novelty_score: float = 0.0
    is_explored: bool = False

    @property
    def ucb_score(self) -> float:
        """UCB1 — التوازن بين الاستغلال والاستكشاف."""
        if self.visits == 0:
            return float("inf")
        if not self.parent:
            return self.value / self.visits
        C = 1.414
        exploitation = self.value / self.visits
        exploration = C * math.sqrt(
            math.log(self.parent.visits) / self.visits
        )
        return exploitation + exploration


class MCTSHypothesisExplorer:
    """محرك MCTS لاستكشاف فضاء الفرضيات.

    يعمل في الخلفية — يولّد فرضيات ويختبرها ويحتفظ بالواعدة.
    """

    SEED_TOPICS = [
        {"topic": "نسبية الزمن في القرآن", "discipline": "physics"},
        {"topic": "الأجنة والتطور في القرآن", "discipline": "biology"},
        {"topic": "الصحة النفسية والذكر", "discipline": "psychology"},
        {"topic": "العدالة الاقتصادية القرآنية", "discipline": "economics"},
        {"topic": "الأنظمة الاجتماعية في القرآن", "discipline": "sociology"},
        {"topic": "الكونيات والفيزياء الفلكية", "discipline": "astrophysics"},
        {"topic": "الطب الوقائي في القرآن", "discipline": "medicine"},
        {"topic": "القيادة والإدارة القرآنية", "discipline": "management"},
    ]

    def __init__(self, llm_client, db, validator):
        self.llm = llm_client
        self.db = db
        self.validator = validator
        self.root = None

    async def run_exploration(
        self,
        seed_topic: str,
        discipline: str,
        n_iterations: int = 20,
    ) -> list[dict]:
        """حلقة الاستكشاف الرئيسية."""
        # تهيئة الجذر
        self.root = HypothesisNode(
            hypothesis={"topic": seed_topic, "discipline": discipline},
            visits=1,
            value=0.5,
        )

        best_hypotheses = []

        for _i in range(n_iterations):
            # 1. الاختيار — أي عقدة نستكشف؟
            node = self._select(self.root)

            # 2. التوسع — ولّد فرضيات أبناء
            if not node.is_explored:
                children = await self._expand(node)
                node.children.extend(children)
                node.is_explored = True

            # 3. المحاكاة — قيّم الفرضية
            if node.children:
                child = random.choice(node.children)
                score = await self._simulate(child)
                self._backpropagate(child, score)

                if score > 0.6:
                    best_hypotheses.append(
                        {
                            "hypothesis": child.hypothesis,
                            "score": score,
                            "discipline": discipline,
                        }
                    )

        # أعد أفضل 5 فرضيات
        return sorted(
            best_hypotheses,
            key=lambda x: x["score"],
            reverse=True,
        )[:5]

    def _select(self, node: HypothesisNode) -> HypothesisNode:
        """اختر العقدة الأعلى UCB score."""
        current = node
        while current.children:
            unexplored = [c for c in current.children if c.visits == 0]
            if unexplored:
                return random.choice(unexplored)
            current = max(current.children, key=lambda c: c.ucb_score)
        return current

    async def _expand(
        self, node: HypothesisNode
    ) -> list[HypothesisNode]:
        """ولّد فرضيات جديدة باستخدام Claude."""
        topic = node.hypothesis.get("topic", "")
        discipline = node.hypothesis.get("discipline", "")

        response = await self.llm.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=1500,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "أنت باحث متخصص في الإعجاز القرآني.\n"
                        f"الموضوع: {topic}\n"
                        f"التخصص: {discipline}\n"
                        "ولّد 3 فرضيات بحثية محددة وقابلة للاختبار.\n"
                        "لكل فرضية:\n"
                        "- hypothesis_ar: الفرضية بالعربية\n"
                        "- verse_hint: اقتراح آية قرآنية مرتبطة\n"
                        "- testability: كيف يمكن اختبارها؟ (0-1)\n"
                        "- novelty: مدى الجدة (0-1)\n"
                        "- main_objection: أقوى اعتراض عليها\n"
                        'أجب بـ JSON فقط: [{{"hypothesis_ar": ..., '
                        '"verse_hint": ..., "testability": ..., '
                        '"novelty": ..., "main_objection": ...}}]'
                    ),
                }
            ],
            temperature=0.7,
        )

        try:
            text = response.content[0].text
            # استخرج JSON
            match = re.search(r"\[.*\]", text, re.DOTALL)
            if not match:
                return []
            hypotheses = json.loads(match.group())
            return [
                HypothesisNode(
                    hypothesis=h,
                    parent=node,
                    discipline=discipline,
                    novelty_score=h.get("novelty", 0.5),
                )
                for h in hypotheses
            ]
        except Exception:
            return []

    async def _simulate(self, node: HypothesisNode) -> float:
        """قيّم الفرضية — اجمع درجة من 0 إلى 1."""
        h = node.hypothesis
        testability = float(h.get("testability", 0.5))
        novelty = float(h.get("novelty", 0.5))

        # درجة مركّبة
        return (testability * 0.6) + (novelty * 0.4)

    def _backpropagate(self, node: HypothesisNode, score: float):
        """ارفع النتيجة للأعلى في الشجرة."""
        current = node
        while current:
            current.visits += 1
            current.value += score
            current = current.parent
