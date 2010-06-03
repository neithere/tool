# -*- coding: utf-8 -*-

from werkzeug import Response, Request, responder, run_simple, cached_property
from werkzeug.script import make_shell

from tool import commands, conf, signals
from tool.context_locals import context
from tool.importing import import_attribute
from tool.routing import find_urls, Map, Submount


__all__ = ['ApplicationManager']


# signals
request_ready = 'request_ready'
pre_bind_urls, post_bind_urls = 'pre_bind_urls', 'post_bind_urls'


class ApplicationManager(object):    # TODO: adapt docstring from make_app (which is commented out below) XXX
    """
    Shell/WSGI application manager. Supports common WSGI middleware. Can be
    configured to run a shell script including a WSGI application server; can
    *be* run as a WSGI application itself.

    :param settings: dictionary or path to a YAML file from which the
        dictionary can be obtained
    :param urls: a tool.routing.Map object. If not provided, can be
        constructed later on using :meth:`~ApplicationManager.add_url`.

    Usage::

        #!/usr/bin/env python

        from tool import ApplicationManager
        from werkzeug import DebuggedApplication    # WSGI middleware

        app = ApplicationManager('conf.yaml')
        app.add_urls('hello_world')         # add URLs exposed in that module
        app.wrap_in(DebuggedApplication)  # add middleware

        if __name__=='__main__':
            app.dispatch()    # process sys.argv and call a command

    The code above is a complete management script. Assuming that it's saved as
    `app.py`, you can call it this way::

        $ ./app.py shell
        $ ./app.py run
        $ ./app.py import-some-data

    All these commands are handled by :meth:`~ApplicationManager.dispatch`.
    Commands `shell` and `run` are added by Tool, command `help` is added by
    `opster` and all other commands are registered elsewhere (e.g. in bundles).
    See :doc:`commands` for details.

    The URLs map can be defined using :meth:`~ApplicationManager.add_urls`
    and/or by providing the pre-composed map::

        from tool.routing import Map, Rule

        urlmap = Map([
            Rule('/foo/', endpoint='foo')
        ])
        app = ApplicationManager('conf.yaml', urlmap)
        app.add_urls([
            Rule('/bar/', endpoint='bar')
        ])

    """
    def __init__(self, settings, url_map=None):
        self.settings = self._prepare_settings(settings)
        self.url_map = url_map or Map()
        self.urls = None    # bonotund MapAdapter

        self.wsgi_stack = []

        self.register()
        self.init_bundles()

    def _prepare_settings(self, settings):
        if settings is None:
            return {}
        if isinstance(settings, dict):
            return settings
        if isinstance(settings, basestring):
            return conf.load(settings)
        raise TypeError('expected None, dict or string, got %s' % settings)

    def add_urls(self, rules, submount=None):
        """
        :param rules: list of rules or dotted path to module where the rules
            are exposed.
        :param submount: (string) prefix for the rules
        """
        if self.urls:
            raise RuntimeError('Cannot add URLs: the URL map is already bound '
                               'to environment.')
        if not hasattr(rules, '__iter__'):
            rules = find_urls(rules)
        if submount:
            self.url_map.add(Submount(submount, rules))
        else:
            for rule in rules:
                self.url_map.add(rule)

    def dispatch(self):
        """
        Dispatches commands.
        """
        commands.dispatch()

    def register(self):
        """
        Makes the app available from any part of app, incl. from shell.

        After this method is called, `context.app` and `context.app_manager`
        are set to current ApplicationManager instance. If you later wrap it in
        WSGI middleware without using :meth:`~ApplicationManager.wrap_in`, make
        sure you override `context.app` (see `wrap_in` documentation).
        """
        context.app_manager = self
        context.app = self

    def init_bundles(self):
        """
        Initializes bundles by calling initializers defined in
        ``config['bundles']``.
        This is not required for the bundles to work.
        Each initializer must be a callable object or a dotted path to it.
        Example initializer::

            def init(app):
                path = app.settings.get('foo_path', '.')
                app.foo = Foo(path)

        """
        for initializer in self.settings.get('bundles', []):
            print 'initializing', initializer
            if isinstance(initializer, basestring):
                try:
                    initializer = import_attribute(initializer)
                except ImportError as e:
                    raise ImportError('Could not initialize bundle %s: %s' % (initializer, e))
            initializer(self)

    def __call__(self, environ, start_response):
        wsgi_app = self._compiled_wsgi_app
        print 'wsgi_app', wsgi_app
        return wsgi_app(environ, start_response)

    @cached_property
    def _innermost_wsgi_app(self):
        """
        Creates and returns the innermost WSGI application. Cached.
        """
        def find_and_call_view(endpoint, v):
            if isinstance(endpoint, basestring):
                try:
                    endpoint = import_attribute(endpoint)
                except ImportError as e:
                    raise ImportError('Could not import view "%s"' % endpoint)
            assert hasattr(endpoint, '__call__')
            return endpoint(context.request, **v)

        @responder
        def app_factory(environ, start_response):

            # create request object
            context.request = Request(environ)
            signals.send(request_ready, sender=context.request)

            # bind URLs
            signals.send(pre_bind_urls, sender=self.url_map)
            self.urls = self.url_map.bind_to_environ(environ)
            signals.send(post_bind_urls, sender=self.url_map)

            # determine current URL, find and call corresponding view function
            # another approach: http://stackoverflow.com/questions/1796063/werkzeug-mapping-urls-to-views-via-endpoint
            return self.urls.dispatch(find_and_call_view,
                                      catch_http_exceptions=True)
        return app_factory

    @cached_property
    def _compiled_wsgi_app(self):
        """
        Processes the stack of WSGI applications, wrapping them one in
        another and executing the result.

            app = tool.Application()
            app.wrap_in(SharedDataMiddleware, {'/media': 'media'})
            app.wrap_in(DebuggedApplication, evalex=True)
            >>> app._get_wsgi_app()
            <DebuggedApplication>

        See, what we get is the last application in the list -- or the
        *outermost middleware*. This is the real WSGI application.

        Result is cached.
        """
        outermost = self._innermost_wsgi_app
        for factory, args, kwargs in self.wsgi_stack:
            _tmp_get_name=lambda x: getattr(x, '__name__', type(x).__name__)
            print 'wrapping', _tmp_get_name(outermost), 'in', _tmp_get_name(factory)
            outermost = factory(outermost, *args, **kwargs)
        return outermost

    def wrap_in(self, func, *args, **kwargs):
        """
        Wraps current application in given WSGI middleware. Actually just
        appends that middleware to the stack so that is can be called later on.

        Usage::

            app.wrap_in(SharedDataMiddleware, {'/media': 'media'})
            app.wrap_in(DebuggedApplication, evalex=True)

        ...which is identical to this::

            app.wsgi_stack.append([SharedDataMiddleware,
                                   [{'/media': 'media'], {}])
            app.wsgi_stack.append([DebuggedApplication, [], {'evalex': True}])

        In rare cases you will need playing directly with the stack; in most
        cases wrapping is sufficient as long as the order is controlled by you.

        It is possible to wrap the WSGI application provided by the
        ApplicationManager into WSGI middleware without using
        :meth:`~ApplicationManager.wrap_in`. However, you'll have to register
        the resulting WSGI application yourself::

            from tool import ApplicationManager, context
            from werkzeug import DebuggedApplication

            app = ApplicationManager('conf.yaml')
            app.add_urls('hello_world')
            app = DebuggedApplication(app)
            context.app = app    # important!

            if __name__=='__main__':
                app.dispatch()

        If `context.app` is left intact, the standard commands will serve the
        *unwrapped* application (i.e. only wrapped in middleware from
        `ApplicationManager.wsgi_stack`).

        """
        self.wsgi_stack.append((func, args, kwargs))

'''
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
        this *breaks middleware*. See `register_apps` for details.

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

        # create request object
        context.request = Request(environ)
        signals.send(request_ready, sender=context.request)

        # bind URLs
        signals.send(pre_bind_urls, sender=urls)
        context.urls = urls.bind_to_environ(environ)
        signals.send(post_bind_urls, sender=context.urls)

        # determine current URL, find and call corresponding view function
        # another approach: http://stackoverflow.com/questions/1796063/werkzeug-mapping-urls-to-views-via-endpoint
        return context.urls.dispatch(find_and_call_view,
                                     catch_http_exceptions=True)

    # register app-specfic commands. Use with care (see docstring).
    if with_commands:
        register_commands(app)

    return app
'''

#def init_bundles(settings):
#    """
#    Initializes bundles by calling initializers defined in
#    ``config['bundles']``.
#    This is not required for the bundles to work.
#    Each initializer must be a callable object or a dotted path to it.
#    Example initializer::
#
#        def init(settings, context):
#            path = settings.get('foo_path', '.')
#            context.foo = Foo(path)
#
#    """
#    for initializer in settings.get('bundles', []):
#        if isinstance(initializer, basestring):
#            try:
#                initializer = import_attribute(initializer)
#            except ImportError as e:
#                raise ImportError('Could not initialize bundle %s: %s' % (initializer, e))
#        initializer(settings, context)

#def register_commands(app_factory):
#    """
#    Registers default commands for application management.
#
#    Use with care: if you later wrap the app into some middleware, the
#    commands will not know about it. You do not modify an application with
#    middleware; you wrap current application into middleware and the
#    middleware itself becomes the current app. So the commands should be
#    registered as late as possible if you want to associate them with the
#    outermost application.
#
#    """
@commands.command()
def run(host=('h', 'localhost', 'host'), port=('p', 6060, 'port')):
    "Run development server for your application."
    run_simple(host, port, context.app)

@commands.command()
def shell(plain=('p', False, 'plain')):
    "Spawns an interactive Python shell for your application."
    init_func = lambda: {'context': context}    #{'app': app_factory}
    sh = make_shell(init_func, plain=plain)
    sh()

def make_shell(init_func=None, banner=None, plain=False):
    """Returns an action callback that spawns a new interactive
    python shell.

    :param init_func: an optional initialization function that is
                      called before the shell is started.  The return
                      value of this function is the initial namespace.
    :param banner: the banner that is displayed before the shell.  If
                   not specified a generic banner is used instead.
    :param plain: if set to `True`, default Python shell is used. If set to
                  `False`, bpython or IPython will be used if available (this
                  is the default behaviour).

    This function is identical to that of Werkzeug but allows using bpython.
    """
    banner = banner or 'Interactive Tool Shell'
    init_func = init_func or dict
    def pick_shell(banner, namespace):
        """
        Picks and spawns an interactive shell choosing the first available option
        from: bpython, IPython and the default one.
        """
        if not plain:
            # bpython
            try:
                import bpython
            except ImportError:
                pass
            else:
                bpython.embed(namespace, banner=banner)
                return

            # IPython
            try:
                import IPython
            except ImportError:
                pass
            else:
                sh = IPython.Shell.IPShellEmbed(banner=banner)
                sh(global_ns={}, local_ns=namespace)
                return

        # plain
        from code import interact
        interact(banner, local=namespace)
        return

    return lambda: pick_shell(banner, init_func())
