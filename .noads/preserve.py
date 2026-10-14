"""Restore downstream maintenance files from trusted main, never from upstream."""
import shutil
from pathlib import Path

FILES = ('AGENTS.md', 'README.md', 'NOADS.md')
DIRECTORIES = ('.noads', '.github/workflows')
# These files are deliberately regenerated from the reviewed upstream release.
GENERATED = {'provenance.json', 'upstream-bot-context_test.go.txt'}

def file_map(root, directory):
    base = root / directory
    return {p.relative_to(base).as_posix(): p.read_bytes() for p in base.rglob('*')
            if p.is_file() and '__pycache__' not in p.parts}

def verify_control(source, control):
    for name in FILES:
        if (source / name).read_bytes() != (control / name).read_bytes():
            raise ValueError('Downstream maintenance file overwritten: ' + name)
    for directory in DIRECTORIES:
        actual, expected = file_map(source, directory), file_map(control, directory)
        if directory == '.noads':
            def retained(name):
                return name not in GENERATED and not name.startswith('build/')
            actual = {n: b for n, b in actual.items() if retained(n)}
            expected = {n: b for n, b in expected.items() if retained(n)}
        if actual != expected:
            raise ValueError('Downstream control files overwritten: ' + directory)

def preserve_control(source, control):
    source, control = Path(source).resolve(), Path(control).resolve()
    if source == control:
        raise ValueError('Use an isolated upstream checkout')
    for name in (*FILES, *DIRECTORIES):
        if not (source / name).resolve().is_relative_to(source):
            raise ValueError('Protected path escapes checkout: ' + name)
        if not (control / name).exists():
            raise ValueError('Trusted downstream maintenance file missing: ' + name)
    for directory in DIRECTORIES:
        if (source / directory).exists():
            shutil.rmtree(source / directory)
        shutil.copytree(control / directory, source / directory, ignore=shutil.ignore_patterns('__pycache__'))
    for name in FILES:
        shutil.copy2(control / name, source / name)
    verify_control(source, control)
