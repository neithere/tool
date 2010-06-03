# -*- coding: utf-8 -*-

"""
Shell commands. A thin wrapper around Opster_.

.. _Opster: http://pypi.python.org/pypi/opster

Basic usage::

    from tool.commands import command, dispatch

    @command()
    def foo():
        print 'bar'

    if __name__=='__main__':
        dispatch()

You can call :meth:`tool.application.ApplicationManager.dispatch` instead of
:func:`dispatch`, they are exactly the same.

To register a command just wrap it in the :func:`command` decorator and import
the module that contains the command before dispatching.
"""

__all__ = ['command', 'dispatch']

from opster import command, dispatch

