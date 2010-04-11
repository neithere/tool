# -*- coding: utf-8 -*-

from werkzeug import Response, Request, responder, run_simple
from werkzeug.script import make_shell

from tool.commands import command
from tool.context import context
from tool.importing import import_attribute
from tool import signals


__all__ = ['make_app']


# signals
request_ready, urls_ready = 'request_ready', 'urls_ready'


def make_app(settings, urls, with_commands=False):
    """
    Returns a WSGI application based on given configuration (a ``dict``) and
    URL map (a ``werkzeug.routing.Map``).

    :param settings: a dictionary
    :param urls: a werkzeug.Map object
    :param with_commands: a bool, default is False. If True, registers standard
        application management commands. Use with caution because this binds
        *current* application to the ``run`` and other commands, no matter
        whether the app is then wrapped in middleware or not. In other words,
        this *breaks middleware*.

    Configuration example::

        conf = {
            'bundles': [
                'tool.contrib.models.setup',
            ],
            'foo': 'bar',    # custom variable required by some bundle
        }

    For convenience ``tool.conf.load`` helper is provided so you can define the
    configuration in YAML or other formats::

        bundles:
            - tool.contrib.models.setup
        foo: bar

    Here's a complete example with a configuration file::

        from tool import commands, conf, make_app, register_commands, routing

        settings = conf.load('conf.yaml')

        urls = routing.Map(
            routing.find_urls('myapp.views')
        )

        app = make_app(settings, urls)

        register_commands(app)     # exposes standard commands ("run", etc.)

        if __name__ == '__main__':
            commands.dispatch()    # parses arguments, e.g. "run"

    We keep things as simple as possible. This means that no configuration
    management is involved. There is no validation except for the check
    whether the whole configuration is a dictionary. You can stuff anything
    into that dictionary. This has all the advantages of being dead simple
    and all the disadvantages of letting you mess everything up and discover
    that not earlier than a certain view function gets called. So be careful.
    """
    context.settings = settings

    init_bundles(settings)

    def find_and_call_view(endpoint, v):
        if isinstance(endpoint, basestring):
            try:
                endpoint = import_attribute(endpoint)
            except ImportError as e:
                raise ImportError('Could not import view "%s"' % endpoint)
        assert hasattr(endpoint, '__call__')
        return endpoint(context.request, **v)

    @responder
    def app(environ, start_response):
        context.request = Request(environ)
        signals.send(request_ready, sender=context.request)

        context.urls = urls.bind_to_environ(environ)
        signals.send(urls_ready, sender=context.urls)

        # another approach: http://stackoverflow.com/questions/1796063/werkzeug-mapping-urls-to-views-via-endpoint
        return context.urls.dispatch(find_and_call_view,
                                     catch_http_exceptions=True)

    if with_commands:
        register_commands(app)

    return app

def init_bundles(settings):
    """
    Initializes bundles by calling initializers defined in
    ``config['bundles']``.
    This is not required for the bundles to work.
    Each initializer must be a callable object or a dotted path to it.
    Example initializer::

        def init(settings, context):
            path = settings.get('foo_path', '.')
            context.foo = Foo(path)

    """
    for initializer in settings.get('bundles', []):
        if isinstance(initializer, basestring):
            try:
                initializer = import_attribute(initializer)
            except ImportError as e:
                raise ImportError('Could not initialize bundle %s: %s' % (initializer, e))
        initializer(settings, context)

def register_commands(app_factory):
    """
    Registers default commands for application management.
    """
    @command()
    def run(host=('h', 'localhost', 'host'), port=('p', 6060, 'port')):
        "Run development server for your application."
        run_simple(host, port, app_factory)

    @command()
    def shell(plain=('p', False, 'plain')):
        "Spawns an interactive Python shell for your application."
        init_func = lambda: {'app': app_factory}
        use_ipython = not plain
        sh = make_shell(init_func, use_ipython=use_ipython)
        sh()
