import hashlib
import io
import tarfile
import urllib.request
from pathlib import Path

version = '8.30.1'
base = f'https://github.com/gitleaks/gitleaks/releases/download/v{version}/'
name = f'gitleaks_{version}_linux_x64.tar.gz'
def fetch(name):
    with urllib.request.urlopen(base + name, timeout=60) as response:
        return response.read()
checksums = fetch(f'gitleaks_{version}_checksums.txt').decode()
expected = next(line.split()[0] for line in checksums.splitlines() if line.split()[-1] == name)
content = fetch(name)
if hashlib.sha256(content).hexdigest() != expected:
    raise RuntimeError('Gitleaks archive checksum mismatch')
dest = Path('/tmp/noads-gitleaks')
dest.mkdir(exist_ok=True)
with tarfile.open(fileobj=io.BytesIO(content), mode='r:gz') as archive:
    member = archive.getmember('gitleaks')
    member.mode = 0o755
    archive.extract(member, dest, filter='data')
print('Verified official Gitleaks ' + version)
