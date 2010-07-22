# -*- coding: utf-8 -*-

"""
Document storage
================

:state: stable
:dependencies: `Docu`_

`Docu`_ is a lightweight Python framework for document databases. It provides a
uniform API for modeling, validation and queries across various kinds of
storages. It's the SQLAlchemy for non-relational databases.

.. _Docu: http://pypi.python.org/pypi/docu

Configuration example (in YAML)::

    bundles:
        documents:
            backend: docu.ext.tokyo_tyrant
            host: localhost
            port: 1978

Or with defaults::

    bundles:
        documents: nil

The configuration is not Tool-specific. You can provide whatever keywords and
values Docu itself accepts.

Default backend chosen by Tool is `Shelve`_ and the data is stored in the file
`docu_shelve.db`. Please note that despite this extension does not require any
packages except for Docu itself, it is also unsuitable for medium to large
volumes of data. However, it offers a simple persistence layer. Please refer to
the `Docu documentation`_ to choose a more efficient backend (for example,
Tokyo Cabinet or MongoDB).

In short, this is what you will get::

    import datetime
    from tool.ext.documents import db
    from docu import Document, validators

    class Person(Document):
        structure = {
            'name': unicode,
            'birth_date': datetime.date
        }
        validators = {'name': [validators.required()]}
        defaults = {'birth_date': datetime.date.today}
        labels = {
            'name': _('Full name'),
            'birth_date': _('Birth date'),
        }
        use_dot_notation = True

    john = Person(name='John')

    print john.name

    john.save(db)

    print Person.objects(db).where(name__startswith='J').count()

Also, :doc:`ext_admin` provides an automatically generated web interface for
all your document classes (if you register them).

More details:

* `Docu documentation`_ (usage examples, tutorial, etc.)
* `Shelve`_ Docu extension reference
* :doc:`ext_admin` (complete web interface for documents)

.. _Docu documentation: http://packages.python.org/docu
.. _Shelve: http://packages.python.org/docu/ext_shelve.html

"""
import werkzeug.exceptions

from tool import context
from tool import dist
from tool.application import app_manager_ready
from tool.signals import called_on

dist.check_dependencies(__name__)

from docu import get_db


__all__ = ['get_object_or_404', 'StorageProxy', 'db']


DEFAULTS = {
    'backend': 'docu.ext.shelve_db',
    'path': 'docu_shelve.db',
}


class StorageProxy(object):
    """
    Syntactic sugar for get_db(). Usage::

        from tool.ext.documents import db

        def some_view(request):
            return Response(Page.objects(db))

    ...which is just another way to write::

        from tool import context

        def some_view(request):
            return Response(Page.objects(context.docu_db))
    """
    def __getattr__(self, name):
        if not hasattr(context, 'docu_db'):
            raise AttributeError('Documents bundle must be set up')
        return getattr(context.docu_db, name)

    def __eq__(self, other_storage):
        # this is important because otherwise doc.save(db) on existing
        # documents will always reset the primary key and create duplicates.
        return context.docu_db == other_storage

    def __len__(self):
        return len(context.docu_db)

    def __repr__(self):
        return '<{cls} for {backend}>'.format(
            cls=self.__class__.__name__, backend=context.docu_db.__module__)


db = StorageProxy()


def get_object_or_404(model, **conditions):
    """
    Returns a Docu model instance that ................................................
    """
    qs = model.objects(db).where(**conditions)
    if not qs:
        raise werkzeug.exceptions.NotFound
    if 1 < len(qs):
        raise RuntimeError('multiple objects returned')
    return qs[0]

@called_on(app_manager_ready)
def setup(**kwargs):
    """
    Setup the ApplicationManager to use Docu.
    """
    manager = kwargs['sender']
    try:
        conf = manager.get_settings_for_bundle(__name__, DEFAULTS)
    except KeyError:
        return False
    context.docu_db = get_db(conf)
