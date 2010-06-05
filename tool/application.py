# -*- coding: utf-8 -*-

import os.path

from werkzeug import Response, Request, responder, run_simple, cached_property
from werkzeug.script import make_shell

from tool import commands, conf, signals
from tool import context
from tool.importing import import_attribute
from tool.routing import find_urls, Map, Rule, Submount


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

    Werkzeug debugger is disabled by default but can be enabled by setting the
    configuration variable `debug` to `True`.

    """
    def __init__(self, settings, url_map=None):
        self.settings = self._prepare_settings(settings)
        self.url_map = url_map or Map()    # unbound URLs
        # when the WSGI application is compiled, self.url_map is bound to the
        # environment and the resulting MapAdapter instance is set to self.urls
        self.urls = None    # bound URLs

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

    def add_files(self, path, rule=None, endpoint=None):
        """
        Exposes all files in given directory using given rule. By default all
        files (recursively) are made available with prefix `/media/`.

        The simplest example::

            app.add_files('pictures')

        If you have the file `pictures/image123.jpg`, it will be accessible at
        the URL `http://localhost:6060/media/pictures/image123.jpg`. Note that
        the resulting URL is automatically prefixed with "media" to avoid
        clashes with other URLs.

        To specify custom URLs (especially if you are adding multiple
        directories) provide the relevant rules, e.g.::

            # ./pictures/image123.jpg --> http://localhost/images/image123.jpg
            app.add_files('pictures', '/images')

            # ./text/report456.pdf --> http://localhost/text/report456.pdf
            app.add_files('docs', '/text')

        The path to directory can be either absolute or relative to the
        project.

        To build a URL, type::

            app.urls.build('media:pictures', {'file': 'image123.jpg'})

        (The `media:` prefix is added automatically; if will not be present if
        you specify custom `endpoint` param or if the innermost directory in
        the path is named "media".)

        """

        innermost_dir = os.path.split(path)[-1].lstrip('./')

        ## Serving the files

        # generate rule (just take the innermost directory name and prefix it
        # with "media" if it's not already named so)
        if not rule:
            template = u'/%s/' if innermost_dir == 'media' else u'/media/%s/'
            rule = template % innermost_dir

        # generate unique (and transparent) endpoint
        if not endpoint:
            template = u'%s' if innermost_dir == 'media' else u'media:%s'
            endpoint = template % innermost_dir

        # set up the middleware
        from werkzeug import SharedDataMiddleware
        self.wrap_in(SharedDataMiddleware, {rule: path+'/'})

        ## Building the URL

        # make sure we can build('media:endpoint', {'file':...})
        if not '<file>' in rule:
            rule = rule.rstrip('/') + '/<file>'

        # add fake URL so that MapAdapter.build works as expected
        self.add_urls([Rule(rule, endpoint=endpoint, build_only=True)])

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
            #print 'initializing', initializer
            if isinstance(initializer, basestring):
                try:
                    initializer = import_attribute(initializer)
                except ImportError as e:
                    raise ImportError('Could not initialize bundle %s: %s' % (initializer, e))
            initializer(self)

    def __call__(self, environ, start_response):
        wsgi_app = self._compiled_wsgi_app
        #print 'wsgi_app', wsgi_app
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
            #print 'wrapping', _tmp_get_name(outermost), 'in', _tmp_get_name(factory)
            outermost = factory(outermost, *args, **kwargs)

        # activate debugger
        if self.settings.get('debug', False):
            from werkzeug import DebuggedApplication
            outermost = DebuggedApplication(outermost, evalex=True)

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
