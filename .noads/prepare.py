"""Apply the reviewed patch to an official release and export its build recipe."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

import yaml
from clean_docs import clean_docs
from preserve import preserve_control, verify_control

def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()

def prepare(source, control, tag, sha, repository):
    source, control = source.resolve(), control.resolve()
    if source == control:
        raise ValueError('Use an isolated upstream worktree')
    if not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
        raise ValueError('Only stable semantic version tags are supported')
    if not re.fullmatch(r'[0-9a-f]{40}', sha):
        raise ValueError('Invalid upstream commit')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository):
        raise ValueError('Invalid repository name')
    if git(source, 'rev-parse', 'HEAD') != sha:
        raise ValueError('Upstream checkout does not match the resolved release commit')

    recipe = yaml.safe_load((source / '.github/workflows/release.yml').read_text(encoding='utf-8'))
    platforms = [str(p) for p in recipe['jobs']['build']['strategy']['matrix']['platform']]
    expected = ['amd64', 'arm64', 'armv7', 'armv6', '386', 'armv5', 's390x']
    if platforms != expected:
        raise ValueError('Official platform matrix changed; manual review is required')
    def step(job, name):
        matches = [s['run'] for s in recipe['jobs'][job]['steps'] if s.get('name') == name and 'run' in s]
        if len(matches) != 1:
            raise ValueError(f'Official build step changed: {job}/{name}')
        return matches[0]

    linux = step('build', 'Build 3X-UI')
    windows = step('build-windows', 'Build 3X-UI for Windows (CGO)')
    # Scheduled runs otherwise stamp official stable releases as dev builds.
    for text in (linux, windows):
        if text.count('if [[ "$GITHUB_REF" != refs/tags/* ]]; then') != 1:
            raise ValueError('Official version stamping changed')
    linux = linux.replace('if [[ "$GITHUB_REF" != refs/tags/* ]]; then', 'if false; then')
    windows = windows.replace('if [[ "$GITHUB_REF" != refs/tags/* ]]; then', 'if false; then')
    linux = linux.replace('${{ matrix.platform }}', '${NOADS_PLATFORM}')
    package = step('build', 'Package').replace('${{ matrix.platform }}', '${NOADS_PLATFORM}')
    windows_resources = step('build-windows', 'Copy and download resources')
    windows_package = step('build-windows', 'Package to Zip')
    for text in (linux, windows, package, windows_resources, windows_package):
        if '${{' in text:
            raise ValueError('Unresolved GitHub expression in official build recipe')

    patch = control / '.noads/noads.patch'
    subprocess.run(['git', '-C', str(source), 'apply', '--check', str(patch)], check=True)
    subprocess.run(['git', '-C', str(source), 'apply', str(patch)], check=True)
    for name in ('install.sh', 'update.sh', 'x-ui.sh', 'internal/web/service/panel/panel.go'):
        file = source / name
        text = file.read_text(encoding='utf-8')
        for host in ('github.com', 'raw.githubusercontent.com', 'api.github.com/repos'):
            pattern = re.escape(f'https://{host}/MHSanaei/3x-ui') + r'(?=/|["\s])'
            text = re.sub(pattern, lambda m: f'https://{host}/{repository}', text, flags=re.I)
        file.write_text(text, encoding='utf-8', newline='\n')

    preserve_control(source, control)
    # These checks exclusively validate the upstream Claude bots and their CI
    # documentation. Those workflows are replaced in this distribution.
    bot_checks = source / 'bot_context_test.go'
    if bot_checks.exists():
        names = re.findall(r'^func (Test\w+)\(', bot_checks.read_text(encoding='utf-8'), flags=re.M)
        if not names or any(not name.startswith(('TestAnalystContext', 'TestReview', 'TestBotPrompts')) for name in names):
            raise ValueError('Upstream bot-check scope changed; review before archiving')
        shutil.move(bot_checks, source / '.noads/upstream-bot-context_test.go.txt')
    clean_docs(source)
    shutil.copy2(control / '.noads/tests/noads_routes_test.go', source / 'internal/web/controller/noads_routes_test.go')
    attributes = source / '.gitattributes'
    existing = attributes.read_text(encoding='utf-8') if attributes.exists() else ''
    rule = '.noads/noads.patch -whitespace'
    if rule not in existing.splitlines():
        attributes.write_text(existing.rstrip() + '\n' + rule + '\n', encoding='utf-8', newline='\n')
    provenance = {
        'upstream_repository': 'MHSanaei/3x-ui',
        'upstream_tag': tag,
        'upstream_commit': sha,
        'downstream_repository': repository,
        'patch_sha256': hashlib.sha256(patch.read_bytes()).hexdigest(),
        'variant': 'noads',
    }
    (source / '.noads/provenance.json').write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8')
    build_dir = source / '.noads/build'
    build_dir.mkdir(exist_ok=True)
    linux_header = '#!/usr/bin/env bash\nset -euo pipefail\ncase "${NOADS_PLATFORM:-}" in amd64|arm64|armv7|armv6|386|armv5|s390x) ;; *) exit 1;; esac\n'
    (build_dir / 'linux.sh').write_text(linux_header + linux + '\ncp LICENSE NOADS.md .noads/provenance.json x-ui/\n' + package, encoding='utf-8', newline='\n')
    (build_dir / 'windows.sh').write_text('#!/usr/bin/env bash\nset -euo pipefail\n' + windows, encoding='utf-8', newline='\n')
    (build_dir / 'windows-resources.ps1').write_text('$ErrorActionPreference="Stop"\n' + windows_resources + '\nCopy-Item LICENSE, NOADS.md, .noads/provenance.json x-ui/\n', encoding='utf-8', newline='\n')
    (build_dir / 'windows-package.ps1').write_text('$ErrorActionPreference="Stop"\n' + windows_package, encoding='utf-8', newline='\n')
    verify_control(source, control)
    print(f'Prepared {tag} ({sha[:12]}); official builds retained for all eight platforms.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--control', type=Path, required=True)
    parser.add_argument('--tag', required=True)
    parser.add_argument('--sha', required=True)
    parser.add_argument('--repository', default='xinian5216/3x-ui-private')
    args = parser.parse_args()
    prepare(args.source, args.control, args.tag, args.sha, args.repository)
