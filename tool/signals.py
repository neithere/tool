# -*- coding: utf-8 -*-

"""
Tool makes use of `PyDispatcher`_ to send and receive signals. That's an
excellent "multi-producer-multi-consumer signal dispatching mechanism". The
only thing added here is a convenience decorator :func:`~connected`.

.. _PyDispatcher: http://pypi.python.org/pypi/PyDispatcher/

"""

from functools import wraps
from pydispatch.dispatcher import _Any, connect, disconnect, send


__all__ = ['connect', 'connected', 'disconnect', 'send']


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
