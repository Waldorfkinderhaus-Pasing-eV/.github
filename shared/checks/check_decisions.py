#!/usr/bin/env python3
"""Check that decision documents have the required headings and hold no history (ADR-0028, ADR-0029)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import baseline  # noqa: E402

DECISIONS_LOG = 'docs/decisions.md'
ADR_FILE = re.compile(r'^adrs/ADR-\d{4}-[^/]+\.md$')
RFC_FILE = re.compile(r'^rfcs/RFC-\d{4}-[^/]+\.md$')
LOG_TITLE = 'Decisions'
LOG_ENTRY = re.compile(r'^D(?P<number>\d+) — \S')
ADR_SECTIONS = ('Context', 'Decision', 'Consequences', 'Alternatives considered', 'Implementation and verification')
RFC_SECTIONS = ('Problem and scope', 'Context and evidence', 'Requirements and constraints', 'Alternatives',
                'Candidate design and trust boundaries', 'Open decisions', 'Cost and operability',
                'Privacy, security and legal checks', 'Ownership, rollout and rollback', 'Verification',
                'Adversarial review', 'Decision')
HISTORY_MARKERS = (
    r'(?i)\bsuperseded\b', r'(?i)\bset aside\b', r'(?i)\buntil\b[^.\n]{0,80}\bit was\b', r'(?i)\bamended by\b',
    r'\bRecord of\b', r'(?i)\breplaced by (?:D|ADR-)\d+', r'(?i)\bno longer in force\b', r'(?i)\bchanged the same day\b',
)
QUOTED = re.compile(r'`[^`]*`|"[^"\n]*"|“[^”\n]*”|„[^“\n]*“')


def prose_lines(text):
    """The lines outside fenced code, with inline code and quotations removed: number and text."""
    for number, line in baseline.outside_fences(text):
        yield number, QUOTED.sub('', line)


def headings(text, level):
    return [(number, name) for number, name, _ in baseline.sections(text, level)]


def check_sections(rel, text, prefix, sections):
    found = []
    titles = headings(text, 1)
    if not titles or not titles[0][1].startswith(prefix):
        found.append(f'{rel}:1: the title must start with "{prefix}"')
    present = [name for _, name in headings(text, 2)]
    if [name for name in present if name in sections] != list(sections):
        found.append(f'{rel}:1: the sections must be, in order: {", ".join(sections)}')
    return found


def check_log(rel, text, title):
    titles = headings(text, 1)
    found = [] if titles and titles[0][1] == title else [f'{rel}:1: the title must be "# {title}"']
    numbers = {}
    for number, name in headings(text, 2):
        match = LOG_ENTRY.match(name)
        if not match:
            found.append(f'{rel}:{number}: an entry is "## D<number> — <decision>", not "{name}"')
        elif match['number'] in numbers:
            found.append(f'{rel}:{number}: D{match["number"]} is used twice (also line {numbers[match["number"]]})')
        else:
            numbers[match['number']] = number
    return found


def check_history(rel, text, markers):
    patterns = [re.compile(marker) for marker in markers]
    return [f'{rel}:{number}: history marker "{match[0]}" (a decision document holds only the decision in force)'
            for number, line in prose_lines(text) for pattern in patterns if (match := pattern.search(line))]


def check_document(rel, text, settings):
    """The findings for one document, or none when it is not a decision document."""
    markers = tuple(settings.get('history_markers', HISTORY_MARKERS))
    if rel == DECISIONS_LOG:
        found = check_log(rel, text, settings.get('title', LOG_TITLE))
    elif ADR_FILE.match(rel):
        found = check_sections(rel, text, f'{rel[len("adrs/"):][:len("ADR-0000")]}: ', ADR_SECTIONS)
    elif RFC_FILE.match(rel):
        found = check_sections(rel, text, f'{rel[len("rfcs/"):][:len("RFC-0000")]}: ', RFC_SECTIONS)
    else:
        return []
    if baseline.excluded(rel, settings.get('history_exempt', ())):
        return found
    return found + check_history(rel, text, markers)


def check_repository(root):
    settings = baseline.configuration(root, 'decisions')
    findings, checked = [], 0
    for rel in baseline.repository_files(root):
        if rel == DECISIONS_LOG or ADR_FILE.match(rel) or RFC_FILE.match(rel):
            checked += 1
            findings += check_document(rel, (Path(root) / rel).read_text(encoding='utf-8'), settings)
    return findings, checked


def main():
    findings, checked = check_repository(baseline.repository_root())
    return baseline.report(findings, f'Checked {checked} decision documents')


if __name__ == '__main__':
    sys.exit(main())
