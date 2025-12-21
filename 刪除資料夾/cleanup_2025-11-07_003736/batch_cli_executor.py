#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
F1 分析 CLI 批量執行器
====================
功能：批量執行任意 CLI 功能，支援自定義功能列表、年份範圍和會話類型
作者：F1T Analysis Team
日期：2025-10-31
版本：1.0.0

使用範例：
    # 批量執行功能 48, 54, 34, 47, 1（賽道特徵相關）
    python batch_cli_executor.py --functions 48,54,34,47,1 --years 2018-2024 --sessions FP3
    
    # 批量執行功能 70（FP→Q 數據收集）
    python batch_cli_executor.py --functions 70 --years 2018-2024
    
    # 批量執行功能 72（XGBoost 訓練）
    python batch_cli_executor.py --functions 72 --years 2018-2023
"""

import os
import sys
import subprocess
import argparse
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# 確保在專案根目錄執行
if not Path("f1_analysis_modular_main.py").exists():
    print("[ERROR] 請在專案根目錄執行此腳本")
    sys.exit(1)

# 嘗試導入 tqdm 進度條
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("[INFO] 安裝 tqdm 可獲得更好的進度條體驗: pip install tqdm")
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
        percent = (self.current / self.total) * 100 if self.total > 0 else 0
        elapsed = time.time() - self.start_time
        eta = (elapsed / self.current * (self.total - self.current)) if self.current > 0 else 0
        
        bar_length = 40
        filled_length = int(bar_length * self.current / self.total) if self.total > 0 else 0
        bar = '#' * filled_length + '-' * (bar_length - filled_length)
        
        print(f"\r{self.desc} |{bar}| {self.current}/{self.total} [{percent:.1f}%] "
              f"ETA: {eta:.0f}s", end='', flush=True)
    
    def close(self):
        print()  # 換行


class BatchCLIExecutor:
    """批量 CLI 執行器"""
    
    # 功能 ID 到 JSON 檔名模式的映射
    FUNCTION_JSON_PATTERNS = {
        1:  "enhanced_rain_analysis_{year}_{race}_{session}.json",
        34: "brake_performance_{year}_{race}_{session}.json",
        47: "all_drivers_cornering_analysis_{year}_{race}_{session}.json",
        48: "all_drivers_straight_line_speed_{year}_{race}_{session}.json",
        54: "driver_throttle_ratio_{year}_{race}_{session}.json",  # 已更新為統一命名格式
        70: "fp_q_data_{year}_{race}.json",
        72: "xgboost_fp_q_baseline*.pkl",  # 模型檔案
    }
    
    # 功能名稱映射
    FUNCTION_NAMES = {
        1:  "降雨強度分析",
        34: "煞車性能分析",
        47: "全車手彎道分析",
        48: "全車手直線速度",
        54: "車手油門比例",
        70: "FP→Q 數據收集",
        72: "XGBoost 訓練",
    }
    
    def __init__(self, functions: List[int], years: List[int], 
                 sessions: List[str], skip_existing: bool = True,
                 verbose: bool = False):
        """
        初始化批量執行器
        
        Args:
            functions: 功能 ID 列表
            years: 年份列表
            sessions: 會話類型列表（如 ['R', 'Q', 'FP3']）
            skip_existing: 是否跳過已存在的 JSON 檔案
            verbose: 是否顯示詳細輸出
        """
        self.functions = functions
        self.years = years
        self.sessions = sessions
        self.skip_existing = skip_existing
        self.verbose = verbose
        
        self.json_dir = Path("json")
        self.models_dir = Path("models")
        
        # 統計計數器
        self.success_count = 0
        self.fail_count = 0
        self.skip_count = 0
        
        # 衝刺賽週末列表（沒有 FP3，用 FP1 替代）
        self.sprint_weekends = {
            2020: ["Emilia Romagna"],
            2021: ["Great Britain", "Italy", "Brazil"],
            2022: ["Emilia Romagna", "Austria", "Brazil"],
            2023: ["Azerbaijan", "Austria", "Belgium", "Qatar", "United States", "Brazil"],
            2024: ["China", "Miami", "Austria", "United States", "Brazil", "Qatar"],
        }
        
    def is_sprint_weekend(self, year: int, race: str) -> bool:
        """檢查是否為衝刺賽週末"""
        return race in self.sprint_weekends.get(year, [])
    
    def get_fallback_session(self, year: int, race: str, requested_session: str) -> str:
        """
        為衝刺賽週末獲取替代會話
        
        Args:
            year: 年份
            race: 賽事名稱
            requested_session: 請求的會話類型
            
        Returns:
            替代會話類型（如 FP1）或原始會話
        """
        if requested_session == "FP3" and self.is_sprint_weekend(year, race):
            return "FP1"  # 衝刺週末用 FP1 替代 FP3
        return requested_session
        
    def get_race_calendar(self, year: int) -> List[str]:
        """獲取指定年份的賽事列表"""
        # 嘗試從 race_calendar.py 導入
        try:
            from CLI_modules.cli.prediction.race_calendar import RACE_CALENDAR
            return RACE_CALENDAR.get(year, [])
        except ImportError:
            print(f"[WARNING] 無法導入 race_calendar，使用預設賽事列表")
            # 使用通用的賽事列表
            return [
                "Australia", "Bahrain", "China", "Japan", "Saudi Arabia",
                "Miami", "Emilia Romagna", "Monaco", "Spain", "Canada",
                "Austria", "Great Britain", "Belgium", "Hungary", "Netherlands",
                "Italy", "Azerbaijan", "Singapore", "United States", "Mexico",
                "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
            ]
    
    def check_json_exists(self, func_id: int, year: int, 
                          race: Optional[str] = None, 
                          session: Optional[str] = None) -> Tuple[bool, Optional[Path]]:
        """
        檢查 JSON 檔案是否已存在
        
        Returns:
            (exists: bool, file_path: Optional[Path])
        """
        pattern = self.FUNCTION_JSON_PATTERNS.get(func_id)
        if not pattern:
            return False, None
        
        # 格式化模式
        if race and session:
            search_pattern = pattern.format(year=year, race=race, session=session)
        elif race:
            search_pattern = pattern.format(year=year, race=race)
        else:
            search_pattern = pattern.format(year=year)
        
        # 搜索檔案（支援多種變體：大小寫、空格/底線）
        search_dirs = [self.json_dir, self.models_dir, Path("reports")]
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
                
            # 嘗試多種檔名變體
            variants = [
                search_pattern,
                search_pattern.lower(),
                search_pattern.replace(' ', '_'),
                search_pattern.replace('_', ' '),
            ]
            
            for variant in variants:
                matches = list(search_dir.rglob(variant))
                if matches:
                    return True, matches[0]
        
        return False, None
    
    def run_cli_function(self, func_id: int, year: int, 
                         race: Optional[str] = None,
                         session: Optional[str] = None) -> Tuple[bool, str]:
        """
        執行單個 CLI 功能
        
        Returns:
            (success: bool, message: str)
        """
        cmd = [
            sys.executable,
            "f1_analysis_modular_main.py",
            "-f", str(func_id),
            "-y", str(year)
        ]
        
        if race:
            cmd.extend(["-r", race])
        if session:
            cmd.extend(["-s", session])
        
        try:
            if self.verbose:
                # 顯示詳細輸出
                result = subprocess.run(
                    cmd,
                    check=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    timeout=600  # 10 分鐘超時
                )
                
                if result.returncode != 0 and "UserWarning" not in result.stdout:
                    return False, f"執行失敗 (返回碼: {result.returncode})"
            else:
                # 靜默執行
                result = subprocess.run(
                    cmd,
                    check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=600
                )
                
                if result.returncode != 0:
                    return False, f"執行失敗 (返回碼: {result.returncode})"
            
            # 等待檔案寫入完成
            time.sleep(0.5)
            
            # 檢查 JSON/模型是否生成
            exists, file_path = self.check_json_exists(func_id, year, race, session)
            if exists:
                return True, f"成功 ({file_path.name if file_path else 'OK'})"
            else:
                return False, "檔案未生成"
                
        except subprocess.TimeoutExpired:
            return False, "超時（> 10 分鐘）"
        except Exception as e:
            return False, f"異常: {str(e)}"
    
    def build_tasks(self) -> List[Dict]:
        """建立任務列表"""
        tasks = []
        
        for func_id in self.functions:
            func_name = self.FUNCTION_NAMES.get(func_id, f"功能 {func_id}")
            
            for year in self.years:
                races = self.get_race_calendar(year)
                
                # 某些功能不需要指定賽事（如 F72 訓練）
                if func_id in [72]:
                    tasks.append({
                        "func_id": func_id,
                        "func_name": func_name,
                        "year": year,
                        "race": None,
                        "session": None
                    })
                else:
                    for race in races:
                        for session in self.sessions:
                            # 為衝刺賽週末自動切換會話
                            actual_session = self.get_fallback_session(year, race, session)
                            tasks.append({
                                "func_id": func_id,
                                "func_name": func_name,
                                "year": year,
                                "race": race,
                                "session": actual_session,
                                "original_session": session if actual_session != session else None
                            })
        
        return tasks
    
    def execute(self):
        """執行批量任務"""
        print("=" * 80)
        print("  F1 分析 CLI 批量執行器")
        print("=" * 80)
        print()
        
        # 建立任務列表
        tasks = self.build_tasks()
        total_tasks = len(tasks)
        
        print(f"執行計畫：")
        print(f"  - 功能列表：{', '.join([f'F{f}' for f in self.functions])}")
        print(f"  - 年份範圍：{min(self.years)}-{max(self.years)}")
        print(f"  - 會話類型：{', '.join(self.sessions)}")
        print(f"  - 總任務數：{total_tasks}")
        print(f"  - 跳過已存在：{'是' if self.skip_existing else '否'}")
        print()
        
        # 開始計時
        start_time = time.time()
        
        # 選擇進度條
        if HAS_TQDM:
            progress_bar = tqdm(tasks, desc="總進度", unit="任務")
        else:
            progress_bar = SimpleProgressBar(len(tasks), "總進度")
        
        # 執行每個任務
        for task in (progress_bar if HAS_TQDM else tasks):
            if not HAS_TQDM:
                progress_bar.update(1)
            
            func_id = task["func_id"]
            func_name = task["func_name"]
            year = task["year"]
            race = task["race"]
            session = task["session"]
            original_session = task.get("original_session")
            
            # 顯示當前任務（包含會話替換資訊）
            if race and session:
                if original_session:
                    task_desc = f"[F{func_id:2d}] {year} {race:20s} {session:3s} (替代 {original_session})"
                else:
                    task_desc = f"[F{func_id:2d}] {year} {race:20s} {session:3s}"
            elif race:
                task_desc = f"[F{func_id:2d}] {year} {race:20s}"
            else:
                task_desc = f"[F{func_id:2d}] {year}"
            
            if HAS_TQDM:
                progress_bar.set_description(task_desc)
            else:
                if self.verbose:
                    print(f"\n{task_desc}")
            
            # 檢查是否已存在
            if self.skip_existing:
                exists, file_path = self.check_json_exists(func_id, year, race, session)
                if exists:
                    if self.verbose:
                        print(f"  [SKIP] 已存在：{file_path.name if file_path else 'OK'}")
                    self.skip_count += 1
                    continue
            
            # 執行分析
            success, message = self.run_cli_function(func_id, year, race, session)
            
            if success:
                if self.verbose:
                    print(f"  [OK] {message}")
                self.success_count += 1
            else:
                if self.verbose:
                    print(f"  [FAIL] {message}")
                else:
                    print(f"\n{task_desc} - [FAIL] {message}")
                self.fail_count += 1
            
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
        print("=" * 80)
        print("  執行完成")
        print("=" * 80)
        print()
        print("統計資訊：")
        print(f"  - [OK]   成功：{self.success_count} 個任務")
        print(f"  - [FAIL] 失敗：{self.fail_count} 個任務")
        print(f"  - [SKIP] 跳過：{self.skip_count} 個任務（已存在）")
        print(f"  - [TOTAL] 總計：{total_tasks} 個任務")
        print()
        print(f"執行時間：{duration:.1f} 秒 ({duration/60:.1f} 分鐘)")
        print()
        
        return self.fail_count == 0


def parse_arguments():
    """解析命令列參數"""
    parser = argparse.ArgumentParser(
        description="F1 分析 CLI 批量執行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例：
  # 批量執行賽道特徵相關功能（F48, F54, F34, F47, F1）
  python batch_cli_executor.py --functions 48,54,34,47,1 --years 2018-2024 --sessions FP3
  
  # 批量收集 FP→Q 數據（功能 70）
  python batch_cli_executor.py --functions 70 --years 2018-2024
  
  # 批量訓練 XGBoost 模型（功能 72）
  python batch_cli_executor.py --functions 72 --years 2018-2023
  
  # 多功能批量執行
  python batch_cli_executor.py --functions 1,34,47,48,54 --years 2023,2024 --sessions R,Q,FP3 --verbose
        """
    )
    
    parser.add_argument(
        "--functions", "-f",
        required=True,
        help="功能 ID 列表（逗號分隔），例如：48,54,34,47,1"
    )
    
    parser.add_argument(
        "--years", "-y",
        required=True,
        help="年份範圍（格式：2018-2024 或 2023,2024）"
    )
    
    parser.add_argument(
        "--sessions", "-s",
        default="R,Q,FP3",
        help="會話類型列表（逗號分隔），預設：R,Q,FP3"
    )
    
    parser.add_argument(
        "--no-skip",
        action="store_true",
        help="不跳過已存在的檔案（強制重新執行）"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="顯示詳細輸出"
    )
    
    return parser.parse_args()


def parse_range(range_str: str) -> List[int]:
    """
    解析範圍字串
    
    支援格式：
        - "2018-2024" → [2018, 2019, 2020, 2021, 2022, 2023, 2024]
        - "2023,2024" → [2023, 2024]
    """
    if '-' in range_str:
        start, end = map(int, range_str.split('-'))
        return list(range(start, end + 1))
    else:
        return [int(x.strip()) for x in range_str.split(',')]


def main():
    """主函數"""
    args = parse_arguments()
    
    # 解析功能列表
    functions = [int(x.strip()) for x in args.functions.split(',')]
    
    # 解析年份範圍
    years = parse_range(args.years)
    
    # 解析會話類型
    sessions = [x.strip() for x in args.sessions.split(',')]
    
    # 創建執行器
    executor = BatchCLIExecutor(
        functions=functions,
        years=years,
        sessions=sessions,
        skip_existing=not args.no_skip,
        verbose=args.verbose
    )
    
    # 執行批量任務
    success = executor.execute()
    
    # 返回退出碼
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARNING] 用戶中斷執行")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n[ERROR] 錯誤：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
