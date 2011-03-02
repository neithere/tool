# -*- coding: utf-8 -*-

from tool.plugins import BasePlugin

from commands import ls, add, drop


class Blog(BasePlugin):
    identity = 'blog'  # optional but handy for commands
    requires = ('tool.ext.documents', 'routing')
    commands = (ls, add, drop)  # try "./manage.py blog add hello"

    def make_env(self):
        # FIXME this should be done externally; the plugin should only declare
        # the views and URLs, and the configuration should tell where (and
        # whether) to mount them.
        views = '.'.join([__name__, 'views'])
        self.app.plugins['routing'].add_urls(views)
        return {}
