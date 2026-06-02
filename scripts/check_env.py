#!/usr/bin/env python3
"""Check MXM env vars and print first-run onboarding for research_writer."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    check_env_status,
    export_setup_hint,
    format_first_run_onboarding,
    load_image_config,
    validate_image_api_url,
)


def main() -> int:
    parser = argparse.ArgumentParser(description='Check research_writer MXM environment')
    parser.add_argument('--project-dir', default='.', help='project dir for image.env lookup')
    parser.add_argument('--input-mode', default='web', choices=['local', 'web', 'hybrid'])
    parser.add_argument('--needs-images', action='store_true', help='user requested AI images')
    parser.add_argument('--json', action='store_true', help='machine-readable status')
    parser.add_argument('--quiet', action='store_true', help='only print onboarding when action needed')
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    status = check_env_status(project_dir)

    need_research = status.missing_research and args.input_mode in ('web', 'hybrid')
    need_image = status.missing_image and args.needs_images
    action_needed = need_research or need_image

    payload = {
        'research_ready': status.research_ready,
        'image_ready': status.image_ready,
        'research_source': status.research_source,
        'image_source': status.image_source,
        'input_mode': args.input_mode,
        'needs_images': args.needs_images,
        'action_needed': action_needed,
        'setup_hint': export_setup_hint(),
    }

    if args.json:
        onboarding = format_first_run_onboarding(
            status,
            input_mode=args.input_mode,
            needs_images=args.needs_images,
        )
        payload['onboarding'] = onboarding
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if not args.quiet or action_needed:
        print('research_writer environment check')
        print(f'Project: {project_dir}')
        print()
        if status.research_ready:
            print(f'  MXM_RESEARCH_APIKEY: OK ({status.research_source or "configured"})')
        else:
            print('  MXM_RESEARCH_APIKEY: MISSING')
        if status.image_ready:
            img = load_image_config(project_dir)
            print(f'  MXM_GEN_IMAGE_*: OK ({status.image_source or "configured"})')
            print(f'    URL: {img.api_url}')
            for w in validate_image_api_url(img.api_url):
                print(f'    note: {w}')
        else:
            print('  MXM_GEN_IMAGE_*: MISSING')

    onboarding = format_first_run_onboarding(
        status,
        input_mode=args.input_mode,
        needs_images=args.needs_images,
    )
    if onboarding:
        if not args.quiet:
            print()
        print(onboarding)
    elif not args.quiet:
        print()
        print('All required variables for this mode are configured.')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
