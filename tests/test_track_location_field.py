#!/usr/bin/env python3
"""
測試 Function 8 的 track_location 欄位
驗證新增的 track_location 欄位是否正確提取 TURN 資訊
"""

import json
import os

def test_track_location_extraction():
    """測試 extract_track_location() 函數"""
    from CLI_modules.cli.analyzer.all_incidents_summary import extract_track_location
    
    test_cases = [
        ("TURN 11 INCIDENT INVOLVING CARS 18 (STR) AND 47 (MSC) NOTED", 
         {"type": "TURN", "number": 11, "description": "Turn 11"}),
        ("CORNER 5 - YELLOW FLAG", 
         {"type": "CORNER", "number": 5, "description": "Corner 5"}),
        ("SAFETY CAR DEPLOYED - NO SPECIFIC LOCATION", 
         None),
        ("INCIDENT AT TURN 1 UNDER INVESTIGATION",
         {"type": "TURN", "number": 1, "description": "Turn 1"}),
    ]
    
    print("=" * 80)
    print("測試 extract_track_location() 函數")
    print("=" * 80)
    
    all_passed = True
    for i, (message, expected) in enumerate(test_cases, 1):
        result = extract_track_location(message)
        passed = result == expected
        all_passed = all_passed and passed
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n測試案例 {i}: {status}")
        print(f"訊息: {message}")
        print(f"預期: {expected}")
        print(f"結果: {result}")
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ 所有測試通過！")
    else:
        print("❌ 有測試失敗！")
    print("=" * 80)
    
    return all_passed


def check_json_structure():
    """檢查現有 JSON 檔案是否包含 track_location 欄位"""
    json_dir = "json"
    
    # 查找最新的 all_incidents_summary JSON
    json_files = [f for f in os.listdir(json_dir) 
                  if f.startswith("all_incidents_summary") and f.endswith(".json")]
    
    if not json_files:
        print("❌ 找不到 all_incidents_summary JSON 檔案")
        return False
    
    # 取最新的檔案
    latest_file = max([os.path.join(json_dir, f) for f in json_files], 
                     key=os.path.getmtime)
    
    print("\n" + "=" * 80)
    print(f"檢查檔案: {latest_file}")
    print("=" * 80)
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    incidents = data.get('data', {}).get('all_incidents', [])
    
    if not incidents:
        print("❌ 檔案中沒有事件數據")
        return False
    
    print(f"\n總事件數量: {len(incidents)}")
    
    # 檢查前 10 個事件的 track_location 欄位
    track_location_count = 0
    print("\n前 10 個事件的 track_location 欄位:")
    print("-" * 80)
    
    for i, incident in enumerate(incidents[:10], 1):
        track_location = incident.get('track_location')
        has_location = track_location is not None
        
        if has_location:
            track_location_count += 1
        
        status = "✅" if has_location else "⚪"
        message = incident.get('message', '')[:70]
        
        print(f"{status} 事件 {i}:")
        print(f"   訊息: {message}...")
        print(f"   track_location: {track_location}")
        print()
    
    total_with_location = sum(1 for inc in incidents if inc.get('track_location'))
    
    print("=" * 80)
    print(f"統計結果:")
    print(f"  總事件數: {len(incidents)}")
    print(f"  有 track_location 的事件: {total_with_location}")
    print(f"  比例: {total_with_location/len(incidents)*100:.1f}%")
    print("=" * 80)
    
    # 顯示所有有 TURN 的事件
    turn_incidents = [inc for inc in incidents 
                     if inc.get('track_location') and 
                        inc.get('track_location').get('type') == 'TURN']
    
    if turn_incidents:
        print(f"\n發現 {len(turn_incidents)} 個 TURN 事件:")
        print("-" * 80)
        for i, inc in enumerate(turn_incidents, 1):
            loc = inc['track_location']
            print(f"{i}. Lap {inc['lap']} - {loc['description']}")
            print(f"   {inc['message'][:100]}...")
            print()
    
    return True


if __name__ == "__main__":
    print("\n🔬 開始測試 track_location 欄位功能\n")
    
    # 測試 1: 函數功能測試
    print("【階段 1】測試 extract_track_location() 函數")
    test_passed = test_track_location_extraction()
    
    # 測試 2: JSON 結構檢查
    print("\n【階段 2】檢查現有 JSON 檔案結構")
    json_checked = check_json_structure()
    
    # 總結
    print("\n" + "=" * 80)
    print("測試總結")
    print("=" * 80)
    print(f"函數測試: {'✅ 通過' if test_passed else '❌ 失敗'}")
    print(f"JSON 檢查: {'✅ 完成' if json_checked else '❌ 失敗'}")
    print("=" * 80)
