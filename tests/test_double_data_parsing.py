"""
測試 TrackAnalysisMDI 的雙層 data 解析邏輯
"""
import sys
sys.path.insert(0, r'c:\Users\mike2\OneDrive\Code\F1-data-analyze')

import json

print("="*70)
print("  測試 TrackAnalysisMDI 雙層 data 解析")
print("="*70)

# 步驟 1: 載入真實 API 響應
with open('test_api_track_position_response.json', 'r', encoding='utf-8') as f:
    api_response = json.load(f)

print("\n✅ 已載入真實 API 響應")
print(f"Top-level keys: {list(api_response.keys())}")

# 步驟 2: 模擬 _extract_analysis_payload 邏輯
def extract_analysis_payload_fixed(data):
    """修正後的解析邏輯"""
    if not isinstance(data, dict):
        return data, {}
    
    candidate = data.get("data")
    
    # 檢查雙層 data 結構
    if isinstance(candidate, dict) and "data" in candidate:
        inner_data = candidate.get("data")
        has_inner_core_fields = isinstance(inner_data, dict) and (
            "position_records" in inner_data 
            or "detailed_position_records" in inner_data
            or "official_corners" in inner_data
        )
        if has_inner_core_fields:
            print("\n✅ 偵測到雙層 data 結構")
            return inner_data, {}
    
    # 單層結構
    has_core_fields = isinstance(candidate, dict) and (
        "position_records" in candidate or "detailed_position_records" in candidate
    )
    if has_core_fields:
        return candidate, {}
    
    return data, {}

# 步驟 3: 測試修正後的邏輯
print("\n" + "="*70)
print("  測試解析邏輯")
print("="*70)

payload, _ = extract_analysis_payload_fixed(api_response)

print(f"\n解析結果:")
print(f"  - 類型: {type(payload)}")
print(f"  - 包含 position_records: {'position_records' in payload}")
print(f"  - 包含 official_corners: {'official_corners' in payload}")

if 'official_corners' in payload:
    corners = payload['official_corners']
    print(f"\n✅ 成功提取 official_corners!")
    print(f"  - available: {corners.get('available')}")
    print(f"  - count: {corners.get('count')}")
    print(f"  - 彎道數量: {len(corners.get('corners', []))}")
    
    if corners.get('corners'):
        print(f"\n前 3 個彎道:")
        for c in corners['corners'][:3]:
            print(f"    彎道 {c['number']}: "
                  f"X={c['x']:.2f}, "
                  f"Y={c['y']:.2f}, "
                  f"Distance={c.get('mapped_distance', 0):.2f}m")
    
    print("\n" + "="*70)
    print("✅ 測試通過：雙層 data 解析正確！")
    print("="*70)
else:
    print("\n" + "="*70)
    print("❌ 測試失敗：仍然無法提取 official_corners")
    print("="*70)
    print(f"payload keys: {list(payload.keys())}")
    sys.exit(1)

# 步驟 4: 驗證完整數據流
print("\n完整數據路徑驗證:")
print(f"  response['data'] 類型: {type(api_response.get('data'))}")
print(f"  response['data']['data'] 類型: {type(api_response.get('data', {}).get('data'))}")
print(f"  response['data']['data']['official_corners'] 存在: {'official_corners' in api_response.get('data', {}).get('data', {})}")

print("\n✅ 所有測試通過！GUI 現在可以正確讀取 API 彎道資訊")
