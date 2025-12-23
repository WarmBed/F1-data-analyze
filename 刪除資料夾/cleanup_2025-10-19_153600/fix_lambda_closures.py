# Lambda 閉包洩漏批次修復腳本

import re

# 讀取文件
with open('f1t_gui_main.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 統計原始 lambda 數量
lambda_count_before = len(re.findall(r'sub_window\.window_closed\.connect\(lambda:', content))
print(f"修復前 lambda 數量: {lambda_count_before}")

# 在文件開頭添加 functools import（如果不存在）
if 'from functools import partial' not in content:
    # 在 import 區塊中添加
    content = content.replace(
        'from PyQt5.QtWidgets import (',
        'from functools import partial\nfrom PyQt5.QtWidgets import ('
    )
    print("✅ 已添加 functools.partial import")

# 替換模式 1: on_lap_analysis_window_closed(analysis_module)
pattern1 = r'(\s+)sub_window\.window_closed\.connect\(lambda: self\.on_lap_analysis_window_closed\(analysis_module\)\)'
replacement1 = r'''\1# 🔴 使用 partial 避免 lambda 閉包洩漏
\1sub_window.window_closed.connect(
\1    partial(self.on_lap_analysis_window_closed, analysis_module)
\1)'''

content, count1 = re.subn(pattern1, replacement1, content)
print(f"✅ 修復 on_lap_analysis_window_closed(analysis_module): {count1} 處")

# 替換模式 2: on_lap_analysis_window_closed(chart_widget)
pattern2 = r'(\s+)sub_window\.window_closed\.connect\(lambda: self\.on_lap_analysis_window_closed\(chart_widget\)\)'
replacement2 = r'''\1# 🔴 使用 partial 避免 lambda 閉包洩漏
\1sub_window.window_closed.connect(
\1    partial(self.on_lap_analysis_window_closed, chart_widget)
\1)'''

content, count2 = re.subn(pattern2, replacement2, content)
print(f"✅ 修復 on_lap_analysis_window_closed(chart_widget): {count2} 處")

# 替換模式 3: on_subwindow_closed(sub_window)
pattern3 = r'(\s+)sub_window\.window_closed\.connect\(lambda: self\.on_subwindow_closed\(sub_window\)\)'
replacement3 = r'''\1# 🔴 使用 partial 避免 lambda 閉包洩漏
\1sub_window.window_closed.connect(
\1    partial(self.on_subwindow_closed, sub_window)
\1)'''

content, count3 = re.subn(pattern3, replacement3, content)
print(f"✅ 修復 on_subwindow_closed(sub_window): {count3} 處")

# 統計修復後的 lambda 數量
lambda_count_after = len(re.findall(r'sub_window\.window_closed\.connect\(lambda:', content))
print(f"修復後 lambda 數量: {lambda_count_after}")
print(f"總共修復: {count1 + count2 + count3} 處")

# 寫回文件
with open('f1t_gui_main.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ 批次修復完成！")
print(f"修復前: {lambda_count_before} 個 lambda")
print(f"修復後: {lambda_count_after} 個 lambda")
print(f"減少: {lambda_count_before - lambda_count_after} 個 lambda")
