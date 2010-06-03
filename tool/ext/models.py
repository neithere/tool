# -*- coding: utf-8 -*-

"""
`PyModels`_ is a lightweight framework for mapping Python classes to
schema-less databases. It's the SQLAlchemy for non-relational databases.

.. _PyModels: http://pypi.python.org/pypi/pymodels

Configuration example (in YAML)::

    bundles:
        - tool.ext.models
    pymodels:
        backend: pymodels.backends.tokyo_tyrant
        host: localhost
        port: 1978

The `pymodels` section of configuration is not Tool-specific. You can provide
whatever keywords and values PyModels itself accepts.

More detailed documentation:

* :doc:`conf` (Tool)
* `Backends <http://packages.python.org/pymodels/backends.html>`_ (PyModels)

"""

from pymodels import get_storage
from tool.context_locals import context


DEFAULTS = {
    'backend': 'pymodels.backends.tokyo_tyrant',
    'host': 'localhost',
    'port': 1978,
}


class StorageProxy(object):
    """
    Syntactic sugar for get_db(). Usage::

        from bundles.models import storage

        def some_view(request):
            return Response(Page.query(storage))

    ...which is just another way to write::

        from tool.context_locals import context

        def some_view(request):
            return Response(Page.query(context.models_db))
    """
    def __getattr__(self, name):
        if not hasattr(context, 'pymodels_db'):
            raise AttributeError('PyModels bundle must be set up')
        return getattr(context.pymodels_db, name)


storage = StorageProxy()


def setup(app):
    """
    Setup the application to use PyModels.
    """
    conf = app.settings.get('pymodels', DEFAULTS)
    context.pymodels_db = get_storage(conf)
