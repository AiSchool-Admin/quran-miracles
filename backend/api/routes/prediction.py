"""Predictive engine API routes — توليد الفرضيات واستكشاف MCTS."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from discovery_engine.mcts.hypothesis_explorer import MCTSHypothesisExplorer
from discovery_engine.prediction.abductive_engine import AbductiveReasoningEngine
from discovery_engine.prediction.research_navigator import ResearchNavigator
from discovery_engine.prediction.statistical_safeguards import StatisticalSafeguards

router = APIRouter()


@router.post("/generate")
async def generate_predictions(request: Request, body: dict):
    """توليد فرضيات بحثية من آيات قرآنية.

    Input:  { verses: [...], discipline: "physics" }
    Output: { predictions: [...], research_maps: [...] }
    """
    raw_verses = body.get("verses", [])
    discipline = body.get("discipline", "physics")

    # تحويل النصوص إلى dicts إذا أرسل الـ frontend نصوصاً
    verses: list[dict] = []
    for v in raw_verses:
        if isinstance(v, str):
            verses.append({"text_uthmani": v, "text": v})
        elif isinstance(v, dict):
            verses.append(v)

    # التحقق من توفر LLM client
    llm = getattr(request.app.state, "llm", None)
    if llm is None:
        return JSONResponse(
            {"error": "LLM client غير متاح", "predictions": [], "research_maps": [], "total": 0},
            status_code=503,
        )

    # تهيئة المحركات
    validator = StatisticalSafeguards()
    engine = AbductiveReasoningEngine(llm, validator)
    navigator = ResearchNavigator()

    try:
        # توليد الفرضيات
        predictions = await engine.generate_predictions(
            verses, discipline, max_hypotheses=5
        )
    except (TypeError, Exception) as exc:
        # TypeError عند غياب API key، أو أي خطأ آخر من الـ LLM
        return JSONResponse(
            {
                "error": f"خطأ في محرك التنبؤ: {exc}",
                "predictions": [],
                "research_maps": [],
                "total": 0,
            },
            status_code=503,
        )

    # توليد خرائط البحث
    research_maps = [
        await navigator.generate_research_map(p) for p in predictions
    ]

    return JSONResponse(
        {
            "predictions": [p.model_dump() for p in predictions],
            "research_maps": research_maps,
            "total": len(predictions),
            "disclaimer": (
                "هذه فرضيات آلية — لم تُراجَع بشرياً بعد. "
                "كل فرضية تحمل مستواها الإحصائي وخارطة التحقق منها."
            ),
        }
    )


@router.post("/mcts/explore")
async def mcts_explore(request: Request, body: dict):
    """استكشاف MCTS على موضوع محدد.

    Input:  { topic: "...", discipline: "..." }
    Output: { best_hypotheses: [...] }
    """
    topic = body.get("topic", "")
    discipline = body.get("discipline", "physics")

    explorer = MCTSHypothesisExplorer(
        request.app.state.llm,
        request.app.state.db,
        StatisticalSafeguards(),
    )

    best = await explorer.run_exploration(
        topic, discipline, n_iterations=20
    )

    return JSONResponse(
        {
            "best_hypotheses": best,
            "topic": topic,
            "discipline": discipline,
            "iterations": 20,
        }
    )
