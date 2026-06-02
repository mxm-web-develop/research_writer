#!/usr/bin/env python3
"""Tavily web search for research_writer (requires MXM_RESEARCH_APIKEY)."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import export_setup_hint, load_research_config


def run_search(query: str, *, depth: str, max_results: int, api_key: str) -> list[dict]:
    from tavily import TavilyClient

    client = TavilyClient(api_key=api_key)
    response = client.search(
        query=query,
        search_depth=depth,
        max_results=max_results,
    )
    results = response.get('results') or []
    out: list[dict] = []
    for item in results:
        out.append(
            {
                'title': item.get('title', ''),
                'url': item.get('url', ''),
                'content': (item.get('content') or '')[:500],
                'score': item.get('score'),
            }
        )
    return out


def format_results_table(
    query: str,
    results: list[dict],
    *,
    round_label: str = 'R',
    dimension: str = '',
) -> tuple[str, str]:
    hits = f'{len(results)} hits'
    table_row = f'| {round_label} | {dimension or "—"} | {query} | Tavily | {hits} | see below |'
    detail = [f'#### Query: {query}', '']
    for i, r in enumerate(results, 1):
        snippet = r['content'].replace('\n', ' ').strip()
        if len(snippet) > 200:
            snippet = snippet[:200] + '...'
        detail.append(f"- **[{i}] {r['title']}** — {r['url']}")
        detail.append(f"  - {snippet}")
        detail.append('')
    return table_row, '\n'.join(detail)


def append_to_brief(brief_path: Path, table_row: str, detail_block: str) -> None:
    text = brief_path.read_text(encoding='utf-8') if brief_path.exists() else ''
    if '## 3. Search Plan & Log' in text:
        marker = '|-------|-----------|-------|------|---------------|--------------|'
        if marker in text:
            text = text.replace(marker, marker + '\n' + table_row, 1)
        else:
            text += f'\n{table_row}\n'
    else:
        text += (
            '\n## 3. Search Plan & Log\n\n'
            '| Round | Dimension | Query | Tool | Sources found | Key takeaway |\n'
            '|-------|-----------|-------|------|---------------|--------------|\n'
            f'{table_row}\n'
        )
    text += '\n' + detail_block + '\n'
    brief_path.write_text(text, encoding='utf-8')


def main() -> int:
    parser = argparse.ArgumentParser(description='Search via Tavily API')
    parser.add_argument('--query', required=True)
    parser.add_argument('--depth', default='basic', choices=['basic', 'advanced'])
    parser.add_argument('--max-results', type=int, default=5)
    parser.add_argument('--append', default=None, help='append results to research-brief.md')
    parser.add_argument('--out', default=None, help='write JSON results to file')
    parser.add_argument('--round', default='R', help='round label for brief table')
    parser.add_argument('--dimension', default='', help='dimension label for brief table')
    args = parser.parse_args()

    cfg = load_research_config(Path(args.append).parent if args.append else None)
    if not cfg.ready:
        print('MXM_RESEARCH_APIKEY not set.', file=sys.stderr)
        print(export_setup_hint(), file=sys.stderr)
        print('Fallback: use Cursor Agent WebSearch (see references/fallbacks.md)', file=sys.stderr)
        return 1

    try:
        results = run_search(
            args.query,
            depth=args.depth,
            max_results=args.max_results,
            api_key=cfg.api_key,
        )
    except Exception as exc:
        print(f'Tavily search failed: {exc}', file=sys.stderr)
        return 1

    payload = {
        'query': args.query,
        'date': date.today().isoformat(),
        'results': results,
    }

    if args.out:
        Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f'Wrote {args.out} ({len(results)} results)')

    if args.append:
        table_row, detail = format_results_table(
            args.query,
            results,
            round_label=args.round,
            dimension=args.dimension,
        )
        append_to_brief(Path(args.append), table_row, detail)
        print(f'Appended to {args.append}')

    if not args.out and not args.append:
        print(json.dumps(payload, ensure_ascii=False, indent=2))

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
