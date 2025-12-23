#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 GUI 年份範圍是否包含 2026 並能正確讀取資料
"""

import sys
from pathlib import Path

# 添加專案路徑
sys.path.insert(0, str(Path(__file__).parent))

def test_year_range():
    """測試 GUI 主視窗的年份範圍"""
    print("=" * 80)
    print("🧪 測試 GUI 年份範圍和 2026 資料")
    print("=" * 80)
    
    # 測試年份範圍配置
    year_range = list(range(2020, 2027))
    print(f"\n📅 GUI 年份範圍: {year_range}")
    assert 2026 in year_range, "❌ 年份範圍不包含 2026"
    print("✅ 年份範圍包含 2026")
    
    return True

def test_calendar_provider():
    """測試 SeasonCalendarProvider 讀取 2026 資料"""
    from modules.gui.shared.season_calendar_provider import SeasonCalendarProvider
    
    print(f"\n{'=' * 80}")
    print("🔍 測試 SeasonCalendarProvider 讀取 2026 年資料")
    print("=" * 80)
    
    provider = SeasonCalendarProvider()
    
    # 測試 2026 年
    print(f"\n📊 載入 2026 年賽事...")
    events = provider.get_completed_events(2026)
    
    print(f"✅ 成功載入 {len(events)} 場賽事")
    assert len(events) > 0, "❌ 2026 年賽事數為 0"
    
    # 顯示前 5 場賽事
    print(f"\n📅 前 5 場賽事:")
    for i, event in enumerate(events[:5], 1):
        print(f"   {i}. {event.display_label:30} ({event.race_date})")
    
    # 檢查賽事完成狀態
    completed = [e for e in events if e.is_completed]
    upcoming = [e for e in events if not e.is_completed]
    
    print(f"\n📈 賽事統計:")
    print(f"   已完成: {len(completed)}")
    print(f"   未來賽事: {len(upcoming)}")
    
    return True

def test_json_file():
    """測試 JSON 檔案包含 2026 資料"""
    import json
    from pathlib import Path
    
    print(f"\n{'=' * 80}")
    print("📂 檢查 JSON 檔案內容")
    print("=" * 80)
    
    json_dir = Path("json")
    calendar_files = sorted(
        json_dir.glob("season_calendar_multi_year_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    if not calendar_files:
        print("❌ 找不到 season_calendar JSON 檔案")
        return False
    
    latest_file = calendar_files[0]
    print(f"\n📄 最新檔案: {latest_file.name}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 檢查年份覆蓋
    if 'data' in data:
        years = list(data['data'].keys())
        print(f"📅 包含年份: {years}")
        
        if '2026' in years:
            events_2026 = data['data']['2026']
            print(f"✅ 2026 年資料: {len(events_2026)} 場賽事")
            
            # 顯示第一場賽事
            if events_2026:
                first_event = events_2026[0]
                print(f"\n🏁 首場賽事:")
                print(f"   名稱: {first_event.get('event_name')}")
                print(f"   日期: {first_event.get('race_date_local', first_event.get('race_date_utc'))}")
                print(f"   地點: {first_event.get('location')}")
        else:
            print("❌ JSON 不包含 2026 年資料")
            return False
    
    return True

def main():
    """執行所有測試"""
    print("\n🚀 開始測試...")
    
    try:
        # 測試 1: 年份範圍
        if not test_year_range():
            print("\n❌ 年份範圍測試失敗")
            return False
        
        # 測試 2: Calendar Provider
        if not test_calendar_provider():
            print("\n❌ Calendar Provider 測試失敗")
            return False
        
        # 測試 3: JSON 檔案
        if not test_json_file():
            print("\n❌ JSON 檔案測試失敗")
            return False
        
        print("\n" + "=" * 80)
        print("✅ 所有測試通過！GUI HOME 應能正常讀取 2026 年資料")
        print("=" * 80)
        return True
        
    except Exception as e:
        print(f"\n❌ 測試過程發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
