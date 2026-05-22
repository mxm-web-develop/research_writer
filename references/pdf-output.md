# PDF Output Rules

Preferred approach on macOS:
- use Chrome headless
- render from generated HTML
- keep report structure: cover → TOC → body → references

Key requirements:
1. PDF is derived from `report.md`
2. TOC should reflect report headings
3. references section must be separated and preserved
4. use real file paths for Chrome print-to-pdf

Recommended command:

```bash
python3 scripts/generate_pdf.py --input report.md --output output/report.pdf --title "Research Report"
```

Or use the full pipeline:

```bash
python3 scripts/build_bundle.py --input report.md --outdir output --sources sources.md
```
