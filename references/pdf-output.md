# PDF Output Rules

Preferred approach on macOS:
- use Chrome headless
- render from generated HTML
- keep report structure: **full-page cover** → TOC → body → references

## Cover page (dedicated A4 page)

Four typography levels on the cover:

| Level | Field | Source |
|-------|-------|--------|
| 大标题 | title | `# Report Title` or `--title` |
| 副标题 | subtitle | parentheses in H1, frontmatter, or `--subtitle` |
| 作者 | author | `--author` / frontmatter (default: MxM研究部) |
| 日期 | date | `--date` / frontmatter (default: today) |

Optional YAML frontmatter or comment at top of `report.md`:

```markdown
---
title: WebAssist 应用说明书
subtitle: 功能 + 实现 + 演进
author: MxM研究部
date: 2026-06-01
---
```

Or:

```markdown
<!-- rw-cover
title: WebAssist 应用说明书
subtitle: 功能 + 实现 + 演进
author: MxM研究部
date: 2026-06-01
-->
```

H1 with parentheses is auto-split: `# Title（Subtitle）` → title + subtitle.

Key requirements:
1. PDF is derived from `report.md`
2. TOC should reflect report headings
3. references section must be separated and preserved
4. local and generated images under `assets/` are embedded into PDF (see `references/images.md`)
5. use real file paths for Chrome print-to-pdf

Recommended command:

```bash
python3 scripts/generate_pdf.py --input report.md --output output/report.pdf --title "Research Report"
```

Or use the full pipeline:

```bash
python3 scripts/build_bundle.py --input report.md --outdir output --sources sources.md
```
