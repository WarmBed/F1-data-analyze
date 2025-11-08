#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試三角形符號在 GUI 中的顯示
"""

# 測試 Unicode 三角形符號
up_triangle = "\u25B2"    # ▲
down_triangle = "\u25BC"  # ▼
horizontal = "\u2500"     # ─

print("=" * 60)
print("Unicode 三角形符號測試")
print("=" * 60)

print(f"\n向上三角形: {up_triangle} (Unicode: U+25B2)")
print(f"向下三角形: {down_triangle} (Unicode: U+25BC)")
print(f"橫線: {horizontal} (Unicode: U+2500)")

print("\n組合測試:")
print(f"進步: 8 {up_triangle}")
print(f"退步: 6 {down_triangle}")
print(f"持平: 0 {horizontal}")

# 測試代碼中的實際字串
print("\n" + "=" * 60)
print("代碼中的實際使用:")
print("=" * 60)

rank_change = 8
text1 = f"{rank_change} ▲"
print(f"進步文字: '{text1}'")
print(f"repr: {repr(text1)}")

rank_change = -6
text2 = f"{abs(rank_change)} ▼"
print(f"退步文字: '{text2}'")
print(f"repr: {repr(text2)}")

# 檢查字串中的字符
print("\n" + "=" * 60)
print("字符分析:")
print("=" * 60)

test_str = "8 ▲"
for i, char in enumerate(test_str):
    print(f"位置 {i}: '{char}' (U+{ord(char):04X})")
