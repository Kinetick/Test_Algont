import aiofiles.os as aos
import aiohttp_jinja2 as aioj
import asyncio as aio
import jinja2 as jj2
import matplotlib.pyplot as plt
from aiohttp.web import Application, AppRunner, TCPSite
from datetime import datetime
from os import PathLike
from psutil import cpu_percent
from typing import Any, Coroutine, Dict, Type, List, Tuple, Optional

from monitoring.ABC import ABCMonitor, ABCDataBaseObjectFact, ABCFigure


class LinearFigure(ABCFigure):
    def __init__(self, y_val: List[float], title: str, x_label: str, y_label: str, fig_size: Tuple[int, int], save_path: PathLike, x_step: Optional[int] = None) -> None:
        self.__y_val = y_val
        self.__y_len = len(y_val)
        self.__title = title
        self.__x_label = x_label
        self.__x_step = x_step
        self.__y_label = y_label
        self.__fig_size = fig_size
        self.__save_path = save_path
        self.__plt = plt
        self.__plt.switch_backend('agg')
    
    async def _cleaner(self) -> Coroutine[Any, Any, None]:
        if await aos.path.exists(self.__save_path):
            await aos.remove(self.__save_path)
    
    def _calc_figure(self) -> None:
        self.__x_val = [x for x in range(0, self.__y_len)]
        self.__figure = self.__plt.figure(figsize=self.__fig_size)
        self.__ax = self.__figure.add_subplot()
        self.__figure.suptitle(self.__title)
        self.__ax.set_ylim(ymax=100, ymin=0)
        self.__ax.set_xlabel(self.__x_label)
        self.__ax.set_ylabel(self.__y_label)
        it = range(0, self.__y_len)
        if self.__x_step:
            it = range(0, self.__y_len, self.__x_step)
        self.__ax.set_xticks([x for x in it], size=2)
        self.__ax.set_yticks([y for y in range(0, 110, 10)], size=2)
        self.__plt.grid(color='red', linestyle='--', linewidth=0.5)
        self.__plt.plot(self.__x_val, self.__y_val)

    async def save(self) -> Coroutine[Any, Any, None]:
        await self._cleaner()
        self._calc_figure()
        await aio.to_thread(self.__plt.savefig, self.__save_path)


class CpuLoadsObjectFact(ABCDataBaseObjectFact):
    
    @staticmethod
    def create(load: float, time: datetime):
        return CpuLoads(r_value=load, r_time=time)

from monitoring.db.models import CpuLoads
# Монитор для получения загрузки ЦП и записи значения в БД
class CpuLoadMonitor(ABCMonitor):
    def __init__(self, db_handler, fact: Type[CpuLoadsObjectFact] = CpuLoadsObjectFact) -> None:
        self.__db_handler = db_handler
        self.__fact = fact()
    
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
            db_object = self.__fact.create(cpu_load, date)
            await self._save_value(db_object)
            await aio.sleep(interval)

from monitoring.routes import routes_setup
# Сервер для обработки запросов, точнее для получения графиков
# Запуск сервера через метод "start", там же произойдет настройка сервера
class MonitoringServer:
    def __init__(self, port: int, app_vars: Dict[str, Any]) -> None:
        self.__port = port
        self.__app_vars = app_vars
        self.__app = Application()
        self.__app['config'] = {}
    
    def __get_parameter(self, source: Dict[str, Any], key: str) -> Any:
        error_msg = f'Отсутствует необходиый параметр: "{key}", в переменных приложения.'
        try:
            value = source[key]
        except KeyError:
            print(error_msg)
            raise
        
        return value
    
    async def __release_db(self, *args):
        yield
        db_handler = self.__get_parameter(self.__app['config'], 'DB_HANDLER')
        await db_handler.release()
    
    def __setup_app(self) -> None:
        self.__app['config'] = self.__app_vars
        routes_setup(self.__app)
        templates_path = self.__get_parameter(self.__app['config'], 'TEMPLATES_PATH')
        aioj.setup(self.__app, loader=jj2.FileSystemLoader(templates_path))
        self.__app.cleanup_ctx.append(self.__release_db)

    async def start(self) -> Coroutine[Any, Any, None]:
        self.__setup_app()
        runner = AppRunner(self.__app)
        await runner.setup()
        site = TCPSite(runner, port=self.__port)
        await site.start()
        while True:
            await aio.sleep(3600)
