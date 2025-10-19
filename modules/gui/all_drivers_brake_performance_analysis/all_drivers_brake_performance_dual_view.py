#!/usr/bin/env python3
"""
全車手煞車性能分析 - 雙視圖容器
All Drivers Brake Performance - Dual View Container

整合表格視圖和圖表視圖，使用 QTabWidget 切換

作者: F1T Team
日期: 2025-10-18
版本: 1.0.0
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from PyQt5.QtCore import pyqtSignal
from typing import Dict, Any, Optional

# 導入兩個視圖
from .all_drivers_brake_performance_table_widget import AllDriversBrakePerformanceTableWidget
from .all_drivers_brake_performance_widget import AllDriversBrakePerformanceWidget

# 導入國際化
from core.gui_i18n import tr


class AllDriversBrakePerformanceDualView(QWidget):
    """
    全車手煞車性能分析 - 雙視圖容器
    
    功能：
    - Tab 1: 表格視圖（QTableWidget，詳細數據）
    - Tab 2: 圖表視圖（Matplotlib，視覺化）
    - 兩個視圖共享相同的數據源
    """
    
    # 信號定義
    data_loaded = pyqtSignal(dict)  # 數據載入完成
    
    def __init__(self, parent=None):
        """初始化雙視圖容器"""
        super().__init__(parent)
        
        # 數據屬性
        self.current_data: Optional[Dict] = None
        
        # 初始化 UI
        self._init_ui()
    
    def _init_ui(self):
        """初始化使用者介面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 創建 Tab Widget
        self.tab_widget = QTabWidget()
        
        # ===== Tab 1: 表格視圖（立即創建）=====
        self.table_view = AllDriversBrakePerformanceTableWidget()
        self.tab_widget.addTab(
            self.table_view,
            tr('brake_performance_tab_table', '表格視圖')
        )
        
        # ===== Tab 2: 圖表視圖（延遲載入，避免 Matplotlib 初始化阻塞）=====
        self.chart_view = None  # 延遲創建
        self.chart_view_placeholder = QWidget()  # 佔位符
        self.tab_widget.addTab(
            self.chart_view_placeholder,
            tr('brake_performance_tab_chart', '圖表視圖')
        )
        
        # 添加到佈局
        layout.addWidget(self.tab_widget)
        
        # 連接信號
        self._connect_signals()
    
    def _connect_signals(self):
        """連接信號"""
        # Tab 切換事件
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
    
    def update_data(self, data: Dict[str, Any]):
        """
        更新數據到兩個視圖
        
        Args:
            data: 包含 driver_brakes 的字典
        """
        try:
            print(f"[BRAKE_DUAL_VIEW] 接收數據，準備更新視圖")
            
            # 儲存數據
            self.current_data = data
            
            # 更新表格視圖（總是立即更新）
            self.table_view.update_data(data)
            
            # 更新圖表視圖（只在已創建時更新）
            if self.chart_view is not None:
                self.chart_view.update_data(data)
                print("[BRAKE_DUAL_VIEW] 圖表視圖已更新")
            else:
                print("[BRAKE_DUAL_VIEW] 圖表視圖尚未創建，將在切換時延遲載入")
            
            # 發射信號
            self.data_loaded.emit(data)
            
            print(f"[BRAKE_DUAL_VIEW] 視圖更新完成")
            
        except Exception as e:
            print(f"[ERROR] [BRAKE_DUAL_VIEW] 更新數據失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_tab_changed(self, index: int):
        """
        Tab 切換事件處理
        
        當切換到圖表 tab 時，延遲創建 Matplotlib widget 並載入數據
        """
        if index == 0:
            print("[BRAKE_DUAL_VIEW] 切換到表格視圖")
        elif index == 1:
            print("[BRAKE_DUAL_VIEW] 切換到圖表視圖")
            
            # 延遲載入：第一次切換時才創建 Matplotlib widget
            if self.chart_view is None:
                print("[BRAKE_DUAL_VIEW] 首次切換，創建 Matplotlib widget...")
                self.chart_view = AllDriversBrakePerformanceWidget()
                
                # 替換佔位符
                self.tab_widget.removeTab(1)
                self.tab_widget.insertTab(
                    1,
                    self.chart_view,
                    tr('brake_performance_tab_chart', '圖表視圖')
                )
                self.tab_widget.setCurrentIndex(1)  # 確保顯示正確的 tab
                
                print("[BRAKE_DUAL_VIEW] Matplotlib widget 創建完成")
            
            # 確保圖表視圖有數據
            if self.current_data:
                if not hasattr(self.chart_view, 'current_data') or self.chart_view.current_data is None:
                    self.chart_view.update_data(self.current_data)
    
    def get_current_view(self) -> str:
        """
        獲取當前視圖類型
        
        Returns:
            str: "table" 或 "chart"
        """
        current_index = self.tab_widget.currentIndex()
        return "table" if current_index == 0 else "chart"
    
    def switch_to_table_view(self):
        """切換到表格視圖"""
        self.tab_widget.setCurrentIndex(0)
    
    def switch_to_chart_view(self):
        """切換到圖表視圖"""
        self.tab_widget.setCurrentIndex(1)
    
    def export_current_view(self, file_path: str) -> bool:
        """
        匯出當前視圖
        
        Args:
            file_path: 匯出檔案路徑
            
        Returns:
            bool: 匯出是否成功
        """
        try:
            current_index = self.tab_widget.currentIndex()
            
            if current_index == 0:
                # 表格視圖匯出
                return self.table_view.export_chart(file_path)
            else:
                # 圖表視圖匯出
                return self.chart_view.export_chart(file_path)
                
        except Exception as e:
            print(f"[ERROR] [BRAKE_DUAL_VIEW] 匯出失敗: {e}")
            return False


__all__ = ["AllDriversBrakePerformanceDualView"]
