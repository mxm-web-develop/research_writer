# Document Types

Agent classifies user requests into one type **before** writing `report.md`. Record `document_type` in `research-brief.md` §1.

| ID | 类型 | PPT 默认 | PDF 封面 |
|----|------|----------|----------|
| `research-report` | 调研报告 | 是 | 深蓝 classic |
| `product-manual` | 产品说明书 | 是 | 青蓝 editorial |
| `tech-proposal` | 技术方案 | 是 | 灰绿 bold |
| `prd` | PRD | 是 | 靛紫 editorial |
| `whitepaper` | 白皮书 | 是 | 藏青+金 classic |
| `competitive-analysis` | 竞品分析 | 是 | 酒红 bold |
| `tech-tutorial` | 技术教程 | 是 | 翠绿 minimal |
| `press-release` | 新闻稿 | 否 | 黑红 bold |
| `spoken-script` | 口播稿 | 否 | 橙暖 editorial |
| `social-narrative` | 自媒体叙事稿 | 否 | 紫粉 minimal |

PDF cover themes are applied automatically by `generate_pdf.py` from `document_type`. See `references/pdf-output.md`.

Each `{id}.md` defines recognition signals, required sections, tone, and search query templates.

After classification, optionally Tavily-search: `"[type label] 文档结构 写作规范"`.
