#!/usr/bin/env python3
"""
檢查 JSON 檔案中的 NaN 值
檢查 Australia 和 Singapore JSON 檔案中是否有導致繪圖失敗的異常值
"""
import json
import math

def check_json_nan(filepath):
    """檢查 JSON 檔案中的 NaN 值"""
    print(f"\n{'='*80}")
    print(f"檢查檔案: {filepath}")
    print(f"{'='*80}\n")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 檢查 telemetry_comparison 中的 NaN
    if 'results' in data and 'telemetry_comparison' in data['results']:
        telemetry = data['results']['telemetry_comparison']
        
        for key, channel in telemetry.items():
            print(f"\n📊 檢查通道: {key}")
            
            # 檢查 driver1_data
            if 'driver1_data' in channel:
                driver1_data = channel['driver1_data']
                nan_count = 0
                nan_indices = []
                
                for i, value in enumerate(driver1_data):
                    if value is None or (isinstance(value, float) and math.isnan(value)):
                        nan_count += 1
                        nan_indices.append(i)
                
                if nan_count > 0:
                    print(f"  ⚠️  driver1_data 有 {nan_count} 個 NaN 值")
                    print(f"  位置: {nan_indices[:10]}{'...' if len(nan_indices) > 10 else ''}")
                else:
                    print(f"  ✅ driver1_data 無 NaN 值 ({len(driver1_data)} 個數據點)")
            
            # 檢查 driver2_data
            if 'driver2_data' in channel:
                driver2_data = channel['driver2_data']
                nan_count = 0
                nan_indices = []
                
                for i, value in enumerate(driver2_data):
                    if value is None or (isinstance(value, float) and math.isnan(value)):
                        nan_count += 1
                        nan_indices.append(i)
                
                if nan_count > 0:
                    print(f"  ⚠️  driver2_data 有 {nan_count} 個 NaN 值")
                    print(f"  位置: {nan_indices[:10]}{'...' if len(nan_indices) > 10 else ''}")
                else:
                    print(f"  ✅ driver2_data 無 NaN 值 ({len(driver2_data)} 個數據點)")
    
    # 檢查 speed_difference
    if 'results' in data and 'speed_difference' in data['results']:
        speed_diff = data['results']['speed_difference']
        print(f"\n📊 檢查 speed_difference")
        
        if 'speed_difference' in speed_diff:
            speed_diff_data = speed_diff['speed_difference']
            nan_count = 0
            nan_indices = []
            
            for i, value in enumerate(speed_diff_data):
                if value is None or (isinstance(value, float) and math.isnan(value)):
                    nan_count += 1
                    nan_indices.append(i)
            
            if nan_count > 0:
                print(f"  ⚠️  speed_difference 有 {nan_count} 個 NaN 值")
                print(f"  位置: {nan_indices[:10]}{'...' if len(nan_indices) > 10 else ''}")
            else:
                print(f"  ✅ speed_difference 無 NaN 值 ({len(speed_diff_data)} 個數據點)")
        
        # 檢查 distance 和 time 數據
        if 'distance' in speed_diff:
            distance_data = speed_diff['distance']
            nan_count = sum(1 for v in distance_data if v is None or (isinstance(v, float) and math.isnan(v)))
            if nan_count > 0:
                print(f"  ⚠️  distance 有 {nan_count} 個 NaN 值")
            else:
                print(f"  ✅ distance 無 NaN 值 ({len(distance_data)} 個數據點)")
        
        if 'driver1_time_seconds' in speed_diff:
            time_data = speed_diff['driver1_time_seconds']
            nan_count = sum(1 for v in time_data if v is None or (isinstance(v, float) and math.isnan(v)))
            if nan_count > 0:
                print(f"  ⚠️  driver1_time_seconds 有 {nan_count} 個 NaN 值")
            else:
                print(f"  ✅ driver1_time_seconds 無 NaN 值 ({len(time_data)} 個數據點)")
    
    # 檢查 distance_difference
    if 'results' in data and 'distance_difference' in data['results']:
        dist_diff = data['results']['distance_difference']
        print(f"\n📊 檢查 distance_difference")
        
        if 'position_difference' in dist_diff:
            pos_diff_data = dist_diff['position_difference']
            nan_count = sum(1 for v in pos_diff_data if v is None or (isinstance(v, float) and math.isnan(v)))
            if nan_count > 0:
                print(f"  ⚠️  position_difference 有 {nan_count} 個 NaN 值")
            else:
                print(f"  ✅ position_difference 無 NaN 值 ({len(pos_diff_data)} 個數據點)")
        
        if 'cumulative_distance_difference' in dist_diff:
            cum_diff_data = dist_diff['cumulative_distance_difference']
            nan_count = sum(1 for v in cum_diff_data if v is None or (isinstance(v, float) and math.isnan(v)))
            if nan_count > 0:
                print(f"  ⚠️  cumulative_distance_difference 有 {nan_count} 個 NaN 值")
            else:
                print(f"  ✅ cumulative_distance_difference 無 NaN 值 ({len(cum_diff_data)} 個數據點)")
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    # 檢查 Australia JSON
    check_json_nan("json/comparison_telemetry_VER_LEC_2025_Australia_R_Lap99_Lap99.json")
    
    # 檢查 Singapore JSON
    check_json_nan("json/comparison_telemetry_VER_LEC_2025_Singapore_R_Lap99_Lap99.json")
