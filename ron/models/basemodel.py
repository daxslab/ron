from peewee import Model

from ron import Application


class BaseModel(Model):
    """
    Base class for peewee ORM models
    """

    class Meta(object):
        database = Application().db().proxy