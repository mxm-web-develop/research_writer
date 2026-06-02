# PDF Output Rules

Preferred approach on macOS:
- use Chrome headless
- render from generated HTML
- keep report structure: **full-page cover** → TOC → body → references

## Cover page (dedicated A4 page)

Four typography levels on the cover, plus a **document-type badge** and **type-specific color theme**:

| Level | Field | Source |
|-------|-------|--------|
| 类型徽章 | type label | `document_type` in brief/report → auto theme |
| 大标题 | title | `# Report Title` or `--title` |
| 副标题 | subtitle | parentheses in H1, frontmatter, or `--subtitle` |
| 作者 | author | `--author` / frontmatter (default: MxM研究部) |
| 日期 | date | `--date` / frontmatter (default: today) |

`generate_pdf.py` reads `document_type` from `research-brief.md` or report frontmatter and applies a distinct **gradient + layout + accent** per type (10 themes in `scripts/doc_types.py` → `COVER_THEMES`).

| document_type | 封面风格 |
|---------------|----------|
| `research-report` | 深蓝咨询风 · classic |
| `product-manual` | 青蓝产品风 · editorial |
| `tech-proposal` | 灰绿工程风 · bold（左色条） |
| `prd` | 靛紫产品风 · editorial |
| `whitepaper` | 藏青+金色 · classic |
| `competitive-analysis` | 酒红竞争风 · bold |
| `tech-tutorial` | 翠绿教程风 · minimal（顶色条） |
| `press-release` | 黑红新闻风 · bold |
| `spoken-script` | 橙暖口播风 · editorial |
| `social-narrative` | 紫粉社媒风 · minimal |

Optional YAML frontmatter or comment at top of `report.md`:

```markdown
---
document_type: product-manual
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
