"""
TrackAnalysisModule 實際整合代碼
==============================

這個檔案提供將 TrackAnalysisModule 整合到現有 f1t_gui_main.py 系統的實際代碼。

整合方式：
1. 在 f1t_gui_main.py 中添加賽道分析選項
2. 使用現有的 PopoutSubWindow 架構
3. 利用現有的參數提供者和信號系統

Author: F1T Team
Date: 2025-08-28
"""

# 在 f1t_gui_main.py 中需要添加的導入
REQUIRED_IMPORTS = """
# 賽道分析模組導入 (添加到現有導入區域)
try:
    from modules.track_analysis import TrackAnalysisModule
    TRACK_ANALYSIS_AVAILABLE = True
except ImportError:
    TRACK_ANALYSIS_AVAILABLE = False
    print("警告: TrackAnalysisModule 不可用")
"""

# 在主視窗中需要添加的按鈕代碼
MAIN_WINDOW_BUTTON_CODE = """
# 賽道分析按鈕 (添加到現有按鈕區域)
if TRACK_ANALYSIS_AVAILABLE:
    track_analysis_button = QPushButton("🏁 賽道軌跡分析")
    track_analysis_button.setFont(button_font)
    track_analysis_button.setFixedHeight(button_height)
    track_analysis_button.clicked.connect(self.open_track_analysis_window)
    track_analysis_button.setToolTip("開啟賽道位置軌跡分析視窗")
    analysis_buttons_layout.addWidget(track_analysis_button)
"""

# 在主視窗類中需要添加的方法
MAIN_WINDOW_METHOD_CODE = """
def open_track_analysis_window(self):
    \"\"\"開啟賽道分析視窗\"\"\"
    try:
        if not TRACK_ANALYSIS_AVAILABLE:
            QMessageBox.warning(self, "警告", "賽道分析模組不可用")
            return
            
        # 創建賽道分析模組實例
        track_module = TrackAnalysisModule()
        
        # 生成視窗標題
        current_year = self.main_window_parameter_provider.get_current_year()
        current_race = self.main_window_parameter_provider.get_current_race()
        current_session = self.main_window_parameter_provider.get_current_session()
        
        window_title = track_module.get_window_title(current_year, current_race, current_session)
        
        # 創建 PopoutSubWindow
        sub_window = PopoutSubWindow(
            parent=self,
            title=window_title,
            analysis_module=track_module,  # 傳遞分析模組
            sync_enabled=True,  # 預設使用同步模式
            parameter_provider=self.main_window_parameter_provider,
            global_signal_manager=self.global_signal_manager
        )
        
        # 添加到 MDI 區域
        self.mdi_area.addSubWindow(sub_window)
        sub_window.show()
        
        # 連接信號
        sub_window.window_closed.connect(lambda: self.on_subwindow_closed(sub_window))
        track_module.module_error.connect(lambda msg: self.show_error_message(f"賽道分析錯誤: {msg}"))
        
        # 記錄視窗
        self.active_subwindows.append(sub_window)
        
        # 更新狀態
        self.update_status_bar(f"已開啟賽道分析視窗: {window_title}")
        
    except Exception as e:
        QMessageBox.critical(self, "錯誤", f"無法開啟賽道分析視窗: {str(e)}")
        self.update_status_bar(f"賽道分析視窗開啟失敗: {str(e)}")
"""

def generate_integration_patch():
    """生成整合補丁檔案"""
    patch_content = f"""
# TrackAnalysisModule 整合補丁
# ============================
# 
# 此補丁提供將 TrackAnalysisModule 整合到現有 f1t_gui_main.py 的代碼。
# 
# 整合步驟：
# 1. 在導入區域添加模組導入
# 2. 在按鈕區域添加賽道分析按鈕  
# 3. 在主視窗類中添加開啟方法
#
# 日期: 2025-08-28

## 1. 導入區域修改 (在現有導入後添加)
{REQUIRED_IMPORTS}

## 2. 按鈕區域修改 (在分析按鈕佈局中添加)  
{MAIN_WINDOW_BUTTON_CODE}

## 3. 主視窗方法添加 (在 MainWindow 類中添加)
{MAIN_WINDOW_METHOD_CODE}

## 4. 菜單項目添加 (可選，在分析菜單中添加)
# 在 create_menu_bar 方法的分析菜單部分添加：
track_analysis_action = QAction("🏁 賽道軌跡分析", self)
track_analysis_action.triggered.connect(self.open_track_analysis_window)
track_analysis_action.setToolTip("開啟賽道位置軌跡分析視窗")
if TRACK_ANALYSIS_AVAILABLE:
    analysis_menu.addAction(track_analysis_action)

## 5. 快捷鍵添加 (可選)
# 在 create_shortcuts 方法中添加：
if TRACK_ANALYSIS_AVAILABLE:
    track_analysis_shortcut = QShortcut(QKeySequence("Ctrl+T"), self)
    track_analysis_shortcut.activated.connect(self.open_track_analysis_window)
"""
    
    return patch_content

if __name__ == "__main__":
    # 生成整合補丁
    patch = generate_integration_patch()
    
    # 保存到檔案
    with open("track_analysis_integration_patch.txt", "w", encoding="utf-8") as f:
        f.write(patch)
        
    print("✅ 整合補丁已生成: track_analysis_integration_patch.txt")
    print("📝 請按照補丁內容修改 f1t_gui_main.py 以完成整合")
