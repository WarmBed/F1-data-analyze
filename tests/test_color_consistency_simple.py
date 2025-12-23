#!/usr/bin/env python3
"""
簡化的顏色一致性測試
只檢查源代碼，不實際導入模組
"""

from pathlib import Path

def check_file_color_usage(file_path: Path, module_name: str) -> bool:
    """檢查檔案是否正確使用 color_palette_provider"""
    print(f"\n檢查 {module_name}:")
    
    try:
        content = file_path.read_text(encoding='utf-8')
        
        # 檢查是否使用 color_palette_provider
        uses_color_provider = 'color_palette_provider' in content
        uses_get_driver_color = 'get_driver_color' in content
        uses_old_shared_colors = 'ideal_lap_analysis.shared_colors' in content
        uses_old_get_team_color = 'from modules.gui.ideal_lap_analysis.shared_colors import' in content
        
        print(f"  ✅ 使用 color_palette_provider: {uses_color_provider}")
        print(f"  ✅ 調用 get_driver_color(): {uses_get_driver_color}")
        print(f"  ❌ 使用舊的 shared_colors: {uses_old_shared_colors}")
        print(f"  ❌ 導入舊的 get_team_color: {uses_old_get_team_color}")
        
        # 檢查是否有正確的導入語句
        has_correct_import = 'from modules.gui.themes.color_palette_provider import color_palette_provider' in content
        print(f"  ✅ 正確的導入語句: {has_correct_import}")
        
        # 檢查是否有亮度計算（與 driver_standings 一致）
        has_luminance_calc = 'luminance = (0.299 * driver_color.red()' in content
        print(f"  ✅ 包含亮度計算: {has_luminance_calc}")
        
        success = (
            uses_color_provider and 
            uses_get_driver_color and 
            not uses_old_get_team_color and
            has_correct_import and
            has_luminance_calc
        )
        
        if success:
            print(f"  🎉 {module_name} 顏色配置正確！")
        else:
            print(f"  ⚠️  {module_name} 顏色配置需要調整")
        
        return success
        
    except Exception as e:
        print(f"  ❌ 錯誤: {e}")
        return False

def main():
    print("="*80)
    print("F1T 車手與車隊顏色一致性源代碼檢查")
    print("="*80)
    
    project_root = Path(__file__).parent
    
    # 檢查三個模組
    files_to_check = [
        (
            project_root / "modules" / "gui" / "all_drivers_brake_performance_analysis" / "all_drivers_brake_performance_table_widget.py",
            "All Drivers Brake Performance"
        ),
        (
            project_root / "modules" / "gui" / "all_drivers_straight_line_speed_analysis" / "all_drivers_straight_line_speed_table_widget.py",
            "All Drivers Straight Line Speed"
        ),
        (
            project_root / "modules" / "gui" / "driver_standings" / "driver_standings_widget.py",
            "Driver Standings (參考標準)"
        ),
    ]
    
    results = []
    for file_path, module_name in files_to_check:
        if file_path.exists():
            result = check_file_color_usage(file_path, module_name)
            results.append((module_name, result))
        else:
            print(f"\n❌ 檔案不存在: {file_path}")
            results.append((module_name, False))
    
    # 總結
    print("\n" + "="*80)
    print("檢查總結")
    print("="*80)
    
    for module_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{module_name}: {status}")
    
    # 檢查是否有任何舊的 shared_colors 使用
    print("\n檢查是否有其他檔案仍使用舊的 shared_colors...")
    all_py_files = list(project_root.glob("modules/gui/all_drivers_*/**/*.py"))
    old_usage_found = False
    
    for py_file in all_py_files:
        try:
            content = py_file.read_text(encoding='utf-8')
            if 'ideal_lap_analysis.shared_colors' in content and 'get_team_color' in content:
                print(f"  ⚠️  發現使用舊配色: {py_file.relative_to(project_root)}")
                old_usage_found = True
        except:
            pass
    
    if not old_usage_found:
        print("  ✅ 未發現其他檔案使用舊配色")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 所有模組顏色配置已統一！")
        return 0
    else:
        print("\n⚠️  部分模組需要調整，請檢查上述錯誤訊息。")
        return 1

if __name__ == "__main__":
    exit(main())
