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
    verses = body.get("verses", [])
    discipline = body.get("discipline", "physics")

    # تهيئة المحركات
    validator = StatisticalSafeguards()
    engine = AbductiveReasoningEngine(
        request.app.state.llm, validator
    )
    navigator = ResearchNavigator()

    # توليد الفرضيات
    predictions = await engine.generate_predictions(
        verses, discipline, max_hypotheses=5
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
