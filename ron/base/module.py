import inspect
import os
import pkgutil

from importlib import import_module
from bottle import Bottle

from ron.base.ronobject import RonObject
from ron.base.view import View
from ron.exceptions.invalid_configuration_exception import InvalidConfigurationException
from ron.web import Controller


class Module(Bottle, RonObject):
    """Module is the base class for module and application classes.

    A module represents a sub-application which contains MVC elements by itself, such as
    models, views, controllers, etc.

    A module may consist of sub-modules.
    """

    # view object
    view = None

    # modules
    modules = []

    # mount type can be used for defining mount behavior, can be "mount" or "merge"
    mount_type = 'mount'

    controllers = {}

    models = []

    # components configuration information for this module
    components = {}

    # module plugins
    module_plugins = []

    # module base path
    base_path = None

    # Module namespace. Private
    __namespace = None

    # Module package. Private
    __package = None


    def __init__(self, config=None, parent=None, catchall=True, autojson=True):
        """Initializes the module setting the correct path for the controllers and views"""

        Bottle.__init__(self, catchall, autojson)
        RonObject.__init__(self, config=config)

        if not self.view:
            self.view = View(config = {'module':self})

        if isinstance(config, dict):
            self.__namespace = self._get_module_namespace()
            if not self.base_path:
                self.__package = import_module(self.__namespace)
                self.base_path = os.path.dirname(self.__package.__file__)
            self.parent = parent

        self.load_components()


    def load_components(self, on_initialize=False):
        """
        Load module components from configuration
        """
        for name, component_data in self.components.items():
            start_on_initialize = component_data.get('on_initialize', False)
            if start_on_initialize == on_initialize:
                component_data.pop('on_initialize', None)

                # inject parent module in component
                if not component_data.get('options', None):
                    component_data['options'] = {}

                component_data['options']['module'] = self
                component = RonObject.instanceObject(component_data)
                setattr(self, name, component)


    def _get_module_namespace(self):
        module = inspect.getmodule(self.__class__)
        parent_name = '.'.join(module.__name__.split('.')[:-1])
        return parent_name

    def initialize(self):
        self.load_components(on_initialize=True)
        for plugin in self.module_plugins:
            self.install(plugin)
        if self.__namespace:
            self.init_controllers()
            self.init_models()
        if self.modules:
            self.init_modules(self.modules)

    def init_controllers(self):
        """Initializes all the controllers in the [controllers_path] directory and registers them against the currently
            running app."""
        if self.controllers == None:
            return
        controllers_namespace = self.__namespace + ".controllers"  # TODO: allow customize this
        try:
            controllers_package = import_module(controllers_namespace)
        except:
            return None

        from ron import Application
        controllers_modules = self._get_package_modules(controllers_package)
        for controller_name in controllers_modules:
            imported_controller = import_module('.' + controller_name, package=controllers_namespace)
            for i in dir(imported_controller):
                attribute = getattr(imported_controller, i)
                if inspect.isclass(attribute) and issubclass(attribute, Controller):
                    controller_class = attribute(self)
                    self.controllers[controllers_namespace+'.'+controller_name] = controller_class
                    Application().controllers[controllers_namespace+'.'+controller_name] = controller_class

    def init_models(self):
        """
        Registers all the models in the [models_path] directory against the current application database
        """
        from ron import Application
        from ron.models.basemodel import BaseModel
        if self.models == None or not Application().db:
            return
        models_namespace = self.__namespace + ".models"  # TODO: allow customize this
        try:
            models_package = import_module(models_namespace)
        except:
            models_package = None
        if models_package:
            models_modules = self._get_package_modules(models_package)
            for model_name in models_modules:
                imported_model = import_module('.' + model_name, package=models_namespace)
                for i in dir(imported_model):
                    attribute = getattr(imported_model, i)
                    if inspect.isclass(attribute) and issubclass(attribute, BaseModel):
                        self.models.append(attribute)
            Application().db().database.create_tables(self.models)

    def init_modules(self, modules):
        for module_name in modules:
            module_class = modules[module_name].get('_class')
            module_instance = RonObject.instanceObject(modules[module_name])
            module_instance.initialize()
            if module_instance.mount_type == 'mount':
                self.mount(module_name, module_instance)
            elif module_instance.mount_type == 'merge':
                self.merge(module_instance)
            else:
                raise InvalidConfigurationException(
                    'Mount type should be "mount" or "merge", not {mount_type}'.format(mount_type=self.mount_type))
            # self.modules.append(module_instance)
            modules[module_name] = module_instance
        from ron import Application
        app = Application()
        if app.url_manager:
            app.url_manager.remove_defined_routes()
            app.url_manager.set_routes()

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
