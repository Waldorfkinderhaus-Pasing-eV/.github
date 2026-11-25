"""The repository, its files and its configuration, for the shared checks (ADR-0029, shared/README.md)."""
from __future__ import annotations

import fnmatch
import json
import re
import subprocess
import sys
from pathlib import Path

CONFIGURATION = 'shared/config.json'
BINARY_PROBE_BYTES = 8192
FENCE = re.compile(r'^\s*(```|~~~)')
HEADING = re.compile(r'^(?P<marks>#{1,6})\s+(?P<text>.+?)\s*#*\s*$')


def repository_root(start=None):
    """The top folder of the Git repository that holds the working directory, or `start`."""
    listed = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=start or Path.cwd(), capture_output=True,
                            text=True, check=True).stdout.strip()
    return Path(listed)


def repository_files(root):
    listed = subprocess.run(['git', 'ls-files', '--cached', '--others', '--exclude-standard'], cwd=root,
                            capture_output=True, text=True, check=True).stdout.splitlines()
    return [name for name in listed if (root / name).is_file()]


def configuration(root, section):
    """The section of the repository's shared/config.json, empty when the file or the section is missing."""
    path = Path(root) / CONFIGURATION
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding='utf-8')).get(section, {})


def excluded(name, patterns):
    return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)


def text_of(path):
    """The file as text, or None for a binary file or one that is not UTF-8."""
    data = Path(path).read_bytes()
    if b'\0' in data[:BINARY_PROBE_BYTES]:
        return None
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        return None


def outside_fences(text):
    """The lines of a Markdown text outside fenced code blocks: number and text."""
    fenced = False
    for number, line in enumerate(text.splitlines(), start=1):
        if FENCE.match(line):
            fenced = not fenced
        elif not fenced:
            yield number, line


def sections(text, level):
    """The sections of one heading level: line number, heading and the lines up to the next such heading."""
    found = []
    for number, line in outside_fences(text):
        match = HEADING.match(line)
        if match and len(match['marks']) <= level:
            found.append([number, match['text'], []] if len(match['marks']) == level else None)
        elif found and found[-1] is not None:
            found[-1][2].append(line)
    return [tuple(section) for section in found if section is not None]


def utf8_output():
    """Write UTF-8 to the console streams, which default to the system's code page on Windows."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8', errors='replace')


def report(findings, summary):
    """Print the findings and the summary; the exit status of a check."""
    utf8_output()
    for finding in findings:
        print(finding, file=sys.stderr)
    print(f'{summary}; {len(findings)} findings')
    return 1 if findings else 0
