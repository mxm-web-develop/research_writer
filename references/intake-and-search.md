# Intake, Search & Reasoning

Agent **must** complete Phases 0–2 before drafting `report.md`. Do not skip straight to writing or `build_bundle.py`.

Cursor agents: use **`search_tavily.py`** when `MXM_RESEARCH_APIKEY` is set; otherwise **WebSearch**, **codebase search**, and **browser** (see `references/fallbacks.md`). Never rely on parametric knowledge alone for factual claims.

---

## Preflight — Environment Check（首次 / 新会话必做）

**Before Phase 0**, run:

```bash
python3 scripts/check_env.py --project-dir . --input-mode web
```

Add `--needs-images` if the user wants AI-generated illustrations.

| Missing | Required when | Agent action |
|---------|---------------|--------------|
| `MXM_RESEARCH_APIKEY` | `input_mode` = web or hybrid | **Stop**; show export guide from `references/env-setup.md`; wait for user |
| `MXM_GEN_IMAGE_*` | user asked for AI images | **Stop**; show export guide; or user opts for local-only images |

If onboarding is printed:

1. Present the `export` commands (do not invent keys)
2. Wait for **「已配置」** or explicit fallback choice
3. Re-run `check_env.py` to verify
4. Then proceed to Phase 0

`local`-only tasks skip Tavily requirement.

See **`references/env-setup.md`** for full template.

---

## Phase 0 — Requirement Intake（需求澄清）

Extract or confirm with the user when ambiguous:

| Field | Questions |
|-------|-----------|
| **Core question** | 用户究竟要回答什么？一句话调研命题 |
| **document_type** | 10 类之一（见 `references/document-types/README.md`）；默认 `research-report` |
| **Audience** | 给谁看（决策层 / 研发 / 投资 / 通用） |
| **Scope** | 时间范围、地域、产品/技术边界 |
| **Out of scope** | 明确不做什么（避免报告发散） |
| **Deliverables** | report only？PDF/PPT？是否要配图？ |
| **Decision context** | 用户要用这份报告做什么决策？ |

If the user request is vague, **ask 2–4 clarifying questions** before searching. Do not guess scope silently.

Write output to `research-brief.md` §1 (see `templates/sample-research-brief.md`).

Load the matching type template from `references/document-types/{document_type}.md` for required sections, tone, and recommended search queries.

---

## Phase 0.5 — Input Mode（输入模式判定）

| Mode | Trigger | Data collection |
|------|---------|-----------------|
| **local** | User provides file/folder path | `scan_local.py` → `local-index.md` |
| **web** | Topic only, no local materials | `search_tavily.py` or Agent WebSearch |
| **hybrid** | Local materials + external gaps | scan first, then Tavily/WebSearch for gaps |

Record in `research-brief.md` §1: `input_mode` and `local_paths` (if any).

### Local scan

```bash
python3 scripts/scan_local.py --path /path/to/folder --out local-index.md
python3 scripts/scan_local.py --path ./docs --include-code   # optional .py/.ts headers
```

Output: file paths, headings, summaries. Cite in `sources.md` with Publisher = path, URL = relative path or `file://`.

### Web search (Tavily)

```bash
export MXM_RESEARCH_APIKEY="tvly-..."
python3 scripts/search_tavily.py --query "[topic] overview 2025" --append research-brief.md
```

Batch from brief §3 queries:

```bash
python3 scripts/build_bundle.py --input report.md --outdir output --stage search --brief research-brief.md
```

**Fallback chain** (`references/fallbacks.md`): Tavily → Cursor WebSearch → browser → local-only (with tier labels).

---

## Phase 1 — Multi-Dimensional Framing（多维框架）

Select **4–6 dimensions** tailored to the topic **and document_type**. Start from the type template's recommended dimensions, then this menu:

| Dimension | Typical angles |
|-----------|----------------|
| Background & context | 历史、定义、为什么现在重要 |
| Current state | 主流方案、市场份额、成熟度 |
| Architecture / mechanism | 怎么实现的、关键组件、数据流 |
| Comparison / alternatives | 竞品、路线 A vs B、trade-offs |
| Business / ecosystem | 定价、商业模式、产业链 |
| Risks & constraints | 合规、技术债、锁定、失败模式 |
| Trends & outlook | 12–36 个月演进、催化剂 |

For each dimension, define:

1. **Sub-questions**（2–3 个可验证问题）
2. **What would change our conclusion**（反证条件）
3. **Preferred source types**（官方文档 / 论文 / 监管 / 一手新闻）

Write to `research-brief.md` §2.

---

## Phase 2 — Deep Search Protocol（深度搜索）

### Search rounds（至少 3 轮）

| Round | Goal | Query style |
|-------|------|-------------|
| **R1 — Landscape** | 建立全局地图 | broad: `"[topic] overview"`, `"[topic] market 2025 2026"` |
| **R2 — Depth** | 每维度 2+ 针对性查询 | `"[topic] architecture"`, `"[competitor] vs [alternative]"` |
| **R3 — Verify** | 交叉验证关键事实 | 换关键词、换来源类型、查官方/primary |

Per dimension: **minimum 2 independent sources**. Important claims: **≥2 sources that agree**, or mark as **single-source / uncertain**.

### Source tiers（优先级）

| Tier | Examples | Use for |
|------|----------|---------|
| **T1** | Official docs, standards, filings, repo README, API reference | Architecture, capabilities, limits |
| **T2** | Peer-reviewed, major analyst (named), reputable tech media with citations | Market, trends |
| **T3** | Blogs, forums, social | Hypotheses only; verify elsewhere |

Record every meaningful source in `sources.md` (format: `references/sources-format.md`) **as you search**, not after writing the report.

### Search execution (Cursor / scripts)

1. **`search_tavily.py`** — when `MXM_RESEARCH_APIKEY` is set; log in §3
2. **WebSearch** — fallback or supplement; vary query language (中文/英文)
3. **`scan_local.py`** — local/hybrid mode; index in `local-index.md`
4. **Codebase / docs in repo** — for product-internal topics
5. **Browser** — when snippets insufficient; fetch official pages
6. **Stop rule** — dimension covered when sub-questions have T1/T2 backing OR explicitly logged as gap

Log queries + key findings in `research-brief.md` §3–§4.

---

## Phase 3 — Reasoning & Synthesis（推理综合）

Before writing `report.md`, complete in `research-brief.md` §5–§6:

### Evidence → Claim chain

For each major conclusion, document:

```text
Claim: [one sentence]
Evidence: [Source N], [Source M]
Reasoning: [why evidence supports claim]
Confidence: high / medium / low
Caveats: [scope limits, date, conflict]
```

### Cross-validation

- List **conflicts** between sources; resolve or present both sides
- Flag **stale** data (note access date; prefer ≤18 months for fast-moving tech)
- Run **devil's advocate**: strongest argument against your emerging thesis

### Gap honesty

§7 Open questions: what you could not verify. Do not fabricate to fill sections.

---

## Phase 4 — Write Report（写作）

Only after Phases 0–3:

1. `sources.md` — complete; entry count ≥ type's `min_sources` (default 5)
2. `report.md` — sections per **document_type** template; every key claim traceable to sources
3. `build_bundle.py` — deterministic artifacts

Report section mapping for **`research-report`** (other types: see `references/document-types/`):

| Report section | Primary inputs |
|----------------|----------------|
| Executive Summary | §6 synthesis, top 3 claims |
| Background | Dim: background + current state |
| Problem Definition | Phase 0 core question |
| Deep Analysis | Dims: architecture, mechanism, depth searches |
| Comparison / Alternatives | Dim: comparison |
| Risks and Constraints | Dim: risks + devil's advocate |
| Recommendations | §6 + decision context; no new facts |
| References | Mirror `sources.md` |

---

## Anti-patterns（禁止）

- Writing `report.md` from memory without search logs
- Single-source critical claims presented as certain
- Search once, one query per dimension
- Skipping `research-brief.md` on "simple" topics
- Adding facts in PDF/PPT/deck that are not in `report.md`

---

## Completion checklist

- [ ] Phase 0: scope, audience, **document_type**, **input_mode** in `research-brief.md`
- [ ] Phase 0.5: `local-index.md` and/or Tavily/WebSearch logs in §3
- [ ] Phase 1: 4–6 dimensions with sub-questions
- [ ] Phase 2: ≥3 search rounds; ≥5 sources; important claims cross-checked
- [ ] Phase 3: claim chains + conflicts + gaps documented
- [ ] Phase 4: `report.md` + `sources.md` written; `validate` passes
