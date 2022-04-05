import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.ext.asyncio.session import AsyncSession

# from .models import Base

ENGINE: AsyncEngine


# async def create_tables():
#     async with engine.begin() as conn:
#         await conn.run_sync(Base.metadata.create_all)


def init_engine():
    global ENGINE
    ENGINE = create_async_engine(os.environ["DB_URI"])


async def close_db():
    global ENGINE
    await ENGINE.dispose()


def async_session() -> AsyncSession:
    global ENGINE
    return AsyncSession(ENGINE)
