#!/usr/bin/env python3
"""直接測試 cache_service 的 Function 100 查找邏輯"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from api.services.cache_service import F1AnalysisCacheService

# 初始化緩存服務
cache_service = F1AnalysisCacheService()

# 模擬 API 請求參數
params = {
    "function_id": "100",
    "race": "Abu Dhabi",
    "year": 2025,
    "session": "R"
}

print('=== 測試 CacheService.search_cached_analysis ===\n')
print(f'參數: {params}\n')

# 調用緩存搜索
result = cache_service.search_cached_analysis(**params)

if result:
    print('✅ 找到緩存檔案\n')
    
    # 檢查數據結構
    if 'data' in result:
        data = result['data']
        print(f'data 鍵: {list(data.keys())[:10]}...\n')
        
        if 'yearly_summary' in data:
            yearly_summary = data['yearly_summary']
            print(f'=== yearly_summary ===')
            print(f'包含的年份: {sorted(yearly_summary.keys())}')
            
            for year in ['2022', '2023', '2024', '2025']:
                if year in yearly_summary:
                    year_data = yearly_summary[year]
                    pos_changes = year_data.get('position_changes', 0)
                    print(f'  {year}: position_changes = {pos_changes}')
                else:
                    print(f'  {year}: ❌ 不存在')
            
            # 特別檢查 2025
            if '2025' in yearly_summary:
                print(f'\n✅ 2025 數據存在於緩存中')
                print(f'   position_changes: {yearly_summary["2025"].get("position_changes")}')
            else:
                print(f'\n❌ 2025 數據不存在於緩存中')
        else:
            print('❌ 緩存數據缺少 yearly_summary')
    else:
        print('❌ 緩存數據缺少 data')
else:
    print('❌ 未找到緩存檔案')
    print('可能原因：')
    print('1. JSON 檔案不存在')
    print('2. 檔案名稱不匹配')
    print('3. 驗證邏輯失敗')
