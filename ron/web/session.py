from beaker.middleware import SessionMiddleware

class SessionComponent:
    """
    Session component using the beaker session middleware
    """

    def __init__(self, *args, **kwargs):
        from ron import Application
        app = Application()

        options = {}

        for option, value in kwargs.items():
            options['session.{name}'.format(name=option)] = value

        app.middlewares.append({
            'class': SessionMiddleware,
            'options': options
        })

    def __call__(self, *args, **kwargs):
        from ron import request
        return request.environ.get('beaker.session')