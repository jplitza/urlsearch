#! /usr/bin/env python3

import argparse
import pickle
from urllib.parse import unquote_plus


def search(index, terms):
    terms = [term.lower() for term in terms]
    index = {id: (parent, name) for id, parent, name in index}

    def compose_url(id, rem):
        if id == 0:
            return rem
        else:
            parent, name = index[id]
            return compose_url(parent, '/'.join((name, rem)))

    for id, item in index.items():
        parent, name = item
        realname = unquote_plus(name)
        if all(term in realname.lower() for term in terms):
            yield (realname, compose_url(parent, name))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Search URLs')
    parser.add_argument(
        'terms',
        nargs='+',
        help='Terms to search for (arbitrary order)',
    )
    parser.add_argument(
        '--index',
        type=argparse.FileType('rb'),
        required=True,
        help='Location of the index file to read from',
    )
    args = parser.parse_args()

    index = pickle.load(args.index)
    args.index.close()

    for result in search(index, args.terms):
        print("\t".join(result))
