#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import count_sources, split_sections
from doc_types import resolve_document_type
from images import validate_images

REPORT_SECTION_PATTERN = re.compile(r'^##\s+(.+)$', re.MULTILINE)


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate research_writer deliverables')
    parser.add_argument('--report', required=True)
    parser.add_argument('--sources', required=True)
    parser.add_argument('--outdir', default=None, help='output dir with derived artifacts')
    parser.add_argument('--min-sources', type=int, default=None)
    parser.add_argument('--relax-sources', action='store_true')
    parser.add_argument('--assets', default='assets', help='assets directory relative to report.md')
    parser.add_argument('--brief', default=None, help='path to research-brief.md')
    args = parser.parse_args()

    report = Path(args.report)
    sources = Path(args.sources)
    brief = Path(args.brief) if args.brief else report.parent / 'research-brief.md'
    outdir = Path(args.outdir) if args.outdir else None
    errors: list[str] = []
    warnings: list[str] = []

    if not report.exists():
        errors.append(f'missing report: {report}')
    if not sources.exists():
        errors.append(f'missing sources: {sources}')

    doc_spec = resolve_document_type(report, brief if brief.exists() else None)
    min_sources = args.min_sources if args.min_sources is not None else doc_spec.min_sources

    if report.exists():
        text = report.read_text(encoding='utf-8')
        if not brief.exists():
            warnings.append(
                'missing research-brief.md — complete intake/search/reasoning phases first '
                '(see references/intake-and-search.md)'
            )
        _, sections = split_sections(text)
        found = {s['title'] for s in sections}
        for req in doc_spec.required_sections:
            if req not in found:
                warnings.append(
                    f'report missing section for {doc_spec.id} ({doc_spec.label}): {req}'
                )
        if not re.search(r'\d{4}[-/年]', text):
            warnings.append('report may lack date/time context on key facts')
        for w in validate_images(text, report.parent, Path(args.assets)):
            warnings.append(w)

    if sources.exists():
        src_text = sources.read_text(encoding='utf-8')
        n = count_sources(src_text)
        if n < min_sources and not args.relax_sources:
            errors.append(
                f'sources.md has {n} entries; need at least {min_sources} for {doc_spec.id}'
            )
        if 'http' not in src_text and 'https' not in src_text and 'file://' not in src_text:
            warnings.append('sources.md may be missing URLs or local file paths')

    if outdir:
        required_outputs = ['deck-outline.md', 'speaker-notes.md', 'report.pdf']
        if doc_spec.ppt_default:
            required_outputs.append('report.pptx')
        for name in required_outputs:
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

    print(f'Validation passed. (document_type={doc_spec.id})')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
