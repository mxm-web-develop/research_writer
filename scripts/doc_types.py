#!/usr/bin/env python3
"""Document type registry for research_writer."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

FRONTMATTER = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
BRIEF_TYPE = re.compile(r'^\|\s*document_type\s*\|\s*(.+?)\s*\|', re.MULTILINE | re.IGNORECASE)
BRIEF_TYPE_ALT = re.compile(r'^document_type:\s*(.+)$', re.MULTILINE | re.IGNORECASE)


@dataclass(frozen=True)
class DocTypeSpec:
    id: str
    label: str
    required_sections: tuple[str, ...]
    ppt_default: bool = True
    min_sources: int = 5


DOC_TYPES: dict[str, DocTypeSpec] = {
    'research-report': DocTypeSpec(
        'research-report',
        '调研报告',
        (
            'Executive Summary',
            'Background and Context',
            'Problem Definition',
            'Deep Analysis',
            'Comparison / Alternatives',
            'Risks and Constraints',
            'Recommendations / Conclusion',
            'References',
        ),
    ),
    'product-manual': DocTypeSpec(
        'product-manual',
        '产品说明书',
        (
            '读者与目标',
            '功能概览',
            '使用方式',
            '架构与实现',
            '边界与限制',
            'References',
        ),
        min_sources=3,
    ),
    'tech-proposal': DocTypeSpec(
        'tech-proposal',
        '技术方案',
        (
            '背景与目标',
            '方案对比',
            '推荐方案',
            '架构设计',
            '实施计划',
            '风险与约束',
            'References',
        ),
    ),
    'prd': DocTypeSpec(
        'prd',
        'PRD',
        (
            '问题与背景',
            '用户与场景',
            '需求说明',
            '流程与交互',
            '验收标准',
            '里程碑',
            'References',
        ),
    ),
    'whitepaper': DocTypeSpec(
        'whitepaper',
        '白皮书',
        (
            'Executive Summary',
            '行业背景',
            '方法论',
            '案例与证据',
            '结论与展望',
            'References',
        ),
    ),
    'competitive-analysis': DocTypeSpec(
        'competitive-analysis',
        '竞品分析',
        (
            '分析范围',
            '对比维度',
            '竞品逐一分析',
            'SWOT 汇总',
            '建议',
            'References',
        ),
    ),
    'tech-tutorial': DocTypeSpec(
        'tech-tutorial',
        '技术教程',
        (
            '前置条件',
            '目标与成果',
            '步骤说明',
            '示例',
            '常见问题',
            'References',
        ),
        min_sources=3,
    ),
    'press-release': DocTypeSpec(
        'press-release',
        '新闻稿',
        (
            '标题',
            '导语',
            '主体',
            '引语',
            '关于我们',
        ),
        ppt_default=False,
        min_sources=2,
    ),
    'spoken-script': DocTypeSpec(
        'spoken-script',
        '口播稿',
        (
            '开场',
            '主体段落',
            '结尾与 CTA',
            '画面/配图提示',
        ),
        ppt_default=False,
        min_sources=2,
    ),
    'social-narrative': DocTypeSpec(
        'social-narrative',
        '自媒体叙事稿',
        (
            '钩子',
            '叙事主线',
            '金句',
            '行动号召',
            '平台适配说明',
        ),
        ppt_default=False,
        min_sources=2,
    ),
}

DEFAULT_DOC_TYPE = 'research-report'


def skill_doc_types_dir() -> Path:
    return Path(__file__).resolve().parent.parent / 'references' / 'document-types'


def get_doc_type(type_id: str | None) -> DocTypeSpec:
    if type_id and type_id in DOC_TYPES:
        return DOC_TYPES[type_id]
    return DOC_TYPES[DEFAULT_DOC_TYPE]


def parse_document_type(text: str) -> str | None:
    fm = FRONTMATTER.match(text)
    if fm:
        for line in fm.group(1).splitlines():
            if line.strip().lower().startswith('document_type:'):
                return line.split(':', 1)[1].strip()
    m = BRIEF_TYPE.search(text)
    if m:
        return m.group(1).strip().strip('`')
    m = BRIEF_TYPE_ALT.search(text)
    if m:
        return m.group(1).strip()
    return None


def resolve_document_type(report_path: Path, brief_path: Path | None = None) -> DocTypeSpec:
    for path in (brief_path, report_path):
        if path and path.exists():
            doc_id = parse_document_type(path.read_text(encoding='utf-8'))
            if doc_id:
                return get_doc_type(doc_id)
    return get_doc_type(None)


def list_doc_type_ids() -> list[str]:
    return list(DOC_TYPES.keys())
