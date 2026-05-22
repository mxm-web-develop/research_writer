# Installation

## Requirements

- Python 3.9+
- Google Chrome or Chromium (PDF export)
- pip (or `python3 -m ensurepip`)

## Steps

```bash
python3 scripts/bootstrap.py --install
python3 scripts/doctor.py
```

## Build from a completed report

```bash
python3 scripts/build_bundle.py --input report.md --outdir output --sources sources.md
```

All subprocess scripts use the **same Python interpreter** as the command you run.
