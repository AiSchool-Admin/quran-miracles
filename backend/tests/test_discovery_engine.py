"""Tests for the LangGraph multi-agent discovery engine.

Test query: "الماء في القرآن الكريم" (Water in the Holy Quran)
Disciplines: ["physics", "biology", "psychology"]

All tests run without external APIs — agents fall back to mock data.
"""

import importlib.util

import pytest

from discovery_engine.agents.humanities import HumanitiesAgent
from discovery_engine.agents.linguistic import LinguisticAnalysisAgent
from discovery_engine.agents.quality_review import QualityReviewAgent
from discovery_engine.agents.quran_rag import QuranRAGAgent
from discovery_engine.agents.scientific import ScientificExplorerAgent
from discovery_engine.agents.synthesis import SynthesisAgent
from discovery_engine.agents.tafseer import TafseerAgent
from discovery_engine.core.graph import build_discovery_graph
from discovery_engine.core.state import DiscoveryState

_has_fastapi = importlib.util.find_spec("fastapi") is not None

_QUERY = "الماء في القرآن الكريم"
_DISCIPLINES = ["physics", "biology", "psychology"]


# ═══════════════════════════════════════════════════════════════
# 1. QuranRAGAgent
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_quran_rag_agent():
    agent = QuranRAGAgent()
    state: DiscoveryState = {"query": _QUERY}
    result = await agent.search(_QUERY, state)

    assert "verses" in result
    assert "tafseer_context" in result
    assert len(result["verses"]) > 0

    verse = result["verses"][0]
    assert "verse_key" in verse
    assert "text_uthmani" in verse
    assert "surah_number" in verse
    assert "verse_number" in verse

    # Verify mock returns water-related verses
    verse_keys = [v["verse_key"] for v in result["verses"]]
    assert "21:30" in verse_keys


# ═══════════════════════════════════════════════════════════════
# 2. LinguisticAnalysisAgent
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_linguistic_agent():
    # Get verses first
    rag = QuranRAGAgent()
    state: DiscoveryState = {"query": _QUERY}
    rag_result = await rag.search(_QUERY, state)
    verses = rag_result["verses"]

    agent = LinguisticAnalysisAgent()
    result = await agent.analyze(verses, state)

    assert "roots" in result
    assert "morphology" in result
    assert "rhetorical_devices" in result
    assert len(result["roots"]) > 0
    assert isinstance(result["morphology"], dict)

    # Check roots contain Arabic root patterns
    for root in result["roots"]:
        assert isinstance(root, str)
        assert len(root) > 0


@pytest.mark.asyncio
async def test_linguistic_agent_empty_verses():
    agent = LinguisticAnalysisAgent()
    state: DiscoveryState = {"query": _QUERY}
    result = await agent.analyze([], state)

    assert result == {"roots": [], "morphology": {}, "rhetorical_devices": []}


# ═══════════════════════════════════════════════════════════════
# 3. ScientificExplorerAgent
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_scientific_agent():
    rag = QuranRAGAgent()
    state: DiscoveryState = {"query": _QUERY}
    rag_result = await rag.search(_QUERY, state)

    agent = ScientificExplorerAgent()
    context = {
        "verses": rag_result["verses"],
        "tafseer_context": rag_result["tafseer_context"],
    }
    result = await agent.explore(_QUERY, "biology", context)

    assert isinstance(result, list)
    assert len(result) > 0

    finding = result[0]
    assert "verse_key" in finding
    assert "scientific_claim" in finding
    assert "confidence_tier" in finding
    assert "main_objection" in finding
    assert "pre_islamic_knowledge" in finding

    # Confidence tier must be valid
    assert finding["confidence_tier"] in ("tier_1", "tier_2", "tier_3")


# ═══════════════════════════════════════════════════════════════
# 4. TafseerAgent
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_tafseer_agent():
    rag = QuranRAGAgent()
    state: DiscoveryState = {"query": _QUERY}
    rag_result = await rag.search(_QUERY, state)
    verses = rag_result["verses"]

    agent = TafseerAgent()
    result = await agent.analyze(verses, state)

    assert "consensus_view" in result
    assert "differences" in result
    assert "shaarawy_linguistic_note" in result
    assert "tafseer_details" in result

    assert isinstance(result["consensus_view"], str)
    assert len(result["consensus_view"]) > 0
    assert isinstance(result["differences"], list)
    assert isinstance(result["shaarawy_linguistic_note"], str)
    assert len(result["shaarawy_linguistic_note"]) > 0


@pytest.mark.asyncio
async def test_tafseer_agent_empty_verses():
    agent = TafseerAgent()
    state: DiscoveryState = {"query": _QUERY}
    result = await agent.analyze([], state)

    assert result["consensus_view"] == ""
    assert result["differences"] == []


# ═══════════════════════════════════════════════════════════════
# 5. HumanitiesAgent
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_humanities_agent():
    rag = QuranRAGAgent()
    state: DiscoveryState = {"query": _QUERY}
    rag_result = await rag.search(_QUERY, state)

    agent = HumanitiesAgent()
    context = {
        "verses": rag_result["verses"],
        "tafseer_context": rag_result["tafseer_context"],
    }
    result = await agent.analyze(rag_result["verses"], context, _DISCIPLINES)

    assert isinstance(result, list)
    assert len(result) > 0

    finding = result[0]
    assert "verse_key" in finding
    assert "correlation_type" in finding
    assert "intellectual_honesty_note" in finding

    # Correlation type must be valid
    assert finding["correlation_type"] in (
        "intersecting",
        "parallel",
        "inspirational",
    )


# ═══════════════════════════════════════════════════════════════
# 6. SynthesisAgent
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_synthesis_agent():
    state: DiscoveryState = {"query": _QUERY}

    all_findings: dict = {
        "verses": [{"verse_key": "21:30", "text_simple": "mock"}],
        "linguistic_analysis": {"roots": ["م-و-ه"], "morphology": {}, "rhetorical_devices": []},
        "science_findings": [
            {
                "verse_key": "21:30",
                "confidence_tier": "tier_2",
                "scientific_claim": "mock",
                "main_objection": "mock",
            }
        ],
        "tafseer_findings": {
            "consensus_view": "mock consensus",
            "shaarawy_linguistic_note": "mock note",
        },
        "humanities_findings": [
            {
                "verse_key": "21:30",
                "correlation_type": "parallel",
                "quranic_concept": "mock",
                "intellectual_honesty_note": "mock",
            }
        ],
    }

    agent = SynthesisAgent()
    result = await agent.synthesize(all_findings, state)

    assert isinstance(result, str)
    assert len(result) > 0
    # Synthesis should mention tier
    assert "tier_" in result


@pytest.mark.asyncio
async def test_synthesis_stream():
    state: DiscoveryState = {"query": _QUERY}

    all_findings: dict = {
        "verses": [],
        "linguistic_analysis": {},
        "science_findings": [],
        "tafseer_findings": {},
        "humanities_findings": [],
    }

    agent = SynthesisAgent()
    chunks = []
    async for chunk in agent.synthesize_stream(all_findings, state):
        chunks.append(chunk)

    assert len(chunks) > 0
    full_text = "".join(chunks)
    assert len(full_text) > 0


# ═══════════════════════════════════════════════════════════════
# 7. QualityReviewAgent
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_quality_review_agent():
    state: DiscoveryState = {
        "query": _QUERY,
        "verses": [{"verse_key": "21:30"}],
        "linguistic_analysis": {"roots": ["م-و-ه"], "morphology": {}, "rhetorical_devices": []},
        "science_findings": [
            {
                "verse_key": "21:30",
                "confidence_tier": "tier_2",
                "main_objection": "اعتراض",
            }
        ],
        "tafseer_findings": {
            "consensus_view": "إجماع",
            "shaarawy_linguistic_note": "ملاحظة",
        },
        "humanities_findings": [
            {
                "verse_key": "21:30",
                "correlation_type": "parallel",
                "intellectual_honesty_note": "ملاحظة أمانة",
            }
        ],
        "synthesis": "توليف بحثي ... confidence_tier: tier_2",
    }

    agent = QualityReviewAgent()
    result = await agent.review(state)

    assert "quality_score" in result
    assert "quality_issues" in result
    assert "should_deepen" in result
    assert 0.0 <= result["quality_score"] <= 1.0
    assert isinstance(result["quality_issues"], list)
    assert isinstance(result["should_deepen"], bool)


@pytest.mark.asyncio
async def test_quality_review_catches_missing_objection():
    state: DiscoveryState = {
        "query": _QUERY,
        "verses": [{"verse_key": "21:30"}],
        "linguistic_analysis": {"roots": ["م-و-ه"]},
        "science_findings": [
            {
                "verse_key": "21:30",
                "confidence_tier": "tier_2",
                "main_objection": "",  # Missing objection
            }
        ],
        "tafseer_findings": {
            "consensus_view": "إجماع",
            "shaarawy_linguistic_note": "ملاحظة",
        },
        "humanities_findings": [],
        "synthesis": "توليف tier_2",
    }

    agent = QualityReviewAgent()
    result = await agent.review(state)

    # Should detect missing objection
    has_objection_issue = any("اعتراض" in issue for issue in result["quality_issues"])
    assert has_objection_issue


# ═══════════════════════════════════════════════════════════════
# 8. Full Graph (end-to-end)
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_full_discovery_graph():
    """End-to-end test: run the full graph on the water query."""
    graph = build_discovery_graph()

    initial_state: DiscoveryState = {
        "query": _QUERY,
        "disciplines": _DISCIPLINES,
        "mode": "guided",
        "iteration_count": 0,
        "streaming_updates": [],
    }

    config = {"configurable": {"thread_id": "test-session-1"}}
    result = await graph.ainvoke(initial_state, config=config)

    # Verify all agent outputs are present
    assert len(result.get("verses", [])) > 0
    assert len(result.get("linguistic_analysis", {}).get("roots", [])) > 0
    assert len(result.get("science_findings", [])) > 0
    assert result.get("tafseer_findings", {}).get("consensus_view")
    assert len(result.get("humanities_findings", [])) > 0
    assert len(result.get("synthesis", "")) > 0
    assert 0.0 <= result.get("quality_score", -1) <= 1.0

    # Verify streaming updates tracked all stages
    stages = [u.get("stage") for u in result.get("streaming_updates", [])]
    assert "route_query" in stages
    assert "quran_rag" in stages
    assert "linguistic" in stages
    assert "science" in stages
    assert "tafseer" in stages
    assert "humanities" in stages
    assert "synthesis" in stages
    assert "quality_review" in stages


# ═══════════════════════════════════════════════════════════════
# 9. SSE Endpoint (via httpx)
# ═══════════════════════════════════════════════════════════════


@pytest.mark.asyncio
@pytest.mark.skipif(not _has_fastapi, reason="fastapi not installed")
async def test_discovery_stream_endpoint():
    """Test the SSE streaming endpoint."""
    from httpx import ASGITransport, AsyncClient

    from main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/discovery/stream",
            json={
                "query": _QUERY,
                "disciplines": _DISCIPLINES,
                "mode": "guided",
            },
            timeout=30.0,
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

        body = response.text
        # Should contain SSE events
        assert "event:" in body
        assert "data:" in body
        # Should have session_start and complete events
        assert "session_start" in body
        assert "complete" in body


@pytest.mark.asyncio
@pytest.mark.skipif(not _has_fastapi, reason="fastapi not installed")
async def test_discovery_explore_endpoint():
    """Test the non-streaming explore endpoint."""
    from httpx import ASGITransport, AsyncClient

    from main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/discovery/explore",
            json={
                "query": _QUERY,
                "disciplines": _DISCIPLINES,
            },
            timeout=30.0,
        )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "synthesis" in data
        assert "confidence_tier" in data
        assert "quality_score" in data
        assert data["verses_count"] > 0
        assert data["science_findings_count"] > 0
