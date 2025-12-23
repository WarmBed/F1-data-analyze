#!/usr/bin/env python3
"""F1T 日誌查看器工具

功能:
- 查看今天的日誌檔案
- 過濾特定等級的日誌（ERROR/WARNING/INFO）
- 即時監控日誌（類似 tail -f）
- 搜尋特定關鍵字
"""

import sys
import os
import time
from pathlib import Path
from datetime import datetime
import argparse

def print_header(title: str):
    """列印標題"""
    print("\n" + "="*80)
    print(f"📋 {title}")
    print("="*80 + "\n")

def get_log_file(component: str = "gui", error_only: bool = False) -> Path:
    """取得今天的日誌檔案路徑"""
    today = datetime.now().strftime("%Y-%m-%d")
    log_dir = Path("logs")
    
    if error_only:
        log_file = log_dir / f"f1_{component}_error_{today}.log"
    else:
        log_file = log_dir / f"f1_{component}_{today}.log"
    
    return log_file

def read_log_file(log_file: Path, lines: int = None, level: str = None, keyword: str = None):
    """讀取日誌檔案"""
    if not log_file.exists():
        print(f"❌ 日誌檔案不存在: {log_file}")
        return
    
    print(f"📂 讀取日誌: {log_file}\n")
    
    with open(log_file, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
    
    # 過濾行
    filtered_lines = all_lines
    
    # 過濾等級
    if level:
        level_upper = level.upper()
        filtered_lines = [
            line for line in filtered_lines 
            if f"| {level_upper} |" in line
        ]
    
    # 過濾關鍵字
    if keyword:
        filtered_lines = [
            line for line in filtered_lines 
            if keyword in line
        ]
    
    # 限制行數
    if lines:
        filtered_lines = filtered_lines[-lines:]
    
    # 列印結果
    if not filtered_lines:
        print("📭 沒有符合條件的日誌記錄")
    else:
        print(f"📊 找到 {len(filtered_lines)} 行記錄:\n")
        for line in filtered_lines:
            # 根據等級著色（簡易版）
            if "| ERROR |" in line:
                print(f"❌ {line.rstrip()}")
            elif "| WARNING |" in line:
                print(f"⚠️  {line.rstrip()}")
            elif "| INFO |" in line:
                print(f"ℹ️  {line.rstrip()}")
            else:
                print(f"   {line.rstrip()}")

def tail_log_file(log_file: Path, lines: int = 20):
    """即時監控日誌檔案（類似 tail -f）"""
    if not log_file.exists():
        print(f"❌ 日誌檔案不存在: {log_file}")
        print(f"💡 提示: 啟動 GUI 後日誌檔案會自動創建")
        return
    
    print_header(f"即時監控日誌: {log_file.name}")
    print("💡 按 Ctrl+C 停止監控\n")
    
    # 讀取最後 N 行
    with open(log_file, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
        for line in all_lines[-lines:]:
            print(line.rstrip())
    
    print("\n" + "-"*80)
    print("🔄 等待新日誌...\n")
    
    # 持續監控
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            # 移動到檔案結尾
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if line:
                    # 根據等級著色
                    if "| ERROR |" in line:
                        print(f"❌ {line.rstrip()}")
                    elif "| WARNING |" in line:
                        print(f"⚠️  {line.rstrip()}")
                    elif "| INFO |" in line:
                        print(f"ℹ️  {line.rstrip()}")
                    else:
                        print(f"   {line.rstrip()}")
                else:
                    time.sleep(0.1)
    except KeyboardInterrupt:
        print("\n\n✅ 監控已停止")

def list_all_logs():
    """列出所有日誌檔案"""
    print_header("所有日誌檔案")
    
    log_dir = Path("logs")
    if not log_dir.exists():
        print("❌ logs/ 目錄不存在")
        return
    
    log_files = sorted(log_dir.glob("f1_*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not log_files:
        print("📭 沒有找到日誌檔案")
        return
    
    print(f"📊 找到 {len(log_files)} 個日誌檔案:\n")
    
    for log_file in log_files:
        size_kb = log_file.stat().st_size / 1024
        mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
        print(f"  📄 {log_file.name}")
        print(f"     大小: {size_kb:.2f} KB")
        print(f"     修改時間: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

def main():
    parser = argparse.ArgumentParser(
        description="F1T 日誌查看器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 查看今天的 GUI 日誌（最後 50 行）
  python view_logs.py -n 50
  
  # 查看錯誤日誌
  python view_logs.py --error
  
  # 過濾 ERROR 等級的日誌
  python view_logs.py --level ERROR
  
  # 搜尋包含 "圈速控制" 的日誌
  python view_logs.py -k "圈速控制"
  
  # 即時監控日誌
  python view_logs.py --tail
  
  # 列出所有日誌檔案
  python view_logs.py --list
        """
    )
    
    parser.add_argument(
        "-c", "--component",
        default="gui",
        help="日誌組件名稱（預設: gui）"
    )
    
    parser.add_argument(
        "-n", "--lines",
        type=int,
        help="顯示最後 N 行"
    )
    
    parser.add_argument(
        "--level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="過濾特定等級的日誌"
    )
    
    parser.add_argument(
        "-k", "--keyword",
        help="搜尋包含特定關鍵字的日誌"
    )
    
    parser.add_argument(
        "--error",
        action="store_true",
        help="查看錯誤日誌檔案"
    )
    
    parser.add_argument(
        "--tail",
        action="store_true",
        help="即時監控日誌（類似 tail -f）"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有日誌檔案"
    )
    
    args = parser.parse_args()
    
    # 列出所有日誌
    if args.list:
        list_all_logs()
        return
    
    # 取得日誌檔案
    log_file = get_log_file(args.component, args.error)
    
    # 即時監控
    if args.tail:
        tail_log_file(log_file, args.lines or 20)
        return
    
    # 讀取日誌
    print_header(f"F1T 日誌查看器 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    read_log_file(log_file, args.lines, args.level, args.keyword)

if __name__ == "__main__":
    main()
