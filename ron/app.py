import os

from bottle import static_file

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
        self._expose_statics()
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

    def _expose_statics(self):
        """
        Expose statics folder
        """
        @self.route('/static/<filename:path>')
        @self.route('/static/_<version:re:\d+\.\d+\.\d+>/<filename:path>')
        def server_static(filename, path='', version=None):
            return static_file(filename, root=os.path.join(path, 'static'))
