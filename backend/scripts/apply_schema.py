"""Apply database schema to PostgreSQL."""

import asyncio
import os

from sqlalchemy.ext.asyncio import create_async_engine

from database.models import Base


async def apply_schema():
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://localhost:5432/quran_miracles",
    )
    engine = create_async_engine(database_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    print("Schema applied successfully.")


if __name__ == "__main__":
    asyncio.run(apply_schema())
