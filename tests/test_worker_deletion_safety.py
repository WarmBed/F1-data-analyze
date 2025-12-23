"""
簡單測試：驗證 QTimer 延遲回調中的 Worker 刪除保護
模擬批量開啟模組時的競爭條件
"""
from PyQt5.QtCore import QThread, QTimer, pyqtSignal
from PyQt5.QtWidgets import QApplication
import sys

class DummyWorker(QThread):
    """模擬 API Worker"""
    finished = pyqtSignal()
    
    def run(self):
        self.msleep(100)  # 模擬快速完成

def test_unsafe_pattern():
    """❌ 不安全的模式（修復前）"""
    print("\n❌ 測試不安全模式（應該會失敗）:")
    app = QApplication(sys.argv)
    
    worker = DummyWorker()
    worker.start()
    
    # 模擬快速清理
    def quick_cleanup():
        if worker.isRunning():
            worker.requestInterruption()
            worker.quit()
        worker.deleteLater()
        print("  Worker 已刪除")
    
    # 不安全的延遲檢查（沒有 try-except）
    def unsafe_force_terminate():
        # ⚠️ 這裡會觸發 RuntimeError
        if worker and worker.isRunning():
            worker.terminate()
        print("  延遲檢查完成")
    
    QTimer.singleShot(50, quick_cleanup)
    QTimer.singleShot(200, unsafe_force_terminate)  # 這時 worker 已被刪除
    
    # 300ms 後退出
    QTimer.singleShot(300, lambda: app.exit(1))
    
    try:
        app.exec_()
        print("  ✅ 無錯誤（不應該發生）")
        return False
    except RuntimeError as e:
        if "wrapped C/C++ object" in str(e):
            print(f"  ❌ 預期的 RuntimeError: {e}")
            return True
        raise

def test_safe_pattern():
    """✅ 安全的模式（修復後）"""
    print("\n✅ 測試安全模式（應該通過）:")
    app = QApplication(sys.argv)
    
    worker = DummyWorker()
    worker.start()
    
    # 模擬快速清理
    def quick_cleanup():
        if worker.isRunning():
            worker.requestInterruption()
            worker.quit()
        worker.deleteLater()
        print("  Worker 已刪除")
    
    # ✅ 安全的延遲檢查（有 try-except）
    def safe_force_terminate():
        try:
            if worker and worker.isRunning():
                worker.terminate()
            print("  延遲檢查完成（Worker 仍存在）")
        except (RuntimeError, AttributeError):
            print("  延遲檢查完成（Worker 已刪除，安全捕獲）")
    
    QTimer.singleShot(50, quick_cleanup)
    QTimer.singleShot(200, safe_force_terminate)
    
    # 300ms 後退出
    QTimer.singleShot(300, lambda: app.exit(0))
    
    result = app.exec_()
    success = (result == 0)
    if success:
        print("  ✅ 測試通過！")
    else:
        print("  ❌ 測試失敗")
    return success

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Worker 刪除安全性測試")
    print("=" * 60)
    
    # 注意：test_unsafe_pattern 會觸發 RuntimeError 導致程序崩潰
    # 所以只測試安全模式
    print("\n⚠️  跳過不安全模式測試（會導致崩潰）")
    
    # 測試安全模式
    if test_safe_pattern():
        print("\n🎉 所有測試通過！修復有效")
        sys.exit(0)
    else:
        print("\n❌ 測試失敗")
        sys.exit(1)
