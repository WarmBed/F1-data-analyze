#!/usr/bin/env python3
"""
車手遙測資料統計模組 - 功能 14.2
Driver Telemetry Statistics Module
提供車手遙測資料統計（按比賽名次排序）
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

def run_driver_telemetry_statistics(data_loader, dynamic_team_mapping=None, f1_analysis_instance=None):
    """執行車手遙測資料統計分析 - 功能 14.2"""
    try:
        print("\n[CONFIG] 執行車手遙測資料統計分析...")
        
        # 獲取已載入的數據
        data = data_loader.get_loaded_data()
        if not data:
            print("[ERROR] 沒有可用的數據，請先載入數據")
            return
        
        laps = data['laps']
        session = data['session']
        drivers_info = data.get('drivers_info', {})
        car_data = data.get('car_data', {})
        results = data.get('results', None)
        
        print(f"[CONFIG] 分析 {len(drivers_info) if drivers_info else len(laps['Driver'].unique())} 位車手的遙測統計...")
        
        # 導入輔助函數
        from modules.driver_comprehensive import (_create_basic_drivers_info, 
                                                 _create_driver_summary_report,
                                                 _sort_drivers_by_position,
                                                 _display_telemetry_table)
        
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
        
        # 遙測資料統計（按名次排序）
        print(f"\n[CONFIG] 車手遙測資料統計 (按比賽名次排序)")
        print("[INFO] 數據說明:")
        print("   • 平均油門: 整場比賽的油門開度平均值 (0-100%，100表示全油門)")
        print("   • 平均煞車: 整場比賽的煞車力度平均值 (0-100%，100表示全力煞車)")
        print("   • 最高速度: 整場比賽記錄到的最高速度 (km/h)")
        print("   • 平均速度: 整場比賽的平均速度 (km/h)")
        print("   • 最高轉速: 整場比賽記錄到的最高引擎轉速 (RPM)")
        
        _display_telemetry_table(sorted_drivers, all_driver_data)
        
        # 生成詳細遙測統計
        telemetry_stats = {}
        for abbr in sorted_drivers:
            driver_data = all_driver_data[abbr]
            telemetry = driver_data.get('telemetry', {})
            
            telemetry_stats[abbr] = {
                'driver_info': driver_data['driver_info'],
                'telemetry_summary': telemetry,
                'performance_metrics': {
                    'avg_throttle': telemetry.get('avg_throttle', 'N/A'),
                    'avg_brake': telemetry.get('avg_brake', 'N/A'),
                    'max_speed': telemetry.get('max_speed', 'N/A'),
                    'avg_speed': telemetry.get('avg_speed', 'N/A'),
                    'max_rpm': telemetry.get('max_rpm', 'N/A')
                }
            }
        
        # 生成JSON輸出
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_output = {
            "analysis_info": {
                "function_id": "14.2",
                "analysis_type": "driver_telemetry_statistics",
                "timestamp": timestamp,
                "total_drivers": len(all_driver_data)
            },
            "telemetry_statistics": _make_serializable(telemetry_stats),
            "sorted_drivers": sorted_drivers,
            "analysis_notes": {
                "throttle_range": "0-100% (100=全油門)",
                "brake_range": "0-100% (100=全力煞車)", 
                "speed_unit": "km/h",
                "rpm_unit": "轉/分鐘"
            }
        }
        
        # 確保 JSON 輸出目錄存在
        json_dir = "json_exports"
        os.makedirs(json_dir, exist_ok=True)
        
        filename = f"{json_dir}/driver_telemetry_statistics_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_output, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n[SUCCESS] 車手遙測資料統計分析完成！JSON輸出已保存到: {filename}")
        return True
        
    except Exception as e:
        print(f"[ERROR] 車手遙測統計分析執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("[CONFIG] 車手遙測資料統計分析 - 功能 14.2")
    print("="*60)
    print("[WARNING] 此模組需要配合 f1_analysis_modular_main.py 使用")
    print("請執行: python f1_analysis_modular_main.py -f 14.2")

if __name__ == "__main__":
    main()
