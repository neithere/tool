# -*- coding: utf-8 -*-

"""
URL routing. A thin wrapper around Werkzeug's routing module.
"""

from werkzeug.routing import *
from tool.context import context


def url(string=None, **kw):
    """
    Decorator for web application views. Marks given function as bindable to
    the given URL.

    Basically it is equivalent to the decorator ``expose`` of CherryPy, however
    we don't try to infer the rule from function signature; instead, we only
    support the easiest case (URL is equal to function name) and require the
    rule to be explicitly defined when the function accepts arguments.

    Can be chained so that the view function is available under different URLs.

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

        #context.urls = getattr(context, 'urls', Map())
        #context.urls.add(Rule(rule, **kw))
        #context.views = getattr(context, 'views', ViewFinder())
        #context.views.add_view(endpoint, f)

        view.url_rules = getattr(view, 'url_rules', [])
        view.url_rules.append(Rule(**kw))
        return view
    return inner

def find_in(mod_or_dict):
    """
    Accepts either module or dictionary.
    Returns a cumulative list of rules for all objects in given module or
    dictionary that are a) callable, and b) have the attribute ``url_rules``.
    """
    if isinstance(mod_or_dict, dict):
        d = mod_or_dict
    else:
        d = dict((n, getattr(mod_or_dict, n)) for n in dir(mod_or_dict))

    def generate(d):
        for name, attr in d.iteritems():
            if hasattr(attr, '__call__') and hasattr(attr, 'url_rules'):
                for rule in attr.url_rules:
                    yield rule
    return list(generate(d))
