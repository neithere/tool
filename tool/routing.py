# -*- coding: utf-8 -*-

"""
URL routing. A thin wrapper around Werkzeug's routing module.
"""

import sys
from werkzeug.routing import *
from werkzeug import redirect
from tool.context_locals import context
from tool.importing import import_module, import_whatever


def url(string=None, **kw):
    """
    Decorator for web application views. Marks given function as bindable to
    the given URL.

    Basically it is equivalent to the decorator ``expose`` of CherryPy, however
    we don't try to infer the rule from function signature; instead, we only
    support the easiest case (URL is equal to function name) and require the
    rule to be explicitly defined when the function accepts arguments.


    Usage::

        @url()                # rule not defined, inferred from function name
        def index(request):
            return 'hello'

        @url('/index/')       # same rule, defined explicitly
        def index(request):
            return 'hello'

        @url('/page/<int:page_id>/')
        def page(request, page_id):     # extra args, rule is *required*
            return 'page #%d' % page_id

    The above is roughly same as::

        def index(request):
            return 'hello'
        index.url_rules = [werkzeug.Rule('/index/', endpoint=index)]

    ...and so on.

    The ``url`` decorators can be chained so that the view function is
    available under different URLs::

        @url('/archive/')
        @url('/archive/<int:year>/')
        @url('/archive/<int:year>/<int:month>/')
        def archive(request, **kwargs):
            entries = Entry.objects(db).where(**kwargs)
            return ', '.join(unicode(e) for e in entries)

    """
    def inner(view):
        if 'endpoint' in kw:
            raise NameError('Endpoint must not be defined explicitly when '
                            'using the @url decorator.')
        kw['endpoint'] = view    # = view.__name__

        # infer URL from function name (only simple case without kwargs)
        if not string and 1 < view.__code__.co_argcount:
            raise ValueError('Routing rule must be specified in the @url '
                             'decorator if the wrapped view function '
                             'accepts more than one argument.')
        kw['string'] = string or '/%s/' % view.__name__
        view.url_rules = getattr(view, 'url_rules', [])
        view.url_rules.append(Rule(**kw))
        return view
    return inner

def url_for(endpoint, **kwargs):
    try:
        return context.app_manager.urls.build(endpoint, kwargs)
    except BuildError:
        if isinstance(endpoint, basestring):
            # we store callable endpoints, so try importing
            endpoint = import_whatever(endpoint)
        return context.app_manager.urls.build(endpoint, kwargs)

def find_urls(source):
    """
    Accepts either module or dictionary.

    Returns a cumulative list of rules for all members of given module or
    dictionary.

    How does this work? Any callable object can provide a list of rules as its
    own attribute named ``url_rules``.  The ``url`` decorator adds such an
    attribute to the wrapped object and sets the object as endpoint for rules
    being added. ``find_urls``, however, does not care about endpoints, it
    simply gathers rules scattered all over the place.

    Usage::

        from tool.routing import Map, Submount
        import foo.views

        # define a view exposed at given URL. Note that it is *not* a good idea
        # to mix views with configuration and management code in real apps.
        @url('/hello/')
        def hello(request):
            return 'Hello!'

        # gather URLs from this module (yields the "hello" one)
        local_urls = find_urls(locals())

        # gather URLs from some bundle's views module
        foo_urls = find_urls(foo.views)

        # gather URLs from a module that is not imported yet
        bar_urls = find_urls('bar.views')

        url_map = Map(
            local_urls + [
                Submount('/foo/', foo_urls),
                Submount('/bar/', bar_urls),
            ]
        )

        # ...make app, etc.

    Such approach does not impose any further conventions (such as where to
    place the views) and leaves it up to you whether to store URL mappings and
    views in separate modules or keep them together using the ``url``
    decorator. It is considered good practice, however, to not mix different
    things in the same module.
    """
    if isinstance(source, dict):
        d = source
    else:
        if isinstance(source, basestring):
            source = import_module(source)
        d = dict((n, getattr(source, n)) for n in dir(source))

    def generate(d):
        for name, attr in d.iteritems():
            if hasattr(attr, '__call__') and hasattr(attr, 'url_rules'):
                for rule in attr.url_rules:
                    yield rule
    return list(generate(d))

def redirect_to(endpoint, **kwargs):
    url = url_for(endpoint, **kwargs)
    return redirect(url)
