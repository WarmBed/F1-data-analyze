"""
撤銷所有 Qt.QueuedConnection 修改
恢復到默認的 AutoConnection
"""

import re
from pathlib import Path
from typing import List

# 需要恢復的文件
FILES_TO_REVERT = [
    "modules/gui/ideal_lap_analysis/ideal_lap_ranking_table/ideal_lap_ranking_table_mdi.py",
    "modules/gui/ideal_lap_analysis/ideal_lap_sector_comparison/ideal_lap_sector_comparison_mdi.py",
    "modules/gui/tire_analysis/tire_analysis_mdi.py",
    "modules/gui/Throttle_analysis/throttle_line_chart_analysis/throttle_line_chart_data_loader.py",
    "modules/gui/Throttle_analysis/throttle_box_plot_analysis/throttle_box_plot_analysis_mdi.py",
    "modules/gui/track_analysis/track_analysis_mdi.py",
    "modules/gui/telemetry_analysis_mdi.py",
    "modules/gui/rain_analysis/rain_analysis_mdi.py",
    "modules/gui/driver_race/detailed_lap_analysis/driverlap_analysis_mdi.py",
    "modules/gui/driver_race/lap_box_plot_analysis/lap_box_plot_analysis_mdi.py",
    "modules/gui/lap_box_plot_analysis/lap_box_plot_analysis_mdi.py",
    "modules/gui/accident_analysis/accident_data_manager.py",
]

def revert_queuedconnection(file_path: str) -> bool:
    """撤銷 Qt.QueuedConnection，恢復到普通連接"""
    full_path = Path(file_path)
    
    if not full_path.exists():
        print(f"⏭️  跳過（文件不存在）: {file_path}")
        return False
    
    # 讀取文件
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否有 Qt.QueuedConnection
    if ', Qt.QueuedConnection)' not in content:
        print(f"⏭️  無需恢復: {file_path}")
        return False
    
    print(f"\n🔄 恢復文件: {file_path}")
    
    # 移除所有 , Qt.QueuedConnection
    new_content = content.replace(', Qt.QueuedConnection)', ')')
    
    # 計算修改數量
    changes = content.count(', Qt.QueuedConnection)')
    print(f"   移除了 {changes} 個 Qt.QueuedConnection")
    
    # 寫回文件
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"   ✅ 恢復完成")
    return True

def main():
    """批量恢復所有文件"""
    print("=" * 80)
    print("🔄 批量撤銷 Qt.QueuedConnection 修改")
    print("=" * 80)
    print("\n原因: Qt.QueuedConnection 會導致事件循環問題")
    print("      原始崩潰的根本原因不是線程安全問題\n")
    
    reverted_count = 0
    skipped_count = 0
    
    for file_path in FILES_TO_REVERT:
        if revert_queuedconnection(file_path):
            reverted_count += 1
        else:
            skipped_count += 1
    
    print("\n" + "=" * 80)
    print(f"✅ 恢復完成！")
    print(f"   恢復: {reverted_count} 個文件")
    print(f"   跳過: {skipped_count} 個文件")
    print("=" * 80)

if __name__ == "__main__":
    main()
