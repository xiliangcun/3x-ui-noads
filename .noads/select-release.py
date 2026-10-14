"""Find the oldest unprocessed stable upstream release at or above the baseline."""
import json
import os
import re
import urllib.request

def api(path):
    req = urllib.request.Request('https://api.github.com/' + path, headers={
        'Accept': 'application/vnd.github+json',
        'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
        'X-GitHub-Api-Version': '2022-11-28',
    })
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)

def all_releases(repo):
    items = []
    page = 1
    while True:
        batch = api(f'repos/{repo}/releases?per_page=100&page={page}')
        items.extend(batch)
        if len(batch) < 100:
            return items
        page += 1

def version(tag):
    match = re.fullmatch(r'v(\d+)\.(\d+)\.(\d+)', tag)
    return tuple(map(int, match.groups())) if match else None

def select(upstream, downstream, requested=''):
    published = {r['tag_name'] for r in downstream if not r['draft'] and not r['prerelease']}
    candidates = [r for r in upstream if not r['draft'] and not r['prerelease'] and
                  version(r['tag_name']) is not None and version(r['tag_name']) >= (3, 10, 0)]
    if requested:
        if not version(requested) or not any(r['tag_name'] == requested for r in candidates):
            raise ValueError('Requested tag must be a published official stable release >= v3.10.0')
        candidates = [r for r in candidates if r['tag_name'] == requested]
    candidates = sorted((r for r in candidates if r['tag_name'] not in published), key=lambda r: version(r['tag_name']))
    return candidates[0] if candidates else None

if __name__ == '__main__':
    result = select(all_releases('MHSanaei/3x-ui'), all_releases(os.environ['GITHUB_REPOSITORY']), os.environ.get('REQUESTED_TAG', ''))
    values = {'changed': str(bool(result)).lower(), 'tag': result['tag_name'] if result else ''}
    with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as output:
        for key, value in values.items():
            output.write(f'{key}={value}\n')
    if result:
        with open(os.environ['RUNNER_TEMP'] + '/upstream-release.json', 'w', encoding='utf-8') as output:
            json.dump({k: result[k] for k in ('tag_name', 'html_url', 'body', 'published_at')}, output)
    print('Pending official stable release: ' + values['tag'] if result else 'No new stable release.')
