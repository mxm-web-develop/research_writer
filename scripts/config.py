#!/usr/bin/env python3
"""Central configuration for research_writer (MXM env vars + legacy fallbacks)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# Primary MXM env var names
MXM_RESEARCH_APIKEY = 'MXM_RESEARCH_APIKEY'
MXM_GEN_IMAGE_KEY = 'MXM_GEN_IMAGE_KEY'
MXM_GEN_IMAGE_URL = 'MXM_GEN_IMAGE_URL'
MXM_GEN_IMAGE_MODEL = 'MXM_GEN_IMAGE_MODEL'
MXM_GEN_IMAGE_SIZE = 'MXM_GEN_IMAGE_SIZE'

# Legacy fallbacks (transition only)
_LEGACY_IMAGE = {
    'api_url': 'RW_IMAGE_API_URL',
    'api_key': 'RW_IMAGE_API_KEY',
    'model': 'RW_IMAGE_MODEL',
    'size': 'RW_IMAGE_SIZE',
}
_LEGACY_RESEARCH = ('TAVILY_API_KEY',)


def _load_env_files(project_dir: Path | None) -> dict[str, str]:
    values: dict[str, str] = {}
    if project_dir is None:
        return values
    for env_file in (project_dir / '.research_writer' / 'image.env', project_dir / 'image.env'):
        if not env_file.exists():
            continue
        for line in env_file.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, val = line.split('=', 1)
            values[key.strip().lower()] = val.strip().strip('"').strip("'")
    return values


def _first(*candidates: str) -> str:
    for c in candidates:
        if c:
            return c
    return ''


IMAGE_API_PATH_SUFFIX = '/v1/images/generations'


def normalize_image_api_url(url: str) -> str:
    """Ensure OpenAI-compatible images endpoint path (fixes common 404 from bare gateway host)."""
    url = url.strip().rstrip('/')
    if not url:
        return url
    lower = url.lower()
    if lower.endswith('/v1/images/generations') or lower.endswith('/images/generations'):
        return url
    if lower.endswith('/v1'):
        return url + '/images/generations'
    return url + IMAGE_API_PATH_SUFFIX


def validate_image_api_url(url: str) -> list[str]:
    warnings: list[str] = []
    if not url:
        return warnings
    normalized = normalize_image_api_url(url)
    if normalized != url.rstrip('/'):
        warnings.append(
            f'MXM_GEN_IMAGE_URL will be normalized to include {IMAGE_API_PATH_SUFFIX} '
            f'(was missing path — common cause of HTTP 404)'
        )
    if not normalized.lower().endswith('/v1/images/generations'):
        warnings.append(
            f'MXM_GEN_IMAGE_URL should end with {IMAGE_API_PATH_SUFFIX}; got: {url}'
        )
    return warnings


@dataclass
class ResearchConfig:
    api_key: str = ''

    @property
    def ready(self) -> bool:
        return bool(self.api_key)


@dataclass
class ImageConfig:
    api_url: str = ''
    api_key: str = ''
    model: str = 'gpt-image-2'
    size: str = '1024x1024'
    assets_dir: Path = field(default_factory=lambda: Path('assets'))

    @property
    def ready(self) -> bool:
        return bool(self.api_url and self.api_key)


def load_research_config(project_dir: Path | None = None) -> ResearchConfig:
    file_vals = _load_env_files(project_dir)
    api_key = _first(
        os.environ.get(MXM_RESEARCH_APIKEY, ''),
        file_vals.get('mxm_research_apikey', ''),
        file_vals.get('tavily_api_key', ''),
        *(os.environ.get(k, '') for k in _LEGACY_RESEARCH),
    )
    return ResearchConfig(api_key=api_key)


def load_image_config(project_dir: Path | None = None, assets_dir: Path | None = None) -> ImageConfig:
    file_vals = _load_env_files(project_dir)
    api_url = _first(
        os.environ.get(MXM_GEN_IMAGE_URL, ''),
        file_vals.get('mxm_gen_image_url', ''),
        os.environ.get(_LEGACY_IMAGE['api_url'], ''),
        file_vals.get('rw_image_api_url', ''),
    )
    if api_url:
        api_url = normalize_image_api_url(api_url)
    api_key = _first(
        os.environ.get(MXM_GEN_IMAGE_KEY, ''),
        file_vals.get('mxm_gen_image_key', ''),
        os.environ.get(_LEGACY_IMAGE['api_key'], ''),
        file_vals.get('rw_image_api_key', ''),
    )
    model = _first(
        os.environ.get(MXM_GEN_IMAGE_MODEL, ''),
        file_vals.get('mxm_gen_image_model', ''),
        os.environ.get(_LEGACY_IMAGE['model'], ''),
        file_vals.get('rw_image_model', ''),
        'gpt-image-2',
    )
    size = _first(
        os.environ.get(MXM_GEN_IMAGE_SIZE, ''),
        file_vals.get('mxm_gen_image_size', ''),
        os.environ.get(_LEGACY_IMAGE['size'], ''),
        file_vals.get('rw_image_size', ''),
        '1024x1024',
    )
    return ImageConfig(
        api_url=api_url,
        api_key=api_key,
        model=model,
        size=size,
        assets_dir=assets_dir or Path('assets'),
    )


def export_setup_hint() -> str:
    return (
        'export MXM_RESEARCH_APIKEY="your-tavily-key"\n'
        'export MXM_GEN_IMAGE_KEY="your-image-key"\n'
        'export MXM_GEN_IMAGE_URL="https://your-gateway/v1/images/generations"\n'
        'export MXM_GEN_IMAGE_MODEL="gpt-image-2"'
    )


@dataclass
class EnvStatus:
    research_ready: bool
    image_ready: bool
    research_source: str = ''
    image_source: str = ''

    @property
    def all_ready(self) -> bool:
        return self.research_ready and self.image_ready

    @property
    def missing_research(self) -> bool:
        return not self.research_ready

    @property
    def missing_image(self) -> bool:
        return not self.image_ready


def _detect_source(env_key: str, file_vals: dict[str, str], *legacy_keys: str) -> str:
    if os.environ.get(env_key):
        return 'process env'
    lowered = env_key.lower()
    if file_vals.get(lowered):
        return 'image.env'
    for lk in legacy_keys:
        if os.environ.get(lk):
            return f'legacy ({lk})'
    return ''


def check_env_status(project_dir: Path | None = None) -> EnvStatus:
    file_vals = _load_env_files(project_dir)
    research = load_research_config(project_dir)
    image = load_image_config(project_dir)
    research_source = _detect_source(MXM_RESEARCH_APIKEY, file_vals, *_LEGACY_RESEARCH)
    image_source = ''
    if image.ready:
        if os.environ.get(MXM_GEN_IMAGE_KEY) or os.environ.get(MXM_GEN_IMAGE_URL):
            image_source = 'process env'
        elif file_vals.get('mxm_gen_image_key') or file_vals.get('mxm_gen_image_url'):
            image_source = 'image.env'
        else:
            image_source = 'legacy RW_IMAGE_*'
    return EnvStatus(
        research_ready=research.ready,
        image_ready=image.ready,
        research_source=research_source,
        image_source=image_source,
    )


def format_first_run_onboarding(
    status: EnvStatus,
    *,
    input_mode: str = 'web',
    needs_images: bool = False,
) -> str:
    """User-facing onboarding when env vars are missing (Agent shows this on first call)."""
    lines: list[str] = []
    need_research = status.missing_research and input_mode in ('web', 'hybrid')
    need_image = status.missing_image and needs_images

    if not need_research and not need_image:
        return ''

    lines.append('## research_writer 环境配置（首次使用）')
    lines.append('')
    lines.append('检测到尚未配置以下 API 凭证。请先配置后再继续（或选择降级方案）。')
    lines.append('')

    if need_research:
        lines.append('### 1. 网络调研 — `MXM_RESEARCH_APIKEY`（Tavily）')
        lines.append('')
        lines.append('用于 `search_tavily.py` 自动搜索。请在终端执行（建议写入 `~/.zshrc` 后 `source ~/.zshrc`）：')
        lines.append('')
        lines.append('```bash')
        lines.append('export MXM_RESEARCH_APIKEY="tvly-你的密钥"')
        lines.append('```')
        lines.append('')
        lines.append('或复制 `templates/image.env.example` → 项目根 `image.env`，填入同名变量。')
        lines.append('')
        lines.append('**暂不配置？** 可改用 Cursor WebSearch 降级，但请在 brief §3 标注来源 tier。')
        lines.append('')

    if need_image:
        lines.append('### 2. AI 配图 — `MXM_GEN_IMAGE_*`')
        lines.append('')
        lines.append('用于 GPT-image-2 自动生成插图。请在终端执行：')
        lines.append('')
        lines.append('```bash')
        lines.append('export MXM_GEN_IMAGE_KEY="你的生图密钥"')
        lines.append('export MXM_GEN_IMAGE_URL="https://你的网关/v1/images/generations"')
        lines.append('export MXM_GEN_IMAGE_MODEL="gpt-image-2"')
        lines.append('```')
        lines.append('')
        lines.append('**暂不配置？** 可仅使用本地图片，跳过 AI 生图。')
        lines.append('')

    if need_research and need_image:
        lines.append('### 一次性配置全部变量')
        lines.append('')
        lines.append('```bash')
        lines.append(export_setup_hint())
        lines.append('```')
        lines.append('')

    lines.append('配置完成后请回复 **「已配置」**，Agent 将运行 `python3 scripts/check_env.py` 验证并继续。')
    return '\n'.join(lines)
