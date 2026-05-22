# research_writer

跨 Agent（Claude Code、Cursor、OpenClaw、Hermes）可复用的深度调研输出 Skill。

以 `report.md` 为单一事实源，自动派生 `deck-outline.md`、`speaker-notes.md`、`report.pdf`、`report.pptx`，并通过 `validate.py` 做交付前校验。

## Install

```bash
git clone https://github.com/mxm-web-develop/research_writer.git
cd research_writer
python3 scripts/bootstrap.py --install
python3 scripts/doctor.py
```

将本目录复制到项目的 `.cursor/skills/research_writer/` 或全局 `~/.cursor/skills/research_writer/` 即可在 Cursor 中使用。

## Usage

1. 复制模板：`templates/sample-report.md` → `report.md`，`templates/sample-sources.md` → `sources.md`
2. 完成调研写作
3. 构建产物：

```bash
python3 scripts/build_bundle.py --input report.md --outdir output --sources sources.md
```

## Requirements

- Python 3.9+
- Google Chrome 或 Chromium（PDF 导出）
- `markdown`, `python-pptx`, `lxml`（由 bootstrap 安装）

## License

MIT — see [LICENSE](LICENSE).
