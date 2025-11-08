"""測試 Speed 模組的序列化邏輯"""
import sys
import os

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 導入必要模組
from modules.gui.lap_analysis.speed_analysis.speed_analysis_mdi import SpeedAnalysisModule
from PyQt5.QtWidgets import QApplication, QMdiSubWindow

print("=" * 80)
print("🧪 測試 Speed 模組的屬性讀取")
print("=" * 80)

# 創建 Qt 應用（必須）
app = QApplication(sys.argv)

# 1. 測試模組實例化
print("\n📦 步驟 1: 創建 SpeedAnalysisModule 實例")
speed_module = SpeedAnalysisModule(parent=None)

print(f"  - 類名: {speed_module.__class__.__name__}")
print(f"  - 是否有 analysis_type 屬性: {hasattr(speed_module, 'analysis_type')}")

if hasattr(speed_module, 'analysis_type'):
    print(f"  ✅ analysis_type = '{speed_module.analysis_type}'")
else:
    print(f"  ❌ 沒有 analysis_type 屬性！")

# 2. 測試 SubWindow 包裝後的情況
print("\n📦 步驟 2: 創建 MDI SubWindow 並包裝模組")
sub_window = QMdiSubWindow()

# 檢查是否有 analysis_module 屬性（PopoutSubWindow 的特性）
print(f"  - SubWindow 類名: {sub_window.__class__.__name__}")
print(f"  - 是否有 analysis_module 屬性: {hasattr(sub_window, 'analysis_module')}")

# 3. 模擬 PopoutSubWindow 的設置方式
print("\n📦 步驟 3: 模擬 PopoutSubWindow 設置 analysis_module")
sub_window.analysis_module = speed_module

print(f"  - 設置後是否有 analysis_module: {hasattr(sub_window, 'analysis_module')}")
if hasattr(sub_window, 'analysis_module'):
    module = sub_window.analysis_module
    print(f"  - analysis_module 類名: {module.__class__.__name__}")
    print(f"  - analysis_module 是否有 analysis_type: {hasattr(module, 'analysis_type')}")
    if hasattr(module, 'analysis_type'):
        print(f"  ✅ 可以讀取 analysis_type = '{module.analysis_type}'")

# 4. 測試類名映射
print("\n📦 步驟 4: 測試 WINDOW_TYPE_MAPPING 映射")
from core.workspace_serializer import WorkspaceSerializer

MAPPING = WorkspaceSerializer.WINDOW_TYPE_MAPPING
module_class_name = speed_module.__class__.__name__

print(f"  - 模組類名: '{module_class_name}'")
print(f"  - 映射表中的值: '{MAPPING.get(module_class_name, '未找到')}'")

if module_class_name in MAPPING:
    mapped_type = MAPPING[module_class_name]
    print(f"  ✅ 類名映射結果: '{module_class_name}' → '{mapped_type}'")
    
    # 檢查是否與 analysis_type 一致
    if mapped_type == speed_module.analysis_type:
        print(f"  ✅ 映射值與 analysis_type 一致！")
    else:
        print(f"  ⚠️ 映射值 '{mapped_type}' 與 analysis_type '{speed_module.analysis_type}' 不一致！")
else:
    print(f"  ❌ 類名 '{module_class_name}' 不在映射表中！")

# 5. 檢查映射表中所有 SpeedAnalysis 相關的條目
print("\n📦 步驟 5: 檢查映射表中的所有相關條目")
speed_related = {k: v for k, v in MAPPING.items() if 'speed' in k.lower() or 'speed' in v.lower()}

if speed_related:
    print(f"  找到 {len(speed_related)} 個相關條目:")
    for class_name, window_type in speed_related.items():
        print(f"    - '{class_name}' → '{window_type}'")
else:
    print("  ❌ 沒有找到相關條目！")

print("\n" + "=" * 80)
print("🎯 測試結論")
print("=" * 80)

print("\n如果保存時:")
print(f"  1. 使用 analysis_type: window_type = '{speed_module.analysis_type}'")
print(f"  2. 使用類名映射: window_type = '{MAPPING.get(module_class_name, 'unknown')}'")

print("\n載入時期望:")
print(f"  - workspace_serializer.py 檢查: window_type == 'speed'")

if MAPPING.get(module_class_name) == speed_module.analysis_type:
    print("\n✅ 一致！應該可以正常工作")
else:
    print(f"\n❌ 不一致！映射表返回 '{MAPPING.get(module_class_name)}' 但期望 '{speed_module.analysis_type}'")

print("=" * 80)

# 退出應用
app.quit()
