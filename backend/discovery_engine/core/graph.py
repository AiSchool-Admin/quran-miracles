"""LangGraph workflow definition for the discovery engine.

Flow:
  route_query → quran_rag → linguistic ─┬→ science
                                         ├→ tafseer
                                         └→ humanities
                                           ↓
                                        synthesis → quality_review
                                           ↓
                            [Conditional: deepen or kg_update → END]

Services (DatabaseService, EmbeddingsService) are injected via
build_discovery_graph() and captured in closures.
"""

from __future__ import annotations

import asyncio
from typing import Any, cast

from discovery_engine.agents.humanities import HumanitiesAgent
from discovery_engine.agents.linguistic import LinguisticAnalysisAgent
from discovery_engine.agents.quality_review import QualityReviewAgent
from discovery_engine.agents.quran_rag import QuranRAGAgent
from discovery_engine.agents.router import RouteQueryAgent
from discovery_engine.agents.scientific import ScientificExplorerAgent
from discovery_engine.agents.synthesis import SynthesisAgent
from discovery_engine.agents.tafseer import TafseerAgent
from discovery_engine.core.state import DiscoveryState

# Maximum iterations for the deepen loop
_MAX_ITERATIONS = 3


# ── Node factory ──────────────────────────────────────────────


def _make_nodes(db: Any = None, embeddings: Any = None) -> dict:
    """Create node functions with injected services.

    Returns a dict of {name: async_function} for each graph node.
    """

    async def route_query(state: DiscoveryState) -> DiscoveryState:
        updates: DiscoveryState = {}
        if not state.get("disciplines"):
            updates["disciplines"] = ["physics", "biology", "psychology"]
        if not state.get("mode"):
            updates["mode"] = "guided"
        if not state.get("iteration_count"):
            updates["iteration_count"] = 0

        router = RouteQueryAgent()
        effective_state = {**state, **updates}
        route = router.route(effective_state)

        updates["streaming_updates"] = state.get("streaming_updates", []) + [
            {"stage": "route_query", "status": "done", "route": route}
        ]
        return updates

    async def quran_rag_node(state: DiscoveryState) -> DiscoveryState:
        agent = QuranRAGAgent(db=db, embeddings=embeddings)
        result = await agent.search(state.get("query", ""), state)
        return {
            "verses": result.get("verses", []),
            "tafseer_context": result.get("tafseer_context", {}),
            "streaming_updates": state.get("streaming_updates", [])
            + [
                {
                    "stage": "quran_rag",
                    "status": "done",
                    "source": result.get("source", "unknown"),
                    "verse_count": len(result.get("verses", [])),
                }
            ],
        }

    async def linguistic_node(state: DiscoveryState) -> DiscoveryState:
        agent = LinguisticAnalysisAgent()
        result = await agent.analyze(state.get("verses", []), state)
        return {
            "linguistic_analysis": result,
            "streaming_updates": state.get("streaming_updates", [])
            + [{"stage": "linguistic", "status": "done"}],
        }

    async def science_node(state: DiscoveryState) -> DiscoveryState:
        agent = ScientificExplorerAgent()
        disciplines = state.get("disciplines", ["physics", "biology"])
        context = {
            "verses": state.get("verses", []),
            "tafseer_context": state.get("tafseer_context", ""),
        }

        all_findings: list[dict] = []
        tasks = [
            agent.explore(state.get("query", ""), d, context)
            for d in disciplines
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for r in results:
            if isinstance(r, list):
                all_findings.extend(r)

        return {
            "science_findings": all_findings,
            "streaming_updates": state.get("streaming_updates", [])
            + [{"stage": "science", "status": "done", "finding_count": len(all_findings)}],
        }

    async def tafseer_node(state: DiscoveryState) -> DiscoveryState:
        agent = TafseerAgent(db=db)
        result = await agent.analyze(state.get("verses", []), state)
        return {
            "tafseer_findings": result,
            "streaming_updates": state.get("streaming_updates", [])
            + [{"stage": "tafseer", "status": "done"}],
        }

    async def humanities_node(state: DiscoveryState) -> DiscoveryState:
        agent = HumanitiesAgent()
        context = {
            "verses": state.get("verses", []),
            "tafseer_context": state.get("tafseer_context", ""),
        }
        disciplines = state.get("disciplines", ["psychology", "sociology"])
        result = await agent.analyze(
            state.get("verses", []), context, disciplines
        )
        return {
            "humanities_findings": result,
            "streaming_updates": state.get("streaming_updates", [])
            + [{"stage": "humanities", "status": "done", "finding_count": len(result)}],
        }

    async def synthesis_node(state: DiscoveryState) -> DiscoveryState:
        agent = SynthesisAgent(db=db)
        all_findings = {
            "verses": state.get("verses", []),
            "linguistic_analysis": state.get("linguistic_analysis", {}),
            "science_findings": state.get("science_findings", []),
            "tafseer_findings": state.get("tafseer_findings", {}),
            "humanities_findings": state.get("humanities_findings", []),
        }
        result = await agent.synthesize(all_findings, state)

        # Extract confidence_tier from synthesis text
        tier = "tier_2"  # default
        synthesis_text = result.get("synthesis", "") if isinstance(result, dict) else result
        for t in ("tier_1", "tier_3"):
            if t in str(synthesis_text):
                tier = t
                break

        if isinstance(result, dict):
            return {
                "synthesis": result.get("synthesis", ""),
                "confidence_tier": result.get("confidence_tier", tier),
                "discovery_id": result.get("discovery_id"),
                "streaming_updates": state.get("streaming_updates", [])
                + [{"stage": "synthesis", "status": "done"}],
            }

        return {
            "synthesis": result,
            "confidence_tier": tier,
            "streaming_updates": state.get("streaming_updates", [])
            + [{"stage": "synthesis", "status": "done"}],
        }

    async def quality_review_node(state: DiscoveryState) -> DiscoveryState:
        agent = QualityReviewAgent()
        result = await agent.review(state)
        iteration = state.get("iteration_count", 0) + 1
        return {
            "quality_score": result["quality_score"],
            "quality_issues": result["quality_issues"],
            "should_deepen": result["should_deepen"] and iteration < _MAX_ITERATIONS,
            "iteration_count": iteration,
            "streaming_updates": state.get("streaming_updates", [])
            + [
                {
                    "stage": "quality_review",
                    "status": "done",
                    "quality_score": result["quality_score"],
                    "should_deepen": result["should_deepen"],
                }
            ],
        }

    async def kg_update_node(state: DiscoveryState) -> DiscoveryState:
        return {
            "streaming_updates": state.get("streaming_updates", [])
            + [{"stage": "kg_update", "status": "done"}],
        }

    return {
        "route_query": route_query,
        "quran_rag": quran_rag_node,
        "linguistic": linguistic_node,
        "science": science_node,
        "tafseer": tafseer_node,
        "humanities": humanities_node,
        "synthesis": synthesis_node,
        "quality_review": quality_review_node,
        "kg_update": kg_update_node,
    }


def should_deepen(state: DiscoveryState) -> str:
    """Conditional edge: decide whether to deepen search or finalize."""
    if state.get("should_deepen") and state.get("iteration_count", 0) < _MAX_ITERATIONS:
        return "deepen"
    return "complete"


# ── Graph builder ──────────────────────────────────────────


def build_discovery_graph(db: Any = None, embeddings: Any = None):
    """Build and compile the LangGraph StateGraph.

    Args:
        db: optional DatabaseService instance (shared pool).
        embeddings: optional EmbeddingsService instance.

    Returns a compiled graph with MemorySaver checkpointer.
    """
    nodes = _make_nodes(db=db, embeddings=embeddings)

    try:
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph.graph import END, StateGraph
    except ImportError:
        return _FallbackGraph(nodes)

    graph = StateGraph(DiscoveryState)

    for name, fn in nodes.items():
        graph.add_node(name, fn)

    graph.set_entry_point("route_query")

    graph.add_edge("route_query", "quran_rag")
    graph.add_edge("quran_rag", "linguistic")

    # Parallel: linguistic → science, tafseer, humanities
    graph.add_edge("linguistic", "science")
    graph.add_edge("linguistic", "tafseer")
    graph.add_edge("linguistic", "humanities")

    # Converge to synthesis
    graph.add_edge("science", "synthesis")
    graph.add_edge("tafseer", "synthesis")
    graph.add_edge("humanities", "synthesis")

    graph.add_edge("synthesis", "quality_review")

    graph.add_conditional_edges(
        "quality_review",
        should_deepen,
        {
            "deepen": "quran_rag",
            "complete": "kg_update",
        },
    )

    graph.add_edge("kg_update", END)

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


class _FallbackGraph:
    """Simple fallback when LangGraph is not installed."""

    def __init__(self, nodes: dict) -> None:
        self._nodes = nodes

    async def ainvoke(
        self, state: DiscoveryState, config: dict | None = None
    ) -> DiscoveryState:
        result: dict[str, Any] = dict(state)
        n = self._nodes

        for fn_name in ("route_query", "quran_rag", "linguistic"):
            updates = await n[fn_name](result)
            result.update(updates)

        _state = cast(DiscoveryState, result)
        sci, taf, hum = await asyncio.gather(
            n["science"](_state),
            n["tafseer"](_state),
            n["humanities"](_state),
        )
        base_updates = list(result.get("streaming_updates", []))
        for partial in (sci, taf, hum):
            for key, val in partial.items():
                if key == "streaming_updates" and isinstance(val, list):
                    for u in val:
                        if u not in base_updates:
                            base_updates.append(u)
                else:
                    result[key] = val
        result["streaming_updates"] = base_updates

        for fn_name in ("synthesis", "quality_review", "kg_update"):
            updates = await n[fn_name](result)
            result.update(updates)

        return cast(DiscoveryState, result)
