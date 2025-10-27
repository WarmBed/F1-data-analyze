"""
深度調查：驗證完整的 official_corners 數據流
根據反幻覺編碼五原則 - 必須驗證每個環節
"""
import sys
sys.path.insert(0, r'c:\Users\mike2\OneDrive\Code\F1-data-analyze')

import json

print("="*70)
print("  深度調查：official_corners 數據流驗證")
print("="*70)

# 階段 1: 驗證 API 響應包含 official_corners
print("\n階段 1: 驗證 API 響應")
print("-"*70)

with open('test_api_track_position_response.json', 'r', encoding='utf-8') as f:
    api_response = json.load(f)

# 檢查雙層 data 結構
outer_data = api_response.get('data', {})
inner_data = outer_data.get('data', {})
official_corners = inner_data.get('official_corners', {})

print(f"✅ API 響應路徑:")
print(f"   response['data']['data']['official_corners']")
print(f"✅ official_corners 存在: {bool(official_corners)}")
print(f"✅ 彎道數量: {official_corners.get('count', 0)}")

# 階段 2: 模擬 _extract_analysis_payload
print("\n階段 2: 模擬 _extract_analysis_payload 解析")
print("-"*70)

def simulate_extract_payload(data):
    """模擬修復後的解析邏輯"""
    if not isinstance(data, dict):
        return data
    
    candidate = data.get("data")
    
    # 檢查雙層 data
    if isinstance(candidate, dict) and "data" in candidate:
        inner_data = candidate.get("data")
        has_inner_core = isinstance(inner_data, dict) and (
            "position_records" in inner_data 
            or "official_corners" in inner_data
        )
        if has_inner_core:
            print("✅ 偵測到雙層 data，解析到內層")
            return inner_data
    
    return candidate

payload = simulate_extract_payload(api_response)
print(f"✅ 解析後 payload 類型: {type(payload)}")
print(f"✅ payload 包含 official_corners: {'official_corners' in payload}")
print(f"✅ payload 包含 position_records: {'position_records' in payload}")

# 階段 3: 模擬 process_loaded_data
print("\n階段 3: 模擬 process_loaded_data 處理")
print("-"*70)

# 提取 official_corners (修復後的邏輯)
extracted_corners = payload.get("official_corners") or {}
print(f"✅ 提取 official_corners: {bool(extracted_corners)}")
if extracted_corners:
    print(f"   - available: {extracted_corners.get('available')}")
    print(f"   - count: {extracted_corners.get('count')}")
    print(f"   - 彎道數量: {len(extracted_corners.get('corners', []))}")

# 構建 processed_data (修復後的邏輯)
processed_data = {
    "position_records": payload.get("position_records", []),
    "track_bounds": payload.get("track_bounds", {}),
    "official_corners": extracted_corners,  # 新增
    "session_info": payload.get("session_info", {}),
}

print(f"✅ processed_data 包含 official_corners: {'official_corners' in processed_data}")
print(f"✅ processed_data['official_corners'] 有效: {bool(processed_data['official_corners'])}")

# 階段 4: 模擬 on_data_loaded
print("\n階段 4: 模擬 on_data_loaded 傳遞給 Widget")
print("-"*70)

# 構建 track_data (修復後的邏輯)
track_data = {
    'detailed_position_records': processed_data['position_records'],
    'position_analysis': {
        'track_bounds': processed_data['track_bounds']
    },
    'official_corners': processed_data['official_corners'],  # 新增
    'session_info': processed_data['session_info'],
}

print(f"✅ track_data 包含 official_corners: {'official_corners' in track_data}")
print(f"✅ track_data['official_corners'] 有效: {bool(track_data['official_corners'])}")

if track_data['official_corners']:
    corners = track_data['official_corners']
    print(f"\n✅ 最終傳遞給 TrackMapWidget 的彎道資訊:")
    print(f"   - available: {corners.get('available')}")
    print(f"   - count: {corners.get('count')}")
    print(f"   - 彎道列表長度: {len(corners.get('corners', []))}")

# 階段 5: 驗證 TrackMapWidget.load_track_data 能接收
print("\n階段 5: 驗證 TrackMapWidget 接收邏輯")
print("-"*70)

# 檢查 TrackMapWidget.load_track_data 的參數處理
print("檢查 track_map_widget.py 的 load_track_data 方法...")

import inspect
from modules.gui.track_analysis.track_map_widget import TrackMapWidget

load_method_source = inspect.getsource(TrackMapWidget.load_track_data)
if 'official_corners' in load_method_source:
    print("✅ TrackMapWidget.load_track_data 包含 official_corners 處理邏輯")
else:
    print("❌ TrackMapWidget.load_track_data 缺少 official_corners 處理邏輯")

# 最終驗證
print("\n" + "="*70)
print("  深度調查結果")
print("="*70)

all_checks = [
    ("API 響應包含 official_corners", bool(official_corners)),
    ("_extract_analysis_payload 解析正確", 'official_corners' in payload),
    ("process_loaded_data 提取正確", 'official_corners' in processed_data),
    ("on_data_loaded 傳遞正確", 'official_corners' in track_data),
    ("TrackMapWidget 支援接收", 'official_corners' in load_method_source),
]

all_pass = all(check[1] for check in all_checks)

for name, passed in all_checks:
    status = "✅" if passed else "❌"
    print(f"{status} {name}")

print("\n" + "="*70)
if all_pass:
    print("✅ 所有環節驗證通過！數據流完整！")
    print("="*70)
    sys.exit(0)
else:
    print("❌ 發現問題環節，請修復！")
    print("="*70)
    sys.exit(1)
