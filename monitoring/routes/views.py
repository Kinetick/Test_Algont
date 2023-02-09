import asyncio as aio
import matplotlib.pyplot as plt
import sqlalchemy as sql
from aiohttp.web import Application, Request, Response
from datetime import datetime, timedelta
from typing import Any, Coroutine, List

from monitoring import LinearFigure
from monitoring.db.models import CpuLoads


class IndexHandler:
    def __init__(self, app: Application) -> None:
        self.__app = app
    
    @staticmethod
    def __get_result(res_iter: sql.ChunkedIteratorResult) -> List[float]:
        return [r.r_value for r in res_iter.scalars()]
    
    async def get(self, request: Request) -> Coroutine[Any, Any, Response]:
        to_date_value = datetime.now()
        from_date_value = to_date_value - timedelta(minutes=self.__app['config']['SLICE_PERIOD_MINUTES'])
        moment_load_query = sql.select(CpuLoads)\
            .where(CpuLoads.r_time.between(sql.func.datetime(from_date_value), sql.func.datetime(to_date_value)))\
            .order_by(CpuLoads.r_time)
            
        average_load_query = sql.select(CpuLoads)\
            .where(CpuLoads.r_time.between(sql.func.datetime(from_date_value), sql.func.datetime(to_date_value)))\
            .group_by(sql.func.strftime('%M', CpuLoads.r_time))\
            .order_by(CpuLoads.r_time)
        
        async with self.__app['config']['DB_HANDLER'].get_session() as session:
            res_moment = await session.execute(moment_load_query)
            res_avg = await session.execute(average_load_query)
            moment = self.__get_result(res_moment)
            average = self.__get_result(res_avg)
        print(average)
        moment_fig = LinearFigure(
            moment,
            'Моментальная загрузка ЦП',
            f'Интервалы сканирования, 1 интервал = {self.__app["config"]["SCAN_PERIOD_SEC"]} сек.',
            'Загрузка процессора, %',
            (10, 10),
            self.__app['config']['IMAGE_MOMENT_PATH'],
            10
            )

        avg_fig = LinearFigure(
            average,
            'Средняя загрузка ЦП',
            f'Интервалы сканирования, 1 интервал = {self.__app["config"]["SCAN_PERIOD_SEC"]} сек.',
            'Загрузка процессора, %',
            (10, 10),
            self.__app['config']['IMAGE_AVG_PATH']
            )
        
        # Собственно сама отрисовка и сохранение графиков
        await moment_fig.save()
        await avg_fig.save()
        
        # К сожалению конкурентно запустить запись двух графиков не получается,
        # вернее получается, но добиться стабильной отрисовки не выходит
        # поэтому принято решение оставить их не блокирующими но не конкурентными, а жаль
        # может есть еще какие-либо библиотеки для отрисовки графиков, которые стабильно работают с асинхронкой, но мне о них не известно.
        # Скорее всего, нестабильная отрисовка связана с использованием одного экземпляра pyplot, две сопрограммы мешают друг другу.
        # Конечно можно было бы разместить два графика в одной фигуре через subplot, но захотелось сделать из раздельно, отсавлю как есть.
        # await aio.gather(moment_fig.save(), avg_fig.save())
        return Response(status=200, text='OK!')