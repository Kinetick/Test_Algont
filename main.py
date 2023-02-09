import asyncio as aio
import monitoring
from monitoring.db import DataBaseHandler
from monitoring.db.models import Base
from pathlib import Path

# Константы для настройки приложения
# Пути
BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR.joinpath('test.sqlite')
DB_URL = f'sqlite+aiosqlite:///{DB_PATH}'

# Перемнные приложения
APP_VARS = {
    'TEMPLATES_PATH': BASE_DIR.joinpath('templates'),
    'DB_HANDLER': DataBaseHandler(DB_URL),
    'STATIC_PATH': BASE_DIR.joinpath('static'),
    'IMAGE_MOMENT_PATH': BASE_DIR.joinpath('static/images/inmoment/m_load.png'),
    'IMAGE_AVG_PATH': BASE_DIR.joinpath('static/images/avg/av_load.png'),
    'SLICE_PERIOD_MINUTES': 60,
    'SCAN_PERIOD_SEC': 5
}


async def main():
    if not DB_PATH.exists():
        DB_PATH.touch(exist_ok=True)
    
    # Монитор загрузки ЦП
    monitor = monitoring.CpuLoadMonitor(APP_VARS['DB_HANDLER'])
    # Сервер для выдачи странички с графиками
    server = monitoring.MonitoringServer(5000, APP_VARS)
    # Создание таблицы для хранения записей по загрузке ЦП
    await APP_VARS['DB_HANDLER'].create(Base)
    # Собственно сам мониторинг, состоит из двух задач
    # которые выполняются конкурентно
    res = await aio.gather(monitor.run(APP_VARS['SCAN_PERIOD_SEC']), server.start())

if __name__ == '__main__':
    try:
        aio.run(main())
    
    except KeyboardInterrupt:
        print('\b\bStop!!!')