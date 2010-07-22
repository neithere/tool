# -*- coding: utf-8 -*-
"""
Command-line interface
======================

Shell commands subsystem. A thin wrapper around Opster_.

.. _Opster: http://pypi.python.org/pypi/opster

Overview
--------

Basic usage::

    from tool import cli

    @cli.command()
    def foo():
        print 'bar'

    if __name__=='__main__':
        cli.dispatch()

You can call :meth:`tool.application.ApplicationManager.dispatch` instead of
:func:`dispatch`, they are exactly the same.

To register a command just wrap it in the :func:`command` decorator and import
the module that contains the command before dispatching.

API reference
-------------
"""

__all__ = ['command', 'dispatch']

from opster import command, dispatch
