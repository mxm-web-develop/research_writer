#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQ = ROOT / 'templates' / 'requirements.txt'


def run(cmd: list[str]) -> int:
    print('+', ' '.join(cmd))
    return subprocess.call(cmd)


def main() -> int:
    parser = argparse.ArgumentParser(description='Install dependencies for research_writer skill')
    parser.add_argument('--install', action='store_true', help='install python dependencies')
    args = parser.parse_args()

    chrome = None
    try:
        from common import find_chrome

        chrome = find_chrome()
    except Exception:
        pass

    print(f'Skill root: {ROOT}')
    print(f'Python: {sys.executable}')
    print(f'Requirements: {REQ}')
    print(f'Chrome: {"OK (" + str(chrome) + ")" if chrome else "MISSING"}')

    if args.install:
        if not REQ.exists():
            print('requirements.txt not found', file=sys.stderr)
            return 1
        code = run([sys.executable, '-m', 'pip', 'install', '-r', str(REQ)])
        if code != 0:
            print('pip install failed. Try: python3 -m ensurepip --upgrade', file=sys.stderr)
            return code
        print('Dependency installation finished.')
    else:
        print('Dry run only. Re-run with --install to install dependencies.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
