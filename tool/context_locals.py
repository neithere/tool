# -*- coding: utf-8 -*-

"""
Context locals
==============

Contains things you want to have in every single view or helper function or
whatever. Thread safe.

Usage::

    from tool import context

    context.foo = 'bar'

"""

from werkzeug import Local, LocalManager


__all__ = ['context', 'context_manager']


context = Local()
context_manager = LocalManager([context])
#application = context('application')
