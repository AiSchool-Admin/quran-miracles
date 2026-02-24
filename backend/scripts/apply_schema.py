"""Apply database schema to PostgreSQL.

Uses raw SQL from schema.sql (which includes pgvector, all tables, and seed data)
instead of SQLAlchemy metadata, since schema.sql is the source of truth.

Includes retry logic for CI environments where PostgreSQL may still be starting.
"""

import asyncio
import os
import sys
from pathlib import Path

import asyncpg


async def apply_schema(max_retries: int = 5, base_delay: float = 2.0) -> None:
    database_url = os.environ.get(
        "DATABASE_URL",
        "postgresql://localhost:5432/quran_miracles",
    )

    schema_path = Path(__file__).parent.parent / "database" / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")

    conn: asyncpg.Connection | None = None
    for attempt in range(1, max_retries + 1):
        try:
            conn = await asyncio.wait_for(
                asyncpg.connect(database_url),
                timeout=10,
            )
            break
        except Exception as exc:
            if attempt == max_retries:
                print(f"Failed to connect after {max_retries} attempts: {exc}")
                sys.exit(1)
            delay = base_delay * (2 ** (attempt - 1))
            print(f"Connection attempt {attempt} failed: {exc}. Retrying in {delay}s...")
            await asyncio.sleep(delay)

    assert conn is not None
    try:
        await conn.execute(sql)
        print("Schema applied successfully.")
    except Exception as exc:
        print(f"Schema application failed: {exc}")
        sys.exit(1)
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(apply_schema())
