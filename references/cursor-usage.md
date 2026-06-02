# Cursor Usage

## Setup

1. **Install from GitHub** (not rsync from a dev checkout):

```bash
bash ~/.agents/skills/research_writer/scripts/install_skill.sh
```

2. Copy `.cursor/rules/research-writer.mdc` from the installed skill into your project `.cursor/rules/` (optional; enforces workflow on `report.md`).

## Research workflow (Agent)

**On first call**, run env check before intake:

```bash
python3 ~/.cursor/skills/research_writer/scripts/check_env.py \
  --project-dir . --input-mode web --needs-images
```

If keys are missing, guide the user per `references/env-setup.md` and wait for confirmation.

**Read `references/intake-and-search.md` first.** Summary:

1. Copy `templates/sample-research-brief.md` → `research-brief.md`
2. Phase 0: clarify requirement; set **document_type** and **input_mode**
3. Phase 0.5: **`scan_local.py`** (local/hybrid) and/or **`search_tavily.py`** (web/hybrid; needs `MXM_RESEARCH_APIKEY`)
4. Phase 1: dimensions from type template
5. Phase 2: multi-round search; populate `sources.md` during search
6. Phase 3: reasoning chains, conflicts, gaps
7. Phase 4: write `report.md` (type-specific sections), then build artifacts

**When to use scripts vs Agent tools:**

| Task | Prefer |
|------|--------|
| Local folder index | `scan_local.py` |
| Web search (key set) | `search_tavily.py` |
| Web search (no key) | Cursor **WebSearch** + browser |
| Structure lookup | `references/document-types/{id}.md` |
| PDF/PPT build | `build_bundle.py` |

Fallbacks: `references/fallbacks.md`

## Build workflow (Scripts)

Install once:

```bash
python3 ~/.cursor/skills/research_writer/scripts/bootstrap.py --install
python3 ~/.cursor/skills/research_writer/scripts/doctor.py
```

After `report.md` is complete, from your project directory:

```bash
python3 ~/.cursor/skills/research_writer/scripts/build_bundle.py \
  --input report.md --outdir output --sources sources.md
```

Scripts handle PDF/PPT compilation; Agent handles research and authoring.

## Failure Recovery

```bash
python3 ~/.cursor/skills/research_writer/scripts/build_bundle.py \
  --input report.md --outdir output --stage search --brief research-brief.md

python3 ~/.cursor/skills/research_writer/scripts/build_bundle.py \
  --input report.md --outdir output --stage ppt
```
