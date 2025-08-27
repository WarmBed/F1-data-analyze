#!/usr/bin/env python3
"""
車手超車分析模組 - 功能 14.3
Driver Overtaking Analysis Module
提供車手超車分析（當前比賽）
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from prettytable import PrettyTable
from datetime import datetime
import json

def _make_serializable(obj):
    """確保對象可以序列化為JSON"""
    if obj is None:
        return None
    elif isinstance(obj, (int, float, str, bool)):
        return obj
    elif isinstance(obj, (list, tuple)):
        return [_make_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        result = {}
        for key, value in obj.items():
            # 跳過 driver_laps 以避免序列化問題
            if key == 'driver_laps':
                continue
            result[key] = _make_serializable(value)
        return result
    elif isinstance(obj, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32, np.float16)):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, pd.Timedelta):
        return str(obj)
    elif hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
        try:
            return _make_serializable(obj.to_dict())
        except:
            return str(obj)
    elif hasattr(obj, 'tolist') and callable(getattr(obj, 'tolist')):
        try:
            return obj.tolist()
        except:
            return str(obj)
    else:
        return str(obj)

def run_driver_overtaking_analysis(data_loader, dynamic_team_mapping=None, f1_analysis_instance=None):
    """執行車手超車分析 - 功能 14.3"""
    try:
        print("\n[START] 執行車手超車分析...")
        
        # 獲取已載入的數據
        data = data_loader.get_loaded_data()
        if not data:
            print("[ERROR] 沒有可用的數據，請先載入數據")
            return
        
        laps = data['laps']
        session = data['session']
        drivers_info = data.get('drivers_info', {})
        car_data = data.get('car_data', {})
        
        # 直接從 session 獲取 results 和 laps 資料
        try:
            # 獲取比賽結果 (包含起始位置和最終名次)
            results = session.results if hasattr(session, 'results') else None
            
            # 獲取進站資料
            laps_data = session.laps if hasattr(session, 'laps') else laps
            
            print(f"[INFO] 可用數據檢查:")
            print(f"   • Results 數據: {'[SUCCESS]' if results is not None else '[ERROR]'}")
            print(f"   • Laps 數據: {len(laps_data) if laps_data is not None else 0} 筆記錄")
            
        except Exception as e:
            print(f"[WARNING]  數據獲取警告: {e}")
            results = None
        results = data.get('results', None)
        
        print(f"[START] 分析 {len(drivers_info) if drivers_info else len(laps['Driver'].unique())} 位車手的超車表現...")
        
        # 導入輔助函數
        from modules.driver_comprehensive import (_create_basic_drivers_info, 
                                                 _create_driver_summary_report,
                                                 _sort_drivers_by_position,
                                                 _generate_comprehensive_overtaking_table)
        
        # 創建所有車手的分析報告
        all_driver_data = {}
        
        # 如果沒有 drivers_info，從 laps 中創建基本信息
        if not drivers_info:
            drivers_info = _create_basic_drivers_info(laps, dynamic_team_mapping)
        
        # 收集所有車手資料
        for abbr, info in drivers_info.items():
            driver_data = _create_driver_summary_report(abbr, laps, drivers_info, car_data, dynamic_team_mapping)
            if driver_data:
                all_driver_data[abbr] = driver_data
        
        if not all_driver_data:
            print("[ERROR] 無法獲取任何車手數據")
            return
        
        # 按比賽名次排序車手
        sorted_drivers = _sort_drivers_by_position(all_driver_data, results, laps)
        
        # 超車分析（當前比賽）
        print(f"\n[START] 車手超車分析 (當前比賽)")
        print("[INFO] 數據說明:")
        print("   • 起始排位: 比賽開始時的起跑順位")
        print("   • 最終名次: 比賽結束時的最終排名")
        print("   • 名次變化: 比賽中的總名次變化 (正數=進步，負數=退步)")
        print("   • 進站次數: 總計進站維修次數")
        print("   • 超車次數: 在賽道上完成的超車動作次數")
        print("   • 被超次數: 被其他車手超越的次數")
        print("   • 淨超車: 超車次數減去被超次數")
        
        # 顯示超車表格
        from prettytable import PrettyTable
        table = PrettyTable()
        table.field_names = ["名次", "車號", "車手", "車隊", "起始排位", "最終名次", "名次變化", "進站次數"]
        table.align = "l"
        
        for idx, abbr in enumerate(sorted_drivers, 1):
            driver_data = all_driver_data[abbr]
            driver_info = driver_data['driver_info']
            
            # 獲取基本信息
            number = driver_info.get('number', 'N/A')
            full_name = driver_info.get('full_name', abbr)
            team = driver_info.get('team', 'Unknown')
            
            # 從 results 獲取起始位置和最終名次
            grid_pos = 'N/A'
            final_pos = 'N/A'
            position_change = 'N/A'
            
            if results is not None:
                try:
                    # 查找車手在 results 中的記錄
                    driver_result = results[results['Abbreviation'] == abbr]
                    if not driver_result.empty:
                        grid_pos = driver_result.iloc[0].get('GridPosition', 'N/A')
                        final_pos = driver_result.iloc[0].get('Position', 'N/A')
                        
                        # 計算名次變化
                        if isinstance(grid_pos, (int, float)) and isinstance(final_pos, (int, float)):
                            change = int(grid_pos) - int(final_pos)
                            if change > 0:
                                position_change = f"+{change}"
                            elif change < 0:
                                position_change = str(change)
                            else:
                                position_change = "0"
                except Exception as e:
                    print(f"[WARNING]  處理 {abbr} 賽果數據時出錯: {e}")
            
            # 計算進站次數 (從圈速數據中計算)
            pit_count = 'N/A'
            try:
                driver_laps = laps[laps['Driver'] == abbr]
                if not driver_laps.empty and 'PitInTime' in driver_laps.columns:
                    # 計算有效進站次數
                    pit_ins = driver_laps['PitInTime'].notna().sum()
                    pit_count = int(pit_ins) if pit_ins > 0 else 0
                elif not driver_laps.empty:
                    # 後備方案：檢查輪胎變化次數作為進站估算
                    if 'Compound' in driver_laps.columns:
                        compound_changes = (driver_laps['Compound'] != driver_laps['Compound'].shift()).sum() - 1
                        pit_count = max(0, compound_changes)
            except Exception as e:
                print(f"[WARNING]  計算 {abbr} 進站次數時出錯: {e}")
            
            table.add_row([
                idx,
                number,
                full_name,
                team,
                grid_pos,
                final_pos,
                position_change,
                pit_count
            ])
        
        print(table)
        
        # 生成詳細超車統計
        overtaking_stats = {}
        total_overtakes = 0
        
        print(f"\n[INFO] 超車統計摘要:")
        
        # 基於位置變化計算超車統計
        for abbr in sorted_drivers:
            driver_data = all_driver_data[abbr]
            driver_info = driver_data['driver_info']
            
            # 初始化超車數據
            overtakes = 0
            position_gain = 0
            
            if results is not None:
                try:
                    driver_result = results[results['Abbreviation'] == abbr]
                    if not driver_result.empty:
                        grid_pos = driver_result.iloc[0].get('GridPosition', None)
                        final_pos = driver_result.iloc[0].get('Position', None)
                        
                        if isinstance(grid_pos, (int, float)) and isinstance(final_pos, (int, float)):
                            position_gain = max(0, int(grid_pos) - int(final_pos))
                            # 簡化超車計算：位置進步可視為成功超車
                            overtakes = position_gain
                            total_overtakes += overtakes
                except Exception as e:
                    print(f"[WARNING]  處理 {abbr} 超車統計時出錯: {e}")
            
            overtaking_stats[abbr] = {
                'driver_info': driver_info,
                'overtakes': overtakes,
                'position_gain': position_gain,
                'overtaken': max(0, -position_gain) if position_gain < 0 else 0,
                'net_overtakes': overtakes - (max(0, -position_gain) if position_gain < 0 else 0)
            }
        
        # 顯示統計摘要
        if total_overtakes > 0:
            print(f"   • 比賽總位置進步次數: {total_overtakes}")
            print(f"   • 平均每位車手位置進步: {total_overtakes/len(sorted_drivers):.1f}")
            
            # 顯示前5名超車表現車手
            top_overtakers = sorted(overtaking_stats.items(), 
                                  key=lambda x: x[1]['overtakes'], 
                                  reverse=True)[:5]
            print(f"   • 位置進步最多車手:")
            for abbr, stats in top_overtakers:
                if stats['overtakes'] > 0:
                    name = stats['driver_info'].get('full_name', abbr)
                    print(f"     - {name} ({abbr}): +{stats['overtakes']} 位")
        else:
            print(f"   • 比賽總超車次數: 0")
            print(f"   • 平均每位車手超車: 0.0")
        
        # 找出最佳表現者
        best_overtaker = None
        most_overtakes = 0
        best_gainer = None
        most_gain = 0
        
        for abbr, stats in overtaking_stats.items():
            # 最多超車
            overtakes = stats.get('overtakes', 0)
            if isinstance(overtakes, (int, float)) and overtakes > most_overtakes:
                most_overtakes = overtakes
                best_overtaker = abbr
            
            # 最大進步
            pos_gain = stats.get('position_gain', 0)
            if isinstance(pos_gain, (int, float)) and pos_gain > most_gain:
                most_gain = pos_gain
                best_gainer = abbr
        
        # 生成JSON輸出
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_output = {
            "analysis_info": {
                "function_id": "14.3",
                "analysis_type": "driver_overtaking_analysis",
                "timestamp": timestamp,
                "total_drivers": len(all_driver_data)
            },
            "overtaking_statistics": _make_serializable(overtaking_stats),
            "race_summary": {
                "total_overtakes": total_overtakes,
                "average_overtakes_per_driver": round(total_overtakes / len(all_driver_data), 1) if all_driver_data else 0,
                "best_overtaker": best_overtaker,
                "most_overtakes": most_overtakes,
                "best_gainer": best_gainer,
                "most_position_gain": most_gain if most_gain != float('-inf') else 0
            },
            "sorted_drivers": sorted_drivers,
            "analysis_notes": {
                "position_change": "正數表示進步，負數表示退步",
                "net_overtakes": "超車次數 - 被超次數",
                "data_source": "當前比賽數據"
            }
        }
        
        # 確保 JSON 輸出目錄存在
        json_dir = "json_exports"
        os.makedirs(json_dir, exist_ok=True)
        
        filename = f"{json_dir}/driver_overtaking_analysis_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_output, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n[SUCCESS] 車手超車分析完成！JSON輸出已保存到: {filename}")
        return True
        
    except Exception as e:
        print(f"[ERROR] 車手超車分析執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("[START] 車手超車分析 - 功能 14.3")
    print("="*60)
    print("[WARNING] 此模組需要配合 f1_analysis_modular_main.py 使用")
    print("請執行: python f1_analysis_modular_main.py -f 14.3")

if __name__ == "__main__":
    main()
