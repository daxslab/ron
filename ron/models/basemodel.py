from peewee import Model
from peewee_validates import ModelValidator

from ron import Application


class BaseModel(Model):
    """
    Base class for peewee ORM models
    """

    def __init__(self, *args, **kwargs):
        Model.__init__(self, *args, **kwargs)

        self._validator = ModelValidator(self)

    def validate(self, data=None):
        if data:
            return self._validator.validate(data)
        else:
            return self._validator.validate()

    def validator(self):
        return self._validator

    def update_model(self, data):
        for key,value in data.items():
            setattr(self,key,value)

    class Meta(object):
        database = Application().db().proxy