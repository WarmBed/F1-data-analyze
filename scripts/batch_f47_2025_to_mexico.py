#!/usr/bin/env python3
"""
F47 全車手彎道分析 - 2025 賽季批量執行腳本（反向下載）
============================================================
功能：自動執行 CLI Function 47（全車手彎道速度分析）
範圍：2025 年所有賽事（從墨西哥站往回下載到澳洲站）
會話：R（正賽）、Q（排位賽）、FP1/FP2/FP3（練習賽）
順序：第 20 場（墨西哥）→ 第 1 場（澳洲）
============================================================
"""

import os
import sys
import subprocess
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

# 確保在專案根目錄執行
if not Path("f1_analysis_modular_main.py").exists():
    print("錯誤：請在專案根目錄執行此腳本")
    sys.exit(1)

# 嘗試導入 tqdm 進度條（如果沒有則使用簡單的進度顯示）
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("提示：安裝 tqdm 可獲得更好的進度條體驗 (pip install tqdm)")
    print()


class SimpleProgressBar:
    """簡單的進度條替代品（當 tqdm 不可用時）"""
    
    def __init__(self, total: int, desc: str = ""):
        self.total = total
        self.current = 0
        self.desc = desc
        self.start_time = time.time()
    
    def update(self, n: int = 1):
        self.current += n
        self._display()
    
    def _display(self):
        percent = (self.current / self.total) * 100
        elapsed = time.time() - self.start_time
        eta = (elapsed / self.current * (self.total - self.current)) if self.current > 0 else 0
        
        bar_length = 40
        filled_length = int(bar_length * self.current / self.total)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)
        
        print(f"\r{self.desc} |{bar}| {self.current}/{self.total} [{percent:.1f}%] "
              f"ETA: {eta:.0f}s", end='', flush=True)
    
    def close(self):
        print()  # 換行


def get_2025_races() -> List[Dict]:
    """獲取 2025 年賽事列表（反向順序：墨西哥 → 澳洲）"""
    # 原始順序的賽事列表
    races_forward = [
        {"round": 1,  "name": "Australia",      "sessions": ["R", "Q", "FP1", "FP2", "FP3"]},
        {"round": 2,  "name": "China",          "sessions": ["R", "Q", "FP1", "FP2", "FP3"]},
        {"round": 3,  "name": "Japan",          "sessions": ["R", "Q", "FP1", "FP2", "FP3"]},
        {"round": 4,  "name": "Bahrain",        "sessions": ["R", "Q", "FP1", "FP2", "FP3"]},
        {"round": 5,  "name": "Saudi Arabia",   "sessions": ["R", "Q", "FP1", "FP2", "FP3"]},
        {"round": 6,  "name": "Miami",          "sessions": ["R", "Q", "FP1", "FP2", "FP3"]},
        {"round": 7,  "name": "Emilia Romagna", "sessions": ["R", "Q", "FP1", "FP2", "FP3"]},
        {"round": 8,  "name": "Monaco",         "sessions": ["R", "Q", "FP1", "FP2", "FP3"]},
        {"round": 9,  "name": "Spain",          "sessions": ["R", "Q", "FP1", "FP2", "FP3"]},
        {"round": 10, "name": "Canada",         "sessions": ["R", "Q", "FP1", "FP2", "FP3"]},
        {"round": 11, "name": "Austria",        "sessions": ["R", "Q", "FP1", "FP2", "FP3"]},
        {"round": 12, "name": "Great Britain",  "sessions": ["R", "Q", "FP1", "FP2", "FP3"]},
        {"round": 13, "name": "Belgium",        "sessions": ["R", "Q", "FP1", "FP2", "FP3"]},
        {"round": 14, "name": "Hungary",        "sessions": ["R", "Q", "FP1", "FP2", "FP3"]},
        {"round": 15, "name": "Netherlands",    "sessions": ["R", "Q", "FP1", "FP2", "FP3"]},
        {"round": 16, "name": "Italy",          "sessions": ["R", "Q", "FP1", "FP2", "FP3"]},
        {"round": 17, "name": "Azerbaijan",     "sessions": ["R", "Q", "FP1", "FP2", "FP3"]},
        {"round": 18, "name": "Singapore",      "sessions": ["R", "Q", "FP1", "FP2", "FP3"]},
        {"round": 19, "name": "United States",  "sessions": ["R", "Q", "FP1", "FP2", "FP3"]},
        {"round": 20, "name": "Mexico",         "sessions": ["R", "Q", "FP1", "FP2", "FP3"]},  # 墨西哥站包含所有會話
    ]
    
    # 反轉順序：墨西哥 (20) → 澳洲 (1)
    return list(reversed(races_forward))


def check_json_exists(year: int, race: str, session: str) -> bool:
    """檢查 JSON 檔案是否已存在"""
    json_dir = Path("json")
    pattern = f"all_drivers_cornering_analysis_{year}_{race}_{session}_*.json"
    return len(list(json_dir.glob(pattern))) > 0


def run_f47_analysis(year: int, race: str, session: str, verbose: bool = False) -> Tuple[bool, str]:
    """
    執行 CLI F47 分析
    
    Returns:
        (success: bool, message: str)
    """
    cmd = [
        sys.executable,
        "f1_analysis_modular_main.py",
        "-f", "47",
        "-y", str(year),
        "-r", race,
        "-s", session
    ]
    
    try:
        if verbose:
            # 顯示詳細輸出
            result = subprocess.run(
                cmd,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode != 0:
                return False, f"執行失敗 (返回碼: {result.returncode})"
        else:
            # 靜默執行
            result = subprocess.run(
                cmd,
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            if result.returncode != 0:
                return False, f"執行失敗 (返回碼: {result.returncode})"
        
        # 檢查 JSON 是否生成
        if check_json_exists(year, race, session):
            return True, "成功"
        else:
            return False, "JSON 未生成"
            
    except Exception as e:
        return False, f"異常: {str(e)}"


def main():
    """主函數"""
    print("=" * 70)
    print("  F47 全車手彎道分析 - 2025 賽季批量執行（反向下載）")
    print("=" * 70)
    print()
    
    # 獲取賽事列表
    races = get_2025_races()
    total_races = len(races)
    total_sessions = sum(len(race["sessions"]) for race in races)
    
    print(f"執行計畫：")
    print(f"  - 賽事數量：{total_races} 場")
    print(f"  - 總會話數：{total_sessions} 個")
    print(f"  - CLI 功能：F47 (全車手彎道速度分析)")
    print(f"  - 下載順序：墨西哥站 (R20) → 澳洲站 (R1)")
    print(f"  - 包含插值法：修復缺失的 Entry/Exit 50m 數據")
    print()
    
    # 詢問是否跳過已存在的檔案
    skip_existing_str = input("是否跳過已存在的 JSON 檔案？(Y/n): ").strip().lower()
    skip_existing = skip_existing_str != 'n'
    
    # 詢問是否顯示詳細輸出
    verbose_str = input("是否顯示詳細輸出？(y/N): ").strip().lower()
    verbose = verbose_str == 'y'
    
    print()
    print("開始執行...")
    print()
    
    # 統計計數器
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    # 建立任務列表
    tasks = []
    for race in races:
        for session in race["sessions"]:
            tasks.append({
                "round": race["round"],
                "race": race["name"],
                "session": session
            })
    
    # 開始計時
    start_time = time.time()
    
    # 選擇進度條
    if HAS_TQDM:
        progress_bar = tqdm(tasks, desc="總進度", unit="會話")
    else:
        progress_bar = SimpleProgressBar(len(tasks), "總進度")
    
    # 執行每個任務
    for task in (progress_bar if HAS_TQDM else tasks):
        if not HAS_TQDM:
            progress_bar.update(1)
        
        race_name = task["race"]
        session = task["session"]
        round_num = task["round"]
        
        # 顯示當前任務
        task_desc = f"[{round_num:2d}] {race_name:20s} - {session}"
        
        if HAS_TQDM:
            progress_bar.set_description(task_desc)
        else:
            print(f"\n{task_desc}")
        
        # 檢查是否已存在
        if skip_existing and check_json_exists(2025, race_name, session):
            if verbose:
                print(f"  ⏭️  跳過（已存在）")
            skip_count += 1
            continue
        
        # 執行分析
        success, message = run_f47_analysis(2025, race_name, session, verbose)
        
        if success:
            if verbose:
                print(f"  ✅ {message}")
            success_count += 1
        else:
            if verbose:
                print(f"  ❌ {message}")
            else:
                print(f"\n{task_desc} - ❌ {message}")
            fail_count += 1
        
        # 短暫延遲避免過載
        time.sleep(0.1)
    
    # 關閉進度條
    if not HAS_TQDM:
        progress_bar.close()
    
    # 結束計時
    end_time = time.time()
    duration = end_time - start_time
    
    # 顯示總結
    print()
    print("=" * 70)
    print("  執行完成")
    print("=" * 70)
    print()
    print("統計資訊：")
    print(f"  - ✅ 成功：{success_count} 個會話")
    print(f"  - ❌ 失敗：{fail_count} 個會話")
    print(f"  - ⏭️  跳過：{skip_count} 個會話（已存在）")
    print(f"  - 📊 總計：{total_sessions} 個會話")
    print()
    print(f"⏱️  執行時間：{duration:.1f} 秒 ({duration/60:.1f} 分鐘)")
    print()
    
    # 顯示最新生成的 JSON 檔案
    print("最新生成的 JSON 檔案：")
    json_dir = Path("json")
    json_files = sorted(
        json_dir.glob("all_drivers_cornering_analysis_2025_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )[:10]
    
    if json_files:
        for json_file in json_files:
            size_kb = json_file.stat().st_size / 1024
            mtime = datetime.fromtimestamp(json_file.stat().st_mtime)
            print(f"  - {json_file.name} ({size_kb:.1f} KB, {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
    else:
        print("  （無檔案）")
    
    print()
    print("腳本執行完畢！")
    
    # 返回失敗計數作為退出碼
    sys.exit(min(fail_count, 255))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用戶中斷執行")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ 錯誤：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
