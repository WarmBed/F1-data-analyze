"""診斷 Workspace 保存邏輯中的 window_type 來源"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 模擬 GUI 創建 Speed 模組的流程
from PyQt5.QtWidgets import QApplication
from modules.gui.lap_analysis.speed_analysis.speed_analysis_mdi import SpeedAnalysisModule

# 關鍵：導入 PopoutSubWindow
import importlib
f1t_gui = importlib.import_module('f1t_gui_main')
PopoutSubWindow = f1t_gui.PopoutSubWindow

print("=" * 80)
print("診斷: Workspace 保存時的 window_type 來源")
print("=" * 80)

app = QApplication(sys.argv)

# 步驟 1: 創建 Speed 模組（完全模擬 GUI 的創建方式）
print("\n[步驟 1] 創建 SpeedAnalysisModule")
speed_module = SpeedAnalysisModule()
print(f"  - 模組類名: {speed_module.__class__.__name__}")
print(f"  - analysis_type: {speed_module.analysis_type}")

# 步驟 2: 創建 PopoutSubWindow（完全模擬 f1t_gui_main.py:14520）
print("\n[步驟 2] 創建 PopoutSubWindow（模擬 GUI 創建方式）")
sub_window = PopoutSubWindow(
    title="Speed Analysis_2025_United States_R",
    parent_mdi=None,
    analysis_module=speed_module  # ✅ 關鍵：傳遞 analysis_module
)

print(f"  - SubWindow 類名: {sub_window.__class__.__name__}")
print(f"  - 是否有 analysis_module: {hasattr(sub_window, 'analysis_module')}")

if hasattr(sub_window, 'analysis_module'):
    print(f"  - analysis_module 類名: {sub_window.analysis_module.__class__.__name__}")
    print(f"  - analysis_module.analysis_type: {sub_window.analysis_module.analysis_type}")

# 步驟 3: 模擬序列化邏輯（來自 workspace_serializer.py:224-267）
print("\n[步驟 3] 模擬序列化邏輯")

window_type = "unknown"

# 策略 1: 檢查是否有 analysis_module
if hasattr(sub_window, 'analysis_module') and sub_window.analysis_module:
    analysis_module = sub_window.analysis_module
    print(f"  ✅ 找到 analysis_module: {analysis_module.__class__.__name__}")
    
    # 從 analysis_module 獲取類型
    if hasattr(analysis_module, 'analysis_type'):
        window_type = analysis_module.analysis_type
        print(f"  ✅ 讀取 analysis_type: '{window_type}'")
    else:
        print(f"  ❌ analysis_module 沒有 analysis_type!")
else:
    print(f"  ❌ SubWindow 沒有 analysis_module!")
    # 備選方案：使用類名映射
    from core.workspace_serializer import WorkspaceSerializer
    widget_class_name = speed_module.__class__.__name__
    window_type = WorkspaceSerializer.WINDOW_TYPE_MAPPING.get(widget_class_name, "unknown")
    print(f"  ⚠️ 使用類名映射: {widget_class_name} → {window_type}")

print(f"\n[結果] window_type = '{window_type}'")

# 步驟 4: 驗證
print("\n" + "=" * 80)
print("驗證")
print("=" * 80)

if window_type == "speed":
    print(f"✅ 正確！window_type = 'speed'")
    print(f"  - 保存時：window_type = 'speed'")
    print(f"  - 載入時：檢查 window_type == 'speed'  ✅ 匹配")
else:
    print(f"❌ 錯誤！window_type = '{window_type}'")
    print(f"  - 預期：'speed'")
    print(f"  - 實際：'{window_type}'")
    print(f"\n可能原因：")
    print(f"  1. PopoutSubWindow 沒有正確設置 analysis_module 屬性")
    print(f"  2. 序列化邏輯沒有正確讀取 analysis_module.analysis_type")
    print(f"  3. 代碼路徑與測試不同")

print("=" * 80)

app.quit()
