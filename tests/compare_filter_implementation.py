"""
逐行比較 Throttle Box Plot 和 Lap Time Box Plot 的 Filter 功能實現

對比關鍵方法：
1. __init__ - hidden_drivers 初始化
2. _hide_driver - 隱藏車手邏輯
3. show_all_drivers - 恢復所有車手
4. _detect_hovered_driver - 檢測懸停車手
5. mousePressEvent - 滑鼠點擊事件
6. mouseMoveEvent - 滑鼠移動事件
7. leaveEvent - 滑鼠離開事件
8. _draw_box_plots - 繪製過濾邏輯
9. _calculate_y_range - Y 軸計算過濾邏輯
"""

import ast
import difflib
from pathlib import Path

def extract_method(file_path, method_name):
    """提取指定方法的完整代碼"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tree = ast.parse(content)
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == method_name:
            # 獲取方法的行號
            start_line = node.lineno
            end_line = node.end_lineno
            
            # 提取代碼
            lines = content.split('\n')
            method_code = '\n'.join(lines[start_line-1:end_line])
            
            return method_code, start_line, end_line
    
    return None, None, None

def compare_methods(throttle_file, lap_file, method_name):
    """比較兩個檔案中的同一方法"""
    print(f"\n{'='*80}")
    print(f"比較方法: {method_name}")
    print(f"{'='*80}\n")
    
    throttle_code, t_start, t_end = extract_method(throttle_file, method_name)
    lap_code, l_start, l_end = extract_method(lap_file, method_name)
    
    if throttle_code is None:
        print(f"❌ Throttle: 方法 {method_name} 不存在")
    else:
        print(f"✅ Throttle: {method_name} (行 {t_start}-{t_end})")
    
    if lap_code is None:
        print(f"❌ Lap Time: 方法 {method_name} 不存在")
    else:
        print(f"✅ Lap Time: {method_name} (行 {l_start}-{l_end})")
    
    if throttle_code is None or lap_code is None:
        print("\n⚠️ 無法比較（方法缺失）\n")
        return False
    
    # 比較代碼
    if throttle_code.strip() == lap_code.strip():
        print("\n✅ 完全相同\n")
        return True
    else:
        print("\n❌ 存在差異\n")
        
        # 顯示差異
        throttle_lines = throttle_code.split('\n')
        lap_lines = lap_code.split('\n')
        
        diff = difflib.unified_diff(
            throttle_lines,
            lap_lines,
            fromfile='Throttle Box Plot',
            tofile='Lap Time Box Plot',
            lineterm=''
        )
        
        print("差異詳情:")
        print("-" * 80)
        for line in diff:
            if line.startswith('---') or line.startswith('+++'):
                print(f"\033[1m{line}\033[0m")
            elif line.startswith('-'):
                print(f"\033[91m{line}\033[0m")  # 紅色
            elif line.startswith('+'):
                print(f"\033[92m{line}\033[0m")  # 綠色
            elif line.startswith('@@'):
                print(f"\033[94m{line}\033[0m")  # 藍色
            else:
                print(line)
        print("-" * 80)
        
        return False

# 檔案路徑
throttle_file = Path('modules/gui/Throttle_analysis/throttle_box_plot_analysis/throttle_box_plot_chart_widget.py')
lap_file = Path('modules/gui/driver_race/lap_box_plot_analysis/lap_box_plot_chart_widget.py')

print("=" * 80)
print("Throttle Box Plot vs Lap Time Box Plot - Filter 功能逐行比較")
print("=" * 80)

# 檢查檔案是否存在
if not throttle_file.exists():
    print(f"❌ Throttle 檔案不存在: {throttle_file}")
    exit(1)

if not lap_file.exists():
    print(f"❌ Lap Time 檔案不存在: {lap_file}")
    exit(1)

print(f"\n✅ Throttle 檔案: {throttle_file}")
print(f"✅ Lap Time 檔案: {lap_file}")

# 要比較的方法列表
methods_to_compare = [
    '__init__',
    '_hide_driver',
    'show_all_drivers',
    '_detect_hovered_driver',
    'mousePressEvent',
    'mouseMoveEvent',
    'leaveEvent',
    '_calculate_y_range',
    '_draw_box_plots',
]

# 統計結果
same_count = 0
diff_count = 0
missing_count = 0

for method in methods_to_compare:
    result = compare_methods(throttle_file, lap_file, method)
    if result is True:
        same_count += 1
    elif result is False:
        diff_count += 1
    else:
        missing_count += 1

# 總結
print("\n" + "=" * 80)
print("比較總結")
print("=" * 80)
print(f"相同方法: {same_count}")
print(f"有差異方法: {diff_count}")
print(f"缺失方法: {missing_count}")
print("=" * 80)

if diff_count > 0 or missing_count > 0:
    print("\n⚠️ 發現差異或缺失，需要進一步檢查")
    exit(1)
else:
    print("\n✅ 所有關鍵方法實現一致")
    exit(0)
