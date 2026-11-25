#!/usr/bin/env python3
"""Check that comments and documentation headers are short (ADR-0028, architecture standards/comments.md)."""
from __future__ import annotations

import ast
import io
import re
import sys
import tokenize
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import baseline  # noqa: E402

MAX_COMMENT_LINES = 2
SYNOPSIS_LINES = 1
MAX_REFERENCE_LINES = 3
REFERENCE = re.compile(
    r'https?://|\b(?:ADR|RFC)-\d{4}\b|\bRFC \d+\b|\bISO(?:/IEC)? \d+|\bD\d+\b|\b[A-Z]{2,}(?:-[A-Z]+)*-[A-Z]?\d+\b')
PYTHON = {'.py'}
SHELL = {'.sh', '.bash'}
SLASH = {'.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs'}
POWERSHELL = {'.ps1', '.psm1'}
TLA = {'.tla'}
BICEP = {'.bicep', '.bicepparam'}
YAML = {'.yml', '.yaml'}
YAML_HEADER_PARAMETERS = 0
YAML_DOCUMENT_MARKER = '---'
YAML_BLOCK_SCALAR = re.compile(r'(?:^|:\s|^-\s)\s*[|>][1-9+-]{0,2}$')
YAML_TRAILING_COMMENT = re.compile(r'\s+#.*$')
BOX_LINE = re.compile(r'^[\s#=*~_-]*$')
TLA_LINE, TLA_OPEN, TLA_CLOSE = r'\*', '(*', '*)'
TLA_PRAGMA = re.compile(r'^\s*@(?:type|typeAlias):')
SHELL_DIRECTORIES = ('.githooks',)
SHELL_SHEBANG = re.compile(r'^#!.*\b(?:sh|bash|dash|zsh)\b')
PRAGMA = re.compile(r'^#\s*(?:-\*-|noqa|type:|pragma|shellcheck|region|endregion|yaml-language-server:|yamllint\b|cloud-config$)'
                    r'|^//\s*(?:eslint|@ts-|prettier|#region)')
HELP_KEYWORD = re.compile(r'^\s*\.(?P<word>[A-Z]+)\b(?P<rest>.*)$')
TSDOC_PARAM = re.compile(r'^@param\b')


@dataclass
class Finding:
    path: str
    line: int
    message: str

    def __str__(self):
        return f'{self.path}:{self.line}: {self.message}'


def header_findings(rel, line, lines, parameters):
    """Measure a documentation header: one synopsis line, one line per parameter, then references."""
    content = [text.strip() for text in lines if text.strip()][SYNOPSIS_LINES:]
    references = [text for text in content if REFERENCE.search(text)]
    prose = SYNOPSIS_LINES + len(content) - len(references)
    allowed = SYNOPSIS_LINES + parameters
    found = []
    if prose > allowed:
        found.append(Finding(rel, line, f'documentation header has {prose} lines of text '
                                        f'(at most {allowed}: a synopsis and one per parameter)'))
    if len(references) > MAX_REFERENCE_LINES:
        found.append(Finding(rel, line, f'documentation header has {len(references)} reference lines '
                                        f'(at most {MAX_REFERENCE_LINES})'))
    return found


def comment_findings(rel, blocks):
    return [Finding(rel, start, f'comment of {size} lines (at most {MAX_COMMENT_LINES})')
            for start, size in blocks if size > MAX_COMMENT_LINES]


def blocks_of(numbers):
    """Group sorted line numbers into runs of consecutive lines: (first line, length)."""
    runs = []
    for number in numbers:
        if runs and number == runs[-1][0] + runs[-1][1]:
            runs[-1] = (runs[-1][0], runs[-1][1] + 1)
        else:
            runs.append((number, 1))
    return runs


def python_parameters(node):
    arguments = node.args
    names = [a.arg for a in arguments.posonlyargs + arguments.args + arguments.kwonlyargs]
    names += [a.arg for a in (arguments.vararg, arguments.kwarg) if a]
    return len([name for name in names if name not in ('self', 'cls')])


def check_python(rel, text):
    standalone = []
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type != tokenize.COMMENT:
            continue
        row, column = token.start
        line = token.line
        if line[:column].strip() or (row == 1 and token.string.startswith('#!')) or PRAGMA.match(token.string):
            continue
        standalone.append(row)
    found = comment_findings(rel, blocks_of(standalone))
    for node in ast.walk(ast.parse(text)):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        docstring = ast.get_docstring(node, clean=True)
        if docstring is None:
            continue
        parameters = python_parameters(node) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else 0
        line = node.body[0].lineno
        found += header_findings(rel, line, docstring.splitlines(), parameters)
    return found


def powershell_help(rel, start, lines):
    parameters = 0
    content = []
    for text in lines:
        keyword = HELP_KEYWORD.match(text)
        if keyword:
            parameters += keyword['word'] == 'PARAMETER'
            if keyword['rest'].strip() and keyword['word'] != 'PARAMETER':
                content.append(keyword['rest'])
        else:
            content.append(text)
    return header_findings(rel, start, content, parameters)


def check_lines(rel, text, marker, block_open, block_close, headers=True):
    lines = text.splitlines()
    standalone, found, index = [], [], 0
    while index < len(lines):
        stripped = lines[index].strip()
        if block_open and stripped.startswith(block_open):
            start = index
            if block_close not in lines[index][lines[index].find(block_open) + len(block_open):]:
                index += 1
                while index < len(lines) and block_close not in lines[index]:
                    index += 1
                index = min(index, len(lines) - 1)
            raw = lines[start:index + 1]
            raw[0] = raw[0].split(block_open, 1)[1].lstrip('*')
            raw[-1] = raw[-1].rsplit(block_close, 1)[0]
            body = [re.sub(r'^\s*\*?\s?', '', item) for item in raw]
            found += block_findings(rel, start + 1, block_open, stripped, body, headers)
        elif stripped.startswith(marker) and not (index == 0 and stripped.startswith('#!')) and not PRAGMA.match(stripped):
            standalone.append(index + 1)
        index += 1
    return comment_findings(rel, blocks_of(standalone)) + found


def block_findings(rel, start, block_open, first, body, headers=True):
    if headers and block_open == '<#' and any(HELP_KEYWORD.match(item) for item in body):
        return powershell_help(rel, start, body)
    if headers and block_open == '/*' and first.startswith('/**'):
        parameters = sum(bool(TSDOC_PARAM.match(item.strip())) for item in body)
        return header_findings(rel, start, body, parameters)
    size = len([item for item in body if item.strip()])
    return comment_findings(rel, [(start, size)])


def tla_comment_lines(lines):
    """The comment lines of a TLA+ module, without Apalache's type annotations: number and text."""
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped.startswith(TLA_LINE):
            body = stripped[len(TLA_LINE):]
            if not TLA_PRAGMA.match(body):
                yield index + 1, body
        elif stripped.startswith(TLA_OPEN):
            block = [(index + 1, stripped[len(TLA_OPEN):])]
            while TLA_CLOSE not in block[-1][1] and index + 1 < len(lines):
                index += 1
                block.append((index + 1, lines[index]))
            block[-1] = (block[-1][0], block[-1][1].split(TLA_CLOSE, 1)[0])
            if not TLA_PRAGMA.match(block[0][1]):
                yield from block
        index += 1


def check_tla(rel, text):
    """A run of consecutive comment lines is one block, so a box of one-line (* *) comments counts whole."""
    runs = []
    for number, body in tla_comment_lines(text.splitlines()):
        content = bool(body.strip('*( )\t'))
        if runs and number == runs[-1][0] + runs[-1][1]:
            runs[-1] = (runs[-1][0], runs[-1][1] + 1, runs[-1][2] + content)
        else:
            runs.append((number, 1, int(content)))
    return comment_findings(rel, [(start, size) for start, _, size in runs])


def yaml_comment_lines(lines):
    """The standalone comment lines of a YAML file outside block scalars (`|`, `>`): number and text."""
    scalar_indent = None
    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if scalar_indent is not None and (not stripped or indent > scalar_indent):
            continue
        scalar_indent = indent if YAML_BLOCK_SCALAR.search(YAML_TRAILING_COMMENT.sub('', stripped)) else None
        if stripped.startswith('#') and not PRAGMA.match(stripped):
            yield number, stripped[1:]


def check_yaml(rel, text):
    """The leading comment block is the file's documentation header; every later block is a comment."""
    lines = text.splitlines()
    first_content = next((number for number, line in enumerate(lines, start=1)
                          if line.strip() and not line.strip().startswith('#')
                          and line.strip() != YAML_DOCUMENT_MARKER), len(lines) + 1)
    comments = list(yaml_comment_lines(lines))
    header = [body for number, body in comments if number < first_content and not BOX_LINE.match(body)]
    found = []
    if header:
        found += header_findings(rel, comments[0][0], header, YAML_HEADER_PARAMETERS)
    runs = []
    for number, body in comments:
        if number < first_content:
            continue
        content = int(not BOX_LINE.match(body))
        if runs and number == runs[-1][0] + runs[-1][1]:
            runs[-1] = (runs[-1][0], runs[-1][1] + 1, runs[-1][2] + content)
        else:
            runs.append((number, 1, content))
    return found + comment_findings(rel, [(start, size) for start, _, size in runs])


def language(path, rel, text, shell_directories=SHELL_DIRECTORIES):
    suffix = path.suffix.lower()
    if suffix in PYTHON:
        return 'python'
    if suffix in POWERSHELL:
        return 'powershell'
    in_shell_directory = rel.split('/')[0] in shell_directories
    if suffix in SHELL or (not suffix and (in_shell_directory or SHELL_SHEBANG.match(text.split('\n', 1)[0]))):
        return 'shell'
    if suffix in SLASH:
        return 'slash'
    if suffix in TLA:
        return 'tla'
    if suffix in BICEP:
        return 'bicep'
    if suffix in YAML:
        return 'yaml'
    return None


def check_file(path, rel, shell_directories=SHELL_DIRECTORIES):
    text = baseline.text_of(path)
    kind = language(path, rel, text, shell_directories) if text is not None else None
    if kind == 'python':
        return check_python(rel, text)
    if kind == 'powershell':
        return check_lines(rel, text, '#', '<#', '#>')
    if kind == 'shell':
        return check_lines(rel, text, '#', None, None)
    if kind == 'slash':
        return check_lines(rel, text, '//', '/*', '*/')
    if kind == 'tla':
        return check_tla(rel, text)
    if kind == 'bicep':
        return check_lines(rel, text, '//', '/*', '*/', headers=False)
    if kind == 'yaml':
        return check_yaml(rel, text)
    return []


def main(argv=None):
    root = baseline.repository_root()
    settings = baseline.configuration(root, 'comments')
    shell_directories = SHELL_DIRECTORIES + tuple(settings.get('shell_directories', ()))
    names = (argv if argv is not None else sys.argv[1:]) or baseline.repository_files(root)
    names = [name for name in names if not baseline.excluded(Path(name).as_posix(), settings.get('exclude', ()))]
    findings = []
    for name in names:
        path = Path(name) if Path(name).is_absolute() else root / name
        findings += check_file(path, Path(name).as_posix(), shell_directories)
    return baseline.report(findings, f'Checked comments in {len(names)} files')


if __name__ == '__main__':
    sys.exit(main())
