"""
簡化版視窗標題多國語言化測試
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.gui_i18n import tr, set_gui_language

def test_window_title_translation():
    """測試視窗標題翻譯鍵"""
    print("\n" + "="*70)
    print("測試：視窗標題翻譯鍵")
    print("="*70)
    
    languages = [
        ('zh', '繁體中文'),
        ('en', 'English'),
        ('ja', '日本語')
    ]
    
    # 預期翻譯
    expected = {
        'all_drivers_brake_performance': {
            'zh': '全車手煞車性能',
            'en': 'All Drivers Brake Performance',
            'ja': '全ドライバーブレーキ性能'
        },
        'all_drivers_straight_speed': {
            'zh': '全車手速度與加速',
            'en': 'All Drivers Speed & Acceleration',
            'ja': '全ドライバー速度と加速'
        }
    }
    
    all_passed = True
    
    for lang_code, lang_name in languages:
        print(f"\n[{lang_name} ({lang_code})]")
        print("-" * 70)
        
        # 切換語言
        set_gui_language(lang_code)
        
        # 測試 brake performance
        brake_name = tr('all_drivers_brake_performance', 'All Drivers Brake Performance')
        expected_brake = expected['all_drivers_brake_performance'][lang_code]
        
        if brake_name == expected_brake:
            print(f"  ✅ Brake Performance: {brake_name}")
        else:
            print(f"  ❌ Brake Performance: {brake_name} (預期: {expected_brake})")
            all_passed = False
        
        # 測試 straight speed
        speed_name = tr('all_drivers_straight_speed', 'All Drivers Speed & Acceleration')
        expected_speed = expected['all_drivers_straight_speed'][lang_code]
        
        if speed_name == expected_speed:
            print(f"  ✅ Straight Speed: {speed_name}")
        else:
            print(f"  ❌ Straight Speed: {speed_name} (預期: {expected_speed})")
            all_passed = False
        
        # 顯示完整標題格式
        brake_title = f"{brake_name}_2025_Singapore_R"
        speed_title = f"{speed_name}_2025_Singapore_R"
        print(f"\n  視窗標題範例：")
        print(f"    - {brake_title}")
        print(f"    - {speed_title}")
    
    return all_passed

def main():
    """執行測試"""
    print("\n" + "="*70)
    print("🌍 視窗標題多國語言化測試（簡化版）")
    print("="*70)
    
    try:
        passed = test_window_title_translation()
        
        print("\n" + "="*70)
        if passed:
            print("🎉 所有測試通過！")
            print("="*70)
            print("\n✅ 修復摘要：")
            print("  1. ✅ 移除語言判斷邏輯（if language == 'zh'）")
            print("  2. ✅ 直接使用 tr() 函數獲取多國語言化的模組名稱")
            print("  3. ✅ 支援繁體中文、英文、日文")
            print("\n視窗標題格式：")
            print("  - 繁體中文：全車手煞車性能_2025_Singapore_R")
            print("  - English：All Drivers Brake Performance_2025_Singapore_R")
            print("  - 日本語：全ドライバーブレーキ性能_2025_Singapore_R")
            print("\n建議：請手動啟動 GUI 並切換語言驗證視窗標題")
            print("命令：python f1t_gui_main.py")
            print("="*70)
            return True
        else:
            print("❌ 部分測試失敗")
            print("="*70)
            return False
        
    except Exception as e:
        print(f"\n❌ 測試失敗：{e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
