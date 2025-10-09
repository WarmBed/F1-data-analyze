#!/usr/bin/env python3
"""
理想圈分析選項對話框
讓使用者在啟動 Ideal Lap Analysis 時選擇分析類型

完全基於 DetailedLapAnalysisOptionsDialog 的樣式和結構
支援多選，讓使用者可以同時選擇多種分析類型：
1. 排名表格總覽 (Ranking Table)
2. 分段熱力圖 (Sector Heatmap)
3. 分段對比圖 (Sector Comparison)

作者: F1T Team
日期: 2025-10-09
版本: 1.0.0 (支援多選，完全複製 DetailedLapAnalysisOptionsDialog 結構和行為)
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QGroupBox, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# 嘗試導入國際化模組
try:
    from core.gui_i18n import tr, set_gui_language
    I18N_AVAILABLE = True
except ImportError:
    # 如果沒有國際化模組，使用簡單的回退函數
    def tr(key, fallback=None):
        return fallback if fallback else key
    def set_gui_language(lang):
        pass
    I18N_AVAILABLE = False


class IdealLapAnalysisOptionsDialog(QDialog):
    """
    理想圈分析選項對話框
    
    完全採用 DetailedLapAnalysisOptionsDialog 的樣式和結構（使用 QListWidget）
    支援多選，讓使用者可以同時選擇多種分析類型：
    1. 排名表格總覽 - 顯示所有車手理想圈排名、時間差、全場最速對比
    2. 分段熱力圖 - 視覺化各車手在 S1/S2/S3 的最佳表現
    3. 分段對比圖 - 理想圈 vs 最快圈的分段詳細對比
    
    範例：
        dialog = IdealLapAnalysisOptionsDialog(parent)
        if dialog.exec_() == QDialog.Accepted:
            selected_types = dialog.get_selected_types()
            # selected_types 可能是 ["ranking_table", "sector_heatmap"] 或所有三個
    """
    
    # 分析類型常數
    TYPE_RANKING_TABLE = "ranking_table"        # 排名表格總覽
    TYPE_SECTOR_HEATMAP = "sector_heatmap"      # 分段熱力圖
    TYPE_SECTOR_COMPARISON = "sector_comparison"  # 分段對比圖
    
    def __init__(self, parent=None):
        """
        初始化對話框
        
        Args:
            parent: 父視窗（通常是主視窗）
        """
        super().__init__(parent)
        
        # 保留用戶當前語言設定，不強制切換
        # if I18N_AVAILABLE:
        #     set_gui_language('en')  # 已移除強制設定
        
        self.setWindowTitle(tr("ideal_lap_options_title", "Ideal Lap Analysis Options"))
        self.setModal(True)
        self.setFixedSize(480, 380)  # 增加尺寸以容納三個選項
        
        # 設置字體 - 與主程式保持一致
        font = QFont("Arial", 8)
        self.setFont(font)
        
        # 設置視窗樣式 - 完全採用 DetailedLapAnalysisOptionsDialog 的樣式
        self._apply_stylesheet()
        
        # 初始化 UI
        self.init_ui()
        
        print("[IDEAL_LAP_DIALOG] IdealLapAnalysisOptionsDialog 已初始化")
    
    def _apply_stylesheet(self):
        """應用樣式表 - 完全複製自 DetailedLapAnalysisOptionsDialog"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f0f0f0;
                color: #333333;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
                font-size: 8pt;
            }
            QLabel {
                color: #333333;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
                font-size: 8pt;
            }
            QGroupBox {
                color: #333333;
                font-weight: bold;
                font-size: 8pt;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                margin-top: 8px;
                padding-top: 5px;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px 0 3px;
                background: #f0f0f0;
            }
            QListWidget {
                background-color: white;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                font-size: 8pt;
                outline: none;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #EEEEEE;
            }
            QListWidget::item:selected {
                background-color: #d1e7dd;
                color: #0f5132;
            }
            QListWidget::item:hover {
                background-color: #E8F5E9;
            }
            QPushButton {
                background: #FFFFFF;
                color: #333333;
                border: 1px solid #AAAAAA;
                border-radius: 3px;
                font-size: 8pt;
                padding: 4px 12px;
                min-height: 18px;
                font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
            }
            QPushButton:hover {
                background: #F0F0F0;
                border: 1px solid #999999;
            }
            QPushButton:pressed {
                background: #E0E0E0;
            }
        """)
    
    def init_ui(self):
        """初始化使用者介面 - 完全複製 DetailedLapAnalysisOptionsDialog 結構"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 標題 - 完全複製樣式
        title_label = QLabel(tr("select_ideal_lap_analysis_type", 
                                "Please select ideal lap analysis type(s)"))
        title_label.setStyleSheet("""
            font-size: 8pt; 
            color: #333333; 
            margin-bottom: 3px; 
            font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
        """)
        layout.addWidget(title_label)
        
        # 分析類型選擇區域 - 使用 QListWidget（多選模式）
        type_group = QGroupBox(tr("analysis_type", "Analysis Type"))
        type_layout = QVBoxLayout(type_group)
        type_layout.setSpacing(5)
        type_layout.setContentsMargins(10, 12, 10, 10)
        
        # 創建列表小工具（多選模式）
        self.analysis_list = QListWidget()
        self.analysis_list.setSelectionMode(QListWidget.MultiSelection)
        self.analysis_list.setFixedHeight(120)  # 容納三個項目
        
        # 添加選項項目
        item1 = QListWidgetItem(tr("ranking_table", "Ranking Table (All Drivers Overview)"))
        item1.setData(Qt.UserRole, self.TYPE_RANKING_TABLE)
        self.analysis_list.addItem(item1)
        
        item2 = QListWidgetItem(tr("sector_heatmap", "Sector Heatmap (S1/S2/S3 Performance)"))
        item2.setData(Qt.UserRole, self.TYPE_SECTOR_HEATMAP)
        self.analysis_list.addItem(item2)
        
        item3 = QListWidgetItem(tr("sector_comparison", "Sector Comparison (Ideal vs Fastest)"))
        item3.setData(Qt.UserRole, self.TYPE_SECTOR_COMPARISON)
        self.analysis_list.addItem(item3)
        
        # 預設選中第一個（排名表格）
        self.analysis_list.setCurrentRow(0)
        
        type_layout.addWidget(self.analysis_list)
        
        # 快速選擇按鈕
        quick_select_layout = QHBoxLayout()
        quick_select_layout.setSpacing(8)
        
        select_all_btn = QPushButton(tr("select_all", "Select All"))
        select_all_btn.setFixedHeight(28)
        select_all_btn.clicked.connect(self.select_all)
        quick_select_layout.addWidget(select_all_btn)
        
        select_none_btn = QPushButton(tr("select_none", "Clear"))
        select_none_btn.setFixedHeight(28)
        select_none_btn.clicked.connect(self.select_none)
        quick_select_layout.addWidget(select_none_btn)
        
        quick_select_layout.addStretch()
        type_layout.addLayout(quick_select_layout)
        
        layout.addWidget(type_group)
        
        # 說明文字
        desc_label = QLabel(
            "• " + tr("ranking_table_desc", "Ranking Table: Shows ideal lap ranking, time gaps, and session fastest lap") + "\n"
            "• " + tr("heatmap_desc", "Sector Heatmap: Visualizes sector performance across all drivers (S1/S2/S3)") + "\n"
            "• " + tr("comparison_desc", "Sector Comparison: Compares ideal lap vs fastest lap sector breakdown")
        )
        desc_label.setStyleSheet("""
            color: #777777; 
            font-size: 7pt; 
            padding: 5px 8px; 
            background-color: #fafafa; 
            border: 1px solid #e0e0e0; 
            border-radius: 2px;
            font-family: 'Arial', 'Microsoft JhengHei', sans-serif;
        """)
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # 彈性空間
        layout.addStretch()
        
        # 按鈕區域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        button_layout.addStretch()
        
        # 確定按鈕
        ok_btn = QPushButton(tr("ok", "OK"))
        ok_btn.setFixedSize(60, 26)
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        # 取消按鈕
        cancel_btn = QPushButton(tr("cancel", "Cancel"))
        cancel_btn.setFixedSize(60, 26)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        print("[IDEAL_LAP_DIALOG] UI 初始化完成")
    
    def get_selected_types(self) -> list:
        """
        獲取使用者選擇的分析類型（支援多選）
        
        Returns:
            list: 選中的分析類型列表，例如 ["ranking_table", "sector_heatmap"]
        """
        selected_types = []
        for item in self.analysis_list.selectedItems():
            selected_type = item.data(Qt.UserRole)
            selected_types.append(selected_type)
        
        print(f"[IDEAL_LAP_DIALOG] 使用者選擇的分析類型: {selected_types}")
        
        # 如果沒有選擇任何項目，返回預設值（排名表格）
        if not selected_types:
            print("[IDEAL_LAP_DIALOG] 未選擇任何項目，返回預設值: [ranking_table]")
            return [self.TYPE_RANKING_TABLE]
        
        return selected_types
    
    def select_all(self):
        """選擇所有分析類型"""
        print("[IDEAL_LAP_DIALOG] 選擇所有分析類型")
        for i in range(self.analysis_list.count()):
            self.analysis_list.item(i).setSelected(True)
    
    def select_none(self):
        """取消選擇所有分析類型"""
        print("[IDEAL_LAP_DIALOG] 取消選擇所有分析類型")
        self.analysis_list.clearSelection()
    
    def accept(self):
        """確定按鈕被點擊"""
        selected_types = self.get_selected_types()
        type_names = []
        for st in selected_types:
            if st == self.TYPE_RANKING_TABLE:
                type_names.append("Ranking Table")
            elif st == self.TYPE_SECTOR_HEATMAP:
                type_names.append("Sector Heatmap")
            elif st == self.TYPE_SECTOR_COMPARISON:
                type_names.append("Sector Comparison")
        print(f"[IDEAL_LAP_DIALOG] 使用者確認選擇: {', '.join(type_names)}")
        super().accept()
    
    def reject(self):
        """取消按鈕被點擊"""
        print("[IDEAL_LAP_DIALOG] 使用者取消選擇")
        super().reject()


# 測試代碼
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # 創建並顯示對話框
    dialog = IdealLapAnalysisOptionsDialog()
    
    if dialog.exec_() == QDialog.Accepted:
        selected_types = dialog.get_selected_types()
        print(f"✅ 測試結果: 使用者選擇了 {len(selected_types)} 個分析類型:")
        for st in selected_types:
            if st == IdealLapAnalysisOptionsDialog.TYPE_RANKING_TABLE:
                print("   - 📊 排名表格總覽")
            elif st == IdealLapAnalysisOptionsDialog.TYPE_SECTOR_HEATMAP:
                print("   - 🔥 分段熱力圖")
            elif st == IdealLapAnalysisOptionsDialog.TYPE_SECTOR_COMPARISON:
                print("   - 📈 分段對比圖")
    else:
        print("❌ 測試結果: 使用者取消了選擇")
    
    sys.exit()
