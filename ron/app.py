from ron.base import Module
from ron.base.singleton import Singleton

class Application(Module, metaclass=Singleton):

    # components configuration information for this application
    components = {}

    # configuration information for this application
    middlewares = []

    def __init__(self, config=None, catchall=True, autojson=True):
        # self.__name__ = name

        Module.__init__(self, config=config, catchall=catchall, autojson=autojson)
        self.load_components()


    def initialize(self):
        super(self.__class__, self).initialize()
        self.load_components(on_initialize=True)


    def load_components(self, on_initialize=False):
        """
        Load application components from configuration
        """
        for name, component_data in self.components.items():
            start_on_initialize = component_data.get('on_initialize', False)
            if start_on_initialize == on_initialize:
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
