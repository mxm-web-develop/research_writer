#!/usr/bin/env python3
from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import find_chrome, skill_root
from config import export_setup_hint, load_image_config, load_research_config

MODULES = ['markdown', 'pptx', 'lxml', 'pypdf', 'requests']


def main() -> int:
    ok = True
    print('research_writer environment doctor')
    print('Python:', sys.executable)
    for mod in MODULES:
        try:
            importlib.import_module(mod)
            print(f'{mod}: OK')
        except Exception as e:
            ok = False
            print(f'{mod}: MISSING ({e})')
    try:
        importlib.import_module('tavily')
        print('tavily: OK')
    except Exception as e:
        print(f'tavily: MISSING ({e}) — pip install tavily-python')

    chrome = find_chrome()
    if chrome:
        print(f'chrome: OK ({chrome})')
    else:
        ok = False
        print('chrome: MISSING (install Google Chrome or Chromium for PDF export)')

    research = load_research_config()
    image = load_image_config()
    print()
    print('API configuration:')
    if research.ready:
        print('  Tavily (MXM_RESEARCH_APIKEY): OK')
    else:
        print('  Tavily (MXM_RESEARCH_APIKEY): MISSING — use Agent WebSearch fallback')
    if image.ready:
        print(f'  Image gen ({image.model}): OK')
    else:
        print('  Image gen (MXM_GEN_IMAGE_*): MISSING — local images only')

    if not research.ready or not image.ready:
        print()
        print('Setup hint:')
        print(export_setup_hint())

    root = skill_root()
    print()
    print('Build from your project directory (where report.md lives):')
    print(
        f'  python3 {root}/scripts/build_bundle.py '
        '--input report.md --outdir output --sources sources.md'
    )
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
