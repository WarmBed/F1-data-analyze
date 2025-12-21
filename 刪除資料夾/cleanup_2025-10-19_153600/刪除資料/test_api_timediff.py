"""
測試 API 是否返回 time_difference 數據
"""
import requests
import json

def test_api_time_difference():
    """測試 API 端點"""
    url = 'https://api.f1telemetrystationpro.org/api/v2/analysis/execute'
    payload = {
        'function_id': 13,  # Time Diff Analysis
        'year': 2025,
        'race': 'Australia',
        'session': 'R',
        'driver1': 'VER',
        'driver2': 'LEC',  # 測試 VER vs LEC 有實際差異
        'lap1': 99,
        'lap2': 99,
        'force_refresh': False
    }
    
    print('=' * 80)
    print('發送 API 請求...')
    print(f'URL: {url}')
    print(f'Payload: {json.dumps(payload, indent=2)}')
    print('=' * 80)
    
    try:
        resp = requests.post(url, params=payload, timeout=30)  # 使用 params 而不是 json
        print(f'\n✅ HTTP 狀態碼: {resp.status_code}')
        
        if resp.status_code != 200:
            print(f'❌ 錯誤: {resp.text}')
            return
        
        data = resp.json()
        print(f'\n📦 返回數據頂層 keys: {list(data.keys())}')
        
        # 檢查 data 欄位
        if 'data' not in data:
            print('❌ 沒有 data 欄位!')
            return
        
        analysis_data = data['data']
        print(f'📊 Data keys: {list(analysis_data.keys())}')
        
        # 檢查 results
        if 'results' in analysis_data:
            results = analysis_data['results']
            print(f'📊 Results keys: {list(results.keys())}')
        else:
            print('⚠️  沒有 results 欄位，直接檢查 data')
            results = analysis_data
        
        # 檢查 time_difference
        if 'time_difference' in results:
            td = results['time_difference']
            print(f'\n✅ ✅ ✅ time_difference 存在!')
            print(f'   Keys: {list(td.keys())}')
            
            if 'reference_time' in td:
                print(f'   📈 reference_time 點數: {len(td["reference_time"])}')
                print(f'      範圍: {td["reference_time"][0]:.3f}s - {td["reference_time"][-1]:.3f}s')
            
            if 'cumulative_time_difference' in td:
                print(f'   📈 cumulative_time_difference 點數: {len(td["cumulative_time_difference"])}')
                diffs = td["cumulative_time_difference"]
                print(f'      最大值: {max(diffs):.3f}s')
                print(f'      最小值: {min(diffs):.3f}s')
                print(f'      平均值: {sum(diffs)/len(diffs):.3f}s')
            
            print('\n✅ API 正常返回 time_difference 數據!')
        else:
            print(f'\n❌ ❌ ❌ time_difference 不存在!')
            print(f'可用的 keys: {list(results.keys())}')
            
    except Exception as e:
        print(f'\n❌ 錯誤: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_api_time_difference()
