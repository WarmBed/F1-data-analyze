#!/usr/bin/env python3
"""測試 Function 29 API 反饋格式"""
import requests
import json

print("=" * 80)
print(" Function 29 API 反饋格式測試")
print("=" * 80)

# 測試 API (v2 端點 + analysis 路由)
url = "http://localhost:8000/api/v2/analysis/execute"
params = {
    "function_id": "29",
    "year": 2025
}

print(f"\n📡 發送請求: {url}")
print(f"Params: {params}")

try:
    response = requests.post(url, params=params, timeout=30)
    print(f"\n✅ Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\n=== API Response 頂層結構 ===")
        print(f"Keys: {list(data.keys())}")
        print(f"Success: {data.get('success')}")
        print(f"Message: {data.get('message')}")
        print(f"Source: {data.get('source')}")
        
        # 檢查 data 欄位
        if 'data' in data:
            inner_data = data['data']
            print(f"\n=== Data 內層結構 ===")
            print(f"Type: {type(inner_data)}")
            print(f"Keys: {list(inner_data.keys()) if isinstance(inner_data, dict) else 'N/A'}")
            
            # 檢查 records
            if isinstance(inner_data, dict) and 'records' in inner_data:
                records = inner_data['records']
                print(f"\n=== Records 結構 ===")
                print(f"Total Records: {len(records)}")
                
                if records:
                    print(f"\n=== 第 1 筆記錄 ===")
                    record = records[0]
                    print(json.dumps(record, ensure_ascii=False, indent=2))
                    
                    print(f"\n=== 記錄欄位 ===")
                    print(f"Keys: {list(record.keys())}")
                    
                    # 檢查關鍵欄位
                    print(f"\n=== 關鍵欄位檢查 ===")
                    print(f"賽事: {record.get('賽事', '❌ 缺少')}")
                    print(f"賽事日期: {record.get('賽事日期', '❌ 缺少')}")
                    print(f"車隊: {record.get('車隊', '❌ 缺少')}")
                    print(f"車手: {record.get('車手', '❌ 缺少')}")
                    print(f"車號: {record.get('車號', '❌ 缺少')}")
                    print(f"部件: {record.get('部件', '❌ 缺少')}")
                    
                    # 檢查前 5 筆
                    print(f"\n=== 前 5 筆記錄摘要 ===")
                    for i, r in enumerate(records[:5], 1):
                        print(f"{i}. 賽事={r.get('賽事', 'N/A')}, 車隊={r.get('車隊', 'N/A')}, 部件={r.get('部件', 'N/A')[:30]}...")
            else:
                print(f"\n❌ data 中沒有 'records' 欄位")
                print(f"data keys: {list(inner_data.keys()) if isinstance(inner_data, dict) else 'N/A'}")
        
        else:
            print(f"\n❌ 錯誤：API 回應中沒有 'data' 欄位")
    
    else:
        print(f"\n❌ API 錯誤")
        print(f"Response: {response.text[:500]}")

except requests.exceptions.ConnectionError:
    print(f"\n❌ 無法連接到 API 服務器")
    print(f"請確認 API 服務器是否在運行：http://localhost:8000")
except Exception as e:
    print(f"\n❌ 錯誤: {e}")
    import traceback
    traceback.print_exc()

print(f"\n" + "=" * 80)
print(" 測試完成")
print("=" * 80)
