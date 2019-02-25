import functools
import os

from bottle import BaseTemplate, template



class YatlTemplate(BaseTemplate):
    def prepare(self, *args, **kwargs):
        from yatl import render
        self.tpl = render

    def render(self, *args, **kwargs):
        for dictarg in args: kwargs.update(dictarg)
        _defaults = self.defaults.copy()
        _defaults.update(kwargs)
        dirname = os.path.dirname(self.filename)
        return self.tpl(path=dirname, filename=self.filename, context=_defaults)

yatl_template = functools.partial(template, template_adapter=YatlTemplate)