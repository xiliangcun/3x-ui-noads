import hashlib
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from clean_docs import clean_text

def gh(*args):
    return subprocess.check_output(['gh', *args], text=True)

def retry(*args):
    for attempt in range(5):
        try:
            return gh(*args)
        except subprocess.CalledProcessError:
            if attempt == 4:
                raise
            time.sleep((attempt + 1) * 3)

def version(tag):
    return tuple(map(int, tag.removeprefix('v').split('.')))

tag, sha, repo = (os.environ[n] for n in ('RELEASE_TAG', 'SOURCE_SHA', 'GITHUB_REPOSITORY'))
if not re.fullmatch(r'v\d+\.\d+\.\d+', tag) or not re.fullmatch(r'[0-9a-f]{40}', sha):
    raise ValueError('Invalid release identifiers')
provenance = json.loads(Path('.noads/provenance.json').read_text())
if provenance['upstream_tag'] != tag or provenance['downstream_repository'] != repo:
    raise ValueError('Source provenance does not match the requested release')

directory = Path('release-artifacts')
expected = [f'x-ui-linux-{p}.tar.gz' for p in ('amd64', 'arm64', 'armv7', 'armv6', '386', 'armv5', 's390x')]
expected.append('x-ui-windows-amd64.zip')
allowed_files = set(expected + [n + '.sha256' for n in expected])
if {p.name for p in directory.iterdir()} != allowed_files:
    raise ValueError('Release assets are incomplete or contain unexpected files')
sums = []
for name in expected:
    checksum, filename = (directory / (name + '.sha256')).read_text().strip().split(maxsplit=1)
    if filename.lstrip('*').strip() != name:
        raise ValueError('Checksum filename mismatch')
    actual = hashlib.sha256((directory / name).read_bytes()).hexdigest()
    if checksum.lower() != actual:
        raise ValueError('Package checksum mismatch: ' + name)
    sums.append(f'{actual}  {name}')
(directory / 'SHA256SUMS').write_text('\n'.join(sums) + '\n')
(directory / 'provenance.json').write_text(json.dumps({**provenance, 'source_commit': sha}, indent=2) + '\n')

upstream = json.loads(Path('.noads/upstream-release.json').read_text())
upstream_notes = clean_text(upstream.get('body') or '')
notes = f'''Unofficial no-ads build of [{tag}]({upstream['html_url']}).

Removed the Sponsors menu/page, overview/sidebar/login paid placements and remote sponsor-list/logo endpoints. Installation and panel/CLI updates follow this repository. Original GPL-3.0 license and attribution are retained.

upstream_commit={provenance['upstream_commit']}
source_commit={sha}
patch_sha256={provenance['patch_sha256']}

All advertising/credential checks, frontend/Go regression tests and all eight platform builds passed before publication. Every package has a SHA-256 sidecar; SHA256SUMS and provenance.json are included.

### Upstream release notes

{upstream_notes}
'''
notes_file = Path(os.environ['RUNNER_TEMP']) / 'noads-release-notes.md'
notes_file.write_text(notes, encoding='utf-8')

releases = json.loads(gh('api', f'repos/{repo}/releases?per_page=100'))
existing = next((r for r in releases if r['tag_name'] == tag), None)
if existing and not existing['draft']:
    raise ValueError('Release already published; immutable assets will not be overwritten')
if existing and existing['target_commitish'] != sha:
    raise ValueError('Existing draft refers to a different commit; refusing to replace it')
# Do not silently overwrite an unrelated pre-existing tag.
if not existing:
    refs = json.loads(gh('api', f'repos/{repo}/git/matching-refs/tags/{tag}'))
    if any(r['ref'] == f'refs/tags/{tag}' for r in refs):
        raise ValueError('Tag already exists without this release; manual review is required')
    retry('release', 'create', tag, '--repo', repo, '--target', sha, '--draft', '--title', tag + ' · No Ads', '--notes-file', str(notes_file))
for file in sorted(directory.iterdir()):
    # A retry may continue an incomplete draft, but never a published release.
    retry('release', 'upload', tag, str(file), '--repo', repo, '--clobber')
# Draft releases have no published tag yet, so the tag endpoint returns 404.
drafts = json.loads(gh('api', f'repos/{repo}/releases?per_page=100'))
draft_id = next(r['id'] for r in drafts if r['tag_name'] == tag and r['draft'])
remote = json.loads(gh('api', f'repos/{repo}/releases/{draft_id}'))
if {a['name'] for a in remote['assets']} != {p.name for p in directory.iterdir()}:
    raise ValueError('Uploaded draft is incomplete')
subprocess.run(['git', 'config', 'credential.https://github.com.helper', '!gh auth git-credential'], check=True)
# Only move main after all checks/builds and every draft upload passed. A
# concurrent human change causes a normal fast-forward rejection, not overwrite.
subprocess.run(['git', 'push', 'origin', f'{sha}:refs/heads/main'], check=True)
published_versions = [version(r['tag_name']) for r in releases if not r['draft'] and not r['prerelease'] and re.fullmatch(r'v\d+\.\d+\.\d+', r['tag_name'])]
latest = not published_versions or version(tag) >= max(published_versions)
retry('release', 'edit', tag, '--repo', repo, '--draft=false', '--prerelease=false', '--latest=' + str(latest).lower(), '--notes-file', str(notes_file))
pending_branch = f'noads/build-{tag}-{os.environ["GITHUB_RUN_ID"]}'
subprocess.run(['gh', 'api', '--method', 'DELETE', f'repos/{repo}/git/refs/heads/{pending_branch}'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(f'Published complete immutable no-ads release {tag}: {len(list(directory.iterdir()))} assets.')
