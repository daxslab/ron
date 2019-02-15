from ron.base import Module
from ron.base.singleton import Singleton


@Singleton
class Application(Module):

    # components configuration information for this application
    components = {}

    # configuration information for this application
    middlewares = []

    def __init__(self, config=None, catchall=True, autojson=True):
        # self.__name__ = name

        Module.__init__(self, config=config, catchall=catchall, autojson=autojson)
        self.load_components()

    def load_components(self):
        """
        Load application components from configuration
        """
        for name, component_data in self.components.items():
            component = component_data['class'](**component_data.get('options', {}))
            setattr(self, name, component)

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
