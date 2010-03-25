# -*- coding: utf-8 -*-

"""
This is a very thin wrapper around PyDispatcher. Take a look at its
documentation for API reference.
"""

from functools import wraps
from pydispatch.dispatcher import _Any, connect, disconnect, send


__all__ = ['connect', 'connected', 'disconnect', 'fire_on', 'send']


def connected(*args, **kwargs):
    """
    Decorator, connects given function to given signal. Semantic sugar for
    PyDispatcher's ``connect``.

    Usage::

        from tool.signals import connected

        @connected(pre_save, SomeModel)
        def log_saving_event(**kwargs):
            print '%(sender)s has been saved' % kwargs

    This is semantically equivalent to::

        from tool.signals import connect

        def log_saving_event(**kwargs):
            print '%(sender)s has been saved' % kwargs
        connect(log_saving_event, pre_save, SomeModel)

    """
    def inner(f):
        connect(f, *args, **kwargs)
        return f
    return inner
