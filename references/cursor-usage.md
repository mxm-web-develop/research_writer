# Cursor Usage

## Setup

1. Copy this skill to `.cursor/skills/research_writer/` (project) or `~/.cursor/skills/research_writer/` (global).
2. Optional: copy `.cursor/rules/research-writer.mdc` into your project `.cursor/rules/`.

## Workflow

1. Use Cursor Agent to research and write `report.md` + `sources.md`.
2. Run bundled scripts for deterministic artifact generation:

```bash
python3 scripts/bootstrap.py --install
python3 scripts/build_bundle.py --input report.md --outdir output --sources sources.md
```

Cursor handles authoring; scripts handle PDF/PPT compilation.

## Failure Recovery

```bash
python3 scripts/build_bundle.py --input report.md --outdir output --stage ppt
```
