#!/usr/bin/env python3
"""驗證 team_colors JSON 檔案"""

import json
import glob
import os

# 找到最新的 team_colors JSON
json_files = glob.glob("json/team_colors_2024_*.json")
if not json_files:
    print("❌ 找不到 team_colors JSON 檔案")
    exit(1)

latest = max(json_files, key=os.path.getmtime)
print(f"📄 檢查檔案: {latest}")
print(f"   大小: {os.path.getsize(latest)} bytes")
print(f"   修改時間: {os.path.getmtime(latest)}")

# 讀取並驗證
try:
    with open(latest, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("\n✅ JSON 格式驗證通過")
    print(f"   成功: {data['success']}")
    print(f"   訊息: {data['message']}")
    print(f"   車隊數: {data['metadata']['teams_count']}")
    print(f"   車手數: {len(data['data']['drivers'])}")
    print(f"   生成時間: {data['metadata']['generated_at']}")
    
    # 顯示部分車隊資料
    print("\n📊 車隊顏色範例:")
    for i, (team_id, team_data) in enumerate(list(data['data']['teams'].items())[:3]):
        print(f"   {i+1}. {team_data['team_name']}: {team_data['selected_hex']}")
    
    # 顯示部分車手資料
    print("\n🏎️  車手顏色範例:")
    for i, (driver_code, driver_data) in enumerate(list(data['data']['drivers'].items())[:5]):
        print(f"   {i+1}. {driver_code} ({driver_data['full_name']}): {driver_data.get('selected_hex', 'N/A')}")
        
except Exception as e:
    print(f"\n❌ JSON 驗證失敗: {e}")
    import traceback
    traceback.print_exc()
