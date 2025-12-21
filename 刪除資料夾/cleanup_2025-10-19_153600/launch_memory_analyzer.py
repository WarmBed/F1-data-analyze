"""
快速啟動 Objgraph 診斷視窗（包含 Python Console）
"""

from modules.gui.diagnostics.objgraph_window import ObjgraphDiagnosticWindow
from PyQt5.QtWidgets import QApplication
import sys

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ObjgraphDiagnosticWindow()
    window.show()
    
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║              🔍 Objgraph 診斷視窗已啟動（含 Python Console）              ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 功能說明：

1. **Python Console Tab** (新增！)
   - 直接執行 Python 代碼進行診斷
   - 6 個快速診斷按鈕
   - 自訂代碼執行區

2. **快速診斷按鈕**：
   ✅ 檢查 DummyThread 數量
   ✅ 檢查 TelemetryApiWorker
   ✅ 檢查 threading._active
   ✅ 檢查 DataLoader 洩漏
   ✅ 檢查死亡執行緒
   ✅ 強制 GC + 報告

3. **使用方式**：
   - 點擊快速診斷按鈕自動執行常用檢查
   - 或在「自訂 Python 代碼」區輸入代碼手動執行
   - 執行結果會顯示在「執行結果」區

4. **可用變數**：
   - objgraph, gc, threading, sys, os, Path, datetime

🎯 現在你可以：
   1. 切換到「Python Console」Tab
   2. 點擊快速診斷按鈕
   3. 查看診斷結果
    """)
    
    sys.exit(app.exec_())
