from contextlib import asynccontextmanager
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from typing import Generator, Optional



class DataBaseHandler:
    def __new__(cls, *args, **kwargs):
        inst = None
        
        if inst is None:
            inst = object.__new__(cls)
        
        return inst
    
    def __init__(self, db_url: Optional[str] = None) -> None:
        if db_url is not None:
            self.__engine = create_async_engine(db_url, echo=True, future=True)
            self.__session_maker = sessionmaker(self.__engine, expire_on_commit=False, class_=AsyncSession)
        
        else:
            self.__engine = None
            self.__session_maker = None
    
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
    
    def setup(self, db_url: str) -> None:
        self.__engine = create_async_engine(db_url, echo=True, future=True)
        self.__session_maker = sessionmaker(self.__engine, expire_on_commit=False, class_=AsyncSession)
    
    