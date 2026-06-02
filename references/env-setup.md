# Environment Setup（首次调用必做）

Agent **must** run env check **before Phase 0** on every new project/session when MXM vars may be unset.

## Preflight command

From project directory (or skill root):

```bash
python3 ~/.cursor/skills/research_writer/scripts/check_env.py \
  --project-dir . \
  --input-mode web \
  --needs-images
```

Flags:

| Flag | When |
|------|------|
| `--input-mode local` | 仅本地 scan，不要求 `MXM_RESEARCH_APIKEY` |
| `--input-mode web` | 需要 Tavily；缺 key 则输出引导 |
| `--input-mode hybrid` | 同 web |
| `--needs-images` | 用户要 AI 配图时加上；缺 key 则输出引导 |
| `--json` | Agent 解析用 |

## Agent workflow（第一次调用）

1. **判断模式**：从用户请求推断 `input_mode` 与是否要配图
2. **运行** `check_env.py`（带对应 flags）
3. **若输出 onboarding**：
   - **暂停**后续搜索/写作
   - **原样展示**引导文案（含 `export` 命令）
   - **等待用户**配置并回复「已配置」或选择降级（WebSearch / 仅本地图）
4. **用户确认后**再跑 `check_env.py` 验证，然后进入 Phase 0

## 引导文案模板（缺变量时展示）

```markdown
## research_writer 环境配置（首次使用）

检测到尚未配置 API 凭证。请先配置后再继续（或选择降级方案）。

### 1. 网络调研 — MXM_RESEARCH_APIKEY（Tavily）

```bash
export MXM_RESEARCH_APIKEY="tvly-你的密钥"
```

或写入项目根 `image.env`（从 `templates/image.env.example` 复制）。

**暂不配置？** 可改用 Cursor WebSearch，在 brief §3 标注来源 tier。

### 2. AI 配图 — MXM_GEN_IMAGE_*

```bash
export MXM_GEN_IMAGE_KEY="你的生图密钥"
export MXM_GEN_IMAGE_URL="https://你的网关/v1/images/generations"
export MXM_GEN_IMAGE_MODEL="gpt-image-2"
```

**暂不配置？** 可仅使用本地图片。

### 一次性配置

```bash
export MXM_RESEARCH_APIKEY="tvly-..."
export MXM_GEN_IMAGE_KEY="..."
export MXM_GEN_IMAGE_URL="https://.../v1/images/generations"
export MXM_GEN_IMAGE_MODEL="gpt-image-2"
```

配置完成后回复 **「已配置」**，我将验证并继续。
```

## 持久化方式

| 方式 | 适用 |
|------|------|
| `export` in `~/.zshrc` / `~/.bashrc` | 全局，推荐 |
| 项目根 `image.env` | 仅当前项目 |
| `.research_writer/image.env` | 仅当前项目（不提交 git） |

进程环境变量 **优先于** `image.env`。

## 验证

```bash
python3 scripts/doctor.py
python3 scripts/check_env.py --project-dir . --input-mode web
```

## 安全

- **Never** 将真实密钥写入 `report.md`、`research-brief.md` 或 git 跟踪文件
- 引导用户只粘贴到终端或本地 `image.env`（已在 `.gitignore`）
