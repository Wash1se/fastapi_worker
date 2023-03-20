from main import Base, ScanningUser, set_if_scanning
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import text

import settings
import asyncio

engine = create_async_engine(settings.REAL_DATABASE_URL, future=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

async def reset_all_strings():
    async with async_session() as session:
        async with session.begin():
            #await session.execute(ScanningUser.all())
            res = (await session.execute(text('SELECT *  FROM scanning_users')))
            for row in res:
                await set_if_scanning(row[0], False)
asyncio.run(reset_all_strings())
