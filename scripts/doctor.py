#!/usr/bin/env python3
from __future__ import annotations

import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import find_chrome

MODULES = ['markdown', 'pptx', 'lxml']


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
    chrome = find_chrome()
    if chrome:
        print(f'chrome: OK ({chrome})')
    else:
        ok = False
        print('chrome: MISSING (install Google Chrome or Chromium for PDF export)')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
