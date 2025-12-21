"""
批量修復所有 QThread API Worker 的信號連接
確保使用 Qt.QueuedConnection 強制在 UI 線程執行槽函數
"""

import os
import re
from pathlib import Path

# 需要修復的文件列表（從 grep_search 結果整理）
FILES_TO_FIX = [
    # Tire Analysis
    "modules/gui/tire_analysis/tire_analysis_mdi.py",
    
    # Pitstop Analysis  
    "modules/gui/pitstop_analysis/pitstop_analysis_mdi.py",
    
    # Throttle Analysis
    "modules/gui/Throttle_analysis/throttle_line_chart_analysis/throttle_line_chart_data_loader.py",
    "modules/gui/Throttle_analysis/throttle_box_plot_analysis/throttle_box_plot_analysis_mdi.py",
    
    # Track Analysis
    "modules/gui/track_analysis/track_analysis_mdi.py",
    "modules/gui/track_analysis/track_analysis_module.py",
    
    # Telemetry Analysis
    "modules/gui/telemetry_analysis_mdi.py",
    
    # Rain Analysis
    "modules/gui/rain_analysis/rain_analysis_mdi.py",
    
    # Driver Race Analysis
    "modules/gui/driver_race/detailed_lap_analysis/driverlap_analysis_mdi.py",
    "modules/gui/driver_race/lap_box_plot_analysis/lap_box_plot_analysis_mdi.py",
    
    # Lap Box Plot
    "modules/gui/lap_box_plot_analysis/lap_box_plot_analysis_mdi.py",
    
    # Accident Analysis
    "modules/gui/accident_analysis/accident_data_manager.py",
]

# 匹配模式：
# 1. worker.signal.connect(self.slot)
# 2. worker.signal.connect(self.slot, Qt.QueuedConnection) - 已修復的
# 3. worker.finished.connect(...) - QThread 的 finished 信號也需要修復
PATTERN_SIMPLE = re.compile(
    r'(\s*)(self\._?[\w_]*worker[\w_]*\.(success|failure|progress|finished|data_loaded|error)\.connect\([^)]+)\)(?!\s*,\s*Qt\.QueuedConnection)',
    re.MULTILINE
)

def fix_file(file_path: str) -> bool:
    """修復單個文件的信號連接"""
    full_path = Path(file_path)
    
    if not full_path.exists():
        print(f"⏭️  跳過（文件不存在）: {file_path}")
        return False
    
    # 讀取文件內容
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否已經修復
    if 'Qt.QueuedConnection' in content and '.connect(' in content:
        # 計算已修復的連接數
        fixed_count = content.count('Qt.QueuedConnection')
        print(f"✅ 已修復: {file_path} ({fixed_count} 個連接)")
        return False
    
    # 查找需要修復的連接
    matches = list(PATTERN_SIMPLE.finditer(content))
    
    if not matches:
        print(f"⏭️  無需修復: {file_path}")
        return False
    
    print(f"\n🔧 修復文件: {file_path}")
    print(f"   找到 {len(matches)} 個需要修復的連接")
    
    # 替換所有匹配項
    new_content = content
    for match in reversed(matches):  # 從後往前替換，避免位置偏移
        indent = match.group(1)
        connect_call = match.group(2)
        
        # 提取信號名稱
        signal_name = match.group(3)
        
        old_line = f"{indent}{connect_call})"
        new_line = f"{indent}{connect_call}, Qt.QueuedConnection)"
        
        print(f"   - 修復 .{signal_name}.connect() 連接")
        new_content = new_content.replace(old_line, new_line, 1)
    
    # 檢查是否需要導入 Qt
    if 'from PyQt5.QtCore import' in new_content:
        # 檢查是否已經導入 Qt
        if ', Qt' not in new_content and ' Qt,' not in new_content and ' Qt\n' not in new_content:
            # 查找 PyQt5.QtCore import 語句
            import_pattern = re.compile(r'(from PyQt5\.QtCore import [^)]+)', re.MULTILINE)
            import_match = import_pattern.search(new_content)
            
            if import_match:
                old_import = import_match.group(1)
                if old_import.endswith(')'):
                    # 多行導入
                    new_import = old_import.replace(')', ', Qt)')
                else:
                    # 單行導入
                    new_import = f"{old_import}, Qt"
                
                new_content = new_content.replace(old_import, new_import, 1)
                print(f"   ✅ 已添加 Qt 導入")
    
    # 寫回文件
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"   ✅ 修復完成")
    return True

def main():
    """批量修復所有文件"""
    print("=" * 80)
    print("🔧 批量修復 QThread 信號連接")
    print("=" * 80)
    print("\n目標: 確保所有 API Worker 的信號連接使用 Qt.QueuedConnection")
    print("原因: 在非 UI 線程更新 Qt Widget 會導致程式崩潰\n")
    
    fixed_count = 0
    skipped_count = 0
    
    for file_path in FILES_TO_FIX:
        if fix_file(file_path):
            fixed_count += 1
        else:
            skipped_count += 1
    
    print("\n" + "=" * 80)
    print(f"✅ 修復完成！")
    print(f"   修復: {fixed_count} 個文件")
    print(f"   跳過: {skipped_count} 個文件")
    print("=" * 80)

if __name__ == "__main__":
    main()
