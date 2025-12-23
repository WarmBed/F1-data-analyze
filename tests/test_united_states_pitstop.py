#!/usr/bin/env python3
"""測試 United States 功能 3 和 5 的執行"""

import sys
import os

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🧪 測試 United States 賽事功能 3 和 5")
print("=" * 80)

# 測試 1: 檢查 OpenF1 API 能否找到 United States 會話
print("\n📡 測試 1: OpenF1API 會話查找")
print("-" * 80)

try:
    from CLI_modules.cli.core.openf1_data_analyzer import F1OpenDataAnalyzer
    
    analyzer = F1OpenDataAnalyzer()
    
    # 測試不同的搜索名稱
    test_names = ['usa', 'united states', 'austin', 'cota', 'american']
    
    for search_name in test_names:
        print(f"\n🔍 搜索名稱: '{search_name}'")
        session = analyzer.find_race_session_by_name(2025, search_name)
        
        if session:
            print(f"  ✅ 找到會話:")
            print(f"     • Location: {session.get('location')}")
            print(f"     • Country: {session.get('country_name')}")
            print(f"     • Session Key: {session.get('session_key')}")
            print(f"     • Date: {session.get('date_start')}")
        else:
            print(f"  ❌ 未找到會話")
    
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()

# 測試 2: 檢查 DataLoader 能否載入 United States 數據
print("\n\n📊 測試 2: DataLoader 載入測試")
print("-" * 80)

try:
    from core.data_loader import F1DataLoader
    
    loader = F1DataLoader()
    print(f"\n🔄 嘗試載入: 2025 United States R")
    success = loader.load_data(2025, "United States", "R")
    
    if success:
        print("  ✅ 數據載入成功")
        
        # 檢查會話資訊
        if hasattr(loader, 'session') and loader.session:
            event = loader.session.event
            print(f"  📍 Event Name: {event.get('EventName')}")
            print(f"  📍 Location: {event.get('Location')}")
            print(f"  📍 Country: {event.get('Country')}")
    else:
        print("  ❌ 數據載入失敗")
        
except Exception as e:
    print(f"❌ 測試失敗: {e}")
    import traceback
    traceback.print_exc()

# 測試 3: 檢查功能 3 的賽事名稱映射
print("\n\n🗺️  測試 3: 功能 3 賽事名稱映射")
print("-" * 80)

race_name_mapping = {
    'British Grand Prix': 'britain',
    'Japanese Grand Prix': 'japan', 
    'Australian Grand Prix': 'australia',
    'Chinese Grand Prix': 'china',
    'Monaco Grand Prix': 'monaco',
    'Spanish Grand Prix': 'spain',
    'Canadian Grand Prix': 'canada',
    'Austrian Grand Prix': 'austria',
    'French Grand Prix': 'france',
    'Hungarian Grand Prix': 'hungary',
    'Belgian Grand Prix': 'belgium',
    'Italian Grand Prix': 'italy',
    'Singapore Grand Prix': 'singapore',
    'Russian Grand Prix': 'russia',
    'Turkish Grand Prix': 'turkey',
    'United States Grand Prix': 'usa',
    'Mexican Grand Prix': 'mexico',
    'Brazilian Grand Prix': 'brazil',
    'Abu Dhabi Grand Prix': 'abu dhabi',
    'Bahrain Grand Prix': 'bahrain',
    'Saudi Arabian Grand Prix': 'saudi arabia'
}

event_name = "United States Grand Prix"
mapped_name = race_name_mapping.get(event_name, event_name.lower())

print(f"  原始名稱: {event_name}")
print(f"  映射名稱: {mapped_name}")
print(f"  映射狀態: {'✅ 已映射' if event_name in race_name_mapping else '❌ 未映射'}")

print("\n" + "=" * 80)
print("測試完成")
print("=" * 80)
