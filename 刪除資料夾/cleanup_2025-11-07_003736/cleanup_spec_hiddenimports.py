"""
清理 F1T_GUI.spec 中不存在的 hiddenimports
"""
import sys
import importlib

# 需要移除的模組（已確認不存在）
modules_to_remove = [
    'modules.gui.lap_analysis.lap_time_analysis_module',
    'modules.gui.lap_analysis.lap_time_analysis_mdi',
    'modules.gui.speed_analysis.speed_analysis_module',
    'modules.gui.rain_analysis.rain_analysis_data_loader',
    'modules.gui.tire_analysis.tire_analysis_data_loader',
    'modules.gui.lap_analysis.speeddiff_analysis.speeddiff_analysis_module',
    'modules.gui.lap_analysis.distancediff_analysis.distancediff_analysis_module',
    'modules.gui.lap_analysis.timediff_analysis.timediff_analysis_module',
    'modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_data_loader',
    'modules.gui.shared.race_selection_manager',
    'modules.gui.lap_analysis.linkage_manager',
    'modules.gui.throttle_duration_chart_widget',
    'modules.gui.lap_time_chart_widget',
    'modules.gui.base.universal_analysis_mdi',
    'modules.gui.lap_analysis.base.telemetry_data_loader',
    'modules.gui.lap_analysis.base.telemetry_chart_widget_base',
    'modules.gui.lap_analysis.linkage.lap_analysis_linkage_mixin',
    'modules.gui.lap_analysis.linkage.lap_analysis_linkage_drawing_mixin',
    'modules.gui.workspace',
    'modules.gui.workspace.workspace_manager',
    'modules.gui.workspace.workspace_serializer',
    'modules.gui.workspace.analysis_module_adapters',
    'modules.gui.all_drivers_straight_line_speed_analysis.straight_line_speed_loader',
    'modules.gui.all_drivers_corner_box_plot_analysis',
    'modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_data_loader',
    'modules.gui.driver_race.lap_box_plot_analysis.lap_box_plot_data_loader',
    'modules.gui.lap_box_plot_analysis.lap_box_plot_data_loader',
    'numpy.core._methods',
    'pandas._libs.skiplist',
]

print("=" * 70)
print("清理 F1T_GUI.spec 中的無效 hiddenimports")
print("=" * 70)
print(f"\n將移除 {len(modules_to_remove)} 個不存在的模組\n")

# 讀取 spec 檔案
with open("F1T_GUI.spec", "r", encoding="utf-8") as f:
    content = f.read()

# 逐一移除
removed_count = 0
for module in modules_to_remove:
    # 嘗試多種格式
    patterns = [
        f"        '{module}',\n",
        f"        \"{module}\",\n",
        f"'{module}',\n",
        f"\"{module}\",\n",
    ]
    
    for pattern in patterns:
        if pattern in content:
            content = content.replace(pattern, "")
            print(f"✅ 移除: {module}")
            removed_count += 1
            break

# 儲存
with open("F1T_GUI.spec", "w", encoding="utf-8") as f:
    f.write(content)

print(f"\n" + "=" * 70)
print(f"✅ 清理完成！移除了 {removed_count} 個無效模組")
print("=" * 70)
