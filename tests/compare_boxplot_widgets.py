#!/usr/bin/env python3
"""
深度比較 Throttle Box Plot 和 Lap Time Box Plot 的實現差異
"""

import re
from pathlib import Path

def extract_methods(file_path):
    """提取檔案中的所有方法"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找所有方法定義
    method_pattern = r'^\s{4}def\s+(\w+)\s*\([^)]*\):'
    methods = re.findall(method_pattern, content, re.MULTILINE)
    return set(methods)

def extract_imports(file_path):
    """提取檔案中的所有 import"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    imports = []
    for line in content.split('\n'):
        if line.strip().startswith('from ') or line.strip().startswith('import '):
            imports.append(line.strip())
    return imports

def extract_attributes(file_path):
    """提取 __init__ 中的所有屬性"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找到 __init__ 方法
    init_match = re.search(r'def __init__\(self[^)]*\):(.*?)(?=\n    def |\nclass |\Z)', content, re.DOTALL)
    if not init_match:
        return []
    
    init_content = init_match.group(1)
    
    # 找所有 self.xxx = 的屬性
    attr_pattern = r'self\.(\w+)\s*='
    attributes = re.findall(attr_pattern, init_content)
    return set(attributes)

def check_method_implementation(file_path, method_name):
    """檢查方法是否存在且有實現"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 找方法定義及其內容
    pattern = rf'def {method_name}\(self[^)]*\):(.*?)(?=\n    def |\nclass |\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if not match:
        return False, None
    
    method_body = match.group(1)
    lines = [line for line in method_body.split('\n') if line.strip() and not line.strip().startswith('#')]
    
    return True, len(lines)

# 檔案路徑
throttle_path = Path('modules/gui/Throttle_analysis/throttle_box_plot_analysis/throttle_box_plot_chart_widget.py')
lap_path = Path('modules/gui/driver_race/lap_box_plot_analysis/lap_box_plot_chart_widget.py')

print("=" * 80)
print("深度比較：Throttle Box Plot vs Lap Time Box Plot")
print("=" * 80)

# 1. 方法比較
print("\n[1] 方法比較")
print("-" * 80)
throttle_methods = extract_methods(throttle_path)
lap_methods = extract_methods(lap_path)

print(f"Throttle 方法數量: {len(throttle_methods)}")
print(f"Lap Time 方法數量: {len(lap_methods)}")

only_throttle = throttle_methods - lap_methods
only_lap = lap_methods - throttle_methods
common = throttle_methods & lap_methods

if only_throttle:
    print(f"\n❌ 只在 Throttle 中: {len(only_throttle)} 個")
    for method in sorted(only_throttle):
        print(f"   - {method}")

if only_lap:
    print(f"\n❌ 只在 Lap Time 中: {len(only_lap)} 個")
    for method in sorted(only_lap):
        print(f"   - {method}")

print(f"\n✅ 共同方法: {len(common)} 個")

# 2. Import 比較
print("\n[2] Import 比較")
print("-" * 80)
throttle_imports = extract_imports(throttle_path)
lap_imports = extract_imports(lap_path)

print("Throttle imports:")
for imp in throttle_imports[:5]:
    print(f"   {imp}")

print("\nLap Time imports:")
for imp in lap_imports[:5]:
    print(f"   {imp}")

# 檢查關鍵 import
critical_imports = ['QMenu', 'QCursor']
print(f"\n關鍵 import 檢查:")
for imp in critical_imports:
    in_throttle = any(imp in line for line in throttle_imports)
    in_lap = any(imp in line for line in lap_imports)
    print(f"   {imp}: Throttle={in_throttle}, Lap={in_lap}")

# 3. 屬性比較
print("\n[3] __init__ 屬性比較")
print("-" * 80)
throttle_attrs = extract_attributes(throttle_path)
lap_attrs = extract_attributes(lap_path)

print(f"Throttle 屬性數量: {len(throttle_attrs)}")
print(f"Lap Time 屬性數量: {len(lap_attrs)}")

only_throttle_attrs = throttle_attrs - lap_attrs
only_lap_attrs = lap_attrs - throttle_attrs

if only_throttle_attrs:
    print(f"\n❌ 只在 Throttle 中: {sorted(only_throttle_attrs)}")

if only_lap_attrs:
    print(f"\n❌ 只在 Lap Time 中: {sorted(only_lap_attrs)}")

# 4. 關鍵 Filter 方法檢查
print("\n[4] Filter 功能方法實現檢查")
print("-" * 80)

filter_methods = [
    '_show_context_menu',
    '_hide_driver',
    'show_all_drivers',
    'mousePressEvent'
]

for method in filter_methods:
    throttle_exists, throttle_lines = check_method_implementation(throttle_path, method)
    lap_exists, lap_lines = check_method_implementation(lap_path, method)
    
    status = "✅" if (throttle_exists and lap_exists) else "❌"
    print(f"{status} {method}:")
    print(f"   Throttle: {'存在' if throttle_exists else '不存在'} ({throttle_lines} 行)" if throttle_exists else f"   Throttle: 不存在")
    print(f"   Lap Time: {'存在' if lap_exists else '不存在'} ({lap_lines} 行)" if lap_exists else f"   Lap Time: 不存在")

# 5. 搜尋關鍵程式碼片段
print("\n[5] 關鍵程式碼片段檢查")
print("-" * 80)

key_snippets = [
    ('hidden_drivers', 'hidden_drivers 集合'),
    ('QMenu', 'QMenu 導入'),
    ('QCursor', 'QCursor 導入'),
    ('visible_drivers =', '過濾可見車手'),
    ('menu.exec_', '顯示右鍵選單'),
]

with open(throttle_path, 'r', encoding='utf-8') as f:
    throttle_content = f.read()
with open(lap_path, 'r', encoding='utf-8') as f:
    lap_content = f.read()

for snippet, desc in key_snippets:
    throttle_count = throttle_content.count(snippet)
    lap_count = lap_content.count(snippet)
    
    status = "✅" if (throttle_count > 0 and lap_count > 0) else "❌"
    print(f"{status} {desc}:")
    print(f"   Throttle: {throttle_count} 次")
    print(f"   Lap Time: {lap_count} 次")

print("\n" + "=" * 80)
print("分析完成")
print("=" * 80)
