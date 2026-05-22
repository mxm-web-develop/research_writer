#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import REQUIRED_SECTIONS, count_sources, split_sections

REPORT_SECTION_PATTERN = re.compile(r'^##\s+(.+)$', re.MULTILINE)


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate research_writer deliverables')
    parser.add_argument('--report', required=True)
    parser.add_argument('--sources', required=True)
    parser.add_argument('--outdir', default=None, help='output dir with derived artifacts')
    parser.add_argument('--min-sources', type=int, default=5)
    parser.add_argument('--relax-sources', action='store_true')
    args = parser.parse_args()

    report = Path(args.report)
    sources = Path(args.sources)
    outdir = Path(args.outdir) if args.outdir else None
    errors: list[str] = []
    warnings: list[str] = []

    if not report.exists():
        errors.append(f'missing report: {report}')
    if not sources.exists():
        errors.append(f'missing sources: {sources}')

    if report.exists():
        text = report.read_text(encoding='utf-8')
        _, sections = split_sections(text)
        found = {s['title'] for s in sections}
        for req in REQUIRED_SECTIONS:
            if req not in found:
                warnings.append(f'report missing recommended section: {req}')
        if not re.search(r'\d{4}[-/年]', text):
            warnings.append('report may lack date/time context on key facts')

    if sources.exists():
        src_text = sources.read_text(encoding='utf-8')
        n = count_sources(src_text)
        if n < args.min_sources and not args.relax_sources:
            errors.append(f'sources.md has {n} entries; need at least {args.min_sources}')
        if 'http' not in src_text and 'https' not in src_text:
            warnings.append('sources.md may be missing URLs')

    if outdir:
        for name in ('deck-outline.md', 'speaker-notes.md', 'report.pdf', 'report.pptx'):
            p = outdir / name
            if not p.exists():
                errors.append(f'missing output artifact: {p}')

    if warnings:
        print('Warnings:')
        for w in warnings:
            print(' -', w)
    if errors:
        print('Validation FAILED:')
        for e in errors:
            print(' -', e)
        return 1

    print('Validation passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
