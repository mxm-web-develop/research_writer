# OpenClaw Usage

## Recommended Pattern

1. Treat `research_writer` as a **staged workflow**, not a single prompt.
2. Write `report.md` and `sources.md` to the workspace.
3. Run bundled scripts for reproducible PDF/PPT builds.

## Execution Guidance

- Use gateway-level task ingestion for long research jobs.
- Preserve per-session ordering (lane / queue) for consistency.
- Write intermediate artifacts to the workspace for resumability.
- Add heartbeat or checkpoint reviews on multi-hour tasks.

## Adapter Responsibilities

- Map the skill contract into OpenClaw control-plane conventions (SOUL.md / AGENTS.md / MEMORY.md).
- Persist stage outputs: `report.md` → `output/*`
- On failure, rerun only the failed `--stage` (see `build_bundle.py --stage`).

## Suggested Flow

```bash
python3 scripts/bootstrap.py --install
# ... agent completes report.md and sources.md ...
python3 scripts/build_bundle.py --input report.md --outdir output --sources sources.md
python3 scripts/build_bundle.py --input report.md --outdir output --sources sources.md --stage validate
```
