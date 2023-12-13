import functools
import os

from bottle import template as bottle_template

from ron.base.basecomponent import BaseComponent
from collections.abc import MutableMapping

from ron.templates.yatl_template import YatlTemplate


class View(BaseComponent):

    # template adapter
    template_adapter = YatlTemplate

    # views path
    path = 'views'

    def render(self, view_file, *args, **params):
        """
        Renders a view.
        :param view_file: the view name.
        :type view_file: str
        :param args: template rendering arguments
        :type args:
        :param params: the parameters (name-value pairs) that will be made available in the view file.
        :type params:
        :return: the rendering result
        :rtype: str
        """
        template = functools.partial(bottle_template, template_adapter=self.template_adapter)
        from ron import Application
        return template(view_file, *args, template_lookup=[os.path.join(self.module.base_path, self.path)], layout=Application().layout, **params)


    def __call__(self, view_file, **defaults):
        ''' Decorator: renders a template for a handler.
                The handler can control its behavior like that:

                  - return a dict of template vars to fill out the template
                  - return something other than a dict and the view decorator will not
                    process the template, but return the handler result as is.
                    This includes returning a HTTPResponse(dict) to get,
                    for instance, JSON with autojson or other castfilters.
            '''
        def decorator(func):
            @functools.wraps(func)
            def wrapper(controller, *args, **kwargs):
                from bottle import template
                template = functools.partial(template, template_adapter=self.template_adapter)
                result = func(controller, *args, **kwargs)
                from ron import Application
                if isinstance(result, (dict, MutableMapping)):
                    tplvars = defaults.copy()
                    tplvars.update(result)
                    return template(view_file, layout=Application().layout, **tplvars)
                elif result is None:
                    return template(view_file, defaults, layout=Application().layout)
                return result

            return wrapper

        return decorator