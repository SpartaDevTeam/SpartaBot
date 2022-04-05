import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.ext.asyncio.session import AsyncSession

from .models import Base

engine: AsyncEngine = create_async_engine(os.environ["DB_URI"])
async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)


async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close():
    await engine.dispose()
