from ron.base import Module


class Application(Module):

    def __init__(self, name, config=None, catchall=True, autojson=True):
        self.__name__ = name

        Module.__init__(self, catchall, autojson)
        self.config = config
        self.init_modules()


