"""
測試 Qt.QueuedConnection 是否會阻止 API 調用
"""

from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, Qt, QObject, QCoreApplication
import sys

class TestWorker(QThread):
    """測試 Worker"""
    test_signal = pyqtSignal(str)
    
    def run(self):
        print("🔵 Worker: 開始執行 (在 Worker 線程)")
        self.test_signal.emit("Hello from Worker Thread!")
        print("🔵 Worker: 信號已發射")

class TestReceiver(QObject):
    """測試接收器"""
    
    def __init__(self):
        super().__init__()
        self.received = False
    
    @pyqtSlot(str)
    def on_test_signal(self, message):
        print(f"🟢 Receiver: 收到信號: {message}")
        self.received = True
        QCoreApplication.quit()

def test_auto_connection():
    """測試 AutoConnection (默認)"""
    print("\n" + "=" * 80)
    print("測試 1: AutoConnection (默認)")
    print("=" * 80)
    
    app = QCoreApplication(sys.argv)
    
    worker = TestWorker()
    receiver = TestReceiver()
    
    # 使用默認連接 (AutoConnection)
    worker.test_signal.connect(receiver.on_test_signal)
    
    worker.start()
    worker.wait()  # 等待 Worker 完成
    
    # 處理事件循環
    app.processEvents()
    
    if receiver.received:
        print("✅ AutoConnection: 信號成功接收")
    else:
        print("❌ AutoConnection: 信號未接收")
    
    return receiver.received

def test_queued_connection():
    """測試 QueuedConnection"""
    print("\n" + "=" * 80)
    print("測試 2: QueuedConnection")
    print("=" * 80)
    
    app = QCoreApplication(sys.argv)
    
    worker = TestWorker()
    receiver = TestReceiver()
    
    # 使用 QueuedConnection
    worker.test_signal.connect(receiver.on_test_signal, Qt.QueuedConnection)
    
    worker.start()
    worker.wait()  # 等待 Worker 完成
    
    # 處理事件循環（QueuedConnection 需要事件循環）
    app.processEvents()
    
    if receiver.received:
        print("✅ QueuedConnection: 信號成功接收")
    else:
        print("❌ QueuedConnection: 信號未接收（可能需要事件循環）")
    
    return receiver.received

def main():
    print("=" * 80)
    print("🔍 測試 Qt 信號連接類型對信號傳遞的影響")
    print("=" * 80)
    
    result1 = test_auto_connection()
    result2 = test_queued_connection()
    
    print("\n" + "=" * 80)
    print("📊 測試結果")
    print("=" * 80)
    print(f"AutoConnection: {'✅ 成功' if result1 else '❌ 失敗'}")
    print(f"QueuedConnection: {'✅ 成功' if result2 else '❌ 失敗'}")
    print("=" * 80)
    
    if result1 and result2:
        print("\n✅ 結論: Qt.QueuedConnection 不會阻止信號傳遞")
        print("   問題不在於 QueuedConnection 的使用")
    else:
        print("\n❌ 結論: 信號連接存在問題")

if __name__ == "__main__":
    main()
