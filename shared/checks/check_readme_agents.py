#!/usr/bin/env python3
"""Check the required sections of README.md and AGENTS.md and the pointers to AGENTS.md (ADR-0029)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import baseline  # noqa: E402

README_SECTIONS = ('What this is', "Where it fits in WKP's IT", 'Who it is for', 'First steps', 'How it is checked',
                   'Docs, decisions and requirements')
AGENTS_SECTIONS = ('Commands', 'Rules no check enforces', 'Standards')
OVERVIEW_LINK = r'github\.com/Waldorfkinderhaus-Pasing-eV/architecture'
POINTERS = ('CLAUDE.md', '.github/copilot-instructions.md')
MAX_POINTER_LINES = 3
RULE_REFERENCE = re.compile(r'\bADR-\d{4}\b|\bD\d+\b')
LIST_ITEM = re.compile(r'^(?:[-*+]|\d+\.)\s')
CODE = re.compile(r'`[^`]+`|^\s*(```|~~~)', re.M)
FIT, RULES, STANDARDS, COMMANDS = 1, 1, 2, 0  # positions in the section lists above


def required_sections(rel, text, names):
    """Findings for missing or misordered sections; the sections found, by name."""
    found = {name: lines for _, name, lines in baseline.sections(text, 2)}
    present = [name for name in found if name in names]
    if present != list(names):
        missing = [name for name in names if name not in found]
        detail = f'missing: {", ".join(missing)}' if missing else 'out of order'
        return [f'{rel}: the "##" sections must be, in this order: {", ".join(names)} ({detail})'], found
    return [], found


def check_readme(text, settings):
    names = tuple(settings.get('readme_sections', README_SECTIONS))
    findings, found = required_sections('README.md', text, names)
    fit = '\n'.join(found.get(names[FIT], ()))
    if names[FIT] in found and not re.search(settings.get('overview_link', OVERVIEW_LINK), fit):
        findings.append(f'README.md: "{names[FIT]}" must link the architecture overview')
    return findings


def check_agents(text, settings):
    names = tuple(settings.get('agents_sections', AGENTS_SECTIONS))
    findings, found = required_sections('AGENTS.md', text, names)
    if names[COMMANDS] in found and not CODE.search('\n'.join(found[names[COMMANDS]])):
        findings.append(f'AGENTS.md: "{names[COMMANDS]}" must name the commands as code')
    for line in found.get(names[RULES], ()):
        if LIST_ITEM.match(line) and not RULE_REFERENCE.search(line):
            findings.append(f'AGENTS.md: a rule without an ADR or local decision reference: {line.strip()[:80]}')
    if names[STANDARDS] in found and 'standards/' not in '\n'.join(found[names[STANDARDS]]):
        findings.append(f'AGENTS.md: "{names[STANDARDS]}" must link the standards (standards/)')
    return findings


def check_pointer(rel, text):
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) > MAX_POINTER_LINES or 'AGENTS.md' not in text:
        return [f'{rel}: only points to AGENTS.md, in at most {MAX_POINTER_LINES} lines']
    return []


def check_repository(root):
    settings = baseline.configuration(root, 'readme_agents')
    findings = []
    for rel, check in (('README.md', check_readme), ('AGENTS.md', check_agents)):
        path = Path(root) / rel
        findings += check(path.read_text(encoding='utf-8'), settings) if path.is_file() else [f'{rel}: missing']
    for rel in POINTERS:
        path = Path(root) / rel
        if path.is_file():
            findings += check_pointer(rel, path.read_text(encoding='utf-8'))
    return findings


def main():
    return baseline.report(check_repository(baseline.repository_root()), 'Checked README.md, AGENTS.md and pointers')


if __name__ == '__main__':
    sys.exit(main())
