"""Database connection management — PostgreSQL + Neo4j + Redis."""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from api.deps import get_settings


settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncSession:  # type: ignore[misc]
    """Get async database session."""
    async with async_session() as session:
        yield session
