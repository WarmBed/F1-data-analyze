"""
測試視窗標題的多國語言化

驗證項目：
1. All Drivers Brake Performance 視窗標題
2. All Drivers Straight Line Speed 視窗標題
3. 支援繁體中文、英文、日文
"""

import os
import sys

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from PyQt5.QtWidgets import QApplication
from core.gui_i18n import tr, set_gui_language

# 創建 QApplication（GUI 測試需要）
app = QApplication(sys.argv)

def test_window_title_i18n():
    """測試視窗標題的多國語言化"""
    print("\n" + "="*70)
    print("測試：視窗標題的多國語言化")
    print("="*70)
    
    # 導入 MDI 類別
    from modules.gui.all_drivers_brake_performance_analysis.all_drivers_brake_performance_mdi import AllDriversBrakePerformanceMDI
    from modules.gui.all_drivers_straight_line_speed_analysis.all_drivers_straight_line_speed_mdi import AllDriversStraightLineSpeedMDI
    
    # 測試數據
    test_params = {
        'year': '2025',
        'race': 'Singapore',
        'session': 'R'
    }
    
    # 預期標題
    expected_titles = {
        'brake': {
            'zh': '全車手煞車性能_2025_Singapore_R',
            'en': 'All Drivers Brake Performance_2025_Singapore_R',
            'ja': '全ドライバーブレーキ性能_2025_Singapore_R'
        },
        'speed': {
            'zh': '全車手速度與加速_2025_Singapore_R',
            'en': 'All Drivers Speed & Acceleration_2025_Singapore_R',
            'ja': '全ドライバー速度と加速_2025_Singapore_R'
        }
    }
    
    languages = [
        ('zh', '繁體中文'),
        ('en', 'English'),
        ('ja', '日本語')
    ]
    
    all_passed = True
    
    for lang_code, lang_name in languages:
        print(f"\n[{lang_name} ({lang_code})]")
        print("-" * 70)
        
        # 切換語言
        set_gui_language(lang_code)
        
        # 測試 Brake Performance 標題
        brake_mdi = AllDriversBrakePerformanceMDI()
        brake_title = brake_mdi.get_window_title(**test_params)
        expected_brake = expected_titles['brake'][lang_code]
        
        if brake_title == expected_brake:
            print(f"  ✅ Brake Performance: {brake_title}")
        else:
            print(f"  ❌ Brake Performance: {brake_title}")
            print(f"     預期: {expected_brake}")
            all_passed = False
        
        # 測試 Straight Line Speed 標題
        speed_mdi = AllDriversStraightLineSpeedMDI()
        speed_title = speed_mdi.get_window_title(**test_params)
        expected_speed = expected_titles['speed'][lang_code]
        
        if speed_title == expected_speed:
            print(f"  ✅ Straight Line Speed: {speed_title}")
        else:
            print(f"  ❌ Straight Line Speed: {speed_title}")
            print(f"     預期: {expected_speed}")
            all_passed = False
    
    return all_passed

def test_window_title_display():
    """測試視窗標題顯示格式"""
    print("\n" + "="*70)
    print("測試：視窗標題顯示格式（模擬實際顯示）")
    print("="*70)
    
    languages = [
        ('zh', '繁體中文'),
        ('en', 'English'),
        ('ja', '日本語')
    ]
    
    from modules.gui.all_drivers_brake_performance_analysis.all_drivers_brake_performance_mdi import AllDriversBrakePerformanceMDI
    from modules.gui.all_drivers_straight_line_speed_analysis.all_drivers_straight_line_speed_mdi import AllDriversStraightLineSpeedMDI
    
    for lang_code, lang_name in languages:
        print(f"\n[{lang_name}]")
        print("-" * 70)
        
        # 切換語言
        set_gui_language(lang_code)
        
        # Brake Performance
        brake_mdi = AllDriversBrakePerformanceMDI()
        brake_title = brake_mdi.get_window_title('2025', 'Singapore', 'R')
        print(f"  視窗 1: {brake_title}")
        
        # Straight Line Speed
        speed_mdi = AllDriversStraightLineSpeedMDI()
        speed_title = speed_mdi.get_window_title('2025', 'Singapore', 'R')
        print(f"  視窗 2: {speed_title}")
    
    print("\n" + "="*70)
    print("✅ 視窗標題顯示格式測試完成")
    print("="*70)
    
    return True

def main():
    """執行所有測試"""
    print("\n" + "="*70)
    print("🌍 視窗標題多國語言化測試")
    print("="*70)
    
    try:
        # 測試 1：視窗標題翻譯
        test1_passed = test_window_title_i18n()
        
        # 測試 2：視窗標題顯示格式
        test2_passed = test_window_title_display()
        
        # 總結
        print("\n" + "="*70)
        if test1_passed and test2_passed:
            print("🎉 所有測試通過！")
            print("="*70)
            print("\n✅ 修復摘要：")
            print("  1. ✅ All Drivers Brake Performance 視窗標題支援多國語言")
            print("  2. ✅ All Drivers Straight Line Speed 視窗標題支援多國語言")
            print("  3. ✅ 支援繁體中文、英文、日文")
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
