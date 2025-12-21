#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ideal Lap 模組國際化測試腳本
Test Script for Ideal Lap Module Internationalization

測試項目：
1. 翻譯系統是否正確載入
2. 中文翻譯是否正確
3. 英文翻譯是否正確
4. 日文翻譯是否正確
5. Options Dialog 翻譯
6. Ranking Table Widget 翻譯

作者: F1T Team
日期: 2025-10-09
版本: 1.0.0
"""

import sys
import os

# 設定 UTF-8 輸出編碼（Windows 環境）
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    # 設定環境變數
    os.environ['PYTHONIOENCODING'] = 'utf-8'

from PyQt5.QtWidgets import QApplication
from core.gui_i18n import tr, set_gui_language, get_gui_language

def test_translation_keys():
    """測試所有翻譯鍵是否正確"""
    
    print("=" * 80)
    print("Ideal Lap 模組國際化測試")
    print("=" * 80)
    
    # 測試翻譯鍵列表
    test_keys = [
        # Options Dialog
        ('ideal_lap_options_title', 'Ideal Lap Analysis Options'),
        ('select_ideal_lap_analysis_type', 'Please select...'),
        ('ranking_table', 'Ranking Table'),
        ('sector_heatmap', 'Sector Heatmap'),
        ('sector_comparison', 'Sector Comparison'),
        
        # Ranking Table Widget - 統計摘要
        ('race_statistics_summary', 'Race Statistics Summary'),
        ('total_drivers', 'Total Drivers'),
        ('session_fastest_lap', 'Session Fastest Lap'),
        ('fastest_ideal_lap', 'Fastest Ideal Lap'),
        ('ideal_lap_range', 'Ideal Lap Range'),
        ('average_gap', 'Average Gap'),
        ('perfect_lap_rate', 'Perfect Lap Rate'),
        
        # 表格欄位
        ('table_header_position', 'Pos'),
        ('table_header_driver', 'Driver'),
        ('table_header_fastest_lap', 'Fastest Lap'),
        ('table_header_ideal_lap', 'Ideal Lap'),
        ('table_header_gap', 'Gap'),
        ('table_header_gap_to_fastest', 'Gap to Session Fastest'),
        ('table_header_sector_breakdown', 'Sectors'),
        ('table_header_action', 'Action'),
        
        # 按鈕與工具列
        ('export_csv', 'Export CSV'),
        ('detail_button', 'Details'),
        ('status_ready', 'Ready'),
        
        # Tooltip
        ('tooltip_no_fastest_lap_data', 'No fastest lap data'),
        ('tooltip_gap_near_perfect', 'Assessment: Near perfect lap'),
        ('tooltip_gap_moderate', 'Assessment: Moderate improvement potential'),
        ('tooltip_gap_significant', 'Assessment: Significant improvement potential'),
    ]
    
    # 測試三種語言
    languages = ['zh', 'en', 'ja']
    language_names = {
        'zh': '中文 (Chinese)',
        'en': '英文 (English)',
        'ja': '日文 (Japanese)'
    }
    
    results = {}
    
    for lang in languages:
        print(f"\n{'=' * 80}")
        print(f"測試語言: {language_names[lang]} ({lang})")
        print(f"{'=' * 80}")
        
        # 切換語言
        set_gui_language(lang)
        current_lang = get_gui_language()
        
        if current_lang != lang:
            print(f"❌ 語言切換失敗！預期: {lang}, 實際: {current_lang}")
            continue
        else:
            print(f"✅ 語言切換成功: {lang}")
        
        # 測試每個鍵
        lang_results = []
        for key, default in test_keys:
            translation = tr(key, default)
            
            # 檢查是否成功翻譯（不等於預設值表示有翻譯）
            is_translated = (translation != default) if lang != 'en' else True
            
            status = "✅" if is_translated or lang == 'en' else "⚠️ "
            
            print(f"  {status} {key}: {translation}")
            
            lang_results.append({
                'key': key,
                'translation': translation,
                'is_translated': is_translated
            })
        
        results[lang] = lang_results
        
        # 統計
        translated_count = sum(1 for r in lang_results if r['is_translated'])
        total_count = len(lang_results)
        percentage = (translated_count / total_count) * 100
        
        print(f"\n  📊 統計: {translated_count}/{total_count} 已翻譯 ({percentage:.1f}%)")
    
    # 最終總結
    print("\n" + "=" * 80)
    print("測試總結")
    print("=" * 80)
    
    for lang in languages:
        lang_results = results[lang]
        translated_count = sum(1 for r in lang_results if r['is_translated'])
        total_count = len(lang_results)
        percentage = (translated_count / total_count) * 100
        
        status = "✅ 完成" if percentage == 100 else f"⚠️  進度 {percentage:.1f}%"
        
        print(f"{language_names[lang]:20} : {status} ({translated_count}/{total_count})")
    
    print("\n" + "=" * 80)
    print("測試完成！")
    print("=" * 80)


def test_format_strings():
    """測試格式化字串功能"""
    
    print("\n" + "=" * 80)
    print("測試格式化字串")
    print("=" * 80)
    
    # 測試中文
    set_gui_language('zh')
    print(f"\n語言: 中文 (zh)")
    print(f"  status_loaded_drivers: {tr('status_loaded_drivers', 'Loaded {{count}} drivers').format(count=20)}")
    print(f"  tooltip_fastest_lap: {tr('tooltip_fastest_lap', 'Fastest Lap: {{time}}').format(time='1:23.456')}")
    print(f"  tooltip_gap_value: {tr('tooltip_gap_value', 'Gap: +{{gap}}s (+{{percentage}}%)').format(gap='0.234', percentage='0.25')}")
    
    # 測試英文
    set_gui_language('en')
    print(f"\n語言: 英文 (en)")
    print(f"  status_loaded_drivers: {tr('status_loaded_drivers', 'Loaded {{count}} drivers').format(count=20)}")
    print(f"  tooltip_fastest_lap: {tr('tooltip_fastest_lap', 'Fastest Lap: {{time}}').format(time='1:23.456')}")
    print(f"  tooltip_gap_value: {tr('tooltip_gap_value', 'Gap: +{{gap}}s (+{{percentage}}%)').format(gap='0.234', percentage='0.25')}")
    
    # 測試日文
    set_gui_language('ja')
    print(f"\n語言: 日文 (ja)")
    print(f"  status_loaded_drivers: {tr('status_loaded_drivers', 'Loaded {{count}} drivers').format(count=20)}")
    print(f"  tooltip_fastest_lap: {tr('tooltip_fastest_lap', 'Fastest Lap: {{time}}').format(time='1:23.456')}")
    print(f"  tooltip_gap_value: {tr('tooltip_gap_value', 'Gap: +{{gap}}s (+{{percentage}}%)').format(gap='0.234', percentage='0.25')}")


if __name__ == "__main__":
    # 創建 QApplication（翻譯系統可能需要）
    app = QApplication(sys.argv)
    
    # 執行測試
    test_translation_keys()
    test_format_strings()
    
    print("\n✅ 所有測試完成！")
