# Troubleshooting

## PDF generation fails

- Run `python3 scripts/doctor.py` — Chrome/Chromium must be available.
- macOS: install Google Chrome. Linux: `google-chrome` or `chromium`.
- Re-run: `python3 scripts/build_bundle.py --input report.md --outdir output --stage pdf`

## Wrong Python / missing modules

Scripts use `sys.executable` (the same `python3` you invoke). If modules are missing:

```bash
python3 scripts/bootstrap.py --install
```

If pip is missing: `python3 -m ensurepip --upgrade`

## PPT generation fails

- Ensure `python-pptx` and `lxml` are installed.
- Ensure `output/deck-outline.md` exists before `--stage ppt`.

## Validation fails on sources

- Add entries to `sources.md` (see `references/sources-format.md`).
- Or pass `--relax-sources` for draft builds.

## Notes and slides drift

```bash
rm output/deck-outline.md output/speaker-notes.md
python3 scripts/build_bundle.py --input report.md --outdir output --stage deck
python3 scripts/build_bundle.py --input report.md --outdir output --stage notes
python3 scripts/build_bundle.py --input report.md --outdir output --stage ppt
```
