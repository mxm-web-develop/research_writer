# Claude Code Usage

## Recommended Pattern
1. Install skill from GitHub: `bash ~/.agents/skills/research_writer/scripts/install_skill.sh`
2. Load the `research_writer` skill
3. Use Claude Code to research and write `report.md`
4. Complete `sources.md` (see `sources-format.md`)
5. Run bundled scripts for downstream outputs

## Good Fit
- bounded deep research tasks
- report-first workflows
- staged artifact generation

## Suggested Flow
- research and write the report
- verify source coverage
- run:

```bash
python3 scripts/build_bundle.py --input report.md --outdir output
```

This keeps the deliverable build deterministic and script-driven.
