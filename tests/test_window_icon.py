"""
測試主視窗圖示設置
"""
import sys
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

# 測試圖示路徑
icon_path = Path("image") / "logo.ico"

print("=" * 60)
print("🖼️  F1T GUI 視窗圖示測試")
print("=" * 60)

# 檢查 1: 檔案存在性
print(f"\n✅ 檢查 1: ICO 檔案存在")
print(f"   路徑: {icon_path}")
print(f"   存在: {icon_path.exists()}")
if icon_path.exists():
    print(f"   大小: {icon_path.stat().st_size:,} bytes")

# 檢查 2: QIcon 載入
print(f"\n✅ 檢查 2: QIcon 載入測試")
app = QApplication(sys.argv)
icon = QIcon(str(icon_path))
print(f"   QIcon 是否為空: {icon.isNull()}")
if not icon.isNull():
    available_sizes = icon.availableSizes()
    print(f"   可用解析度數量: {len(available_sizes)}")
    print(f"   可用解析度: {[f'{s.width()}x{s.height()}' for s in available_sizes]}")

# 檢查 3: 模擬主視窗設置
print(f"\n✅ 檢查 3: 模擬主視窗圖示設置")
from PyQt5.QtWidgets import QMainWindow
test_window = QMainWindow()
test_window.setWindowIcon(icon)
window_icon = test_window.windowIcon()
print(f"   視窗圖示已設置: {not window_icon.isNull()}")

print("\n" + "=" * 60)
print("✅ 所有檢查完成！")
print("=" * 60)
print("\n💡 提示:")
print("   - EXE 圖示: 用於檔案總管和工作列")
print("   - 視窗圖示: 用於應用程式視窗左上角和 ALT+TAB")
print("   - 兩者都使用 logo.ico，但設置方式不同")
print("\n🎯 下一步: 啟動完整 GUI 驗證視窗圖示")
print("   指令: python f1t_gui_main.py")
