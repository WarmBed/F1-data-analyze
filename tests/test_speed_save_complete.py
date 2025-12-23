"""完整測試 Speed 模組的保存流程"""
import sys
import os

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication, QMdiSubWindow
from modules.gui.lap_analysis.speed_analysis.speed_analysis_mdi import SpeedAnalysisModule

print("=" * 80)
print("🧪 完整測試 Speed 模組的保存流程")
print("=" * 80)

# 創建 Qt 應用（必須）
app = QApplication(sys.argv)

# ========== 步驟 1: 創建 Speed 模組 ==========
print("\n📦 步驟 1: 創建 SpeedAnalysisModule")
speed_module = SpeedAnalysisModule(parent=None)

print(f"  - 模組類名: {speed_module.__class__.__name__}")
print(f"  - 是否有 analysis_type: {hasattr(speed_module, 'analysis_type')}")

if hasattr(speed_module, 'analysis_type'):
    print(f"  ✅ analysis_type = '{speed_module.analysis_type}'")
else:
    print(f"  ❌ 沒有 analysis_type！測試失敗")
    sys.exit(1)

# ========== 步驟 2: 創建 PopoutSubWindow（模擬 GUI）==========
print("\n📦 步驟 2: 創建 PopoutSubWindow（使用 analysis_module 參數）")

# 模擬 PopoutSubWindow 的創建方式（參考 f1t_gui_main.py:14520）
class TestPopoutSubWindow(QMdiSubWindow):
    """簡化版 PopoutSubWindow 用於測試"""
    def __init__(self, title="", parent_mdi=None, analysis_module=None):
        super().__init__()
        self.analysis_module = analysis_module  # ✅ 關鍵：保存 analysis_module
        self.setWindowTitle(title)

sub_window = TestPopoutSubWindow(
    title="Speed Analysis_2025_Japan_R",
    parent_mdi=None,
    analysis_module=speed_module  # ✅ 傳遞 analysis_module
)

print(f"  - SubWindow 類名: {sub_window.__class__.__name__}")
print(f"  - 是否有 analysis_module 屬性: {hasattr(sub_window, 'analysis_module')}")

if hasattr(sub_window, 'analysis_module'):
    print(f"  ✅ analysis_module 已設置")
    print(f"  - analysis_module 類名: {sub_window.analysis_module.__class__.__name__}")
    print(f"  - analysis_module.analysis_type: {sub_window.analysis_module.analysis_type}")
else:
    print(f"  ❌ 沒有 analysis_module！測試失敗")
    sys.exit(1)

# ========== 步驟 3: 模擬序列化邏輯（來自 workspace_serializer.py:224-241）==========
print("\n📦 步驟 3: 模擬序列化邏輯（策略 1: 檢查 analysis_module）")

window_type = "unknown"

# 策略 1: 檢查是否是 PopoutSubWindow 且有 analysis_module
if hasattr(sub_window, 'analysis_module') and sub_window.analysis_module:
    analysis_module = sub_window.analysis_module
    print(f"  ✅ 找到 analysis_module: {analysis_module.__class__.__name__}")
    
    # 從 analysis_module 獲取類型
    if hasattr(analysis_module, 'analysis_type'):
        window_type = analysis_module.analysis_type
        print(f"  ✅ 直接識別模組類型: '{window_type}' (來自 analysis_module.analysis_type)")
    else:
        print(f"  ❌ analysis_module 沒有 analysis_type！")

print(f"\n  🎯 序列化結果: window_type = '{window_type}'")

# ========== 步驟 4: 驗證結果 ==========
print("\n" + "=" * 80)
print("🎯 驗證結果")
print("=" * 80)

if window_type == "speed":
    print(f"\n✅ 測試成功！window_type = '{window_type}'")
    print(f"  - 保存時: window_type = '{window_type}'")
    print(f"  - 載入時: 檢查 window_type == 'speed'  ✅ 匹配！")
elif window_type == "speed_analysis":
    print(f"\n❌ 測試失敗！window_type = '{window_type}'")
    print(f"  - 保存時: window_type = '{window_type}'")
    print(f"  - 載入時: 檢查 window_type == 'speed'  ❌ 不匹配！")
    print(f"\n🔍 問題原因: 保存邏輯沒有正確讀取 analysis_type")
else:
    print(f"\n❌ 測試失敗！window_type = '{window_type}'（未知類型）")

# ========== 步驟 5: 檢查備用映射 ==========
print("\n" + "=" * 80)
print("📦 步驟 5: 檢查備用映射（策略 3: WINDOW_TYPE_MAPPING）")
print("=" * 80)

from core.workspace_serializer import WorkspaceSerializer

MAPPING = WorkspaceSerializer.WINDOW_TYPE_MAPPING
module_class_name = speed_module.__class__.__name__

print(f"\n  - 模組類名: '{module_class_name}'")
print(f"  - 映射表中的值: '{MAPPING.get(module_class_name, '未找到')}'")

if module_class_name in MAPPING:
    mapped_value = MAPPING[module_class_name]
    print(f"\n  ✅ 類名映射: '{module_class_name}' → '{mapped_value}'")
    
    if mapped_value == window_type:
        print(f"  ✅ 映射值與 analysis_type 一致！")
    else:
        print(f"  ⚠️ 映射值 '{mapped_value}' 與 analysis_type '{window_type}' 不一致")
        print(f"     （但這不影響，因為策略 1 應該優先使用 analysis_type）")

print("\n" + "=" * 80)
print("🎯 最終結論")
print("=" * 80)

if window_type == "speed":
    print("\n✅ 保存邏輯正確！")
    print("  - SubWindow 有 analysis_module 屬性")
    print("  - analysis_module 有 analysis_type = 'speed'")
    print("  - 序列化應該保存 window_type = 'speed'")
    print("\n🔍 **但用戶實際數據庫中是 'speed_analysis'，說明實際運行時邏輯不同！**")
    print("  - 可能原因 1: 用戶的 SubWindow 沒有 analysis_module 屬性（進入策略 2）")
    print("  - 可能原因 2: 保存時使用了類名映射（但映射表明明是 'speed'）")
    print("  - 可能原因 3: 代碼在實際運行時有不同行為（需要實際測試）")
else:
    print("\n❌ 保存邏輯有問題！")
    print(f"  - 預期 window_type = 'speed'")
    print(f"  - 實際 window_type = '{window_type}'")

print("=" * 80)

# 退出應用
app.quit()
