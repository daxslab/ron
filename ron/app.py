from ron.base import Module
from ron.base.singleton import Singleton

class Application(Module, metaclass=Singleton):

    # configuration information for this application
    middlewares = []

    # application instance has no controllers
    controllers = None

    def __init__(self, config=None, catchall=True, autojson=True):
        # self.__name__ = name

        Module.__init__(self, config=config, catchall=catchall, autojson=autojson)
        # self.load_components()

    def get_with_middleware(self):
        """
        Returns current application applying middlewares from configuration
        :return: Application middleware
        :rtype: Middleware
        """
        app = self
        for middleware_data in self.middlewares:
            app = middleware_data['class'](app, **middleware_data.get('options', {}))
        return app
