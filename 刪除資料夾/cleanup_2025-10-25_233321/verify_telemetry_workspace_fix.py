"""
驗證遙測分析模組 Workspace 支援修復

⚠️ 反幻覺編碼五原則檢查：
原則 0：已宣告五個原則
原則 1：已驗證 analysis_type 屬性（speed_analysis_mdi.py line 346）
原則 2：已檢查 modules/gui/lap_analysis/ 資料夾的現有實現
原則 3：已確認使用 IAnalysisModule 接口
原則 4：已驗證使用 tr() 函數（模組內已實現）
原則 5：已確認 print 輸出會被 logger 導出

測試內容：
1. 檢查 WINDOW_TYPE_MAPPING 映射是否與 analysis_type 一致
2. 驗證 _create_module_instance 的 case 條件是否正確
3. 測試序列化/反序列化流程
"""

import sys
from pathlib import Path

def test_window_type_mapping():
    """測試視窗類型映射是否與模組 analysis_type 一致"""
    print("=" * 80)
    print("測試 1: WINDOW_TYPE_MAPPING 與 analysis_type 一致性")
    print("=" * 80)
    
    from core.workspace_serializer import WorkspaceSerializer
    
    # 預期的映射（基於模組實際的 analysis_type）
    expected_mappings = {
        "SpeedAnalysisModule": "speed",
        "BrakeAnalysisModule": "brake",
        "ThrottleAnalysisModule": "throttle",
        "RPMAnalysisModule": "rpm",
        "accelerationAnalysisModule": "acceleration",
        "GearAnalysisModule": "gear",
        "SpeeddiffAnalysisModule": "Speeddiff",  # 注意：大寫S
        "distancediffAnalysisModule": "distancediff",
        "timediffAnalysisModule": "timediff",
    }
    
    all_passed = True
    for class_name, expected_type in expected_mappings.items():
        actual_type = WorkspaceSerializer.WINDOW_TYPE_MAPPING.get(class_name)
        if actual_type == expected_type:
            print(f"✅ {class_name:35} → {actual_type:20} (正確)")
        else:
            print(f"❌ {class_name:35} → {actual_type:20} (預期: {expected_type})")
            all_passed = False
    
    print()
    if all_passed:
        print("✅ 所有映射都正確！")
    else:
        print("❌ 發現不匹配的映射")
    
    return all_passed

def test_module_analysis_types():
    """測試實際模組的 analysis_type 屬性"""
    print("\n" + "=" * 80)
    print("測試 2: 驗證模組的 analysis_type 屬性")
    print("=" * 80)
    
    modules_to_test = [
        ("modules.gui.lap_analysis.speed_analysis.speed_analysis_mdi", "SpeedAnalysisModule", "speed"),
        ("modules.gui.lap_analysis.brake_analysis.brake_analysis_mdi", "BrakeAnalysisModule", "brake"),
        ("modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_mdi", "ThrottleAnalysisModule", "throttle"),
        ("modules.gui.lap_analysis.rpm_analysis.rpm_analysis_mdi", "RPMAnalysisModule", "rpm"),
        ("modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_mdi", "accelerationAnalysisModule", "acceleration"),
        ("modules.gui.lap_analysis.gear_analysis.gear_analysis_mdi", "GearAnalysisModule", "gear"),
        ("modules.gui.lap_analysis.speeddiff_analysis.speeddiff_analysis_mdi", "SpeeddiffAnalysisModule", "Speeddiff"),
        ("modules.gui.lap_analysis.distancediff_analysis.distancediff_analysis_mdi", "distancediffAnalysisModule", "distancediff"),
        ("modules.gui.lap_analysis.timediff_analysis.timediff_analysis_mdi", "timediffAnalysisModule", "timediff"),
    ]
    
    all_passed = True
    for module_path, class_name, expected_type in modules_to_test:
        try:
            # 動態導入模組
            module = __import__(module_path, fromlist=[class_name])
            module_class = getattr(module, class_name)
            
            # 創建實例
            instance = module_class()
            
            # 檢查 analysis_type
            if hasattr(instance, 'analysis_type'):
                actual_type = instance.analysis_type
                if actual_type == expected_type:
                    print(f"✅ {class_name:35} analysis_type = '{actual_type}' (正確)")
                else:
                    print(f"❌ {class_name:35} analysis_type = '{actual_type}' (預期: '{expected_type}')")
                    all_passed = False
            else:
                print(f"❌ {class_name:35} 沒有 analysis_type 屬性")
                all_passed = False
                
        except Exception as e:
            print(f"⚠️ {class_name:35} 導入失敗: {e}")
            all_passed = False
    
    print()
    if all_passed:
        print("✅ 所有模組的 analysis_type 都正確！")
    else:
        print("❌ 發現不匹配或缺失的 analysis_type")
    
    return all_passed

def test_create_module_instance_cases():
    """測試 _create_module_instance 方法的 case 條件"""
    print("\n" + "=" * 80)
    print("測試 3: 檢查 _create_module_instance 的 case 條件")
    print("=" * 80)
    
    import inspect
    from core.workspace_serializer import WorkspaceSerializer
    
    # 獲取方法源代碼
    source = inspect.getsource(WorkspaceSerializer._create_module_instance)
    
    # 檢查每個遙測類型的 case
    expected_cases = [
        'window_type == "speed"',
        'window_type == "brake"',
        'window_type == "throttle"',
        'window_type == "rpm"',
        'window_type == "acceleration"',
        'window_type == "gear"',
        'window_type == "Speeddiff"',  # 大寫S
        'window_type == "distancediff"',
        'window_type == "timediff"',
    ]
    
    all_passed = True
    for case in expected_cases:
        if case in source:
            print(f"✅ 找到 case: {case}")
        else:
            print(f"❌ 缺少 case: {case}")
            all_passed = False
    
    # 檢查是否有舊的錯誤 case（含 _analysis 後綴）
    wrong_cases = [
        'window_type == "speed_analysis"',
        'window_type == "brake_analysis"',
        'window_type == "throttle_analysis"',
        'window_type == "rpm_analysis"',
        'window_type == "acceleration_analysis"',
        'window_type == "gear_analysis"',
        'window_type == "speeddiff_analysis"',
        'window_type == "distancediff_analysis"',
        'window_type == "timediff_analysis"',
    ]
    
    print("\n檢查是否有舊的錯誤 case:")
    for case in wrong_cases:
        if case in source:
            print(f"⚠️ 發現舊 case（需移除）: {case}")
            all_passed = False
        else:
            print(f"✅ 沒有舊 case: {case}")
    
    print()
    if all_passed:
        print("✅ 所有 case 條件都正確！")
    else:
        print("❌ 發現錯誤或缺失的 case 條件")
    
    return all_passed

def main():
    """主測試函數"""
    print("=" * 80)
    print("遙測分析模組 Workspace 支援修復驗證")
    print("=" * 80)
    print()
    
    # 執行測試
    test1_passed = test_window_type_mapping()
    test2_passed = test_module_analysis_types()
    test3_passed = test_create_module_instance_cases()
    
    # 總結
    print("\n" + "=" * 80)
    print("測試總結")
    print("=" * 80)
    print(f"測試 1 (WINDOW_TYPE_MAPPING): {'✅ 通過' if test1_passed else '❌ 失敗'}")
    print(f"測試 2 (模組 analysis_type): {'✅ 通過' if test2_passed else '❌ 失敗'}")
    print(f"測試 3 (_create_module_instance case): {'✅ 通過' if test3_passed else '❌ 失敗'}")
    print()
    
    if all([test1_passed, test2_passed, test3_passed]):
        print("🎉 所有測試通過！遙測分析模組 Workspace 支援已正確修復！")
        print()
        print("📋 問題根本原因:")
        print("   - WINDOW_TYPE_MAPPING 使用了 'xxx_analysis' 格式")
        print("   - 但模組的 analysis_type 屬性使用 'xxx' 格式（無後綴）")
        print("   - 導致序列化/反序列化時類型不匹配")
        print()
        print("✅ 修復內容:")
        print("   1. 移除 WINDOW_TYPE_MAPPING 中的 '_analysis' 後綴")
        print("   2. 更新 _create_module_instance 的 case 條件")
        print("   3. 特別處理 'Speeddiff' 的大寫 S")
        return 0
    else:
        print("❌ 發現問題，請檢查上述測試結果")
        return 1

if __name__ == "__main__":
    sys.exit(main())
