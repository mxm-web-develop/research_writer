---
name: research_writer
description: Deep multi-dimensional research — intake, web search, reasoning chains, then report.md, sources, PDF/PPT via bundled scripts. Use for structured investigations requiring evidence-backed deliverables.
version: 3.6.0
author: HanfengZhang_mxm
license: MIT
metadata:
  hermes:
    tags: [research, report, pdf, ppt, claude-code, cursor, openclaw, deliverables]
    related_skills: [expert, md-to-pdf, powerpoint]
---

# research_writer

跨 Agent 可复用的深度调研输出 Skill：支持 **本地资料** 与 **Tavily 网络调研** 双路径；先识别 **10 类文档类型** 再写作；以 `report.md` 为单一事实源，派生来源清单、幻灯片大纲、口播稿、PDF 与 PPT。

## When to Use

- 多源深度调研 + 结构化 Markdown 报告
- 需要 PDF / PPT / 口播稿等正式交付物
- 同一工作流需在 Claude Code、Cursor、OpenClaw 等环境复用

## Required Outputs

| 文件 | 说明 |
|------|------|
| `research-brief.md` | 调研工作稿：需求澄清、**document_type**、**input_mode**、维度、搜索日志、推理链（**写作前必完成**） |
| `local-index.md` | 本地资料索引（`local` / `hybrid` 模式，由 `scan_local.py` 生成） |
| `report.md` | 主报告 |
| `sources.md` | 来源台账（搜索过程中持续更新，见 `references/sources-format.md`） |
| `output/deck-outline.md` | 由脚本从 report 派生 |
| `output/speaker-notes.md` | 由脚本从 report 派生 |
| `output/report.pdf` | 由脚本从 report 编译 |
| `output/report.pptx` | 由 deck-outline + speaker-notes 编译 |

## Single Source of Truth

1. 识别 **document_type** 与 **input_mode**（local / web / hybrid）
2. 完成 `research-brief.md`（需求 → scan/search → 推理）
3. 撰写 `report.md` 与 `sources.md`（结构按类型模板，结论必须可追溯到 brief 与来源）
4. 再运行 `build_bundle.py`
5. PPT / 口播稿不得引入 report 中不存在的主张

## Research Phases（Agent 必遵）

**完整规范：`references/intake-and-search.md`**

| Phase | 动作 | 产出 |
|-------|------|------|
| **0 需求澄清** | 提炼核心问题、读者、范围、排除项；识别 **document_type**；模糊则先问用户 | `research-brief.md` §1 |
| **0.5 输入模式** | `local`（本地路径）/ `web`（仅话题）/ `hybrid`（两者） | §1 `input_mode` + `scan_local.py` 和/或 `search_tavily.py` |
| **1 多维框架** | 从类型模板加载章节与维度；每维 2–3 个子问题 + 反证条件 | `research-brief.md` §2 |
| **2 深度搜索** | ≥3 轮搜索（全景→深入→验证）；每维 ≥2 独立来源 | `research-brief.md` §3–4 + `sources.md` |
| **3 推理综合** | 主张→证据→推理链；交叉验证；魔鬼代言人；标注 gaps | `research-brief.md` §5–7 |
| **4 写作交付** | 按 **document_type** 结构写 report；跑 build_bundle；validate | `report.md` + 派生产物 |

**10 类文档**：`references/document-types/README.md`（调研报告、产品说明书、技术方案、PRD、白皮书、竞品分析、技术教程、新闻稿、口播稿、自媒体叙事稿）

**数据采集脚本**：

```bash
# 本地资料
python3 scripts/scan_local.py --path /path/to/docs --out local-index.md

# 网络调研（需 MXM_RESEARCH_APIKEY）
python3 scripts/search_tavily.py --query "topic overview" --append research-brief.md

# 批量搜索（从 brief §3 表格读取 query）
python3 scripts/build_bundle.py --input report.md --outdir output --stage search --brief research-brief.md
```

**Fallback**：见 `references/fallbacks.md`（Tavily → Agent WebSearch → 浏览器 → 仅本地）

**禁止**：跳过搜索直接用模型知识写 report；单来源关键结论；只搜一轮。

模板：`templates/sample-research-brief.md`

## Quick Start

```bash
# 1. 安装依赖（使用当前 Python 解释器）
python3 scripts/bootstrap.py --install
python3 scripts/doctor.py

# 可选：配置 MXM 环境变量
export MXM_RESEARCH_APIKEY="tvly-..."
export MXM_GEN_IMAGE_KEY="..."
export MXM_GEN_IMAGE_URL="https://.../v1/images/generations"
export MXM_GEN_IMAGE_MODEL="gpt-image-2"

# 2. 撰写 report.md、sources.md（可参考 templates/）

# 3. 一键构建派生产物并校验
python3 scripts/build_bundle.py --input report.md --outdir output --sources sources.md
```

分阶段重跑（失败恢复）：

```bash
python3 scripts/build_bundle.py --input report.md --outdir output --stage search --brief research-brief.md
python3 scripts/build_bundle.py --input report.md --outdir output --stage deck
python3 scripts/build_bundle.py --input report.md --outdir output --stage images
python3 scripts/build_bundle.py --input report.md --outdir output --stage pdf
python3 scripts/build_bundle.py --input report.md --outdir output --stage ppt
python3 scripts/build_bundle.py --input report.md --outdir output --sources sources.md --stage validate
```

## Document Types（按类型选结构）

默认 `research-report`（8 节调研结构）。其他类型见 `references/document-types/{id}.md`：

| ID | 类型 | 默认 PPT |
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

在 `research-brief.md` §1 设置 `document_type`；`validate.py` 按类型检查必含章节与 `min_sources`。

## Workflow

1. **Phase 0–0.5**：识别类型与输入模式；`scan_local.py` / `search_tavily.py`
2. **Phase 1–3**：完成 `research-brief.md` 与 `sources.md` 草稿
3. **Phase 4**：按 **document_type** 撰写 `report.md`
4. 运行 `build_bundle.py`
5. 通过 `validate.py` 质量门禁后交付

（旧版简写：明确目标 → 多源检索 → 交叉验证 → 写作 → 构建 → 校验）

## Agent Adapters

| 环境 | 说明 |
|------|------|
| Claude Code | `references/claude-code-usage.md` |
| Cursor | `references/cursor-usage.md` + `.cursor/rules/research-writer.mdc` |
| OpenClaw | `references/openclaw-usage.md` |

## Bundled Files

**Scripts:** `bootstrap.py`, `doctor.py`, `config.py`, `doc_types.py`, `build_bundle.py`, `search_tavily.py`, `scan_local.py`, `generate_images.py`, `generate_pdf.py`, `generate_ppt.py`, `validate.py`, `common.py`, `images.py`

**References:** `intake-and-search.md`, `fallbacks.md`, `document-types/`, `research-methodology.md`, `sources-format.md`, `images.md`, `pdf-output.md`, `installation.md`, `troubleshooting.md`, agent usage docs

**Templates:** `sample-research-brief.md`, `sample-report.md`, `sample-sources.md`, `requirements.txt`, `image.env.example`

## Quality Gates

`validate.py` 检查（可通过 `--relax-sources` 放宽来源数）：

- `sources.md` 条目数量（按 `document_type` 的 `min_sources`）
- 报告必含章节（按 `document_type`，非一律 8 节）
- 输出目录中派生文件齐全（部分类型默认不要求 PPT）

人工复核：

- `research-brief.md` 含搜索日志与推理链（非 trivial 任务）
- 重要事实含日期/时间范围
- PDF 目录与 report 标题一致
- PPT 与 report 观点不矛盾
- 口播稿与对应幻灯片主题一致

## Project Layout

```text
project/
├── research-brief.md    # 需求、document_type、input_mode、搜索日志、推理链
├── local-index.md       # optional: scan_local.py output
├── report.md
├── sources.md
├── output/
│   ├── deck-outline.md
│   ├── speaker-notes.md
│   ├── report.pdf
│   └── report.pptx
├── assets/              # local images + AI-generated PNGs
└── image.env            # optional GPT-image API config (do not commit)
```

## Images

Reports and PDFs support **local images** and **GPT-image-2** generation. See `references/images.md`.

### 用户要求「为话题/项目生成配图」时（Agent 必遵）

**不要立刻调 API 或写 directive。** 按顺序执行：

1. **询问凭证**（若项目尚无 `image.env`）：向用户索取 GPT-image-2 的 **API URL** 与 **API Key**（及可选 model / size）。说明密钥只写入本地 `image.env`，不会提交 git。
2. **分析话题/项目**：阅读 `report.md`、项目文档或用户描述；梳理结构、读者、交付形态（PDF/PPT）。
3. **输出配图建议**（仅建议，不生成）：列出建议配图的位置、类型（本地 / AI）、用途、推荐 prompt 草案；标注优先级（高/中/低）。**等待用户确认**后再继续。
4. **用户确认后**：将批准的条目写入 `<!-- rw-image ... -->` 或 `![alt](assets/...)`，写入 `image.env`，再运行 `generate_images.py` 或 `build_bundle --generate-images`。

建议回复格式见 `references/images.md` §「配图建议模板」。

### 构建命令

1. Mark sections with `<!-- rw-image ... -->` directives (or standard `![alt](assets/...)`).
2. Configure `image.env` from `templates/image.env.example` (`MXM_GEN_IMAGE_*` or legacy `RW_IMAGE_*`).
3. Generate images (interactive):

```bash
python3 scripts/generate_images.py --input report.md
```

4. Build PDF (embeds images as base64 for Chrome print):

```bash
python3 scripts/build_bundle.py --input report.md --outdir output --sources sources.md --generate-images
```

One-shot with approval already given: add `--yes`.

**PDF 封面**：独占一整页 A4；四级字体（大标题 / 副标题 / 作者 / 日期）。可从 report 首行 `# 标题（副标题）`、YAML frontmatter 或 `<!-- rw-cover ... -->` 解析，详见 `references/pdf-output.md`。

## Portability

- **contract**（本文件）：做什么、产出什么
- **methodology**（references/）：调研质量标准
- **scripts**：可重复的制品构建
- **adapters**：各 Agent 环境的执行映射
