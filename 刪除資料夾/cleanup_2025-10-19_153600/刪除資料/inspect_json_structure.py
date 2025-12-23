"""
檢查 JSON 結構，查找 time_series 的位置
"""
import json
import glob
import os

# 找最新的 JSON 檔案
json_pattern = "json/comparison_telemetry_VER_LEC_2024_Japan_R_*.json"
json_files = sorted(glob.glob(json_pattern), key=os.path.getmtime, reverse=True)

if not json_files:
    print(f"❌ 找不到 JSON 檔案")
    exit(1)

latest_json = json_files[0]
print(f"📂 讀取檔案: {latest_json}")

with open(latest_json, 'r', encoding='utf-8') as f:
    data = json.load(f)

def print_dict_structure(d, indent=0, max_depth=4):
    """遞歸打印字典結構"""
    if indent > max_depth:
        return
    
    for key, value in d.items():
        prefix = "  " * indent
        if isinstance(value, dict):
            print(f"{prefix}{key}: {{")
            print_dict_structure(value, indent + 1, max_depth)
            print(f"{prefix}}}")
        elif isinstance(value, list):
            if value and isinstance(value[0], dict):
                print(f"{prefix}{key}: [ {{...}} ] ({len(value)} items)")
            else:
                print(f"{prefix}{key}: [...] ({len(value)} items)")
        else:
            value_str = str(value)
            if len(value_str) > 50:
                value_str = value_str[:50] + "..."
            print(f"{prefix}{key}: {value_str}")

print("\n📋 JSON 完整結構:")
print("=" * 80)
print_dict_structure(data)

# 搜索 time_series
def find_key_in_dict(d, target_key, path=""):
    """在嵌套字典中搜索特定的鍵"""
    results = []
    for key, value in d.items():
        current_path = f"{path}.{key}" if path else key
        if key == target_key:
            results.append(current_path)
        if isinstance(value, dict):
            results.extend(find_key_in_dict(value, target_key, current_path))
    return results

print("\n" + "=" * 80)
print("🔍 搜索 'time_series' 鍵的位置:")
time_series_paths = find_key_in_dict(data, 'time_series')
if time_series_paths:
    for path in time_series_paths:
        print(f"   ✅ 找到: {path}")
else:
    print("   ❌ 未找到 'time_series' 鍵")

# 檢查 results 下的結構
if 'results' in data:
    print("\n" + "=" * 80)
    print("📊 results 結構:")
    print_dict_structure(data['results'], indent=1, max_depth=5)
