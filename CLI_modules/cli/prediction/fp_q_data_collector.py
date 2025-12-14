#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
功能 70: FP->Q 預測訓練數據收集器
目的: 提取 FP1/FP2/FP3 和 Q 的數據用於機器學習訓練

根據開發原則:
- 原則 0: 禁止幻覺編碼 - 所有數據來源已驗證 (FastF1 API)
- 原則 1: 模組資料夾優先 - 置於 CLI_modules/cli/prediction/
- 原則 2: 通用模組優先 - 遵循 CLI 標準架構
- 原則 3: 多國語言化 - 使用 tr() 包裹字串 (CLI 模式暫不實現)
- 原則 4: print 輸出導向 logger

版本: 1.0.0
作者: F1T Development Team
日期: 2025-10-29
"""

import os
import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import json
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

# 添加專案根目錄到 Python 路徑
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    import fastf1
    from fastf1 import plotting
except ImportError:
    print("❌ 錯誤: 無法導入 fastf1，請執行 'pip install fastf1'")
    sys.exit(1)


class FPQDataCollector:
    """
    FP→Q 預測訓練數據收集器
    
    功能:
    1. 提取 FP1/FP2/FP3 的圈速數據
    2. 提取 Q 的結果數據
    3. 提取天氣數據
    4. 提取輪胎數據
    5. 導出為結構化 JSON 格式
    
    數據來源: FastF1 API (已驗證可用)
    """
    
    def __init__(self, cache_dir: str = "f1_analysis_cache"):
        """
        初始化數據收集器
        
        Args:
            cache_dir: FastF1 緩存目錄
        """
        self.cache_dir = cache_dir
        fastf1.Cache.enable_cache(cache_dir)
        
        # 輸出目錄
        self.output_dir = os.path.join(project_root, "json", "predictionJSON")
        os.makedirs(self.output_dir, exist_ok=True)
        
        print(f"✅ FPQDataCollector 初始化完成")
        print(f"📁 輸出目錄: {self.output_dir}")
        print(f"💾 緩存目錄: {self.cache_dir}")
    
    def collect_single_race(
        self, 
        year: int, 
        race: str, 
        include_fp1: bool = True,
        include_fp2: bool = True,
        include_fp3: bool = True
    ) -> Dict[str, Any]:
        """
        收集單場賽事的 FP→Q 數據
        
        Args:
            year: 賽季年份
            race: 賽事名稱或編號
            include_fp1: 是否包含 FP1 數據
            include_fp2: 是否包含 FP2 數據
            include_fp3: 是否包含 FP3 數據
            
        Returns:
            包含所有數據的字典
        """
        print(f"\n{'='*60}")
        print(f"📊 開始收集: {year} {race}")
        print(f"{'='*60}")
        
        data = {
            "metadata": {
                "year": year,
                "race": race,
                "collection_timestamp": datetime.now().isoformat(),
                "fastf1_version": fastf1.__version__,
                "data_source": "FastF1 API"
            },
            "practice_sessions": {},
            "qualifying": {},
            "drivers": []
        }
        
        try:
            # 1. 載入 Q 數據 (必須)
            print("\n[1/2] 正在載入排位賽數據...")
            q_session = fastf1.get_session(year, race, 'Q')
            q_session.load()
            
            if q_session.results is None or len(q_session.results) == 0:
                print("⚠️  排位賽數據不可用，跳過此賽事")
                return None
            
            print(f"✅ 排位賽數據載入完成: {len(q_session.results)} 位車手")
            
            # 2. 載入 FP 數據
            print("\n[2/2] 正在載入練習賽數據...")
            fp_sessions = {}
            
            if include_fp1:
                try:
                    fp1 = fastf1.get_session(year, race, 'FP1')
                    fp1.load()
                    if fp1.laps is not None and len(fp1.laps) > 0:
                        fp_sessions['FP1'] = fp1
                        print(f"✅ FP1 數據載入完成: {len(fp1.laps)} 圈")
                except Exception as e:
                    print(f"⚠️  FP1 數據不可用: {str(e)[:50]}")
            
            if include_fp2:
                try:
                    fp2 = fastf1.get_session(year, race, 'FP2')
                    fp2.load()
                    if fp2.laps is not None and len(fp2.laps) > 0:
                        fp_sessions['FP2'] = fp2
                        print(f"✅ FP2 數據載入完成: {len(fp2.laps)} 圈")
                except Exception as e:
                    print(f"⚠️  FP2 數據不可用: {str(e)[:50]}")
            
            if include_fp3:
                # 先嘗試 FP3
                fp3_loaded = False
                try:
                    fp3 = fastf1.get_session(year, race, 'FP3')
                    fp3.load()
                    if fp3.laps is not None and len(fp3.laps) > 0:
                        fp_sessions['FP3'] = fp3
                        print(f"✅ FP3 數據載入完成: {len(fp3.laps)} 圈")
                        fp3_loaded = True
                except Exception as e:
                    print(f"⚠️  FP3 數據不可用: {str(e)[:50]}")
                
                # 如果 FP3 失敗，嘗試使用衝刺排位賽（SQ）或衝刺賽（S）
                if not fp3_loaded:
                    print("  [衝刺賽週末] 嘗試使用衝刺賽數據代替 FP3...")
                    
                    # 優先使用 Sprint Qualifying (SQ)
                    try:
                        sprint_q = fastf1.get_session(year, race, 'SQ')
                        sprint_q.load()
                        if sprint_q.laps is not None and len(sprint_q.laps) > 0:
                            fp_sessions['FP3'] = sprint_q  # 命名為 FP3 以保持兼容性
                            print(f"✅ 衝刺排位賽（SQ）數據載入完成: {len(sprint_q.laps)} 圈")
                            fp3_loaded = True
                    except Exception as e:
                        print(f"  ⚠️  SQ 不可用: {str(e)[:50]}")
                    
                    # 如果 SQ 也失敗，使用 Sprint Race (S)
                    if not fp3_loaded:
                        try:
                            sprint = fastf1.get_session(year, race, 'S')
                            sprint.load()
                            if sprint.laps is not None and len(sprint.laps) > 0:
                                fp_sessions['FP3'] = sprint  # 命名為 FP3 以保持兼容性
                                print(f"✅ 衝刺賽（S）數據載入完成: {len(sprint.laps)} 圈")
                                fp3_loaded = True
                        except Exception as e:
                            print(f"  ⚠️  Sprint 不可用: {str(e)[:50]}")
                    
                    if not fp3_loaded:
                        print("  ❌ 無法載入 FP3/SQ/S 數據")
            
            if len(fp_sessions) == 0:
                print("⚠️  沒有可用的練習賽數據，跳過此賽事")
                return None
            
            # 3. 提取 Q 結果
            print("\n[3/4] 正在提取排位賽結果...")
            data["qualifying"] = self._extract_qualifying_results(q_session)
            print(f"✅ 提取了 {len(data['qualifying']['results'])} 位車手的排位賽結果")
            
            # 4. 提取 FP 數據
            print("\n[4/4] 正在提取練習賽數據...")
            for session_name, session in fp_sessions.items():
                print(f"  - 處理 {session_name}...")
                data["practice_sessions"][session_name] = self._extract_practice_session(session)
            
            # 5. 建立車手列表
            data["drivers"] = sorted(list(set(data["qualifying"]["results"].keys())))
            
            print(f"\n✅ 數據收集完成")
            print(f"   - 練習賽會話: {', '.join(fp_sessions.keys())}")
            print(f"   - 車手數量: {len(data['drivers'])}")
            
            return data
            
        except Exception as e:
            print(f"\n❌ 收集數據時發生錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_qualifying_results(self, q_session) -> Dict[str, Any]:
        """
        提取排位賽結果
        
        Args:
            q_session: FastF1 排位賽 Session 物件
            
        Returns:
            包含排位賽結果的字典
        """
        q_data = {
            "session_info": {
                "event_name": q_session.event['EventName'],
                "circuit": q_session.event['Location'],
                "country": q_session.event['Country'],
                "date": q_session.date.isoformat() if hasattr(q_session.date, 'isoformat') else str(q_session.date)
            },
            "weather": self._extract_weather(q_session),
            "results": {}
        }
        
        # 提取每位車手的結果
        for idx, row in q_session.results.iterrows():
            driver = row['Abbreviation']
            
            q_data["results"][driver] = {
                "position": int(row['Position']) if pd.notna(row['Position']) else None,
                "q1_time": str(row['Q1']) if pd.notna(row['Q1']) else None,
                "q2_time": str(row['Q2']) if pd.notna(row['Q2']) else None,
                "q3_time": str(row['Q3']) if pd.notna(row['Q3']) else None,
                "best_time": str(row['Q3']) if pd.notna(row['Q3']) else (
                    str(row['Q2']) if pd.notna(row['Q2']) else (
                        str(row['Q1']) if pd.notna(row['Q1']) else None
                    )
                ),
                "team": row['TeamName'],
                "team_color": row['TeamColor'] if 'TeamColor' in row else None
            }
        
        return q_data
    
    def _extract_practice_session(self, fp_session) -> Dict[str, Any]:
        """
        提取練習賽數據
        
        Args:
            fp_session: FastF1 練習賽 Session 物件
            
        Returns:
            包含練習賽數據的字典
        """
        fp_data = {
            "session_info": {
                "session_name": fp_session.name,
                "date": fp_session.date.isoformat() if hasattr(fp_session.date, 'isoformat') else str(fp_session.date)
            },
            "weather": self._extract_weather(fp_session),
            "driver_data": {}
        }
        
        # 提取每位車手的數據
        for driver in fp_session.laps['Driver'].unique():
            driver_laps = fp_session.laps.pick_driver(driver)
            
            if len(driver_laps) == 0:
                continue
            
            # 過濾有效圈速 (排除 pit lap, out lap)
            valid_laps = driver_laps[
                (driver_laps['LapTime'].notna()) & 
                (~driver_laps['IsAccurate'] | driver_laps['IsAccurate'])  # 包含所有圈
            ]
            
            if len(valid_laps) == 0:
                continue
            
            # 計算統計數據（使用所有有效圈）
            lap_times = valid_laps['LapTime'].dt.total_seconds()
            
            # 🆕 階段 1：全圈分析特徵
            # 找出最速圈
            fastest_lap_time = float(lap_times.min()) if len(lap_times) > 0 else None
            
            # 所有圈的平均時間
            all_laps_mean = float(lap_times.mean()) if len(lap_times) > 0 else None
            
            # 所有圈的標準差（一致性指標）
            all_laps_std = float(lap_times.std()) if len(lap_times) > 0 else None
            
            # 長距離模擬（連續 10+ 圈，模擬正賽）
            race_sim_laps = []
            race_sim_degradation = None
            if len(valid_laps) >= 10:
                # 找最長的連續圈數序列（輪胎壽命連續）
                for i in range(len(valid_laps) - 9):
                    consecutive_laps = valid_laps.iloc[i:i+10]
                    if (consecutive_laps['TyreLife'].notna().all() if 'TyreLife' in consecutive_laps.columns else True):
                        race_sim_laps = consecutive_laps['LapTime'].dt.total_seconds().tolist()
                        break
                
                # 計算圈速衰退率（第 10 圈 vs 第 1 圈）
                if len(race_sim_laps) >= 10:
                    race_sim_degradation = float((race_sim_laps[-1] - race_sim_laps[0]) / race_sim_laps[0] * 100)
            
            race_sim_avg = float(np.mean(race_sim_laps)) if len(race_sim_laps) >= 10 else None
            
            fp_data["driver_data"][driver] = {
                "total_laps": int(len(driver_laps)),
                "valid_laps": int(len(valid_laps)),
                
                # 原有特徵
                "best_lap_time": fastest_lap_time,
                "avg_lap_time": all_laps_mean,
                "lap_time_std": all_laps_std,
                
                # 🆕 全圈分析特徵
                "fastest_lap": fastest_lap_time,  # 明確標註為最速圈
                "all_laps_mean": all_laps_mean,   # 所有有效圈平均
                "all_laps_std": all_laps_std,     # 所有圈標準差（一致性）
                "race_sim_avg": race_sim_avg,     # 長距離模擬平均（10+ 圈）
                "race_sim_degradation": race_sim_degradation,  # 圈速衰退率 (%)
                
                "team": driver_laps.iloc[0]['Team'] if 'Team' in driver_laps.columns else None,
                
                # 扇區時間
                "sector1_best": float(valid_laps['Sector1Time'].dt.total_seconds().min()) if valid_laps['Sector1Time'].notna().any() else None,
                "sector2_best": float(valid_laps['Sector2Time'].dt.total_seconds().min()) if valid_laps['Sector2Time'].notna().any() else None,
                "sector3_best": float(valid_laps['Sector3Time'].dt.total_seconds().min()) if valid_laps['Sector3Time'].notna().any() else None,
                
                # 速度陷阱
                "speed_trap_max": float(valid_laps['SpeedST'].max()) if 'SpeedST' in valid_laps.columns and valid_laps['SpeedST'].notna().any() else None,
                
                # 輪胎數據
                "compounds_used": valid_laps['Compound'].dropna().unique().tolist() if 'Compound' in valid_laps.columns else [],
                "tire_age_avg": float(valid_laps['TyreLife'].mean()) if 'TyreLife' in valid_laps.columns and valid_laps['TyreLife'].notna().any() else None,
            }
        
        return fp_data
    
    def _extract_weather(self, session) -> Dict[str, Any]:
        """
        提取天氣數據
        
        Args:
            session: FastF1 Session 物件
            
        Returns:
            天氣數據字典
        """
        try:
            weather_data = session.weather_data
            
            if weather_data is None or len(weather_data) == 0:
                return {
                    "air_temp_avg": None,
                    "track_temp_avg": None,
                    "humidity_avg": None,
                    "rainfall": False
                }
            
            return {
                "air_temp_avg": float(weather_data['AirTemp'].mean()) if 'AirTemp' in weather_data.columns else None,
                "track_temp_avg": float(weather_data['TrackTemp'].mean()) if 'TrackTemp' in weather_data.columns else None,
                "humidity_avg": float(weather_data['Humidity'].mean()) if 'Humidity' in weather_data.columns else None,
                "rainfall": bool(weather_data['Rainfall'].any()) if 'Rainfall' in weather_data.columns else False
            }
        except Exception as e:
            print(f"⚠️  提取天氣數據失敗: {str(e)[:50]}")
            return {
                "air_temp_avg": None,
                "track_temp_avg": None,
                "humidity_avg": None,
                "rainfall": False
            }
    
    def collect_season(
        self, 
        year: int,
        start_race: int = 1,
        end_race: Optional[int] = None,
        include_fp1: bool = True,
        include_fp2: bool = True,
        include_fp3: bool = True
    ) -> List[Dict[str, Any]]:
        """
        收集整個賽季的數據
        
        Args:
            year: 賽季年份
            start_race: 起始賽事編號
            end_race: 結束賽事編號 (None = 全部)
            include_fp1: 是否包含 FP1
            include_fp2: 是否包含 FP2
            include_fp3: 是否包含 FP3
            
        Returns:
            數據列表
        """
        print(f"\n{'#'*60}")
        print(f"# 收集 {year} 賽季數據")
        print(f"# 起始賽事: {start_race}")
        print(f"# 結束賽事: {end_race if end_race else '全部'}")
        print(f"{'#'*60}")
        
        all_data = []
        race_num = start_race
        consecutive_failures = 0  # 連續失敗次數計數器
        MAX_CONSECUTIVE_FAILURES = 3  # 最多允許 3 次連續失敗
        
        while True:
            if end_race and race_num > end_race:
                break
            
            # 安全閥：防止無限循環（正常賽季最多 24 場）
            if race_num > 30:
                print(f"\n⚠️  警告：賽事編號超過 30，可能發生無限循環，強制停止")
                break
            
            try:
                data = self.collect_single_race(
                    year, 
                    race_num,
                    include_fp1=include_fp1,
                    include_fp2=include_fp2,
                    include_fp3=include_fp3
                )
                
                if data:
                    all_data.append(data)
                    consecutive_failures = 0  # 成功後重置計數器
                else:
                    print(f"⚠️  賽事 {race_num} 數據不完整，跳過")
                    consecutive_failures += 1
                
                race_num += 1
                
            except Exception as e:
                error_str = str(e)
                if "Invalid round" in error_str or "No matching round" in error_str or "cannot be found" in error_str:
                    print(f"\n✅ 達到賽季結束 (賽事 {race_num-1})")
                    break
                else:
                    print(f"❌ 賽事 {race_num} 發生錯誤: {str(e)[:100]}")
                    consecutive_failures += 1
                    
                    # 連續失敗 3 次，可能已超過賽季範圍
                    if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                        print(f"\n⚠️  連續 {MAX_CONSECUTIVE_FAILURES} 場賽事失敗，可能已達賽季結束")
                        break
                    
                    race_num += 1
                    continue
        
        print(f"\n{'#'*60}")
        print(f"# 收集完成: 成功收集 {len(all_data)} 場賽事")
        print(f"{'#'*60}")
        
        return all_data
    
    def save_to_json(self, data: Dict[str, Any], filename: Optional[str] = None) -> str:
        """
        儲存數據到 JSON 檔案
        
        Args:
            data: 要儲存的數據
            filename: 檔案名稱 (None = 自動生成)
            
        Returns:
            儲存的檔案路徑
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            year = data['metadata']['year']
            race = data['metadata']['race']
            filename = f"fp_q_data_{year}_{race}_{timestamp}.json"
        
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 數據已儲存: {filepath}")
        return filepath
    
    def save_season_to_json(self, season_data: List[Dict[str, Any]], year: int) -> str:
        """
        儲存整個賽季的數據到單一 JSON 檔案
        
        Args:
            season_data: 賽季數據列表
            year: 年份
            
        Returns:
            儲存的檔案路徑
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fp_q_season_{year}_{timestamp}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        output = {
            "metadata": {
                "year": year,
                "total_races": len(season_data),
                "collection_timestamp": timestamp,
                "fastf1_version": fastf1.__version__
            },
            "races": season_data
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 賽季數據已儲存: {filepath}")
        print(f"   - 檔案大小: {os.path.getsize(filepath) / 1024 / 1024:.2f} MB")
        
        return filepath


def main():
    """主函數 - CLI 入口"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="F1 FP→Q 預測訓練數據收集器 (功能 70)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # 收集單場賽事
  python -m CLI_modules.cli.prediction.fp_q_data_collector -y 2025 -r Japan
  
  # 收集整個賽季
  python -m CLI_modules.cli.prediction.fp_q_data_collector -y 2025 --season
  
  # 收集多個賽季 (2018-2024)
  python -m CLI_modules.cli.prediction.fp_q_data_collector --start-year 2018 --end-year 2024 --season
        """
    )
    
    parser.add_argument('-y', '--year', type=int, help='賽季年份 (例如: 2025)')
    parser.add_argument('-r', '--race', help='賽事名稱或編號 (例如: Japan 或 1)')
    parser.add_argument('--season', action='store_true', help='收集整個賽季')
    parser.add_argument('--start-year', type=int, help='起始年份 (用於多賽季收集)')
    parser.add_argument('--end-year', type=int, help='結束年份 (用於多賽季收集)')
    parser.add_argument('--start-race', type=int, default=1, help='起始賽事編號 (預設: 1)')
    parser.add_argument('--end-race', type=int, help='結束賽事編號 (預設: 全部)')
    parser.add_argument('--no-fp1', action='store_true', help='不包含 FP1 數據')
    parser.add_argument('--no-fp2', action='store_true', help='不包含 FP2 數據')
    parser.add_argument('--no-fp3', action='store_true', help='不包含 FP3 數據')
    
    args = parser.parse_args()
    
    # 驗證參數
    if args.start_year and args.end_year:
        # 多賽季模式
        pass
    elif args.year:
        # 單賽季模式
        pass
    else:
        parser.print_help()
        return
    
    # 初始化收集器
    collector = FPQDataCollector()
    
    # 執行收集
    if args.start_year and args.end_year:
        # 多賽季收集
        print(f"\n🏁 多賽季模式: {args.start_year}-{args.end_year}")
        
        for year in range(args.start_year, args.end_year + 1):
            season_data = collector.collect_season(
                year,
                start_race=args.start_race,
                end_race=args.end_race,
                include_fp1=not args.no_fp1,
                include_fp2=not args.no_fp2,
                include_fp3=not args.no_fp3
            )
            
            if season_data:
                collector.save_season_to_json(season_data, year)
    
    elif args.season:
        # 單賽季收集
        print(f"\n🏁 賽季模式: {args.year}")
        
        season_data = collector.collect_season(
            args.year,
            start_race=args.start_race,
            end_race=args.end_race,
            include_fp1=not args.no_fp1,
            include_fp2=not args.no_fp2,
            include_fp3=not args.no_fp3
        )
        
        if season_data:
            collector.save_season_to_json(season_data, args.year)
    
    else:
        # 單場賽事收集
        print(f"\n🏁 單場賽事模式: {args.year} {args.race}")
        
        data = collector.collect_single_race(
            args.year,
            args.race,
            include_fp1=not args.no_fp1,
            include_fp2=not args.no_fp2,
            include_fp3=not args.no_fp3
        )
        
        if data:
            collector.save_to_json(data)
    
    print("\n✅ 所有任務完成！")


if __name__ == "__main__":
    main()
