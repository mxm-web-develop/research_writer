# Fallback Strategies

When MXM API keys are missing or calls fail, use this order.

## Search

| Priority | Method | When |
|----------|--------|------|
| 1 | **Tavily** (`search_tavily.py`, `MXM_RESEARCH_APIKEY`) | Default for web research |
| 2 | **Cursor WebSearch** | Tavily key missing or script fails |
| 3 | **Browser MCP** | Need full page / official docs |
| 4 | **Local scan only** (`scan_local.py`) | User provided folder; web optional |

Agent must log which method was used in `research-brief.md` §3.

### Setup Tavily

```bash
export MXM_RESEARCH_APIKEY="tvly-..."
python3 scripts/search_tavily.py --query "topic overview" --append research-brief.md
```

### Free fallback (no Tavily key)

1. Tell user how to set `MXM_RESEARCH_APIKEY`
2. If user declines: use Cursor **WebSearch** + browser; mark sources tier T2/T3
3. Never present unverified claims as high confidence

## Image generation

| Priority | Method | When |
|----------|--------|------|
| 1 | **MXM_GEN_IMAGE_*** + `generate_images.py` | Default for AI illustrations |
| 2 | **Legacy RW_IMAGE_*** / `image.env` | Transition only |
| 3 | **Local assets** | User screenshots, diagrams |
| 4 | **Skip AI images** | No keys; validate warns on pending `rw-image` |

```bash
export MXM_GEN_IMAGE_KEY="..."
export MXM_GEN_IMAGE_URL="https://.../v1/images/generations"
export MXM_GEN_IMAGE_MODEL="gpt-image-2"
```

## Document structure

| Priority | Method |
|----------|--------|
| 1 | Built-in type template (`references/document-types/{id}.md`) |
| 2 | Tavily: `"[type] 文档结构 写作规范"` |
| 3 | Agent knowledge (lowest; note in brief if no search) |
