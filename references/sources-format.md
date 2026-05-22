# sources.md Format

Each source entry should include:

| Field | Required | Description |
|-------|----------|-------------|
| Title | yes | Source name |
| URL | yes | Canonical link |
| Publisher | yes | Domain or organization |
| Accessed | yes | ISO date (YYYY-MM-DD) |
| Supports | yes | Which fact(s) in `report.md` this source backs |

## Minimum

- At least **5 independent sources** unless the task explicitly relaxes this rule.
- Use `## Source N` headings or a numbered list; `validate.py` counts list items.

## Example

```markdown
## Source 1
- **Title:** Official API Docs
- **URL:** https://example.com/docs
- **Publisher:** Example Inc.
- **Accessed:** 2026-05-22
- **Supports:** API rate limits in Deep Analysis
```
