#!/usr/bin/env python3
"""Check that the shared checks equal their manifest, and the manifest that of the architecture commit (ADR-0029)."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import baseline  # noqa: E402

CHECKS = 'shared/checks'
MANIFEST = 'shared/checks/MANIFEST.json'
SOURCE = 'shared/SOURCE.json'
COVERED = '*.py'


def digest(path):
    """SHA-256 of the file with LF line ends, so that a checkout with CRLF has the same digest."""
    return hashlib.sha256(Path(path).read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def build_manifest(folder):
    return {'files': {path.name: digest(path) for path in sorted(Path(folder).glob(COVERED))}}


def check_folder(root):
    """Findings where the files of shared/checks differ from MANIFEST.json beside them."""
    manifest_path = Path(root) / MANIFEST
    if not manifest_path.is_file():
        return [f'{MANIFEST}: missing (vendor the shared checks from the architecture repository)']
    expected = json.loads(manifest_path.read_text(encoding='utf-8'))['files']
    actual = build_manifest(Path(root) / CHECKS)['files']
    findings = [f'{CHECKS}/{name}: missing' for name in expected if name not in actual]
    findings += [f'{CHECKS}/{name}: differs from {MANIFEST}' for name in expected
                 if name in actual and actual[name] != expected[name]]
    findings += [f'{CHECKS}/{name}: not in {MANIFEST}' for name in actual if name not in expected]
    return findings


def check_source(root, architecture):
    """Findings where MANIFEST.json differs from the manifest of the commit SOURCE.json names."""
    source_path = Path(root) / SOURCE
    if not source_path.is_file():
        return [f'{SOURCE}: missing (it names the architecture commit the checks were vendored from)']
    commit = json.loads(source_path.read_text(encoding='utf-8'))['commit']
    shown = subprocess.run(['git', 'show', f'{commit}:{MANIFEST}'], cwd=architecture, capture_output=True,
                           text=True, check=False)
    if shown.returncode != 0:
        return [f'{SOURCE}: the architecture repository has no {MANIFEST} at {commit[:12]} (fetch it, or re-vendor)']
    local = json.loads((Path(root) / MANIFEST).read_text(encoding='utf-8'))
    if json.loads(shown.stdout) != local:
        return [f'{MANIFEST}: differs from the manifest of architecture {commit[:12]}']
    return []


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', help='an architecture clone, to compare the manifest with the vendored commit')
    parser.add_argument('--write', action='store_true', help='rewrite MANIFEST.json (the architecture repository only)')
    args = parser.parse_args(argv)
    root = baseline.repository_root()
    if args.write:
        if (root / SOURCE).is_file():
            parser.error(f'{SOURCE} exists: a vendored copy is changed in the architecture repository, not here')
        (root / MANIFEST).write_text(json.dumps(build_manifest(root / CHECKS), indent=2) + '\n', encoding='utf-8',
                                     newline='\n')
    findings = check_folder(root)
    if (root / SOURCE).is_file() and args.source:
        findings += check_source(root, Path(args.source))
    elif (root / SOURCE).is_file():
        print(f'Not compared with the architecture repository: give --source PATH to compare {MANIFEST}')
    return baseline.report(findings, f'Checked the shared checks against {MANIFEST}')


if __name__ == '__main__':
    sys.exit(main())
