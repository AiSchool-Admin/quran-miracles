"""معجزات القرآن الكريم — FastAPI Application Entry Point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import anthropic
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.deps import get_settings
from api.routes import discovery, prediction, quran
from arabic_nlp.embeddings_service import EmbeddingsService
from database.service import DatabaseService
from discovery_engine.autonomous.scheduler import AutonomousDiscoveryScheduler
from discovery_engine.core.graph import build_discovery_graph


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # ── Startup ─────────────────────────────────────────────
    settings = get_settings()
    db: DatabaseService | None = None
    embeddings: EmbeddingsService | None = None

    try:
        db = DatabaseService(settings.database_url)
        await db.connect()
        app.state.db = db
        print("✅ Database connected")
    except Exception as exc:
        print(f"⚠️ Database unavailable — running in degraded mode: {exc}")
        app.state.db = None

    try:
        if db is not None:
            embeddings = EmbeddingsService()
            await embeddings.initialize(settings.database_url)
            app.state.embeddings = embeddings
            print("✅ Embeddings loaded")
        else:
            app.state.embeddings = None
            print("⚠️ Embeddings skipped — no database")
    except Exception as exc:
        print(f"⚠️ Embeddings unavailable: {exc}")
        app.state.embeddings = None

    # Build LangGraph — works with or without services
    app.state.graph = build_discovery_graph(
        db=app.state.db, embeddings=app.state.embeddings
    )
    print("✅ المحرك جاهز — LangGraph initialized")

    # Anthropic LLM client for prediction engine
    try:
        app.state.llm = anthropic.AsyncAnthropic(
            api_key=settings.anthropic_api_key or None
        )
        print("✅ Anthropic client initialized")
    except Exception as exc:
        print(f"⚠️ Anthropic client unavailable: {exc}")
        app.state.llm = None

    # Autonomous discovery scheduler (MCTS background jobs)
    try:
        scheduler = AutonomousDiscoveryScheduler(
            engine=app.state.graph,
            db=app.state.db,
        )
        scheduler.start()
        app.state.scheduler = scheduler
    except Exception as exc:
        print(f"⚠️ Autonomous scheduler unavailable: {exc}")
        app.state.scheduler = None

    yield

    # ── Shutdown ─────────────────────────────────────────────
    if hasattr(app.state, "scheduler") and app.state.scheduler:
        app.state.scheduler.scheduler.shutdown(wait=False)
    if db is not None:
        await db.close()


app = FastAPI(
    title="معجزات القرآن الكريم API",
    description="AI Discovery Platform for Quranic Miracles",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(quran.router, prefix="/api/quran", tags=["quran"])
app.include_router(discovery.router, prefix="/api/discovery", tags=["discovery"])
app.include_router(prediction.router, prefix="/api/prediction", tags=["prediction"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
