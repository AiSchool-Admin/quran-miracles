"""معجزات القرآن الكريم — FastAPI Application Entry Point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import discovery, quran, prediction


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="معجزات القرآن الكريم API",
    description="AI Discovery Platform for Quranic Miracles",
    version="0.1.0",
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
