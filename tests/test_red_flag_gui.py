"""
GUI 整合測試：System Settings Dialog 中的 Red Flag Filter
遵循反幻覺編碼五原則
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from modules.gui.settings.system_settings_dialog import SystemSettingsDialog
from core.gui_settings_manager import gui_settings_manager

class TestMainWindow(QMainWindow):
    """測試用主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Settings Dialog 測試")
        self.resize(400, 200)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 開啟 System Settings 按鈕
        open_button = QPushButton("開啟 System Settings")
        open_button.clicked.connect(self.open_system_settings)
        layout.addWidget(open_button)
        
        # 顯示當前設定按鈕
        show_button = QPushButton("顯示當前設定")
        show_button.clicked.connect(self.show_current_settings)
        layout.addWidget(show_button)
        
        # 訂閱設定變更信號
        gui_settings_manager.boxplot_settings_changed.connect(self.on_settings_changed)
        
        print("=" * 60)
        print("GUI 整合測試已啟動")
        print("=" * 60)
        print("\n請執行以下手動測試:")
        print("1. 點擊 '開啟 System Settings'")
        print("2. 切換到 'Box Plot Analysis' 分頁")
        print("3. 檢查是否有 'Filter red flag laps' 選項")
        print("4. 測試勾選/取消勾選該選項")
        print("5. 點擊 OK 按鈕")
        print("6. 點擊 '顯示當前設定' 驗證變更")
        print("\n" + "=" * 60 + "\n")
    
    def open_system_settings(self):
        """開啟 System Settings 對話框"""
        print("\n[測試] 開啟 System Settings Dialog")
        dialog = SystemSettingsDialog(self, gui_settings_manager)
        
        # 驗證 filter_red_flags_checkbox 存在
        assert hasattr(dialog, 'filter_red_flags_checkbox'), "❌ 錯誤: filter_red_flags_checkbox 不存在"
        print("✅ filter_red_flags_checkbox 已創建")
        
        # 驗證初始狀態
        current_settings = gui_settings_manager.get_boxplot_settings()
        expected_checked = current_settings.get("filter_red_flags", True)
        actual_checked = dialog.filter_red_flags_checkbox.isChecked()
        
        assert actual_checked == expected_checked, f"❌ 錯誤: 初始狀態不符 (expected={expected_checked}, actual={actual_checked})"
        print(f"✅ 初始狀態正確: filter_red_flags = {actual_checked}")
        
        # 顯示對話框
        result = dialog.exec_()
        
        if result:
            print("✅ 用戶點擊了 OK，設定已保存")
        else:
            print("ℹ️ 用戶點擊了 Cancel，設定未變更")
    
    def show_current_settings(self):
        """顯示當前設定"""
        print("\n[當前設定]")
        settings = gui_settings_manager.get_boxplot_settings()
        for key, value in settings.items():
            print(f"  {key}: {value}")
        print()
    
    def on_settings_changed(self, new_settings):
        """設定變更回調"""
        print("\n📡 [信號接收] BoxPlot 設定已變更:")
        print(f"  filter_red_flags: {new_settings.get('filter_red_flags')}")
        print()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 初始化測試
    print("初始化測試環境...")
    window = TestMainWindow()
    window.show()
    
    sys.exit(app.exec_())
