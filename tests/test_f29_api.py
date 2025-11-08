#!/usr/bin/env python3
"""測試 Function 29 API 整合"""

import requests
import json

# 測試參數
url = "http://localhost:8000/api/v2/analysis/execute"
params = {
    "function_id": "29",
    "year": 2025,
    "min_confidence": 0.80,
    "exclude_noise": True
}

print("="*80)
print("測試 Function 29 API 呼叫")
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
            print(f"  平均信心度: {stats.get('avg_confidence')}")
            if 'by_change_type' in stats:
                print(f"  變更類型:")
                for change_type, count in stats['by_change_type'].items():
                    print(f"    {change_type}: {count}")
    
    if not result.get('success') and result.get('cli_info'):
        print(f"\n❌ CLI Error:")
        print(f"  Command: {result['cli_info'].get('command')}")
        print(f"  Stderr: {result['cli_info'].get('stderr_preview')[:500]}")
    
    print("\n" + "="*80)
    print(json.dumps(result, indent=2, ensure_ascii=False)[:2000])
    
except Exception as e:
    print(f"\n❌ Exception: {e}")
    import traceback
    traceback.print_exc()
