import functools
from functools import wraps
from inflection import underscore

def routeapp(obj, app):
    for kw in dir(obj):
        attr = getattr(obj, kw)
        if hasattr(attr, 'route'):
            if isinstance(attr.route, dict):
                route_params = attr.route
                if obj.base_route:
                    route_params['path'] = obj.base_route + route_params['path']
                app.route(**route_params)(attr)
            elif isinstance(attr.route, list):
                for route_data in attr.route:
                    route_params = route_data
                    if obj.base_route:
                        route_params['path'] = obj.base_route + route_params['path']
                    app.route(**route_params)(attr)


class Controller:

    base_route = None

    module = None

    def __init__(self, module):
        self.module = module
        routeapp(self, self.module.app())

    @staticmethod
    def add_route(function, route, **route_args):
        if not hasattr(function, 'route'):
            function.route = []
        if not route:
            function.route.append(dict(path='/' + underscore(function.__name__), **route_args))
        else:
            function.route.append(dict(path=route, **route_args))

    def route(route=None, **route_args):
        def decorator(f):
            Controller.add_route(f, route, **route_args)
            return f

        return decorator

    def action(route=None, filepath=None, ext='.tpl', **route_args):
        ''' Decorator: renders a template for a handler.
                        The handler can control its behavior like that:

                          - return a dict of template vars to fill out the template
                          - return something other than a dict and the view decorator will not
                            process the template, but return the handler result as is.
                            This includes returning a HTTPResponse(dict) to get,
                            for instance, JSON with autojson or other castfilters.
                    '''
        def real_decorator(func):

            Controller.add_route(func, route, **route_args)

            @wraps(func)
            def wrapper(self, *args, **kwargs):
                result = func(self, *args, **kwargs)
                if not filepath:
                    action = func.__name__
                    filename = underscore(self.__class__.__name__) + '/' + action + ext
                else:
                    filename = filepath
                return self.module.view.render(filename, **result)

            return wrapper

        return real_decorator

    def view(tpl_name):
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
            def wrapper(self, *args, **kwargs):
                result = func(self, *args, **kwargs)
                return self.module.view.render(tpl_name, **result)

            return wrapper

        return decorator
