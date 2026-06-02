# research_writer

跨 Agent（Claude Code、Cursor、OpenClaw、Hermes）可复用的深度调研输出 Skill **v3.6.0**。

支持 **本地资料扫描** 与 **Tavily 网络调研** 双路径；**10 类文档** 结构路由；以 `report.md` 为单一事实源，自动派生 PDF/PPT 等产物。

## Install

```bash
git clone https://github.com/mxm-web-develop/research_writer.git
cd research_writer
python3 scripts/bootstrap.py --install
python3 scripts/doctor.py
```

将本目录复制到项目的 `.cursor/skills/research_writer/` 或全局 `~/.cursor/skills/research_writer/` 即可在 Cursor 中使用。

## Environment (MXM)

进程环境变量优先；也可写入项目根 `image.env` 或 `.research_writer/image.env`：

```bash
export MXM_RESEARCH_APIKEY="tvly-..."          # Tavily 搜索
export MXM_GEN_IMAGE_KEY="..."                 # AI 配图
export MXM_GEN_IMAGE_URL="https://.../v1/images/generations"
export MXM_GEN_IMAGE_MODEL="gpt-image-2"
```

无 Tavily key 时 Agent 使用 WebSearch 降级（见 `references/fallbacks.md`）。

## 首次调用

Agent 会先运行 `check_env.py`。若缺变量，会引导你配置：

```bash
export MXM_RESEARCH_APIKEY="tvly-..."
export MXM_GEN_IMAGE_KEY="..."
export MXM_GEN_IMAGE_URL="https://.../v1/images/generations"
export MXM_GEN_IMAGE_MODEL="gpt-image-2"
```

也可写入项目根 `image.env`（见 `templates/image.env.example`）。配置后回复「已配置」即可继续。详见 `references/env-setup.md`。

## Usage

1. 复制 `templates/sample-research-brief.md` → `research-brief.md`，识别 `document_type` 与 `input_mode`
2. 本地资料：`python3 scripts/scan_local.py --path ./docs --out local-index.md`
3. 网络调研：`python3 scripts/search_tavily.py --query "..." --append research-brief.md`
4. 完成 `report.md`、`sources.md`
5. 构建产物：

```bash
python3 scripts/build_bundle.py --input report.md --outdir output --sources sources.md
```

## Requirements

- Python 3.9+
- Google Chrome 或 Chromium（PDF 导出）
- `markdown`, `python-pptx`, `lxml`, `tavily-python`（由 bootstrap 安装）

## License

MIT — see [LICENSE](LICENSE).
