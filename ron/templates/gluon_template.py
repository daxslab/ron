import functools
import os

from bottle import BaseTemplate, template



class GluonTemplate(BaseTemplate):
    def prepare(self, *args, **kwargs):
        from ron.gluon.template import render
        self.tpl = render

    def render(self, *args, **kwargs):
        for dictarg in args: kwargs.update(dictarg)
        _defaults = self.defaults.copy()
        _defaults.update(kwargs)
        dirname = os.path.dirname(self.filename)
        return self.tpl(path=dirname, filename=self.filename, context=_defaults)

    def loader(self, name):
        fname = self.search(name, self.lookup)
        if not fname: return
        with open(fname, "rb") as f:
            return f.read().decode(self.encoding)

gluon_template = functools.partial(template, template_adapter=GluonTemplate)