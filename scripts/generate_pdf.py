#!/usr/bin/env python3
"""Markdown -> PDF using Chrome/Chromium headless."""
from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
import tempfile
import unicodedata
from dataclasses import dataclass
from datetime import date
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
FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
RW_COVER_PATTERN = re.compile(r'<!--\s*rw-cover\b(.*?)-->\s*', re.DOTALL | re.IGNORECASE)
TITLE_SUBTITLE_PATTERN = re.compile(r'^(.+?)[（(]([^）)]+)[）)]\s*$')


@dataclass
class CoverMeta:
    title: str
    subtitle: str = ''
    author: str = 'MxM研究部'
    date: str = ''


CSS = '''
@page { size: A4; margin: 0; }
html, body { margin: 0; padding: 0; width: 210mm; }
body { font-family: "PingFang SC", "Microsoft YaHei", sans-serif; font-size: 10.5pt; color:#1a1a1a; }
.page-cover {
  box-sizing: border-box;
  width: 210mm;
  height: 297mm;
  min-height: 297mm;
  max-height: 297mm;
  margin: 0;
  padding: 0;
  background: linear-gradient(150deg,#051C2C 0%,#0d3a5c 50%,#1a6b8a 100%);
  color: white;
  page-break-after: always;
  break-after: page;
  page-break-inside: avoid;
  break-inside: avoid;
  overflow: hidden;
  position: relative;
  display: block;
}
.cover-inner {
  box-sizing: border-box;
  height: 297mm;
  padding: 42mm 32mm 28mm;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 0;
}
.cover-title {
  margin: 0 0 6mm;
  padding: 0;
  border: none;
  font-size: 30pt;
  font-weight: 700;
  line-height: 1.25;
  letter-spacing: 0.02em;
  color: white;
}
.cover-subtitle {
  margin: 0 0 18mm;
  padding: 0;
  font-size: 16pt;
  font-weight: 400;
  line-height: 1.45;
  color: rgba(255,255,255,0.92);
}
.cover-meta {
  margin-top: auto;
  padding-top: 10mm;
  border-top: 0.4pt solid rgba(255,255,255,0.35);
}
.cover-author {
  margin: 0 0 3mm;
  font-size: 12pt;
  font-weight: 500;
  line-height: 1.5;
  color: rgba(255,255,255,0.95);
}
.cover-date {
  margin: 0;
  font-size: 11pt;
  font-weight: 400;
  line-height: 1.5;
  color: rgba(255,255,255,0.82);
}
.page-toc { width:210mm; min-height:297mm; padding:18mm 28mm; page-break-after:always; break-after:page; box-sizing:border-box; }
.page-body { width:210mm; padding:14mm 28mm; box-sizing:border-box; }
.page-refs { width:210mm; padding:14mm 28mm; page-break-before:always; break-before:page; box-sizing:border-box; }
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


def _parse_key_values(text: str) -> dict[str, str]:
    if text.strip().startswith('{'):
        try:
            data = json.loads(text.strip())
            return {str(k).lower(): str(v) for k, v in data.items()}
        except json.JSONDecodeError:
            pass
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or ':' not in line:
            continue
        key, value = line.split(':', 1)
        out[key.strip().lower()] = value.strip()
    return out


def split_title_subtitle(raw: str) -> tuple[str, str]:
    raw = raw.strip()
    match = TITLE_SUBTITLE_PATTERN.match(raw)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return raw, ''


def strip_cover_markers(md_text: str) -> str:
    text = FRONTMATTER_PATTERN.sub('', md_text, count=1)
    return RW_COVER_PATTERN.sub('', text, count=1)


def parse_cover_meta(
    md_text: str,
    *,
    title: str | None = None,
    subtitle: str | None = None,
    author: str | None = None,
    report_date: str | None = None,
) -> CoverMeta:
    fields: dict[str, str] = {}

    frontmatter = FRONTMATTER_PATTERN.match(md_text)
    if frontmatter:
        fields.update(_parse_key_values(frontmatter.group(1)))

    cover_match = RW_COVER_PATTERN.search(md_text)
    if cover_match:
        fields.update(_parse_key_values(cover_match.group(1)))

    h1_match = re.search(r'^#\s+(.+)$', md_text, re.MULTILINE)
    h1_text = h1_match.group(1).strip() if h1_match else 'Research Report'
    h1_title, h1_subtitle = split_title_subtitle(h1_text)

    base_title = fields.get('title') or h1_title
    base_title, title_paren_sub = split_title_subtitle(base_title)

    if title:
        resolved_title, title_override_sub = split_title_subtitle(title)
        if title_override_sub:
            title_paren_sub = title_paren_sub or title_override_sub
    else:
        resolved_title = base_title

    if subtitle is not None:
        resolved_subtitle = subtitle
    else:
        resolved_subtitle = fields.get('subtitle') or title_paren_sub or h1_subtitle

    resolved_author = author or fields.get('author') or 'MxM研究部'
    resolved_date = report_date or fields.get('date') or date.today().isoformat()

    return CoverMeta(
        title=resolved_title,
        subtitle=resolved_subtitle,
        author=resolved_author,
        date=resolved_date,
    )


def build_cover_html(cover: CoverMeta) -> str:
    subtitle_block = (
        f'<p class="cover-subtitle">{html.escape(cover.subtitle)}</p>' if cover.subtitle else ''
    )
    return (
        '<div class="page-cover">'
        '<div class="cover-inner">'
        f'<h1 class="cover-title">{html.escape(cover.title)}</h1>'
        f'{subtitle_block}'
        '<div class="cover-meta">'
        f'<p class="cover-author">{html.escape(cover.author)}</p>'
        f'<p class="cover-date">{html.escape(cover.date)}</p>'
        '</div>'
        '</div>'
        '</div>'
    )


def parse_md_parts(md_text: str) -> tuple[str, str]:
    md_text = strip_cover_markers(md_text)
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
    cover: CoverMeta,
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
    cover_block = build_cover_html(cover)
    return f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8"><style>{CSS}</style></head><body>
{cover_block}
{toc_block}
{body_block}
{refs_block}
</body></html>'''


def measure_toc_pages(chrome: Path, cover: CoverMeta, toc_html: str) -> int:
    with tempfile.TemporaryDirectory(prefix='rw-toc-') as tmp:
        tmp_dir = Path(tmp)
        probe_html = tmp_dir / 'toc-probe.html'
        probe_pdf = tmp_dir / 'toc-probe.pdf'
        probe_html.write_text(
            assemble_html(
                cover,
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
    cover: CoverMeta,
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
            assemble_html(cover, body_html, refs_html, '', include_toc=False),
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
            measured = measure_toc_pages(chrome, cover, toc_html)
            resolved = tentative.copy()
            if measured == toc_pages:
                break
            toc_pages = measured

    return resolved


def md_to_html(
    md_text: str,
    cover: CoverMeta,
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
        page_map = resolve_toc_page_numbers(chrome, cover, body_html, refs_html, headings)
    else:
        page_map = {h['id']: None for h in headings}

    toc_html = build_toc_html(headings, page_map)
    return assemble_html(cover, body_html, refs_html, toc_html, include_toc=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--title', default=None, help='cover main title override')
    parser.add_argument('--subtitle', default=None, help='cover subtitle override')
    parser.add_argument('--author', default=None, help='cover author override')
    parser.add_argument('--date', default=None, help='cover date override (default: today or frontmatter)')
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
    cover = parse_cover_meta(
        md_text,
        title=args.title,
        subtitle=args.subtitle,
        author=args.author,
        report_date=args.date,
    )
    try:
        html_doc = md_to_html(
            md_text,
            cover,
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
