# -*- coding: utf-8 -*-

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
        print '   %(rule)s %(padding)s %(endpoint)s %(arguments)s' % {
            'rule': rule,
            'padding': '.' * (max_len - len(unicode(rule)) + 2),
            'endpoint': get_endpoint_repr(rule.endpoint),
            'arguments': '(%s)'%', '.join(rule.arguments) if rule.arguments else '',
        }
    print
