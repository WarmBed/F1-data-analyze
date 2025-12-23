#!/usr/bin/env python3
"""
測試全車手直線速度分析的多國語言化
Test All Drivers Straight Line Speed I18N
"""

from core.gui_i18n import tr, set_gui_language

def test_translations():
    """測試所有翻譯鍵"""
    print("=" * 80)
    print("測試全車手直線速度分析 - 多國語言化")
    print("=" * 80)
    
    # 測試鍵列表
    test_keys = [
        # 表格欄位標題
        ('speed_analysis_header_driver', '車手'),
        ('speed_analysis_header_team', '車隊'),
        ('speed_analysis_header_max_speed', '最高速度'),
        ('speed_analysis_header_segment_accel_time', '加速時間'),
        ('speed_analysis_header_segment_avg_accel', '平均加速度'),
        ('speed_analysis_header_segment_start_speed', '起始速度'),
        ('speed_analysis_header_accel_bar', '加速性能視覺化'),
        
        # 資訊標籤
        ('straight_speed_info_no_data', '分析範圍: 未載入資料'),
        ('straight_speed_info_range', '分析範圍: {start}m → {end}m (長度: {length}m)'),
        ('straight_speed_info_reference', ' | 參考車手: {driver}'),
        
        # Tooltip
        ('straight_speed_driver_tooltip', '{driver} - {team}'),
        ('straight_speed_team_tooltip', '{team}'),
        ('straight_speed_start_speed_tooltip', '起始→結束: {start} → {end} km/h'),
        
        # 車手詳細資訊
        ('straight_speed_driver_info_title', '車手資訊 - {driver}'),
    ]
    
    # 測試三種語言
    languages = [
        ('zh', '中文'),
        ('en', 'English'),
        ('ja', '日本語')
    ]
    
    for lang_code, lang_name in languages:
        print(f"\n{'=' * 80}")
        print(f"測試語言: {lang_name} ({lang_code})")
        print(f"{'=' * 80}")
        
        set_gui_language(lang_code)
        
        for key, default in test_keys:
            result = tr(key, default)
            # 檢查是否使用了預設值（表示翻譯缺失）
            if result == default and lang_code != 'zh':
                status = "⚠️  使用預設值"
            elif result == key:
                status = "❌ 翻譯缺失"
            else:
                status = "✅"
            
            print(f"{status} {key:50s} → {result}")
    
    # 測試格式化字串
    print(f"\n{'=' * 80}")
    print("測試格式化字串")
    print(f"{'=' * 80}")
    
    set_gui_language('zh')
    
    # 測試範圍資訊
    range_text = tr('straight_speed_info_range', '分析範圍: {start}m → {end}m (長度: {length}m)')
    formatted_range = range_text.format(start="3547.1", end="4101.2", length="554.1")
    print(f"✅ 範圍資訊 (中文): {formatted_range}")
    
    # 測試參考車手
    ref_text = tr('straight_speed_info_reference', ' | 參考車手: {driver}')
    formatted_ref = ref_text.format(driver="HAM")
    print(f"✅ 參考車手 (中文): {formatted_ref}")
    
    # 測試完整資訊
    full_info = formatted_range + formatted_ref
    print(f"✅ 完整資訊 (中文): {full_info}")
    
    # 測試英文
    set_gui_language('en')
    range_text_en = tr('straight_speed_info_range', '分析範圍: {start}m → {end}m (長度: {length}m)')
    formatted_range_en = range_text_en.format(start="3547.1", end="4101.2", length="554.1")
    ref_text_en = tr('straight_speed_info_reference', ' | 參考車手: {driver}')
    formatted_ref_en = ref_text_en.format(driver="HAM")
    full_info_en = formatted_range_en + formatted_ref_en
    print(f"✅ 完整資訊 (English): {full_info_en}")
    
    # 測試日文
    set_gui_language('ja')
    range_text_ja = tr('straight_speed_info_range', '分析範圍: {start}m → {end}m (長度: {length}m)')
    formatted_range_ja = range_text_ja.format(start="3547.1", end="4101.2", length="554.1")
    ref_text_ja = tr('straight_speed_info_reference', ' | 參考車手: {driver}')
    formatted_ref_ja = ref_text_ja.format(driver="HAM")
    full_info_ja = formatted_range_ja + formatted_ref_ja
    print(f"✅ 完整資訊 (日本語): {full_info_ja}")
    
    print(f"\n{'=' * 80}")
    print("✅ 所有多國語言化測試完成！")
    print(f"{'=' * 80}")

if __name__ == "__main__":
    try:
        test_translations()
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
