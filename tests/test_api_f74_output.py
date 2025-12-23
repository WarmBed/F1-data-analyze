#!/usr/bin/env python3
"""
測試 API F74 端點的輸出格式
"""
import requests
import json

print("=" * 70)
print("測試 API F74 端點輸出格式")
print("=" * 70)

# 調用 API
url = "http://localhost:8000/api/v2/analysis/execute"
params = {"function_id": 74}
payload = {
    "year": 2025,
    "race": "Mexico"
}

print(f"\n請求 URL: {url}")
print(f"參數: {params}")
print(f"Payload: {payload}")

try:
    resp = requests.post(url, params=params, json=payload, timeout=30)
    print(f"\n狀態碼: {resp.status_code}")
    
    if resp.status_code != 200:
        print(f"錯誤: {resp.text}")
    else:
        data = resp.json()
        
        print("\n" + "=" * 70)
        print("API 返回的頂層結構:")
        print("=" * 70)
        print(f"Keys: {list(data.keys())}")
        
        if 'data' in data:
            print("\n" + "=" * 70)
            print("data 層級的結構:")
            print("=" * 70)
            print(f"Keys: {list(data['data'].keys())}")
            
            if 'metadata' in data['data']:
                print("\n📊 Metadata:")
                print(json.dumps(data['data']['metadata'], indent=2, ensure_ascii=False))
            
            if 'predictions' in data['data']:
                predictions = data['data']['predictions']
                print(f"\n✅ 找到 {len(predictions)} 個預測")
                
                print("\n" + "=" * 70)
                print("第一個預測的完整結構:")
                print("=" * 70)
                print(json.dumps(predictions[0], indent=2, ensure_ascii=False))
                
                print("\n" + "=" * 70)
                print("檢查關鍵欄位:")
                print("=" * 70)
                first = predictions[0]
                print(f"✓ driver: {first.get('driver')}")
                print(f"✓ actual_q_time: {first.get('actual_q_time')}")
                print(f"✓ actual_q_rank: {first.get('actual_q_rank', 'KEY NOT FOUND')}")
                print(f"✓ fp3_predicted_rank: {first.get('fp3_predicted_rank', 'KEY NOT FOUND')}")
                
except requests.exceptions.ConnectionError:
    print("\n❌ 無法連接到 API 服務器")
    print("💡 提示: 請確保 API 服務器正在運行（python refactored_api.py）")
except Exception as e:
    print(f"\n❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()
