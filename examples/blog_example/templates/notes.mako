<h1>Notes</h1>

<p>There are ${ notes.count() or "no" } notes.</p>

<dl>
% for note in notes:
    <dt>${ note.date }</dt>
        <dd><a href="${ note.get_url() }">${ note.text }</a></dd>
% endfor
</dl>
