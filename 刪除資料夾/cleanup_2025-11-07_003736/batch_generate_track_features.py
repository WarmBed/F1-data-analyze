#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
批量生成賽道特徵數據
Batch Generate Track Feature Data

用途：
- 批量執行 CLI 功能 48, 54, 34, 17, 1
- 為 133 場賽事生成必要的特徵 JSON
- 支援斷點續傳（已存在的 JSON 自動跳過）

執行方式:
    python batch_generate_track_features.py
    
作者: F1 Analysis Team
創建日期: 2025-10-31
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime
import time
import sys
import pandas as pd

# 啟用 FastF1 緩存
import fastf1
fastf1.Cache.enable_cache('f1_analysis_cache')


class TrackFeatureBatchGenerator:
    """批量生成賽道特徵數據的管理器"""
    
    def __init__(self):
        self.json_dir = Path("json")
        
        # 定義需要執行的 CLI 功能（使用實際 CLI 輸出的檔名模式）
        self.functions = {
            48: {
                "name": "全車手直線速度",
                "json_pattern": "all_drivers_straight_line_speed_{year}_{race}_{session}.json"
            },
            54: {
                "name": "車手油門比例",
                "json_pattern": "throttle_ratio_{year}_{race}_{session}.json"
            },
            34: {
                "name": "煞車性能分析",
                "json_pattern": "brake_performance_{year}_{race}_{session}.json"
            },
            47: {
                "name": "所有車手彎道分析",
                "json_pattern": "all_drivers_cornering_analysis_{year}_{race}_{session}.json"
            },
            1: {
                "name": "降雨強度分析",
                "json_pattern": "enhanced_rain_analysis_{year}_{race}_{session}.json"
            }
        }
        
        self.stats = {
            "total_tasks": 0,
            "completed": 0,
            "skipped": 0,
            "failed": 0,
            "start_time": None,
            "end_time": None
        }
    
    def get_race_schedule(self, year_range=(2018, 2024)):
        """獲取所有賽事的賽程"""
        all_races = []
        
        print(" 載入賽事賽程...")
        
        for year in range(year_range[0], year_range[1] + 1):
            try:
                schedule = fastf1.get_event_schedule(year)
                
                for idx, event in schedule.iterrows():
                    race_name = event['EventName']
                    round_number = event['RoundNumber']
                    
                    # 跳過測試賽和其他非正式賽事
                    if pd.isna(round_number) or event['EventFormat'] == 'testing':
                        continue
                    
                    # 標準化賽道名稱
                    normalized_name = self._normalize_race_name(race_name)
                    
                    all_races.append({
                        'year': year,
                        'race': normalized_name,
                        'round': int(round_number),
                        'original_name': race_name
                    })
                
                print(f"   {year}: {len([r for r in all_races if r['year'] == year])} 場賽事")
                
            except Exception as e:
                print(f" 無法載入 {year} 賽程: {e}")
                continue
        
        print(f"\n 共載入 {len(all_races)} 場賽事")
        return all_races
    
    def _normalize_race_name(self, race_name):
        """標準化賽道名稱（與 CLI 一致）"""
        # 移除 "Grand Prix" 後綴
        name = race_name.replace(' Grand Prix', '').strip()
        
        # 特殊情況映射
        mappings = {
            'Emilia Romagna': 'Emilia_Romagna',
            'Great Britain': 'Great_Britain',
            'Saudi Arabia': 'Saudi_Arabia',
            'United States': 'United_States',
            'Abu Dhabi': 'Abu_Dhabi',
            'Las Vegas': 'Las_Vegas'
        }
        
        return mappings.get(name, name)
    
    def check_json_exists(self, function_id, year, race, session):
        """檢查 JSON 檔案是否已存在（不區分大小寫，支援多種檔名格式）"""
        pattern = self.functions[function_id]["json_pattern"]
        
        # 嘗試多種可能的檔名格式
        possible_filenames = [
            pattern.format(year=year, race=race, session=session),           # 原始大小寫
            pattern.format(year=year, race=race.lower(), session=session),   # 小寫賽事名
            pattern.format(year=year, race=race.title(), session=session),   # 標題格式
            pattern.format(year=year, race=race.replace(' ', '_'), session=session),  # 底線替換空格
        ]
        
        # 搜索所有子目錄（不區分大小寫）
        for json_file in self.json_dir.rglob("*.json"):
            for possible_name in possible_filenames:
                if json_file.name.lower() == possible_name.lower():
                    return True, json_file
        
        return False, None
    
    def execute_cli_function(self, function_id, year, race, session):
        """執行單個 CLI 功能"""
        function_name = self.functions[function_id]["name"]
        
        try:
            # 構建命令
            cmd = [
                "python",
                "f1_analysis_modular_main.py",
                "-f", str(function_id),
                "-y", str(year),
                "-r", race,
                "-s", session
            ]
            
            print(f"   執行: {' '.join(cmd)}")
            
            # 執行命令（設置超時 5 分鐘）
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                encoding='utf-8',
                errors='replace'
            )
            
            # 檢查 JSON 檔案是否成功生成（比返回碼更可靠）
            # 等待檔案寫入完成
            time.sleep(0.5)
            
            json_exists, json_path = self.check_json_exists(function_id, year, race, session)
            if json_exists:
                print(f"    {function_name} 執行成功（JSON 已生成）")
                return True
            else:
                # 只有在 JSON 不存在且有實際錯誤時才報錯
                if result.returncode != 0 and result.stderr and "UserWarning" not in result.stderr:
                    # 忽略 FastF1 的 UserWarning
                    print(f"    {function_name} 執行失敗 (返回碼: {result.returncode})")
                    print(f"      錯誤: {result.stderr[:200]}")
                else:
                    print(f"   ️  {function_name} 執行完成但未找到 JSON（可能檔案位置不同）")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"   ⏱️  {function_name} 超時（超過 5 分鐘）")
            return False
        except Exception as e:
            print(f"    {function_name} 執行異常: {e}")
            return False
    
    def generate_all_features(self):
        """批量生成所有賽道特徵"""
        import pandas as pd
        
        print("\n" + "=" * 80)
        print(" 批量生成賽道特徵數據")
        print("=" * 80)
        
        self.stats["start_time"] = datetime.now()
        
        # 1. 獲取賽事列表
        races = self.get_race_schedule()
        
        # 只分析 FP3 會話（最接近正賽狀態）
        session = "FP3"
        
        # 計算總任務數
        self.stats["total_tasks"] = len(races) * len(self.functions)
        
        print(f"\n 任務統計:")
        print(f"   - 賽事數量: {len(races)}")
        print(f"   - 功能數量: {len(self.functions)}")
        print(f"   - 總任務數: {self.stats['total_tasks']}")
        print(f"   - 會話類型: {session}")
        
        # 2. 逐個賽事執行
        for idx, race_info in enumerate(races, 1):
            year = race_info['year']
            race = race_info['race']
            
            print(f"\n{'=' * 80}")
            print(f"[{idx}/{len(races)}] 處理: {year} {race_info['original_name']} ({race})")
            print("=" * 80)
            
            # 對每個功能檢查和執行
            for func_id, func_info in self.functions.items():
                print(f"\n 功能 {func_id}: {func_info['name']}")
                
                # 檢查 JSON 是否已存在
                exists, json_path = self.check_json_exists(func_id, year, race, session)
                
                if exists:
                    print(f"   ⏭️  已存在，跳過: {json_path.name}")
                    self.stats["skipped"] += 1
                    continue
                
                # 執行 CLI 功能
                success = self.execute_cli_function(func_id, year, race, session)
                
                if success:
                    self.stats["completed"] += 1
                    
                    # 驗證 JSON 是否成功生成
                    time.sleep(1)  # 等待檔案寫入
                    exists, json_path = self.check_json_exists(func_id, year, race, session)
                    
                    if exists:
                        print(f"    JSON 已生成: {json_path.name}")
                    else:
                        print(f"   ️  CLI 返回成功但未找到 JSON 檔案")
                        self.stats["failed"] += 1
                        self.stats["completed"] -= 1
                else:
                    self.stats["failed"] += 1
                
                # 進度報告
                total_processed = self.stats["completed"] + self.stats["skipped"] + self.stats["failed"]
                progress = (total_processed / self.stats["total_tasks"]) * 100
                print(f"\n 進度: {total_processed}/{self.stats['total_tasks']} ({progress:.1f}%)")
                print(f"   完成: {self.stats['completed']}, 跳過: {self.stats['skipped']}, 失敗: {self.stats['failed']}")
                
                # 避免 API 限流
                time.sleep(2)
        
        self.stats["end_time"] = datetime.now()
        self._print_final_report()
    
    def _print_final_report(self):
        """輸出最終報告"""
        print("\n" + "=" * 80)
        print(" 最終統計報告")
        print("=" * 80)
        
        duration = self.stats["end_time"] - self.stats["start_time"]
        hours = duration.total_seconds() / 3600
        
        print(f"⏱️  總耗時: {hours:.2f} 小時")
        print(f" 總任務: {self.stats['total_tasks']}")
        print(f" 成功: {self.stats['completed']}")
        print(f"⏭️  跳過: {self.stats['skipped']}")
        print(f" 失敗: {self.stats['failed']}")
        
        success_rate = (self.stats['completed'] / self.stats['total_tasks']) * 100 if self.stats['total_tasks'] > 0 else 0
        print(f"\n 成功率: {success_rate:.1f}%")
        
        print("\n" + "=" * 80)


def main():
    """主程式"""
    generator = TrackFeatureBatchGenerator()
    
    try:
        generator.generate_all_features()
    except KeyboardInterrupt:
        print("\n\n️  使用者中斷執行")
        print(" 當前進度:")
        total_processed = generator.stats["completed"] + generator.stats["skipped"] + generator.stats["failed"]
        print(f"   已處理: {total_processed}/{generator.stats['total_tasks']}")
        print(f"   完成: {generator.stats['completed']}, 跳過: {generator.stats['skipped']}, 失敗: {generator.stats['failed']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
