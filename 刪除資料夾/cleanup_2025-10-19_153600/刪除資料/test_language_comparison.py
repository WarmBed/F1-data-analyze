"""深度診斷：比較英文、日文、中文在 lap analysis 更新時的差異"""
import sys
import os
from typing import Dict, Any

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.gui_i18n import set_gui_language, get_gui_language, tr
from modules.gui.shared.season_calendar_provider import SeasonCalendarProvider

def test_language(lang_code: str, lang_name: str):
    """測試單一語言的完整流程"""
    print(f"\n{'='*80}")
    print(f"【{lang_name}】測試")
    print(f"{'='*80}")
    
    # 1. 設置語言
    set_gui_language(lang_code)
    current_lang = get_gui_language()
    print(f"\n1️⃣ 語言設置:")
    print(f"   要求語言: {lang_code}")
    print(f"   當前語言: {current_lang}")
    print(f"   設置成功: {'✅' if current_lang == lang_code else '❌'}")
    
    # 2. 獲取日曆數據
    print(f"\n2️⃣ 獲取賽季日曆:")
    provider = SeasonCalendarProvider()
    events = provider.get_completed_events(2025)
    print(f"   找到賽事數: {len(events)}")
    
    # 找到日本站
    japan_events = [e for e in events if 'japan' in e.race_key.lower()]
    if not japan_events:
        print(f"   ❌ 未找到日本站賽事")
        return None
    
    japan_event = japan_events[0]
    print(f"   日本站數據:")
    print(f"     - race_key: '{japan_event.race_key}'")
    print(f"     - display_label: '{japan_event.display_label}'")
    print(f"     - race_date: '{japan_event.race_date}'")
    
    # 3. 模擬 race_combo 的行為
    print(f"\n3️⃣ 模擬 race_combo 下拉選單:")
    race_combo_text = japan_event.display_label  # 這就是 race_combo.currentText() 會返回的值
    print(f"   race_combo.currentText(): '{race_combo_text}'")
    
    # 4. 測試 _get_race_key_from_display 的邏輯
    print(f"\n4️⃣ 測試 race 參數清理邏輯:")
    
    # 模擬 _display_to_race_key 映射表
    display_to_race_key = {}
    for event in events:
        display_to_race_key[event.display_label] = event.race_key
    
    print(f"   _display_to_race_key 映射表中有 {len(display_to_race_key)} 個條目")
    print(f"   查找鍵: '{race_combo_text}'")
    
    # 方法1: 使用映射表查找
    race_from_map = display_to_race_key.get(race_combo_text)
    print(f"   從映射表查找: '{race_from_map}' {'✅' if race_from_map else '❌ 未找到'}")
    
    # 方法2: 使用正則表達式清理（後備方案）
    import re
    race_from_regex = re.sub(r'\s*\(\d{4}-\d{2}-\d{2}\)\s*$', '', race_combo_text).strip()
    print(f"   正則表達式清理: '{race_from_regex}'")
    
    # 最終使用的 race 值
    final_race = race_from_map if race_from_map else race_from_regex
    print(f"   最終 race 值: '{final_race}' {'✅' if final_race == 'Japan' else '❌'}")
    
    # 5. 構建檔案搜尋模式
    print(f"\n5️⃣ JSON 檔案搜尋模式:")
    driver1 = "VER"
    driver2 = "LEC"
    year = "2025"
    session = "R"
    lap1 = 99
    lap2 = 99
    
    # 雙車手對比檔案模式
    patterns = [
        f"comparison_telemetry_{driver1}_{driver2}_{year}_{final_race}_{session}_Lap{lap1}_Lap{lap2}.json",
        f"comparison_telemetry_{driver1}_{driver2}_{year}_{final_race}_{session}_Lap{lap1}_Lap*.json",
        f"comparison_telemetry_{driver1}_{driver2}_{year}_{final_race}_{session}_Lap*_Lap{lap2}.json",
        f"comparison_telemetry_{driver1}_{driver2}_{year}_{final_race}_{session}_Lap*_Lap*.json"
    ]
    
    print(f"   搜尋參數:")
    print(f"     - driver1: {driver1}")
    print(f"     - driver2: {driver2}")
    print(f"     - year: {year}")
    print(f"     - race: {final_race}")
    print(f"     - session: {session}")
    print(f"     - lap1: {lap1}")
    print(f"     - lap2: {lap2}")
    print(f"\n   搜尋模式 (共 {len(patterns)} 個):")
    for i, pattern in enumerate(patterns, 1):
        print(f"     {i}. {pattern}")
    
    # 6. 實際搜尋檔案
    print(f"\n6️⃣ 實際搜尋 JSON 檔案:")
    import glob
    search_dirs = ["json", "json_exports", "cache"]
    found_files = []
    
    for search_dir in search_dirs:
        if not os.path.exists(search_dir):
            continue
        print(f"\n   📂 目錄: {search_dir}")
        for i, pattern in enumerate(patterns, 1):
            search_pattern = os.path.join(search_dir, pattern)
            matches = glob.glob(search_pattern)
            print(f"     模式 {i}: {'✅ 找到 ' + str(len(matches)) + ' 個' if matches else '❌ 無匹配'}")
            if matches:
                for match in matches:
                    print(f"       - {match}")
                    found_files.extend(matches)
    
    print(f"\n   搜尋結果: {'✅ 找到 ' + str(len(found_files)) + ' 個檔案' if found_files else '❌ 未找到任何檔案'}")
    
    # 7. 翻譯測試
    print(f"\n7️⃣ UI 翻譯測試:")
    test_keys = [
        'speed_analysis',
        'throttle_analysis', 
        'brake_analysis',
        'rpm_analysis',
        'gear_analysis',
        'acceleration_analysis'
    ]
    print(f"   測試翻譯鍵:")
    for key in test_keys:
        translated = tr(key, key)
        print(f"     - {key}: '{translated}'")
    
    return {
        'language': lang_code,
        'race_combo_text': race_combo_text,
        'race_from_map': race_from_map,
        'race_from_regex': race_from_regex,
        'final_race': final_race,
        'files_found': len(found_files),
        'is_correct': final_race == 'Japan' and len(found_files) > 0
    }

def main():
    print("🔍 深度診斷：比較英文、日文、中文在 lap analysis 更新時的差異\n")
    
    results = {}
    
    # 測試三種語言
    results['zh'] = test_language('zh', '中文 (Chinese)')
    results['en'] = test_language('en', '英文 (English)')
    results['ja'] = test_language('ja', '日文 (Japanese)')
    
    # 總結比較
    print(f"\n{'='*80}")
    print("📊 總結比較")
    print(f"{'='*80}\n")
    
    print(f"{'語言':<10} {'race_combo_text':<30} {'final_race':<15} {'檔案數':<10} {'狀態':<10}")
    print(f"{'-'*80}")
    
    for lang_code in ['zh', 'en', 'ja']:
        if lang_code not in results or not results[lang_code]:
            continue
        r = results[lang_code]
        lang_name = {'zh': '中文', 'en': '英文', 'ja': '日文'}[lang_code]
        status = '✅ 正常' if r['is_correct'] else '❌ 異常'
        print(f"{lang_name:<10} {r['race_combo_text']:<30} {r['final_race']:<15} {r['files_found']:<10} {status:<10}")
    
    print(f"\n{'='*80}")
    print("🔍 差異分析")
    print(f"{'='*80}\n")
    
    # 比較 race_combo_text
    race_texts = {lang: results[lang]['race_combo_text'] for lang in results if results[lang]}
    if len(set(race_texts.values())) == 1:
        print(f"✅ race_combo_text 在所有語言下相同: '{list(race_texts.values())[0]}'")
    else:
        print(f"❌ race_combo_text 在不同語言下不同:")
        for lang, text in race_texts.items():
            print(f"   - {lang}: '{text}'")
    
    # 比較 final_race
    final_races = {lang: results[lang]['final_race'] for lang in results if results[lang]}
    if len(set(final_races.values())) == 1:
        print(f"✅ final_race 在所有語言下相同: '{list(final_races.values())[0]}'")
    else:
        print(f"❌ final_race 在不同語言下不同:")
        for lang, race in final_races.items():
            print(f"   - {lang}: '{race}'")
    
    # 比較檔案搜尋結果
    files_found = {lang: results[lang]['files_found'] for lang in results if results[lang]}
    if len(set(files_found.values())) == 1 and list(files_found.values())[0] > 0:
        print(f"✅ 所有語言都能找到檔案 (找到 {list(files_found.values())[0]} 個)")
    else:
        print(f"❌ 不同語言找到的檔案數不同:")
        for lang, count in files_found.items():
            print(f"   - {lang}: {count} 個")
    
    print(f"\n{'='*80}")
    print("💡 結論")
    print(f"{'='*80}\n")
    
    all_correct = all(r['is_correct'] for r in results.values() if r)
    if all_correct:
        print("✅ 所有語言都正常工作，沒有發現差異")
    else:
        problems = [lang for lang, r in results.items() if r and not r['is_correct']]
        print(f"❌ 發現問題的語言: {', '.join(problems)}")
        
        for lang in problems:
            r = results[lang]
            print(f"\n{lang} 的問題:")
            if r['final_race'] != 'Japan':
                print(f"  - race 參數錯誤: 期望 'Japan'，實際 '{r['final_race']}'")
            if r['files_found'] == 0:
                print(f"  - 找不到 JSON 檔案 (使用 race='{r['final_race']}')")

if __name__ == "__main__":
    main()
