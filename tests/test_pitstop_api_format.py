import requests
import json

print('=' * 80)
print(' 測試 Pitstop Analysis API 返回格式')
print('=' * 80)

# 測試 Function 5 (車手詳細進站數據)
print('\n[Function 5] 車手詳細進站數據:')
r5 = requests.get('https://localhost:8000/analyze', params={
    'function_id': 5,
    'year': 2025,
    'race': 'Mexico',
    'session': 'R'
})
data5 = r5.json()

print(f'  Keys: {list(data5.keys())}')

# 檢查是否是錯誤響應
if 'detail' in data5:
    print(f'  ❌ API 返回錯誤:')
    print(f'     {data5["detail"]}')
else:
    print(f'  Success: {data5.get("success")}')
    print(f'  Data type: {type(data5.get("data"))}')

if isinstance(data5.get('data'), dict):
    drivers = list(data5.get('data', {}).keys())
    print(f'  ✅ Data 是物件格式（以車手為鍵）')
    print(f'  車手數量: {len(drivers)}')
    print(f'  前3位車手: {drivers[:3]}')
    
    first_driver = drivers[0]
    print(f'\n  第一位車手: {first_driver}')
    print(f'  數據類型: {type(data5["data"][first_driver])}')
    if isinstance(data5['data'][first_driver], list) and data5['data'][first_driver]:
        print(f'  進站次數: {len(data5["data"][first_driver])}')
        print(f'  第一次進站欄位: {list(data5["data"][first_driver][0].keys())}')
        
elif isinstance(data5.get('data'), list):
    print(f'  ❌ Data 是陣列格式（錯誤！）')
    print(f'  陣列長度: {len(data5.get("data", []))}')
    if data5.get("data"):
        print(f'  第一筆記錄欄位: {list(data5["data"][0].keys())}')

print('\n' + '=' * 80)
