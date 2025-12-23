"""測試 API 修正後的結果"""
import requests
import time

print("等待 API 服務器啟動...")
time.sleep(5)

print("正在測試 API...")
try:
    r = requests.post(
        'https://localhost:8000/api/v2/analysis/execute',
        params={'function_id': '29', 'year': 2025},
        timeout=30
    )
    
    data = r.json()['data']
    records = data['records']
    
    # 提取部件並排除噪音
    parts = [rec.get('部件', '') for rec in records if rec.get('部件')]
    exclude = ['Date ', 'Time ', 'To The Stewards', 'written request']
    valid_parts = [p for p in parts if not any(ex in p for ex in exclude)]
    unique_parts = set(valid_parts)
    
    print("\n" + "="*50)
    print("API 修正後結果")
    print("="*50)
    print(f"API 返回記錄數: {len(records)}")
    print(f"有效部件記錄數: {len(valid_parts)}")
    print(f"部件種類數: {len(unique_parts)}")
    
    print("\n" + "="*50)
    print("與本地數據對比")
    print("="*50)
    print(f"本地 JSON 記錄數: 475")
    print(f"本地部件種類數: 307")
    
    print("\n" + "="*50)
    if len(records) >= 475:
        print("✅ 修正成功！API 現在返回完整數據")
    elif len(records) > 50:
        print(f"⚠️  部分成功：API 返回 {len(records)} 筆（預期 475 筆）")
    else:
        print("❌ 修正失敗：API 仍然只返回 50 筆")
    print("="*50)
    
except Exception as e:
    print(f"\n❌ 測試失敗: {e}")
