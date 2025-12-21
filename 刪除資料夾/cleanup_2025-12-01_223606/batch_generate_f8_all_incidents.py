#!/usr/bin/env python3
"""
批次生成 2020-2025 所有賽事的 CLI Function 8 (All Incidents Summary)
自動化處理所有年份和賽事的事件詳細列表，包含新增的 track_location 欄位
"""

import subprocess
import time
import json
import os
from datetime import datetime
from pathlib import Path

# 2020-2025 年度賽事列表（根據 F1 實際賽曆）
RACE_CALENDAR = {
    2020: [
        "Austrian", "Styrian", "Hungarian", "British", "70th Anniversary",
        "Spanish", "Belgian", "Italian", "Tuscan", "Russian",
        "Eifel", "Portuguese", "Emilia Romagna", "Turkish", "Bahrain",
        "Sakhir", "Abu Dhabi"
    ],
    2021: [
        "Bahrain", "Emilia Romagna", "Portuguese", "Spanish", "Monaco",
        "Azerbaijan", "French", "Styrian", "Austrian", "British",
        "Hungarian", "Belgian", "Dutch", "Italian", "Russian",
        "Turkish", "United States", "Mexico", "São Paulo", "Qatar",
        "Saudi Arabian", "Abu Dhabi"
    ],
    2022: [
        "Bahrain", "Saudi Arabian", "Australian", "Emilia Romagna", "Miami",
        "Spanish", "Monaco", "Azerbaijan", "Canadian", "British",
        "Austrian", "French", "Hungarian", "Belgian", "Dutch",
        "Italian", "Singapore", "Japanese", "United States", "Mexico",
        "São Paulo", "Abu Dhabi"
    ],
    2023: [
        "Bahrain", "Saudi Arabian", "Australian", "Azerbaijan", "Miami",
        "Monaco", "Spanish", "Canadian", "Austrian", "British",
        "Hungarian", "Belgian", "Dutch", "Italian", "Singapore",
        "Japanese", "Qatar", "United States", "Mexico", "São Paulo",
        "Las Vegas", "Abu Dhabi"
    ],
    2024: [
        "Bahrain", "Saudi Arabian", "Australian", "Japanese", "Chinese",
        "Miami", "Emilia Romagna", "Monaco", "Canadian", "Spanish",
        "Austrian", "British", "Hungarian", "Belgian", "Dutch",
        "Italian", "Azerbaijan", "Singapore", "United States", "Mexico",
        "São Paulo", "Las Vegas", "Qatar", "Abu Dhabi"
    ],
    2025: [
        "Australian", "Chinese", "Japanese", "Bahrain", "Saudi Arabian",
        "Miami", "Emilia Romagna", "Monaco", "Spanish", "Canadian",
        "Austrian", "British", "Belgian", "Hungarian", "Dutch",
        "Italian", "Azerbaijan", "Singapore", "United States", "Mexico",
        "São Paulo", "Las Vegas", "Qatar", "Abu Dhabi"
    ]
}

# 賽段類型（可根據需求調整）
SESSION_TYPES = ["R"]  # R = Race, Q = Qualifying, FP1/FP2/FP3 = Practice

# 統計數據
stats = {
    "total_races": 0,
    "successful": 0,
    "failed": 0,
    "skipped": 0,
    "total_incidents": 0,
    "total_turn_events": 0,
    "failed_races": [],
    "processing_times": []
}


def sanitize_race_name(race_name):
    """標準化賽事名稱，處理特殊字符"""
    # 移除 Grand Prix 後綴（CLI 可能不需要）
    standardized = race_name.replace(" Grand Prix", "")
    
    # 特殊名稱映射
    name_mapping = {
        "70th Anniversary": "70th_Anniversary_Grand_Prix",
        "Styrian": "Styrian_Grand_Prix",
        "Emilia Romagna": "Emilia_Romagna_Grand_Prix",
        "São Paulo": "Sao_Paulo_Grand_Prix",
        "Sakhir": "Sakhir_Grand_Prix"
    }
    
    if standardized in name_mapping:
        return name_mapping[standardized]
    
    return standardized


def check_json_exists(year, race, session):
    """檢查 JSON 檔案是否已存在"""
    race_token = race.replace(" ", "_")
    session_token = session.upper()
    
    # 檢查多種可能的檔名格式
    possible_names = [
        f"all_incidents_summary_{year}_{race_token}_{session_token}.json",
        f"all_incidents_summary_{year}_{race_token}_Grand_Prix_{session_token}.json",
        f"all_incidents_summary_{year}_{race.replace(' ', '_')}_Grand_Prix_{session_token}.json"
    ]
    
    json_dir = Path("json")
    for filename in possible_names:
        if (json_dir / filename).exists():
            return True, filename
    
    return False, None


def run_cli_function_8(year, race, session):
    """執行 CLI Function 8 生成 JSON"""
    
    # 標準化賽事名稱
    race_name = f"{race} Grand Prix"
    
    print(f"\n{'='*80}")
    print(f"處理: {year} {race_name} - {session}")
    print(f"{'='*80}")
    
    # 檢查是否已存在
    exists, existing_file = check_json_exists(year, race, session)
    if exists:
        print(f"⏭️  檔案已存在: {existing_file}")
        stats["skipped"] += 1
        return True
    
    # 執行 CLI 命令
    cmd = [
        "python", 
        "f1_analysis_modular_main.py",
        "-f", "8",
        "-y", str(year),
        "-r", race_name,
        "-s", session
    ]
    
    print(f"🚀 執行命令: {' '.join(cmd)}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=300  # 5 分鐘超時
        )
        
        elapsed_time = time.time() - start_time
        stats["processing_times"].append(elapsed_time)
        
        if result.returncode == 0:
            print(f"✅ 成功完成 (耗時: {elapsed_time:.1f}秒)")
            stats["successful"] += 1
            
            # 分析生成的 JSON
            analyze_generated_json(year, race, session)
            return True
        else:
            print(f"❌ 執行失敗 (Exit Code: {result.returncode})")
            print(f"錯誤輸出: {result.stderr[-500:]}")  # 顯示最後 500 字元
            stats["failed"] += 1
            stats["failed_races"].append(f"{year} {race} {session}")
            return False
            
    except subprocess.TimeoutExpired:
        elapsed_time = time.time() - start_time
        print(f"⏱️  執行超時 (超過 {elapsed_time:.1f}秒)")
        stats["failed"] += 1
        stats["failed_races"].append(f"{year} {race} {session} (超時)")
        return False
        
    except Exception as e:
        print(f"❌ 執行錯誤: {str(e)}")
        stats["failed"] += 1
        stats["failed_races"].append(f"{year} {race} {session} (異常)")
        return False


def analyze_generated_json(year, race, session):
    """分析生成的 JSON，統計 track_location 欄位"""
    exists, filename = check_json_exists(year, race, session)
    
    if not exists:
        print("⚠️  找不到生成的 JSON 檔案")
        return
    
    json_path = Path("json") / filename
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        incidents = data.get('data', {}).get('all_incidents', [])
        total = len(incidents)
        with_location = sum(1 for inc in incidents if inc.get('track_location'))
        turn_events = sum(1 for inc in incidents 
                         if inc.get('track_location', {}) and 
                            inc.get('track_location').get('type') == 'TURN')
        
        stats["total_incidents"] += total
        stats["total_turn_events"] += turn_events
        
        print(f"📊 事件統計:")
        print(f"   總事件數: {total}")
        print(f"   有 track_location: {with_location} ({with_location/total*100:.1f}%)")
        print(f"   TURN 事件: {turn_events}")
        
    except Exception as e:
        print(f"⚠️  JSON 分析失敗: {str(e)}")


def generate_progress_report():
    """生成進度報告"""
    print("\n" + "="*80)
    print("批次處理進度報告")
    print("="*80)
    
    total_processed = stats["successful"] + stats["failed"]
    
    print(f"\n總計:")
    print(f"  目標賽事數: {stats['total_races']}")
    print(f"  已處理: {total_processed}")
    print(f"  ✅ 成功: {stats['successful']}")
    print(f"  ⏭️  跳過（已存在）: {stats['skipped']}")
    print(f"  ❌ 失敗: {stats['failed']}")
    
    if stats["processing_times"]:
        avg_time = sum(stats["processing_times"]) / len(stats["processing_times"])
        total_time = sum(stats["processing_times"])
        print(f"\n處理時間:")
        print(f"  平均每場: {avg_time:.1f}秒")
        print(f"  總耗時: {total_time:.1f}秒 ({total_time/60:.1f}分鐘)")
    
    print(f"\n數據統計:")
    print(f"  總事件數: {stats['total_incidents']}")
    print(f"  總 TURN 事件: {stats['total_turn_events']}")
    
    if stats["failed_races"]:
        print(f"\n失敗的賽事:")
        for race in stats["failed_races"]:
            print(f"  ❌ {race}")
    
    print("\n" + "="*80)


def save_summary_report():
    """儲存摘要報告"""
    report = {
        "generation_date": datetime.now().isoformat(),
        "statistics": stats,
        "race_calendar": RACE_CALENDAR
    }
    
    report_path = Path("json") / "f8_batch_generation_report.json"
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 摘要報告已儲存: {report_path}")


def main():
    """主函數"""
    print("="*80)
    print("CLI Function 8 批次生成工具")
    print("生成 2020-2025 所有賽事的事件詳細列表（包含 track_location 欄位）")
    print("="*80)
    
    # 確認 json 目錄存在
    Path("json").mkdir(exist_ok=True)
    
    # 詢問使用者是否要跳過已存在的檔案
    skip_existing = input("\n是否跳過已存在的 JSON 檔案？(Y/n): ").strip().lower() != 'n'
    
    # 詢問要處理的年份
    print("\n選擇要處理的年份:")
    print("1. 全部 (2020-2025)")
    print("2. 指定年份")
    choice = input("請選擇 (1/2): ").strip()
    
    if choice == "2":
        year_input = input("請輸入年份（用逗號分隔，如: 2022,2023）: ").strip()
        selected_years = [int(y.strip()) for y in year_input.split(",")]
        selected_years = [y for y in selected_years if y in RACE_CALENDAR]
    else:
        selected_years = list(RACE_CALENDAR.keys())
    
    print(f"\n將處理以下年份: {', '.join(map(str, selected_years))}")
    
    # 計算總賽事數
    for year in selected_years:
        stats["total_races"] += len(RACE_CALENDAR[year]) * len(SESSION_TYPES)
    
    print(f"總共 {stats['total_races']} 場賽事")
    
    # 確認開始
    confirm = input("\n是否開始批次處理？(Y/n): ").strip().lower()
    if confirm == 'n':
        print("已取消批次處理")
        return
    
    # 開始批次處理
    start_time = time.time()
    
    for year in sorted(selected_years):
        print(f"\n{'#'*80}")
        print(f"# {year} 賽季")
        print(f"{'#'*80}")
        
        for race in RACE_CALENDAR[year]:
            for session in SESSION_TYPES:
                run_cli_function_8(year, race, session)
                
                # 每場比賽之間暫停 2 秒，避免過載
                time.sleep(2)
    
    total_elapsed = time.time() - start_time
    
    # 生成報告
    generate_progress_report()
    
    print(f"\n總執行時間: {total_elapsed:.1f}秒 ({total_elapsed/60:.1f}分鐘)")
    
    # 儲存報告
    save_summary_report()
    
    print("\n✅ 批次處理完成！")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  使用者中斷執行")
        generate_progress_report()
        save_summary_report()
    except Exception as e:
        print(f"\n\n❌ 執行錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        generate_progress_report()
        save_summary_report()
