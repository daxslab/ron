from ron.exceptions.invalid_configuration_exception import InvalidConfigurationException


class Object:

    def __init__(self, *args, **kwargs):
        config = kwargs.get('config')
        if not config:
            raise InvalidConfigurationException(
                '{object} should contain a config parameter'.format(object=self.__class__.__name__))
        if not isinstance(config, dict):
            raise InvalidConfigurationException(
                'Configuration should be a dict instance'.format(object=self.__class__.__name__))
        for key in config:
            setattr(self, key, config[key])