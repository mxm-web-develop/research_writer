# Images in Reports

`report.md` and generated PDFs support **local images** and **AI-generated illustrations** via `rw-image` directives.

## Local image (user-provided)

Standard Markdown:

```markdown
![产品架构概览](assets/architecture.png)
```

Or directive form (copied into `assets/` at build time):

```markdown
<!-- rw-image
id: architecture
mode: local
src: ./design/architecture.png
alt: 产品架构概览
-->
```

Paths are relative to `report.md`. Supported formats: PNG, JPG, GIF, WebP, SVG.

## AI-generated image (GPT-image-2)

Mark sections that need an illustration. **The Agent must ask the user for permission before generating.**

```markdown
<!-- rw-image
id: market-map
mode: generate
prompt: Clean flat infographic showing three market segments with labels, professional consulting style, light background, no watermark
alt: 市场格局示意图
size: 1024x1024
-->
```

JSON one-liner also works:

```markdown
<!-- rw-image: {"id":"timeline","mode":"generate","prompt":"Horizontal timeline 2024-2027 with four milestones","alt":"发展时间线"} -->
```

## Configuration

Copy `templates/image.env.example` → `image.env` (project root) or `.research_writer/image.env`:

```bash
RW_IMAGE_API_URL=https://your-gateway.example/v1/images/generations
RW_IMAGE_API_KEY=your-key
RW_IMAGE_MODEL=gpt-image-2
RW_IMAGE_SIZE=1024x1024
```

Or export env vars: `RW_IMAGE_API_URL`, `RW_IMAGE_API_KEY`, `RW_IMAGE_MODEL`.

**Never commit API keys.**

## Build commands

List pending images:

```bash
python3 scripts/generate_images.py --input report.md --dry-run
```

Generate with interactive confirmation:

```bash
python3 scripts/generate_images.py --input report.md
```

Non-interactive (CI / approved batch):

```bash
python3 scripts/generate_images.py --input report.md --yes
```

Full pipeline with AI images:

```bash
python3 scripts/build_bundle.py \
  --input report.md --outdir output --sources sources.md \
  --generate-images --yes
```

PDF only (local images embedded; pending AI images skipped with warning):

```bash
python3 scripts/generate_pdf.py --input report.md --output output/report.pdf
```

## Agent rules (Cursor / Claude Code)

### 触发条件

用户说「给这个话题/项目配图」「生成插图」「report 需要图」等时，进入 **配图咨询流程**（非立即生成）。

### 流程（四步，不可跳步）

#### 第 1 步：询问 API 凭证

若 `image.env` / `.research_writer/image.env` 不存在或未配置，先问用户：

- GPT-image-2 **API URL**（如 `https://…/v1/images/generations`）
- **API Key**
- 可选：model 名称（默认 `gpt-image-2`）、尺寸（默认 `1024x1024`）

说明：凭证仅用于本地 `image.env`，勿写入 `report.md` 或提交 git。

**此步只收集信息，不调 API。**

#### 第 2 步：分析话题/项目

结合以下来源做结构化分析：

| 输入 | 用途 |
|------|------|
| 已有 `report.md` | 按章节扫描：哪里信息密度高、缺视觉辅助 |
| 项目 README / 架构文档 | 识别系统边界、模块关系、用户流程 |
| 用户口头描述 | 补全报告尚未覆盖的交付场景 |

判断哪些位置**值得配图**（不是每节都要）：

- **架构 / 模块关系** → 系统框图、分层图
- **流程 / 时序** → 步骤图、泳道图、timeline
- **对比 / 方案选型** → 对比矩阵可视化、雷达图
- **市场 / 生态** → 格局示意图、产业链图
- **产品 UI** → 优先 **本地截图**，非 AI 臆造
- **数据结论** → 仅当有真实数据时可建议图表；无数据则不生成误导图

#### 第 3 步：回复配图建议（等用户确认）

用下方 **配图建议模板** 回复，**不要**在此步运行 `generate_images.py`。

用户确认后再进入第 4 步（写 directive + 生成）。

#### 第 4 步：执行（用户批准后）

1. 将批准项写入 `report.md`（`rw-image` 或本地 `![...](assets/...)`）
2. 写入 `image.env`
3. 运行 `generate_images.py` 或 `build_bundle --generate-images`（需用户明确同意；非交互加 `--yes`）

---

### 配图建议模板

Agent 回复建议时，使用类似结构：

```markdown
## 配图建议：[话题/项目名称]

**分析摘要**：（2–3 句：文档类型、读者、当前缺视觉辅助的主要问题）

| # | 建议位置 | 类型 | 优先级 | 用途 | 建议 prompt / 来源 |
|---|----------|------|--------|------|-------------------|
| 1 | §3 架构分层 | AI 生成 | 高 | 展示 Content Script / Popup / Backend 三层关系 | Flat technical architecture diagram, three horizontal layers… |
| 2 | §6 页面助理流程 | AI 生成 | 高 | observe→decide→act 循环 | Circular or left-to-right flowchart, 4 steps… |
| 3 | §3.1 界面 | 本地 | 中 | Popup 截图 | 请用户提供 `assets/popup-screenshot.png` |
| 4 | §2 五种业务模式 | AI 生成 | 低 | 五模式关系总览 | Five-mode capability matrix, minimal icons… |

**不建议配图**：References、纯文字列表章节、无稳定视觉语义的概念段。

**下一步**：请确认要采纳的条目（可删改优先级）。确认后我将写入 `report.md` 并调用 GPT-image-2 生成。
```

---

### 其他规则

- 有用户截图/Logo 时，**优先本地**，不用 AI 重画。
- Prompt 须具体（风格、布局、元素、禁止水印）；避免与 report 事实矛盾的臆造内容。
- 用户只问「要不要配图」时，只做第 2–3 步，不索要 Key（除非用户已表示要 AI 生成）。

## PDF rendering

- Images are embedded as base64 in HTML so Chrome headless can print them reliably.
- Wide images scale to page width; captions use the `alt` text from the directive or Markdown.
