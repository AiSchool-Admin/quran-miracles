"""LangGraph state definitions for the discovery engine."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DiscoveryState:
    """State passed between LangGraph nodes during discovery."""

    query: str = ""
    surah: int | None = None
    verse: int | None = None

    # Results from each agent
    quran_context: dict[str, Any] = field(default_factory=dict)
    linguistic_analysis: dict[str, Any] = field(default_factory=dict)
    scientific_correlations: list[dict[str, Any]] = field(default_factory=list)
    humanities_connections: list[dict[str, Any]] = field(default_factory=list)
    tafseer_insights: list[dict[str, Any]] = field(default_factory=list)
    pattern_results: dict[str, Any] = field(default_factory=dict)

    # Synthesis
    synthesis: dict[str, Any] = field(default_factory=dict)
    confidence_tier: str = "tier_0"
    objections: list[str] = field(default_factory=list)

    # Control flow
    should_deepen: bool = False
    iteration: int = 0
    max_iterations: int = 3
