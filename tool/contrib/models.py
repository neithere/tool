# -*- coding: utf-8 -*-

from pymodels import get_storage
from tool.context import context


DEFAULTS = {
    'backend': 'pymodels.backends.tokyo_tyrant',
    'host': 'localhost',
    'port': 1978,
    #'path': '',
}


class StorageProxy(object):
    """
    Syntactic sugar for get_db(). Usage::

        from bundles.models import storage

        def some_view(request):
            return Response(Page.query(storage))

    ...which is just another way to write::

        from glashammer.utils import get_app

        def some_view(request):
            app = get_app()
            return Response(Page.query(app.models_db))
    """
    def __getattr__(self, name):
        if not hasattr(context, 'pymodels_db'):
            raise AttributeError('PyModels bundle must be set up')
        return getattr(context.pymodels_db, name)

storage = StorageProxy()

def setup(config, context):
    """
    Setup the application to use PyModels.
    """
    conf = dict(config.get('pymodels', {}))
    for k in DEFAULTS:
        conf.setdefault(k, DEFAULTS[k])
    context.pymodels_db = get_storage(conf)
