"""
測試 API 返回的數據結構是否符合 _validate_telemetry_data 的期望
"""
import json

# 載入 JSON (這是 API 返回並保存的檔案)
with open('json/comparison_telemetry_VER_VER_2025_Japan_R_Lap1_Lap1.json', 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

print("========== 檢查 API 返回的數據結構 ==========")
print(f"✅ raw_data 是字典: {isinstance(raw_data, dict)}")
print(f"✅ raw_data 鍵值: {list(raw_data.keys())}")

# 檢查 results
if 'results' in raw_data:
    print(f"✅ 包含 'results'")
    results = raw_data['results']
    print(f"   results 鍵值: {list(results.keys())}")
    
    # 檢查 telemetry_comparison (速度分析應該在這裡)
    if 'telemetry_comparison' in results:
        print(f"✅ 包含 'telemetry_comparison'")
        telemetry_comp = results['telemetry_comparison']
        print(f"   telemetry_comparison 鍵值: {list(telemetry_comp.keys())}")
        
        # 檢查 Speed 數據
        if 'Speed' in telemetry_comp:
            print(f"✅ 包含 'Speed'")
            speed_data = telemetry_comp['Speed']
            print(f"   Speed 鍵值: {list(speed_data.keys())}")
            
            # 檢查必要欄位
            required_fields = ['distance', 'driver1_data', 'driver2_data']
            for field in required_fields:
                if field in speed_data:
                    print(f"   ✅ 包含 '{field}': {len(speed_data[field])} 點")
                else:
                    print(f"   ❌ 缺少 '{field}'")
        else:
            print(f"❌ 缺少 'Speed'")
    else:
        print(f"❌ 缺少 'telemetry_comparison'")
else:
    print(f"❌ 缺少 'results'")

print("\n========== 問題診斷 ==========")
# API 返回的數據結構
print("API 應該返回的結構 (給 _handle_api_success 的 data 參數):")
print("1. 可能是完整的 JSON (包含 analysis_type, metadata, results)")
print("2. 也可能只是 results 部分")
print("\n讓我們檢查 API endpoint 返回的是什麼...")

# 檢查 API payload 結構
print("\n如果 API 返回格式是:")
print("{ 'success': True, 'data': {...}, 'message': '...' }")
print("那麼 _handle_api_success 接收到的 'data' 應該是 {...} 內部的內容")
print("\n需要確認 API 返回的 'data' 欄位包含什麼結構")
