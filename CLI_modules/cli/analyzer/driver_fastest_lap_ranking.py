#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1 Analysis - 車手最速圈排名分析模組 (功能 14.4)
Driver Fastest Lap Ranking Analysis Module (Function 14.4)

本模組提供車手最速圈排名分析功能，包含：
- 🏆 最速圈排名分析 - 含區間時間
- 輪胎策略與最速圈的關聯分析
- 各區間時間詳細對比
- JSON格式完整輸出

版本: 1.0
作者: F1 Analysis Team
日期: 2025-08-05
"""

import json
import os
import pandas as pd
import numpy as np
from datetime import datetime
from prettytable import PrettyTable


def _make_serializable(obj):
    """將對象轉換為JSON可序列化格式"""
    if obj is None or isinstance(obj, (bool, int, float, str)):
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


def _format_sector_time(time_value):
    """格式化區間時間"""
    if pd.isna(time_value) or time_value is None:
        return 'N/A'
    try:
        if isinstance(time_value, pd.Timedelta):
            total_seconds = time_value.total_seconds()
            return f"{total_seconds:.3f}s"
        elif isinstance(time_value, (int, float)):
            return f"{time_value:.3f}s"
        else:
            return str(time_value)
    except:
        return 'N/A'


def _get_fastest_lap_sector_times(driver_laps, fastest_lap_num):
    """獲取最快圈的區間時間"""
    sector_times = {}
    try:
        if fastest_lap_num != 'N/A' and not driver_laps.empty:
            fastest_lap_data = driver_laps[driver_laps['LapNumber'] == fastest_lap_num]
            if not fastest_lap_data.empty:
                lap_row = fastest_lap_data.iloc[0]
                for sector in ['Sector1Time', 'Sector2Time', 'Sector3Time']:
                    if sector in lap_row and pd.notna(lap_row[sector]):
                        sector_times[sector] = lap_row[sector]
                    else:
                        sector_times[sector] = 'N/A'
            else:
                sector_times = {'Sector1Time': 'N/A', 'Sector2Time': 'N/A', 'Sector3Time': 'N/A'}
        else:
            sector_times = {'Sector1Time': 'N/A', 'Sector2Time': 'N/A', 'Sector3Time': 'N/A'}
    except Exception as e:
        print(f"[WARNING]  獲取區間時間時出錯: {e}")
        sector_times = {'Sector1Time': 'N/A', 'Sector2Time': 'N/A', 'Sector3Time': 'N/A'}
    
    return sector_times


def _get_fastest_lap_tire_info(driver_laps, fastest_lap_num):
    """獲取最快圈的輪胎資訊"""
    try:
        if fastest_lap_num != 'N/A' and not driver_laps.empty:
            fastest_lap_data = driver_laps[driver_laps['LapNumber'] == fastest_lap_num]
            if not fastest_lap_data.empty:
                lap_row = fastest_lap_data.iloc[0]
                compound = lap_row.get('Compound', 'N/A')
                tyre_life = lap_row.get('TyreLife', 'N/A')
                return str(compound), str(tyre_life)
    except:
        pass
    return 'N/A', 'N/A'


def run_driver_fastest_lap_ranking(data_loader, dynamic_team_mapping=None, f1_analysis_instance=None):
    """執行車手最速圈排名分析 - 功能 14.4"""
    try:
        print("\n🏆 執行車手最速圈排名分析...")
        
        # 獲取已載入的數據
        data = data_loader.get_loaded_data()
        if not data:
            print("[ERROR] 沒有可用的數據，請先載入數據")
            return
        
        laps = data['laps']
        session = data['session']
        drivers_info = data.get('drivers_info', {})
        car_data = data.get('car_data', {})
        
        # 驗證數據完整性
        print("\n[DEBUG] 資料驗證檢查:")
        print("-" * 50)
        
        # 比賽資料檢查
        if hasattr(session, 'event') and hasattr(session.event, 'EventName'):
            race_name = session.event.EventName
            race_date = session.event.EventDate if hasattr(session.event, 'EventDate') else "未知日期"
            print(f"[SUCCESS] 比賽資料: {race_name} - {session.name}")
            print(f"   比賽時間: {race_date}")
        else:
            print("[WARNING]  比賽資料: 資訊不完整")
        
        # 圈速資料檢查
        if not laps.empty:
            total_laps = len(laps)
            drivers_count = laps['Driver'].nunique()
            print(f"[SUCCESS] 圈速資料: {total_laps} 筆記錄")
            print(f"   涉及車手數: {drivers_count}")
            
            # 檢查關鍵欄位
            required_columns = ['Driver', 'LapTime', 'LapNumber']
            missing_columns = [col for col in required_columns if col not in laps.columns]
            if not missing_columns:
                print(f"   [SUCCESS] 關鍵欄位完整")
                # 檢查有效圈速
                valid_laps = laps['LapTime'].notna().sum()
                print(f"   [SUCCESS] 有效圈速: {valid_laps} 筆")
            else:
                print(f"   [ERROR] 缺少欄位: {missing_columns}")
        else:
            print("[ERROR] 圈速資料: 無資料")
        
        # 車手資訊檢查
        if drivers_info:
            print(f"[SUCCESS] 車手資訊: {len(drivers_info)} 位車手")
        else:
            print("[WARNING]  車手資訊: 將從圈速資料中提取")
        
        # 遙測資料檢查
        if car_data:
            telemetry_drivers = len(car_data)
            print(f"[SUCCESS] 遙測資料: {telemetry_drivers} 位車手有資料")
        else:
            print("[WARNING]  遙測資料: 無資料")
        
        print("-" * 50)
        
        # 導入輔助函數
        from modules.driver_comprehensive import (_create_basic_drivers_info, 
                                                 _create_driver_summary_report,
                                                 _sort_drivers_by_position)
        
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
        
        # 直接從 session 獲取 results 資料
        try:
            results = session.results if hasattr(session, 'results') else None
        except Exception as e:
            print(f"[WARNING]  獲取結果數據時出錯: {e}")
            results = None
        
        print(f"\n🏆 分析 {len(all_driver_data)} 位車手的最速圈表現...")
        
        # 最速圈排名分析 - 含區間時間
        print(f"\n🏆 最速圈排名分析 - 含區間時間")
        print("[INFO] 數據說明:")
        print("   • 排名: 根據最快圈速排序 (從快到慢)")
        print("   • 圈數: 創造最快圈的圈次")
        print("   • 輪胎: 創造最快圈時使用的輪胎類型")
        print("   • 胎齡: 輪胎已使用的圈數")
        print("   • S1-S3: 各區間時間 (秒)")
        
        # 收集所有車手的最快圈速進行排名
        fastest_laps = []
        for abbr, driver_data in all_driver_data.items():
            if driver_data['fastest_lap_time'] != 'N/A':
                # 獲取最快圈的區間時間
                fastest_lap_times = _get_fastest_lap_sector_times(driver_data['driver_laps'], driver_data['fastest_lap_num'])
                
                fastest_laps.append({
                    'abbr': abbr,
                    'driver_info': driver_data['driver_info'],
                    'fastest_lap_time': driver_data['fastest_lap_time'],
                    'fastest_lap_num': driver_data['fastest_lap_num'],
                    'fastest_lap_compound': _get_fastest_lap_tire_info(driver_data['driver_laps'], driver_data['fastest_lap_num'])[0],
                    'fastest_lap_tyre_life': _get_fastest_lap_tire_info(driver_data['driver_laps'], driver_data['fastest_lap_num'])[1],
                    'sector_1': _format_sector_time(fastest_lap_times.get('Sector1Time', 'N/A')),
                    'sector_2': _format_sector_time(fastest_lap_times.get('Sector2Time', 'N/A')),
                    'sector_3': _format_sector_time(fastest_lap_times.get('Sector3Time', 'N/A')),
                    'raw_time': driver_data['driver_laps'][driver_data['driver_laps']['LapNumber'] == driver_data['fastest_lap_num']]['LapTime'].iloc[0] if driver_data['fastest_lap_num'] != 'N/A' else pd.Timedelta(seconds=999)
                })
        
        # 按最快圈速排序
        fastest_laps.sort(key=lambda x: x['raw_time'])
        
        # 顯示最速圈排名表格
        fastest_table = PrettyTable()
        fastest_table.field_names = ["排名", "車號", "車手", "車隊", "最快圈速", "圈數", "輪胎", "胎齡", "S1時間", "S2時間", "S3時間"]
        fastest_table.align = "l"
        
        for rank, lap_data in enumerate(fastest_laps, 1):
            info = lap_data['driver_info']
            fastest_table.add_row([
                rank,
                info['number'],
                info['name'][:17],
                info['team'][:19],
                lap_data['fastest_lap_time'],
                lap_data['fastest_lap_num'],
                lap_data['fastest_lap_compound'],
                lap_data['fastest_lap_tyre_life'],
                lap_data['sector_1'],
                lap_data['sector_2'],
                lap_data['sector_3']
            ])
        
        print(fastest_table)
        
        # 統計分析
        if fastest_laps:
            print(f"\n[INFO] 最速圈統計摘要:")
            fastest_time = fastest_laps[0]['raw_time']
            print(f"   • 最快圈速: {fastest_laps[0]['fastest_lap_time']} ({fastest_laps[0]['driver_info']['name']})")
            
            # 前三名
            print(f"   • 前三名:")
            for i, lap in enumerate(fastest_laps[:3], 1):
                gap = (lap['raw_time'] - fastest_time).total_seconds() if i > 1 else 0
                gap_str = f" (+{gap:.3f}s)" if gap > 0 else ""
                print(f"     {i}. {lap['driver_info']['name']} - {lap['fastest_lap_time']}{gap_str}")
            
            # 輪胎分析
            tire_stats = {}
            for lap in fastest_laps:
                compound = lap['fastest_lap_compound']
                if compound != 'N/A':
                    if compound not in tire_stats:
                        tire_stats[compound] = {'count': 0, 'fastest': None}
                    tire_stats[compound]['count'] += 1
                    if tire_stats[compound]['fastest'] is None or lap['raw_time'] < tire_stats[compound]['fastest']:
                        tire_stats[compound]['fastest'] = lap['raw_time']
            
            if tire_stats:
                print(f"   • 輪胎統計:")
                for compound, stats in tire_stats.items():
                    print(f"     - {compound}: {stats['count']} 位車手使用")
        
        # 生成JSON輸出
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_output = {
            "analysis_info": {
                "function_id": "14.4",
                "analysis_type": "driver_fastest_lap_ranking",
                "timestamp": timestamp,
                "total_drivers": len(all_driver_data)
            },
            "fastest_lap_ranking": _make_serializable(fastest_laps),
            "tire_statistics": _make_serializable(tire_stats) if 'tire_stats' in locals() else {},
            "analysis_notes": {
                "ranking_basis": "最快圈速 (從快到慢)",
                "sector_times": "各區間時間以秒為單位",
                "tire_info": "輪胎類型與胎齡來自最快圈"
            }
        }
        
        # 確保 JSON 輸出目錄存在
        json_dir = "json_exports"
        os.makedirs(json_dir, exist_ok=True)
        
        filename = f"{json_dir}/driver_fastest_lap_ranking_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_output, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n[SUCCESS] 車手最速圈排名分析完成！JSON輸出已保存到: {filename}")
        return True
        
    except Exception as e:
        print(f"[ERROR] 車手最速圈排名分析執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函數"""
    print("🏆 車手最速圈排名分析 - 功能 14.4")
    print("="*60)
    print("[WARNING] 此模組需要配合 f1_analysis_modular_main.py 使用")
    print("請執行: python f1_analysis_modular_main.py -f 14.4")


if __name__ == "__main__":
    main()
