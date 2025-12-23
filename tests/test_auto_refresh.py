#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試賽後自動刷新機制

驗證 Function 96/97/99 的智慧刷新邏輯
"""

import asyncio
import json
from datetime import datetime, timezone

print("=" * 80)
print("測試賽後自動刷新機制")
print("=" * 80)

# 測試 1: Function 99 (Season Calendar) 賽後檢查
print("\n🧪 測試 1: Function 99 - Season Calendar 賽後智慧刷新")
print("-" * 80)

from CLI_modules.cli.analyzer.season_calendar_analysis import check_calendar_freshness

result_f99 = check_calendar_freshness(all_years=True)
print(json.dumps(result_f99, indent=2, ensure_ascii=False))

if result_f99.get('should_regenerate'):
    print(f"\n✅ 測試通過: Function 99 正確偵測到需要刷新")
    print(f"   - 觸發模式: {result_f99.get('trigger_mode')}")
    print(f"   - 需要更新的賽事: {len(result_f99.get('events_to_update', []))}")
else:
    print(f"\n❌ 測試失敗: Function 99 未偵測到刷新需求")

# 測試 2: Function 97 (Championship Standings) 賽後檢查
print("\n\n🧪 測試 2: Function 97 - Championship Standings 賽後加速模式")
print("-" * 80)

from CLI_modules.cli.analyzer.championship_standings_analysis import check_standings_freshness

result_f97 = check_standings_freshness(2025)
print(json.dumps(result_f97, indent=2, ensure_ascii=False))

if result_f97.get('should_regenerate'):
    print(f"\n✅ 測試通過: Function 97 正確偵測到需要刷新")
    print(f"   - 刷新間隔: {result_f97.get('refresh_interval_hours')} 小時")
    print(f"   - 原因: {result_f97.get('reason')}")
else:
    print(f"\n❌ 測試失敗: Function 97 未偵測到刷新需求")

# 測試 3: Function 96 (Weather Forecast) 賽後檢查
print("\n\n🧪 測試 3: Function 96 - Weather Forecast 智慧刷新")
print("-" * 80)

from CLI_modules.cli.analyzer.race_weather_forecast import check_weather_forecast_freshness

result_f96 = check_weather_forecast_freshness(2025, "Las Vegas")
print(json.dumps(result_f96, indent=2, ensure_ascii=False))

if not result_f96.get('exists'):
    print(f"\n⚠️ 警告: Las Vegas 天氣數據不存在（正常情況）")
    print(f"   - 建議: 執行 Function 96 生成天氣預報")
else:
    if result_f96.get('should_regenerate'):
        print(f"\n✅ 測試通過: Function 96 正確偵測到需要刷新")
        print(f"   - 刷新間隔: {result_f96.get('refresh_interval_hours')} 小時")
    else:
        print(f"\n✅ 測試通過: Function 96 數據仍新鮮")

# 測試 4: API 監控器模擬測試
print("\n\n🧪 測試 4: API 監控器邏輯驗證")
print("-" * 80)

async def test_monitor_logic():
    """模擬監控器邏輯"""
    from api.services.race_event_monitor import RaceEventMonitor
    from api.services.simple_analysis_service import SimpleF1AnalysisService
    
    print("初始化監控器...")
    analysis_service = SimpleF1AnalysisService()
    monitor = RaceEventMonitor(analysis_service)
    
    # 測試載入 Season Calendar
    print("測試載入 Season Calendar...")
    success = await monitor._load_calendar()
    
    if success:
        print(f"✅ Season Calendar 載入成功")
        print(f"   - 監控年份: {list(monitor.calendar_data.keys())}")
        
        # 檢查 Las Vegas 賽事
        vegas_events = [
            e for e in monitor.calendar_data.get('2025', []) 
            if e.get('location') == 'Las Vegas'
        ]
        
        if vegas_events:
            vegas = vegas_events[0]
            race_date = datetime.fromisoformat(vegas['race_date_utc'].replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            hours_since = (now - race_date).total_seconds() / 3600
            
            print(f"\n🏁 Las Vegas 賽事狀態:")
            print(f"   - Round: {vegas['round']}")
            print(f"   - is_completed: {vegas['is_completed']}")
            print(f"   - 賽後經過: {hours_since:.1f} 小時")
            
            if 0 <= hours_since <= 72:
                print(f"   - ✅ 應該觸發賽後刷新 (0-72h 內)")
            else:
                print(f"   - ⏭️ 超出賽後監控窗口")
        else:
            print("❌ 找不到 Las Vegas 賽事")
    else:
        print("❌ Season Calendar 載入失敗")
    
    return success

# 執行異步測試
try:
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # 如果已有 event loop，創建新的任務
        task = asyncio.ensure_future(test_monitor_logic())
        print("⏳ 異步測試已啟動...")
    else:
        # 如果沒有 event loop，直接運行
        result = loop.run_until_complete(test_monitor_logic())
except Exception as e:
    print(f"❌ 監控器測試失敗: {e}")
    import traceback
    traceback.print_exc()

# 總結
print("\n" + "=" * 80)
print("測試總結")
print("=" * 80)

all_tests_passed = (
    result_f99.get('should_regenerate', False) and
    result_f97.get('should_regenerate', False)
)

if all_tests_passed:
    print("✅ 所有核心測試通過！")
    print("\n建議後續步驟：")
    print("1. 執行 CLI 手動刷新: python f1_analysis_modular_main.py -f 99 --force")
    print("2. 執行 CLI 手動刷新: python f1_analysis_modular_main.py -f 97 -y 2025 --force")
    print("3. 啟動 API 服務器: python refactored_api.py")
    print("4. 觀察監控器日誌，確認自動刷新運作")
else:
    print("⚠️ 部分測試未通過，請檢查日誌")

print("\n" + "=" * 80)
