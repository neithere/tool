Glossary
========

.. admonition:: TODO

    http://docs.repoze.org/bfg/1.2/glossary.html#term-application-registry
    (as inspiration)

.. glossary::
   
    Application
        a `WSGI application`_

    Application manager
        Manager for the :term:`application`. Provides :term:`routing` and
        supports :term:`middleware`. Implemented by
        :class:`tool.application.ApplicationManager`.

    CLI
        Command Line Interface. Implemented by :mod:`tool.cli`.

    Middleware
        ordinary `WSGI middleware`_. It doesn't matter whether you wrap the
        :term:`application` into the middleware using the :term:`application
        manager` or not. However, introspection is much easier if you use the
        manager.

    Routing
        the process of finding the right callable for given request. The
        callable is then returned by the :term:`application`. Tool uses
        Werkzeug_ for routing.

.. _WSGI application: http://wsgi.org/wsgi/
.. _WSGI middleware: http://wsgi.org/wsgi/Middleware_and_Utilities
.. _Werkzeug: http://werkzeug.pocoo.org
