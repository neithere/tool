# -*- coding: utf-8 -*-
"""
Commands
========

This module provides the blog's command-line interface. It is implemented by
functions :func:`list` and :func:`add`. They are available as ``blog list`` and
``blog add`` respectively provided that you prepare the application as
follows::

    >>> from tool import ApplicationManager
    >>> app = ApplicationManager('test_conf.yaml')

And then call::

    app.dispatch()

Here's how the commands work (note that this is Python API, not CLI)::

    >>> cmd = lambda args: app.cli_parser.dispatch(args.split())

    >>> cmd('blog ls')
    There are no notes in the database.

    >>> cmd('blog add Hello!') # doctest: +ELLIPSIS
    Note has been added with primary key ...

    >>> cmd('blog add Second') # doctest: +ELLIPSIS
    Note has been added with primary key ...

    >>> cmd('blog ls') # doctest: +ELLIPSIS
    There are 2 notes:
    ---
    #0 ... Second
    #1 ... Hello!

    >>> cmd('blog drop -n 1') # doctest: +ELLIPSIS
    Note "Hello!" (...) has been deleted.

    >>> cmd('blog drop --all')
    All notes have been deleted.

    >>> cmd('blog ls')
    There are no notes in the database.

"""

# tool
from tool.cli import arg
from tool.ext.documents import default_storage

# this app
from schema import Note


def ls(args):
    "Lists all existing notes."
    db = default_storage()
    notes = Note.objects(db).order_by(['date', 'text'], reverse=True)
    notes_cnt = notes.count()
    if notes_cnt:
        print('There are {0} notes:'.format(notes_cnt))
        print('---')
        for num, note in enumerate(notes):
            print(u'#{num} {date} {text}'.format(num=num, **note))
    else:
        print('There are no notes in the database.')

@arg('text')
def add(args):
    "Creates a note with given text."
    db = default_storage()
    pk = Note(text=args.text.decode('utf-8')).save(db)
    print('Note has been added with primary key {0}.'.format(pk))

@arg('-n', '--number', type=int, help='which note to delete (as in list)')
@arg('-a', '--all', action='store_true', help='drop all notes')
def drop(args):
    """Deletes given notes from the database. If note number is not specified,
    deletes all notes.
    """
    db = default_storage()
    notes = Note.objects(db).order_by(['date', 'text'], reverse=True)
    if args.number:
        choices = dict(enumerate(notes))
        try:
            note = choices[args.number]
        except KeyError:
            print('There is no note #{0}'.format(args.number))
        else:
            note.delete()
            print('Note "{text}" ({date}) has been deleted.'.format(**note))
    elif args.all:
        notes.delete()
        print('All notes have been deleted.')
    else:
        print args
        print('Please specify either --number or --all.')
