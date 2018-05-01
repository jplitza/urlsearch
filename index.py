#! /usr/bin/env python3

import argparse
import requests
import html.parser
import logging
import pickle
from collections import defaultdict
from urllib.parse import urljoin, urlsplit, urlunsplit, quote, unquote


class FileTree(defaultdict):
    __auto_id = 0

    def __init__(self, *args, **kwargs):
        self.id = FileTree.__auto_id
        FileTree.__auto_id += 1
        super().__init__(FileTree, *args, **kwargs)

    def add(self, path):
        if path:
            self[path[0]].add(path[1:])

    def has(self, path):
        if not path:
            return True

        if path[0] in self:
            return self[path[0]].has(path[1:])

    def flatten(self, parent=None):
        for name, child in self.items():
            yield (child.id, self.id, name)
            yield from child.flatten()


class MyHTMLParser(html.parser.HTMLParser):
    def __init__(self):
        self.links = []
        super().__init__()

    def reset(self):
        self.links = []
        super().reset()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])


def normalize_url(url):
    split = urlsplit(url)
    return urlunsplit((
        split.scheme,
        split.netloc.lower(),
        quote(unquote(split.path)),
        "",
        "",
    ))


def crawl(roots, maxlength=51200, timeout=1):
    roots = tuple(map(normalize_url, roots))

    found = FileTree()
    for root in roots:
        found.add(root)

    queue = list(roots)
    parser = MyHTMLParser()
    logger = logging.getLogger('URLSearch')
    session = requests.Session()

    while len(queue) > 0:
        url = queue.pop(0)
        try:
            with session.get(url, timeout=timeout) as req:
                if not req.ok:
                    logger.debug(
                        'HEAD request for %s returned HTTP status code %d',
                        url,
                        req.status_code,
                    )
                    continue

                if req.headers['Content-Type'] != 'text/html' and not \
                        req.headers['Content-Type'].startswith('text/html;'):
                    logger.debug(
                        'URL %s is of type %s, not text/html',
                        url,
                        req.headers['Content-Type'],
                    )
                    continue

                if int(req.headers.get('Content-Length', 0)) > maxlength:
                    logger.debug(
                        'URL %s is longer than %d bytes',
                        url,
                        maxlength,
                    )
                    continue

                parser.feed(req.text)
            parser.close()

            for link in parser.links:
                link = normalize_url(urljoin(url, link))
                if link.startswith(roots):
                    path = link.rstrip('/').split('/')
                    if not found.has(path):
                        found.add(path)
                        if link.endswith('/'):
                            queue.append(link)

            parser.reset()
        except requests.exceptions.RequestException:
            logging.exception("Exception while fetching URL %s", url)

    return found


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Index URLs')
    parser.add_argument(
        'URLs',
        nargs='+',
        help='List of URLs that serves both as starting point as well as root filter',
    )
    parser.add_argument(
        '--index',
        type=argparse.FileType('wb'),
        required=True,
        help='Location of the index file to write to',
    )
    args = parser.parse_args()

    links = crawl(args.URLs)
    pickle.dump(list(links.flatten()), args.index)
    args.index.close()
