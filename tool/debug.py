# -*- coding: utf-8 -*-

"""
Debugging utilities
===================

Werkzeug provides excellent `debugging features`_. This module only provides a
few wrappers for easier coupling of these features with the Tool API.

.. _debugging features: http://werkzeug.pocoo.org/documentation/dev/test.html

"""

from werkzeug import BaseResponse, Client
from tool import context


__all__ = ['client_factory', 'print_url_map']


# http://stackoverflow.com/questions/287871/print-in-terminal-with-colors-using-python
COLOR_BLUE = '\033[94m'
COLOR_GREEN = '\033[92m'
COLOR_WARNING = '\033[93m'
COLOR_FAIL = '\033[91m'
COLOR_ENDC = '\033[0m'


def print_url_map(url_map):
    """
    Pretty-prints given URL map (must be a werkzeug.routing.Map).
    """
    def get_endpoint_repr(endpoint):
        if hasattr(endpoint, '__call__'):
            return u'%s.%s' % (endpoint.__module__, endpoint.__name__)
        return endpoint
    print
    print ' URLS:'
    if not url_map._rules:
        print '   (the URL map does not contain any rules.)'
        print
        return
    max_len = max(len(unicode(rule)) for rule in url_map._rules)
    for rule in url_map._rules:
        rule_label = ''.join([COLOR_BLUE, unicode(rule), COLOR_ENDC])
        endpoint_repr = get_endpoint_repr(rule.endpoint)
        endpoint_label = ''.join([COLOR_GREEN, endpoint_repr, COLOR_ENDC])
        print '   {rule:.<{width}} {endpoint} {arguments}'.format(
            rule = rule_label,
            width = max_len + len(COLOR_BLUE+COLOR_ENDC) + 2,
            endpoint = endpoint_label,
            arguments = '({0})'.format(', '.join(rule.arguments)) if rule.arguments else '',
        )
    print


class ClientResponse(BaseResponse):
    pass


def client_factory():
    """
    Creates and returns a :class:`werkzeug.Client` instance bound to the
    application manager. Allows to send requests to the application. Can be
    used both in automated tests and in the interactive shell.

    Usage::

        from tool.debug import client_factory
        c = client_factory()
        r = c.get('/')
        print r.data

    See Werkzeug documentation, section `debug` for details.
    """
    return Client(context.app_manager, response_wrapper=ClientResponse)
