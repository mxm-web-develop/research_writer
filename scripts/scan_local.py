#!/usr/bin/env python3
"""Scan local files/folders into local-index.md for research_writer."""
from __future__ import annotations

import argparse
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

TEXT_EXTENSIONS = {'.md', '.txt', '.rst', '.markdown'}
CODE_EXTENSIONS = {'.py', '.ts', '.tsx', '.js', '.jsx', '.go', '.rs', '.java'}
HEADING_RE = re.compile(r'^(#{1,3})\s+(.+)$', re.MULTILINE)
SKIP_DIRS = {
    '.git', 'node_modules', '__pycache__', '.venv', 'venv', 'output', 'dist', 'dist-chrome',
}


def summarize_text(text: str, limit: int = 400) -> str:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith('#')]
    joined = ' '.join(lines)
    joined = re.sub(r'\s+', ' ', joined)
    if len(joined) > limit:
        return joined[:limit] + '...'
    return joined


def extract_headings(text: str) -> list[str]:
    return [m.group(2).strip() for m in HEADING_RE.finditer(text)][:12]


def iter_files(root: Path, include_code: bool) -> list[Path]:
    exts = set(TEXT_EXTENSIONS)
    if include_code:
        exts |= CODE_EXTENSIONS
    files: list[Path] = []
    for path in root.rglob('*'):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name.startswith('.'):
            continue
        if path.suffix.lower() in exts or path.name.lower().startswith('readme'):
            files.append(path)
    return sorted(files)


def scan_path(root: Path, *, include_code: bool, max_files: int) -> list[dict]:
    entries: list[dict] = []
    for path in iter_files(root, include_code)[:max_files]:
        try:
            text = path.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        rel = path.relative_to(root.resolve())
        entries.append(
            {
                'path': rel.as_posix(),
                'headings': extract_headings(text),
                'summary': summarize_text(text),
                'size': path.stat().st_size,
            }
        )
    return entries


def render_index(root: Path, entries: list[dict]) -> str:
    lines = [
        '# Local Index',
        '',
        f'- **Root**: `{root.resolve()}`',
        f'- **Scanned**: {date.today().isoformat()}',
        f'- **Files**: {len(entries)}',
        '',
        '## Files',
        '',
    ]
    for i, e in enumerate(entries, 1):
        lines.append(f'### [{i}] `{e["path"]}`')
        if e['headings']:
            lines.append('- **Headings**: ' + '; '.join(e['headings'][:8]))
        lines.append(f'- **Summary**: {e["summary"]}')
        lines.append('')
    lines.append('## Usage')
    lines.append('')
    lines.append('Reference as local sources in `sources.md` (Publisher = path, URL = file path or file://).')
    return '\n'.join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description='Scan local folder into local-index.md')
    parser.add_argument('--path', required=True, help='folder to scan')
    parser.add_argument('--out', default='local-index.md', help='output markdown path')
    parser.add_argument('--max-files', type=int, default=200)
    parser.add_argument('--include-code', action='store_true')
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.exists():
        print(f'Path not found: {root}', file=sys.stderr)
        return 1

    entries = scan_path(root, include_code=args.include_code, max_files=args.max_files)
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = Path.cwd() / out_path
    out_path.write_text(render_index(root, entries), encoding='utf-8')
    print(f'Scanned {len(entries)} files → {out_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
