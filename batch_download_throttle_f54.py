#!/usr/bin/env python3
"""
批次下載 2020-2025 所有賽事的 Function 54 (Throttle Ratio) JSON
Batch Download Function 54 for All Races 2020-2025

執行方式:
    python batch_download_throttle_f54.py

功能:
    - 自動載入 2020-2025 年所有賽季賽程
    - 逐場執行 Function 54 生成 JSON
    - 跳過已存在的檔案 (可選強制重新生成)
    - 顯示進度和預估剩餘時間
    - 錯誤處理和自動重試
"""

import os
import sys
import json
import time
import warnings
from datetime import datetime
from typing import List, Dict, Tuple

# 抑制警告
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# 確保路徑
sys.path.insert(0, '.')

from CLI_modules.cli.core.compatible_data_loader import CompatibleF1DataLoader
from CLI_modules.cli.analyzer.driver_throttle_ratio import run_driver_throttle_ratio_analysis

# ==================== 配置區 ====================

# 是否強制重新生成已存在的 JSON
FORCE_REGENERATE = False

# 每場比賽失敗後的重試次數
MAX_RETRIES = 2

# JSON 輸出目錄
JSON_OUTPUT_DIR = "json"

# 預估每場比賽耗時（秒）
ESTIMATED_TIME_PER_RACE = 110

# 下載年份（依照排列順序處理）。預設為 2025 → 2024。
TARGET_YEARS = [2025, 2024]

# ==================== 賽季賽程資料 ====================

RACE_CALENDAR = {
    2020: [
        "Austria", "Styria", "Hungary", "Great Britain", "70th Anniversary", 
        "Spain", "Belgium", "Italy", "Tuscany", "Russia", "Eifel", 
        "Portugal", "Emilia Romagna", "Turkey", "Bahrain", "Sakhir", "Abu Dhabi"
    ],
    2021: [
        "Bahrain", "Emilia Romagna", "Portugal", "Spain", "Monaco", "Azerbaijan",
        "France", "Styria", "Austria", "Great Britain", "Hungary", "Belgium",
        "Netherlands", "Italy", "Russia", "Turkey", "United States", "Mexico",
        "Brazil", "Qatar", "Saudi Arabia", "Abu Dhabi"
    ],
    2022: [
        "Bahrain", "Saudi Arabia", "Australia", "Emilia Romagna", "Miami", "Spain",
        "Monaco", "Azerbaijan", "Canada", "Great Britain", "Austria", "France",
        "Hungary", "Belgium", "Netherlands", "Italy", "Singapore", "Japan",
        "United States", "Mexico", "Brazil", "Abu Dhabi"
    ],
    2023: [
        "Bahrain", "Saudi Arabia", "Australia", "Azerbaijan", "Miami", "Monaco",
        "Spain", "Canada", "Austria", "Great Britain", "Hungary", "Belgium",
        "Netherlands", "Italy", "Singapore", "Japan", "Qatar", "United States",
        "Mexico", "Brazil", "Las Vegas", "Abu Dhabi"
    ],
    2024: [
        "Bahrain", "Saudi Arabia", "Australia", "Japan", "China", "Miami",
        "Emilia Romagna", "Monaco", "Canada", "Spain", "Austria", "Great Britain",
        "Hungary", "Belgium", "Netherlands", "Italy", "Azerbaijan", "Singapore",
        "United States", "Mexico", "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
    ],
    2025: [
        "Australia", "China", "Japan", "Bahrain", "Saudi Arabia", "Miami",
        "Emilia Romagna", "Monaco", "Spain", "Canada", "Austria", "Great Britain",
        "Belgium", "Hungary", "Netherlands", "Italy", "Azerbaijan", "Singapore",
        "United States", "Mexico", "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
    ]
}

SESSIONS = ["R"]  # 只下載正賽，可改為 ["FP1", "FP2", "FP3", "Q", "R"]

# ==================== 輔助函數 ====================

def slugify(text: str) -> str:
    """轉換為檔案名稱格式"""
    return text.strip().replace(" ", "_").replace("/", "-").lower()

def check_json_exists(year: int, race: str, session: str) -> Tuple[bool, str]:
    """檢查 JSON 是否已存在"""
    race_slug = slugify(race)
    filename = f"throttle_ratio_{year}_{race_slug}_{session}.json"
    filepath = os.path.join(JSON_OUTPUT_DIR, filename)
    return os.path.exists(filepath), filepath

def format_time(seconds: float) -> str:
    """格式化時間顯示"""
    if seconds < 60:
        return f"{seconds:.0f}秒"
    elif seconds < 3600:
        return f"{seconds/60:.1f}分鐘"
    else:
        return f"{seconds/3600:.1f}小時"

def get_total_races(years: List[int]) -> int:
    """計算指定年份的總賽事數量"""
    total = 0
    for year in years:
        races = RACE_CALENDAR.get(year, [])
        total += len(races) * len(SESSIONS)
    return total

# ==================== 主要執行邏輯 ====================

def download_single_race(year: int, race: str, session: str, 
                         current: int, total: int) -> Dict:
    """下載單場比賽的 Function 54 JSON"""
    
    race_slug = slugify(race)
    print(f"\n{'='*80}")
    print(f"📍 [{current}/{total}] {year} {race} - {session}")
    print(f"{'='*80}")
    
    # 檢查是否已存在
    exists, filepath = check_json_exists(year, race, session)
    if exists and not FORCE_REGENERATE:
        print(f"✅ JSON 已存在，跳過: {os.path.basename(filepath)}")
        return {
            "success": True,
            "year": year,
            "race": race,
            "session": session,
            "skipped": True,
            "filepath": filepath
        }
    
    # 初始化數據載入器
    print(f"🔄 正在載入賽事數據...")
    loader = CompatibleF1DataLoader()
    
    if not loader.load_race_data(year, race, session):
        print(f"❌ 數據載入失敗")
        return {
            "success": False,
            "year": year,
            "race": race,
            "session": session,
            "error": "數據載入失敗"
        }
    
    # 執行 Function 54
    print(f"⚙️  正在執行 Function 54 分析...")
    start_time = time.time()
    
    try:
        result = run_driver_throttle_ratio_analysis(
            data_loader=loader,
            threshold=0.9,
            coast_threshold=0.2,
            show_summary=False,
            save_json=True
        )
        
        elapsed = time.time() - start_time
        
        if result.get("success"):
            print(f"✅ 分析完成 (耗時: {elapsed:.1f}秒)")
            print(f"💾 JSON 已保存: {os.path.basename(result.get('json_output', filepath))}")
            return {
                "success": True,
                "year": year,
                "race": race,
                "session": session,
                "elapsed": elapsed,
                "filepath": result.get("json_output", filepath)
            }
        else:
            print(f"❌ 分析失敗: {result.get('message', '未知錯誤')}")
            return {
                "success": False,
                "year": year,
                "race": race,
                "session": session,
                "error": result.get("message", "未知錯誤")
            }
            
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"❌ 執行異常 (耗時: {elapsed:.1f}秒): {str(e)}")
        return {
            "success": False,
            "year": year,
            "race": race,
            "session": session,
            "error": str(e)
        }

def main():
    """主程式入口"""
    
    print("\n" + "="*80)
    print("🏎️  F1 Throttle Ratio 批次下載工具 (Function 54)")
    print("="*80)
    target_years_label = ", ".join(str(year) for year in TARGET_YEARS)
    print(f"📅 目標年份: {target_years_label}")
    print(f"🏁 會話類型: {', '.join(SESSIONS)}")
    print(f"📁 輸出目錄: {JSON_OUTPUT_DIR}")
    print(f"🔄 強制重新生成: {'是' if FORCE_REGENERATE else '否'}")
    print("="*80 + "\n")
    
    # 確保輸出目錄存在
    os.makedirs(JSON_OUTPUT_DIR, exist_ok=True)
    
    # 建立任務列表
    tasks = []
    missing_years = []
    for year in TARGET_YEARS:
        races = RACE_CALENDAR.get(year)
        if not races:
            missing_years.append(year)
            continue
        for race in races:
            for session in SESSIONS:
                tasks.append((year, race, session))

    if missing_years:
        print(f"⚠️  未在 RACE_CALENDAR 找到以下年份，將跳過: {', '.join(str(y) for y in missing_years)}")
    
    total_tasks = len(tasks)
    if total_tasks == 0:
        print("❌ 未找到可處理的賽事，請確認 TARGET_YEARS 或 RACE_CALENDAR 配置。")
        return

    print(f"📊 總計 {total_tasks} 場比賽待處理")
    print(f"⏱️  預估總耗時: {format_time(total_tasks * ESTIMATED_TIME_PER_RACE)}\n")
    
    input("按 Enter 開始下載，或 Ctrl+C 取消...")
    
    # 執行下載
    results = []
    start_time = time.time()
    successful = 0
    skipped = 0
    failed = 0
    
    for idx, (year, race, session) in enumerate(tasks, 1):
        result = download_single_race(year, race, session, idx, total_tasks)
        results.append(result)
        
        if result.get("success"):
            if result.get("skipped"):
                skipped += 1
            else:
                successful += 1
        else:
            failed += 1
            # 失敗時可選擇重試
            for retry in range(MAX_RETRIES):
                print(f"🔄 重試 {retry+1}/{MAX_RETRIES}...")
                time.sleep(5)  # 等待 5 秒後重試
                result = download_single_race(year, race, session, idx, total_tasks)
                if result.get("success"):
                    failed -= 1
                    successful += 1
                    results[-1] = result
                    break
        
        # 顯示進度
        completed = idx
        remaining = total_tasks - completed
        elapsed = time.time() - start_time
        avg_time = elapsed / completed
        estimated_remaining = remaining * avg_time
        
        print(f"\n📈 進度: {completed}/{total_tasks} ({completed/total_tasks*100:.1f}%)")
        print(f"⏱️  已耗時: {format_time(elapsed)} | 預估剩餘: {format_time(estimated_remaining)}")
        print(f"✅ 成功: {successful} | ⏭️  跳過: {skipped} | ❌ 失敗: {failed}")
    
    # 最終報告
    total_elapsed = time.time() - start_time
    print("\n" + "="*80)
    print("🏁 批次下載完成！")
    print("="*80)
    print(f"⏱️  總耗時: {format_time(total_elapsed)}")
    print(f"✅ 成功: {successful}")
    print(f"⏭️  跳過: {skipped}")
    print(f"❌ 失敗: {failed}")
    print(f"📊 總計: {total_tasks}")
    print("="*80 + "\n")
    
    # 保存結果報告
    report_file = f"throttle_download_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump({
            "summary": {
                "total": total_tasks,
                "successful": successful,
                "skipped": skipped,
                "failed": failed,
                "elapsed_seconds": total_elapsed
            },
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"📄 詳細報告已保存: {report_file}")
    
    # 列出失敗的賽事
    if failed > 0:
        print("\n❌ 失敗的賽事:")
        for result in results:
            if not result.get("success"):
                print(f"   - {result['year']} {result['race']} {result['session']}: {result.get('error', '未知錯誤')}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  使用者中斷執行")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ 執行錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
