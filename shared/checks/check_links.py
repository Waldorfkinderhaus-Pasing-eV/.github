#!/usr/bin/env python3
"""Check that the relative links of the Markdown files resolve, with their anchors (ADR-0029)."""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path
from urllib.parse import unquote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import baseline  # noqa: E402

INLINE_CODE = re.compile(r'`+[^`]*`+')
# A destination may hold one level of balanced parentheses, as CommonMark allows.
INLINE_LINK = re.compile(r'!?\[(?:[^\[\]]|\[[^\]]*\])*\]\(\s*<?(?P<dest>(?:[^()\s<>]|\([^()\s]*\))+)>?(?:\s+"[^"]*")?\s*\)')
REFERENCE = re.compile(r'^\s{0,3}\[[^\]]+\]:\s*<?(?P<dest>\S+?)>?(?:\s+.*)?$')
SCHEME = re.compile(r'^[A-Za-z][A-Za-z0-9+.-]*:')
INLINE_MARKUP = re.compile(r'!?\[([^\]]*)\]\([^)]*\)|[*`]|<[^>]+>')


def slug(heading, style='github'):
    """The anchor of a heading as GitHub makes it, or as MkDocs does (`"links": {"slug": "mkdocs"}`)."""
    text = INLINE_MARKUP.sub(lambda match: match.group(1) or '', heading).strip().lower()
    if style == 'mkdocs':
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        return re.sub(r'[-\s]+', '-', re.sub(r'[^\w\s-]', '', text)).strip('-')
    return re.sub(r'[^\w\- ]', '', text).replace(' ', '-')


def anchors(text, style='github'):
    seen, found = {}, set()
    for _, line in baseline.outside_fences(text):
        match = baseline.HEADING.match(line)
        if match:
            base = slug(match['text'], style)
            count = seen.get(base, 0)
            seen[base] = count + 1
            found.add(base if count == 0 else f'{base}-{count}')
    return found


def destinations(text):
    for number, line in baseline.outside_fences(text):
        line = INLINE_CODE.sub('', line)
        for match in INLINE_LINK.finditer(line):
            yield number, match['dest']
        reference = REFERENCE.match(line)
        if reference:
            yield number, reference['dest']


def check_file(root, rel, text, cache, style='github'):
    """The links of one Markdown file that do not resolve."""
    found = []
    for number, destination in destinations(text):
        if SCHEME.match(destination) or destination.startswith('//'):
            continue
        target, _, anchor = destination.partition('#')
        target = unquote(target)
        base = Path(root) if target.startswith('/') else (Path(root) / rel).parent
        path = (base / target.lstrip('/')).resolve() if target else (Path(root) / rel).resolve()
        if not path.exists():
            found.append(f'{rel}:{number}: the link target {target} does not exist')
        elif anchor and path.suffix.lower() == '.md' and path.is_file():
            if path not in cache:
                cache[path] = anchors(path.read_text(encoding='utf-8'), style)
            if unquote(anchor).lower() not in cache[path]:
                found.append(f'{rel}:{number}: the anchor #{anchor} is not a heading of {target or rel}')
    return found


def main(argv=None):
    root = baseline.repository_root()
    settings = baseline.configuration(root, 'links')
    names = [name for name in (argv if argv is not None else sys.argv[1:]) or baseline.repository_files(root)
             if name.lower().endswith('.md') and not baseline.excluded(name, settings.get('exclude', ()))]
    findings, cache = [], {}
    for name in names:
        text = (root / name).read_text(encoding='utf-8')
        findings += check_file(root, Path(name).as_posix(), text, cache, settings.get('slug', 'github'))
    return baseline.report(findings, f'Checked the links of {len(names)} Markdown files')


if __name__ == '__main__':
    sys.exit(main())
