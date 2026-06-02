# Document Types

Agent classifies user requests into one type **before** writing `report.md`. Record `document_type` in `research-brief.md` §1.

| ID | 类型 | PPT 默认 |
|----|------|----------|
| `research-report` | 调研报告 | 是 |
| `product-manual` | 产品说明书 | 是 |
| `tech-proposal` | 技术方案 | 是 |
| `prd` | PRD | 是 |
| `whitepaper` | 白皮书 | 是 |
| `competitive-analysis` | 竞品分析 | 是 |
| `tech-tutorial` | 技术教程 | 是 |
| `press-release` | 新闻稿 | 否 |
| `spoken-script` | 口播稿 | 否 |
| `social-narrative` | 自媒体叙事稿 | 否 |

Each `{id}.md` defines recognition signals, required sections, tone, and search query templates.

After classification, optionally Tavily-search: `"[type label] 文档结构 写作规范"`.
