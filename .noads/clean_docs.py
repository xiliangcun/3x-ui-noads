"""Remove promotional README sections; reject unfamiliar leftover placements."""
import argparse
import re
import subprocess
from pathlib import Path

# Exact support headings avoid removing technical documentation about support.
SUPPORT_HEADINGS = {
    'support the project', 'support this project', 'support project',
    '支持项目', '支持本项目', '支持專案', '支持此專案',
    'projeyi destekleyin', 'поддержка проекта', '\u067eشتیبانی از پروژه',
    'apoyar el proyecto', 'apoya el proyecto', 'دعم المشروع',
}
PROMO_HEADING = re.compile(
    r'\b(?:sponsors?|sponsorship|sponsored|donations?|donate|advertis(?:ing|ements?)|paid partners?)\b'
    r'|赞助|贊助|捐赠|捐贈|付费推广|付費推廣|спонсор|пожертв|حامیان|حمایت مالی|رعاة|تبرع', re.I)
PROMO_LINK = re.compile(
    r'sponsors\.sanaei\.dev|donate\.sanaei\.dev|buymeacoffee\.com'
    r'|nowpayments\.io/(?:donation|payment)|github\.com/sponsors/'
    r'|patreon\.com|ko-fi\.com|opencollective\.com|liberapay\.com'
    r'|donation-button|default-yellow\.png|img\.shields\.io/[^\s\"<>]*sponsors?', re.I)

def promotional_heading(title):
    title = re.sub(r'<[^>]+>|[*_`#]', '', title).strip().casefold()
    return title in SUPPORT_HEADINGS or bool(PROMO_HEADING.search(title))

def headings(lines):
    """Locate Markdown/HTML headings without treating fenced examples as prose."""
    result, fence = [], None
    for i, line in enumerate(lines):
        marker = re.match(r'^\s{0,3}(`{3,}|~{3,})', line)
        if marker:
            if fence is None:
                fence = marker[1][0]
            elif marker[1][0] == fence:
                fence = None
            continue
        if fence:
            continue
        match = re.match(r'^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$', line)
        if match:
            result.append((i, len(match[1]), match[2]))
            continue
        match = re.match(r'^\s*<h([1-6])\b[^>]*>(.*?)</h\1>\s*$', line, re.I)
        if match:
            result.append((i, int(match[1]), match[2]))
        elif i and re.fullmatch(r'\s{0,3}(?:=+|-+)\s*', line) and lines[i - 1].strip():
            result.append((i - 1, 1 if '=' in line else 2, lines[i - 1].strip()))
    return result

def clean_text(text):
    lines = text.splitlines(keepends=True)
    sections = headings(lines)
    removed = set()
    for n, (start, level, title) in enumerate(sections):
        if not promotional_heading(title):
            continue
        end = next((i for i, depth, _ in sections[n + 1:] if depth <= level), len(lines))
        removed.update(range(start, end))
    cleaned = ''.join(line for i, line in enumerate(lines) if i not in removed)
    # An unknown inline placement is blocked, never silently published.
    assert_clean_text(cleaned)
    return cleaned

def assert_clean_text(text):
    if any(promotional_heading(title) for _, _, title in headings(text.splitlines())):
        raise ValueError('Promotional README section remains')
    if PROMO_LINK.search(text):
        raise ValueError('Promotional README link/image outside a recognized section; review required')

def readmes(root):
    tracked = subprocess.check_output(['git', '-C', str(root), 'ls-files', '-z'], text=True)
    for name in tracked.split('\0'):
        file = root / name
        if file.name.lower().startswith('readme') and file.suffix.lower() in ('.md', '.mdx', '.markdown'):
            if not file.resolve().is_relative_to(root.resolve()):
                raise ValueError('README escapes checkout')
            if file.is_file():
                yield file

def check_docs(root):
    for name in ('.github/FUNDING.yml', '.github/FUNDING.yaml'):
        if (root / name).exists():
            raise ValueError('GitHub funding configuration remains: ' + name)
    for file in readmes(root):
        try:
            assert_clean_text(file.read_text(encoding='utf-8'))
        except ValueError as error:
            raise ValueError(f'{file.relative_to(root)}: {error}') from error

def clean_docs(root):
    changed = []
    # Prepare changes before writing, so an unknown placement stops the cleanup.
    for file in readmes(root):
        original = file.read_text(encoding='utf-8')
        cleaned = clean_text(original)
        if cleaned != original:
            changed.append((file, cleaned))
    for file, cleaned in changed:
        file.write_text(cleaned, encoding='utf-8', newline='\n')
    for name in ('.github/FUNDING.yml', '.github/FUNDING.yaml'):
        (root / name).unlink(missing_ok=True)
    check_docs(root)
    print(f'Removed promotional sections from {len(changed)} READMEs; funding entries absent.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path.cwd())
    args = parser.parse_args()
    clean_docs(args.root.resolve())
