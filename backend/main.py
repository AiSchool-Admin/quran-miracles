"""معجزات القرآن الكريم — FastAPI Application Entry Point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.deps import get_settings
from api.routes import discovery, prediction, quran
from arabic_nlp.embeddings_service import EmbeddingsService
from database.service import DatabaseService
from discovery_engine.core.graph import build_discovery_graph


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # ── Startup ─────────────────────────────────────────────
    settings = get_settings()

    # Database service
    db = DatabaseService(settings.database_url)
    await db.connect()
    app.state.db = db

    # Embeddings service
    embeddings = EmbeddingsService()
    await embeddings.initialize(settings.database_url)
    app.state.embeddings = embeddings

    # Build LangGraph with injected services
    app.state.graph = build_discovery_graph(db=db, embeddings=embeddings)

    print("✅ المحرك جاهز — DB + Embeddings متصلان")

    yield

    # ── Shutdown ─────────────────────────────────────────────
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
