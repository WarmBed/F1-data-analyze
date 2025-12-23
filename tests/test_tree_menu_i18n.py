"""
測試樹狀圖選單的多國語言化

驗證項目：
1. Straight Speed Analysis (主項目)
2. All Drivers Speed & Acceleration (子項目)
3. All Drivers Brake Performance (子項目)
"""

import os
import sys

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.gui_i18n import tr, set_gui_language

def test_tree_menu_i18n():
    """測試樹狀圖選單的多國語言化"""
    print("\n" + "="*70)
    print("測試：樹狀圖選單的多國語言化")
    print("="*70)
    
    # 測試項目
    menu_items = [
        ('straight_speed_analysis', 'Straight Speed Analysis'),
        ('all_drivers_straight_speed', 'All Drivers Speed & Acceleration'),
        ('all_drivers_brake_performance', 'All Drivers Brake Performance'),
    ]
    
    # 預期翻譯
    expected_translations = {
        'straight_speed_analysis': {
            'zh': '直線速度分析',
            'en': 'Straight Speed Analysis',
            'ja': '直線速度分析'
        },
        'all_drivers_straight_speed': {
            'zh': '全車手速度與加速',
            'en': 'All Drivers Speed & Acceleration',
            'ja': '全ドライバー速度と加速'
        },
        'all_drivers_brake_performance': {
            'zh': '全車手煞車性能',
            'en': 'All Drivers Brake Performance',
            'ja': '全ドライバーブレーキ性能'
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
        
        for key, fallback in menu_items:
            # 獲取翻譯
            translated = tr(key, fallback)
            expected = expected_translations[key][lang_code]
            
            # 驗證
            if translated == expected:
                print(f"  ✅ {key}: {translated}")
            else:
                print(f"  ❌ {key}: {translated} (預期: {expected})")
                all_passed = False
    
    return all_passed

def test_complete_tree_structure():
    """測試完整的樹狀圖結構"""
    print("\n" + "="*70)
    print("測試：完整的樹狀圖結構（模擬 GUI 樹狀圖）")
    print("="*70)
    
    # 模擬 GUI 樹狀圖結構
    tree_structure = {
        'driver_performance_analysis': {
            'straight_speed_analysis': [
                'all_drivers_straight_speed',
                'all_drivers_brake_performance'
            ]
        }
    }
    
    languages = [
        ('zh', '繁體中文'),
        ('en', 'English'),
        ('ja', '日本語')
    ]
    
    for lang_code, lang_name in languages:
        print(f"\n[{lang_name}]")
        print("-" * 70)
        
        # 切換語言
        set_gui_language(lang_code)
        
        # 主分類
        parent = tr('driver_performance_analysis', 'Driver Performance Analysis')
        print(f"📁 {parent}")
        
        # 子分類
        speed_parent = tr('straight_speed_analysis', 'Straight Speed Analysis')
        print(f"  📁 {speed_parent}")
        
        # 子項目
        speed_item = tr('all_drivers_straight_speed', 'All Drivers Speed & Acceleration')
        print(f"      📄 {speed_item}")
        
        brake_item = tr('all_drivers_brake_performance', 'All Drivers Brake Performance')
        print(f"      📄 {brake_item}")
    
    print("\n" + "="*70)
    print("✅ 樹狀圖結構顯示完成")
    print("="*70)
    
    return True

def main():
    """執行所有測試"""
    print("\n" + "="*70)
    print("🌍 樹狀圖選單多國語言化測試")
    print("="*70)
    
    try:
        # 測試 1：樹狀圖選單翻譯
        test1_passed = test_tree_menu_i18n()
        
        # 測試 2：完整樹狀圖結構
        test2_passed = test_complete_tree_structure()
        
        # 總結
        print("\n" + "="*70)
        if test1_passed and test2_passed:
            print("🎉 所有測試通過！")
            print("="*70)
            print("\n✅ 修復摘要：")
            print("  1. ✅ 添加 straight_speed_analysis 翻譯")
            print("  2. ✅ 添加 all_drivers_straight_speed 翻譯")
            print("  3. ✅ 添加 all_drivers_brake_performance 翻譯")
            print("\n建議：請手動啟動 GUI 驗證樹狀圖顯示")
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
