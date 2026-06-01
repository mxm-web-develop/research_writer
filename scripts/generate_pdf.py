#!/usr/bin/env python3
"""Markdown -> PDF using Chrome/Chromium headless."""
from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import find_chrome
from images import ImageConfig, embed_images_in_html, load_image_config, materialize_images

HEADING_RE = re.compile(
    r'<h([1-3])\s+id="([^"]*)"[^>]*>(.*?)</h\1>',
    re.IGNORECASE | re.DOTALL,
)
REFS_PATTERN = re.compile(
    r'^(#{1,3}[^\n]*(?:参考|来源|Sources|References)[^\n]*)\n', re.MULTILINE
)

CSS = '''
@page { size: A4; margin: 0; }
body { font-family: "PingFang SC", "Microsoft YaHei", sans-serif; font-size: 10.5pt; color:#1a1a1a; margin:0; padding:0; }
.page-cover { width:210mm; height:297mm; background:linear-gradient(150deg,#051C2C 0%,#0d3a5c 50%,#1a6b8a 100%); color:white; display:flex; flex-direction:column; justify-content:center; padding:0 50mm; page-break-after:always; }
.page-toc { width:210mm; min-height:297mm; padding:18mm 28mm; page-break-after:always; }
.page-body { width:210mm; padding:14mm 28mm; }
.page-refs { width:210mm; padding:14mm 28mm; page-break-before:always; }
h1 { font-size:14pt; color:#00355F; border-left:3.5pt solid #006BAC; padding-left:4mm; }
h2 { font-size:11.5pt; color:#051C2C; }
h3 { font-size:10.5pt; color:#333; }
p, li { line-height:1.7; }
pre { background:#f4f6f9; border-left:3pt solid #006BAC; padding:4mm; overflow-x:auto; }
table { width:100%; border-collapse:collapse; margin:4mm 0; font-size:9.5pt; }
th, td { border:0.3pt solid #d0d8e0; padding:2mm 3mm; }
thead tr { background:#051C2C; color:white; }
.toc-item { display:flex; gap:3mm; margin-bottom:2.5mm; align-items:baseline; }
.toc-item .dots { flex:1; border-bottom:1pt dotted #aaa; margin-bottom:2mm; }
.toc-item a { color:inherit; text-decoration:none; }
.toc-item .page-num { min-width:6mm; text-align:right; }
figure.rw-figure { margin: 5mm 0; text-align: center; page-break-inside: avoid; }
figure.rw-figure img { max-width: 100%; height: auto; display: block; margin: 0 auto; }
figure.rw-figure figcaption { font-size: 9pt; color: #555; margin-top: 2mm; }
p img { max-width: 100%; height: auto; display: block; margin: 4mm auto; }
'''


def normalize_text(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    text = html.unescape(text)
    text = unicodedata.normalize('NFKC', text)
    return re.sub(r'\s+', '', text)


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


def parse_md_parts(md_text: str) -> tuple[str, str]:
    refs_match = REFS_PATTERN.search(md_text)
    if refs_match:
        return md_text[: refs_match.start()], md_text[refs_match.start() :]
    return md_text, ''


def render_markdown(md_text: str) -> str:
    import markdown

    return markdown.Markdown(extensions=['tables', 'fenced_code', 'toc', 'nl2br']).convert(md_text)


def extract_headings(body_html: str) -> list[dict]:
    items: list[dict] = []
    for match in HEADING_RE.finditer(body_html):
        level = int(match.group(1))
        if level == 1:
            continue
        anchor = match.group(2).strip()
        raw_title = re.sub(r'<[^>]+>', '', match.group(3))
        heading_title = html.unescape(raw_title).strip()
        items.append({'level': level, 'id': anchor, 'title': heading_title})
    return items


def build_toc_html(headings: list[dict], page_map: dict[str, int | None]) -> str:
    if not headings:
        return '<div class="toc-item">(empty)</div>'
    rows: list[str] = []
    for item in headings:
        page = page_map.get(item['id'])
        page_label = str(page) if page is not None else '…'
        safe_title = html.escape(item['title'])
        rows.append(
            f'<div class="toc-item level-{item["level"]}">'
            f'<a href="#{html.escape(item["id"], quote=True)}">{safe_title}</a>'
            f'<span class="dots"></span>'
            f'<span class="page-num">{page_label}</span>'
            f'</div>'
        )
    return '\n'.join(rows)


def assemble_html(
    title: str,
    author: str,
    body_html: str,
    refs_html: str,
    toc_html: str,
    *,
    include_toc: bool,
    include_body: bool = True,
    include_refs: bool = True,
) -> str:
    toc_block = (
        f'<div class="page-toc"><h1>目录</h1>{toc_html}</div>' if include_toc else ''
    )
    body_block = f'<div class="page-body">{body_html}</div>' if include_body else ''
    refs_block = (
        f'<div class="page-refs">{refs_html}</div>' if include_refs and refs_html else ''
    )
    safe_title = html.escape(title)
    safe_author = html.escape(author)
    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><style>{CSS}</style></head><body>
<div class="page-cover"><h1 style="color:white;border-left:none;padding-left:0;">{safe_title}</h1><p>{safe_author}</p></div>
{toc_block}
{body_block}
{refs_block}
</body></html>'''


def measure_toc_pages(chrome: Path, title: str, author: str, toc_html: str) -> int:
    with tempfile.TemporaryDirectory(prefix='rw-toc-') as tmp:
        tmp_dir = Path(tmp)
        probe_html = tmp_dir / 'toc-probe.html'
        probe_pdf = tmp_dir / 'toc-probe.pdf'
        probe_html.write_text(
            assemble_html(
                title,
                author,
                '',
                '',
                toc_html,
                include_toc=True,
                include_body=False,
                include_refs=False,
            ),
            encoding='utf-8',
        )
        chrome_html_to_pdf(chrome, probe_html, probe_pdf)
        return max(pdf_page_count(probe_pdf) - 1, 1)


def pdf_page_count(pdf_path: Path) -> int:
    from pypdf import PdfReader

    return len(PdfReader(str(pdf_path)).pages)


def heading_match_keys(title: str) -> list[str]:
    keys: list[str] = []
    full = normalize_text(title)
    if full:
        keys.append(full)
    stripped = re.sub(r'[（(][^）)]*[）)]', '', title)
    short = normalize_text(stripped)
    if short and short not in keys:
        keys.append(short)
    numbered = re.match(r'^(\d+(?:\.\d+)*)\s+(.+)$', title.strip())
    if numbered:
        prefix = normalize_text(numbered.group(1))
        if prefix and prefix not in keys:
            keys.append(prefix)
    return keys


def map_headings_to_pages(pdf_path: Path, headings: list[dict]) -> dict[str, int]:
    from pypdf import PdfReader

    reader = PdfReader(str(pdf_path))
    page_texts = [normalize_text(page.extract_text() or '') for page in reader.pages]
    page_map: dict[str, int] = {}
    search_from = 1  # skip cover page (index 0)

    for item in headings:
        keys = heading_match_keys(item['title'])
        found_page = None
        for page_idx in range(search_from, len(page_texts)):
            page_text = page_texts[page_idx]
            if any(key and key in page_text for key in keys):
                found_page = page_idx + 1
                search_from = page_idx
                break
        if found_page is not None:
            page_map[item['id']] = found_page

    last_page = 2
    for item in headings:
        if item['id'] in page_map:
            last_page = page_map[item['id']]
        else:
            page_map[item['id']] = last_page
    return page_map


def resolve_toc_page_numbers(
    chrome: Path,
    title: str,
    author: str,
    body_html: str,
    refs_html: str,
    headings: list[dict],
) -> dict[str, int | None]:
    if not headings:
        return {}

    with tempfile.TemporaryDirectory(prefix='rw-pdf-') as tmp:
        tmp_dir = Path(tmp)
        pass1_html = tmp_dir / 'pass1.html'
        pass1_pdf = tmp_dir / 'pass1.pdf'
        pass1_html.write_text(
            assemble_html(title, author, body_html, refs_html, '', include_toc=False),
            encoding='utf-8',
        )
        chrome_html_to_pdf(chrome, pass1_html, pass1_pdf)
        pass1_pages = map_headings_to_pages(pass1_pdf, headings)

        toc_pages = 1
        resolved: dict[str, int | None] = {}
        for _ in range(2):
            tentative = {
                item['id']: pass1_pages.get(item['id'], 2) + toc_pages for item in headings
            }
            toc_html = build_toc_html(headings, tentative)
            measured = measure_toc_pages(chrome, title, author, toc_html)
            resolved = tentative.copy()
            if measured == toc_pages:
                break
            toc_pages = measured

    return resolved


def md_to_html(
    md_text: str,
    title: str,
    author: str,
    report_dir: Path,
    chrome: Path | None = None,
    *,
    image_config: ImageConfig | None = None,
    generate_images: bool = False,
    yes: bool = False,
) -> str:
    config = image_config or load_image_config(report_dir)
    md_text, _ = materialize_images(
        md_text,
        report_dir,
        config,
        generate=generate_images,
        yes=yes,
    )
    body_md, refs_md = parse_md_parts(md_text)
    body_html = render_markdown(body_md)
    refs_html = render_markdown(refs_md) if refs_md else ''
    body_html = embed_images_in_html(body_html, report_dir)
    refs_html = embed_images_in_html(refs_html, report_dir) if refs_html else ''
    headings = extract_headings(body_html)

    if chrome and headings:
        page_map = resolve_toc_page_numbers(chrome, title, author, body_html, refs_html, headings)
    else:
        page_map = {h['id']: None for h in headings}

    toc_html = build_toc_html(headings, page_map)
    return assemble_html(title, author, body_html, refs_html, toc_html, include_toc=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--title', default='Research Report')
    parser.add_argument('--author', default='MxM研究部')
    parser.add_argument('--assets', default='assets', help='assets dir relative to report.md')
    parser.add_argument('--generate-images', action='store_true', help='call GPT-image API for pending rw-image directives')
    parser.add_argument('--yes', action='store_true', help='skip interactive image generation confirmation')
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
    report_dir = md_path.parent
    image_config = load_image_config(report_dir, Path(args.assets))
    md_text = md_path.read_text(encoding='utf-8')
    try:
        html_doc = md_to_html(
            md_text,
            args.title,
            args.author,
            report_dir,
            chrome=chrome,
            image_config=image_config,
            generate_images=args.generate_images,
            yes=args.yes,
        )
    except (RuntimeError, FileNotFoundError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    html_path.write_text(html_doc, encoding='utf-8')
    chrome_html_to_pdf(chrome, html_path, pdf_path)
    print(f'PDF generated: {pdf_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
