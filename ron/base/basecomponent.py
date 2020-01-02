from ron.exceptions.invalid_configuration_exception import InvalidConfigurationException

from ron.base.ronobject import RonObject


class BaseComponent(RonObject):

    def __init__(self, *args, **kwargs):
        RonObject.__init__(self, *args, **kwargs)
        if not self.module:
            raise InvalidConfigurationException("Component needs a 'module'")
