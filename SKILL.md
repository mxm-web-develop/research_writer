---
name: research_writer
description: Cross-agent deep research skill for Claude Code, Cursor, OpenClaw, and Hermes — report.md as source of truth, then sources/deck/notes/PDF/PPT via bundled scripts.
version: 3.4.1
author: HanfengZhang_mxm
license: MIT
metadata:
  hermes:
    tags: [research, report, pdf, ppt, claude-code, cursor, openclaw, deliverables]
    related_skills: [expert, md-to-pdf, powerpoint]
---

# research_writer

跨 Agent 可复用的深度调研输出 Skill：以 `report.md` 为单一事实源，派生来源清单、幻灯片大纲、口播稿、PDF 与 PPT。

## When to Use

- 多源深度调研 + 结构化 Markdown 报告
- 需要 PDF / PPT / 口播稿等正式交付物
- 同一工作流需在 Claude Code、Cursor、OpenClaw 等环境复用

## Required Outputs

| 文件 | 说明 |
|------|------|
| `report.md` | 主报告（必须先完成） |
| `sources.md` | 来源台账（Agent 撰写，格式见 `references/sources-format.md`） |
| `output/deck-outline.md` | 由脚本从 report 派生 |
| `output/speaker-notes.md` | 由脚本从 report 派生 |
| `output/report.pdf` | 由脚本从 report 编译 |
| `output/report.pptx` | 由 deck-outline + speaker-notes 编译 |

## Single Source of Truth

1. 先写 `report.md` 与 `sources.md`
2. 再运行 `build_bundle.py`
3. PPT / 口播稿不得引入 report 中不存在的主张

## Quick Start

```bash
# 1. 安装依赖（使用当前 Python 解释器）
python3 scripts/bootstrap.py --install
python3 scripts/doctor.py

# 2. 撰写 report.md、sources.md（可参考 templates/）

# 3. 一键构建派生产物并校验
python3 scripts/build_bundle.py --input report.md --outdir output --sources sources.md
```

分阶段重跑（失败恢复）：

```bash
python3 scripts/build_bundle.py --input report.md --outdir output --stage deck
python3 scripts/build_bundle.py --input report.md --outdir output --stage images
python3 scripts/build_bundle.py --input report.md --outdir output --stage pdf
python3 scripts/build_bundle.py --input report.md --outdir output --stage ppt
python3 scripts/build_bundle.py --input report.md --outdir output --sources sources.md --stage validate
```

## Standard Report Structure

1. Executive Summary
2. Background and Context
3. Problem Definition
4. Deep Analysis
5. Comparison / Alternatives
6. Risks and Constraints
7. Recommendations / Conclusion
8. References

## Workflow

1. 明确调研目标与排除项
2. 拆分研究维度并多源检索
3. 交叉验证关键事实，标注时间
4. 撰写 `report.md`
5. 撰写 `sources.md`（≥5 条独立来源，除非任务放宽）
6. 运行 `build_bundle.py`
7. 通过 `validate.py` 质量门禁后交付

## Agent Adapters

| 环境 | 说明 |
|------|------|
| Claude Code | `references/claude-code-usage.md` |
| Cursor | `references/cursor-usage.md` + `.cursor/rules/research-writer.mdc` |
| OpenClaw | `references/openclaw-usage.md` |

## Bundled Files

**Scripts:** `bootstrap.py`, `doctor.py`, `build_bundle.py`, `generate_images.py`, `generate_pdf.py`, `generate_ppt.py`, `validate.py`, `common.py`, `images.py`

**References:** `research-methodology.md`, `sources-format.md`, `images.md`, `pdf-output.md`, `installation.md`, `troubleshooting.md`, agent usage docs

**Templates:** `sample-report.md`, `sample-sources.md`, `requirements.txt`, `image.env.example`

## Quality Gates

`validate.py` 检查（可通过 `--relax-sources` 放宽来源数）：

- `sources.md` 条目数量
- 报告推荐章节结构
- 输出目录中派生文件齐全

人工复核：

- 重要事实含日期/时间范围
- PDF 目录与 report 标题一致
- PPT 与 report 观点不矛盾
- 口播稿与对应幻灯片主题一致

## Project Layout

```text
project/
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
2. Configure `image.env` from `templates/image.env.example` (URL + key + model).
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
