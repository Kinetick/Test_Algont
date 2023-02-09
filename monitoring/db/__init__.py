import sqlalchemy as sql
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.decl_api import DeclarativeMeta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from typing import Any, Coroutine, Generator, Optional

from monitoring import CpuLoadsObjectFact
from monitoring.db.models import CpuLoads

# Обработчик БД, была сначала идея передавать класс в инициализатор других классов,
# поэтому был выбран Singleton, потом я от этой, не побоюсь этого слова - "гениальной", хах, затеи отказался и стал
# передавать экземпляр обработчика, но Sigleton пока оставлю, т.к. потом собираюсь расширить 
# тестовое задание добавив новый функционал и там уже буду передавать класс.

# В дальнейшем есть затея добавить полноценный конфигуратор приложения, а не константы в файле main.py
# Плюс хочется добавить возможность добавления других мониторов, для более полной картины состояния системы

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
        self.__engine = create_async_engine(db_url, echo=False, future=True)
        self.__session_maker = sessionmaker(self.__engine, expire_on_commit=False, class_=AsyncSession)
    
    async def release(self) -> Coroutine[Any, Any, None]:
        await self.__engine.dispose()
    
    async def syncronize(self, scan_period: int) -> Coroutine[Any, Any, None]:
        current_date = datetime.now()
        last_record_query = sql.select(CpuLoads.r_time).order_by(sql.func.datetime(CpuLoads.r_time).desc()).limit(1)
        
        async with self.get_session() as session:
            res = await session.execute(last_record_query)
            res = res.scalar()
            if res:
                last_record_date = datetime.strptime(res, '%Y-%m-%d %H:%M:%S.%f')
                shutdown_period_sec = (current_date - last_record_date).seconds
                records_numbers = shutdown_period_sec // scan_period
                fact = CpuLoadsObjectFact()
                records = [fact.create(0, last_record_date + timedelta(seconds=i * scan_period)) for i in range(1, records_numbers + 1)]

                session.add_all(records)
                await session.commit()
            
            # print(last_record_date, current_date)