import inspect
import os
import pkgutil

from importlib import import_module
from bottle import Bottle

from ron.templates import GluonTemplate
from ron.web import Controller


class Module(Bottle):
    """Module is the base class for module and application classes.

    A module represents a sub-application which contains MVC elements by itself, such as
    models, views, controllers, etc.

    A module may consist of sub-modules.
    """

    def __init__(self, config=None, parent=None, catchall=True, autojson=True):
        """Initializes the module setting the correct path for the controllers and views"""

        Bottle.__init__(self, catchall, autojson)

        if isinstance(config, dict):
            self.namespace = config.get('namespace')
            self.template_adapter = config.get('template_adapter', GluonTemplate)
            self.package = import_module(self.namespace)
            self.base_path = os.path.dirname(self.package.__file__)
            self.views_path = config.get('views_path', os.path.join(self.base_path, 'views'))
            self.modules = config.get('modules', None)
            self.parent = parent

            self.init_controllers()

            if config.get('modules', False):
                self.init_modules(config.get('modules'))

    def init_controllers(self):
        """Initializes all the controllers in the [controllers_path] directory and registers them against the currently
            running app."""

        controllers_namespace = self.namespace + ".controllers"  # TODO: allow customize this
        controllers_package = import_module(controllers_namespace)

        controllers = []
        controllers_modules = self._get_package_modules(controllers_package)
        for controller_name in controllers_modules:
            imported_controller = import_module('.' + controller_name, package=controllers_namespace)
            for i in dir(imported_controller):
                attribute = getattr(imported_controller, i)
                if inspect.isclass(attribute) and issubclass(attribute, Controller):
                    controllers.append(attribute(self))

        return controllers

    def init_modules(self, modules):
        self.modules = []
        for module in modules:
            module_instance = Module(modules[module])
            self.mount(module, module_instance)
            self.modules.append(module_instance)

    def app(self):
        current = self
        while current:
            if current.parent is None:
                return current
            current = current.parent

    @staticmethod
    def _get_package_modules(package):
        modules = []
        for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
            if not ispkg:
                modules.append(modname)
        return modules
