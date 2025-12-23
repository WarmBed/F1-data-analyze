#!/usr/bin/env python3
"""
測試 API Function 100 支援
"""

import requests
import json
from datetime import datetime

def test_function_100_api():
    """測試 Function 100 API 調用"""
    
    print("=" * 70)
    print("API Function 100 測試")
    print("=" * 70)
    
    # 1. 檢查 Function 100 是否在支援列表中
    print("\n[步驟 1] 檢查 Function 100 支援狀態...")
    try:
        r = requests.get('http://localhost:8000/api/v2/analysis/functions')
        data = r.json()
        
        if '100' in data.get('functions', {}):
            print("✅ Function 100 已支援")
            func_spec = data['functions']['100']
            print(f"\n名稱: {func_spec['name']}")
            print(f"描述: {func_spec['description'][:100]}...")
            print(f"必需參數: {', '.join(func_spec['required_params'])}")
            print(f"緩存模式: {', '.join(func_spec['cache_patterns'])}")
        else:
            print("❌ Function 100 未找到")
            return False
            
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        return False
    
    # 2. 執行 Function 100 分析
    print("\n" + "=" * 70)
    print("[步驟 2] 執行 Function 100 API 調用...")
    print("參數: year=2024, race=Japan, session=R")
    print("=" * 70)
    
    try:
        start_time = datetime.now()
        
        r = requests.post(
            'http://localhost:8000/api/v2/analysis/execute',
            params={
                'function_id': '100',
                'year': 2024,
                'race': 'Japan',
                'session': 'R'
            },
            timeout=60  # 60 秒超時
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"\n狀態碼: {r.status_code}")
        print(f"回應時間: {elapsed:.2f} 秒")
        
        if r.status_code == 200:
            data = r.json()
            
            print(f"\n✅ API 回應 200")
            print(f"成功標誌: {data.get('success')}")
            
            if 'message' in data:
                print(f"訊息: {data['message']}")
            
            # 顯示完整回應以便調試
            if not data.get('success'):
                print("\n完整錯誤回應:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # 檢查數據結構
            if 'data' in data:
                print("\n數據結構:")
                data_keys = list(data['data'].keys())
                for key in data_keys:
                    print(f"  - {key}")
                
                # 檢查 yearly_summary
                if 'yearly_summary' in data['data']:
                    print("\n年度統計:")
                    yearly = data['data']['yearly_summary']
                    for year, stats in yearly.items():
                        print(f"  {year}: {stats}")
                
                # 檢查 corner_analysis
                if 'corner_analysis' in data['data']:
                    corners = data['data']['corner_analysis']
                    print(f"\n彎道分析: {len(corners)} 個彎道")
                    if corners:
                        print(f"  第一個彎道範例: {corners[0]}")
                
                # 檢查 detailed_position_records
                if 'detailed_position_records' in data['data']:
                    records = data['data']['detailed_position_records']
                    print(f"\n位置記錄: {len(records)} 筆")
                    if records:
                        print(f"  第一筆記錄範例: {records[0]}")
                
                # 檢查 track_data
                if 'track_data' in data['data']:
                    track = data['data']['track_data']
                    print(f"\n賽道數據:")
                    print(f"  賽道名稱: {track.get('track_name', 'N/A')}")
                    if 'corners' in track:
                        print(f"  彎道數量: {len(track['corners'])}")
            
            # 檢查 meta 資訊
            if 'meta' in data:
                print("\nMeta 資訊:")
                for key, value in data['meta'].items():
                    print(f"  {key}: {value}")
            
            return True
            
        else:
            print(f"\n❌ API 調用失敗")
            print(f"錯誤: {r.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"\n❌ 請求超時（60 秒）")
        return False
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = test_function_100_api()
        
        print("\n" + "=" * 70)
        if success:
            print("✅ 測試完成：Function 100 API 運作正常")
        else:
            print("❌ 測試失敗：Function 100 API 有問題")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ 測試中斷")
