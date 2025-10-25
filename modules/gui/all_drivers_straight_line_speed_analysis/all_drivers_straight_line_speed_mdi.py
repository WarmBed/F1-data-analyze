#!/usr/bin/env python3
"""
全車手直線速度與加速性能 MDI 視窗
All Drivers Straight Line Speed MDI

負責管理 MDI 視窗，整合資料載入器和圖表元件

作者: F1T Team
日期: 2025-10-14
版本: 1.0.0
"""

import sys
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QPushButton, QMessageBox, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSlot

# 導入基類
try:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
except ImportError:
    from ...base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig

# 導入資料載入器
try:
    from modules.gui.lap_analysis.speed_analysis.straight_line_speed_loader import (
        StraightLineSpeedDataLoader
    )
except ImportError:
    from ..lap_analysis.speed_analysis.straight_line_speed_loader import (
        StraightLineSpeedDataLoader
    )

# ✅ 導入表格元件（只使用表格視圖）
try:
    from .all_drivers_straight_line_speed_table_widget import AllDriversStraightLineSpeedTableWidget
except ImportError:
    from modules.gui.all_drivers_straight_line_speed_analysis.all_drivers_straight_line_speed_table_widget import (
        AllDriversStraightLineSpeedTableWidget
    )

# 導入國際化
from core.gui_i18n import tr


class AllDriversStraightLineSpeedMDI(UniversalAnalysisMDI):
    """
    全車手直線速度與加速性能 MDI 視窗
    
    繼承自 UniversalAnalysisMDI，提供統一的視窗管理和數據流控制
    整合 StraightLineSpeedDataLoader 和 AllDriversStraightLineSpeedWidget
    """
    
    # 模組類型註冊標記
    _REGISTERED = False
    
    @classmethod
    def ensure_registered(cls):
        """確保模組類型已註冊"""
        if not cls._REGISTERED:
            config = AnalysisMDIConfig(
                analysis_type="all_drivers_straight_line_speed",
                display_name="All Drivers Straight Line Speed",
                default_size=(1200, 900),
                requires_driver_params=False,
                requires_lap_params=False,
                supports_single_driver=False,
                supports_dual_driver=False
            )
            UniversalAnalysisMDI.register_mdi_module_type("all_drivers_straight_line_speed", config)
            cls._REGISTERED = True
            print("[SPEED_MDI] ✅ 模組類型已註冊")
    
    def __init__(self, parent=None):
        """
        初始化 MDI 視窗
        
        Args:
            parent: 父元件
        """
        print("[SPEED_MDI] AllDriversStraightLineSpeedMDI 開始初始化...")
        
        # 確保類型已註冊
        self.ensure_registered()
        
        # 調用基類初始化
        super().__init__(analysis_type="all_drivers_straight_line_speed", parent=parent)
        
        # 初始化參數（將在 initialize_module 中設置）
        self.year = None
        self.race = None
        self.session = None
        
        # 狀態變數
        self._current_data = None
        self._is_data_loaded = False
        
        # 統計面板組件
        self.stats_panel: Optional[QGroupBox] = None
        self.lbl_fastest_driver: Optional[QLabel] = None
        self.lbl_fastest_speed: Optional[QLabel] = None
        self.lbl_fastest_accel: Optional[QLabel] = None
        self.lbl_avg_speed: Optional[QLabel] = None
        self.lbl_avg_accel: Optional[QLabel] = None
        
        print("[SPEED_MDI] 基類初始化完成，等待參數設置...")
    
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """
        初始化模組（設置參數並載入初始數據）
        
        Args:
            parent_widget: 父級 widget（可選）
            **kwargs: 額外參數
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            print("[SPEED_MDI] 開始初始化模組...")
            
            # 驗證必要屬性
            if not hasattr(self, 'current_year') or not self.current_year:
                print("[SPEED_MDI] ❌ 缺少 current_year 屬性")
                return False
                
            if not hasattr(self, 'current_race') or not self.current_race:
                print("[SPEED_MDI] ❌ 缺少 current_race 屬性")
                return False
                
            if not hasattr(self, 'current_session') or not self.current_session:
                print("[SPEED_MDI] ❌ 缺少 current_session 屬性")
                return False
            
            # 設置參數
            self.year = str(self.current_year)
            self.race = self.current_race
            self.session = self.current_session
            
            print(f"[SPEED_MDI] ✅ 參數已設置: {self.year} {self.race} {self.session}")
            
            # 調用基類的 initialize_module
            if not super().initialize_module(parent_widget=parent_widget, **kwargs):
                print("[SPEED_MDI] ❌ 基類初始化失敗")
                return False
            
            # 驗證組件已創建
            if not self.chart_widget:
                print("[SPEED_MDI] ❌ chart_widget 未創建")
                return False
            
            if not self.data_manager:
                print("[SPEED_MDI] ❌ data_manager 未創建")
                return False
            
            print(f"[SPEED_MDI] ✅ 組件創建成功")
            
            # 自動載入初始數據
            print("[SPEED_MDI] 🚀 準備載入初始數據...")
            self.load_initial_data()
            
            return True
            
        except Exception as e:
            print(f"❌ [SPEED_MDI] 初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # ========== 基類抽象方法實作 ==========
    
    def create_data_manager(self):
        """
        創建資料管理器（資料載入器）
        
        Returns:
            StraightLineSpeedDataLoader: 資料載入器實例
        """
        print("[SPEED_MDI] 創建資料管理器...")
        
        # ✅ 複用現有的 StraightLineSpeedDataLoader
        loader = StraightLineSpeedDataLoader(parent=self)
        
        # 連接信號
        loader.data_loaded.connect(self._on_data_loaded)
        loader.load_error.connect(self._on_load_error)
        loader.status_changed.connect(self._on_status_changed)
        
        print("✅ [SPEED_MDI] 資料管理器已創建")
        return loader
    
    def create_chart_widget(self):
        """
        創建表格元件（QTableWidget 版本）
        
        ✅ 替換 Matplotlib Widget 為 QTableWidget
        ✅ 只使用表格視圖（取消圖表視圖）
        
        Returns:
            AllDriversStraightLineSpeedTableWidget: 表格元件實例
        """
        print("[SPEED_MDI] 創建表格元件（QTableWidget 版本）...")
        
        widget = AllDriversStraightLineSpeedTableWidget(parent=None)
        
        # ✅ 表格視圖包含完整的數據展示和棒狀圖視覺化
        
        print("✅ [SPEED_MDI] 表格元件已創建")
        return widget
    
    def create_additional_widgets(self) -> list:
        """
        創建額外的 Widget 組件
        
        ✅ 取消統計面板 - 直接返回空列表
        
        Returns:
            list: 額外的 Widget 列表（空）
        """
        print("[SPEED_MDI] ⚠️ 統計面板已取消")
        
        # ✅ 不創建統計面板，返回空列表
        return []
    
    def _create_stats_panel(self) -> QGroupBox:
        """創建統計面板"""
        panel = QGroupBox(tr("straight_speed_statistics_panel", "統計資訊"))
        layout = QHBoxLayout()
        
        # 最快車手
        fastest_layout = QVBoxLayout()
        fastest_layout.addWidget(QLabel(tr("straight_speed_fastest_driver", "最快車手")))
        self.lbl_fastest_driver = QLabel("--")
        self.lbl_fastest_driver.setStyleSheet("font-size: 14pt; font-weight: bold; color: #00FF00;")
        fastest_layout.addWidget(self.lbl_fastest_driver)
        
        # 最高速度
        speed_layout = QVBoxLayout()
        speed_layout.addWidget(QLabel(tr("straight_speed_fastest_speed", "最高速度")))
        self.lbl_fastest_speed = QLabel("--")
        self.lbl_fastest_speed.setStyleSheet("font-size: 14pt; font-weight: bold;")
        speed_layout.addWidget(self.lbl_fastest_speed)
        
        # 最快加速
        accel_layout = QVBoxLayout()
        accel_layout.addWidget(QLabel(tr("straight_speed_fastest_acceleration", "最快加速")))
        self.lbl_fastest_accel = QLabel("--")
        self.lbl_fastest_accel.setStyleSheet("font-size: 14pt; font-weight: bold;")
        accel_layout.addWidget(self.lbl_fastest_accel)
        
        # 平均速度
        avg_speed_layout = QVBoxLayout()
        avg_speed_layout.addWidget(QLabel(tr("straight_speed_average_speed", "平均速度")))
        self.lbl_avg_speed = QLabel("--")
        self.lbl_avg_speed.setStyleSheet("font-size: 12pt;")
        avg_speed_layout.addWidget(self.lbl_avg_speed)
        
        # 平均加速
        avg_accel_layout = QVBoxLayout()
        avg_accel_layout.addWidget(QLabel(tr("straight_speed_average_acceleration", "平均加速")))
        self.lbl_avg_accel = QLabel("--")
        self.lbl_avg_accel.setStyleSheet("font-size: 12pt;")
        avg_accel_layout.addWidget(self.lbl_avg_accel)
        
        # 添加到主佈局
        layout.addLayout(fastest_layout)
        layout.addLayout(speed_layout)
        layout.addLayout(accel_layout)
        layout.addLayout(avg_speed_layout)
        layout.addLayout(avg_accel_layout)
        layout.addStretch()
        
        panel.setLayout(layout)
        return panel
    
    # ========== 數據處理回調 ==========
    
    @pyqtSlot(dict)
    def _on_data_loaded(self, data: Dict[str, Any]):
        """
        數據載入完成回調
        
        Args:
            data: 載入的資料
        """
        try:
            print("[SPEED_MDI] 收到資料載入完成信號")
            
            if not data:
                self._on_load_error("資料為空")
                return
            
            self._current_data = data
            self._is_data_loaded = True
            
            # ✅ 統計面板已取消，不再更新
            # self._update_stats_panel(data)  # 已移除
            
            # 更新圖表
            if self.chart_widget:
                self.chart_widget.update_data(data)
            
            print("✅ [SPEED_MDI] 資料處理完成")
            
        except Exception as e:
            print(f"❌ [SPEED_MDI] 資料處理失敗: {e}")
            import traceback
            traceback.print_exc()
            self._on_load_error(f"資料處理錯誤: {str(e)}")
    
    @pyqtSlot(str)
    def _on_load_error(self, error_msg: str):
        """
        資料載入錯誤回調
        
        Args:
            error_msg: 錯誤訊息
        """
        print(f"❌ [SPEED_MDI] 資料載入錯誤: {error_msg}")
        QMessageBox.critical(None, tr("load_error", "載入錯誤"), error_msg)
    
    @pyqtSlot(str)
    def _on_status_changed(self, status: str):
        """狀態變更回調"""
        print(f"[SPEED_MDI] 狀態: {status}")
    
    def _update_stats_panel(self, data: Dict[str, Any]):
        """更新統計面板"""
        try:
            summary = data.get("summary", {})
            accel_perf = summary.get("acceleration_performance", {})
            
            # 最快車手
            fastest_driver = summary.get("fastest_driver", "--")
            self.lbl_fastest_driver.setText(fastest_driver)
            
            # 最高速度
            fastest_speed = summary.get("fastest_speed_kmh", 0)
            self.lbl_fastest_speed.setText(f"{fastest_speed:.0f} km/h")
            
            # 最快加速
            fastest_accel = accel_perf.get("fastest_acceleration_time", 0)
            self.lbl_fastest_accel.setText(f"{fastest_accel:.2f}s")
            
            # 平均速度
            avg_speed = summary.get("average_speed_kmh", 0)
            self.lbl_avg_speed.setText(f"{avg_speed:.1f} km/h")
            
            # 平均加速
            avg_accel = accel_perf.get("average_acceleration_time", 0)
            self.lbl_avg_accel.setText(f"{avg_accel:.2f}s")
            
            print("[SPEED_MDI] 統計面板已更新")
            
        except Exception as e:
            print(f"[ERROR] [SPEED_MDI] 更新統計面板失敗: {e}")
    
    def load_initial_data(self):
        """載入初始數據"""
        try:
            print("[SPEED_MDI] 開始載入初始數據...")
            
            if not self.data_manager:
                print("[SPEED_MDI] ❌ data_manager 不存在")
                return
            
            # 呼叫資料載入器
            success = self.data_manager.load_data(
                year=self.year,
                race=self.race,
                session=self.session
            )
            
            if not success:
                print("[SPEED_MDI] ❌ 資料載入失敗")
                
        except Exception as e:
            print(f"❌ [SPEED_MDI] 載入初始數據失敗: {e}")
            import traceback
            traceback.print_exc()
    
    # ========== 覆寫基類方法 ==========
    
    def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
        """
        生成視窗標題（覆寫基類方法）- 只顯示模組名稱
        
        Args:
            year: 年份（忽略）
            race: 賽事（忽略）
            session: 場次（忽略）
            
        Returns:
            str: 模組名稱標題
        """
        from core.gui_i18n import tr
        module_name = tr('all_drivers_straight_speed', 'All Drivers Speed & Acceleration')
        return module_name
    
    # ========== 事件處理 ==========
    
    @pyqtSlot(str)
    def _on_driver_clicked(self, driver_code: str):
        """車手點擊事件"""
        print(f"[SPEED_MDI] 車手被點擊: {driver_code}")
    
    @pyqtSlot(str)
    def _on_chart_switched(self, chart_type: str):
        """圖表切換事件"""
        print(f"[SPEED_MDI] 圖表切換至: {chart_type}")


__all__ = ["AllDriversStraightLineSpeedMDI"]
