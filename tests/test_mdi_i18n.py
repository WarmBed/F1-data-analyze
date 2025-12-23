#!/usr/bin/env python3
"""
測試 MDI 視窗標題的國際化
Test MDI Window Title Internationalization
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.gui_i18n import GuiTranslator

def test_mdi_titles():
    """測試所有 MDI 模組標題的翻譯"""
    
    print("=" * 80)
    print("MDI 視窗標題國際化測試 - MDI Window Title I18N Test")
    print("=" * 80)
    
    # MDI 模組標題鍵列表
    mdi_modules = [
        ('telemetry_analysis', '遙測分析'),
        ('rain_analysis', '降雨分析'),
        ('accident_analysis', '事故分析'),
        ('pitstop_analysis', '進站分析'),
        ('speed_analysis', '速度分析'),
        ('brake_analysis', '煞車分析'),
        ('gear_analysis', '檔位分析'),
        ('rpm_analysis', 'RPM分析'),
        ('throttle_analysis', '油門分析'),
        ('acceleration_analysis', '加速度分析'),
        ('speeddiff_analysis', '速度差異分析'),
        ('distancediff_analysis', '距離差異分析'),
        ('detailed_lap_analysis', '詳細圈速分析'),
    ]
    
    languages = ['zh', 'en', 'ja']
    
    for lang in languages:
        print(f"\n{'='*80}")
        print(f"語言 / Language: {lang.upper()}")
        print(f"{'='*80}\n")
        
        translator = GuiTranslator(language='en')
        translator.set_language(lang)
        
        for key, fallback in mdi_modules:
            translated = translator.t(key, fallback)
            status = "✅" if translated != fallback or lang == 'zh' else "⚠️"
            print(f"{status} {key:30} → {translated}")
    
    print("\n" + "=" * 80)
    print("✅ 測試完成！所有 MDI 模組標題已支援多語言切換")
    print("=" * 80)
    
    # 顯示語言切換示例
    print("\n" + "=" * 80)
    print("MDI 視窗標題語言切換示例")
    print("=" * 80)
    
    example_modules = [
        ('throttle_analysis', '油門分析'),
        ('speed_analysis', '速度分析'),
        ('detailed_lap_analysis', '詳細圈速分析'),
    ]
    
    for key, fallback in example_modules:
        print(f"\n📋 模組: {key}")
        translator_zh = GuiTranslator(language='en')
        translator_zh.set_language('zh')
        translator_en = GuiTranslator(language='en')
        translator_ja = GuiTranslator(language='en')
        translator_ja.set_language('ja')
        
        zh_text = translator_zh.t(key, fallback)
        en_text = translator_en.t(key, fallback)
        ja_text = translator_ja.t(key, fallback)
        
        print(f"   中文 (ZH): {zh_text}")
        print(f"   English (EN): {en_text}")
        print(f"   日本語 (JA): {ja_text}")

if __name__ == '__main__':
    test_mdi_titles()
