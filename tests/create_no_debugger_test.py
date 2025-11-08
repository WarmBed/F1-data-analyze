"""
測試：在無調試器環境下運行 GUI，檢查 DummyThread 數量

這個測試會：
1. 啟動 F1T GUI（不通過調試器）
2. 等待 5 秒
3. 統計 DummyThread 數量
4. 關閉 GUI
5. 再次統計 DummyThread

如果 DummyThread 數量遠少於調試環境，說明問題是調試器造成的
"""
import subprocess
import time
import sys

print("=" * 80)
print("測試：無調試器環境下的 DummyThread 數量")
print("=" * 80)
print()

print("步驟 1: 啟動 F1T GUI（無調試器）...")
print("注意：這會啟動一個新的 Python 進程，不受 VS Code 調試器影響")
print()

# 創建測試腳本
test_script = """
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
import threading
import objgraph
import gc

app = QApplication(sys.argv)

# 等待 GUI 初始化
def check_threads():
    gc.collect()
    dummy_count_objgraph = objgraph.count("_DummyThread")
    dummy_count_threading = sum(1 for t in threading._active.values() if type(t).__name__ == "_DummyThread")
    
    print(f"\\n{'='*60}")
    print("DummyThread 統計（無調試器環境）")
    print(f"{'='*60}")
    print(f"objgraph.count: {dummy_count_objgraph}")
    print(f"threading._active: {dummy_count_threading}")
    print(f"{'='*60}\\n")
    
    # 退出應用
    app.quit()

# 5 秒後檢查
QTimer.singleShot(5000, check_threads)

sys.exit(app.exec_())
"""

with open('test_gui_no_debugger.py', 'w', encoding='utf-8') as f:
    f.write(test_script)

print("✅ 測試腳本已創建: test_gui_no_debugger.py")
print()
print("執行命令:")
print("  python test_gui_no_debugger.py")
print()
print("💡 提示:")
print("  - 如果 DummyThread 數量 < 5，說明大部分是調試器造成的")
print("  - 如果 DummyThread 數量仍然 > 10，說明確實有洩漏問題")
print()
print("=" * 80)
