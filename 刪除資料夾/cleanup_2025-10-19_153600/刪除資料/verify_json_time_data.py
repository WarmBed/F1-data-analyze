#!/usr/bin/env python3
"""
驗證 JSON 檔案中的時間數據
"""
import json

def verify_json_time_data(filepath):
    """驗證 JSON 檔案中是否包含時間數據"""
    print(f"\n{'='*80}")
    print(f"檢查檔案: {filepath}")
    print(f"{'='*80}\n")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    results = data.get('results', {})
    
    # 檢查 speed_difference
    if 'speed_difference' in results:
        sd = results['speed_difference']
        print("📊 speed_difference 區塊:")
        print(f"  ✅ 存在")
        print(f"  鍵: {list(sd.keys())}")
        
        if 'driver1_time_seconds' in sd:
            print(f"  ✅ driver1_time_seconds: {len(sd['driver1_time_seconds'])} 點")
            print(f"     範圍: {min(sd['driver1_time_seconds']):.2f}s - {max(sd['driver1_time_seconds']):.2f}s")
        else:
            print(f"  ❌ driver1_time_seconds: 不存在")
        
        if 'driver2_time_seconds' in sd:
            print(f"  ✅ driver2_time_seconds: {len(sd['driver2_time_seconds'])} 點")
            print(f"     範圍: {min(sd['driver2_time_seconds']):.2f}s - {max(sd['driver2_time_seconds']):.2f}s")
        else:
            print(f"  ❌ driver2_time_seconds: 不存在")
        
        if 'time_reference' in sd:
            print(f"  ✅ time_reference: {sd['time_reference']}")
        else:
            print(f"  ❌ time_reference: 不存在")
    else:
        print("❌ speed_difference 區塊不存在")
    
    # 檢查 distance_difference
    print()
    if 'distance_difference' in results:
        dd = results['distance_difference']
        print("📊 distance_difference 區塊:")
        print(f"  ✅ 存在")
        print(f"  鍵: {list(dd.keys())}")
        
        if 'driver1_time_seconds' in dd:
            print(f"  ✅ driver1_time_seconds: {len(dd['driver1_time_seconds'])} 點")
            print(f"     範圍: {min(dd['driver1_time_seconds']):.2f}s - {max(dd['driver1_time_seconds']):.2f}s")
        else:
            print(f"  ❌ driver1_time_seconds: 不存在")
        
        if 'driver2_time_seconds' in dd:
            print(f"  ✅ driver2_time_seconds: {len(dd['driver2_time_seconds'])} 點")
            print(f"     範圍: {min(dd['driver2_time_seconds']):.2f}s - {max(dd['driver2_time_seconds']):.2f}s")
        else:
            print(f"  ❌ driver2_time_seconds: 不存在")
        
        if 'time_reference' in dd:
            print(f"  ✅ time_reference: {dd['time_reference']}")
        else:
            print(f"  ❌ time_reference: 不存在")
    else:
        print("❌ distance_difference 區塊不存在")
    
    # 檢查 telemetry_comparison 中的時間數據
    print()
    if 'telemetry_comparison' in results:
        tc = results['telemetry_comparison']
        print("📊 telemetry_comparison 區塊:")
        print(f"  ✅ 存在，包含 {len(tc)} 個遙測通道")
        
        # 檢查第一個通道作為範例
        if tc:
            first_channel = list(tc.keys())[0]
            first_data = tc[first_channel]
            
            if 'driver1_time_seconds' in first_data:
                print(f"  ✅ {first_channel} 有 driver1_time_seconds: {len(first_data['driver1_time_seconds'])} 點")
            else:
                print(f"  ❌ {first_channel} 沒有 driver1_time_seconds")
    else:
        print("❌ telemetry_comparison 區塊不存在")
    
    print(f"\n{'='*80}\n")

if __name__ == "__main__":
    # 檢查新生成的 Australia JSON
    verify_json_time_data("json/comparison_telemetry_VER_LEC_2025_Australia_R_Lap1_Lap1.json")
    
    # 對比檢查 Singapore JSON
    print("\n" + "="*80)
    print("對比檢查 Singapore JSON")
    print("="*80)
    verify_json_time_data("json/comparison_telemetry_VER_LEC_2025_Singapore_R_Lap99_Lap99.json")
