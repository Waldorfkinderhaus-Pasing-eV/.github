#!/usr/bin/env python3
"""Activate the hooks of the repository: core.hooksPath .githooks, with the three hooks present (ADR-0029)."""
from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import baseline  # noqa: E402

HOOKS_DIRECTORY = '.githooks'
HOOKS = ('pre-commit', 'commit-msg', 'pre-push')
EXECUTABLE = stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH


def missing_hooks(root):
    return [hook for hook in HOOKS if not (Path(root) / HOOKS_DIRECTORY / hook).is_file()]


def main():
    root = baseline.repository_root()
    missing = missing_hooks(root)
    if missing:
        print(f'{HOOKS_DIRECTORY} lacks {", ".join(missing)}; nothing was activated', file=sys.stderr)
        return 1
    if os.name != 'nt':
        for hook in HOOKS:
            path = root / HOOKS_DIRECTORY / hook
            path.chmod(path.stat().st_mode | EXECUTABLE)
    subprocess.run(['git', 'config', 'core.hooksPath', HOOKS_DIRECTORY], cwd=root, check=True)
    print(f'Hooks active: {", ".join(HOOKS)} from {HOOKS_DIRECTORY}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
