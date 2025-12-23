#!/usr/bin/env python3
"""測試 force_refresh=True 是否能更新 API 緩存"""

import requests
import json
from datetime import datetime
import time

API_BASE = "https://api.f1telemetrystationpro.org"
endpoint = f"{API_BASE}/api/v2/analysis/execute"

print(f'=== 測試 force_refresh=True ===\n')
print(f'目標：讓 API 重新生成包含 2025 數據的 JSON\n')

# 第一步：使用 force_refresh=True
query_params = {
    "function_id": 100,
    "race": "Abu Dhabi",
    "year": 2025,
    "session": "R",
    "force_refresh": True  # 🔥 強制重新生成
}

print(f'📤 請求參數: {json.dumps(query_params, indent=2)}')
print(f'⏳ 發送請求中（可能需要 30-60 秒，因為要重新分析）...\n')

start_time = time.time()

try:
    response = requests.post(
        endpoint,
        params=query_params,
        timeout=120,  # 延長超時時間
        headers={"Accept": "application/json"}
    )
    
    elapsed = time.time() - start_time
    
    if response.status_code == 200:
        payload = response.json()
        
        print(f'✅ API 調用成功（耗時: {elapsed:.1f}秒）\n')
        
        # 提取時間戳
        outer_timestamp = payload.get('data', {}).get('timestamp')
        inner_timestamp = payload.get('data', {}).get('data', {}).get('metadata', {}).get('generated_at')
        source = payload.get('source', 'unknown')
        
        print(f'📅 響應信息:')
        print(f'   source: {source}')
        print(f'   外層 timestamp: {outer_timestamp}')
        print(f'   內層 generated_at: {inner_timestamp}')
        
        # 提取 yearly_summary
        data = payload.get('data', {}).get('data', {})
        yearly_summary = data.get('yearly_summary', {})
        
        print(f'\n📊 yearly_summary:')
        print(f'   包含的年份: {sorted(yearly_summary.keys())}')
        
        has_2025 = False
        for year in ['2022', '2023', '2024', '2025']:
            if year in yearly_summary:
                pos_changes = yearly_summary[year].get('position_changes', 0)
                print(f'   {year}: position_changes = {pos_changes}')
                if year == '2025':
                    has_2025 = True
            else:
                print(f'   {year}: ❌ 不存在')
        
        # 判斷結果
        print(f'\n🎯 結果:')
        if has_2025:
            print(f'   ✅ API 現在包含 2025 數據！')
            print(f'   ✅ 2025 position_changes = {yearly_summary["2025"].get("position_changes")}')
            
            # 檢查時間戳是否更新
            if inner_timestamp and '2025-12-16' in inner_timestamp:
                print(f'   ✅ 時間戳已更新到今天（{inner_timestamp}）')
            elif inner_timestamp and '2025-12-07' in inner_timestamp:
                print(f'   ⚠️  時間戳仍是舊的（{inner_timestamp}）')
                print(f'   💡 可能 API 服務器還在使用舊的 JSON 檔案')
        else:
            print(f'   ❌ force_refresh=True 後仍然沒有 2025 數據')
            print(f'   💡 可能原因：')
            print(f'      1. CLI 分析過程中 2025 數據獲取失敗')
            print(f'      2. 遠程服務器的 FastF1 緩存問題')
            print(f'      3. 年份範圍設定問題')
            
        # 第二步：再次測試不使用 force_refresh（檢查緩存是否更新）
        print(f'\n\n=== 第二次測試：不使用 force_refresh ===\n')
        print(f'⏳ 檢查 API 緩存是否已更新...\n')
        
        time.sleep(2)  # 等待 2 秒
        
        query_params2 = {
            "function_id": 100,
            "race": "Abu Dhabi",
            "year": 2025,
            "session": "R",
            "force_refresh": False  # 使用緩存
        }
        
        response2 = requests.post(
            endpoint,
            params=query_params2,
            timeout=60,
            headers={"Accept": "application/json"}
        )
        
        if response2.status_code == 200:
            payload2 = response2.json()
            data2 = payload2.get('data', {}).get('data', {})
            yearly_summary2 = data2.get('yearly_summary', {})
            source2 = payload2.get('source', 'unknown')
            timestamp2 = payload2.get('data', {}).get('timestamp')
            
            print(f'✅ 第二次調用成功')
            print(f'   source: {source2}')
            print(f'   timestamp: {timestamp2}')
            print(f'   包含的年份: {sorted(yearly_summary2.keys())}')
            
            if '2025' in yearly_summary2:
                print(f'   ✅ 緩存已更新！現在包含 2025 數據')
            else:
                print(f'   ❌ 緩存仍然是舊版本')
        
    else:
        print(f'❌ HTTP {response.status_code}')
        print(f'響應: {response.text[:500]}')
        
except requests.exceptions.Timeout:
    print(f'❌ 請求超時（120秒）')
    print(f'💡 提示：force_refresh 需要重新分析所有年份數據，可能需要更長時間')
except Exception as e:
    print(f'❌ 錯誤: {e}')
    import traceback
    traceback.print_exc()

print(f'\n=== 測試完成 ===')
