#!/usr/bin/env python3
"""The one list of checks of the hooks and the tag run (ADR-0022, ADR-0029, D2)."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS_DIRECTORY = '.githooks'
HOOKS = ('commit-msg', 'pre-commit', 'pre-push')  # each must be executable in Git, or Linux and macOS skip it
EXECUTABLE_MODE = '100755'
BRANCH_BASE = 'refs/remotes/origin/main'


def hooks_executable():
    """Every hook is recorded as executable in Git (a clone with core.fileMode=false does not record it)."""
    listed = subprocess.run(['git', 'ls-files', '-s', '--', *(f'{HOOKS_DIRECTORY}/{hook}' for hook in HOOKS)],
                            cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
    modes = {line.split('\t', 1)[1]: line.split()[0] for line in listed}
    wrong = [f'{HOOKS_DIRECTORY}/{hook}' for hook in HOOKS if modes.get(f'{HOOKS_DIRECTORY}/{hook}') != EXECUTABLE_MODE]
    for path in wrong:
        print(f'{path} is not executable in Git; run: git update-index --chmod=+x {path}', file=sys.stderr)
    return not wrong


SHARED = tuple((f'Shared check {name}', [sys.executable, f'shared/checks/{name}.py'])
               for name in ('check_drift', 'check_comments', 'check_personal_data', 'check_decisions',
                            'check_readme_agents', 'check_links'))
FAST = (
    ('Whitespace errors and conflict markers in the staged changes', ['git', 'diff', '--cached', '--check']),
    ('The hooks are executable in Git', hooks_executable),
    *SHARED,
)
FULL = (
    ('The hooks are executable in Git', hooks_executable),
    *SHARED,
)


def branch_commit_check():
    """The commit check of the commits on top of origin/main, or None where origin/main is not fetched."""
    found = subprocess.run(['git', 'rev-parse', '--verify', '--quiet', BRANCH_BASE], cwd=ROOT, capture_output=True,
                           check=False)
    if found.returncode != 0:
        return None
    return ('Commit messages of the branch',
            [sys.executable, 'shared/checks/check_commits.py', '--range', f'{BRANCH_BASE}..HEAD'])


def clear_repository_variables():
    """Drop the variables of `git rev-parse --local-env-vars`, so that no check acts on another repository."""
    names = subprocess.run(['git', 'rev-parse', '--local-env-vars'], cwd=ROOT, capture_output=True, text=True,
                           check=True).stdout.split()
    for name in names:
        os.environ.pop(name, None)


def run(checks):
    failed = []
    for name, check in checks:
        print(f'--- {name}', flush=True)
        started = time.monotonic()
        passed = check() if callable(check) else subprocess.run(check, cwd=ROOT, check=False).returncode == 0
        print(f'--- {"passed" if passed else "FAILED"} in {time.monotonic() - started:.1f} s', flush=True)
        if not passed:
            failed.append(name)
    return failed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fast', action='store_true', help='the fast checks of the pre-commit hook')
    args = parser.parse_args(argv)
    checks = FAST
    if not args.fast:  # the fast checks read the index Git is committing; the full validation runs as from a shell
        clear_repository_variables()
        commits = branch_commit_check()
        checks = FULL + ((commits,) if commits else ())
        if not commits:
            print(f'Not run here: the commit check of the branch ({BRANCH_BASE} is not fetched)')
    failed = run(checks)
    if failed:
        print(f'FAILED: {"; ".join(failed)}', file=sys.stderr)
        return 1
    print('All checks passed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
