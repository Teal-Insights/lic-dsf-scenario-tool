"""Check static HTML/CSS links and resource references in built documentation.

This is a static check, not browser, accessibility or publication acceptance.
It does not execute JavaScript or prove offline behavior. External reading links
are not fetched. Run after prepare_docs, great-docs build and finish_docs.
"""
import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import tinycss2


def css_urls(text):
    """Read CSS URLs, including escaped URLs and quoted @import rules."""
    found = []

    def visit(tokens):
        for token in tokens:
            if token.type == 'error':
                raise ValueError('CSS could not be parsed: ' + token.message)
            if token.type == 'url':
                found.append(token.value)
            elif token.type == 'function' and token.lower_name == 'url':
                args = [x for x in token.arguments if x.type not in ('whitespace', 'comment')]
                if len(args) != 1 or args[0].type != 'string':
                    raise ValueError('Unrecognized CSS url() syntax')
                found.append(args[0].value)
            elif token.type == 'at-rule' and token.lower_at_keyword == 'import':
                args = [x for x in token.prelude if x.type not in ('whitespace', 'comment')]
                if args and args[0].type == 'string':
                    found.append(args[0].value)
            for name in ('prelude', 'content', 'arguments'):
                nested = getattr(token, name, None)
                if nested:
                    visit(nested)

    visit(tinycss2.parse_stylesheet(text, skip_comments=True, skip_whitespace=True))
    return found


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.styles = []
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.in_style = tag == 'style' or self.in_style
        if attrs.get('style'):
            self.styles.append('x {' + attrs['style'] + '}')
        if attrs.get('id'):
            self.ids.add(attrs['id'])
        if attrs.get('href'):
            resource = tag == 'link' and any(x in attrs.get('rel', '').split()
                                           for x in ('stylesheet', 'preload', 'icon'))
            self.links.append((attrs['href'], resource))
        if attrs.get('src'):
            self.links.append((attrs['src'], tag in ('script', 'img', 'iframe', 'source')))
        if attrs.get('srcset'):
            # The generated site uses ordinary URL candidates. Inline data
            # candidates need explicit review rather than ambiguous splitting.
            if 'data:' in attrs['srcset'].lower():
                raise ValueError('Inline data srcset needs explicit review')
            for candidate in attrs['srcset'].split(','):
                if candidate.strip():
                    self.links.append((candidate.strip().split()[0], True))

    def handle_endtag(self, tag):
        if tag == 'style':
            self.in_style = False

    def handle_data(self, data):
        if self.in_style:
            self.styles.append(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', type=Path, default=Path('great-docs/_site'))
    parser.add_argument('--base', default='/lic-dsf-scenario-tool/')
    args = parser.parse_args()
    root = args.site.resolve()
    pages = {}
    for path in root.rglob('*.html'):
        item = Page()
        item.feed(path.read_text(encoding='utf-8'))
        pages[path.resolve()] = item
    if not pages:
        raise SystemExit('No built HTML pages found.')
    failures = []
    checked = 0
    references = {path: list(page.links) for path, page in pages.items()}
    css_files = list(root.rglob('*.css'))
    for path in css_files:
        references.setdefault(path.resolve(), []).extend(
            (value, True) for value in css_urls(path.read_text(encoding='utf-8')))
    for path, page in pages.items():
        for style in page.styles:
            references[path].extend((value, True) for value in css_urls(style))
    for path, links in references.items():
        for value, resource in links:
            url = urlsplit(value)
            if url.scheme or url.netloc:
                if resource and url.scheme != 'data':
                    failures.append((path, value, 'remote page resource'))
                continue
            raw = unquote(url.path)
            if raw.startswith(args.base):
                raw = raw[len(args.base):]
                target = root / raw
            elif raw.startswith('/'):
                target = root / raw.lstrip('/')
            else:
                target = path.parent / raw if raw else path
            target = target.resolve()
            if target.is_dir():
                target /= 'index.html'
            checked += 1
            if not target.is_relative_to(root) or not target.is_file():
                failures.append((path, value, 'missing or outside site'))
            elif url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids:
                failures.append((path, value, 'missing page anchor'))
    for path, value, message in failures[:40]:
        print(f'{path.relative_to(root)}: {message}: {value}')
    if failures:
        raise SystemExit(f'{len(failures)} documentation link/resource failures.')
    print(f'PASS {len(pages)} HTML pages, {len(css_files)} CSS files and {checked} local references. '
          'JavaScript network behavior and browser review remain separate.')


if __name__ == '__main__':
    main()
