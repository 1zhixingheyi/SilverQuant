#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
量化交易系统V3 进展更新工具 - Python版本
提供交互式菜单，支持分支选择和进展更新
"""

import os
import sys
import subprocess
from pathlib import Path

# 确保脚本从项目根目录运行
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent.parent
os.chdir(project_root)

def clear_screen():
    """清屏"""
    os.system('cls' if os.name == 'nt' else 'clear')

def show_header():
    """显示标题"""
    print("=" * 50)
    print("    量化交易系统V3 进展更新工具")
    print("=" * 50)
    print()

def get_available_branches():
    """获取可用的功能分支"""
    specs_dir = Path('specs')
    if not specs_dir.exists():
        return []

    branches = []
    for item in specs_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            branches.append(item.name)

    return sorted(branches)

def run_command(cmd):
    """运行命令并返回是否成功"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
        print(result.stdout)
        if result.stderr:
            print(f"警告: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"执行命令时出错: {e}")
        return False

def select_branch():
    """分支选择菜单"""
    branches = get_available_branches()
    if not branches:
        print("❌ 未找到可用的功能分支")
        return None

    print("📋 可用的功能分支:")
    for i, branch in enumerate(branches, 1):
        print(f"  {i}. {branch}")
    print()

    try:
        choice = input("请选择分支 (输入数字): ").strip()
        if choice.isdigit():
            index = int(choice) - 1
            if 0 <= index < len(branches):
                return branches[index]
        print("❌ 无效选择")
        return None
    except (EOFError, KeyboardInterrupt):
        return None

def update_current_branch():
    """更新当前分支功能进展"""
    print("🔄 正在更新当前分支功能进展...")
    success = run_command('python ".specify/scripts/python/update_feature_progress.py"')
    if success:
        print("✅ 更新完成")
    else:
        print("❌ 更新失败")

    try:
        input("\n按回车键继续...")
    except (EOFError, KeyboardInterrupt):
        pass

def update_specific_branch():
    """更新指定分支功能进展"""
    branch = select_branch()
    if not branch:
        return

    print(f"🔄 正在更新分支 {branch} 的功能进展...")
    cmd = f'python ".specify/scripts/python/update_feature_progress.py" -f "{branch}"'
    success = run_command(cmd)
    if success:
        print("✅ 更新完成")
    else:
        print("❌ 更新失败")

    try:
        input("\n按回车键继续...")
    except (EOFError, KeyboardInterrupt):
        pass

def update_all_branches():
    """更新所有功能分支进展"""
    print("🔄 正在更新所有功能分支进展...")
    success = run_command('python ".specify/scripts/python/update_feature_progress.py" -a')
    if success:
        print("✅ 更新完成")
    else:
        print("❌ 更新失败")

    try:
        input("\n按回车键继续...")
    except (EOFError, KeyboardInterrupt):
        pass

def update_overall():
    """更新项目总体进展"""
    print("🔄 正在更新项目总体进展...")

    # 检查Python脚本是否存在
    python_script = Path('.specify/scripts/python/update_progress.py')

    if python_script.exists():
        # 使用Python版本
        success = run_command('python ".specify/scripts/python/update_progress.py"')
    else:
        print("❌ 找不到进展更新脚本")
        success = False

    if success:
        print("✅ 更新完成")
    else:
        print("❌ 更新失败")

    try:
        input("\n按回车键继续...")
    except (EOFError, KeyboardInterrupt):
        pass

def show_summary():
    """显示当前进展摘要"""
    print("📊 当前进展摘要")
    print("-" * 30)

    branches = get_available_branches()
    if not branches:
        print("❌ 未找到功能分支")
        return

    print(f"📈 总功能分支数: {len(branches)}")
    print("\n📋 功能分支列表:")
    for branch in branches:
        print(f"  • {branch}")

    print(f"\n💡 使用说明:")
    print("  python .specify/scripts/python/update_feature_progress.py -a")
    print("  python .specify/scripts/python/update_feature_progress.py -f [分支名]")

    try:
        input("\n按回车键继续...")
    except (EOFError, KeyboardInterrupt):
        pass

def show_menu():
    """显示主菜单"""
    clear_screen()
    show_header()

    print("请选择操作:")
    print("1. 更新当前分支功能进展")
    print("2. 更新指定分支功能进展")
    print("3. 更新所有功能分支进展")
    print("4. 更新项目总体进展")
    print("5. 查看当前进展摘要")
    print("6. 退出")
    print()

def main():
    """主函数"""
    while True:
        show_menu()

        try:
            choice = input("请输入选择 (1-6): ").strip()

            if choice == '1':
                update_current_branch()
            elif choice == '2':
                update_specific_branch()
            elif choice == '3':
                update_all_branches()
            elif choice == '4':
                update_overall()
            elif choice == '5':
                show_summary()
            elif choice == '6':
                clear_screen()
                print("\n👋 感谢使用进展更新工具！")
                print()
                break
            else:
                print("❌ 无效选择，请重新输入")
                try:
                    input("\n按回车键继续...")
                except (EOFError, KeyboardInterrupt):
                    break

        except KeyboardInterrupt:
            clear_screen()
            print("\n👋 用户取消，退出程序")
            break
        except Exception as e:
            print(f"\n❌ 程序出错: {e}")
            try:
                input("按回车键继续...")
            except (EOFError, KeyboardInterrupt):
                break

if __name__ == '__main__':
    main()