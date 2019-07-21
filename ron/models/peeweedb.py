import sys

try:
    from bottle_peewee import PeeweePlugin
except ModuleNotFoundError as e:
    print("Required bottle_peewee module, try to install it with 'pip install bottle-peewee'")
    sys.exit(1)

from ron import Application


class PeeweeDB:
    """
    Models component using the peewee ORM
    """

    def __init__(self, *args, module=None, **kwargs):
        app = Application()

        options = {}

        for option, value in kwargs.items():
            options[option] = value

        self.db = PeeweePlugin(**options)

        self.module = module

        app.module_plugins.append(self.db)

    def __call__(self, *args, **kwargs):
        return self.db