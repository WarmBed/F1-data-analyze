#!/usr/bin/env python3
"""測試 Historical Track Map API 返回數據"""

import requests
import json

# 模擬 GUI 的 API 請求方式
API_BASE = "https://localhost:8000"
endpoint = f"{API_BASE}/api/v2/analysis/execute"

# ✅ 使用與 GUI 相同的參數格式
query_params = {
    "function_id": 100,  # Historical Flags Analysis
    "race": "Abu Dhabi",
    "year": 2025,
    "session": "R"
}

print('=== 測試 Historical Track Map API (Function 100) ===\n')
print(f'📡 端點: {endpoint}')
print(f'📤 參數: {json.dumps(query_params, indent=2)}\n')

try:
    # ✅ 使用 POST + params（與 GUI 完全相同）
    response = requests.post(
        endpoint,
        params=query_params,
        timeout=60,
        headers={"Accept": "application/json"}
    )
    
    print(f'📥 HTTP 狀態: {response.status_code}\n')
    
    if response.status_code == 200:
        payload = response.json()
        
        # 檢查頂層結構
        print('=== API 響應結構 ===')
        print(f'✅ success: {payload.get("success")}')
        print(f'✅ message: {payload.get("message")}')
        print(f'✅ execution_time: {payload.get("execution_time")}')
        
        # 獲取數據 (嵌套結構: payload['data']['data'])
        if 'data' in payload:
            outer_data = payload['data']
            print(f'\n=== payload["data"] 字段 ===')
            print(f'外層鍵: {list(outer_data.keys())[:10]}...')
            
            # ✅ 真實數據在 payload['data']['data'] 中
            if 'data' in outer_data:
                data = outer_data['data']
                print(f'\n=== payload["data"]["data"] 字段 (實際數據) ===')
                print(f'數據鍵: {list(data.keys())[:10]}...')
            else:
                data = outer_data
                print(f'\n⚠️  使用 payload["data"] 作為數據源')
            
            # 檢查 yearly_summary
            if 'yearly_summary' in data:
                yearly_summary = data['yearly_summary']
                print(f'\n=== yearly_summary ===')
                print(f'包含的年份: {sorted(yearly_summary.keys())}')
                
                # 逐年檢查
                for year in ['2022', '2023', '2024', '2025']:
                    if year in yearly_summary:
                        year_data = yearly_summary[year]
                        print(f'\n【{year}】')
                        print(f'  類型: {type(year_data).__name__}')
                        
                        if isinstance(year_data, dict):
                            print(f'  yellow_flags: {year_data.get("yellow_flags")}')
                            print(f'  position_changes: {year_data.get("position_changes")} ⭐')
                            print(f'  max_speed: {year_data.get("max_speed")}')
                        else:
                            print(f'  ⚠️  year_data 不是 dict！')
                    else:
                        print(f'\n【{year}】❌ 不存在')
                
                # ⭐ 特別驗證 2025
                print(f'\n=== 🎯 2025 數據驗證 ===')
                if '2025' in yearly_summary:
                    year_2025 = yearly_summary['2025']
                    
                    print(f'✅ 2025 存在於 API 響應')
                    print(f'   類型: {type(year_2025)}')
                    print(f'   isinstance(dict): {isinstance(year_2025, dict)}')
                    
                    if isinstance(year_2025, dict):
                        has_pos_changes = 'position_changes' in year_2025
                        print(f'   "position_changes" in year_2025: {has_pos_changes}')
                        
                        if has_pos_changes:
                            value = year_2025['position_changes']
                            value_type = type(value).__name__
                            
                            print(f'\n   📊 position_changes:')
                            print(f'      值: {value}')
                            print(f'      類型: {value_type}')
                            
                            # 驗證是否正確
                            if value == 456:
                                print(f'      ✅ 正確！API 返回 456')
                            elif value == 0:
                                print(f'      ❌ 錯誤！API 返回 0，應該是 456')
                            else:
                                print(f'      ⚠️  異常值: {value}')
                        else:
                            print(f'   ❌ 缺少 position_changes 鍵')
                else:
                    print(f'❌ 2025 不存在於 yearly_summary')
            else:
                print(f'\n❌ API 響應缺少 yearly_summary')
        else:
            print(f'\n❌ API 響應缺少 data 字段')
            print(f'響應: {json.dumps(payload, indent=2, ensure_ascii=False)[:500]}')
    else:
        print(f'❌ HTTP 錯誤: {response.status_code}')
        try:
            error_data = response.json()
            print(f'錯誤詳情: {json.dumps(error_data, indent=2, ensure_ascii=False)[:500]}')
        except:
            print(f'響應文本: {response.text[:500]}')

except requests.exceptions.Timeout:
    print(f'❌ 請求超時 (60秒)')
except requests.exceptions.RequestException as e:
    print(f'❌ 網絡錯誤: {e}')
except Exception as e:
    print(f'❌ 處理錯誤: {e}')
    import traceback
    traceback.print_exc()

print('\n=== 測試完成 ===')
