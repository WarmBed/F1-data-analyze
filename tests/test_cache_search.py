#!/usr/bin/env python3
"""測試 API 緩存搜尋 Function 100"""

from api.services.cache_service import F1AnalysisCacheService

print("=" * 60)
print("測試 Function 100 緩存搜尋")
print("=" * 60)

cache_service = F1AnalysisCacheService()

# 測試搜尋
result = cache_service.search_cached_analysis(
    function_id="100",
    year=2025,
    race="Japan",
    session="R"
)

print("\n" + "=" * 60)
print("搜尋結果")
print("=" * 60)

if result:
    print("✅ 找到緩存結果！")
    print(f"來源: {result.get('source')}")
    print(f"檔案: {result.get('file_path')}")
    
    data = result.get('data', {})
    if data:
        metadata = data.get('metadata', {})
        print(f"\n賽道: {metadata.get('circuit_name')}")
        print(f"分析年份: {metadata.get('years_analyzed')}")
else:
    print("❌ 未找到緩存結果")
