#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import run_script, split_sections, write_deck_outline, write_speaker_notes

STAGES = ('all', 'search', 'images', 'deck', 'notes', 'pdf', 'ppt', 'validate')


def parse_brief_queries(brief_path: Path) -> list[str]:
    if not brief_path.exists():
        return []
    text = brief_path.read_text(encoding='utf-8')
    queries: list[str] = []
    in_table = False
    for line in text.splitlines():
        if line.strip().startswith('| Round'):
            in_table = True
            continue
        if in_table:
            if not line.strip().startswith('|'):
                break
            if line.strip().startswith('|-------'):
                continue
            cols = [c.strip() for c in line.strip().strip('|').split('|')]
            if len(cols) >= 3 and cols[2] and cols[2] not in ('Query', ''):
                queries.append(cols[2])
    return queries


def main() -> int:
    parser = argparse.ArgumentParser(description='Build downstream artifacts from report.md')
    parser.add_argument('--input', required=True, help='path to report.md')
    parser.add_argument('--outdir', required=True, help='output directory')
    parser.add_argument('--sources', default=None, help='path to sources.md (default: sibling of report)')
    parser.add_argument('--title', default=None, help='optional explicit cover title')
    parser.add_argument('--subtitle', default=None, help='optional cover subtitle')
    parser.add_argument('--author', default=None, help='optional cover author')
    parser.add_argument('--date', default=None, help='optional cover date (YYYY-MM-DD)')
    parser.add_argument('--stage', default='all', choices=STAGES, help='run one pipeline stage')
    parser.add_argument('--min-sources', type=int, default=5, help='minimum sources for validate stage')
    parser.add_argument('--assets', default='assets', help='assets directory relative to report.md')
    parser.add_argument('--brief', default=None, help='path to research-brief.md (default: sibling of report)')
    parser.add_argument('--query', action='append', default=[], help='search query (with --stage search)')
    parser.add_argument('--yes', action='store_true', help='skip interactive image generation confirmation')
    args = parser.parse_args()

    report = Path(args.input).resolve()
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    sources = Path(args.sources).resolve() if args.sources else report.parent / 'sources.md'
    brief = Path(args.brief).resolve() if args.brief else report.parent / 'research-brief.md'

    text = report.read_text(encoding='utf-8')
    parsed_title, sections = split_sections(text)
    title = args.title or parsed_title

    deck_outline = outdir / 'deck-outline.md'
    speaker_notes = outdir / 'speaker-notes.md'
    pdf_out = outdir / 'report.pdf'
    ppt_out = outdir / 'report.pptx'
    base = Path(__file__).resolve().parent
    stage = args.stage

    built: list[Path] = []

    if stage == 'search':
        queries = args.query or parse_brief_queries(brief)
        if not queries:
            print('No queries found in brief §3 and none passed via --query', file=sys.stderr)
            return 1
        for i, q in enumerate(queries, 1):
            run_script(
                base / 'search_tavily.py',
                [
                    '--query', q,
                    '--append', str(brief),
                    '--round', f'R{i}',
                ],
            )
    elif stage == 'images':
        img_args = ['--input', str(report), '--assets', args.assets]
        if args.yes:
            img_args.append('--yes')
        run_script(base / 'generate_images.py', img_args)
    elif stage == 'all':
        dry_or_gen = ['--input', str(report), '--assets', args.assets]
        if args.generate_images:
            if args.yes:
                dry_or_gen.append('--yes')
            run_script(base / 'generate_images.py', dry_or_gen)
        else:
            run_script(base / 'generate_images.py', dry_or_gen + ['--dry-run'])

    if stage in ('all', 'deck'):
        write_deck_outline(deck_outline, title, sections)
        built.append(deck_outline)

    if stage in ('all', 'notes'):
        write_speaker_notes(speaker_notes, title, sections)
        built.append(speaker_notes)

    if stage in ('all', 'pdf'):
        pdf_args = [
            '--input', str(report),
            '--output', str(pdf_out),
            '--assets', args.assets,
        ]
        if args.title:
            pdf_args.extend(['--title', args.title])
        if args.subtitle:
            pdf_args.extend(['--subtitle', args.subtitle])
        if args.author:
            pdf_args.extend(['--author', args.author])
        if args.date:
            pdf_args.extend(['--date', args.date])
        if args.generate_images:
            pdf_args.append('--generate-images')
        if args.yes:
            pdf_args.append('--yes')
        run_script(base / 'generate_pdf.py', pdf_args)
        built.append(pdf_out)

    if stage in ('all', 'ppt'):
        if not deck_outline.exists():
            write_deck_outline(deck_outline, title, sections)
        if not speaker_notes.exists():
            write_speaker_notes(speaker_notes, title, sections)
        run_script(
            base / 'generate_ppt.py',
            [
                '--deck', str(deck_outline),
                '--notes', str(speaker_notes),
                '--output', str(ppt_out),
                '--title', title,
            ],
        )
        built.append(ppt_out)

    if stage in ('all', 'validate'):
        validate_args = [
            '--report', str(report),
            '--sources', str(sources),
            '--outdir', str(outdir),
            '--min-sources', str(args.min_sources),
            '--assets', args.assets,
            '--brief', str(brief),
        ]
        run_script(base / 'validate.py', validate_args)

    if built:
        print('Built:')
        for p in built:
            print('-', p)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
