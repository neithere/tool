# -*- coding: utf-8 -*-
"""
Signals
=======

Overview
--------

The maintainability of a project largely depends on how loosely its components
are coupled. The mechanism of signals allows different components to:

a) declare possible events,
b) subscribe to possible events, and
c) notify all subscribers of actual events.

The signals dispatcher will take care of that. Thus, there is
no need to (monkey-)patch external code to inject extra logic, you can just
split that logic into pieces and tell the dispatcher to call them at certain
points determined by the external code. This helps keep the components truly
separate.

Tool makes use of `PyDispatcher`_ to send and receive signals. That's an
excellent "multi-producer-multi-consumer signal dispatching mechanism".

.. _PyDispatcher: http://pypi.python.org/pypi/PyDispatcher/

Tool adds two things for convenience's sake:

  * decorator :func:`~called_on`;
  * class :class:`~Signal`.

Both are optional. PyDispatcher will accept any objects (including strings) as
signals. However, it is considered good practice to define them is a uniform
way like this::

    from tool.signals import Signal

    post_save = Signal()

.. note:: on signal naming: think of the phrase "function is called on (signal
    name)". Decent examples: "post_save", "app_ready". In most cases it's a
    short description of an event that has just happened.

Then you import the signal and declare a reciever (some function)::

    from xyz import post_save

    def log_saving_event(**kwargs):
        print '%(sender)s has been saved' % kwargs

Now you'll want to connect the receiver to the signal.

If the signal is a :class:`Signal` instance, the receiver can be connected
using the signal method::

    post_save.connect(log_saving_event)

In most cases the :func:`called_on` decorator would be more suitable::

    @called_on(post_save)
    def log_saving_event(**kwargs):
        print '%(sender)s has been saved' % kwargs

Finally, you can use the generic PyDispatcher function :func:`connect` to
achieve the same result::

        connect(log_saving_event, post_save)

.. note:: no matter how exactly you define, connect and send signals, they do
    *not* depend on Tool. Any Tool-specific signals will work with non-tool
    receivers; any non-Tool signals can be subscribed to with Tool decorators.
    The only requirement is the PyDispatcher library.

API reference
-------------
"""

from functools import wraps
from pydispatch.dispatcher import Anonymous, Any, connect, disconnect, send


__all__ = ['called_on', 'connect', 'called_on', 'disconnect', 'send', 'Signal']


class Signal(object):
    """
    Base class for signals.
    """
    def connect(self, receiver, sender=Any, weak=True):
        """
        Connect receiver to sender for this signal. Wrapper for
        :func:`connect`. Usage::

            from xyz import post_save

            def log_saving_event(**kwargs):
                ...
            # call log_saving_event each time a Note is saved
            post_save.connect(log_saving_event, Note)

        """
        connect(receiver, signal=self, sender=sender, weak=weak)

    def send(self, sender=Anonymous, *arguments, **named):
        """
        Send this signal from sender to all connected receivers. Wrapper for
        :func:`send`. Usage::

            from xyz import post_save

            class Note(Model):
                ...
                def save(self):
                    ...
                    post_save.send(Note)

        """
        send(signal=self, sender=sender, *arguments, **named)

    def disconnect(receiver, sender=Any, weak=True):
        """
        Disconnects given receiver from sender for this signal. Wrapper for
        :func:`disconnect`. Usage::

            from xyz import post_save

            # do not trigger log_saving_event when a Note is saved
            post_save.disconnect(log_saving_event, sender=Note)

        """
        disconnect(receiver, signal=self, sender=sender, weak=weak)


def called_on(signal=Any, sender=Any, weak=True):
    """
    Decorator, connects given function to given signal. Semantic sugar for
    PyDispatcher's ``connect``.

    Usage::

        from tool.signals import called_on

        @called_on(pre_save, SomeModel)
        def log_saving_event(**kwargs):
            print '{sender} has been saved'.format(**kwargs)

    This is semantically equivalent to::

        from tool.signals import connect

        def log_saving_event(**kwargs):
            print '{sender} has been saved'.format(**kwargs)
        connect(log_saving_event, pre_save, SomeModel)

    """
    def inner(receiver):
        connect(receiver, signal=signal, sender=sender, weak=weak)
        return receiver
    return inner
