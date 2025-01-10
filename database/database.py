# from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = 'sqlite+aiosqlite:///./PowerSports.db'

async_engine = create_async_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread":False})

SessionLocal = sessionmaker(bind=async_engine,class_=AsyncSession,autocommit=False,autoflush=False)

Base = declarative_base()


# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
        
async def get_db():
    async with SessionLocal() as session:
        # yield session
        try:
            yield session
        finally:
            await session.close()