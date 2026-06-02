#!/usr/bin/env python3
"""Resolve rw-image directives: copy local assets or call GPT-image API (with user consent)."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from images import ImageConfig, load_image_config, materialize_images, pending_generations, parse_rw_image_directives


def main() -> int:
    parser = argparse.ArgumentParser(description='Materialize report images (local copy or AI generation)')
    parser.add_argument('--input', required=True, help='path to report.md')
    parser.add_argument('--assets', default='assets', help='assets directory relative to report')
    parser.add_argument('--api-url', default=None, help='override RW_IMAGE_API_URL')
    parser.add_argument('--api-key', default=None, help='override RW_IMAGE_API_KEY')
    parser.add_argument('--model', default=None, help='override RW_IMAGE_MODEL (default: gpt-image-2)')
    parser.add_argument('--yes', action='store_true', help='skip interactive confirmation')
    parser.add_argument('--skip-failed', action='store_true', help='continue when API returns 4xx/5xx (log and skip)')
    parser.add_argument('--dry-run', action='store_true', help='list pending images only')
    args = parser.parse_args()

    report = Path(args.input).resolve()
    report_dir = report.parent
    config = load_image_config(report_dir, Path(args.assets))
    if args.api_url:
        config.api_url = args.api_url
    if args.api_key:
        config.api_key = args.api_key
    if args.model:
        config.model = args.model

    md_text = report.read_text(encoding='utf-8')
    specs = parse_rw_image_directives(md_text)
    pending = pending_generations(specs, (report_dir / config.assets_dir).resolve())

    if args.dry_run:
        if not specs:
            print('No rw-image directives found.')
            return 0
        print(f'Directives: {len(specs)} | pending generation: {len(pending)}')
        for spec in specs:
            status = 'pending' if spec in pending else 'ready'
            print(f'  - [{spec.id}] mode={spec.mode} status={status}')
        return 0

    try:
        _, messages = materialize_images(
            md_text,
            report_dir,
            config,
            generate=True,
            yes=args.yes,
            skip_failed=args.skip_failed,
        )
    except (RuntimeError, FileNotFoundError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1

    for msg in messages:
        print(msg)
    if not messages:
        print('No image changes needed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
