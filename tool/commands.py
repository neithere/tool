# -*- coding: utf-8 -*-

"""
Built-in commands
=================

Tool provides a set of built-in commands for :doc:`cli`.
"""

from werkzeug import run_simple
#from werkzeug.script import make_shell

from tool import cli
from tool import context


__all__ = ['serve', 'shell']


@cli.command()
def serve(host=('h', 'localhost', 'host'), port=('p', 6060, 'port')):
    "Run development server for your application."
    run_simple(host, port, context.app)

@cli.command()
def shell(plain=('p', False, 'plain')):
    "Spawns an interactive Python shell for your application."
    init_func = lambda: {'context': context}    #{'app': app_factory}
    sh = make_shell(init_func, plain=plain)
    sh()

def make_shell(init_func=None, banner=None, plain=False):
    """Returns an action callback that spawns a new interactive
    python shell.

    :param init_func: an optional initialization function that is
                      called before the shell is started.  The return
                      value of this function is the initial namespace.
    :param banner: the banner that is displayed before the shell.  If
                   not specified a generic banner is used instead.
    :param plain: if set to `True`, default Python shell is used. If set to
                  `False`, bpython or IPython will be used if available (this
                  is the default behaviour).

    This function is identical to that of Werkzeug but allows using bpython.
    """
    banner = banner or 'Interactive Tool Shell'
    init_func = init_func or dict
    def pick_shell(banner, namespace):
        """
        Picks and spawns an interactive shell choosing the first available option
        from: bpython, IPython and the default one.
        """
        if not plain:
            # bpython
            try:
                import bpython
            except ImportError:
                pass
            else:
                bpython.embed(namespace, banner=banner)
                return

            # IPython
            try:
                import IPython
            except ImportError:
                pass
            else:
                sh = IPython.Shell.IPShellEmbed(banner=banner)
                sh(global_ns={}, local_ns=namespace)
                return

        # plain
        from code import interact
        interact(banner, local=namespace)
        return

    return lambda: pick_shell(banner, init_func())
