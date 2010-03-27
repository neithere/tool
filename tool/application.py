# -*- coding: utf-8 -*-

from werkzeug import Response, Request, responder, run_simple

from tool.commands import command
from tool.context import context


def make_app(config, url_map, with_commands=True):
    context.config = config

    init_bundles(config)

    def find_and_call_view(endpoint, v):
        # NOTE: this supports only callable endpoints
        assert hasattr(endpoint, '__call__')
        return endpoint(context.request, **v)
        #f = context.views.get_view(endpoint)
        # return f(request, **v)

    @responder
    def app(environ, start_response):
        context.request = Request(environ)
        context.urls = url_map.bind_to_environ(environ)

        return context.urls.dispatch(find_and_call_view,
                                     catch_http_exceptions=True)

    if with_commands:
        register_commands(app)

    return app

def init_bundles(config):
    """
    Initialized bundles defined in config['init_bundles'].
    This is not required for the bundles to work.
    Each initializer must be a callable object or a dotted path to it.
    Example initializer::

        def init(config, context):
            path = config.get('foo_path', '.')
            context.foo = Foo(path)

    """
    for initializer in config.get('init_bundles', []):
        if isinstance(initializer, basestring):
            name = initializer
            i = name.rfind('.')
            module, attr = name[:i], name[i+1:]
            mod = __import__(module, globals(), locals(), [attr])
            initializer = getattr(mod, attr)
        initializer(config, context)

def register_commands(app):
    """
    Registers default commands for application management.
    """
    @command()
    def run(host=('h', 'localhost', 'host'), port=('p', 6060, 'port')):
        """
        Runs development server for your application.
        """
        run_simple(host, port, app)
