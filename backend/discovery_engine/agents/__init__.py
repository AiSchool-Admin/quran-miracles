"""Eight specialized agents for the discovery engine."""

from discovery_engine.agents.humanities import HumanitiesAgent
from discovery_engine.agents.linguistic import LinguisticAnalysisAgent
from discovery_engine.agents.quality_review import QualityReviewAgent
from discovery_engine.agents.quran_rag import QuranRAGAgent
from discovery_engine.agents.router import RouteQueryAgent
from discovery_engine.agents.scientific import ScientificExplorerAgent
from discovery_engine.agents.synthesis import SynthesisAgent
from discovery_engine.agents.tafseer import TafseerAgent

__all__ = [
    "HumanitiesAgent",
    "LinguisticAnalysisAgent",
    "QualityReviewAgent",
    "QuranRAGAgent",
    "RouteQueryAgent",
    "ScientificExplorerAgent",
    "SynthesisAgent",
    "TafseerAgent",
]
