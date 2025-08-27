#!/usr/bin/env python3
"""
車手數據統計總覽模組 - 功能 14.1
Driver Data Statistics Overview Module
提供車手數據統計總覽表（按比賽名次排序）- 含輪胎策略
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

def run_driver_statistics_overview(data_loader, dynamic_team_mapping=None, f1_analysis_instance=None):
    """執行車手數據統計總覽分析 - 功能 14.1"""
    try:
        print("\n[INFO] 執行車手數據統計總覽分析...")
        
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
        
        print(f"[INFO] 分析 {len(drivers_info) if drivers_info else len(laps['Driver'].unique())} 位車手的統計總覽...")
        
        # 導入輔助函數
        from modules.driver_comprehensive import (_create_basic_drivers_info, 
                                                 _create_driver_summary_report,
                                                 _sort_drivers_by_position,
                                                 _display_overview_table,
                                                 _display_fastest_lap_ranking)
        
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
        
        # 顯示統計總覽表（按名次排序）- 包含輪胎資訊
        print(f"\n[INFO] 車手數據統計總覽 (按比賽名次排序) - 含輪胎策略")
        _display_overview_table(sorted_drivers, all_driver_data)
        
        # 生成JSON輸出
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_output = {
            "analysis_info": {
                "function_id": "14.1",
                "analysis_type": "driver_statistics_overview",
                "timestamp": timestamp,
                "total_drivers": len(all_driver_data)
            },
            "driver_statistics": _make_serializable(all_driver_data),
            "sorted_drivers": sorted_drivers
        }
        
        # 確保 JSON 輸出目錄存在
        json_dir = "json_exports"
        os.makedirs(json_dir, exist_ok=True)
        
        filename = f"{json_dir}/driver_statistics_overview_{timestamp}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_output, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n[SUCCESS] 車手數據統計總覽分析完成！JSON輸出已保存到: {filename}")
        return True
        
    except Exception as e:
        print(f"[ERROR] 車手統計總覽分析執行失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("[INFO] 車手數據統計總覽分析 - 功能 14.1")
    print("="*60)
    print("[WARNING] 此模組需要配合 f1_analysis_modular_main.py 使用")
    print("請執行: python f1_analysis_modular_main.py -f 14.1")

if __name__ == "__main__":
    main()
