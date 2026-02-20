from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.core.config import settings, get_async_database_url

engine = create_async_engine(get_async_database_url(), echo=settings.DEBUG)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    """Yield an async database session. Injected via Depends(get_db) in routes."""
    async with AsyncSessionLocal() as session:
        yield session
