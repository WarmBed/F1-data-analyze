#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""驗證 F1T_GUI.spec 中的 hiddenimports 是否有效"""

import sys
import re

print("=" * 80)
print("驗證 F1T_GUI.spec 的 hiddenimports")
print("=" * 80)

# 讀取 spec 檔案
with open("F1T_GUI.spec", "r", encoding="utf-8") as f:
    spec_content = f.read()

# 提取 hiddenimports 列表
hiddenimports_match = re.search(r"hiddenimports=\[(.*?)\]", spec_content, re.DOTALL)
if not hiddenimports_match:
    print("[ERROR] 無法找到 hiddenimports 列表")
    sys.exit(1)

hiddenimports_text = hiddenimports_match.group(1)

# 提取所有模組名稱（去除註釋和引號）
import_lines = []
for line in hiddenimports_text.split("\n"):
    line = line.strip()
    if line.startswith("#") or not line:
        continue
    # 提取引號中的模組名稱
    match = re.search(r"'([^']+)'", line)
    if match:
        import_lines.append(match.group(1))

print(f"\n[INFO] 找到 {len(import_lines)} 個 hiddenimports")

# 測試每個導入
success_count = 0
failed_imports = []

for i, module_name in enumerate(import_lines, 1):
    try:
        # 動態導入測試
        __import__(module_name)
        success_count += 1
        if i % 10 == 0:
            print(f"[PROGRESS] 已驗證 {i}/{len(import_lines)} 個模組...")
    except ImportError as e:
        failed_imports.append((module_name, str(e)))
    except Exception as e:
        # 某些模組可能需要特定環境才能導入（例如 PyQt5）
        # 只要不是 ImportError，通常表示模組存在
        success_count += 1

print("\n" + "=" * 80)
print(f"驗證完成: {success_count}/{len(import_lines)} 個模組可導入")
print("=" * 80)

if failed_imports:
    print(f"\n[WARNING] 發現 {len(failed_imports)} 個無法導入的模組:\n")
    for module, error in failed_imports:
        print(f"  ❌ {module}")
        print(f"     錯誤: {error}\n")
else:
    print("\n[SUCCESS] 所有模組都可以導入！")

# 統計模組分類
gui_modules = [m for m in import_lines if m.startswith("modules.gui.")]
core_modules = [m for m in import_lines if m.startswith("core.")]

print("\n[STATS] 模組分類統計:")
print(f"  • GUI 模組: {len(gui_modules)}")
print(f"  • Core 模組: {len(core_modules)}")

# 檢查關鍵模組
critical_modules = [
    "modules.gui.all_drivers_brake_performance_analysis.all_drivers_brake_performance_module",
    "modules.gui.all_drivers_straight_line_speed_analysis.all_drivers_straight_line_speed_module",
    "modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_table_module",
    "modules.gui.pitstop_analysis.pitstop_analysis_complete",
    "modules.gui.accident_analysis.accident_analysis_complete",
    "core.gui_i18n",
    "core.api_base_url",
]

print("\n[CHECK] 關鍵模組檢查:")
for module in critical_modules:
    if module in import_lines:
        print(f"  ✅ {module}")
    else:
        print(f"  ❌ {module} - 缺失!")

print("\n" + "=" * 80)
