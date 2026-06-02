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
