import os

import sys
from bottle import static_file

from ron.base import Module
from ron.base.singleton import Singleton
from ron.caching.cache import CacheComponent
from ron.models import PeeweeDB
from ron.web.session import SessionComponent
from ron.web.urlmanager import UrlManagerComponent


class Application(Module, metaclass=Singleton):

    # configuration information for this application
    middlewares = []

    # default application path on running script
    base_path = sys.path[0]

    # default application layout path
    layout = os.path.join(base_path, 'main/views/layout.tpl')

    # application cache component
    cache_component: CacheComponent

    # application session component
    session_manager: SessionComponent

    # application database component
    db: PeeweeDB

    # application URL manager component
    url_manager: UrlManagerComponent

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

    def find_action(self, action):
        action_name = action.split('.')[-1]
        controller_namespace = '.'.join(action.split('.')[0:-1])
        return getattr(self.controllers[controller_namespace], action_name)
