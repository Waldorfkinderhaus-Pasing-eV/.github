#!/usr/bin/env python3
"""Find e-mail addresses, GUIDs and public IPv4 addresses that may identify a person or a system (ADR-0029)."""
from __future__ import annotations

import ipaddress
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import baseline  # noqa: E402

ALLOW_FILE = 'shared/personal-data-allow.txt'
EMAIL = re.compile(r'(?<![\w.+-])[A-Za-z0-9._%+-]+@(?P<domain>[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,})\b')
GUID = re.compile(r'(?<![\w-])[0-9a-fA-F]{8}-(?:[0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}(?![\w-])')
IPV4 = re.compile(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.+]*\d)')  # not a version such as 21.0.13.1+2
NUMBERING = re.compile(r'(?:section|version|§|v)\s*$', re.I)
NUMBERING_CONTEXT = 12
# RFC 2606 and RFC 6761: names reserved for examples and tests.
EXAMPLE_DOMAIN = re.compile(r'(?:^|\.)(?:example\.(?:com|org|net)|example|test|invalid|localhost)$', re.I)
FILE_NAME = re.compile(r'\.(?:png|jpe?g|gif|svg|webp|avif|ico)$', re.I)  # logo@2x.png
DEFAULT_EXCLUDED = ('*.svg', '*.min.js', '*.min.css', '*.map')
PLACEHOLDER_DIGITS = 2  # a GUID of at most two distinct digits is invented: aaaaaaaa-…, 7e7e7e7e-…
PUBLIC_MARKER = 'public-constant'
MASK_GUID_CHARACTERS = 8
PATH_PREFIX = 'path:'
DEFAULT_ALLOWED = {'git@github.com'}  # GitHub's SSH address in remote URLs


def allow_list(root):
    """The allowed values and the excluded path patterns of the repository's allow file."""
    values, paths = set(DEFAULT_ALLOWED), [ALLOW_FILE, *DEFAULT_EXCLUDED]
    path = Path(root) / ALLOW_FILE
    if path.is_file():
        for line in path.read_text(encoding='utf-8').splitlines():
            entry = line.split('#', 1)[0].strip()
            if entry.startswith(PATH_PREFIX):
                paths.append(entry[len(PATH_PREFIX):].strip())
            elif entry:
                values.add(entry.lower())
    return values, paths


def mask(kind, value):
    if kind == 'e-mail address':
        return '***@' + value.split('@', 1)[1]
    if kind == 'GUID':
        return value[:MASK_GUID_CHARACTERS] + '-…'
    return '.'.join(value.split('.')[:2]) + '.*.*'


def public_ipv4(text):
    try:
        address = ipaddress.IPv4Address(text)
    except ValueError:
        return False
    return address.is_global


def line_findings(line, allowed):
    """The (kind, value) pairs of one line that are neither allowed nor marked."""
    found = []
    for match in EMAIL.finditer(line):
        domain = match['domain']
        if not (EXAMPLE_DOMAIN.search(domain) or FILE_NAME.search(domain)) and match[0].lower() not in allowed:
            found.append(('e-mail address', match[0]))
    if PUBLIC_MARKER not in line:
        found += [('GUID', match[0]) for match in GUID.finditer(line)
                  if match[0].lower() not in allowed and len(set(match[0].lower()) - {'-'}) > PLACEHOLDER_DIGITS]
    found += [('public IPv4 address', match[0]) for match in IPV4.finditer(line)
              if public_ipv4(match[0]) and match[0] not in allowed
              and not NUMBERING.search(line[max(0, match.start() - NUMBERING_CONTEXT):match.start()])]
    return found


def check_text(rel, text, allowed):
    return [f'{rel}:{number}: {kind} {mask(kind, value)} (allow it in {ALLOW_FILE}, or remove it)'
            for number, line in enumerate(text.splitlines(), start=1) for kind, value in line_findings(line, allowed)]


def main(argv=None):
    root = baseline.repository_root()
    allowed, excluded = allow_list(root)
    names = (argv if argv is not None else sys.argv[1:]) or baseline.repository_files(root)
    findings, checked = [], 0
    for name in names:
        rel = Path(name).as_posix()
        text = None if baseline.excluded(rel, excluded) else baseline.text_of(root / name)
        if text is not None:
            checked += 1
            findings += check_text(rel, text, allowed)
    return baseline.report(findings, f'Checked {checked} text files for personal data')


if __name__ == '__main__':
    sys.exit(main())
