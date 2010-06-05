.. tool documentation master file, created by
   sphinx-quickstart on Mon Mar 29 01:07:54 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to tool's documentation!
================================

Tool is a lightweight web/console framework. It is intended to:

* be as unobtrusive as possible. No conventions except for APIs. The modules
  are structured following their own logic;
* stick to existing standards and APIs, don't invent own (except for
  convenience wrappers); 
* combine existing components: `Werkzeug`_ for request handling and routing,
  `PyDispatcher`_ for signals, `Opster`_ for commands;
* let user choose non-critical components but ship with batteries included
  (`Jinja`_ for templates, `PyModels`_ for modeling and more specialized
  extensions).

.. _Werkzeug: http://werkzeug.pocoo.org
.. _PyDispatcher: http://pypi.python.org/pypi/PyDispatcher/
.. _Opster: http://pypi.python.org/pypi/opster
.. _Jinja: http://jinja.pocoo.org/2/
.. _PyModels: http://packages.python.org/pymodels

There is no such thing as a "Tool module" as opposed to mere "Python modules".
Any Python module can be plugged into a Tool project as long as that module
makes use of at least one of the basic external components, i.e. provides
commands, fires or listens to signals, provides standard WSGI middleware,
defines routing rules, etc. It is extremely easy to make an ordinary script or
package (or even another framework's module) Tool-compatible. Moreover, there
are already tons of such components. Oh, the joy of respecting the standards!

Contents:

.. toctree::
   :maxdepth: 2

   application
   commands
   conf
   context_locals
   debug
   importing
   routing
   signals
   ext

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

