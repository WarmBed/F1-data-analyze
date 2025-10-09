"""測試日語模式下的 race_key 問題"""
from core.gui_i18n import set_gui_language, get_gui_language
from modules.gui.shared.season_calendar_provider import SeasonCalendarProvider

print("========== 測試開始 ==========")

# 測試中文模式
print("\n【中文模式】")
set_gui_language('zh')
print(f"當前語言: {get_gui_language()}")
provider_zh = SeasonCalendarProvider()
events_zh = provider_zh.get_completed_events(2025)
japan_zh = [e for e in events_zh if 'japan' in e.race_key.lower()]
if japan_zh:
    event = japan_zh[0]
    print(f"  race_key: {event.race_key}")
    print(f"  display_label: {event.display_label}")

# 測試英文模式
print("\n【英文模式】")
set_gui_language('en')
print(f"當前語言: {get_gui_language()}")
provider_en = SeasonCalendarProvider()
events_en = provider_en.get_completed_events(2025)
japan_en = [e for e in events_en if 'japan' in e.race_key.lower()]
if japan_en:
    event = japan_en[0]
    print(f"  race_key: {event.race_key}")
    print(f"  display_label: {event.display_label}")

# 測試日語模式
print("\n【日語模式】")
set_gui_language('ja')
print(f"當前語言: {get_gui_language()}")
provider_ja = SeasonCalendarProvider()
events_ja = provider_ja.get_completed_events(2025)
japan_ja = [e for e in events_ja if 'japan' in e.race_key.lower()]
if japan_ja:
    event = japan_ja[0]
    print(f"  race_key: {event.race_key}")
    print(f"  display_label: {event.display_label}")

print("\n========== 測試結束 ==========")
print("\n結論:")
if japan_zh and japan_en and japan_ja:
    zh_key = japan_zh[0].race_key
    en_key = japan_en[0].race_key
    ja_key = japan_ja[0].race_key
    
    if zh_key == en_key == ja_key:
        print(f"✅ race_key 在所有語言下都相同: {zh_key}")
    else:
        print(f"❌ race_key 不一致!")
        print(f"   中文: {zh_key}")
        print(f"   英文: {en_key}")
        print(f"   日語: {ja_key}")
