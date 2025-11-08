#!/usr/bin/env python3
"""
Track Analysis 修復驗證測試
==============================

測試修復後的 Track Analysis 模組是否仍會導致 GUI 卡死
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QTextEdit
from PyQt5.QtCore import QTimer

class TestMainWindow(QMainWindow):
    """測試主窗口"""
    
    def __init__(self):
        super().__init__()
        self.track_module = None
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Track Analysis 修復驗證測試")
        self.resize(800, 600)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 狀態標籤
        self.status_label = QLabel("準備就緒")
        self.status_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(self.status_label)
        
        # 測試按鈕
        test_btn = QPushButton("🚀 測試打開 Track Analysis (會觸發 API 請求)")
        test_btn.setStyleSheet("font-size: 12pt; padding: 10px;")
        test_btn.clicked.connect(self.test_track_analysis)
        layout.addWidget(test_btn)
        
        # 響應測試按鈕
        response_btn = QPushButton("👆 點我測試 GUI 響應（如果能點擊說明沒卡死）")
        response_btn.setStyleSheet("font-size: 12pt; padding: 10px; background-color: #4CAF50; color: white;")
        response_btn.clicked.connect(lambda: self.log("✅ GUI 響應正常！"))
        layout.addWidget(response_btn)
        
        # 日誌顯示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        self.log("✅ 測試窗口初始化完成")
        self.log("📝 測試方法：")
        self.log("   1. 點擊「測試打開 Track Analysis」按鈕")
        self.log("   2. 觀察 GUI 是否卡死（能否點擊綠色按鈕）")
        self.log("   3. 如果綠色按鈕能點擊，說明修復成功！")
        self.log("")
        self.log("⚠️  注意：API Server 未啟動時，會在 45 秒後超時並顯示錯誤")
    
    def log(self, message):
        """記錄日誌"""
        self.log_text.append(message)
        print(message)
    
    def test_track_analysis(self):
        """測試 Track Analysis"""
        try:
            self.status_label.setText("🚀 正在載入 Track Analysis...")
            self.log("\n" + "="*80)
            self.log("開始測試 Track Analysis")
            self.log("="*80)
            
            # 導入模組
            from modules.gui.track_analysis import TrackAnalysisUniversal
            self.log("✅ 成功導入 TrackAnalysisUniversal")
            
            # 創建模組實例
            self.log("🔧 創建 Track Analysis 實例...")
            self.track_module = TrackAnalysisUniversal()
            self.log("✅ 實例創建完成")
            
            # 更新參數（這會觸發 API 請求）
            self.log("📡 更新參數並觸發 API 請求...")
            self.log("   ⚠️  這裡是關鍵測試點：如果 GUI 卡死，就是 API Worker 的問題")
            
            # 使用 QTimer 延遲執行，避免阻塞 UI 更新
            QTimer.singleShot(100, self.trigger_api_request)
            
        except Exception as e:
            self.log(f"❌ 錯誤: {e}")
            import traceback
            traceback.print_exc()
            self.status_label.setText("❌ 測試失敗")
    
    def trigger_api_request(self):
        """觸發 API 請求"""
        try:
            self.log("🔥 調用 update_parameters() - 即將觸發 API Worker")
            self.log("   💡 如果現在 GUI 卡死，說明 Worker 有同步阻塞問題")
            self.log("   💡 如果 GUI 仍可操作，說明修復成功！")
            
            self.track_module.update_parameters(
                year=2025,
                race="Japan",
                session="R"
            )
            
            self.log("✅ update_parameters() 返回")
            self.log("👉 現在嘗試點擊綠色按鈕測試 GUI 響應！")
            self.status_label.setText("⏳ API 請求中... (最多等待 45 秒)")
            
            # 定時檢查狀態
            self.check_timer = QTimer()
            self.check_timer.timeout.connect(self.check_status)
            self.check_timer.start(1000)  # 每秒檢查一次
            
        except Exception as e:
            self.log(f"❌ 觸發 API 請求失敗: {e}")
            import traceback
            traceback.print_exc()
            self.status_label.setText("❌ 測試失敗")
    
    def check_status(self):
        """檢查狀態"""
        if self.track_module and hasattr(self.track_module, 'data_manager'):
            if self.track_module.data_manager._is_loading:
                # 仍在載入中
                self.log("⏳ 仍在等待 API 響應...")
            else:
                # 載入完成（成功或失敗）
                self.log("🏁 API 請求已完成")
                self.status_label.setText("✅ 測試完成（請查看日誌）")
                self.check_timer.stop()

if __name__ == "__main__":
    print("\n" + "="*80)
    print("Track Analysis 修復驗證測試")
    print("="*80)
    print("\n此測試將驗證以下修復：")
    print("1. _cleanup_api_worker() 的閉包洩漏問題")
    print("2. API Worker 的異步執行是否正確")
    print("3. GUI 是否會在 API 請求時卡死")
    print("\n" + "="*80 + "\n")
    
    app = QApplication(sys.argv)
    window = TestMainWindow()
    window.show()
    sys.exit(app.exec_())
