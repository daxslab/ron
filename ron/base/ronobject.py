from ron.exceptions.invalid_configuration_exception import InvalidConfigurationException


class RonObject:

    def __init__(self, *args, **kwargs):
        config = kwargs.get('config', {})
        # if not config:
        #     raise InvalidConfigurationException(
        #         '{object} should contain a config parameter'.format(object=self.__class__.__name__))
        if config and not isinstance(config, dict):
            raise InvalidConfigurationException(
                'Configuration should be a dict instance'.format(object=self.__class__.__name__))
        for key in config:
            setattr(self, key, config[key])

    @staticmethod
    def instanceObject(config):
        object_class = config.get('_class', None)
        if not object_class:
            raise InvalidConfigurationException('Config should contain a _class object')
        # if not issubclass(object_class, RonObject):
        #     raise InvalidConfigurationException('_class should inherit from RonObject')
        return object_class(config)