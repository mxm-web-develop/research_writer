# Installation

## Requirements

- Python 3.9+
- Google Chrome or Chromium (PDF export)
- pip (or `python3 -m ensurepip`)
- git

## Install from GitHub（推荐）

**不要**从本地开发目录 `rsync` 到全局 skill 路径。正确流程：

1. 在开发仓库改代码 → commit → push 到 GitHub
2. 在用户机器上从 GitHub 安装/更新：

```bash
bash <(curl -fsSL https://raw.githubusercontent.com/mxm-web-develop/research_writer/main/scripts/install_skill.sh)
```

或已 clone 过仓库时：

```bash
git clone https://github.com/mxm-web-develop/research_writer.git /tmp/research_writer
bash /tmp/research_writer/scripts/install_skill.sh
```

脚本会：

- `git clone` / `git pull` 到 `~/.agents/skills/research_writer/`（唯一源码副本）
- 符号链接到 `~/.cursor/skills/research_writer/`（Cursor）
- 符号链接到 `~/.claude/skills/research_writer/`（Claude Code）
- 运行 `bootstrap.py --install` 与 `doctor.py`

### 更新已安装版本

```bash
~/.agents/skills/research_writer/scripts/install_skill.sh
```

或：

```bash
git -C ~/.agents/skills/research_writer pull origin main
python3 ~/.agents/skills/research_writer/scripts/bootstrap.py --install
python3 ~/.agents/skills/research_writer/scripts/doctor.py
```

## 开发 vs 安装

| 场景 | 路径 | 操作 |
|------|------|------|
| **开发** | 你的 monorepo / fork，如 `expert_skill/research_writer/` | 编辑 → test → push GitHub |
| **使用** | `~/.agents/skills/research_writer/` | 仅 `install_skill.sh` 或 `git pull` |

## Build from a completed report

```bash
python3 ~/.agents/skills/research_writer/scripts/build_bundle.py \
  --input report.md --outdir output --sources sources.md
```

All subprocess scripts use the **same Python interpreter** as the command you run.
