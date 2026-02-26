"""LangGraph state definitions for the discovery engine."""

from __future__ import annotations

import operator
from typing import Annotated, Literal, TypedDict


class DiscoveryState(TypedDict, total=False):
    """Shared state passed between all LangGraph nodes.

    Uses TypedDict (not dataclass) for native LangGraph compatibility.
    ``total=False`` makes every key optional so nodes can update
    only the fields they own.
    """

    # ── Inputs ─────────────────────────────────────────────
    query: str
    mode: Literal["guided", "autonomous", "cross_domain"]
    disciplines: list[str]

    # ── Agent results ──────────────────────────────────────
    verses: list[dict]
    linguistic_analysis: dict
    science_findings: list[dict]
    tafseer_findings: dict
    humanities_findings: list[dict]

    # ── Tafseer context (from quran_rag → downstream agents) ─
    tafseer_context: str | dict

    # ── Synthesis ──────────────────────────────────────────
    synthesis: str
    quality_score: float
    quality_issues: list[str]
    confidence_tier: str
    predictions: list[dict]
    discovery_id: str | None

    # ── Control flow ───────────────────────────────────────
    should_deepen: bool
    iteration_count: int

    # ── Streaming (Annotated for concurrent node updates) ──
    streaming_updates: Annotated[list[dict], operator.add]

    # ── Error handling ─────────────────────────────────────
    error: str | None
