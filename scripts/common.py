#!/usr/bin/env python3
"""Shared helpers for research_writer scripts."""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    'Executive Summary',
    'Background and Context',
    'Problem Definition',
    'Deep Analysis',
    'Comparison / Alternatives',
    'Risks and Constraints',
    'Recommendations / Conclusion',
    'References',
]

def skill_root() -> Path:
    return Path(__file__).resolve().parent.parent


CHROME_CANDIDATES = [
    Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),
    Path('/Applications/Chromium.app/Contents/MacOS/Chromium'),
    Path('/usr/bin/google-chrome'),
    Path('/usr/bin/chromium'),
    Path('/usr/bin/chromium-browser'),
]


def python_exe() -> str:
    return sys.executable


def run_script(script: Path, args: list[str]) -> None:
    subprocess.check_call([python_exe(), str(script), *args])


def find_chrome() -> Path | None:
    for path in CHROME_CANDIDATES:
        if path.exists():
            return path
    return shutil.which('google-chrome') or shutil.which('chromium') or shutil.which('chromium-browser')


def split_sections(text: str) -> tuple[str, list[dict]]:
    title = None
    current = None
    sections: list[dict] = []
    for line in text.splitlines():
        m1 = re.match(r'^#\s+(.+)$', line.strip())
        m2 = re.match(r'^##\s+(.+)$', line.strip())
        if m1 and title is None:
            title = m1.group(1).strip()
            continue
        if m2:
            if current:
                sections.append(current)
            current = {'title': m2.group(1).strip(), 'lines': []}
            continue
        if current is not None:
            current['lines'].append(line)
    if current:
        sections.append(current)
    return title or 'Research Report', sections


def section_to_bullets(lines: list[str], limit: int = 5) -> list[str]:
    bullets: list[str] = []
    buf: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith('- '):
            bullets.append(line[2:].strip())
        elif line.startswith('* '):
            bullets.append(line[2:].strip())
        elif not line.startswith('#') and '|' not in line:
            buf.append(line)
    if buf and len(bullets) < limit:
        joined = ' '.join(buf)
        sentences = re.split(r'(?<=[。.!?])\s+', joined)
        for s in sentences:
            s = s.strip()
            if s:
                bullets.append(s)
            if len(bullets) >= limit:
                break
    cleaned: list[str] = []
    for b in bullets:
        b = re.sub(r'\s+', ' ', b).strip()
        if b and b not in cleaned:
            cleaned.append(b)
        if len(cleaned) >= limit:
            break
    return cleaned


def is_refs_section(title: str) -> bool:
    return bool(re.search(r'reference|参考|来源|sources', title, re.I))


def write_deck_outline(path: Path, title: str, sections: list[dict]) -> None:
    out = [f'# Deck Outline: {title}', '']
    slide_no = 1
    out.append(f'## Slide {slide_no}: {title}')
    out.append('- Objective: Introduce the report')
    out.append('- Key point: Title / topic / framing')
    out.append('')
    slide_no += 1
    for sec in sections:
        if is_refs_section(sec['title']):
            continue
        out.append(f'## Slide {slide_no}: {sec["title"]}')
        out.append(f'- Objective: Summarize {sec["title"]}')
        for bullet in section_to_bullets(sec['lines']):
            out.append(f'- {bullet}')
        out.append('')
        slide_no += 1
    path.write_text('\n'.join(out), encoding='utf-8')


def write_speaker_notes(path: Path, title: str, sections: list[dict]) -> None:
    out = [f'# Speaker Notes: {title}', '']
    out.append(f'## {title}')
    out.append(f'本页用于介绍《{title}》的研究主题、范围和输出结构。')
    out.append('')
    for sec in sections:
        if is_refs_section(sec['title']):
            continue
        bullets = section_to_bullets(sec['lines'])
        out.append(f'## {sec["title"]}')
        if bullets:
            out.append(
                f'本页重点围绕“{sec["title"]}”展开，核心内容包括：' + '；'.join(bullets[:4]) + '。'
            )
        else:
            out.append(f'本页用于说明“{sec["title"]}”的核心内容。')
        out.append('')
    path.write_text('\n'.join(out), encoding='utf-8')


def parse_deck_outline(text: str) -> list[dict]:
    slides: list[dict] = []
    current: dict | None = None
    for line in text.splitlines():
        m = re.match(r'^##\s+Slide\s+\d+:\s*(.+)$', line.strip(), re.I)
        if m:
            if current:
                slides.append(current)
            current = {'title': m.group(1).strip(), 'bullets': []}
            continue
        if current and line.strip().startswith('- '):
            bullet = line.strip()[2:].strip()
            if not re.match(r'^objective:\s*', bullet, re.I):
                current['bullets'].append(bullet)
    if current:
        slides.append(current)
    return slides


def parse_notes(text: str) -> dict[str, str]:
    notes: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for line in text.splitlines():
        m = re.match(r'^##\s+(.+)$', line.strip())
        if m:
            if current:
                notes[current] = '\n'.join(buf).strip()
            current = m.group(1).strip()
            buf = []
            continue
        if current is not None:
            buf.append(line)
    if current:
        notes[current] = '\n'.join(buf).strip()
    return notes


def slide_title_key(title: str) -> str:
    m = re.match(r'^Slide\s+\d+:\s*(.+)$', title, re.I)
    return m.group(1).strip() if m else title.strip()


def count_sources(text: str) -> int:
    headings = len(re.findall(r'^##\s+Source\s+\d+', text, re.MULTILINE | re.I))
    if headings:
        return headings
    urls = len(re.findall(r'https?://', text))
    if urls:
        return urls
    count = 0
    for line in text.splitlines():
        s = line.strip()
        if re.match(r'^\d+\.\s+', s):
            count += 1
    return count
