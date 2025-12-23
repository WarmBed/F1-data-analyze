#!/usr/bin/env python3
"""
批量修復 GUI 模組的 SSL 證書問題
為所有 requests.post/get 調用添加 verify=certifi.where()
"""

import re
from pathlib import Path

# 需要修復的檔案清單
FILES = [
    "modules/gui/themes/color_palette_provider.py",
    "modules/gui/tire_analysis/tire_analysis_mdi.py",
    "modules/gui/telemetry_analysis_mdi.py",
    "modules/gui/all_drivers/brake/brake_performance_loader.py",
    "modules/gui/season_progress/season_progress_mdi.py",
    "modules/gui/all_drivers/brake/brake_chart_data_loader.py",
    "modules/gui/all_drivers/brake/brake_all_laps_loader.py",
    "modules/gui/race_analysis/track/track_analysis_mdi.py",
    "modules/gui/race_analysis/track/track_analysis_module.py",
    "modules/gui/race_analysis/track_map/historical_track_map_data_loader.py",
    "modules/gui/race_analysis/temp/temp_analysis_mdi.py",
    "modules/gui/race_analysis/position/driver_position_analysis_mdi.py",
    "modules/gui/race_analysis/pitstop/pitstop_analysis_mdi.py",
    "modules/gui/race_prediction/race_prediction_mdi.py",
    "modules/gui/race_analysis/accident/accident_data_manager.py",
    "modules/gui/partupdated_analysis/parts_analysis_mdi.py",
    "modules/gui/qualifying_prediction/qualifying_prediction_mdi.py",
    "modules/gui/fp2_qualifying_prediction/fp2_qualifying_prediction_mdi.py",
    "modules/gui/multi_season/season_start_reaction/season_start_reaction_mdi.py",
    "modules/gui/live_timing/core/local_source.py",
    "modules/gui/multi_season/pole_defense/pole_defense_mdi.py",
    "modules/gui/lap_analysis/rpm_analysis/rpm_analysis_mdi.py",
    "modules/gui/lap_analysis/timediff_analysis/timediff_analysis_mdi.py",
    "modules/gui/lap_analysis/traffic_timeline_analysis/traffic_timeline_analysis_mdi.py",
    "modules/gui/lap_analysis/telemetry_data_loader_base.py",
    "modules/gui/lap_analysis/Throttle_analysis/throttle_analysis_mdi.py",
    "modules/gui/lap_analysis/speed_analysis/speed_analysis_mdi.py",
    "modules/gui/lap_analysis/Throttle_analysis/throttle_box_plot_analysis/throttle_box_plot_analysis_mdi.py",
    "modules/gui/lap_analysis/speed_analysis/straight_line_speed_loader.py",
    "modules/gui/lap_analysis/speeddiff_analysis/speeddiff_analysis_mdi.py",
    "modules/gui/lap_analysis/Throttle_analysis/throttle_line_chart_analysis/throttle_line_chart_data_loader.py",
    "modules/gui/lap_analysis/lap_box_plot/lap_box_plot_analysis_mdi.py",
    "modules/gui/lap_analysis/gear_analysis/gear_analysis_mdi.py",
    "modules/gui/lap_analysis/distancediff_analysis/distancediff_analysis_mdi.py",
    "modules/gui/lap_analysis/ideal_lap/ideal_lap_sector_heatmap/ideal_lap_sector_heatmap_mdi.py",
    "modules/gui/lap_analysis/ideal_lap/ideal_lap_ranking_table/ideal_lap_ranking_table_mdi.py",
    "modules/gui/lap_analysis/ideal_lap/ideal_lap_sector_comparison/ideal_lap_sector_comparison_mdi.py",
    "modules/gui/lap_analysis/acceleration_analysis/acceleration_analysis_mdi.py",
    "modules/gui/driver_standings/driver_standings_mdi.py",
    "modules/gui/driver_race/lap_box_plot_analysis/lap_box_plot_analysis_mdi.py",
    "modules/gui/lap_analysis/brake_analysis/brake_analysis_mdi.py",
    "modules/gui/driver_race/detailed_lap_analysis/driverlap_analysis_mdi.py",
    "modules/gui/all_drivers/max_speed/max_speed_data_loader.py",
    "modules/gui/diagnostics/objgraph_window.py",
    "modules/gui/all_drivers/corner_performance/corner_performance_loader.py",
]

def fix_file(file_path: Path) -> bool:
    """修復單個檔案的 SSL 證書問題"""
    if not file_path.exists():
        print(f"⏭️  跳過（不存在）: {file_path}")
        return False
    
    content = file_path.read_text(encoding="utf-8")
    
    # 檢查是否已修復
    if "verify=certifi.where()" in content or "verify = certifi.where()" in content:
        print(f"⏭️  已修復: {file_path.name}")
        return False
    
    # 確保有 import certifi
    if "import certifi" not in content:
        # 尋找 import requests 的位置
        if "import requests" in content:
            content = content.replace("import requests", "import requests\nimport certifi")
        else:
            print(f"⚠️  無法添加 certifi import: {file_path.name}")
            return False
    
    modified = False
    original_content = content
    
    # 替換 Pattern 1: headers={"Accept": "application/json"}\n            )
    if 'headers={"Accept": "application/json"}\n            )' in content:
        content = content.replace(
            'headers={"Accept": "application/json"}\n            )',
            'headers={"Accept": "application/json"},\n                verify=certifi.where()  # ✅ SSL證書（EXE必須）\n            )'
        )
        modified = True
    
    # 替換 Pattern 2: timeout=X)
    pattern_timeout = re.compile(r'(timeout\s*=\s*[\w.]+)\s*\)', re.MULTILINE)
    matches = list(pattern_timeout.finditer(content))
    for match in reversed(matches):  # 從後往前替換，避免位置偏移
        # 檢查這個 timeout 後面沒有 verify
        end_pos = match.end()
        if "verify" not in content[match.start():end_pos + 200]:  # 檢查附近200字元
            new_text = f'{match.group(1)}, verify=certifi.where()  # ✅ SSL證書（EXE必須）)'
            content = content[:match.start()] + new_text + content[match.end():]
            modified = True
    
    if modified and content != original_content:
        file_path.write_text(content, encoding="utf-8")
        print(f"✅ 已修復: {file_path.name}")
        return True
    else:
        print(f"⚠️  未修改: {file_path.name}")
        return False

def main():
    print("=" * 50)
    print(" SSL 證書批量修復工具")
    print(" 修復 EXE API 調用問題")
    print("=" * 50)
    print()
    
    root = Path(".")
    fixed_count = 0
    skipped_count = 0
    
    for file_rel in FILES:
        file_path = root / file_rel
        if fix_file(file_path):
            fixed_count += 1
        else:
            skipped_count += 1
    
    print()
    print("=" * 50)
    print(f" 修復完成")
    print("=" * 50)
    print(f"總計: {len(FILES)} 個檔案")
    print(f"已修復: {fixed_count}")
    print(f"跳過: {skipped_count}")

if __name__ == "__main__":
    main()
