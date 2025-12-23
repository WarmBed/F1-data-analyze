#!/usr/bin/env python3
"""
測試車手與車隊顏色一致性
驗證 All Driver Speed、All Driver Brake Performance 和 Driver Standing 的顏色配置是否一致
"""

import sys
from pathlib import Path

# 添加專案根目錄到 Python 路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_import_modules():
    """測試模組導入"""
    print("\n" + "="*80)
    print("測試 1: 模組導入測試")
    print("="*80)
    
    try:
        # 測試 brake performance 導入
        from modules.gui.all_drivers_brake_performance_analysis.all_drivers_brake_performance_table_widget import (
            AllDriversBrakePerformanceTableWidget
        )
        print("[OK] ✅ All Drivers Brake Performance Table Widget 導入成功")
        
        # 測試 straight line speed 導入
        from modules.gui.all_drivers_straight_line_speed_analysis.all_drivers_straight_line_speed_table_widget import (
            AllDriversStraightLineSpeedTableWidget
        )
        print("[OK] ✅ All Drivers Straight Line Speed Table Widget 導入成功")
        
        # 測試 driver standings 導入
        from modules.gui.driver_standings.driver_standings_widget import DriverStandingsWidget
        print("[OK] ✅ Driver Standings Widget 導入成功")
        
        return True
    except Exception as e:
        print(f"[ERROR] ❌ 導入失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_color_provider_usage():
    """測試顏色提供者使用"""
    print("\n" + "="*80)
    print("測試 2: 顏色提供者使用測試")
    print("="*80)
    
    try:
        # 檢查 brake performance 是否使用 color_palette_provider
        from modules.gui.all_drivers_brake_performance_analysis import all_drivers_brake_performance_table_widget
        brake_source = Path(all_drivers_brake_performance_table_widget.__file__).read_text(encoding='utf-8')
        
        if 'color_palette_provider' in brake_source:
            print("[OK] ✅ Brake Performance 使用 color_palette_provider")
        else:
            print("[ERROR] ❌ Brake Performance 未使用 color_palette_provider")
            return False
        
        if 'get_team_color' in brake_source and 'ideal_lap_analysis.shared_colors' in brake_source:
            print("[ERROR] ❌ Brake Performance 仍使用舊的 shared_colors")
            return False
        else:
            print("[OK] ✅ Brake Performance 已移除舊的 shared_colors 依賴")
        
        # 檢查 straight line speed 是否使用 color_palette_provider
        from modules.gui.all_drivers_straight_line_speed_analysis import all_drivers_straight_line_speed_table_widget
        speed_source = Path(all_drivers_straight_line_speed_table_widget.__file__).read_text(encoding='utf-8')
        
        if 'color_palette_provider' in speed_source:
            print("[OK] ✅ Straight Line Speed 使用 color_palette_provider")
        else:
            print("[ERROR] ❌ Straight Line Speed 未使用 color_palette_provider")
            return False
        
        if 'get_team_color' in speed_source and 'ideal_lap_analysis.shared_colors' in speed_source:
            print("[ERROR] ❌ Straight Line Speed 仍使用舊的 shared_colors")
            return False
        else:
            print("[OK] ✅ Straight Line Speed 已移除舊的 shared_colors 依賴")
        
        # 檢查 driver standings 使用 color_palette_provider
        from modules.gui.driver_standings import driver_standings_widget
        standings_source = Path(driver_standings_widget.__file__).read_text(encoding='utf-8')
        
        if 'color_palette_provider' in standings_source:
            print("[OK] ✅ Driver Standings 使用 color_palette_provider")
        else:
            print("[ERROR] ❌ Driver Standings 未使用 color_palette_provider")
            return False
        
        return True
    except Exception as e:
        print(f"[ERROR] ❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_color_method_usage():
    """測試顏色方法使用"""
    print("\n" + "="*80)
    print("測試 3: 顏色方法調用測試")
    print("="*80)
    
    try:
        from modules.gui.themes.color_palette_provider import color_palette_provider
        
        # 測試 get_driver_color 方法
        test_drivers = ["VER", "LEC", "HAM", "NOR", "SAI"]
        
        print("\n測試 get_driver_color() 方法:")
        for driver in test_drivers:
            color = color_palette_provider.get_driver_color(driver, fallback=True)
            print(f"  {driver}: RGB({color.red()}, {color.green()}, {color.blue()})")
        
        # 測試亮度計算
        print("\n測試文字顏色選擇（基於背景亮度）:")
        for driver in test_drivers:
            color = color_palette_provider.get_driver_color(driver, fallback=True)
            luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue())
            text_color = "白色" if luminance < 128 else "黑色"
            print(f"  {driver}: 亮度={luminance:.1f}, 文字顏色={text_color}")
        
        print("\n[OK] ✅ 顏色方法調用測試通過")
        return True
    except Exception as e:
        print(f"[ERROR] ❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """執行所有測試"""
    print("\n" + "🏎️ " * 20)
    print("F1T 車手與車隊顏色一致性測試")
    print("🏎️ " * 20)
    
    results = []
    
    # 測試 1: 模組導入
    results.append(("模組導入測試", test_import_modules()))
    
    # 測試 2: 顏色提供者使用
    results.append(("顏色提供者使用測試", test_color_provider_usage()))
    
    # 測試 3: 顏色方法調用
    results.append(("顏色方法調用測試", test_color_method_usage()))
    
    # 總結
    print("\n" + "="*80)
    print("測試總結")
    print("="*80)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n🎉 所有測試通過！顏色配置已統一。")
        return 0
    else:
        print("\n⚠️  部分測試失敗，請檢查上述錯誤訊息。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
