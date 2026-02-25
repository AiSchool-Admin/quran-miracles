"""LangGraph workflow definition for the discovery engine.

Flow:
  route_query → quran_rag → linguistic ─┬→ science
                                         ├→ tafseer
                                         └→ humanities
                                           ↓
                                        synthesis → quality_review
                                           ↓
                            [Conditional: deepen_search or kg_update]
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


# ── Node functions ─────────────────────────────────────────


async def route_query(state: DiscoveryState) -> DiscoveryState:
    """Route incoming query — classify type and set defaults."""
    updates: DiscoveryState = {}
    if not state.get("disciplines"):
        updates["disciplines"] = ["physics", "biology", "psychology"]
    if not state.get("mode"):
        updates["mode"] = "guided"
    if not state.get("iteration_count"):
        updates["iteration_count"] = 0

    # Classify query type using the router agent
    router = RouteQueryAgent()
    effective_state = {**state, **updates}
    route = router.route(effective_state)

    updates["streaming_updates"] = state.get("streaming_updates", []) + [
        {"stage": "route_query", "status": "done", "route": route}
    ]
    return updates


async def quran_rag_node(state: DiscoveryState) -> DiscoveryState:
    """Retrieve Quranic context using RAG."""
    agent = QuranRAGAgent()
    result = await agent.search(state.get("query", ""), state)
    return {
        "verses": result.get("verses", []),
        "streaming_updates": state.get("streaming_updates", [])
        + [{"stage": "quran_rag", "status": "done", "verse_count": len(result.get("verses", []))}],
    }


async def linguistic_node(state: DiscoveryState) -> DiscoveryState:
    """Perform morphological and rhetorical analysis."""
    agent = LinguisticAnalysisAgent()
    result = await agent.analyze(state.get("verses", []), state)
    return {
        "linguistic_analysis": result,
        "streaming_updates": state.get("streaming_updates", [])
        + [{"stage": "linguistic", "status": "done"}],
    }


async def science_node(state: DiscoveryState) -> DiscoveryState:
    """Find scientific correlations across disciplines."""
    agent = ScientificExplorerAgent()
    disciplines = state.get("disciplines", ["physics", "biology"])
    context = {
        "verses": state.get("verses", []),
        "tafseer_context": "",
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
    """Gather tafseer insights from 7 references."""
    agent = TafseerAgent()
    result = await agent.analyze(state.get("verses", []), state)
    return {
        "tafseer_findings": result,
        "streaming_updates": state.get("streaming_updates", [])
        + [{"stage": "tafseer", "status": "done"}],
    }


async def humanities_node(state: DiscoveryState) -> DiscoveryState:
    """Analyze humanities connections."""
    agent = HumanitiesAgent()
    context = {
        "verses": state.get("verses", []),
        "tafseer_context": "",
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
    """Synthesize findings from all agents."""
    agent = SynthesisAgent()
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
    for t in ("tier_1", "tier_3"):
        if t in result:
            tier = t
            break

    return {
        "synthesis": result,
        "confidence_tier": tier,
        "streaming_updates": state.get("streaming_updates", [])
        + [{"stage": "synthesis", "status": "done"}],
    }


async def quality_review_node(state: DiscoveryState) -> DiscoveryState:
    """Review quality and decide whether to deepen."""
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
    """Update knowledge graph (placeholder for Neo4j integration)."""
    return {
        "streaming_updates": state.get("streaming_updates", [])
        + [{"stage": "kg_update", "status": "done"}],
    }


def should_deepen(state: DiscoveryState) -> str:
    """Conditional edge: decide whether to deepen search or finalize."""
    if state.get("should_deepen") and state.get("iteration_count", 0) < _MAX_ITERATIONS:
        return "deepen"
    return "complete"


# ── Graph builder ──────────────────────────────────────────


def build_discovery_graph():
    """Build and compile the LangGraph StateGraph.

    Returns a compiled graph with MemorySaver checkpointer.
    """
    try:
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph.graph import END, StateGraph
    except ImportError:
        # LangGraph not installed — return a simple callable wrapper
        return _FallbackGraph()

    graph = StateGraph(DiscoveryState)

    # Add nodes
    graph.add_node("route_query", route_query)
    graph.add_node("quran_rag", quran_rag_node)
    graph.add_node("linguistic", linguistic_node)
    graph.add_node("science", science_node)
    graph.add_node("tafseer", tafseer_node)
    graph.add_node("humanities", humanities_node)
    graph.add_node("synthesis", synthesis_node)
    graph.add_node("quality_review", quality_review_node)
    graph.add_node("kg_update", kg_update_node)

    # Set entry point
    graph.set_entry_point("route_query")

    # Sequential edges
    graph.add_edge("route_query", "quran_rag")
    graph.add_edge("quran_rag", "linguistic")

    # Parallel edges: after linguistic → science, tafseer, humanities
    graph.add_edge("linguistic", "science")
    graph.add_edge("linguistic", "tafseer")
    graph.add_edge("linguistic", "humanities")

    # All three converge to synthesis
    graph.add_edge("science", "synthesis")
    graph.add_edge("tafseer", "synthesis")
    graph.add_edge("humanities", "synthesis")

    # synthesis → quality_review
    graph.add_edge("synthesis", "quality_review")

    # Conditional: quality_review → deepen (back to quran_rag) or complete
    graph.add_conditional_edges(
        "quality_review",
        should_deepen,
        {
            "deepen": "quran_rag",
            "complete": "kg_update",
        },
    )

    # kg_update → END
    graph.add_edge("kg_update", END)

    # Compile with checkpointer
    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)


class _FallbackGraph:
    """Simple fallback when LangGraph is not installed.

    Runs nodes sequentially to allow testing without langgraph dependency.
    """

    async def ainvoke(
        self, state: DiscoveryState, config: dict | None = None
    ) -> DiscoveryState:
        """Run all nodes sequentially."""
        result: dict[str, Any] = dict(state)

        for node_fn in (route_query, quran_rag_node, linguistic_node):
            updates = await node_fn(result)  # type: ignore[arg-type]
            result.update(updates)

        # parallel: science, tafseer, humanities
        _state = cast(DiscoveryState, result)
        sci, taf, hum = await asyncio.gather(
            science_node(_state),
            tafseer_node(_state),
            humanities_node(_state),
        )
        # Merge results carefully — concatenate streaming_updates
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

        for node_fn in (synthesis_node, quality_review_node, kg_update_node):
            updates = await node_fn(result)  # type: ignore[arg-type]
            result.update(updates)

        return cast(DiscoveryState, result)
