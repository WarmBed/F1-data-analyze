"""
簡化版：驗證遙測分析模組 Workspace 支援修復

只測試映射和源代碼，不實際導入模組（避免依賴問題）
"""

import sys
import inspect

def test_window_type_mapping():
    """測試視窗類型映射是否與 analysis_type 一致"""
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

def test_create_module_instance_cases():
    """測試 _create_module_instance 方法的 case 條件"""
    print("\n" + "=" * 80)
    print("測試 2: 檢查 _create_module_instance 的 case 條件")
    print("=" * 80)
    
    from core.workspace_serializer import WorkspaceSerializer
    
    # 獲取方法源代碼
    source = inspect.getsource(WorkspaceSerializer._create_module_instance)
    
    # 檢查每個遙測類型的 case
    expected_cases = [
        ('window_type == "speed"', 'Speed Analysis'),
        ('window_type == "brake"', 'Brake Analysis'),
        ('window_type == "throttle"', 'Throttle Analysis'),
        ('window_type == "rpm"', 'RPM Analysis'),
        ('window_type == "acceleration"', 'Acceleration Analysis'),
        ('window_type == "gear"', 'Gear Analysis'),
        ('window_type == "Speeddiff"', 'Speed Diff Analysis'),  # 大寫S
        ('window_type == "distancediff"', 'Distance Diff Analysis'),
        ('window_type == "timediff"', 'Time Diff Analysis'),
    ]
    
    all_passed = True
    print("檢查正確的 case 條件:")
    for case, description in expected_cases:
        if case in source:
            print(f"✅ {description:25} case: {case}")
        else:
            print(f"❌ {description:25} 缺少 case: {case}")
            all_passed = False
    
    # 檢查是否有舊的錯誤 case（含 _analysis 後綴）
    wrong_cases = [
        ('window_type == "speed_analysis"', 'Speed Analysis'),
        ('window_type == "brake_analysis"', 'Brake Analysis'),
        ('window_type == "throttle_analysis"', 'Throttle Analysis'),
        ('window_type == "rpm_analysis"', 'RPM Analysis'),
        ('window_type == "acceleration_analysis"', 'Acceleration Analysis'),
        ('window_type == "gear_analysis"', 'Gear Analysis'),
        ('window_type == "speeddiff_analysis"', 'Speed Diff Analysis'),
        ('window_type == "distancediff_analysis"', 'Distance Diff Analysis'),
        ('window_type == "timediff_analysis"', 'Time Diff Analysis'),
    ]
    
    print("\n檢查是否有舊的錯誤 case (含 _analysis 後綴):")
    has_wrong_cases = False
    for case, description in wrong_cases:
        if case in source:
            print(f"⚠️ {description:25} 發現舊 case（需移除）: {case}")
            all_passed = False
            has_wrong_cases = True
    
    if not has_wrong_cases:
        print("✅ 沒有舊的錯誤 case")
    
    print()
    if all_passed:
        print("✅ 所有 case 條件都正確！")
    else:
        print("❌ 發現錯誤或缺失的 case 條件")
    
    return all_passed

def main():
    """主測試函數"""
    print("=" * 80)
    print("遙測分析模組 Workspace 支援修復驗證（簡化版）")
    print("=" * 80)
    print()
    
    # 執行測試
    test1_passed = test_window_type_mapping()
    test2_passed = test_create_module_instance_cases()
    
    # 總結
    print("\n" + "=" * 80)
    print("測試總結")
    print("=" * 80)
    print(f"測試 1 (WINDOW_TYPE_MAPPING): {'✅ 通過' if test1_passed else '❌ 失敗'}")
    print(f"測試 2 (_create_module_instance): {'✅ 通過' if test2_passed else '❌ 失敗'}")
    print()
    
    if all([test1_passed, test2_passed]):
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
        print()
        print("📝 下一步:")
        print("   1. 啟動 F1T GUI")
        print("   2. 添加遙測分析模組到 workspace")
        print("   3. 保存 workspace")
        print("   4. 重新載入 workspace")
        print("   5. 確認遙測模組正確恢復")
        return 0
    else:
        print("❌ 發現問題，請檢查上述測試結果")
        return 1

if __name__ == "__main__":
    sys.exit(main())
