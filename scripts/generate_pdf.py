#!/usr/bin/env python3
"""Markdown -> PDF using Chrome/Chromium headless."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import find_chrome


def chrome_html_to_pdf(chrome: Path, html_path: Path, pdf_path: Path) -> None:
    result = subprocess.run(
        [
            str(chrome),
            '--headless=new',
            '--disable-gpu',
            '--no-pdf-header-footer',
            f'--print-to-pdf={pdf_path}',
            '--print-to-pdf-no-header',
            str(html_path),
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f'Chrome PDF failed: {result.stderr}')


def build_toc(md_text: str) -> str:
    items = []
    for line in md_text.splitlines():
        m = re.match(r'^(#{1,3})\s+(.+)$', line)
        if m:
            level = len(m.group(1))
            title = re.sub(r'\*\*(.+?)\*\*', r'\1', m.group(2).strip())
            items.append((level, title))
    if not items:
        return '<div class="toc-item">(empty)</div>'
    html = []
    for i, (level, title) in enumerate(items, 1):
        html.append(
            f'<div class="toc-item level-{level}"><span>{title}</span>'
            f'<span class="dots"></span><span>{i}</span></div>'
        )
    return '\n'.join(html)


def md_to_html(md_text: str, title: str, author: str) -> str:
    import markdown

    refs_pattern = re.compile(
        r'^(#{1,3}[^\n]*(?:参考|来源|Sources|References)[^\n]*)\n', re.MULTILINE
    )
    refs_match = refs_pattern.search(md_text)
    if refs_match:
        body_md = md_text[: refs_match.start()]
        refs_md = md_text[refs_match.start() :]
    else:
        body_md = md_text
        refs_md = ''
    body_html = markdown.Markdown(extensions=['tables', 'fenced_code', 'toc', 'nl2br']).convert(body_md)
    refs_html = (
        markdown.Markdown(extensions=['tables', 'fenced_code', 'nl2br']).convert(refs_md)
        if refs_md
        else ''
    )
    toc_html = build_toc(body_md)
    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><style>
@page {{ size: A4; margin: 0; }}
body {{ font-family: "PingFang SC", "Microsoft YaHei", sans-serif; font-size: 10.5pt; color:#1a1a1a; margin:0; padding:0; }}
.page-cover {{ width:210mm; height:297mm; background:linear-gradient(150deg,#051C2C 0%,#0d3a5c 50%,#1a6b8a 100%); color:white; display:flex; flex-direction:column; justify-content:center; padding:0 50mm; page-break-after:always; }}
.page-toc {{ width:210mm; min-height:297mm; padding:18mm 28mm; page-break-after:always; }}
.page-body {{ width:210mm; padding:14mm 28mm; }}
.page-refs {{ width:210mm; padding:14mm 28mm; page-break-before:always; }}
h1 {{ font-size:14pt; color:#00355F; border-left:3.5pt solid #006BAC; padding-left:4mm; }}
h2 {{ font-size:11.5pt; color:#051C2C; }}
p, li {{ line-height:1.7; }}
pre {{ background:#f4f6f9; border-left:3pt solid #006BAC; padding:4mm; overflow-x:auto; }}
table {{ width:100%; border-collapse:collapse; margin:4mm 0; font-size:9.5pt; }}
th, td {{ border:0.3pt solid #d0d8e0; padding:2mm 3mm; }}
thead tr {{ background:#051C2C; color:white; }}
.toc-item {{ display:flex; gap:3mm; margin-bottom:2.5mm; }} .toc-item .dots {{ flex:1; border-bottom:1pt dotted #aaa; margin-bottom:2mm; }}
</style></head><body>
<div class="page-cover"><h1 style="color:white;border-left:none;padding-left:0;">{title}</h1><p>{author}</p></div>
<div class="page-toc"><h1>目录</h1>{toc_html}</div>
<div class="page-body">{body_html}</div>
{f'<div class="page-refs">{refs_html}</div>' if refs_html else ''}
</body></html>'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--title', default='Research Report')
    parser.add_argument('--author', default='MxM研究部')
    args = parser.parse_args()

    chrome = find_chrome()
    if not chrome:
        print('Chrome/Chromium not found. Install Chrome for PDF export.', file=sys.stderr)
        return 1
    if isinstance(chrome, str):
        chrome = Path(chrome)

    md_path = Path(args.input).resolve()
    pdf_path = Path(args.output).resolve()
    html_path = pdf_path.with_suffix('.html')
    html = md_to_html(md_path.read_text(encoding='utf-8'), args.title, args.author)
    html_path.write_text(html, encoding='utf-8')
    chrome_html_to_pdf(chrome, html_path, pdf_path)
    print(f'PDF generated: {pdf_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
