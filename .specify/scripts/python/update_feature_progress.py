#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
功能分支进展文档自动更新脚本
用于生成每个功能分支的详细进展报告
"""

import os
import re
import sys
import argparse
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

def analyze_plan_progress(plan_file):
    """分析plan.md的进度"""
    if not plan_file.exists():
        return [], "规划阶段"

    content = plan_file.read_text(encoding='utf-8')

    # 提取已完成阶段
    completed_phases = []
    phase_pattern = r'- \[x\] (Phase \d+[^:]*): ([^\n]+)'
    matches = re.findall(phase_pattern, content)

    for phase_name, phase_desc in matches:
        completed_phases.append(f"- **{phase_name}**: {phase_desc}")

    # 当前阶段是最后完成的阶段
    current_phase = matches[-1][0] if matches else "规划阶段"

    return completed_phases, current_phase

def analyze_current_phase(plan_file, total_tasks, completed_tasks):
    """基于任务完成情况智能分析当前实际阶段"""
    completed_phases, plan_phase = analyze_plan_progress(plan_file)

    # 基于任务完成情况判断实际阶段
    if completed_tasks >= 8:  # T001-T008 Setup阶段已完成
        if completed_tasks < 20:  # 合约测试阶段
            return "Phase 3.2: 合约测试阶段 (TDD第一步)"
        elif completed_tasks < 44:  # 数据模型测试
            return "Phase 3.3: 数据模型测试 (TDD第二步)"
        elif completed_tasks < 72:  # 集成测试
            return "Phase 3.4: 集成测试 (TDD第三步)"
        elif completed_tasks < 96:  # API实现阶段
            return "Phase 3.6: API实现阶段"
        elif completed_tasks >= 96:  # 存储集成及后续
            return "Phase 3.7+: 高级实现阶段"
    else:
        return plan_phase

def analyze_tasks_progress(tasks_file):
    """分析tasks.md的任务进度 - 智能显示策略，适应不同项目规模"""
    if not tasks_file.exists():
        return 0, 0, [], [], []

    content = tasks_file.read_text(encoding='utf-8')

    # 修复的正则表达式 - 更准确匹配任务格式，支持大小写X
    task_pattern = r'- \[([ xX])\] \*\*(T\d+)\*\* (?:\[P\] )?(.+?)(?=\n- |\n\n|\n$|$)'
    matches = re.findall(task_pattern, content, re.MULTILINE | re.DOTALL)

    total_tasks = len(matches)
    completed_tasks = 0
    recent_completed = []
    active_tasks = []
    pending_tasks = []

    # 智能显示策略：根据项目规模调整显示数量
    if total_tasks <= 50:
        # 小型项目：显示全部任务
        max_completed = total_tasks
        max_active = total_tasks
        max_pending = total_tasks
    elif total_tasks <= 150:
        # 中型项目：显示较多任务，确保重要信息不丢失
        max_completed = min(20, total_tasks)
        max_active = min(15, total_tasks)
        max_pending = min(15, total_tasks)
    else:
        # 大型项目：显示重点任务，关注最新状态
        max_completed = min(25, total_tasks)
        max_active = min(20, total_tasks)
        max_pending = min(20, total_tasks)

    for status, task_id, task_desc in matches:
        task_desc = task_desc.strip().replace('\n', ' ')  # 处理多行描述
        if status.lower() == 'x':
            completed_tasks += 1
            if len(recent_completed) < max_completed:
                recent_completed.append(f"- **{task_id}**: {task_desc}")
        else:
            # 扩展关键词匹配，提高分类准确性
            active_keywords = ['实现', '创建', '配置', '编写', '测试', '合约测试', '单元测试', '集成测试', '性能测试', 'API', 'api']
            if any(keyword in task_desc.lower() for keyword in active_keywords):
                if len(active_tasks) < max_active:
                    active_tasks.append(f"- **{task_id}**: {task_desc}")
            else:
                if len(pending_tasks) < max_pending:
                    pending_tasks.append(f"- **{task_id}**: {task_desc}")

    return total_tasks, completed_tasks, recent_completed, active_tasks, pending_tasks

def get_design_files(feature_dir, feature_name):
    """获取设计文档列表"""
    design_files = []

    # Spec Kit 原生支持的文档
    native_docs = ['plan.md', 'spec.md', 'research.md', 'data-model.md', 'quickstart.md']

    for doc in native_docs:
        doc_path = feature_dir / doc
        if doc_path.exists():
            design_files.append(f"- [{doc}](specs/{feature_name}/{doc})")

    # 检查API合约
    contracts_dir = feature_dir / 'contracts'
    if contracts_dir.exists():
        for contract_file in contracts_dir.glob('*.yaml'):
            name = contract_file.stem.replace('_', ' ')
            design_files.append(f"- [合约: {name}](specs/{feature_name}/contracts/{contract_file.name})")

    # 检查补充技术文档 (supplements 目录)
    supplements_dir = feature_dir / 'supplements'
    if supplements_dir.exists():
        design_files.append("")  # 添加空行分隔
        design_files.append("**补充技术文档**:")

        # 优先显示架构相关文档
        priority_supplements = [
            ('architecture.md', '系统架构'),
            ('storage_design.md', '存储设计'),
            ('data_adapters_design.md', '数据适配器'),
            ('event_driven_design.md', '事件驱动')
        ]

        for doc_name, display_name in priority_supplements:
            doc_path = supplements_dir / doc_name
            if doc_path.exists():
                design_files.append(f"- [{display_name}](specs/{feature_name}/supplements/{doc_name})")

        # 添加其他补充文档
        for supplement_file in supplements_dir.glob('*.md'):
            if supplement_file.name not in [doc[0] for doc in priority_supplements] and supplement_file.name != 'README.md':
                name = supplement_file.stem.replace('_', ' ').title()
                design_files.append(f"- [{name}](specs/{feature_name}/supplements/{supplement_file.name})")

    return design_files

def generate_next_commands(feature_name, current_phase, completed_phases, total_tasks, completed_tasks, feature_dir):
    """根据当前阶段生成下一步操作建议"""
    commands = []

    # 检查文件存在状态
    has_spec = (feature_dir / 'spec.md').exists()
    has_plan = (feature_dir / 'plan.md').exists()
    has_tasks = (feature_dir / 'tasks.md').exists()
    has_research = (feature_dir / 'research.md').exists()
    has_data_model = (feature_dir / 'data-model.md').exists()

    # 基于当前阶段生成建议
    if current_phase == "规划阶段" or not has_spec:
        commands.extend([
            "📝 **当前需要**: 创建功能规格文档",
            "```bash",
            "# 1. 确保在正确的分支",
            f"git checkout {feature_name}",
            "",
            "# 2. 创建基础规格文档",
            f"# 编辑 specs/{feature_name}/spec.md",
            "",
            "# 3. 开始规划流程",
            "/plan",
            "```"
        ])

    elif "Phase 0" in current_phase or not has_research:
        commands.extend([
            "🔍 **当前需要**: 完成技术研究",
            "```bash",
            "# 继续执行规划命令完成研究阶段",
            "/plan",
            "",
            "# 或手动创建研究文档",
            f"# 编辑 specs/{feature_name}/research.md",
            "```"
        ])

    elif "Phase 1" in current_phase or not has_data_model:
        commands.extend([
            "🏗️ **当前需要**: 完成设计和合约",
            "```bash",
            "# 完成设计阶段 (生成 data-model.md, contracts/, quickstart.md)",
            "/plan",
            "",
            "# 验证设计完整性",
            f"ls specs/{feature_name}/contracts/",
            "```"
        ])

    elif "Phase 2" in current_phase or not has_tasks:
        commands.extend([
            "📋 **当前需要**: 生成执行任务清单",
            "```bash",
            "# 生成详细任务清单",
            "/tasks",
            "",
            "# 检查生成的任务",
            f"head -20 specs/{feature_name}/tasks.md",
            "```"
        ])

    elif total_tasks > 0 and completed_tasks < total_tasks:
        # 计算完成百分比
        progress = round((completed_tasks / total_tasks) * 100)
        remaining = total_tasks - completed_tasks

        commands.extend([
            f"⚡ **当前需要**: 执行实施任务 ({progress}% 完成，还有 {remaining} 个任务)",
            "```bash",
            "# 查看下一个待执行任务",
            f"grep -A5 '\\[ \\]' specs/{feature_name}/tasks.md | head -10",
            "",
            "# 执行具体任务 (示例)",
            "# /exec T001  # 替换为实际任务ID",
            "",
            "# 标记任务完成后更新进展",
            f"python .specify/scripts/python/update_feature_progress.py -f {feature_name}",
            "```"
        ])

        # 如果接近完成，提供额外建议
        if progress >= 80:
            commands.extend([
                "",
                "🎯 **即将完成**: 准备最终检查",
                "```bash",
                "# 运行测试验证",
                "# pytest tests/  # 根据项目配置调整",
                "",
                "# 检查代码质量",
                "# ruff check src/  # 根据项目配置调整",
                "",
                "# 准备提交",
                "git status",
                "```"
            ])

    elif total_tasks > 0 and completed_tasks == total_tasks:
        commands.extend([
            "🎉 **当前状态**: 所有任务已完成！",
            "```bash",
            "# 最终验证",
            f"head -5 specs/{feature_name}/quickstart.md",
            "",
            "# 运行完整测试套件",
            "# pytest tests/ --cov=src/",
            "",
            "# 提交完成的功能",
            f'git add . && git commit -m "feat: 完成 {feature_name} 功能实现"',
            "",
            "# 可选: 创建合并请求",
            "# git push -u origin {feature_name}",
            "```"
        ])

    else:
        commands.extend([
            "🤔 **当前状态**: 需要进一步分析",
            "```bash",
            "# 检查当前状态",
            f"ls -la specs/{feature_name}/",
            "",
            "# 更新进展分析",
            f"python .specify/scripts/python/update_feature_progress.py -f {feature_name}",
            "```"
        ])

    # 添加通用的状态检查命令
    commands.extend([
        "",
        "🔧 **随时可用的命令**:",
        "```bash",
        "# 更新进展文档",
        f"python .specify/scripts/python/update_feature_progress.py -f {feature_name}",
        "",
        "# 查看Git状态",
        "git status && git log --oneline -3",
        "",
        "# 更新代理上下文",
        ".specify/scripts/powershell/update-agent-context.ps1 claude",
        "```"
    ])

    return '\n'.join(commands)

def update_feature_progress(feature_name, repo_root):
    """更新指定功能的进展文档"""
    specs_dir = repo_root / 'specs'
    feature_dir = specs_dir / feature_name

    if not feature_dir.exists():
        print(f"警告: 功能目录不存在: {feature_dir}")
        return None

    print(f"正在更新功能: {feature_name}")

    # 文件路径
    spec_file = feature_dir / 'spec.md'
    plan_file = feature_dir / 'plan.md'
    tasks_file = feature_dir / 'tasks.md'
    progress_file = feature_dir / f"{feature_name}_进展.md"
    template_file = repo_root / '.specify' / 'templates' / 'feature-progress-template.md'

    if not template_file.exists():
        print(f"错误: 模板文件不存在: {template_file}")
        return None

    # 分析进度
    completed_phases, plan_phase = analyze_plan_progress(plan_file)
    total_tasks, completed_tasks, recent_completed, active_tasks, pending_tasks = analyze_tasks_progress(tasks_file)
    current_phase = analyze_current_phase(plan_file, total_tasks, completed_tasks)
    design_files = get_design_files(feature_dir, feature_name)

    # 生成下一步操作指令
    next_commands = generate_next_commands(feature_name, current_phase, completed_phases,
                                         total_tasks, completed_tasks, feature_dir)

    # 计算进度百分比
    progress = round((completed_tasks / total_tasks) * 100) if total_tasks > 0 else 0

    # 读取模板
    template_content = template_file.read_text(encoding='utf-8')

    # 替换模板变量
    content = template_content
    content = content.replace('[FEATURE_NAME]', feature_name)
    content = content.replace('[BRANCH_NAME]', feature_name)
    content = content.replace('[SPEC_LINK]', f"specs/{feature_name}/spec.md" if spec_file.exists() else "待创建")
    content = content.replace('[START_DATE]', datetime.now().strftime('%Y-%m-%d'))
    content = content.replace('[CURRENT_PHASE]', current_phase)

    # 阶段信息
    completed_text = '\n'.join(completed_phases) if completed_phases else '- 暂无已完成阶段'
    current_work_text = f"- 当前处于: {current_phase}"
    pending_text = '- 待完成阶段将根据计划文档更新'

    content = content.replace('[COMPLETED_PHASES]', completed_text)
    content = content.replace('[CURRENT_WORK]', current_work_text)
    content = content.replace('[PENDING_PHASES]', pending_text)

    # 下一步操作指令
    content = content.replace('[NEXT_COMMANDS]', next_commands)

    # 任务统计
    stats_text = f"""- **总任务数**: {total_tasks}
- **已完成**: {completed_tasks} ({progress}%)
- **待完成**: {total_tasks - completed_tasks}"""

    recent_text = '\n'.join(recent_completed) if recent_completed else '- 暂无已完成任务'

    # 任务分类显示
    active_text = '\n'.join(active_tasks) if active_tasks else '- 暂无进行中任务'
    pending_text = '\n'.join(pending_tasks) if pending_tasks else '- 暂无待开始任务'

    # 计算实际显示的任务数量（用于统计标题）
    displayed_completed = len(recent_completed)
    displayed_active = len(active_tasks)
    displayed_pending = len(pending_tasks)

    content = content.replace('[TASK_STATISTICS]', stats_text)
    content = content.replace('[RECENT_COMPLETED_TASKS]', recent_text)
    content = content.replace('[ACTIVE_TASKS]', active_text)
    content = content.replace('[PENDING_TASKS]', pending_text)

    # 添加任务数量统计到标题
    content = content.replace('[COMPLETED_COUNT]', str(displayed_completed))
    content = content.replace('[ACTIVE_COUNT]', str(displayed_active))
    content = content.replace('[PENDING_COUNT]', str(displayed_pending))

    # 文件信息
    design_text = '\n'.join(design_files) if design_files else '- 暂无设计文档'
    content = content.replace('[DESIGN_FILES]', design_text)
    content = content.replace('[TEST_FILES]', '- 测试文件检测待完善')
    content = content.replace('[IMPLEMENTATION_FILES]', '- 实现文件检测待完善')

    # 质量指标
    content = content.replace('[TEST_COVERAGE]', '- 测试覆盖率检测待实现')
    content = content.replace('[CODE_QUALITY]', '- 代码质量检测待实现')
    content = content.replace('[PERFORMANCE_METRICS]', '- 性能指标检测待实现')

    content = content.replace('[TIMESTAMP]', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    # 写入文件
    progress_file.write_text(content, encoding='utf-8')
    print(f"✅ 已更新: {progress_file}")

    return {
        'feature': feature_name,
        'progress': progress,
        'completed_tasks': completed_tasks,
        'total_tasks': total_tasks,
        'current_phase': current_phase
    }

def main():
    parser = argparse.ArgumentParser(description='更新功能分支进展文档')
    parser.add_argument('-f', '--feature', help='指定功能名称')
    parser.add_argument('-a', '--all', action='store_true', help='更新所有功能')

    args = parser.parse_args()

    repo_root = get_repo_root()
    specs_dir = repo_root / 'specs'

    if not specs_dir.exists():
        print(f"错误: specs目录不存在: {specs_dir}")
        sys.exit(1)

    print("=== 更新功能分支进展文档 ===")

    # 确定要处理的功能
    target_features = []

    if args.all:
        # 处理所有功能目录（以数字开头的目录）
        feature_dirs = [d for d in specs_dir.iterdir()
                       if d.is_dir() and re.match(r'^\d+', d.name)]
        target_features = [d.name for d in feature_dirs]
    elif args.feature:
        target_features = [args.feature]
    else:
        # 处理当前分支
        current_branch = get_current_branch()
        target_features = [current_branch]

    # 更新所有目标功能
    results = []
    for feature in target_features:
        result = update_feature_progress(feature, repo_root)
        if result:
            results.append(result)

    # 汇总报告
    print("\n=== 更新汇总 ===")
    for result in results:
        print(f"📊 {result['feature']}: {result['progress']}% "
              f"({result['completed_tasks']}/{result['total_tasks']}) - {result['current_phase']}")

    print("\n💡 使用方法:")
    print("  -f <name>  : 更新指定功能")
    print("  -a         : 更新所有功能")
    print("  无参数     : 更新当前分支功能")

if __name__ == '__main__':
    main()