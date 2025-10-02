#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目总体进展文档自动更新脚本
扫描所有功能分支，生成markmap格式的总体进展报告
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path
import subprocess

def get_repo_root():
    """获取Git仓库根目录"""
    try:
        result = subprocess.run(['git', 'rev-parse', '--show-toplevel'],
                              capture_output=True, text=True, check=True)
        return Path(result.stdout.strip())
    except subprocess.CalledProcessError:
        print("错误: 不在Git仓库中")
        sys.exit(1)

def get_current_branch():
    """获取当前分支"""
    try:
        result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "main"

def analyze_feature_status(feature_dir):
    """分析功能状态"""
    spec_file = feature_dir / 'spec.md'
    plan_file = feature_dir / 'plan.md'
    tasks_file = feature_dir / 'tasks.md'

    status = {
        'name': feature_dir.name,
        'has_spec': spec_file.exists(),
        'has_plan': plan_file.exists(),
        'has_tasks': tasks_file.exists(),
        'completed_phases': 0,
        'total_tasks': 0,
        'completed_tasks': 0,
        'current_phase': '规划阶段'
    }

    # 分析plan.md的进度
    if plan_file.exists():
        content = plan_file.read_text(encoding='utf-8')
        completed_matches = re.findall(r'- \[x\] (Phase \d+[^:]*)', content)
        status['completed_phases'] = len(completed_matches)

        if completed_matches:
            status['current_phase'] = completed_matches[-1]

    # 分析tasks.md的进度
    if tasks_file.exists():
        content = tasks_file.read_text(encoding='utf-8')
        all_tasks = re.findall(r'- \[([ x])\] \*\*(T\d+)\*\*', content)
        status['total_tasks'] = len(all_tasks)
        status['completed_tasks'] = len([t for t in all_tasks if t[0] == 'x'])

    return status

def generate_feature_summary(features, title):
    """生成功能摘要"""
    if not features:
        return f"- 暂无{title}"

    result = []
    for feature in features:
        progress = 0
        if feature['total_tasks'] > 0:
            progress = round((feature['completed_tasks'] / feature['total_tasks']) * 100)

        line = f"### {feature['name']}"
        if feature['total_tasks'] > 0:
            line += f" ({progress}%)"

        result.append(line)
        result.append(f"- **当前阶段**: {feature['current_phase']}")
        result.append(f"- **已完成阶段**: {feature['completed_phases']}")

        if feature['total_tasks'] > 0:
            result.append(f"- **任务进度**: {feature['completed_tasks']}/{feature['total_tasks']}")

        # 添加文档链接
        docs = []
        if feature['has_spec']:
            docs.append(f"[规格](specs/{feature['name']}/spec.md)")
        if feature['has_plan']:
            docs.append(f"[计划](specs/{feature['name']}/plan.md)")
        if feature['has_tasks']:
            docs.append(f"[任务](specs/{feature['name']}/tasks.md)")

        if docs:
            result.append(f"- **文档**: {' | '.join(docs)}")

        result.append("")

    return '\n'.join(result)

def generate_file_index(all_features):
    """生成文件索引"""
    planning = []
    design = []
    contracts = []
    config = []

    for feature in all_features:
        base_path = f"specs/{feature['name']}"

        if feature['has_spec']:
            planning.append(f"- [项目规格]({base_path}/spec.md)")
        if feature['has_plan']:
            planning.append(f"- [实施计划]({base_path}/plan.md)")

        # 检查设计文档
        feature_dir = Path(f"specs/{feature['name']}")
        design_files = ['research.md', 'data-model.md', 'quickstart.md']
        for file in design_files:
            file_path = feature_dir / file
            if file_path.exists():
                name = file.replace('.md', '').replace('-', ' ')
                design.append(f"- [{name}]({base_path}/{file})")

        # 检查API合约
        contracts_dir = feature_dir / 'contracts'
        if contracts_dir.exists():
            for contract_file in contracts_dir.glob('*.yaml'):
                name = contract_file.stem.replace('_', ' ')
                contracts.append(f"- [{name}]({base_path}/contracts/{contract_file.name})")

    # 检查配置文件
    config_files = ['pyproject.toml', 'pytest.ini', '.pre-commit-config.yaml']
    for file in config_files:
        if Path(file).exists():
            config.append(f"- [{file}]({file})")

    return {
        'planning': '\n'.join(planning) if planning else '- 暂无规划文档',
        'design': '\n'.join(design) if design else '- 暂无设计文档',
        'contracts': '\n'.join(contracts) if contracts else '- 暂无API合约',
        'config': '\n'.join(config) if config else '- 暂无配置文件'
    }

def main():
    repo_root = get_repo_root()
    os.chdir(repo_root)

    progress_file = repo_root / '进展.md'
    template_file = repo_root / '.specify' / 'templates' / 'progress-template.md'
    specs_dir = repo_root / 'specs'

    print("=== 更新项目总体进展文档 ===")

    if not template_file.exists():
        print(f"错误: 模板文件不存在: {template_file}")
        sys.exit(1)

    if not specs_dir.exists():
        print("specs目录不存在，创建基础进展文档")
        content = template_file.read_text(encoding='utf-8')
        content = content.replace('[PROJECT_NAME]', repo_root.name)
        content = content.replace('[TIMESTAMP]', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        progress_file.write_text(content, encoding='utf-8')
        return

    # 扫描所有功能目录
    feature_dirs = [d for d in specs_dir.iterdir() if d.is_dir() and d.name[0].isdigit()]
    all_features = [analyze_feature_status(d) for d in feature_dirs]

    # 分类功能
    active_features = [f for f in all_features if f['has_plan'] and f['completed_phases'] > 0]
    completed_features = [f for f in all_features if f['total_tasks'] > 0 and f['completed_tasks'] == f['total_tasks']]

    # 生成文件索引
    file_index = generate_file_index(all_features)

    # 读取模板并替换变量
    content = template_file.read_text(encoding='utf-8')
    content = content.replace('[PROJECT_NAME]', '量化交易系统V3')
    content = content.replace('[ARCHITECTURE_TYPE]', '四层存储(HOT<1ms/WARM<100ms/COOL<500ms/COLD<2s)')
    content = content.replace('[CONCURRENCY_TARGET]', '1000+策略同时执行')
    content = content.replace('[QUALITY_STANDARDS]', 'TDD流程+95%测试覆盖率')
    content = content.replace('[TECH_STACK]', 'Python3.11+FastAPI+Pydantic')

    content = content.replace('[ACTIVE_FEATURES]', generate_feature_summary(active_features, "活跃功能"))
    content = content.replace('[COMPLETED_FEATURES]', generate_feature_summary(completed_features, "已完成功能"))

    # 整体统计
    total_phases = sum(f['completed_phases'] for f in all_features)
    completed_phases_text = f"- {total_phases} 个阶段已完成" if total_phases > 0 else "- 暂无已完成阶段"

    current_work_text = '\n'.join([f"- {f['name']}: {f['current_phase']}" for f in active_features[:3]]) if active_features else "- 当前无活跃工作"

    pending_count = len(all_features) - len(active_features) - len(completed_features)
    pending_work_text = f"- {pending_count} 个功能等待开始" if pending_count > 0 else "- 暂无待完成工作"

    content = content.replace('[COMPLETED_PHASES]', completed_phases_text)
    content = content.replace('[CURRENT_WORK]', current_work_text)
    content = content.replace('[PENDING_WORK]', pending_work_text)

    content = content.replace('[PLANNING_DOCS]', file_index['planning'])
    content = content.replace('[DESIGN_DOCS]', file_index['design'])
    content = content.replace('[API_CONTRACTS]', file_index['contracts'])
    content = content.replace('[CONFIG_FILES]', file_index['config'])

    content = content.replace('[TIMESTAMP]', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # 写入文件
    progress_file.write_text(content, encoding='utf-8')

    print(f"✅ 总体进展文档已更新: {progress_file}")
    print()
    print("统计信息:")
    print(f"- 总功能数: {len(all_features)}")
    print(f"- 活跃功能: {len(active_features)}")
    print(f"- 已完成功能: {len(completed_features)}")
    print(f"- 已完成阶段: {total_phases}")

if __name__ == '__main__':
    main()