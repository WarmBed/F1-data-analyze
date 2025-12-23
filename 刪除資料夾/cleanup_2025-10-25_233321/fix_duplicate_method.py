#!/usr/bin/env python3
# 修復 f1t_gui_main.py 中的重複方法

lines = open('f1t_gui_main.py', 'r', encoding='utf-8').readlines()

# 找到行號
first = None
second = None
for i, line in enumerate(lines):
    if 'def _on_fastest_lap_changed(self, state):' in line:
        if first is None:
            first = i
        else:
            second = i
            break

# 刪除第一個到第二個之間的內容 (保留第一個之前的註釋)
if first and second:
    new_lines = lines[:first-3] + lines[second-3:]
    open('f1t_gui_main.py', 'w', encoding='utf-8').writelines(new_lines)
    print(f"OK: 刪除了 {first+1}-{second} 行，剩餘 {len(new_lines)} 行")
