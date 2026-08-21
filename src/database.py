import os
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from .models import Base

inside_docker = os.path.exists('/.dockerenv')

DB_USER=os.getenv('POSTGRES_USER')
DB_PASS=os.getenv('POSTGRES_PASSWORD')
DB_HOST=os.getenv('POSTGRES_HOST') if inside_docker else os.getenv('POSTGRES_HOST_LOCAL')
DB_PORT=os.getenv('DB_PORT')
DB_NAME=os.getenv('POSTGRES_DB')

DATABASE_URL = f'postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

from sqlalchemy.pool import NullPool
engine = create_async_engine(
    DATABASE_URL, 
    echo=True, 
    poolclass=NullPool  # this is necessrary to avoid problems with async coroutines receiving same connection to db and crash
    )

# create tables if not exist
async def create_db_tables():
    async with engine.begin() as conn:
        # run_sync passes the connection to create_all automatically
        await conn.run_sync(Base.metadata.create_all)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as db:
        try:
            yield db  # yield, not return. we need to run db.commit() after endpoint finish its work
            await db.commit()
        except Exception:
            await db.rollback()
            raise

SessionDep = Annotated[AsyncSession, Depends(get_db)]
