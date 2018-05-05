urlsearch
=========

A pair of small programs to index typical webserver directory listings and then
search for arbitrary terms.

Say there is a webserver file listing at `http://example.org/files/` that you
want to be able to search for a specific file recursively. Then you might first
fire up the indexer:
```
$ ./index.py --index=index.db http://example.org/files/
```
and then ask the index for the file you were looking for:
```
$ ./search --index=index.db "important file"
Really important file.doc	http://example.org/files/stuff/old/Really%20important%20file.doc
```

Nothing besides the filenames is indexed and thus searchable. If your search
matches a folder, only the folder itself and not all of its children will be
displayed.
