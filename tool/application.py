# -*- coding: utf-8 -*-
"""
Application
===========

This is the core of Tool. You can safely ignore it and use other parts of the
package, but in most cases you will really need the power of
:class:`ApplicationManager`. It's also a good idea to subscribe to signals that
it emits.

Signals
-------

A set of :doc:`signals <signals>` is provided so external modules can subscribe
to important events related to the life cycle of the application.

.. attribute:: pre_app_manager_ready

   fired by :class:`ApplicationManager` just before :attr:`app_manager_ready`.
   Any pre-processing of settings can be done by functions that listen to this
   signal.

.. attribute:: app_manager_ready

   fired by :class:`ApplicationManager` after its instance is fully
   initialized. This includes processing the configuration and loading bundles.
   This does *not* include compilation of the WSGI application stack.

   Note that most bundles, even already loaded, will wait for this signal to
   initialize themselves (e.g. create database connections, etc.), so it is
   possible that they will not be ready when this signal is fired. It's a good
   idea for such bundles to provide their own "ready" signals.

.. attribute:: wsgi_app_ready

   fired by :class:`ApplicationManager` when the WSGI application stack is
   compiled and the resulting WSGI application is ready to be called. Passes
   the application as `wsgi_app`.

.. attribute:: request_ready

   fired by :class:`ApplicationManager` when the request instance is ready;
   passes the :class:`werkzeug.Request` instance as `request`.

.. attribute:: urls_bound

   fired by :class:`ApplicationManager` when the :class:`tool.routing.Map` is
   built and bound to the WSGI environment. Passes the resulting
   :class:`werkzeug.MapAdapter` instance as `map_adapter`.

API reference
-------------

"""

import os.path

from werkzeug import Response, Request, responder, cached_property
from werkzeug.script import make_shell

from tool import cli, conf, signals
from tool import context
from tool.importing import import_module
from tool.routing import find_urls, Map, Rule, Submount


__all__ = [
    'ApplicationManager', 'request_ready', 'urls_bound', 'wsgi_app_ready',
    'app_manager_ready', 'pre_app_manager_ready',
]


# signals
request_ready     = signals.Signal()
urls_bound        = signals.Signal()
wsgi_app_ready    = signals.Signal()
app_manager_ready = signals.Signal()
pre_app_manager_ready = signals.Signal()


class ApplicationManager(object):
    """
    Shell/WSGI application manager. Supports common WSGI middleware. Can be
    configured to run a shell script including a WSGI application server; can
    *be* run as a WSGI application itself.

    :param settings:
        dictionary or path to a YAML file from which the dictionary can be
        obtained
    :param urls:
        a tool.routing.Map object. If not provided, can be constructed later on
        using :meth:`~ApplicationManager.add_url`.

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
        $ ./app.py serve
        $ ./app.py import-some-data

    All these commands are handled by :meth:`~ApplicationManager.dispatch`.
    Commands `shell` and `serve` are added by Tool (see :doc:`commands`,
    command `help` is added by `opster` and all other commands are registered
    elsewhere (e.g. in bundles). See :doc:`cli` for details.

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

    #-----------------+
    #  Magic methods  |
    #-----------------+

    def __init__(self, settings=None, url_map=None):
        self.settings = self._prepare_settings(settings)
        self.url_map = url_map or Map()    # unbound URLs
        # when the WSGI application is compiled, self.url_map is bound to the
        # environment and the resulting MapAdapter instance is set to self.urls
        self.urls = None    # bound URLs

        self.wsgi_stack = []

        self.register()
        self.load_bundles()

        signals.send(pre_app_manager_ready, sender=self)
        signals.send(app_manager_ready, sender=self)

    def __call__(self, environ, start_response):
        wsgi_app = self._compiled_wsgi_app
        #print 'wsgi_app', wsgi_app
        return wsgi_app(environ, start_response)

    #-------------------+
    #  Private methods  |
    #-------------------+

    @cached_property
    def _compiled_wsgi_app(self):
        """
        Processes the stack of WSGI applications, wrapping them one in
        another and executing the result.

            app = tool.Application()
            app.wrap_in(SharedDataMiddleware, {'/media': 'media'})
            app.wrap_in(DebuggedApplication, evalex=True)
            >>> app._compiled_wsgi_app
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

        signals.send(wsgi_app_ready, sender=self, wsgi_app=outermost)

        return outermost

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
            signals.send(request_ready, sender=self, request=context.request)

            # bind URLs
            self.urls = self.url_map.bind_to_environ(environ)
            signals.send(urls_bound, sender=self, map_adapter=self.urls)

            # determine current URL, find and call corresponding view function
            # another approach: http://stackoverflow.com/questions/1796063/werkzeug-mapping-urls-to-views-via-endpoint
            return self.urls.dispatch(find_and_call_view,
                                      catch_http_exceptions=True)
        return app_factory

    def _prepare_settings(self, settings):
        if settings is None:
            return {}
        if isinstance(settings, dict):
            return settings
        if isinstance(settings, basestring):
            return conf.load(settings)
        raise TypeError('expected None, dict or string, got %s' % settings)

    #----------------------+
    #  Public API methods  |
    #----------------------+

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
            template = u'/{0}/' if innermost_dir == 'media' else u'/media/{0}/'
            rule = template.format(innermost_dir)

        # generate unique (and transparent) endpoint
        if not endpoint:
            template = u'{0}' if innermost_dir == 'media' else u'media:{0}'
            endpoint = template.format(innermost_dir)

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
        :param rules:
            list of rules or dotted path to module where the rules are exposed.
        :param submount:
            (string) prefix for the rules
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
        cli.dispatch()

    def get_settings_for_bundle(self, path, default=None):
        """
        Wrapper for :func:`tool.conf.get_settings_for_bundle`. Current
        instance's settings are passed to that function.
        """
        return conf.get_settings_for_bundle(self.settings, path, default)

    def load_bundles(self):
        """
        Loads bundles by importing the modules specified in
        ``config['bundles']``.
        This is not required for the bundles to work.

        If the bundle needs to be initialized in some way, it can simply
        subscribe to signals provided by Tool, e.g.::

            from tool.application import app_manager_ready
            from tool.signals import called_on

            @called_on(app_manager_ready)
            def init_bundle(sender, **kwargs):
                conf = sender.get_settings_for_bundle(__name__)
                app_manager.foo = Foo(conf)    # or better modify the `context`

        The function `init_bundle` in the example above will be called by an
        ApplicationManager instance when it's ready; the function will receive
        the ApplicationManager instance as `sender`. The initializer configures
        itself via :meth:`ApplicationManager.get_settings_for_bundle`.
        """
        for bundle in self.settings.get('bundles', []):
            assert isinstance(bundle, basestring), (
                'cannot load bundle by module path: expected a string, '
                'got {0}'.format(repr(bundle)))
            mod = import_module(bundle)

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
