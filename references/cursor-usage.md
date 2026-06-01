# Cursor Usage

## Setup

1. Copy this skill to `.cursor/skills/research_writer/` (project) or `~/.cursor/skills/research_writer/` (global).
2. Optional: copy `.cursor/rules/research-writer.mdc` into your project `.cursor/rules/`.

## Workflow

1. Use Cursor Agent to research and write `report.md` + `sources.md` in your project root.
2. Install dependencies once (from the skill directory):

```bash
python3 ~/.cursor/skills/research_writer/scripts/bootstrap.py --install
python3 ~/.cursor/skills/research_writer/scripts/doctor.py
```

3. Build deliverables **from your project directory** (use the absolute script path; `doctor.py` prints the exact command):

```bash
cd /path/to/your/project
python3 ~/.cursor/skills/research_writer/scripts/build_bundle.py \
  --input report.md --outdir output --sources sources.md
```

If the skill is project-local, replace `~/.cursor/skills/research_writer` with `.cursor/skills/research_writer`.

Cursor handles authoring; scripts handle PDF/PPT compilation.

## Failure Recovery

```bash
python3 ~/.cursor/skills/research_writer/scripts/build_bundle.py \
  --input report.md --outdir output --stage ppt
```
