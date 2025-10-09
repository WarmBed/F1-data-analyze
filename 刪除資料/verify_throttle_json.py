#!/usr/bin/env python3
"""驗證 Throttle Ratio JSON 檔案"""
import json

try:
    with open('json/throttle_ratio_2025_singapore_R.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("✅ JSON 檔案載入成功！")
    print("\n📊 元數據:")
    print(f"  Year: {data['metadata']['year']}")
    print(f"  Race: {data['metadata']['race']}")
    print(f"  Session: {data['metadata']['session']}")
    print(f"  Function ID: {data['metadata']['function_id']}")
    print(f"  Full Throttle Threshold: {data['metadata']['thresholds']['full_throttle']}")
    
    print("\n👥 分析數據:")
    print(f"  車手數量: {len(data['analysis']['drivers'])}")
    print(f"  總圈數: {data['analysis']['summary']['total_laps']}")
    print(f"  平均全油門時間: {data['analysis']['summary']['mean_full_throttle_duration_s']:.2f} 秒")
    print(f"  平均全油門比例: {data['analysis']['summary']['mean_full_throttle_ratio']*100:.1f}%")
    
    print("\n🏎️ 車手範例 (前3位):")
    for i, driver in enumerate(data['analysis']['drivers'][:3], 1):
        print(f"  {i}. {driver['driver_code']} ({driver['team_name']})")
        print(f"     有效圈數: {driver['summary']['valid_laps']}")
        print(f"     平均全油門時間: {driver['summary']['avg_full_throttle_duration_s']:.2f}秒")
        print(f"     平均全油門比例: {driver['summary']['avg_full_throttle_ratio']*100:.1f}%")
    
    print("\n✅ 結論: JSON 檔案結構完整且有效！")
    
except Exception as e:
    print(f"❌ 錯誤: {e}")
