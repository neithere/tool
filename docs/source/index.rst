.. tool documentation master file, created by
   sphinx-quickstart on Mon Mar 29 01:07:54 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Tool's documentation!
================================

Tool is a lightweight framework for building modular configurable applications.
It is intended to:

* be as unobtrusive as possible. No conventions except for APIs. The modules
  are structured following their own logic;
* store configuration in ordinary Python structures, impose no limits on them
  and support YAML input out of the box;
* encourage modularity by providing a simple but flexible layered API for
  extensions with support for dependencies;
* stick to existing standards and APIs;
* combine existing components: Argh_ (argparse_) for commands, PyDispatcher_
  for signals;
* let user choose non-critical components but ship with batteries included:
  Werkzeug_ for request handling and routing (yes, even this is pluggable!),
  Jinja_ and Mako_ for templates, Doqu_ for modeling and more specialized
  extensions, repoze.who_ for authentication and so on;
* keep even some core functionality (such as routing and serving) as plugins
  so the framework can be used for CLI, web or CLI+web purposes without adding
  weight when it is not needed; moreover, the user can swap almost every
  component without breaking other components.

.. _Argh: http://pypi.python.org/pypi/argh
.. _argparse: http://docs.python.org/dev/library/argparse.html
.. _Doqu: http://packages.python.org/doqu
.. _Jinja: http://jinja.pocoo.org/2/
.. _Mako: http://makotemplates.org
.. _PyDispatcher: http://pypi.python.org/pypi/PyDispatcher/
.. _repoze.who: http://docs.repoze.org/who/1.0/
.. _Werkzeug: http://werkzeug.pocoo.org

Contents:

.. toctree::
   :maxdepth: 3

   tutorial
   application
   cli
   commands
   conf
   context_locals
   debug
   signals
   plugins
   ext
   glossary

Questions
=========

Feel free to ask on the `mailing list`_.

.. _mailing list: http://groups.google.com/group/tool-users

Similar projects
================

* Cement_:
  * has a more complex and much more restrictive API than that of `Tool`.
    In fact, `Tool` also has a complex API for extensions but it is optional.
  * is based on outdated `optparse` and therefore is bound to implement some
    features already present in `argparse` (e.g. nested commands and some
    help-related stuff).
  * depends on `ConfigObj` and stores the settings in ugly *ini files* while
    `Tool` allows the configuration to be stored in any format (favouring the
    clean YAML) including simple Python structures.
  * stores the environment is stored in a module-level variable while Tool
    stores it in extension objects within the application.
  * has the notion of "namespaces" similar to `Tool`'s "features".

.. _Cement: http://pypi.python.org/pypi/cement/

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

