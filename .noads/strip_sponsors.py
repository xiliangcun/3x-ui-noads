"""Remove dedicated advertising modules and guarded placements by structure."""
import json
import re
import shutil
from pathlib import Path

AD_FILES = (
    'frontend/src/api/queries/useSponsorsQuery.ts',
    'frontend/src/lib/sponsors.ts',
    'frontend/src/test/sponsors.test.tsx',
    'internal/web/service/panel/sponsor.go',
    'internal/web/service/panel/sponsor_test.go',
)
AD_DIRECTORIES = ('frontend/src/components/sponsor', 'frontend/src/pages/sponsors')

def replace(text, pattern, allowed=(1,)):
    changed, count = re.subn(pattern, '', text, flags=re.M)
    if count not in allowed:
        raise ValueError(f'Advertising integration changed: expected {allowed} matches, found {count}: {pattern}')
    return changed

def strip_sidebar(text):
    text = replace(text, r"^import SponsorSlot from '@/components/sponsor/SponsorSlot';\n", (0, 1))
    # v3.10.2 removed both sidebar slots upstream; v3.10.0 has two.
    text = replace(text, r'^\s*<SponsorSlot\b[\s\S]*?/>\n', (0, 2))
    for pattern in (
        r'^  CrownOutlined,\n', r"^  \| 'sponsors'\n", r'^  sponsors: CrownOutlined,\n',
        r"^      \{ key: '/sponsors', icon: 'sponsors', title: t\('menu.sponsors'\) \},\n",
        r'^  HeartOutlined,\n', r"^const DONATE_URL = '[^'\n]+';\n",
        r'^function DonateButton\([^\n]+\) \{\n[\s\S]*?^\}\n\n',
    ):
        text = replace(text, pattern)
    return replace(text, r"^\s*<DonateButton ariaLabel=\{t\('menu.donate'\) \|\| 'Donate'\} />\n", (2,))

def strip_palette(text):
    text = replace(text, r'^  CrownOutlined,\n')
    return replace(text, r"^      \{\n        path: '/sponsors',\n[\s\S]*?^      \},\n")

def strip_json(data, kind):
    if kind == 'translation':
        for key in ('sponsors', 'donate'):
            data.get('menu', {}).pop(key, None)
        data.get('pages', {}).pop('sponsors', None)
    else:
        data.get('paths', {}).pop('/sponsors', None)
        schemas = data.get('components', {}).get('schemas', {})
        for key in list(schemas):
            if key.split('.')[-1] in ('Sponsor', 'SponsorList'):
                del schemas[key]
    return data

def strip_sponsors(root):
    root = Path(root).resolve()
    edits = []
    for name, transform in (
        ('frontend/src/layouts/AppSidebar.tsx', strip_sidebar),
        ('frontend/src/components/command-palette/CommandPalette.tsx', strip_palette),
    ):
        file = root / name
        edits.append((file, transform(file.read_text(encoding='utf-8'))))
    for file in (root / 'internal/web/translation').glob('*.json'):
        data = strip_json(json.loads(file.read_text(encoding='utf-8')), 'translation')
        edits.append((file, json.dumps(data, indent=2, ensure_ascii=False) + '\n'))
    for name in ('frontend/public/openapi.json', 'docs/public/openapi.json'):
        file = root / name
        data = strip_json(json.loads(file.read_text(encoding='utf-8')), 'openapi')
        edits.append((file, json.dumps(data, indent=2, ensure_ascii=False) + '\n'))
    for name in (*AD_FILES, *AD_DIRECTORIES):
        file = root / name
        if not file.resolve().is_relative_to(root) or not file.exists():
            raise ValueError('Dedicated advertising module moved; review required: ' + name)
    for file, text in edits:
        file.write_text(text, encoding='utf-8', newline='\n')
    for name in AD_FILES:
        (root / name).unlink()
    for name in AD_DIRECTORIES:
        shutil.rmtree(root / name)
