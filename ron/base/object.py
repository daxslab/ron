
class Object:

    def __init__(self, *args, **kwargs):
        config = kwargs.get('config')
        for key in config:
            setattr(self, key, config[key])