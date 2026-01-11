# -*- coding: utf-8 -*-
"""
StyleApplier - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtWidgets import QFrame
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMdiSubWindow
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QScrollArea
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QToolBar
from PyQt5.QtWidgets import QTreeWidget
from PyQt5.QtWidgets import QWidget

from core.logger import get_logger
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QMdiArea
from PyQt5.QtWidgets import QStatusBar
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QAbstractItemView

logger = get_logger(__name__)


class StyleApplier:
    """從 f1t_gui_main.py 提取的 apply_style_h 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def apply_style_h(self):
        """應用風格H樣式 - 專業賽車分析工作站 (白色主題)"""
        style = """
        /* 主視窗 - 白色專業主題 */
        QMainWindow {
            background-color: #FFFFFF;
            color: #333333;
            font-family: "Arial", "Helvetica", sans-serif;
            font-size: 8pt;
        }
        
        /* 菜單欄 - 標準白色 */
        QMenuBar {
            background-color: #F8F8F8;
            border-bottom: 1px solid #CCCCCC;
            color: #333333;
            font-size: 8pt;
            padding: 1px;
        }
        QMenuBar::item {
            background-color: transparent;
            padding: 2px 6px;
            border-radius: 0px;
        }
        QMenuBar::item:selected {
            background-color: #E8E8E8;
        }
        QMenu {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            color: #333333;
            padding: 1px;
        }
        QMenu::item {
            padding: 2px 8px;
            border-radius: 0px;
        }
        QMenu::item:selected {
            background-color: #E8E8E8;
        }
        
        /* 右鍵選單 */
        #ContextMenu {
            background-color: #FFFFFF;
            border: 1px solid #AAAAAA;
            color: #333333;
            padding: 2px;
        }
        #ContextMenu::item {
            padding: 3px 12px;
            border-radius: 0px;
        }
        #ContextMenu::item:selected {
            background-color: #E8E8E8;
        }
        
        /* 左側面板白色主題 */
        #LeftPanel {
            background-color: #F8F8F8;
            color: #333333;
        }
        #FunctionTreeWidget {
            background-color: #FFFFFF;
            color: #333333;
        }
        
        /* 通用工具欄 - 白色主題 */
        QToolBar {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
            color: #333333;
            font-size: 8pt;
            spacing: 1px;
            padding: 1px;
        }
        QToolBar QToolButton {
            background: transparent;
            border: 1px solid transparent;
            padding: 2px;
            margin: 0px;
            color: #333333;
            font-size: 9pt;
            border-radius: 0px;
        }
        QToolBar QToolButton:hover {
            background-color: #E8E8E8;
            border: 1px solid #AAAAAA;
        }
        QToolBar QToolButton:pressed {
            background-color: #D8D8D8;
        }
        
        /* 專業工具欄 */
        #ProfessionalToolbar {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
            color: #333333;
            font-size: 8pt;
            spacing: 1px;
            padding: 1px;
        }
        #ProfessionalToolbar QToolButton {
            background: transparent;
            border: 1px solid transparent;
            padding: 2px;
            margin: 0px;
            color: #333333;
            font-size: 9pt;
            border-radius: 0px;
        }
        #ProfessionalToolbar QToolButton:hover {
            background-color: #E8E8E8;
            border: 1px solid #AAAAAA;
        }
        #ProfessionalToolbar QToolButton:pressed {
            background-color: #D8D8D8;
        }
        #ProfessionalToolbar QLabel {
            color: #666666;
            font-size: 7pt;
            padding: 0px 2px;
        }
        
        /* 通用下拉選單 - 白色主題 */
        QComboBox {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            color: #333333;
            font-size: 8pt;
            padding: 2px 4px;
            border-radius: 0px;
        }
        QComboBox::drop-down {
            border: none;
            background-color: #E8E8E8;
            width: 15px;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 3px solid transparent;
            border-right: 3px solid transparent;
            border-top: 3px solid #333333;
            width: 0px;
            height: 0px;
        }
        QComboBox QAbstractItemView {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            selection-background-color: #E8E8E8;
            color: #333333;
        }
        QComboBox:hover {
            border-color: #888888;
        }
        
        /* 通用勾選框 - 白色主題 */
        QCheckBox {
            color: #333333;
            font-size: 8pt;
            background-color: transparent;
            border: none;
        }
        QCheckBox::indicator {
            width: 14px;
            height: 14px;
            border: 1px solid #AAAAAA;
            background-color: #FFFFFF;
        }
        QCheckBox::indicator:checked {
            background-color: #0078D4;
            border-color: #0078D4;
        }
        QCheckBox::indicator:hover {
            border-color: #888888;
        }
        
        /* 通用按鈕 - 白色主題 */
        QPushButton {
            background-color: #F8F8F8;
            border: 1px solid #CCCCCC;
            border-radius: 3px;
            padding: 5px 10px;
            font-size: 8pt;
            color: #333333;
        }
        QPushButton:hover {
            background-color: #E8E8E8;
            border-color: #999999;
        }
        QPushButton:pressed {
            background-color: #D8D8D8;
        }
        QPushButton:disabled {
            background-color: #F0F0F0;
            border-color: #E0E0E0;
            color: #999999;
        }
        
        /* 參數選擇框 */
        #ParameterCombo {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            color: #333333;
            font-size: 7pt;
            padding: 1px 2px;
            border-radius: 0px;
        }
        #ParameterCombo::drop-down {
            border: none;
            background-color: #E8E8E8;
            width: 12px;
        }
        #ParameterCombo::down-arrow {
            image: none;
            border-left: 2px solid transparent;
            border-right: 2px solid transparent;
            border-top: 2px solid #333333;
            width: 0px;
            height: 0px;
        }
        #ParameterCombo QAbstractItemView {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            selection-background-color: #E8E8E8;
            color: #333333;
        }
        
        /* 功能樹標題 */
        #FunctionTreeTitle {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
            color: #333333;
            font-weight: bold;
        }
        
        /* 通用樹狀控件 - 白色主題 */
        QTreeWidget {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            color: #333333;
            outline: none;
            font-size: 8pt;
            alternate-background-color: #F8F8F8;
        }
        QTreeWidget::item {
            height: 14px;
            border: none;
            padding: 1px 1px;
        }
        QTreeWidget::item:hover {
            background-color: #F0F0F0;
        }
        QTreeWidget::item:selected {
            background-color: #0078D4;
            color: #FFFFFF;
        }
        
        /* 專業功能樹 */
        #ProfessionalFunctionTree {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            color: #333333;
            outline: none;
            font-size: 8pt;
            alternate-background-color: #F8F8F8;
        }
        #ProfessionalFunctionTree::item {
            height: 14px;
            border: none;
            padding: 1px 1px;
        }
        #ProfessionalFunctionTree::item:hover {
            background-color: #F0F0F0;
        }
        #ProfessionalFunctionTree::item:selected {
            background-color: #0078D4;
            color: #FFFFFF;
        }
        
        /* MDI工作區 - 白色主題 - 增強版 */
        #ProfessionalMDIArea, #OverviewMDIArea {
            background-color: #F5F5F5 !important;
            background: #F5F5F5 !important;
            border: 1px solid #CCCCCC;
        }
        QMdiArea {
            background-color: #F5F5F5 !important;
            background: #F5F5F5 !important;
        }
        QMdiArea QScrollArea {
            background-color: #F5F5F5 !important;
            background: #F5F5F5 !important;
        }
        QMdiArea QScrollArea QWidget {
            background-color: #F5F5F5 !important;
            background: #F5F5F5 !important;
        }
        QMdiArea > QWidget {
            background-color: #F5F5F5 !important;
            background: #F5F5F5 !important;
        }
        QMdiArea * {
            background-color: #F5F5F5 !important;
        }
        
        /* 通用分頁控件 - 白色主題 */
        QTabWidget {
            background-color: #FFFFFF;
            border: none;
        }
        QTabWidget::pane {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
        }
        QTabWidget::tab-bar {
            alignment: left;
            height: 0px !important;  /* 強制隱藏標籤欄 */
            max-height: 0px !important;
            min-height: 0px !important;
        }
        QTabWidget QTabBar {
            height: 0px !important;  /* 完全隱藏標籤欄 */
            max-height: 0px !important;
            min-height: 0px !important;
            background: transparent !important;
            border: none !important;
        }
        QTabWidget QTabBar::tab {
            height: 0px !important;   /* 強制高度為0 */
            max-height: 0px !important;
            min-height: 0px !important;
            padding: 0px !important;  /* 移除內距 */
            margin: 0px !important;   /* 移除邊距 */
            border: none !important;  /* 移除邊框 */
            font-size: 0pt !important; /* 字體大小設為0 */
            background: transparent !important;
            color: transparent !important;
        }
        QTabWidget QTabBar::tab:selected {
            background-color: transparent;
            color: transparent;
            border: none;
            height: 0px;
            max-height: 0px;
            padding: 0px;
            margin: 0px;
        }
        QTabWidget QTabBar::tab:hover {
            background-color: transparent;
            height: 0px;
            max-height: 0px;
            padding: 0px;
            margin: 0px;
        }
        
        /* 專業分頁控件 - 白色主題 (完全隱藏標籤欄) */
        #ProfessionalTabWidget {
            background-color: #FFFFFF;
            border: none;
        }
        #ProfessionalTabWidget::pane {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
            border-top: none !important;  /* 移除上方邊框 */
        }
        #ProfessionalTabWidget::tab-bar {
            height: 0px !important;
            max-height: 0px !important;
            min-height: 0px !important;
            visible: false !important;
            display: none !important;
        }
        #ProfessionalTabWidget QTabBar {
            height: 0px !important;
            max-height: 0px !important;
            min-height: 0px !important;
            width: 0px !important;
            max-width: 0px !important;
            min-width: 0px !important;
            background: transparent !important;
            border: none !important;
            visible: false !important;
            display: none !important;
        }
        #ProfessionalTabWidget QTabBar::tab {
            height: 0px !important;
            max-height: 0px !important;
            min-height: 0px !important;
            width: 0px !important;
            max-width: 0px !important;
            min-width: 0px !important;
            padding: 0px !important;
            margin: 0px !important;
            border: none !important;
            background: transparent !important;
            color: transparent !important;
            font-size: 0pt !important;
            visible: false !important;
            display: none !important;
        }
        #ProfessionalTabWidget QTabBar::tab:selected {
            height: 0px !important;
            max-height: 0px !important;
            min-height: 0px !important;
            width: 0px !important;
            max-width: 0px !important;
            min-width: 0px !important;
            background: transparent !important;
            color: transparent !important;
            border: none !important;
            visible: false !important;
            display: none !important;
        }
        #ProfessionalTabWidget QTabBar::tab:hover {
            height: 0px !important;
            max-height: 0px !important;
            min-height: 0px !important;
            width: 0px !important;
            max-width: 0px !important;
            min-width: 0px !important;
            background: transparent !important;
            color: transparent !important;
            border: none !important;
            visible: false !important;
            display: none !important;
        }
        
        /* 分頁控制區域 */
        #TabControlArea {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
        }
        
        /* 分頁按鈕容器 - 完全隱藏 */
        #TabButtonsContainer {
            height: 0px !important;
            max-height: 0px !important;
            min-height: 0px !important;
            width: 0px !important;
            max-width: 0px !important;
            min-width: 0px !important;
            background: transparent !important;
            border: none !important;
            visible: false !important;
            display: none !important;
            padding: 0px !important;
            margin: 0px !important;
        }
        
        /* 新增分頁按鈕 */
        #AddTabButton {
            background-color: #FFFFFF;
            color: #006600;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
            font-size: 12pt;
            font-weight: bold;
        }
        #AddTabButton:hover {
            background-color: #F0F0F0;
            border-color: #006600;
        }
        #AddTabButton:pressed {
            background-color: #E8E8E8;
        }
        
        /* 關閉分頁按鈕 */
        #CloseTabButton {
            background-color: #FFFFFF;
            color: #333333;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
            font-size: 12pt;
            font-weight: bold;
        }
        #CloseTabButton:hover {
            background-color: #F0F0F0;
            border-color: #333333;
        }
        #CloseTabButton:pressed {
            background-color: #E8E8E8;
        }
        
        /* 分頁數量標籤 */
        #TabCountLabel {
            color: #333333;
            font-size: 8pt;
            font-weight: bold;
            background-color: transparent;
            border: none;
            padding: 4px 8px;
        }
        
        /* 分析控制面板 */
        #AnalysisControlArea {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
            border-top: 1px solid #CCCCCC;
        }
        
        /* 連動控制勾選框 */
        #SyncWindowsCheckbox {
            color: #333333;
            font-size: 8pt;
            background-color: transparent;
            border: none;
        }
        #SyncWindowsCheckbox::indicator {
            width: 14px;
            height: 14px;
            border: 1px solid #AAAAAA;
            background-color: #FFFFFF;
        }
        #SyncWindowsCheckbox::indicator:checked {
            background-color: #0078D4;
            border-color: #0078D4;
        }
        #SyncWindowsCheckbox::indicator:hover {
            border-color: #888888;
        }
        
        /* 遙測同步勾選框 */
        #SyncTelemetryCheckbox {
            color: #333333;
            font-size: 8pt;
            background-color: transparent;
            border: none;
        }
        #SyncTelemetryCheckbox::indicator {
            width: 14px;
            height: 14px;
            border: 1px solid #AAAAAA;
            background-color: #FFFFFF;
        }
        #SyncTelemetryCheckbox::indicator:checked {
            background-color: #00AA00;
            border-color: #00AA00;
        }
        #SyncTelemetryCheckbox::indicator:hover {
            border-color: #888888;
        }
        
        /* 控制標籤 */
        #ControlLabel {
            color: #333333;
            font-size: 8pt;
            font-weight: bold;
            background-color: transparent;
            border: none;
        }
        
        /* 分析下拉選單 */
        #AnalysisComboBox {
            background-color: #FFFFFF;
            color: #333333;
            border: 1px solid #AAAAAA;
            border-radius: 0px;
            padding: 3px 8px;
            font-size: 8pt;
            min-width: 80px;
        }
        #AnalysisComboBox::drop-down {
            background-color: #E8E8E8;
            border: none;
            width: 20px;
        }
        #AnalysisComboBox::down-arrow {
            border: none;
            width: 0px;
            height: 0px;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 6px solid #333333;
        }
        #AnalysisComboBox QAbstractItemView {
            background-color: #FFFFFF;
            color: #333333;
            border: 1px solid #AAAAAA;
            selection-background-color: #0078D4;
            font-size: 8pt;
        }
        #AnalysisComboBox:hover {
            border-color: #888888;
        }
        #AnalysisComboBox:focus {
            border-color: #0078D4;
        }
        
        /* 重新分析按鈕 */
        #ReanalyzeButton {
            background-color: #FF6B35;
            color: #FFFFFF;
            border: 1px solid #FF6B35;
            border-radius: 0px;
            font-size: 8pt;
            font-weight: bold;
        }
        #ReanalyzeButton:hover {
            background-color: #E55A2B;
            border-color: #E55A2B;
        }
        #ReanalyzeButton:pressed {
            background-color: #CC4A21;
        }
        
        /* 主分頁容器 */
        #MainTabContainer {
            background-color: #FFFFFF;
            border: none;
        }
        
        /* 數據總覽分頁 */
        #DataOverviewTab {
            background-color: #FFFFFF;
        }
        #TabTitleLabel {
            color: #333333;
            font-size: 10pt;
            font-weight: bold;
            background-color: transparent;
            border: none;
            padding: 5px;
        }
        #OverviewMDIArea {
            background-color: #F5F5F5;
            border: 1px solid #CCCCCC;
        }
        #StatsContent {
            color: #333333;
            font-size: 8pt;
            background-color: transparent;
            border: none;
            padding: 10px;
        }
        
        /* 設定對話框 */
        #SettingsDialog {
            background-color: #FFFFFF;
            color: #333333;
            border: 2px solid #CCCCCC;
        }
        #DialogTitle {
            color: #333333;
            font-size: 12pt;
            font-weight: bold;
            background-color: transparent;
            border: none;
            padding: 5px;
        }
        #SettingsGroup {
            color: #333333;
            font-size: 9pt;
            font-weight: bold;
            border: 1px solid #CCCCCC;
            border-radius: 3px;
            margin-top: 5px;
            padding-top: 5px;
        }
        #SettingsGroup::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            color: #666666;
        }
        #DialogButtonBox {
            background-color: transparent;
        }
        #DialogButtonBox QPushButton {
            background-color: #0078D4;
            color: #FFFFFF;
            border: 1px solid #0078D4;
            border-radius: 3px;
            padding: 5px 15px;
            font-size: 9pt;
            min-width: 60px;
        }
        #DialogButtonBox QPushButton:hover {
            background-color: #106EBE;
        }
        #DialogButtonBox QPushButton:pressed {
            background-color: #005A9E;
        }
        
        /* 專業MDI子視窗 - 使用自定義paintEvent繪製邊框 */
        #ProfessionalSubWindow {
            background-color: #FFFFFF;
            border: none;  /* 邊框由paintEvent繪製 */
            border-radius: 0px;
        }
        QMdiSubWindow {
            background-color: #FFFFFF;
            border: 2px solid #0078D4;  /* Windows 10/11標準藍色邊框，更明顯 */
            margin: 0px;
            padding: 0px;
        }
        QMdiSubWindow:active {
            border: 2px solid #106EBE;  /* 活動視窗使用更深的藍色 */
        }
        QMdiSubWindow QWidget {
            margin: 0px;
            padding: 0px;
        }
        QMdiSubWindow::title {
            background: #0078D4;  /* Windows 標準藍色標題欄 */
            color: #FFFFFF;  /* 白色文字 */
            height: 22px;
            padding: 2px 5px;
            margin: 0px;
            border: none;
            font-size: 11px;
            font-weight: normal;
            text-align: left;
        }
        
        QMdiSubWindow QWidget {
            border: none;
        }
        
        /* 子視窗包裝器 */
        #SubWindowWrapper {
            background-color: transparent;  /* 改為透明，讓底層調整區域可見 */
            color: #333333;
            border: none;
        }
        
        /* 視窗控制面板 */
        #WindowControlPanel {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
            border-top: 1px solid #CCCCCC;
        }
        
        /* 自定義標題欄 */
        #CustomTitleBar {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
            border-top: none;
            border-left: none;
            border-right: none;
            color: #000000;
        }
        
        /* 視窗控制按鈕 */
        #WindowControlButton {
            background-color: #F0F0F0;  /* Windows 系統按鈕背景 */
            color: #000000;  /* 黑色文字 */
            border: 1px solid #D0D0D0;  /* 淺灰色邊框 */
            border-radius: 0px;
            font-size: 8pt;
            font-weight: bold;
        }
        #WindowControlButton:hover {
            background-color: #E0E0E0;  /* 滑鼠懸停時稍深 */
        }
        #WindowControlButton:pressed {
            background-color: #D0D0D0;  /* 按下時更深 */
        }
        
        /* 恢復按鈕 */
        #RestoreButton {
            background-color: #2E8B57;
            color: #FFFFFF;
            border: 1px solid #3CB371;
            border-radius: 0px;
            font-size: 8pt;
            font-weight: bold;
        }
        #RestoreButton:hover {
            background-color: #3CB371;
        }
        #RestoreButton:pressed {
            background-color: #228B22;
        }
        
        /* X軸連動按鈕 - 紅綠狀態指示 */
        #SyncButton {
            background-color: #FF4444;  /* 預設紅色 - 未連動 */
            color: #FFFFFF;
            border: 1px solid #CC0000;
            border-radius: 0px;
            font-size: 8pt;
            font-weight: bold;
        }
        #SyncButton:hover {
            background-color: #FF6666;  /* 紅色懸停 */
        }
        #SyncButton:pressed {
            background-color: #CC0000;  /* 紅色按下 */
        }
        #SyncButton:checked {
            background-color: #00CC00;  /* 綠色 - 已連動 */
            border: 1px solid #009900;
        }
        #SyncButton:checked:hover {
            background-color: #00FF00;  /* 綠色懸停 */
        }
        
        /* 個別連動按鈕 - 藍色主題 */
        #LinkageButton {
            background-color: #2196F3;  /* 藍色 - 連動啟用 */
            color: white;
            border: 1px solid #1976D2;
            border-radius: 3px;
            font-size: 8px;
            font-weight: bold;
            text-align: center;
        }
        #LinkageButton:hover {
            background-color: #42A5F5;  /* 藍色懸停 */
        }
        #LinkageButton:pressed {
            background-color: #1565C0;  /* 藍色按下 */
        }
        #LinkageButton:!checked {
            background-color: #9E9E9E;  /* 灰色 - 連動停用 */
            border: 1px solid #757575;
        }
        #LinkageButton:!checked:hover {
            background-color: #BDBDBD;  /* 灰色懸停 */
        }
        
        /* 車手與圈數同步按鈕 - 紫色主題（遙測模組專用） */
        #DriverLapSyncButton {
            background-color: #9C27B0;  /* 紫色 - 同步啟用 */
            color: white;
            border: 1px solid #7B1FA2;
            border-radius: 3px;
            font-size: 8px;
            font-weight: bold;
            text-align: center;
        }
        #DriverLapSyncButton:hover {
            background-color: #AB47BC;  /* 紫色懸停 */
        }
        #DriverLapSyncButton:pressed {
            background-color: #6A1B9A;  /* 紫色按下 */
        }
        #DriverLapSyncButton:!checked {
            background-color: #9E9E9E;  /* 灰色 - 同步停用 */
            border: 1px solid #757575;
        }
        #DriverLapSyncButton:!checked:hover {
            background-color: #BDBDBD;  /* 灰色懸停 */
        }
        
        /* 幫助按鈕 */
        #HelpButton {
            background-color: #F8F8F8;
            color: #4FC3F7;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
            font-size: 9pt;
            font-weight: bold;
        }
        #HelpButton:hover {
            background-color: #E3F2FD;
            color: #039BE5;
        }
        #HelpButton:pressed {
            background-color: #BBDEFB;
        }
        
        /* 設定按鈕 */
        #SettingsButton {
            background-color: #F8F8F8;
            color: #333333;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
            font-size: 8pt;
            font-weight: bold;
        }
        #SettingsButton:hover {
            background-color: #E8E8E8;
        }
        #SettingsButton:pressed {
            background-color: #D8D8D8;
        }
        
        /* 彈出按鈕 */
        #PopoutButton {
            background-color: #F8F8F8;
            color: #333333;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
            font-size: 8pt;
            font-weight: bold;
        }
        #PopoutButton:hover {
            background-color: #E8E8E8;
        }
        #PopoutButton:pressed {
            background-color: #D8D8D8;
        }
        
        /* 子視窗標題 */
        #SubWindowTitle {
            color: #333333;
            font-size: 8pt;
            font-weight: bold;
        }
        
        /* 獨立視窗 */
        #StandaloneWindow {
            background-color: #FFFFFF;
            color: #333333;
        }
        #StandaloneToolbar {
            background-color: #F0F0F0;
            border-bottom: 1px solid #CCCCCC;
            color: #333333;
            font-size: 8pt;
        }
        #StandaloneToolbar QToolButton {
            background: transparent;
            border: 1px solid transparent;
            padding: 2px 6px;
            color: #333333;
            border-radius: 0px;
        }
        #StandaloneToolbar QToolButton:hover {
            background-color: #E8E8E8;
            border: 1px solid #CCCCCC;
        }
        
        /* 遙測圖表 */
        #TelemetryChart {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
        }
        
        /* 賽道地圖 */
        #TrackMap {
            background-color: #FFFFFF;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
        }
        
        /* 專業數據表格 */
        #ProfessionalDataTable {
            background-color: #FFFFFF;
            alternate-background-color: #F8F8F8;
            color: #333333;
            gridline-color: #CCCCCC;
            font-size: 8pt;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
        }
        #ProfessionalDataTable::item {
            padding: 1px;
            border: none;
        }
        #ProfessionalDataTable::item:selected {
            background-color: #0078D4;
            color: #FFFFFF;
        }
        #ProfessionalDataTable QHeaderView::section {
            background-color: #F0F0F0;
            color: #333333;
            padding: 1px;
            border: 1px solid #CCCCCC;
            font-weight: bold;
            font-size: 8pt;
            border-radius: 0px;
        }
        
        /* 狀態列 */
        QStatusBar {
            background-color: #F0F0F0;
            border-top: 1px solid #CCCCCC;
            color: #333333;
            font-size: 8pt;
        }
        #StatusReady {
            color: #00AA00;
            font-weight: bold;
        }
        #VersionInfo {
            color: #0078D4;
            font-weight: bold;
        }
        
        /* 標籤 */
        QLabel {
            color: #333333;
            font-size: 8pt;
        }
        
        /* 滾動條 */
        QScrollBar:vertical {
            background-color: #F0F0F0;
            width: 6px;
            border: 1px solid #CCCCCC;
            border-radius: 0px;
        }
        QScrollBar::handle:vertical {
            background-color: #AAAAAA;
            border-radius: 0px;
            min-height: 10px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #888888;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        
        /* 分割器 */
        QSplitter::handle {
            background-color: #CCCCCC;
        }
        QSplitter::handle:horizontal {
            width: 2px;
        }
        QSplitter::handle:vertical {
            height: 2px;
        }
        
        /* 強制所有容器為白底 */
        QWidget {
            background-color: #FFFFFF;
            color: #333333;
        }
        QFrame {
            background-color: #FFFFFF;
            color: #333333;
        }
        QSplitter {
            background-color: #F5F5F5;
        }
        QSplitter QWidget {
            background-color: #FFFFFF;
        }
        
        /* 強制所有MDI相關元素為白底 */
        QMdiArea QWidget {
            background-color: #FFFFFF;
        }
        QMdiArea QScrollArea QWidget {
            background-color: #FFFFFF;
        }
        QMdiArea > QWidget {
            background-color: #FFFFFF;
        }
        
        /* 左側面板所有子元素強制白底 */
        QTreeWidget QWidget {
            background-color: #FFFFFF;
            color: #333333;
        }
        QTextEdit QWidget {
            background-color: #FFFFFF;
            color: #006600;
        }
        """
        
        #print("[DESIGN] DEBUG: Setting main window QSS styles...")
        #print(f"📄 QSS contains QMdiSubWindow border: {'QMdiSubWindow' in style and 'border:' in style}")
        #print(f"📄 QSS contains CustomTitleBar: {'CustomTitleBar' in style}")
        #print(f"📄 QSS total length: {len(style)} characters")
        # 臨時禁用有問題的樣式表，改用簡化版本
        simple_style = """
        QMainWindow {
            background-color: #FFFFFF;
            color: #333333;
        }
        QWidget {
            background-color: #FFFFFF;
            color: #333333;
        }
        """
        self.main_window.setStyleSheet(simple_style)
        #print("[OK] 簡化版QSS styles applied successfully")
