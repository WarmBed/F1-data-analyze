#!/usr/bin/env python3
"""
F1T GUI 批次數據生成器
=====================
為 GUI 預先生成所有分析功能的 JSON 檔案

使用方式:
    # 單場賽事
    python batch_generate_gui_data.py -y 2025 -r Japan
    
    # 多場賽事
    python batch_generate_gui_data.py -y 2025 -r Japan -r Monaco -r Italy
    
    # 整季 (使用 FastF1 獲取賽事列表)
    python batch_generate_gui_data.py -y 2025 --all-races

功能 ID 對照表:
    F1  - Rain Analysis (降雨分析)
    F2  - Track Analysis (賽道分析)
    F3  - Driver Fastest Pitstop Ranking (車手最快進站排行)
    F4  - Team Pitstop Ranking (車隊進站排行)
    F5  - Driver Detailed Pitstop Records (車手進站詳細記錄)
    F8  - Accident Analysis (事故分析)
    F25 - Driver Race Position (車手位置分析)
    F26 - Tire Strategy Analysis (輪胎策略分析)
    F28 - Detailed Lap Analysis (詳細圈速分析)
    F34 - All Drivers Brake Performance (全車手煞車性能)
    F47 - All Drivers Cornering Analysis (全車手彎道分析)
    F48 - All Drivers Straight Line Speed (全車手直線速度)
    F53 - Ideal Lap Analysis (理想圈分析)
    F54 - Throttle Analysis (油門比例分析)
    F74 - Qualifying Prediction FP3->Q (排位賽預測)
    F80 - Race Prediction Q->R (正賽預測)
    F100 - Historical Track Map (歷年旗幟統計)

作者: F1T Team
日期: 2025-12-01
"""

import argparse
import os
import sys
import subprocess
import glob
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from datetime import datetime

try:
    from tqdm import tqdm
except ImportError:
    print("[WARNING] tqdm not installed, using simple progress")
    tqdm = None

# ============================================================================
# 配置: 功能 ID 與 Session 適用性對照表
# ============================================================================

@dataclass
class FunctionConfig:
    """功能配置"""
    function_id: int
    name: str
    json_prefix: str  # JSON 檔案名稱前綴
    applicable_sessions: Set[str]  # 適用的 Session 類型
    special_naming: bool = False  # 是否有特殊命名規則

# 功能配置表
FUNCTION_CONFIGS: Dict[int, FunctionConfig] = {
    # Race Overview Analysis
    1: FunctionConfig(1, "Rain Analysis", "enhanced_rain_analysis", {"FP1", "FP2", "FP3", "Q", "SQ", "R"}),
    2: FunctionConfig(2, "Track Analysis", "track_position_analysis", {"FP1", "FP2", "FP3", "Q", "SQ", "R"}),
    3: FunctionConfig(3, "Driver Fastest Pitstop", "driver_fastest_pitstop_ranking", {"R"}, special_naming=True),
    4: FunctionConfig(4, "Team Pitstop Ranking", "team_pitstop_ranking", {"R"}, special_naming=True),
    5: FunctionConfig(5, "Driver Detailed Pitstop", "driver_detailed_pitstop_records", {"R"}),
    8: FunctionConfig(8, "Accident Analysis", "all_incidents_summary", {"R"}, special_naming=True),
    
    # Driver Performance Analysis
    25: FunctionConfig(25, "Driver Race Position", "driver_race_position", {"Q", "SQ", "R"}),
    26: FunctionConfig(26, "Tire Strategy", "tire_strategy", {"R"}),
    28: FunctionConfig(28, "Detailed Lap Analysis", "detailed_laptime_analysis", {"Q", "SQ", "R"}),
    34: FunctionConfig(34, "Brake Performance", "brake_performance", {"FP1", "FP2", "FP3", "Q", "SQ", "R"}),
    47: FunctionConfig(47, "Corner Analysis", "all_drivers_cornering_analysis", {"FP1", "FP2", "FP3", "Q", "SQ", "R"}),
    48: FunctionConfig(48, "Straight Line Speed", "all_drivers_straight_line_speed", {"FP1", "FP2", "FP3", "Q", "SQ", "R"}),
    53: FunctionConfig(53, "Ideal Lap Analysis", "ideal_lap_ranking", {"FP3", "Q", "R"}),
    54: FunctionConfig(54, "Throttle Analysis", "driver_throttle_ratio", {"FP1", "FP2", "FP3", "Q", "SQ", "R"}),
    
    # Prediction
    74: FunctionConfig(74, "FP3->Q Prediction", "qualifying_prediction", {"FP3"}),
    80: FunctionConfig(80, "Q->R Prediction", "race_prediction", {"Q"}),
    
    # Multi-Season (不需要 session)
    100: FunctionConfig(100, "Historical Track Map", "historical_flags", set()),
}

# 所有可能的 Session 類型
ALL_SESSIONS = ["FP1", "FP2", "FP3", "Q", "SQ", "SR", "R"]

# ============================================================================
# 工具函數
# ============================================================================

def get_json_dir() -> str:
    """獲取 JSON 目錄路徑"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "json")


def check_json_exists(config: FunctionConfig, year: int, race: str, session: str) -> bool:
    """檢查 JSON 檔案是否已存在"""
    json_dir = get_json_dir()
    
    # 構建搜索模式
    if config.special_naming:
        # 特殊命名: 可能使用 Grand_Prix 格式
        patterns = [
            f"{config.json_prefix}_{year}_{race}_{session}*.json",
            f"{config.json_prefix}_{year}_{race.replace(' ', '_')}*.json",
            f"{config.json_prefix}_{year}_*{race}*_{session}*.json",
        ]
    else:
        patterns = [
            f"{config.json_prefix}_{year}_{race}_{session}*.json",
        ]
    
    for pattern in patterns:
        full_pattern = os.path.join(json_dir, pattern)
        matches = glob.glob(full_pattern)
        if matches:
            return True
    
    return False


def check_historical_json_exists(race: str) -> bool:
    """檢查歷史旗幟 JSON 是否存在"""
    json_dir = get_json_dir()
    race_normalized = race.replace(" ", "_")
    pattern = os.path.join(json_dir, f"historical_flags_{race_normalized}_*.json")
    return len(glob.glob(pattern)) > 0


def get_season_races(year: int) -> List[str]:
    """獲取指定年份的所有賽事名稱"""
    try:
        import fastf1
        schedule = fastf1.get_event_schedule(year)
        # 過濾掉測試賽事
        races = schedule[schedule['EventFormat'] != 'testing']['EventName'].tolist()
        # 簡化賽事名稱 (移除 "Grand Prix" 後綴)
        simplified = []
        for race in races:
            if 'Grand Prix' in race:
                # 提取國家/城市名稱
                name = race.replace(' Grand Prix', '')
                simplified.append(name)
            else:
                simplified.append(race)
        return simplified
    except Exception as e:
        print(f"[ERROR] 無法獲取 {year} 賽季列表: {e}")
        return []


def check_session_exists(year: int, race: str, session: str) -> bool:
    """檢查指定 Session 是否存在 (使用 FastF1)"""
    try:
        import fastf1
        # 嘗試獲取 session 資訊
        event = fastf1.get_event(year, race)
        session_mapping = {
            'FP1': 'Practice 1',
            'FP2': 'Practice 2', 
            'FP3': 'Practice 3',
            'Q': 'Qualifying',
            'SQ': 'Sprint Qualifying',
            'SR': 'Sprint',
            'R': 'Race'
        }
        
        # 檢查 event 格式來判斷是否有 Sprint
        event_format = event.get('EventFormat', 'conventional')
        
        # Sprint 週末沒有 FP2, FP3
        if event_format == 'sprint_qualifying':
            if session in ['FP2', 'FP3']:
                return False
        elif event_format == 'sprint':
            if session in ['FP2', 'FP3']:
                return False
        elif event_format == 'conventional':
            if session in ['SQ', 'SR']:
                return False
        
        return True
        
    except Exception:
        # 如果無法確認，返回 True 讓 CLI 自己處理
        return True


def run_cli_command(function_id: int, year: int, race: str, session: str) -> Dict:
    """執行 CLI 命令"""
    cmd = [
        sys.executable,
        "f1_analysis_modular_main.py",
        "-f", str(function_id),
        "-y", str(year),
        "-r", race,
        "-s", session
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',  # 遇到編碼錯誤時替換字符
            timeout=300  # 5 分鐘超時
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command timed out after 5 minutes",
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }


def run_historical_cli_command(function_id: int, race: str) -> Dict:
    """執行歷史分析 CLI 命令 (不需要 year/session)"""
    cmd = [
        sys.executable,
        "f1_analysis_modular_main.py",
        "-f", str(function_id),
        "-r", race
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',  # 遇到編碼錯誤時替換字符
            timeout=300
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": "Command timed out after 5 minutes",
            "returncode": -1
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "returncode": -1
        }


# ============================================================================
# 主要邏輯
# ============================================================================

@dataclass
class TaskResult:
    """任務結果"""
    function_id: int
    function_name: str
    year: int
    race: str
    session: str
    status: str  # "success", "skipped", "failed", "no_session"
    message: str = ""


def generate_tasks(year: int, races: List[str], functions: Optional[List[int]] = None) -> List[Dict]:
    """生成所有需要執行的任務"""
    tasks = []
    
    # 如果沒有指定功能，使用所有功能
    if functions is None:
        functions = list(FUNCTION_CONFIGS.keys())
    
    for race in races:
        for func_id in functions:
            config = FUNCTION_CONFIGS.get(func_id)
            if not config:
                continue
            
            # F100 歷史分析: 特殊處理
            if func_id == 100:
                tasks.append({
                    "function_id": func_id,
                    "config": config,
                    "year": year,
                    "race": race,
                    "session": "HISTORICAL"
                })
                continue
            
            # 其他功能: 遍歷適用的 Session
            for session in ALL_SESSIONS:
                if session in config.applicable_sessions:
                    tasks.append({
                        "function_id": func_id,
                        "config": config,
                        "year": year,
                        "race": race,
                        "session": session
                    })
    
    return tasks


def execute_task(task: Dict, dry_run: bool = False) -> TaskResult:
    """執行單一任務"""
    func_id = task["function_id"]
    config = task["config"]
    year = task["year"]
    race = task["race"]
    session = task["session"]
    
    # F100 歷史分析
    if func_id == 100:
        if check_historical_json_exists(race):
            return TaskResult(
                func_id, config.name, year, race, "HISTORICAL",
                "skipped", "JSON already exists"
            )
        
        if dry_run:
            return TaskResult(
                func_id, config.name, year, race, "HISTORICAL",
                "dry_run", "Would execute"
            )
        
        result = run_historical_cli_command(func_id, race)
        if result["success"]:
            return TaskResult(
                func_id, config.name, year, race, "HISTORICAL",
                "success", "Generated successfully"
            )
        else:
            return TaskResult(
                func_id, config.name, year, race, "HISTORICAL",
                "failed", result["stderr"][:200]
            )
    
    # 檢查 Session 是否存在
    if not check_session_exists(year, race, session):
        return TaskResult(
            func_id, config.name, year, race, session,
            "no_session", f"Session {session} not available for this race"
        )
    
    # 檢查 JSON 是否已存在
    if check_json_exists(config, year, race, session):
        return TaskResult(
            func_id, config.name, year, race, session,
            "skipped", "JSON already exists"
        )
    
    # Dry run 模式
    if dry_run:
        return TaskResult(
            func_id, config.name, year, race, session,
            "dry_run", "Would execute"
        )
    
    # 執行 CLI
    result = run_cli_command(func_id, year, race, session)
    
    if result["success"]:
        return TaskResult(
            func_id, config.name, year, race, session,
            "success", "Generated successfully"
        )
    else:
        return TaskResult(
            func_id, config.name, year, race, session,
            "failed", result["stderr"][:200] if result["stderr"] else "Unknown error"
        )


def main():
    parser = argparse.ArgumentParser(
        description="F1T GUI 批次數據生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
    # 單場賽事
    python batch_generate_gui_data.py -y 2025 -r Japan
    
    # 多場賽事
    python batch_generate_gui_data.py -y 2025 -r Japan -r Monaco
    
    # 整季
    python batch_generate_gui_data.py -y 2025 --all-races
    
    # 只執行特定功能
    python batch_generate_gui_data.py -y 2025 -r Japan -f 1 -f 2 -f 47
    
    # Dry run (只顯示會執行什麼)
    python batch_generate_gui_data.py -y 2025 -r Japan --dry-run
"""
    )
    
    parser.add_argument("-y", "--year", type=int,
                        help="賽季年份 (例: 2025)")
    parser.add_argument("-r", "--race", action="append", dest="races",
                        help="賽事名稱 (可多次指定)")
    parser.add_argument("--all-races", action="store_true",
                        help="處理整季所有賽事")
    parser.add_argument("-f", "--function", action="append", type=int, dest="functions",
                        help="指定功能 ID (可多次指定)")
    parser.add_argument("--dry-run", action="store_true",
                        help="只顯示會執行的任務，不實際執行")
    parser.add_argument("--list-functions", action="store_true",
                        help="列出所有可用功能")
    
    args = parser.parse_args()
    
    # 列出功能
    if args.list_functions:
        print("\n可用功能列表:")
        print("=" * 70)
        for func_id, config in sorted(FUNCTION_CONFIGS.items()):
            sessions = ", ".join(sorted(config.applicable_sessions)) if config.applicable_sessions else "N/A"
            print(f"  F{func_id:3d} - {config.name:30s} | Sessions: {sessions}")
        print("=" * 70)
        return
    
    # 確認 year 參數
    if not args.year:
        print("[ERROR] 必須指定 -y/--year 參數")
        sys.exit(1)
    
    # 確定賽事列表
    if args.all_races:
        races = get_season_races(args.year)
        if not races:
            print(f"[ERROR] 無法獲取 {args.year} 賽季列表")
            sys.exit(1)
        print(f"[INFO] 找到 {len(races)} 場賽事: {', '.join(races[:5])}...")
    elif args.races:
        races = args.races
    else:
        print("[ERROR] 必須指定 -r/--race 或 --all-races")
        sys.exit(1)
    
    # 生成任務
    tasks = generate_tasks(args.year, races, args.functions)
    print(f"\n[INFO] 總計 {len(tasks)} 個任務待處理")
    
    if args.dry_run:
        print("[INFO] DRY RUN 模式 - 不會實際執行")
    
    # 統計
    results = {
        "success": 0,
        "skipped": 0,
        "failed": 0,
        "no_session": 0,
        "dry_run": 0
    }
    failed_tasks = []
    
    # 執行任務
    if tqdm:
        iterator = tqdm(tasks, desc="Processing", unit="task")
    else:
        iterator = tasks
        print("\n開始處理...")
    
    for i, task in enumerate(iterator):
        if not tqdm:
            print(f"  [{i+1}/{len(tasks)}] F{task['function_id']} - {task['race']} {task['session']}", end=" ")
        
        result = execute_task(task, dry_run=args.dry_run)
        results[result.status] += 1
        
        if result.status == "failed":
            failed_tasks.append(result)
        
        if not tqdm:
            status_symbol = {
                "success": "[OK]",
                "skipped": "[SKIP]",
                "failed": "[FAIL]",
                "no_session": "[N/A]",
                "dry_run": "[DRY]"
            }
            print(status_symbol.get(result.status, "[?]"))
    
    # 輸出結果
    print("\n" + "=" * 60)
    print("執行結果摘要")
    print("=" * 60)
    print(f"  成功生成: {results['success']}")
    print(f"  已存在跳過: {results['skipped']}")
    print(f"  Session 不存在: {results['no_session']}")
    print(f"  執行失敗: {results['failed']}")
    if args.dry_run:
        print(f"  待執行 (dry run): {results['dry_run']}")
    print("=" * 60)
    
    # 輸出失敗任務
    if failed_tasks:
        print("\n失敗任務詳情:")
        print("-" * 60)
        for task in failed_tasks:
            print(f"  F{task.function_id} {task.race} {task.session}: {task.message}")
        print("-" * 60)
    
    # 返回碼
    if results["failed"] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
