"""
DRS 數值調試腳本
檢查 Live Timing 數據中 DRS 值的分佈情況
"""

import sys
import json
import pickle
from pathlib import Path


def analyze_drs_values(pkl_file: str):
    """分析 DRS 數值分佈"""
    print(f"正在載入: {pkl_file}")
    
    try:
        # 直接讀取 PKL
        with open(pkl_file, 'rb') as f:
            data = pickle.load(f)
        
        print(f"✅ PKL 載入成功")
        
        # 從 snapshots 中提取 DRS 數據
        snapshots = data.get('snapshots', [])
        
        if not snapshots:
            print("❌ 找不到 snapshots!")
            return
        
        print(f"✅ Snapshots 筆數: {len(snapshots)}")
        
        # 統計 DRS 值分佈
        drs_distribution = {}
        drs_by_driver = {}
        total_samples = 0
        
        for snapshot in snapshots:
            drivers = snapshot.get('drivers', {})
            
            for driver_num, driver_data in drivers.items():
                drs_val = driver_data.get('drs', '')
                
                if drs_val != '' and drs_val is not None:
                    total_samples += 1
                    
                    # 轉為字串便於統計
                    drs_str = str(drs_val)
                    
                    # 全局分佈
                    drs_distribution[drs_str] = drs_distribution.get(drs_str, 0) + 1
                    
                    # 按車手統計
                    if driver_num not in drs_by_driver:
                        drs_by_driver[driver_num] = {}
                    drs_by_driver[driver_num][drs_str] = drs_by_driver[driver_num].get(drs_str, 0) + 1
        
        print(f"\n📊 DRS 值分佈 (總樣本數: {total_samples})")
        print("="*60)
        
        # 按 DRS 值排序
        sorted_drs = sorted(drs_distribution.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0)
        
        for drs_val, count in sorted_drs:
            percentage = (count / total_samples) * 100 if total_samples > 0 else 0
            
            # 判斷狀態
            try:
                val = int(drs_val)
                if val >= 10 and val % 2 == 0:
                    status = "ON (實際開啟)"
                elif val >= 2 and val % 2 == 0:
                    status = "RDY (可用未開)"
                elif val % 2 == 1:
                    status = "Disabled (禁用)"
                else:
                    status = "Off"
            except:
                status = "Unknown"
            
            print(f"  {drs_val:>3s}: {count:>6d} ({percentage:>5.2f}%) - {status}")
        
        print(f"\n📊 按車手統計 (前 5 名)")
        print("="*60)
        
        # 隨機取 5 位車手
        sample_drivers = list(drs_by_driver.keys())[:5]
        
        for driver_num in sample_drivers:
            driver_stats = drs_by_driver[driver_num]
            driver_total = sum(driver_stats.values())
            
            print(f"\n車手 {driver_num} (樣本數: {driver_total})")
            
            sorted_driver_drs = sorted(driver_stats.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0)
            
            for drs_val, count in sorted_driver_drs:
                percentage = (count / driver_total) * 100 if driver_total > 0 else 0
                
                try:
                    val = int(drs_val)
                    if val >= 10 and val % 2 == 0:
                        status = "ON"
                    elif val >= 2 and val % 2 == 0:
                        status = "RDY"
                    else:
                        status = "OFF/Disabled"
                except:
                    status = "?"
                
                print(f"  {drs_val:>3s}: {count:>5d} ({percentage:>5.2f}%) - {status}")
        
        print("\n" + "="*60)
        print("💡 分析完成")
        print("="*60)
        
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 預設測試檔案
    default_pkl = r"C:\Users\mike2\OneDrive\Code\F1-data-analyze\dist\live_timing_cache\2025\Abu_Dhabi_Race.pkl"
    
    if len(sys.argv) > 1:
        pkl_file = sys.argv[1]
    else:
        pkl_file = default_pkl
    
    analyze_drs_values(pkl_file)
