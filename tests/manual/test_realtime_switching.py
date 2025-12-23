#!/usr/bin/env python3
"""
快速測試語言切換即時性
Quick test for real-time language switching
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.gui_i18n import tr, set_gui_language, get_gui_language

def test_menu_translations():
    """測試選單翻譯"""
    print("=" * 80)
    print("測試選單翻譯 - Menu Translations Test")
    print("=" * 80)
    
    menu_keys = [
        ('file_menu', 'File'),
        ('analysis_menu', 'Analysis'),
        ('view_menu', 'View'),
        ('tools_menu', 'Tools'),
    ]
    
    languages = ['en', 'zh', 'ja']
    
    for lang in languages:
        set_gui_language(lang)
        print(f"\n語言 / Language: {lang}")
        print("-" * 80)
        
        for key, default in menu_keys:
            result = tr(key, default)
            status = "✅" if result != key else "❌"
            print(f"  {status} {key:20} = {result}")

def test_function_tree_translations():
    """測試功能樹翻譯"""
    print("\n" + "=" * 80)
    print("測試功能樹翻譯 - Function Tree Translations Test")
    print("=" * 80)
    
    tree_keys = [
        ('analysis_modules', '分析模組'),
        ('single_race_analysis', '[TOOL] Single Race Analysis'),
        ('rain_analysis', 'Rain Analysis'),
        ('track_analysis', 'Track Analysis'),
        ('pitstop_analysis', 'Pitstop Analysis'),
        ('accident_analysis', 'Accident Analysis'),
        ('driver_analysis', 'Driver Analysis'),
        ('tire_strategy_analysis', 'Tire Strategy Analysis'),
        ('single_race_driver_analysis', '🚗 Single Race Driver Analysis'),
        ('lap_analysis', 'Lap Analysis'),
        ('detailed_lap_analysis', 'Detailed Lap Analysis'),
    ]
    
    languages = ['en', 'zh', 'ja']
    
    for lang in languages:
        set_gui_language(lang)
        print(f"\n語言 / Language: {lang}")
        print("-" * 80)
        
        for key, default in tree_keys:
            result = tr(key, default)
            status = "✅" if result != key else "❌"
            # 縮短顯示以便閱讀
            display_result = result[:50] + "..." if len(result) > 50 else result
            print(f"  {status} {key:30} = {display_result}")

def test_complete_switching():
    """測試完整切換流程"""
    print("\n" + "=" * 80)
    print("測試完整切換流程 - Complete Switching Test")
    print("=" * 80)
    
    test_keys = [
        # 選單
        ('file_menu', 'File'),
        ('analysis_menu', 'Analysis'),
        # 功能樹
        ('analysis_modules', '分析模組'),
        ('rain_analysis', 'Rain Analysis'),
        # Toolbar
        ('year_label', 'Year:'),
        ('race_label', 'Race:'),
        # 視窗標題
    ('main_window_title', 'F1 TelemetryStation Pro v0.0'),
    ]
    
    print("\n切換順序: en -> zh -> ja -> en")
    print("-" * 80)
    
    languages = ['en', 'zh', 'ja', 'en']
    
    for lang in languages:
        set_gui_language(lang)
        current = get_gui_language()
        
        print(f"\n切換到 {lang} (當前: {current})")
        
        if current != lang:
            print(f"  ❌ 語言設定失敗！")
        else:
            print(f"  ✅ 語言設定成功")
            
        # 顯示關鍵翻譯
        print(f"  選單: {tr('file_menu', 'File')} / {tr('analysis_menu', 'Analysis')}")
        print(f"  功能樹標題: {tr('analysis_modules', '分析模組')}")
        print(f"  分析項: {tr('rain_analysis', 'Rain Analysis')}")

def main():
    """主測試函數"""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 25 + "語言切換即時性測試" + " " * 25 + "║")
    print("║" + " " * 20 + "Language Switching Real-Time Test" + " " * 20 + "║")
    print("╚" + "═" * 78 + "╝")
    print()
    
    try:
        test_menu_translations()
        test_function_tree_translations()
        test_complete_switching()
        
        print("\n" + "=" * 80)
        print("測試完成！Test Complete!")
        print("=" * 80 + "\n")
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
