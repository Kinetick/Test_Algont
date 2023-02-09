import asyncio as aio
from datetime import datetime
from psutil import cpu_percent
from typing import Any, Coroutine, Type

from monitoring.ABC import ABCMonitor, ABCDataBaseObjectFabric
from monitoring.db import DataBaseHandler
from monitoring.db.models import CpuLoads


class CpuLoadsObjectFabric(ABCDataBaseObjectFabric):
    
    @staticmethod
    def create(load: float, time: datetime) -> CpuLoads:
        return CpuLoads(r_value=load, r_time=time)


class CpuLoadMonitor(ABCMonitor):
    def __init__(self, db_handler: DataBaseHandler, fabric: Type[CpuLoadsObjectFabric] = CpuLoadsObjectFabric) -> None:
        self.__db_handler = db_handler
        self.__fabric = fabric()
    
    @staticmethod
    def _get_value() -> float:
        return round(cpu_percent(), 1)
    
    async def _save_value(self, db_object: CpuLoads) -> Coroutine[Any, Any, None]:
        async with self.__db_handler.get_session() as session:
            session.add(db_object)
            await session.commit()
    
    async def run(self, interval: float) -> Coroutine[Any, Any, None]:
        while True:
            cpu_load = self._get_value()
            date = datetime.now()
            db_object = self.__fabric.create(cpu_load, date)
            await self._save_value(db_object)
            await aio.sleep(interval)
