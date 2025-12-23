
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
    
    print(f"\n{'='*60}")
    print("DummyThread 統計（無調試器環境）")
    print(f"{'='*60}")
    print(f"objgraph.count: {dummy_count_objgraph}")
    print(f"threading._active: {dummy_count_threading}")
    print(f"{'='*60}\n")
    
    # 退出應用
    app.quit()

# 5 秒後檢查
QTimer.singleShot(5000, check_threads)

sys.exit(app.exec_())
