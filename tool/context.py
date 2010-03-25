# -*- coding: utf-8 -*-

"""
Context locals. Contains things you want to have in every single view or helper
function or whatever. Thread safe.
"""

from werkzeug import Local, LocalManager


__all__ = ['application', 'context', 'context_manaer']


context = Local()
context_manager = LocalManager([context])
application = context('application')
