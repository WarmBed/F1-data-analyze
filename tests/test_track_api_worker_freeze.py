#!/usr/bin/env python3
"""
Track Analysis API Worker 卡死診斷工具
========================================

測試 TrackAnalysisApiWorker 是否會導致 GUI 卡死
"""

import sys
import time
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QLabel
from PyQt5.QtCore import QThread, pyqtSignal

class TestApiWorker(QThread):
    """測試用 API Worker"""
    
    progress = pyqtSignal(int)
    success = pyqtSignal(dict)
    failure = pyqtSignal(str)
    
    def __init__(self, timeout=45.0, parent=None):
        super().__init__(parent)
        self.timeout = timeout
    
    def run(self):
        try:
            print(f"[TEST_WORKER] 🚀 開始執行 (timeout={self.timeout}秒)")
            self.progress.emit(20)
            
            endpoint = "http://localhost:8000/api/v2/analysis/execute"
            params = {
                "function_id": 2,
                "year": 2025,
                "race": "Japan",
                "session": "R"
            }
            
            start_time = time.perf_counter()
            print(f"[TEST_WORKER] ⏳ 開始 requests.post()... (這裡會阻塞最多 {self.timeout} 秒)")
            
            response = requests.post(
                endpoint,
                params=params,
                timeout=self.timeout,
                headers={"Accept": "application/json"}
            )
            
            elapsed = time.perf_counter() - start_time
            print(f"[TEST_WORKER] ✅ requests.post() 完成！耗時: {elapsed:.2f} 秒")
            
            self.progress.emit(70)
            response.raise_for_status()
            
            payload = response.json()
            self.success.emit(payload)
            print(f"[TEST_WORKER] ✅ 成功")
        except Exception as exc:
            elapsed = time.perf_counter() - start_time
            print(f"[TEST_WORKER] ❌ 錯誤（耗時 {elapsed:.2f} 秒）: {exc}")
            self.failure.emit(str(exc))
        finally:
            print(f"[TEST_WORKER] 🏁 Worker 結束")
            self.progress.emit(100)

class TestWindow(QWidget):
    """測試窗口"""
    
    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        self.status_label = QLabel("點擊按鈕啟動 API Worker")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # 測試按鈕 1: 長超時 (45秒)
        btn1 = QPushButton("測試 Track Analysis API (45秒超時)")
        btn1.clicked.connect(lambda: self.start_test(45.0))
        layout.addWidget(btn1)
        
        # 測試按鈕 2: 短超時 (5秒)
        btn2 = QPushButton("測試 Track Analysis API (5秒超時)")
        btn2.clicked.connect(lambda: self.start_test(5.0))
        layout.addWidget(btn2)
        
        # 取消按鈕
        cancel_btn = QPushButton("取消 Worker")
        cancel_btn.clicked.connect(self.cancel_worker)
        layout.addWidget(cancel_btn)
        
        self.setLayout(layout)
        self.setWindowTitle("Track API Worker 診斷工具")
        self.resize(500, 200)
    
    def start_test(self, timeout):
        """啟動測試"""
        if self.worker and self.worker.isRunning():
            self.status_label.setText("❌ Worker 已在運行，請先取消")
            return
        
        self.status_label.setText(f"🚀 啟動 API Worker (timeout={timeout}秒)...\n⚠️  注意觀察 GUI 是否卡死！")
        
        print("\n" + "="*80)
        print(f"開始測試：timeout={timeout}秒")
        print("="*80 + "\n")
        
        self.worker = TestApiWorker(timeout=timeout, parent=self)
        self.worker.progress.connect(self.on_progress)
        self.worker.success.connect(self.on_success)
        self.worker.failure.connect(self.on_failure)
        self.worker.finished.connect(lambda: print("[MAIN] Worker.finished 信號觸發"))
        self.worker.start()
        
        print("[MAIN] Worker.start() 已調用，主線程繼續執行...")
        print("[MAIN] 💡 如果 GUI 能正常響應，說明 Worker 是異步的")
        print("[MAIN] ⚠️  如果 GUI 卡死，說明有同步阻塞問題")
    
    def on_progress(self, value):
        print(f"[MAIN] 進度: {value}%")
        self.status_label.setText(f"⏳ 執行中... {value}%\n👉 嘗試點擊其他按鈕測試 GUI 響應")
    
    def on_success(self, payload):
        print(f"[MAIN] 成功: {type(payload)}")
        self.status_label.setText(f"✅ 成功！\n數據類型: {type(payload)}")
    
    def on_failure(self, error):
        print(f"[MAIN] 失敗: {error}")
        self.status_label.setText(f"❌ 失敗: {error}\n💡 這是預期行為（API 未啟動）")
    
    def cancel_worker(self):
        """取消 Worker"""
        if self.worker and self.worker.isRunning():
            print("[MAIN] 🛑 請求中斷 Worker...")
            self.worker.requestInterruption()
            self.worker.quit()
            
            # 等待短暫時間
            if not self.worker.wait(200):
                print("[MAIN] ⚠️  Worker 未在 200ms 內停止，強制終止")
                self.worker.terminate()
                self.worker.wait(1000)
            
            self.status_label.setText("🛑 Worker 已取消")
            print("[MAIN] Worker 已停止")
        else:
            self.status_label.setText("❌ 沒有正在運行的 Worker")

if __name__ == "__main__":
    print("\n" + "="*80)
    print("Track Analysis API Worker 卡死診斷工具")
    print("="*80)
    print("\n使用方法：")
    print("1. 點擊按鈕啟動 API Worker")
    print("2. 觀察終端輸出和 GUI 響應")
    print("3. 如果 GUI 卡死，說明 Worker 阻塞了主線程")
    print("4. 如果 GUI 仍可操作，說明 Worker 是異步的")
    print("\n" + "="*80 + "\n")
    
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())
