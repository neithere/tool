# -*- coding: utf-8 -*-

# tool
#from tool.commands import command
from tool.routing import url
from tool.ext.documents import default_storage, get_object_or_404
from tool.ext.templating import as_html

# this app
from schema import Note


@url('/')
@url('/<int(4):year>/')
@url('/<int(4):year>/<int(2):month>/')
@as_html('notes.html')
#@as_html('notes.mako')  ← replace templating plugin in config to enable Mako
def notes(request, year=None, month=None):
    db = default_storage()
    notes = Note.objects(db).order_by('date', reverse=True)
    if year:
        notes = notes.where(date__year=year)
        if month:
            notes = notes.where(date__month=month)
    return {'notes': notes}

@url('/<int(4):year>/<int(2):month>/<slug>/')
@as_html('note.html')
def note(request, **kwargs):
    lookups = {
        'date__year': kwargs.pop('year'),
        'date__month': kwargs.pop('month'),
        'slug': kwargs.pop('slug'),
    }
    note = get_object_or_404(Note, **lookups)
    return {'note': note}
