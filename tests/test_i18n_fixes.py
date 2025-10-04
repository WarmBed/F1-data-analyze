#!/usr/bin/env python3
"""
測試國際化修正 - 驗證 "請選擇" 和遙測分析模組的翻譯
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.gui_i18n import tr, GuiTranslator

def test_translations():
    """測試所有新增的翻譯鍵"""
    
    print("=" * 60)
    print("測試國際化修正 - Test Internationalization Fixes")
    print("=" * 60)
    
    # 測試語言列表
    languages = ['zh', 'en', 'ja']
    
    # 測試鍵列表
    test_keys = [
        ('please_select', '請選擇'),
        ('throttle_analysis', '油門分析'),
        ('brake_analysis', '煞車分析'),
        ('speed_analysis', '速度分析'),
        ('rpm_analysis', 'RPM分析'),
        ('gear_analysis', '檔位分析'),
        ('acceleration_analysis', '加速度分析'),
        ('distancediff_analysis', '距離差異分析'),
        ('speeddiff_analysis', '速度差異分析'),
        ('rain_analysis', '雨況分析'),
    ]
    
    for lang in languages:
        print(f"\n{'='*60}")
        print(f"語言 / Language: {lang.upper()}")
        print(f"{'='*60}")
        
        # 創建翻譯器並設定語言
        translator = GuiTranslator(language='en')  # 先用預設
        translator.set_language(lang)  # 再切換到測試語言
        
        for key, fallback in test_keys:
            translated = translator.t(key, fallback)
            status = "✅" if translated != fallback or lang == 'zh' else "⚠️"
            print(f"{status} {key:30} → {translated}")
    
    print("\n" + "=" * 60)
    print("測試完成 - Test Complete")
    print("=" * 60)
    
    # 測試下拉選單格式
    print("\n" + "=" * 60)
    print("測試下拉選單格式 - Test Dropdown Format")
    print("=" * 60)
    
    for lang in languages:
        translator = GuiTranslator(language='en')
        translator.set_language(lang)
        placeholder = f"-- {translator.t('please_select', '請選擇')} --"
        print(f"{lang.upper()}: {placeholder}")
    
    print("\n✅ 所有測試完成！")

if __name__ == '__main__':
    test_translations()
