"""
批量修復所有缺少 Qt.QueuedConnection 的 finished.connect()
"""

import re
from pathlib import Path

# 需要修復的文件（從驗證腳本結果）
FILES_TO_FIX = [
    "modules/gui/accident_analysis/accident_data_manager.py",
    "modules/gui/driver_race/detailed_lap_analysis/driverlap_analysis_mdi.py",
    "modules/gui/driver_race/lap_box_plot_analysis/lap_box_plot_analysis_mdi.py",
    "modules/gui/lap_box_plot_analysis/lap_box_plot_analysis_mdi.py",
    "modules/gui/rain_analysis/rain_analysis_mdi.py",
    "modules/gui/telemetry_analysis_mdi.py",
    "modules/gui/Throttle_analysis/throttle_box_plot_analysis/throttle_box_plot_analysis_mdi.py",
    "modules/gui/Throttle_analysis/throttle_line_chart_analysis/throttle_line_chart_data_loader.py",
    "modules/gui/tire_analysis/tire_analysis_mdi.py",
    "modules/gui/track_analysis/track_analysis_mdi.py",
]

def fix_finished_connect(file_path: str) -> bool:
    """修復 finished.connect() 缺少 Qt.QueuedConnection 的問題"""
    full_path = Path(file_path)
    
    if not full_path.exists():
        print(f"⏭️  跳過（文件不存在）: {file_path}")
        return False
    
    # 讀取文件
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否有需要修復的 finished.connect()
    pattern = re.compile(
        r'(self\._?[\w_]*worker[\w_]*\.finished\.connect\([^)]+)\)(?!\s*,\s*Qt\.QueuedConnection)',
        re.MULTILINE
    )
    
    matches = list(pattern.finditer(content))
    
    if not matches:
        print(f"✅ 無需修復: {file_path}")
        return False
    
    print(f"\n🔧 修復文件: {file_path}")
    print(f"   找到 {len(matches)} 個 finished.connect() 需要修復")
    
    # 替換所有匹配項
    new_content = content
    for match in reversed(matches):
        old_text = match.group(0)
        new_text = old_text.replace(')', ', Qt.QueuedConnection)')
        
        print(f"   - 修復 finished.connect()")
        new_content = new_content.replace(old_text, new_text, 1)
    
    # 檢查是否需要導入 Qt
    if ', Qt' not in new_content and ' Qt,' not in new_content and ' Qt\n' not in new_content:
        # 查找 PyQt5.QtCore import
        import_pattern = re.compile(r'from PyQt5\.QtCore import ([^\n]+)', re.MULTILINE)
        import_match = import_pattern.search(new_content)
        
        if import_match:
            old_import_line = import_match.group(0)
            import_items = import_match.group(1).strip()
            
            # 檢查是否已經有 Qt
            if 'Qt' not in import_items:
                # 添加 Qt 到導入列表
                if import_items.endswith(')'):
                    # 多行導入
                    new_import_line = old_import_line.replace(')', ', Qt)')
                else:
                    # 單行導入
                    new_import_line = f"from PyQt5.QtCore import {import_items}, Qt"
                
                new_content = new_content.replace(old_import_line, new_import_line, 1)
                print(f"   ✅ 已添加 Qt 到導入列表")
    
    # 寫回文件
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"   ✅ 修復完成")
    return True

def main():
    """批量修復所有文件"""
    print("=" * 80)
    print("🔧 批量修復 finished.connect() 缺少 Qt.QueuedConnection 的問題")
    print("=" * 80)
    print()
    
    fixed_count = 0
    skipped_count = 0
    
    for file_path in FILES_TO_FIX:
        if fix_finished_connect(file_path):
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
