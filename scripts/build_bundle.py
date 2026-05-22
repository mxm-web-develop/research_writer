#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import run_script, split_sections, write_deck_outline, write_speaker_notes

STAGES = ('all', 'deck', 'notes', 'pdf', 'ppt', 'validate')


def main() -> int:
    parser = argparse.ArgumentParser(description='Build downstream artifacts from report.md')
    parser.add_argument('--input', required=True, help='path to report.md')
    parser.add_argument('--outdir', required=True, help='output directory')
    parser.add_argument('--sources', default=None, help='path to sources.md (default: sibling of report)')
    parser.add_argument('--title', default=None, help='optional explicit title')
    parser.add_argument('--stage', default='all', choices=STAGES, help='run one pipeline stage')
    parser.add_argument('--min-sources', type=int, default=5, help='minimum sources for validate stage')
    args = parser.parse_args()

    report = Path(args.input).resolve()
    outdir = Path(args.outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    sources = Path(args.sources).resolve() if args.sources else report.parent / 'sources.md'

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

    if stage in ('all', 'deck'):
        write_deck_outline(deck_outline, title, sections)
        built.append(deck_outline)

    if stage in ('all', 'notes'):
        write_speaker_notes(speaker_notes, title, sections)
        built.append(speaker_notes)

    if stage in ('all', 'pdf'):
        run_script(
            base / 'generate_pdf.py',
            ['--input', str(report), '--output', str(pdf_out), '--title', title],
        )
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
        ]
        run_script(base / 'validate.py', validate_args)

    if built:
        print('Built:')
        for p in built:
            print('-', p)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
