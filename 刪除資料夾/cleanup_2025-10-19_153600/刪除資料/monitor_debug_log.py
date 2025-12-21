#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
進度條調試日誌監控腳本

實時監控日誌文件，過濾出所有調試相關的日誌
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path

# 設定 UTF-8 輸出
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

def get_latest_log_file():
    """獲取最新的日誌文件"""
    log_dir = Path("logs")
    if not log_dir.exists():
        return None
    
    # 查找今天的日誌文件
    today = datetime.now().strftime("%Y-%m-%d")
    log_pattern = f"f1_gui_{today}.log"
    
    log_files = list(log_dir.glob(log_pattern))
    if not log_files:
        # 如果沒有今天的，找最新的
        log_files = sorted(log_dir.glob("f1_gui_*.log"), key=os.path.getmtime, reverse=True)
    
    return log_files[0] if log_files else None

def monitor_log(log_file, keywords=None):
    """監控日誌文件"""
    if keywords is None:
        keywords = ["DEBUG", "RACE_CONTROL", "LAP_CONTROL", "_check_and_trigger", "update_all_lap"]
    
    print("=" * 80)
    print("進度條調試日誌監控")
    print("=" * 80)
    print(f"\n監控文件: {log_file}")
    print(f"關鍵字: {', '.join(keywords)}")
    print("\n開始監控... (Ctrl+C 停止)\n")
    print("-" * 80)
    
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            # 移動到文件末尾
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                
                # 檢查是否包含關鍵字
                if any(keyword in line for keyword in keywords):
                    # 高亮顯示
                    if "🔵" in line or "DEBUG" in line:
                        print(f"\033[94m{line.strip()}\033[0m")  # 藍色
                    elif "🟢" in line:
                        print(f"\033[92m{line.strip()}\033[0m")  # 綠色
                    elif "ERROR" in line or "🔴" in line:
                        print(f"\033[91m{line.strip()}\033[0m")  # 紅色
                    elif "⚠️" in line or "WARNING" in line:
                        print(f"\033[93m{line.strip()}\033[0m")  # 黃色
                    else:
                        print(line.strip())
    except KeyboardInterrupt:
        print("\n\n監控已停止")
    except Exception as e:
        print(f"\n錯誤: {e}")

def show_recent_debug_logs(log_file, lines=50):
    """顯示最近的調試日誌"""
    print("=" * 80)
    print(f"最近 {lines} 行調試日誌")
    print("=" * 80)
    
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
            
        # 過濾調試相關的行
        debug_lines = [
            line for line in all_lines 
            if any(k in line for k in ["DEBUG", "RACE_CONTROL", "LAP_CONTROL"])
        ]
        
        # 顯示最後 N 行
        recent_lines = debug_lines[-lines:] if len(debug_lines) > lines else debug_lines
        
        for line in recent_lines:
            if "🔵" in line or "DEBUG" in line:
                print(f"\033[94m{line.strip()}\033[0m")  # 藍色
            elif "🟢" in line:
                print(f"\033[92m{line.strip()}\033[0m")  # 綠色
            elif "ERROR" in line or "🔴" in line:
                print(f"\033[91m{line.strip()}\033[0m")  # 紅色
            else:
                print(line.strip())
        
        print(f"\n總共 {len(debug_lines)} 行調試日誌，顯示最後 {len(recent_lines)} 行")
        
    except Exception as e:
        print(f"錯誤: {e}")

if __name__ == "__main__":
    log_file = get_latest_log_file()
    
    if not log_file:
        print("❌ 找不到日誌文件")
        print("請先啟動 GUI: python f1t_gui_main.py")
        sys.exit(1)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--recent":
        # 顯示最近的日誌
        lines = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        show_recent_debug_logs(log_file, lines)
    else:
        # 實時監控
        monitor_log(log_file)
