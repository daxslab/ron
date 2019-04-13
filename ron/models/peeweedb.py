from bottle_peewee import PeeweePlugin

from ron import Application


class PeeweeDB:
    """
    Models component using the peewee ORM
    """

    def __init__(self, *args, **kwargs):
        app = Application()

        options = {}

        for option, value in kwargs.items():
            options[option] = value

        self.db = PeeweePlugin(**options)

        app.module_plugins.append(self.db)

    def __call__(self, *args, **kwargs):
        return self.db