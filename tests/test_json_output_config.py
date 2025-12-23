#!/usr/bin/env python3
"""
JSON 輸出配置模組單元測試
==========================

測試 JSON 輸出配置模組的核心功能。

Author: F1T Development Team
Date: 2025-10-10
Version: 1.0.0
"""

import sys
from pathlib import Path

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from CLI_modules.cli.core.json_output_config import (
    get_analysis_type_from_filename,
    get_subdirectory_for_type,
    get_json_output_path,
    list_all_analysis_types
)

def test_filename_recognition():
    """測試檔案名稱識別"""
    print("=" * 80)
    print("測試 1: 檔案名稱識別")
    print("=" * 80)
    
    test_cases = [
        ("comparison_telemetry_VER_LEC_2025_Japan_R.json", "comparison_telemetry", "telemetry"),
        ("enhanced_rain_analysis_2025_Japan_R.json", "enhanced_rain_analysis", "weather"),
        ("ideal_lap_ranking_2025_Italy_R.json", "ideal_lap_ranking", "lap_analysis"),
        ("driver_detailed_pitstop_records_2025_Japan.json", "driver_detailed_pitstop", "pitstops"),
        ("all_incidents_summary_2025_Japan_R.json", "all_incidents_summary", "incidents"),
        ("throttle_ratio_2025_japan_R.json", "throttle_ratio", "throttle"),
        ("team_colors_2025_fastf1.json", "team_colors", "metadata"),
        ("season_calendar_multi_year.json", "season_calendar", "metadata"),
    ]
    
    passed = 0
    failed = 0
    
    for filename, expected_type, expected_dir in test_cases:
        actual_type = get_analysis_type_from_filename(filename)
        actual_dir = get_subdirectory_for_type(actual_type)
        
        if actual_type == expected_type and actual_dir == expected_dir:
            print(f"✅ PASS: {filename}")
            print(f"         類型: {actual_type} → 目錄: {actual_dir}")
            passed += 1
        else:
            print(f"❌ FAIL: {filename}")
            print(f"         預期: {expected_type} → {expected_dir}")
            print(f"         實際: {actual_type} → {actual_dir}")
            failed += 1
    
    print(f"\n結果: {passed} 通過, {failed} 失敗")
    return failed == 0


def test_path_generation():
    """測試路徑生成"""
    print("\n" + "=" * 80)
    print("測試 2: 路徑生成")
    print("=" * 80)
    
    test_cases = [
        ("comparison_telemetry", "comparison_telemetry_VER_LEC.json", "telemetry"),
        ("ideal_lap_ranking", "ideal_lap_ranking_2025_Italy_R.json", "lap_analysis"),
        ("throttle_ratio", "throttle_ratio_2025_japan_R.json", "throttle"),
    ]
    
    passed = 0
    failed = 0
    
    for analysis_type, filename, expected_subdir in test_cases:
        path = get_json_output_path(analysis_type, filename)
        
        # 驗證路徑包含子目錄和檔案名稱
        if expected_subdir in str(path) and filename in str(path):
            print(f"✅ PASS: {analysis_type}")
            print(f"         路徑: {path}")
            passed += 1
        else:
            print(f"❌ FAIL: {analysis_type}")
            print(f"         預期子目錄: {expected_subdir}")
            print(f"         實際路徑: {path}")
            failed += 1
    
    print(f"\n結果: {passed} 通過, {failed} 失敗")
    return failed == 0


def test_directory_creation():
    """測試目錄自動創建"""
    print("\n" + "=" * 80)
    print("測試 3: 目錄自動創建")
    print("=" * 80)
    
    test_type = "test_analysis"
    test_filename = "test_file.json"
    
    path = get_json_output_path(test_type, test_filename)
    
    if path.parent.exists():
        print(f"✅ PASS: 目錄自動創建成功")
        print(f"         目錄: {path.parent}")
        return True
    else:
        print(f"❌ FAIL: 目錄創建失敗")
        print(f"         路徑: {path.parent}")
        return False


def test_analysis_types_registry():
    """測試分析類型註冊表"""
    print("\n" + "=" * 80)
    print("測試 4: 分析類型註冊表")
    print("=" * 80)
    
    all_types = list_all_analysis_types()
    
    print(f"已註冊的分析類型數量: {len(all_types)}")
    
    # 驗證關鍵類型存在
    required_types = [
        "comparison_telemetry",
        "ideal_lap_ranking",
        "enhanced_rain_analysis",
        "driver_detailed_pitstop",
        "all_incidents_summary",
        "throttle_ratio",
    ]
    
    passed = 0
    failed = 0
    
    for required_type in required_types:
        if required_type in all_types:
            print(f"✅ {required_type:40s} → {all_types[required_type]}")
            passed += 1
        else:
            print(f"❌ {required_type:40s} (缺失)")
            failed += 1
    
    print(f"\n結果: {passed}/{len(required_types)} 關鍵類型存在")
    return failed == 0


def main():
    """主測試函數"""
    print("\n" + "=" * 80)
    print("JSON 輸出配置模組單元測試")
    print("=" * 80)
    
    results = []
    
    # 執行所有測試
    results.append(("檔案名稱識別", test_filename_recognition()))
    results.append(("路徑生成", test_path_generation()))
    results.append(("目錄自動創建", test_directory_creation()))
    results.append(("分析類型註冊表", test_analysis_types_registry()))
    
    # 總結
    print("\n" + "=" * 80)
    print("測試總結")
    print("=" * 80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("\n🎉 所有測試通過!")
        return 0
    else:
        print(f"\n⚠️ {total - passed} 個測試失敗")
        return 1


if __name__ == "__main__":
    sys.exit(main())
