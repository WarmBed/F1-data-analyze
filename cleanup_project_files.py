#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
F1T 專案清理工具
自動整理專案檔案：
- 移動測試檔案到 tests/ 資料夾
- 移動不需要的檔案到 刪除資料夾/
- 保留核心程式和配置檔案

建立日期: 2025-10-19
版本: v1.1 - 修正自我保護機制
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
import re
import sys

# ANSI 顏色碼
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_color(message, color=Colors.RESET):
    """彩色輸出"""
    print(f"{color}{message}{Colors.RESET}")

def print_header():
    """顯示標題"""
    print_color("=" * 50, Colors.YELLOW)
    print_color("  F1T 專案清理工具 v1.1", Colors.YELLOW)
    print_color("=" * 50, Colors.YELLOW)
    print()

def get_script_name():
    """取得當前腳本的檔名"""
    return Path(__file__).name

def main():
    """主要清理邏輯"""
    print_header()
    
    # 確認當前目錄
    current_dir = Path.cwd()
    script_name = get_script_name()
    
    print_color(f"當前目錄: {current_dir}", Colors.CYAN)
    print_color(f"腳本名稱: {script_name} (自動忽略)", Colors.CYAN)
    print()
    
    # 建立目標資料夾
    delete_folder = Path("刪除資料夾")
    tests_folder = Path("tests")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    delete_folder_with_time = delete_folder / f"cleanup_{timestamp}"
    
    # 建立資料夾
    delete_folder_with_time.mkdir(parents=True, exist_ok=True)
    tests_folder.mkdir(exist_ok=True)
    
    print_color(f"✓ 已建立資料夾: {delete_folder_with_time}", Colors.GREEN)
    print_color(f"✓ 已建立資料夾: {tests_folder}", Colors.GREEN)
    print()
    
    # 🔒 核心保留檔案清單（使用者指定）
    keep_files = {
        "f1t_gui_main.py",
        "f1_analysis_modular_main.py",
        "refactored_api.py",
        "start_gui.bat",
        "start_api.bat",
        "requirements.txt",
        "README.md",
        "F1T_GUI.spec",
        script_name,  # 🔒 自動保護：忽略腳本本身
        "cleanup_project_files.ps1"  # 保留 PS1 腳本
    }
    
    # 測試相關檔案的正則表達式
    test_patterns = [
        r'^test_',
        r'^check_',
        r'^debug_',
        r'^diagnose_',
        r'^compare_',
        r'^demo_',
        r'^capture_',
        r'[Tt][Ee][Ss][Tt]',
        r'_test\.(py|txt)$'
    ]
    
    print_color("掃描專案根目錄檔案...", Colors.CYAN)
    print()
    
    # 處理計數器
    stats = {
        'kept': 0,
        'moved_to_tests': 0,
        'moved_to_delete': 0,
        'skipped': 0
    }
    
    # 獲取所有符合條件的檔案（僅掃描根目錄）
    extensions = {'.py', '.bat', '.md', '.txt'}
    all_files = [f for f in current_dir.iterdir() 
                 if f.is_file() and f.suffix in extensions]
    
    print_color(f"找到 {len(all_files)} 個檔案待處理", Colors.YELLOW)
    print()
    
    # 處理每個檔案
    for file_path in sorted(all_files):
        file_name = file_path.name
        
        # 🔒 自我保護：絕對不移動腳本本身
        if file_name == script_name:
            print_color(f"  🔒 自我保護: {file_name} (不移動)", Colors.BOLD + Colors.GREEN)
            stats['kept'] += 1
            continue
        
        # 檢查是否為保留檔案
        if file_name in keep_files:
            print_color(f"  ✓ 保留: {file_name}", Colors.GREEN)
            stats['kept'] += 1
            continue
        
        # 檢查是否為測試相關檔案
        is_test_file = any(re.search(pattern, file_name) for pattern in test_patterns)
        
        if is_test_file:
            dest_path = tests_folder / file_name
            if dest_path.exists():
                print_color(f"  ⚠ 已存在於 tests/: {file_name} (跳過)", Colors.YELLOW)
                stats['skipped'] += 1
            else:
                try:
                    shutil.move(str(file_path), str(dest_path))
                    print_color(f"  → 移至 tests/: {file_name}", Colors.CYAN)
                    stats['moved_to_tests'] += 1
                except Exception as e:
                    print_color(f"  ✗ 移動失敗: {file_name} - {e}", Colors.RED)
            continue
        
        # 其他檔案移到刪除資料夾
        dest_path = delete_folder_with_time / file_name
        try:
            shutil.move(str(file_path), str(dest_path))
            print_color(f"  ✗ 移至刪除資料夾: {file_name}", Colors.RED)
            stats['moved_to_delete'] += 1
        except Exception as e:
            print_color(f"  ✗ 移動失敗: {file_name} - {e}", Colors.RED)
    
    # 顯示統計
    print()
    print_color("=" * 50, Colors.YELLOW)
    print_color("  清理完成統計", Colors.YELLOW)
    print_color("=" * 50, Colors.YELLOW)
    print_color(f"✓ 保留檔案: {stats['kept']}", Colors.GREEN)
    print_color(f"→ 移至 tests/: {stats['moved_to_tests']}", Colors.CYAN)
    print_color(f"✗ 移至刪除資料夾/: {stats['moved_to_delete']}", Colors.RED)
    print_color(f"⚠ 跳過（已存在）: {stats['skipped']}", Colors.YELLOW)
    print()
    
    # 顯示保留的核心檔案
    print_color("📋 核心保留檔案清單：", Colors.CYAN)
    for file_name in sorted(keep_files):
        if (current_dir / file_name).exists():
            print_color(f"  ✓ {file_name}", Colors.GREEN)
        else:
            print(f"  ✗ {file_name} (檔案不存在)")
    
    print()
    print_color("🎉 清理完成！", Colors.GREEN)
    print()
    
    # 詢問是否查看刪除資料夾內容
    try:
        response = input("是否查看刪除資料夾內容？(Y/N): ").strip().upper()
        if response == 'Y':
            print()
            print_color("📁 刪除資料夾內容：", Colors.CYAN)
            deleted_files = list(delete_folder_with_time.iterdir())
            for f in sorted(deleted_files):
                print(f"  - {f.name}")
            print()
            print_color(f"總計: {len(deleted_files)} 個檔案", Colors.CYAN)
    except (EOFError, KeyboardInterrupt):
        print()
    
    print()
    print_color(f"提示: 刪除的檔案位於 {delete_folder_with_time}", Colors.YELLOW)
    print_color("      如需復原，請手動從該資料夾移回", Colors.YELLOW)
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_color("\n使用者中斷執行", Colors.YELLOW)
    except Exception as e:
        print_color(f"\n執行錯誤: {e}", Colors.RED)
        import traceback
        traceback.print_exc()
