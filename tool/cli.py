# -*- coding: utf-8 -*-
"""
Command-line interface
======================

Shell commands subsystem for :term:`CLI`. A thin wrapper around Argh_ which is
in turn a thin wrapper around `argparse` (bundled with Python 2.7+ and
available as a separate package).

The module also initializes colorama_ (for cross-platform terminal text output)
and exports three of its objects: :class:`Fore`, :class:`Back` and
:class:`Style`. If `colorama` is not available, dummy no-op objects are
exported instead.

.. _Argh: http://pypi.python.org/pypi/argh
.. _colorama: http://pypi.python.org/pypi/colorama

Overview
--------

Basic usage::

    from tool.cli import ArghParser, arg

    @arg('word')
    def echo(args):
        print 'You said {0}'.format(args.word)

    if __name__=='__main__':
        parser = ArghParser()
        parser.add_commands([echo])
        parser.dispatch()

Usage with application manager::

    from tool import ApplicationManager
    from tool.cli import ArghParser, arg

    @arg('word')
    def echo(args):
        print 'You said {0}'.format(args.word)

    app = ApplicationManager('conf.yaml')

    if __name__=='__main__':
        app.add_commands([echo])
        app.dispatch()

You can call :meth:`tool.application.ApplicationManager.dispatch` instead of
:func:`dispatch`, they are exactly the same.

To register a command just wrap it in the :func:`command` decorator and import
the module that contains the command before dispatching.

API reference
-------------
"""

__all__ = [
    # argument parsing:
    'ArghParser', 'alias', 'arg', 'command', 'confirm', 'CommandError',
    'plain_signature', 'wrap_errors',
    # terminal colors:
    'Fore', 'Back', 'Style',
]

from argh import (
    ArghParser, alias, arg, command, confirm, CommandError, plain_signature,
    wrap_errors,
)

try:
    from colorama import init, Fore, Back, Style
except ImportError:
    class Dummy(object):
        def __getattr__(self, name):
            return ''
    Fore = Back = Style = Dummy()
    init = lambda x=None:None
