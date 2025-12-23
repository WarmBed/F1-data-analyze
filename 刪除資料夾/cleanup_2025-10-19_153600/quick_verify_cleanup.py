"""
快速驗證所有 Lap Analysis Chart Widget 是否有 cleanup 方法
"""

import os
import re

# 定義需要檢查的檔案
CHART_WIDGETS = [
    'modules/gui/lap_analysis/speed_analysis/speed_analysis_chart_widget.py',
    'modules/gui/lap_analysis/Throttle_analysis/throttle_analysis_chart_widget.py',
    'modules/gui/lap_analysis/acceleration_analysis/acceleration_analysis_chart_widget.py',
    'modules/gui/lap_analysis/brake_analysis/brake_analysis_chart_widget.py',
    'modules/gui/lap_analysis/gear_analysis/gear_analysis_chart_widget.py',
    'modules/gui/lap_analysis/rpm_analysis/rpm_analysis_chart_widget.py',
    'modules/gui/lap_analysis/timediff_analysis/timediff_analysis_chart_widget.py',
    'modules/gui/lap_analysis/speeddiff_analysis/speeddiff_analysis_chart_widget.py',
    'modules/gui/lap_analysis/distancediff_analysis/distancediff_analysis_chart_widget.py'
]

def check_cleanup_method(file_path):
    """檢查檔案是否有 cleanup 方法"""
    full_path = os.path.join('d:\\OneDrive\\Code\\F1-data-analyze', file_path)
    
    if not os.path.exists(full_path):
        return False, f"檔案不存在"
    
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 檢查是否有 cleanup 方法
    has_cleanup = 'def cleanup(self):' in content
    
    if has_cleanup:
        # 檢查關鍵清理步驟
        has_matplotlib = 'plt.close(self.chart_widget.figure)' in content
        has_table = 'self.stats_table.takeItem(row, col)' in content
        has_receiver = 'self.receiver.deleteLater()' in content
        
        details = []
        if has_matplotlib:
            details.append("Matplotlib")
        if has_table:
            details.append("QTableWidget")
        if has_receiver:
            details.append("Signal")
        
        return True, f"有 cleanup ({', '.join(details)})"
    else:
        return False, "缺少 cleanup 方法"

def main():
    """主程序"""
    print("=" * 80)
    print("Lap Analysis Chart Widget cleanup 方法檢查")
    print("=" * 80)
    
    results = []
    
    for file_path in CHART_WIDGETS:
        module_name = file_path.split('/')[-2].replace('_analysis', '').title()
        has_cleanup, details = check_cleanup_method(file_path)
        results.append((module_name, has_cleanup, details))
        
        status = "✅" if has_cleanup else "❌"
        print(f"{status} {module_name:20s}: {details}")
    
    print("\n" + "=" * 80)
    
    success_count = sum(1 for _, has, _ in results if has)
    total_count = len(results)
    
    print(f"結果: {success_count}/{total_count} 個模組已添加 cleanup 方法")
    
    if success_count == total_count:
        print("🎉 所有 Lap Analysis 模組已成功修復！")
    else:
        print("⚠️  部分模組仍需添加 cleanup 方法")
        for name, has, _ in results:
            if not has:
                print(f"  - {name}")
    
    print("=" * 80)

if __name__ == "__main__":
    main()
