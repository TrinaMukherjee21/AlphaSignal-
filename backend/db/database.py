import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/trade_sentiment").strip().strip('"').strip("'")

engine = create_async_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"ssl": "require"},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

import logging

_db_logger = logging.getLogger("db.database")

async def get_db():
    """
    Yield an async DB session. Errors in cleanup (commit/rollback/close)
    are logged but never re-raised — this prevents FastAPI from replacing
    a successful 200 response with a 500 due to a post-yield exception.
    """
    session = AsyncSessionLocal()
    try:
        yield session
        try:
            await session.commit()
        except Exception as e:
            _db_logger.error(f"DB commit failed (non-fatal, route already responded): {e}")
            try:
                await session.rollback()
            except Exception as rb_err:
                _db_logger.error(f"DB rollback failed: {rb_err}")
    except Exception as e:
        # Exception thrown INTO the generator by FastAPI (route raised).
        # Log it, attempt rollback, but do NOT re-raise.
        _db_logger.error(f"DB session error: {e}")
        try:
            await session.rollback()
        except Exception as rb_err:
            _db_logger.error(f"DB rollback failed: {rb_err}")
    finally:
        try:
            await session.close()
        except Exception as e:
            _db_logger.error(f"DB close failed: {e}")

async def init_db():
    # Import Base and models here to avoid circular imports and ensure models are registered
    from db.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
