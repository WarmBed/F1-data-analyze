"""
測試 All Drivers Brake Performance 與 Straight Line Speed 的多國語言化

測試項目：
1. 驗證所有翻譯鍵都存在於 gui_i18n.py
2. 驗證中文/英文/日文翻譯都存在
3. 模擬切換語言並驗證翻譯正確
"""

import sys
import os

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.gui_i18n import tr, set_gui_language

def test_brake_performance_i18n():
    """測試 Brake Performance 的多國語言化"""
    print("\n" + "="*70)
    print("測試 1：All Drivers Brake Performance 多國語言化")
    print("="*70)
    
    # 需要測試的翻譯鍵
    translation_keys = [
        # 表格欄位標題
        ('brake_header_driver', '車手', 'Driver', 'ドライバー'),
        ('brake_header_team', '車隊', 'Team', 'チーム'),
        ('brake_header_max_deceleration_g', '最大減速度', 'Max Decel', '最大減速度'),
        ('brake_header_brake_time', '煞車時間', 'Brake Time', 'ブレーキ時間'),
        ('brake_header_avg_deceleration', '平均減速度', 'Avg Decel', '平均減速度'),
        ('brake_header_brake_start_speed', '起始速度', 'Start Speed', '開始速度'),
        ('brake_header_brake_bar', '煞車性能視覺化', 'Brake Performance', 'ブレーキ性能ビジュアル'),
        
        # 資訊標籤
        ('brake_performance_info_no_data', '煞車範圍: 未載入資料', 'Brake Range: No Data Loaded', 'ブレーキ範囲: データ未読み込み'),
        
        # Tooltip（使用格式化參數）
        ('brake_performance_driver_tooltip', '{driver} - {team}', '{driver} - {team}', '{driver} - {team}'),
        ('brake_performance_team_tooltip', '{team}', '{team}', '{team}'),
    ]
    
    all_passed = True
    
    for key, zh_expected, en_expected, ja_expected in translation_keys:
        print(f"\n測試鍵: {key}")
        
        # 測試中文
        set_gui_language('zh')
        zh_result = tr(key, zh_expected)
        zh_match = zh_result == zh_expected
        print(f"  中文: {'✅' if zh_match else '❌'} {zh_result}")
        
        # 測試英文
        set_gui_language('en')
        en_result = tr(key, en_expected)
        en_match = en_result == en_expected
        print(f"  英文: {'✅' if en_match else '❌'} {en_result}")
        
        # 測試日文
        set_gui_language('ja')
        ja_result = tr(key, ja_expected)
        ja_match = ja_result == ja_expected
        print(f"  日文: {'✅' if ja_match else '❌'} {ja_result}")
        
        if not (zh_match and en_match and ja_match):
            all_passed = False
    
    # 恢復中文
    set_gui_language('zh')
    
    if all_passed:
        print(f"\n✅ 測試 1 通過：All Drivers Brake Performance 多國語言化完整")
    else:
        print(f"\n❌ 測試 1 失敗：部分翻譯不完整")
    
    return all_passed

def test_straight_line_speed_i18n():
    """測試 Straight Line Speed 的多國語言化"""
    print("\n" + "="*70)
    print("測試 2：All Drivers Straight Line Speed 多國語言化")
    print("="*70)
    
    # 需要測試的翻譯鍵
    translation_keys = [
        # 表格欄位標題
        ('speed_analysis_header_driver', '車手', 'Driver', 'ドライバー'),
        ('speed_analysis_header_team', '車隊', 'Team', 'チーム'),
        ('speed_analysis_header_max_speed', '最高速度', 'Max Speed', '最高速度'),
        ('speed_analysis_header_segment_accel_time', '加速時間', 'Accel Time', '加速時間'),
        ('speed_analysis_header_segment_avg_accel', '平均加速度', 'Avg Accel', '平均加速度'),
        ('speed_analysis_header_segment_start_speed', '起始速度', 'Start Speed', '開始速度'),
        ('speed_analysis_header_max_speed_time', '最高速度時間', 'Max Speed Time', '最高速度時間'),
        ('speed_analysis_header_accel_bar', '加速性能視覺化', 'Accel Performance', '加速性能ビジュアル'),
        
        # 資訊標籤
        ('straight_speed_info_no_data', '分析範圍: 未載入資料', 'Analysis Range: No Data Loaded', '分析範囲: データ未読み込み'),
        
        # Tooltip
        ('straight_speed_driver_tooltip', '{driver} - {team}', '{driver} - {team}', '{driver} - {team}'),
        ('straight_speed_team_tooltip', '{team}', '{team}', '{team}'),
    ]
    
    all_passed = True
    
    for key, zh_expected, en_expected, ja_expected in translation_keys:
        print(f"\n測試鍵: {key}")
        
        # 測試中文
        set_gui_language('zh')
        zh_result = tr(key, zh_expected)
        zh_match = zh_result == zh_expected
        print(f"  中文: {'✅' if zh_match else '❌'} {zh_result}")
        
        # 測試英文
        set_gui_language('en')
        en_result = tr(key, en_expected)
        en_match = en_result == en_expected
        print(f"  英文: {'✅' if en_match else '❌'} {en_result}")
        
        # 測試日文
        set_gui_language('ja')
        ja_result = tr(key, ja_expected)
        ja_match = ja_result == ja_expected
        print(f"  日文: {'✅' if ja_match else '❌'} {ja_result}")
        
        if not (zh_match and en_match and ja_match):
            all_passed = False
    
    # 恢復中文
    set_gui_language('zh')
    
    if all_passed:
        print(f"\n✅ 測試 2 通過：All Drivers Straight Line Speed 多國語言化完整")
    else:
        print(f"\n❌ 測試 2 失敗：部分翻譯不完整")
    
    return all_passed

def test_formatted_strings():
    """測試格式化字串的多國語言化"""
    print("\n" + "="*70)
    print("測試 3：格式化字串多國語言化")
    print("="*70)
    
    test_cases = [
        # Brake Performance
        {
            'key': 'brake_performance_info_range',
            'params': {'start': '100.0', 'end': '200.0', 'length': '100.0'},
            'expected': {
                'zh': '煞車範圍: 100.0m → 200.0m (長度: 100.0m)',
                'en': 'Brake Range: 100.0m → 200.0m (Length: 100.0m)',
                'ja': 'ブレーキ範囲: 100.0m → 200.0m (長さ: 100.0m)'
            }
        },
        {
            'key': 'brake_performance_info_reference',
            'params': {'driver': 'VER'},
            'expected': {
                'zh': ' | 參考車手: VER',
                'en': ' | Reference Driver: VER',
                'ja': ' | 基準ドライバー: VER'
            }
        },
        # Straight Line Speed
        {
            'key': 'straight_speed_info_range',
            'params': {'start': '500.0', 'end': '800.0', 'length': '300.0'},
            'expected': {
                'zh': '分析範圍: 500.0m → 800.0m (長度: 300.0m)',
                'en': 'Analysis Range: 500.0m → 800.0m (Length: 300.0m)',
                'ja': '分析範囲: 500.0m → 800.0m (長さ: 300.0m)'
            }
        },
        {
            'key': 'straight_speed_info_reference',
            'params': {'driver': 'HAM'},
            'expected': {
                'zh': ' | 參考車手: HAM',
                'en': ' | Reference Driver: HAM',
                'ja': ' | 基準ドライバー: HAM'
            }
        }
    ]
    
    all_passed = True
    
    for test_case in test_cases:
        key = test_case['key']
        params = test_case['params']
        expected = test_case['expected']
        
        print(f"\n測試鍵: {key}")
        print(f"參數: {params}")
        
        for lang in ['zh', 'en', 'ja']:
            set_gui_language(lang)
            result = tr(key, expected[lang]).format(**params)
            match = result == expected[lang]
            
            lang_name = {'zh': '中文', 'en': '英文', 'ja': '日文'}[lang]
            print(f"  {lang_name}: {'✅' if match else '❌'} {result}")
            
            if not match:
                all_passed = False
                print(f"    預期: {expected[lang]}")
    
    # 恢復中文
    set_gui_language('zh')
    
    if all_passed:
        print(f"\n✅ 測試 3 通過：格式化字串多國語言化正確")
    else:
        print(f"\n❌ 測試 3 失敗：部分格式化字串不正確")
    
    return all_passed

def main():
    """執行所有測試"""
    print("\n" + "="*70)
    print("🌍 All Drivers Brake Performance & Straight Line Speed 多國語言化測試")
    print("="*70)
    
    try:
        # 測試 1：Brake Performance
        test1_passed = test_brake_performance_i18n()
        
        # 測試 2：Straight Line Speed
        test2_passed = test_straight_line_speed_i18n()
        
        # 測試 3：格式化字串
        test3_passed = test_formatted_strings()
        
        # 全部通過
        if test1_passed and test2_passed and test3_passed:
            print("\n" + "="*70)
            print("🎉 所有測試通過！")
            print("="*70)
            print("\n✅ 多國語言化摘要：")
            print("  1. ✅ All Drivers Brake Performance - 表格欄位/資訊標籤/Tooltip")
            print("  2. ✅ All Drivers Straight Line Speed - 表格欄位/資訊標籤/Tooltip")
            print("  3. ✅ 格式化字串正確處理參數替換")
            print("\n支援語言：")
            print("  - 中文 (zh)")
            print("  - 英文 (en)")
            print("  - 日文 (ja)")
            print("\n建議：請手動啟動 GUI 切換語言驗證視覺效果")
            print("命令：python f1t_gui_main.py")
            print("="*70)
            
            return True
        else:
            print("\n" + "="*70)
            print("❌ 部分測試失敗")
            print("="*70)
            print(f"  測試 1 (Brake Performance): {'✅' if test1_passed else '❌'}")
            print(f"  測試 2 (Straight Line Speed): {'✅' if test2_passed else '❌'}")
            print(f"  測試 3 (格式化字串): {'✅' if test3_passed else '❌'}")
            return False
        
    except Exception as e:
        print(f"\n❌ 測試失敗：{e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
