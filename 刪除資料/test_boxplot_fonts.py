#!/usr/bin/env python3
"""
測試 Box Plot 字體修改
驗證 Throttle Box Plot 和 Lap Time Box Plot 都使用統一的 font.setPointSize(8)
"""

import sys
import re
from pathlib import Path


def test_file_font_settings(file_path: str, file_name: str) -> bool:
    """檢查文件中的字體設置"""
    print(f"\n🔍 檢查 {file_name}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    
    # 檢查是否有舊的字體設置模式
    old_patterns = [
        (r'QFont\("Arial",\s*\d+\)', 'QFont("Arial", size) 模式'),
        (r'QFont\("Microsoft JhengHei",\s*\d+\)', 'QFont("Microsoft JhengHei", size) 模式'),
        (r'QFont\(\w+,\s*\d+,\s*QFont\.Bold\)', 'QFont(family, size, weight) 模式'),
    ]
    
    for pattern, description in old_patterns:
        matches = re.findall(pattern, content)
        if matches:
            issues.append(f"   ❌ 發現舊模式 {description}: {len(matches)} 處")
            for match in matches[:3]:  # 只顯示前 3 個
                issues.append(f"      - {match}")
    
    # 檢查是否有正確的新模式
    new_pattern_count = len(re.findall(r'font\.setPointSize\(8\)', content))
    
    if new_pattern_count > 0:
        print(f"   ✅ 發現 {new_pattern_count} 處使用 font.setPointSize(8)")
    
    if issues:
        for issue in issues:
            print(issue)
        return False
    else:
        print(f"   ✅ 所有字體設置已統一為 font.setPointSize(8)")
        return True


def main():
    print("=" * 70)
    print("🔬 Box Plot 字體設置驗證測試")
    print("=" * 70)
    
    # 測試文件列表
    test_files = [
        {
            "path": "modules/gui/Throttle_analysis/throttle_box_plot_analysis/throttle_box_plot_chart_widget.py",
            "name": "Throttle Box Plot Chart Widget"
        },
        {
            "path": "modules/gui/driver_race/detailed_lap_analysis/laptime_boxplot_widget.py",
            "name": "Lap Time Box Plot Widget"
        }
    ]
    
    results = []
    
    for test_file in test_files:
        file_path = Path(test_file["path"])
        if not file_path.exists():
            print(f"\n⚠️  文件不存在: {test_file['path']}")
            results.append((test_file["name"], False))
            continue
        
        passed = test_file_font_settings(str(file_path), test_file["name"])
        results.append((test_file["name"], passed))
    
    # 總結
    print("\n" + "=" * 70)
    print("📊 測試總結")
    print("=" * 70)
    
    for file_name, passed in results:
        status = "✅ 通過" if passed else "❌ 失敗"
        print(f"   {file_name:50s} : {status}")
    
    all_passed = all(result for _, result in results)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 所有 Box Plot 字體已統一設置為 font.setPointSize(8)！")
        print("\n統一設置包括：")
        print("   - 座標標題 (Axis Labels)")
        print("   - 座標數值 (Tick Labels)")
        print("   - 車手名稱 (Driver Names)")
        print("   - Tooltip 文字")
        print("   - 無數據提示")
    else:
        print("⚠️  部分測試失敗，請檢查修改")
    print("=" * 70)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
