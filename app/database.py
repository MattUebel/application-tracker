import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL is None:
    # Provide a default only if not set, and ensure it matches async driver
    DATABASE_URL = "postgresql+asyncpg://user:password@db/apptrackerdb"

# Use create_async_engine for an asynchronous engine
engine = create_async_engine(DATABASE_URL, echo=False) # Set echo=True for debugging SQL

# Use AsyncSession for the session_maker
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()

# Dependency to get ASYNC DB session
async def get_db() -> AsyncSession: # Marked as async, returns AsyncSession
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback() # Rollback on exception
            raise
        finally:
            await session.close() # Close session in async context 