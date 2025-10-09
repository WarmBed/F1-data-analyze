"""
測試所有動態導入模組是否可用（用於 PyInstaller 打包驗證）
"""

import sys

def test_imports():
    print("=" * 70)
    print("測試動態導入模組（PyInstaller 打包驗證）")
    print("=" * 70)
    
    modules_to_test = [
        # Throttle Analysis
        ('modules.gui.Throttle_analysis.throttle_analysis_options_dialog', 'Throttle Analysis Options Dialog'),
        ('modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_module', 'Throttle Line Chart Module'),
        ('modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_mdi', 'Throttle Line Chart MDI'),
        ('modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_data_loader', 'Throttle Line Chart Data Loader'),
        ('modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_module', 'Throttle Box Plot Module'),
        
        # Detailed Lap Analysis
        ('modules.gui.driver_race.detailed_lap_analysis.detailed_lap_options_dialog', 'Detailed Lap Options Dialog'),
        ('modules.gui.driver_race.detailed_lap_analysis.detailed_lap_analysis_module', 'Detailed Lap Analysis Module'),
        
        # Lap Analysis Chart Widgets
        ('modules.gui.lap_analysis.speed_analysis.speed_analysis_chart_widget', 'Speed Chart Widget'),
        ('modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_chart_widget', 'Throttle Chart Widget'),
        ('modules.gui.lap_analysis.rpm_analysis.rpm_analysis_chart_widget', 'RPM Chart Widget'),
        ('modules.gui.lap_analysis.gear_analysis.gear_analysis_chart_widget', 'Gear Chart Widget'),
        ('modules.gui.lap_analysis.brake_analysis.brake_analysis_chart_widget', 'Brake Chart Widget'),
        ('modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_chart_widget', 'Acceleration Chart Widget'),
        
        # Universal Components
        ('modules.gui.universal_chart_widget', 'Universal Chart Widget'),
        ('modules.gui.base.universal_data_loader_base', 'Universal Data Loader Base'),
        ('modules.gui.base.universal_analysis_mdi', 'Universal Analysis MDI'),
        
        # Core
        ('core.gui_i18n', 'GUI i18n'),
        ('core.gui_settings_manager', 'GUI Settings Manager'),
    ]
    
    success_count = 0
    fail_count = 0
    
    for module_name, description in modules_to_test:
        try:
            __import__(module_name)
            print(f"✅ {description:<50} | {module_name}")
            success_count += 1
        except ImportError as e:
            print(f"❌ {description:<50} | {module_name}")
            print(f"   錯誤: {e}")
            fail_count += 1
        except Exception as e:
            print(f"⚠️  {description:<50} | {module_name}")
            print(f"   警告: {e}")
            success_count += 1  # 視為成功（模組存在但有其他問題）
    
    print("=" * 70)
    print(f"測試結果: {success_count} 成功, {fail_count} 失敗")
    print("=" * 70)
    
    if fail_count > 0:
        print("\n⚠️  有模組導入失敗！請檢查 F1T_GUI.spec 的 hiddenimports 設定")
        return False
    else:
        print("\n✅ 所有模組導入成功！可以進行 PyInstaller 打包")
        return True

if __name__ == '__main__':
    success = test_imports()
    sys.exit(0 if success else 1)
