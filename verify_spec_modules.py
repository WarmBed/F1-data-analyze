"""
驗證 F1T_GUI_clean.spec 檔案中是否包含所有必要的模組
"""

import os
from pathlib import Path

# 需要檢查的模組清單
REQUIRED_MODULES = [
    # Base modules
    'modules.gui.base.universal_stint_selector',
    'modules.gui.base.async_loading_progress',
    'modules.gui.base.global_chart_sync_signal',
    'modules.gui.base.loading_indicator',
    
    # Lap Analysis - Pedal Behavior
    'modules.gui.lap_analysis.pedal_behavior_analysis',
    'modules.gui.lap_analysis.pedal_behavior_analysis.pedal_behavior_analysis_mdi',
    'modules.gui.lap_analysis.pedal_behavior_analysis.pedal_behavior_chart_widget',
    'modules.gui.lap_analysis.pedal_behavior_analysis.pedal_behavior_data_manager',
    
    # Lap Analysis - Other
    'modules.gui.lap_analysis.acceleration_analysis',
    'modules.gui.lap_analysis.brake_analysis',
    'modules.gui.lap_analysis.distancediff_analysis',
    'modules.gui.lap_analysis.gear_analysis',
    'modules.gui.lap_analysis.rpm_analysis',
    'modules.gui.lap_analysis.speeddiff_analysis',
    'modules.gui.lap_analysis.speed_analysis',
    'modules.gui.lap_analysis.Throttle_analysis',
    'modules.gui.lap_analysis.timediff_analysis',
    'modules.gui.lap_analysis.lap_box_plot',
    
    # Race Analysis - Track Map
    'modules.gui.race_analysis.track_map.historical_track_map_mdi',
    'modules.gui.race_analysis.track_map.historical_track_map_data_loader',
    'modules.gui.race_analysis.track_map.speed_distribution_widget',
    'modules.gui.race_analysis.start_reaction',
    'modules.gui.race_analysis.traffic_analysis',
    
    # Long Run Analysis
    'modules.gui.long_run_analysis',
    'modules.gui.long_run_analysis.long_run_mdi',
    'modules.gui.long_run_analysis.long_run_data_loader',
    'modules.gui.long_run_analysis.long_run_calculator',
]

def main():
    project_root = Path(__file__).parent
    spec_file = project_root / 'F1T_GUI_clean.spec'
    
    if not spec_file.exists():
        print(f"❌ Spec 檔案不存在: {spec_file}")
        return False
    
    # 讀取 spec 檔案內容
    with open(spec_file, 'r', encoding='utf-8') as f:
        spec_content = f.read()
    
    print("=" * 80)
    print("驗證 F1T_GUI_clean.spec 模組完整性")
    print("=" * 80)
    print()
    
    missing_modules = []
    found_modules = []
    
    for module in REQUIRED_MODULES:
        # 將模組路徑轉換為 spec 中的格式
        spec_format = f"'{module}'"
        
        if spec_format in spec_content:
            found_modules.append(module)
            print(f"✅ 已包含: {module}")
        else:
            missing_modules.append(module)
            print(f"❌ 缺失: {module}")
    
    print()
    print("=" * 80)
    print("驗證結果")
    print("=" * 80)
    print(f"✅ 已包含模組: {len(found_modules)}/{len(REQUIRED_MODULES)}")
    print(f"❌ 缺失模組: {len(missing_modules)}/{len(REQUIRED_MODULES)}")
    
    if missing_modules:
        print()
        print("缺失的模組清單：")
        for module in missing_modules:
            print(f"  - {module}")
        return False
    else:
        print()
        print("🎉 所有模組都已包含在 spec 檔案中！")
        return True

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
