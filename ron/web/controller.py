import functools
from functools import wraps
from inflection import underscore


def routeapp(obj, app):
    for kw in dir(obj):
        attr = getattr(obj, kw)
        if hasattr(attr, 'route'):
            if isinstance(attr.route, dict):
                route_params = attr.route
                app.route(**route_params)(attr)


class Controller:

    views_path = None

    module = None

    def __init__(self, module):
        self.module = module
        self.views_path = module.views_path + "/" + underscore(self.__class__.__name__)

        routeapp(self, self.module.app())

    @staticmethod
    def add_route(function, route, **route_args):
        if not route:
            function.route = dict(path='/' + underscore(function.__name__), **route_args)
        else:
            function.route = dict(path=route, **route_args)

    def route(route=None, **route_args):
        def decorator(f):
            Controller.add_route(f, route, **route_args)
            return f

        return decorator

    def action(route=None, filepath=None, ext='.tpl', **route_args):
        def real_decorator(func):

            Controller.add_route(func, route, **route_args)

            @wraps(func)
            def wrapper(self, *args, **kwargs):
                from bottle import template
                result = func(self, *args, **kwargs)
                if not filepath:
                    action = func.__name__
                    filename = action + ext
                else:
                    filename = filepath
                template = functools.partial(template, template_adapter=self.module.template_adapter)
                return template(self.views_path + '/' +filename, **result)

            return wrapper

        return real_decorator
