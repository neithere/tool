Tutorial
========

The simple echo script
----------------------

This example shows how to create a simple echo application with and without
Tool. First off, let's design the command-line interface::

    $ ./app.py echo "hello there!"
    hello there!

That's what we need. THe interface is extremely simple.

The naïve approach
~~~~~~~~~~~~~~~~~~

The straightforward implementation (with barebones Python) only takes three
lines of code::

    import sys

    if __name__=='__main__':
        return u'You said {0}'.format(sys.argv[1])

It works!

However, the naïve approach is not scalable. When you have more than one
command and more than one argument, the code dealing with ``sys.argv`` becomes
bloated, overcomplicated and unmaintainable. You'll need many
`if/elif/.../else` branches, you'll need to provide helpful error messaes and
documentation. So we need a parser.

Using parser
~~~~~~~~~~~~

...This is why getopt_ was introduced in early versions of Python and later
replaced by more powerful optparse_ which was in turn recently replaced with
argparse_. We'll use the latter::

    import argparse
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument('text')

    if __name__=='__main__':
        args = parser.parse_args(sys.argv[1:])
        return u'You said {0}'.format(args.text)

This approach has several issues:

* the whole application is a single command; you cannot just plug in a
  function as a subcommand with its own arguments.
* imperative approach to *defining* arguments makes it hard to separate them
  from the dispatcher; therefore the application cannot be truly modular.

.. _getopt: http://docs.python.org/library/getopt.html
.. _optparse: http://docs.python.org/library/optparse.html
.. _argparse: http://docs.python.org/library/argparse.html

Using parser with subcommands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We should at least try to solve the subcommands problem. `Argparse`, unlike
`getopt` and `optparse`, directly supports the concept of subcommands. It
creates a subparser for each command so there can be a tree of nested commands,
e.g.::

    $ ./app.py blog add "hello"
    added #1
    $ ./app.py blog ls
    * hello

This is basically a namespace "blog" with two functions acting as subcommands
with each accepting its own set of arguments. A possible implementation::

    import argparse

    def blog_list(args):
        ... do something ...

    def blog_add(args):
        id = add_to_database(args.text)
        print 'added #'+id

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    blog_parser = subparsers.add_parser('blog')
    blog_list_parser = blog_parser.add_parser('ls')
    blog_list_parser.set_defaults(function=blog_list)
    blog_add_parser = blog_parser.add_parser('add')
    blog_add_parser.set_defaults(function=blog_add)
    blog_add_parser.add_argument('text')

    if __name__=='__main__':
        args = parser.parse_args()
        print args.function(args)

The problems:

* still imperative;
* a lot of boilerplate code related to commands.

Using parser: a cleaner way
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Fortunately, there's an excellent wrapper for `argparse` named argh_. It
enables lazy declaration of commands and removes a lot of boilerplate code
while still allowing you to access the `ArgumentParser`::

    from argh import *

    def blog_list(args):
        ... do something ...

    @arg('text')
    def blog_add(args):
        id = add_to_database(args.text)
        print 'added #'+id

    # ...not necessarily in the same module:

    parser = ArghParser()
    parser.add_commands([blog_list, blog_add], namespace='blog')

    if __name__=='__main__':
        parser.dispatch()

The difference is huge: the script now uses declarative approach and therefore
command declarations can be safely decoupled from the dispatcher.

Now it would be great to have a means to assemble the commands in a uniform
way.

.. _argh: http://pypi.python.org/pypi/argh

The Tool application
~~~~~~~~~~~~~~~~~~~~

A Tool application is an :class:`tool.Application` managed by a script. Let's
go straight to an example::

    from tool import Application

    app = Application()

    if __name__=='__main__':
        app.dispatch()

The method :meth:`tool.application.Application.dispatch` does the same as
``parser.dispatch()`` in the previous section. the application object contains
an `ArghParser` instance as ``app.cli_parser``. So you can add and run the
commands this way::

    app = Application()
    app.cli_parser.add_commands([blog_list, blod_add])
    if __name__=='__main__':
        app.dispatch()

But wait, why do we need this new abstraction level if it doesn't do anything
what the argument parser itself can do? Well, it does. It is *extensible*. You
can configure the application object so that it loads certain extensions and
*they* contribute commands.

The configuration is just a dictionary with optional nested structures. We will
use YAML as it is much more readable than Python in terms of defining data
structures::

    extensions:
        blog.setup: null

Save this to `conf.yaml` and let the application know about the configuration::

    app = Application('conf.yaml')

This is equivalent to::

    app = Application({'extensions': {'blog.setup': None}})

Now the application will load the module ``blog``, find a function ``setup`` in
it and run it with two arguments: ``app`` (the application object itself) and
``conf`` (the *extension settings*, in our case they are just set to `None`).

Let's now write the ``blog`` module::

    def blog_list(args):
        ...do somthing...

    def setup(app, conf):
        app.cli_parser.add_commands([blog_list])

Then try running your management script::

    $ ./app.py

...and you will see usage information with ``blog-list`` command in it! Now run
the command::

    $ ./app.py blog-list

The function ``blog_list`` has been called and the result printed. Easy!

So to write pluggable applications with Tool you need to simply add a function
that accepts the application object and then deal with its API. The function
will be called automatically if it is mentioned in the `extensions` section of
the configuration. And you can configure the extension itself by providing some
data instead of `null` (or `None`), e.g.::

    extensions:
        blog.setup:
            theme: green

...and the setup function will be::

    def setup(app, conf):
        assert 'theme' in conf, 'You must specify the theme!'
        return conf

The returned value (the environment) will be stored in the application object
and can be later accessed this way::

    from tool import app

    env = app.get_extension('blog.setup')
    theme = env['theme']

Why not just ``get_extension('blog')``? Because a single extension can provide
multiple configuration functions (or even classes) for different usage
patterns. If you want a single name for all such functions if your extension or
even across multiple extensions (to make them swappable) you can use the
"feature" concept::

    def setup_cli(app):
        pass
    setup_cli.features = 'blog'

    def setup_web(app):
        pass
    setup_web.features = 'blog'

Or with some syntax sugar::

    from tool.plugins import features

    @features('blog')
    def setup_cli(app):
        pass

    @features('blog')
    def setup_web(app):
        pass

Note that `setup_cli` and `setup_web` are mutually exclusive as they implement
the same feature. A third, mixed CLI/web function can be introduced to offer
both interfaces. Of course the web interface will have more dependencies that
the CLI one, so you can make sure that they are also configured::

    from tool.plugins import requires

    @requires('sqlobject.setup', 'werkzeug_routing.setup')
    def setup_web(app):
        pass

The ORM and routing extensions also can be swappable (e.g. Autumn, SQLAlchemy
or Storm may be used instead of SQLObject), so it is safer to reference them by
feature name::

    @requires('{orm}', '{routing}')
    def setup_web(app):
        pass

The application will gather feature names from all configured extensions and
resolve them to actual paths to the configuring functions.

.. note::
    
    The same API cannot be guaranteed across extensions that implement the same
    feature. This is a problem yet to be resolved so the "feature" concept may
    be changed in the future.

Blog
----

Having understood the basics, let's try something practical.

A blog requires some database and a means to expose the records via web
interface. 

.. note::

    TODO.
