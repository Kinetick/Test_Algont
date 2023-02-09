import aiohttp.web as web
from aiohttp.web import Application

from monitoring.routes import views


def routes_setup(app: Application) -> None:
    index_handler = views.IndexHandler(app)
    app.add_routes([
        web.get('/index', index_handler.get, name='index'),
        web.static('/static', app['config']['STATIC_PATH'], name='static')
    ])