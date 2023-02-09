from contextlib import asynccontextmanager
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from typing import Generator, Self



class DataBaseHandler:
    def __new__(cls: type[Self]) -> Self:
        inst = None
        
        if inst is None:
            inst = object.__new__(cls)
        
        return inst
    
    def __init__(self, db_url: str) -> None:
        self.__engine = create_async_engine(db_url, echo=True, future=True)
        self.__session_maker = sessionmaker(self.__engine, expire_on_commit=False, class_=AsyncSession)
    
    async def create(self, Base: DeclarativeMeta) -> None:
        async with self.__engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
    
    async def drop(self, Base: DeclarativeMeta) -> None:
        async with self.__engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
    
    @asynccontextmanager
    async def get_session(self) -> Generator[None, None, AsyncSession]:
        try:
             async with self.__session_maker() as session:
                 yield session
        
        finally:
            await session.close()