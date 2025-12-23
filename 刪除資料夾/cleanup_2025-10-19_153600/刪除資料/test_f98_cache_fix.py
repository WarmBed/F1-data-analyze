#!/usr/bin/env python3
"""
Function 98 緩存搜尋修復驗證腳本
測試 Team Colors 檔案模式是否正確配置
"""

import os
import glob
from api.services.cache_service import F1AnalysisCacheService

print("=" * 80)
print("Function 98 緩存搜尋修復驗證")
print("=" * 80)

# 初始化緩存服務
cache_service = F1AnalysisCacheService()

# 測試 1: 檢查 function_file_patterns 是否包含 98
print("\n測試 1: 檢查 Function 98 配置")
print("─" * 80)
if "98" in cache_service.function_file_patterns:
    patterns = cache_service.function_file_patterns["98"]
    print(f"✅ Function 98 已配置")
    print(f"   檔案模式: {patterns}")
else:
    print(f"❌ Function 98 未配置")

# 測試 2: 檢查實際檔案是否存在
print("\n測試 2: 檢查實際 JSON 檔案")
print("─" * 80)
json_dir = "json/"
search_pattern = f"{json_dir}team_colors_2025_*.json"
files = glob.glob(search_pattern)

if files:
    print(f"✅ 找到 {len(files)} 個匹配檔案:")
    for f in sorted(files, key=os.path.getmtime, reverse=True)[:3]:
        file_size = os.path.getsize(f) / 1024
        print(f"   - {os.path.basename(f)} ({file_size:.1f} KB)")
else:
    print(f"❌ 未找到任何 team_colors 檔案")
    print(f"   搜尋模式: {search_pattern}")

# 測試 3: 測試緩存搜尋
print("\n測試 3: 測試緩存搜尋功能")
print("─" * 80)

test_params = {
    "function_id": "98",
    "year": 2025,
}

print(f"搜尋參數: {test_params}")
result = cache_service.search_cached_analysis(**test_params)

if result:
    print(f"✅ 緩存搜尋成功!")
    print(f"   匹配類型: {result.get('cache_info', {}).get('match_type', 'unknown')}")
    
    # 檢查數據結構
    if 'data' in result:
        data = result['data']
        if 'teams' in data:
            print(f"   包含車隊數量: {len(data['teams'])}")
        if 'drivers' in data:
            print(f"   包含車手數量: {len(data['drivers'])}")
    
    if 'metadata' in result:
        metadata = result['metadata']
        if 'season_year' in metadata:
            print(f"   賽季年份: {metadata['season_year']}")
        if 'colormap' in metadata:
            print(f"   顏色映射: {metadata['colormap']}")
else:
    print(f"❌ 緩存搜尋失敗 - 未找到結果")

# 測試 4: 測試不同 colormap
print("\n測試 4: 測試不同 colormap 參數")
print("─" * 80)

for colormap in ["fastf1", "official"]:
    test_params = {
        "function_id": "98",
        "year": 2025,
        "colormap": colormap,
    }
    
    print(f"\n搜尋 colormap={colormap}")
    result = cache_service.search_cached_analysis(**test_params)
    
    if result:
        print(f"  ✅ 找到結果")
        actual_colormap = result.get('metadata', {}).get('colormap', 'unknown')
        print(f"  實際 colormap: {actual_colormap}")
    else:
        print(f"  ❌ 未找到結果")

print("\n" + "=" * 80)
print("測試完成")
print("=" * 80)

print("\n✅ 修復內容:")
print("  1. 添加 Function 98 到 function_file_patterns")
print("  2. 添加特殊處理邏輯，支援 year 和 colormap 參數")
print("  3. 搜尋模式: team_colors_{year}_{colormap}_*.json")

print("\n預期結果:")
print("  - API 調用 Function 98 時能找到緩存檔案")
print("  - 支援 colormap 參數過濾（fastf1 或 official）")
print("  - 返回最新的匹配檔案")
