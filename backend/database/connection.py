"""Database connection management — asyncpg pool + pgvector.

Uses raw asyncpg for connection pooling and pgvector support.
Provides get_db() for FastAPI dependency injection.
"""

import asyncpg
from pgvector.asyncpg import register_vector

from api.deps import get_settings

_pool: asyncpg.Pool | None = None


def _get_dsn() -> str:
    """Convert SQLAlchemy-style URL to asyncpg DSN."""
    url = get_settings().database_url
    # asyncpg expects postgresql:// not postgresql+asyncpg://
    return url.replace("postgresql+asyncpg://", "postgresql://")


async def init_pool(min_size: int = 5, max_size: int = 20) -> asyncpg.Pool:
    """Initialize the asyncpg connection pool with pgvector support."""
    global _pool
    if _pool is not None:
        return _pool

    _pool = await asyncpg.create_pool(
        dsn=_get_dsn(),
        min_size=min_size,
        max_size=max_size,
        init=_init_connection,
    )
    return _pool


async def _init_connection(conn: asyncpg.Connection) -> None:
    """Per-connection initialization: register pgvector type."""
    await register_vector(conn)


async def close_pool() -> None:
    """Close the connection pool gracefully."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def get_pool() -> asyncpg.Pool:
    """Get or create the connection pool."""
    global _pool
    if _pool is None:
        _pool = await init_pool()
    return _pool


async def get_db() -> asyncpg.Connection:
    """FastAPI dependency: acquire a connection from the pool.

    Usage:
        @router.get("/example")
        async def example(db = Depends(get_db)):
            rows = await db.fetch("SELECT * FROM surahs")
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn


async def apply_schema(schema_path: str | None = None) -> None:
    """Apply schema.sql to the database."""
    from pathlib import Path

    if schema_path is None:
        schema_path = str(Path(__file__).parent / "schema.sql")

    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()

    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(sql)
