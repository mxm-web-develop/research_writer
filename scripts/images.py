#!/usr/bin/env python3
"""Image directives, local assets, and GPT-image API generation for research_writer."""
from __future__ import annotations

import base64
import hashlib
import json
import mimetypes
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

RW_IMAGE_BLOCK = re.compile(r'<!--\s*rw-image\b(.*?)-->', re.DOTALL | re.IGNORECASE)
MD_IMAGE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
IMG_TAG = re.compile(r'<img\b([^>]*?)\bsrc="([^"]+)"([^>]*)>', re.IGNORECASE)

ENV_KEYS = {
    'api_url': 'RW_IMAGE_API_URL',
    'api_key': 'RW_IMAGE_API_KEY',
    'model': 'RW_IMAGE_MODEL',
    'size': 'RW_IMAGE_SIZE',
}


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


@dataclass
class ImageSpec:
    id: str
    mode: str
    prompt: str = ''
    src: str = ''
    alt: str = ''
    size: str = '1024x1024'
    marker: str = ''

    @property
    def output_name(self) -> str:
        safe = re.sub(r'[^a-zA-Z0-9_-]+', '-', self.id).strip('-').lower() or 'image'
        return f'{safe}.png'

    def output_path(self, assets_dir: Path) -> Path:
        return assets_dir / self.output_name


def _parse_block_body(body: str) -> dict[str, str]:
    body = body.strip()
    if not body:
        return {}
    if body.startswith(':'):
        body = body[1:].strip()
    if body.startswith('{'):
        try:
            data = json.loads(body)
            return {str(k): str(v) for k, v in data.items()}
        except json.JSONDecodeError:
            return {}
    out: dict[str, str] = {}
    for line in body.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if ':' not in line:
            continue
        key, value = line.split(':', 1)
        out[key.strip().lower()] = value.strip()
    return out


def parse_rw_image_directives(md_text: str) -> list[ImageSpec]:
    specs: list[ImageSpec] = []
    for match in RW_IMAGE_BLOCK.finditer(md_text):
        data = _parse_block_body(match.group(1))
        image_id = data.get('id') or f'fig-{len(specs) + 1}'
        mode = data.get('mode', 'local').lower()
        specs.append(
            ImageSpec(
                id=image_id,
                mode=mode,
                prompt=data.get('prompt', ''),
                src=data.get('src', ''),
                alt=data.get('alt', image_id),
                size=data.get('size', '1024x1024'),
                marker=match.group(0),
            )
        )
    return specs


def load_image_config(project_dir: Path, assets_dir: Path | None = None) -> ImageConfig:
    values: dict[str, str] = {}
    for env_file in (project_dir / '.research_writer' / 'image.env', project_dir / 'image.env'):
        if env_file.exists():
            for line in env_file.read_text(encoding='utf-8').splitlines():
                line = line.strip()
                if not line or line.startswith('#') or '=' not in line:
                    continue
                key, val = line.split('=', 1)
                values[key.strip().lower()] = val.strip().strip('"').strip("'")
    cfg = ImageConfig(
        api_url=os.environ.get(ENV_KEYS['api_url'], values.get('rw_image_api_url', '')),
        api_key=os.environ.get(ENV_KEYS['api_key'], values.get('rw_image_api_key', '')),
        model=os.environ.get(ENV_KEYS['model'], values.get('rw_image_model', 'gpt-image-2')),
        size=os.environ.get(ENV_KEYS['size'], values.get('rw_image_size', '1024x1024')),
        assets_dir=assets_dir or Path('assets'),
    )
    return cfg


def assets_relative(report_dir: Path, assets_dir: Path, filename: str) -> str:
    target = (assets_dir / filename).resolve()
    try:
        return target.relative_to(report_dir.resolve()).as_posix()
    except ValueError:
        return target.as_posix()


def resolve_local_path(report_dir: Path, src: str) -> Path:
    path = Path(src)
    if path.is_absolute():
        return path
    return (report_dir / src).resolve()


def list_markdown_image_paths(md_text: str) -> list[str]:
    paths: list[str] = []
    for _, src in MD_IMAGE.findall(md_text):
        src = src.strip()
        if src.startswith(('http://', 'https://', 'data:')):
            continue
        paths.append(src)
    return paths


def pending_generations(specs: list[ImageSpec], assets_dir: Path) -> list[ImageSpec]:
    pending: list[ImageSpec] = []
    for spec in specs:
        if spec.mode != 'generate':
            continue
        if not spec.output_path(assets_dir).exists():
            pending.append(spec)
    return pending


def confirm_generation(specs: list[ImageSpec], config: ImageConfig, *, yes: bool) -> bool:
    if not specs:
        return True
    print('The following AI images will be generated:')
    print(f'  API: {config.api_url}')
    print(f'  Model: {config.model}')
    for spec in specs:
        prompt_preview = spec.prompt.replace('\n', ' ')
        if len(prompt_preview) > 100:
            prompt_preview = prompt_preview[:100] + '...'
        print(f'  - [{spec.id}] {prompt_preview}')
    if yes:
        return True
    if not sys.stdin.isatty():
        print('Non-interactive session: pass --yes to approve image generation.', file=sys.stderr)
        return False
    answer = input('Proceed with image generation? [y/N]: ').strip().lower()
    return answer in ('y', 'yes')


def generate_image_file(config: ImageConfig, spec: ImageSpec, out_path: Path) -> None:
    import requests

    headers = {
        'Authorization': f'Bearer {config.api_key}',
        'Content-Type': 'application/json',
    }
    payload: dict[str, Any] = {
        'model': config.model,
        'prompt': spec.prompt,
        'size': spec.size or config.size,
        'n': 1,
    }
    resp = requests.post(config.api_url, headers=headers, json=payload, timeout=180)
    resp.raise_for_status()
    data = resp.json()
    items = data.get('data') or []
    if not items:
        raise RuntimeError(f'Image API returned no data: {data}')
    item = items[0]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if item.get('b64_json'):
        out_path.write_bytes(base64.b64decode(item['b64_json']))
    elif item.get('url'):
        img_resp = requests.get(item['url'], timeout=120)
        img_resp.raise_for_status()
        out_path.write_bytes(img_resp.content)
    else:
        raise RuntimeError(f'Image API response missing b64_json/url: {item}')


def materialize_images(
    md_text: str,
    report_dir: Path,
    config: ImageConfig,
    *,
    generate: bool = False,
    yes: bool = False,
) -> tuple[str, list[str]]:
    report_dir = report_dir.resolve()
    assets_dir = (report_dir / config.assets_dir).resolve()
    assets_dir.mkdir(parents=True, exist_ok=True)
    messages: list[str] = []
    specs = parse_rw_image_directives(md_text)
    to_generate = pending_generations(specs, assets_dir)

    if to_generate:
        if not generate:
            ids = ', '.join(s.id for s in to_generate)
            messages.append(f'pending AI images not generated: {ids}')
        elif not config.ready:
            raise RuntimeError(
                'Image generation requested but RW_IMAGE_API_URL / RW_IMAGE_API_KEY are missing. '
                'Create image.env from templates/image.env.example or pass env vars.'
            )
        elif not confirm_generation(to_generate, config, yes=yes):
            raise RuntimeError('Image generation cancelled by user.')
        else:
            for spec in to_generate:
                out_path = spec.output_path(assets_dir)
                generate_image_file(config, spec, out_path)
                messages.append(f'generated: {out_path}')

    resolved = md_text
    for spec in specs:
        if spec.mode == 'local':
            src_path = resolve_local_path(report_dir, spec.src)
            if not src_path.exists():
                raise FileNotFoundError(f'Local image not found for [{spec.id}]: {src_path}')
            rel = assets_relative(report_dir, assets_dir, src_path.name)
            if src_path.resolve() != spec.output_path(assets_dir).resolve():
                target = spec.output_path(assets_dir)
                if not target.exists():
                    target.write_bytes(src_path.read_bytes())
                rel = assets_relative(report_dir, assets_dir, target.name)
        elif spec.mode == 'generate':
            out_path = spec.output_path(assets_dir)
            if not out_path.exists():
                continue
            rel = assets_relative(report_dir, assets_dir, out_path.name)
        else:
            raise ValueError(f'Unsupported rw-image mode [{spec.id}]: {spec.mode}')

        alt = spec.alt or spec.id
        replacement = f'![{alt}]({rel})'
        resolved = resolved.replace(spec.marker, replacement, 1)

    return resolved, messages


def validate_images(md_text: str, report_dir: Path, assets_dir: Path | None = None) -> list[str]:
    warnings: list[str] = []
    assets = (report_dir / (assets_dir or Path('assets'))).resolve()
    for spec in parse_rw_image_directives(md_text):
        if spec.mode == 'generate' and not spec.output_path(assets).exists():
            warnings.append(f'pending AI image [{spec.id}] — run --stage images before PDF')
        if spec.mode == 'local':
            src = resolve_local_path(report_dir, spec.src)
            if not src.exists():
                warnings.append(f'missing local image [{spec.id}]: {src}')
    for src in list_markdown_image_paths(md_text):
        path = resolve_local_path(report_dir, src)
        if not path.exists():
            warnings.append(f'missing markdown image: {src}')
    return warnings


def embed_images_in_html(html: str, base_dir: Path) -> str:
    base_dir = base_dir.resolve()

    def repl(match: re.Match[str]) -> str:
        before, src, after = match.group(1), match.group(2), match.group(3)
        if src.startswith(('data:', 'http://', 'https://')):
            return match.group(0)
        path = resolve_local_path(base_dir, src)
        if not path.exists():
            return match.group(0)
        mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        encoded = base64.b64encode(path.read_bytes()).decode('ascii')
        return f'<img{before}src="data:{mime};base64,{encoded}"{after}>'

    return IMG_TAG.sub(repl, html)


def image_fingerprint(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]
