#!/usr/bin/env python3
"""
測試 Championship Standings 智能刷新機制

驗證：
1. 正常模式：120 小時（賽程間期）
2. 加速模式：12 小時（賽前 2 天內）
"""

from datetime import datetime, timezone
from CLI_modules.cli.analyzer.championship_standings_analysis import (
    _determine_standings_refresh_interval,
    check_standings_freshness,
    STANDINGS_REFRESH_HOURS_NORMAL,
    STANDINGS_REFRESH_HOURS_RACE_APPROACHING,
)

print("=" * 70)
print("Championship Standings 智能刷新機制測試")
print("=" * 70)

# 測試 1: 檢查當前刷新間隔
print("\n[測試 1] 檢查 2025 賽季當前刷新間隔")
interval_2025 = _determine_standings_refresh_interval(2025)
print(f"✅ 當前刷新間隔: {interval_2025} 小時")

if interval_2025 == STANDINGS_REFRESH_HOURS_NORMAL:
    print(f"📊 狀態: 正常模式 ({STANDINGS_REFRESH_HOURS_NORMAL}h) - 無臨近賽事")
elif interval_2025 == STANDINGS_REFRESH_HOURS_RACE_APPROACHING:
    print(f"🏁 狀態: 加速模式 ({STANDINGS_REFRESH_HOURS_RACE_APPROACHING}h) - 賽事臨近！")

# 測試 2: 檢查積分檔案新鮮度
print("\n[測試 2] 檢查 2025 積分檔案新鮮度")
freshness = check_standings_freshness(2025)

if freshness.get("exists"):
    print(f"✅ 檔案存在: {freshness['path']}")
    print(f"📅 檔案年齡: {freshness['age_formatted']} ({freshness['age_hours']} 小時)")
    print(f"🔄 刷新間隔: {freshness.get('refresh_interval_hours', 'N/A')} 小時")
    print(f"✨ 是否新鮮: {'是' if freshness['is_fresh'] else '否'}")
    print(f"🔧 需要重新生成: {'是' if freshness['should_regenerate'] else '否'}")
else:
    print(f"❌ 檔案不存在: {freshness['reason']}")

# 測試 3: 顯示即將到來的賽事
print("\n[測試 3] 2025 賽季接下來的賽事")
try:
    import json
    from pathlib import Path
    
    json_dir = Path("json")
    calendar_files = sorted(
        json_dir.glob("season_calendar_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    
    if calendar_files:
        with open(calendar_files[0], "r", encoding="utf-8") as f:
            calendar_data = json.load(f)
        
        events_by_year = calendar_data.get("data", {}).get("events_by_year", {})
        events_2025 = events_by_year.get("2025", [])
        
        upcoming = [e for e in events_2025 if not e.get("is_completed", False)]
        
        now = datetime.now(timezone.utc)
        print(f"📅 當前時間: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"🏁 未完成賽事數: {len(upcoming)}")
        print("\n最近 3 場賽事:")
        
        for i, event in enumerate(upcoming[:3], 1):
            event_name = event.get("event_name", "Unknown")
            race_date_str = event.get("race_date")
            days_until = event.get("days_until_race", 'N/A')
            
            if race_date_str:
                race_date = datetime.strptime(race_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                days_diff = (race_date - now).days
                
                # 判斷是否在加速閾值內
                in_threshold = -1 <= days_diff <= 2
                status = "🚨 加速模式" if in_threshold else "📊 正常模式"
                
                print(f"  {i}. {event_name}")
                print(f"     日期: {race_date_str}")
                print(f"     距離: {days_diff} 天")
                print(f"     狀態: {status}")
            else:
                print(f"  {i}. {event_name}")
                print(f"     距離: {days_until} 天")
    else:
        print("❌ 找不到 season_calendar JSON 檔案")
        
except Exception as e:
    print(f"❌ 讀取賽事資料失敗: {e}")

print("\n" + "=" * 70)
print("測試完成！")
print("=" * 70)

# 總結說明
print("\n📋 智能刷新機制說明:")
print("  • 正常模式: 120 小時 (5 天) - 賽程穩定時期")
print("  • 加速模式: 12 小時 - 賽前 2 天內或賽後 1 天內")
print("  • 觸發條件: -1 <= days_until_race <= 2")
print("\n🎯 預期行為:")
print("  • 墨西哥站 (2025-10-26) 距離 6 天 → 正常模式")
print("  • 到 2025-10-24 後 → 自動切換加速模式")
print("  • 比賽結束後 1 天內仍保持加速模式")
