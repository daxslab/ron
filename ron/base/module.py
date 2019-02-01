import inspect
import os
import pkgutil

from importlib import import_module
from bottle import Bottle

from ron.base.object import Object
from ron.exceptions.invalid_configuration_exception import InvalidConfigurationException
from ron.templates import GluonTemplate
from ron.web import Controller


class Module(Bottle, Object):
    """Module is the base class for module and application classes.

    A module represents a sub-application which contains MVC elements by itself, such as
    models, views, controllers, etc.

    A module may consist of sub-modules.
    """

    # Module class object
    module_class = None

    # template adapter
    template_adapter = GluonTemplate

    # views path
    views_path = 'views'

    # modules
    modules = []

    # mount type can be used for defining mount behavior, can be "mount" or "merge"
    mount_type = 'mount'


    def __init__(self, config=None, parent=None, catchall=True, autojson=True):
        """Initializes the module setting the correct path for the controllers and views"""

        Bottle.__init__(self, catchall, autojson)
        Object.__init__(self, config=config)

        if isinstance(config, dict):
            self.namespace = self._get_module_namespace()
            self.package = import_module(self.namespace)
            self.base_path = os.path.dirname(self.package.__file__)
            self.views_path = os.path.join(self.base_path, self.views_path)
            self.parent = parent

            self.init_controllers()

            if config.get('modules', False):
                self.init_modules(config.get('modules'))

    def _get_module_namespace(self):
        module = inspect.getmodule(self.module_class)
        parent_name = '.'.join(module.__name__.split('.')[:-1])
        return parent_name

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
        for module_name in modules:
            module_class = modules[module_name].get('module_class')
            module_instance = module_class(config=modules[module_name])
            if self.mount_type == 'mount':
                self.mount(module_name, module_instance)
            elif self.mount_type == 'merge':
                self.merge(module_instance)
            else:
                raise InvalidConfigurationException(
                    'Mount type should be "mount" or "merge", not {mount_type}'.format(mount_type=self.mount_type))
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
