"""Apply database schema to PostgreSQL.

Uses raw SQL from schema.sql (which includes pgvector, all tables, and seed data)
instead of SQLAlchemy metadata, since schema.sql is the source of truth.
"""

import asyncio
import os
from pathlib import Path

import asyncpg


async def apply_schema() -> None:
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://localhost:5432/quran_miracles",
    )

    schema_path = Path(__file__).parent.parent / "database" / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")

    conn = await asyncpg.connect(database_url)
    try:
        await conn.execute(sql)
        print("Schema applied successfully.")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(apply_schema())
