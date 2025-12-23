#!/usr/bin/env python3
"""測試 Function 29 API 整合（簡化版 - 僅 year 參數）"""

import requests
import json

# 測試參數（僅 year，無過濾）
url = "http://localhost:8000/api/v2/analysis/execute"
params = {
    "function_id": "29",
    "year": 2025
}

print("="*80)
print("測試 Function 29 API 呼叫（簡化版）")
print("="*80)
print(f"URL: {url}")
print(f"參數: {json.dumps(params, indent=2, ensure_ascii=False)}")
print("="*80)

try:
    response = requests.post(url, params=params, timeout=120)
    print(f"\n✅ Status Code: {response.status_code}")
    
    result = response.json()
    print(f"✅ Success: {result.get('success')}")
    print(f"✅ Message: {result.get('message')}")
    print(f"✅ Source: {result.get('source')}")
    print(f"✅ Execution Time: {result.get('execution_time')}")
    
    if result.get('data'):
        print(f"\n📊 Data Keys: {list(result['data'].keys())}")
        if 'statistics' in result['data']:
            stats = result['data']['statistics']
            print(f"\n統計資訊:")
            print(f"  總記錄數: {stats.get('total_records')}")
            
        if 'confidence_stats' in result['data']:
            conf_stats = result['data']['confidence_stats']
            print(f"  平均信心度: {conf_stats.get('average')}")
            
        if 'type_percentages' in result['data']:
            print(f"  變更類型分佈:")
            for change_type, info in list(result['data']['type_percentages'].items())[:5]:
                print(f"    {change_type}: {info.get('count')} ({info.get('percentage')}%)")
    
    if not result.get('success') and result.get('cli_info'):
        print(f"\n❌ CLI Error:")
        print(f"  Command: {result['cli_info'].get('command')}")
        print(f"  Return Code: {result['cli_info'].get('returncode')}")
    
    print("\n" + "="*80)
    print("完整回應（前 3000 字元）:")
    print(json.dumps(result, indent=2, ensure_ascii=False)[:3000])
    
except Exception as e:
    print(f"\n❌ Exception: {e}")
    import traceback
    traceback.print_exc()
