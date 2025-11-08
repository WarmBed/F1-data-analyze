#!/usr/bin/env python3
"""
檢查 F1T_GUI.spec 是否包含所有必要的模組
"""

import os
import sys
from pathlib import Path

print("=" * 70)
print("F1T_GUI.spec 完整性檢查")
print("=" * 70)

# 讀取 SPEC 檔案
spec_file = Path("F1T_GUI.spec")
with open(spec_file, 'r', encoding='utf-8') as f:
    spec_content = f.read()

# 需要檢查的關鍵模組類別
critical_modules = {
    "Track Analysis 子模組": [
        "modules.gui.track_analysis.track_analysis_mdi",
        "modules.gui.track_analysis.track_analysis_module",
        "modules.gui.track_analysis.track_data_loader",
        "modules.gui.track_analysis.track_data_processor",
        "modules.gui.track_analysis.track_map_widget",
    ],
    "Lap Analysis Linkage 模組": [
        "modules.gui.lap_analysis.linkage.lap_analysis_linkage_mixin",
        "modules.gui.lap_analysis.linkage.lap_analysis_linkage_drawing_mixin",
    ],
    "Workspace 序列化模組": [
        "modules.gui.workspace",
        "modules.gui.workspace.workspace_manager",
        "modules.gui.workspace.workspace_serializer",
        "modules.gui.workspace.analysis_module_adapters",
    ],
    "Telemetry Base 模組": [
        "modules.gui.lap_analysis.base.telemetry_data_loader",
        "modules.gui.lap_analysis.base.telemetry_chart_widget_base",
    ],
}

print("\n[階段 1] 檢查關鍵模組是否已包含")
print("-" * 70)

all_found = True
missing_modules = []

for category, modules in critical_modules.items():
    print(f"\n📂 {category}:")
    for module in modules:
        if f"'{module}'" in spec_content or f'"{module}"' in spec_content:
            print(f"  ✅ {module}")
        else:
            print(f"  ❌ 缺少: {module}")
            missing_modules.append(module)
            all_found = False

# 檢查 runtime_hook
print("\n[階段 2] 檢查 Runtime Hook")
print("-" * 70)
if "runtime_hooks=['pyinstaller_runtime_hook.py']" in spec_content:
    print("✅ Runtime Hook: pyinstaller_runtime_hook.py")
    # 檢查檔案是否存在
    if Path("pyinstaller_runtime_hook.py").exists():
        print("✅ Runtime Hook 檔案存在")
    else:
        print("❌ Runtime Hook 檔案不存在")
        all_found = False
else:
    print("❌ 未設定 Runtime Hook")
    all_found = False

# 檢查圖標和資源
print("\n[階段 3] 檢查資源檔案")
print("-" * 70)

resources = [
    ("image/logo.png", "Splash Screen Logo"),
    ("image/logo.ico", "應用程式圖標"),
]

for resource, desc in resources:
    if resource in spec_content:
        print(f"✅ {desc}: {resource}")
        if not Path(resource).exists():
            print(f"   ⚠️  警告: 檔案不存在!")
            all_found = False
    else:
        print(f"❌ 缺少: {desc} ({resource})")
        all_found = False

# 檢查 console 模式
print("\n[階段 4] 檢查 EXE 配置")
print("-" * 70)

if "console=False" in spec_content:
    print("✅ Console 模式: False (GUI 應用程式)")
else:
    print("⚠️  Console 模式: True (會顯示終端視窗)")

if "debug=False" in spec_content:
    print("✅ Debug 模式: False (生產環境)")
else:
    print("⚠️  Debug 模式: True (開發環境)")

if "upx=True" in spec_content:
    print("✅ UPX 壓縮: 已啟用")
else:
    print("ℹ️  UPX 壓縮: 已停用")

# 檢查 icon
if "icon='image\\\\logo.ico'" in spec_content or "icon='image/logo.ico'" in spec_content:
    print("✅ 應用程式圖標: image/logo.ico")
else:
    print("❌ 未設定應用程式圖標")

# 總結
print("\n" + "=" * 70)
print("檢查結果總結")
print("=" * 70)

if all_found and not missing_modules:
    print("✅ SPEC 檔案完整，所有關鍵模組都已包含")
    print("✅ 可以開始生成 EXE")
    sys.exit(0)
else:
    print(f"❌ 發現 {len(missing_modules)} 個缺失的模組")
    if missing_modules:
        print("\n缺失的模組列表:")
        for module in missing_modules:
            print(f"  - {module}")
    print("\n⚠️  建議先修復 SPEC 檔案再生成 EXE")
    sys.exit(1)
