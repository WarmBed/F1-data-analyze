#!/usr/bin/env python3
"""
UniversalAnalysisMDI - F1T 通用分析 MDI 模組基類
===============================================

這個模組提供了所有 F1T 分析 MDI 模組共用的架構和邏輯，
大幅簡化各種分析模組的實現代碼。

支援的分析類型：
- telemetry: 遙測分析（速度、RPM、檔位、油門、煞車等）
- rain: 降雨分析
- accident: 事故分析  
- pitstop: 進站分析
- driver: 車手分析
- track: 賽道分析

設計原則：
1. 統一的MDI架構，消除代碼重複
2. 實現 IAnalysisModule 標準介面
3. 模組化設計，支援快速新增分析類型
4. 統一的錯誤處理和參數管理
5. 標準化的視窗管理和信號處理
6. 與分析模組管理器的無縫整合

Author: F1T Team
Date: 2025-09-09
Version: 1.0.0
"""

import sys
import os
from typing import Dict, List, Any, Optional, Tuple, Type
from abc import ABC, abstractmethod
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSplitter, 
    QFrame, QGroupBox, QGridLayout, QPushButton, QStatusBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor

# 導入介面和基類
try:
    from ..interfaces.analysis_module import IAnalysisModule
except ImportError:
    from modules.gui.interfaces.analysis_module import IAnalysisModule

try:
    from .universal_data_loader_base import UniversalDataLoader, AnalysisConfig
except ImportError:
    from modules.gui.base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig


class AnalysisMDIConfig:
    """分析 MDI 模組配置類"""
    
    def __init__(self, analysis_type: str, display_name: str, 
                 default_size: Tuple[int, int] = (1200, 800),
                 requires_driver_params: bool = True,
                 requires_lap_params: bool = True,
                 supports_single_driver: bool = True,
                 supports_dual_driver: bool = True,
                 **kwargs):
        """
        初始化 MDI 模組配置
        
        Args:
            analysis_type: 分析類型
            display_name: 顯示名稱
            default_size: 預設視窗大小
            requires_driver_params: 是否需要車手參數
            requires_lap_params: 是否需要圈數參數
            supports_single_driver: 是否支援單車手分析
            supports_dual_driver: 是否支援雙車手對比
            **kwargs: 額外配置參數
        """
        self.analysis_type = analysis_type
        self.display_name = display_name
        self.default_size = default_size
        self.requires_driver_params = requires_driver_params
        self.requires_lap_params = requires_lap_params
        self.supports_single_driver = supports_single_driver
        self.supports_dual_driver = supports_dual_driver
        
        # 儲存額外配置
        for key, value in kwargs.items():
            setattr(self, key, value)


class UniversalAnalysisMDI(IAnalysisModule):
    """
    通用分析 MDI 模組基類
    
    提供所有分析模組共用的 MDI 架構和邏輯，
    子類只需實現特定的數據管理器和圖表組件。
    """
    
    # 標準信號定義
    module_error = pyqtSignal(str)
    parameters_updated = pyqtSignal(dict)
    data_loaded = pyqtSignal(dict)
    analysis_completed = pyqtSignal(dict)
    
    # 支援的 MDI 模組類型註冊表
    MDI_MODULE_TYPES = {}
    
    @classmethod
    def register_mdi_module_type(cls, module_type: str, config: AnalysisMDIConfig):
        """註冊新的 MDI 模組類型"""
        cls.MDI_MODULE_TYPES[module_type] = config
    
    def __init__(self, analysis_type: str, parent=None):
        """
        初始化通用分析 MDI 模組
        
        Args:
            analysis_type: 分析類型
            parent: 父級 QObject
        """
        super().__init__(parent)
        
        # 驗證分析類型
        if analysis_type not in self.MDI_MODULE_TYPES:
            raise ValueError(f"不支援的分析類型: {analysis_type}. 可用類型: {list(self.MDI_MODULE_TYPES.keys())}")
            
        self.analysis_type = analysis_type
        self.config = self.MDI_MODULE_TYPES[analysis_type]
        
        # 基本參數狀態
        self.current_year = "2025"
        self.current_race = "Japan"
        self.current_session = "R"
        self.parameter_provider = None
        
        # 車手和圈數參數（如果需要）
        if self.config.requires_driver_params:
            self.driver1 = "VER"
            self.driver2 = "VER"
            
        if self.config.requires_lap_params:
            self.lap1 = 1
            self.lap2 = 1
        
        # 核心組件 - 延遲初始化
        self.data_manager = None
        self.chart_widget = None
        self.main_widget = None
        self.status_bar = None
        
        # MDI 相關
        self.parent_window = None
        self._analysis_manager = None
        self._module_id = None
        
        # 狀態
        self._initialized = False
        self._debug_prefix = f"{analysis_type.upper()}_MDI"
        
        self._debug(f"初始化 {self.config.display_name} MDI 模組")
    
    def _debug(self, message: str):
        """統一的除錯輸出"""
        print(f"[{self._debug_prefix}] {message}")
    
    def _error(self, message: str):
        """統一的錯誤輸出"""
        print(f"[ERROR] [{self._debug_prefix}] {message}")
    
    # ========== IAnalysisModule 介面實現 ==========
    
    @property
    def module_name(self) -> str:
        """返回模組名稱"""
        return f"{self.analysis_type}_analysis"
    
    @property
    def display_name(self) -> str:
        """返回顯示名稱"""
        return self.config.display_name
    
    @property
    def version(self) -> str:
        """返回模組版本"""
        return "1.0.0"
    
    @property
    def description(self) -> str:
        """返回模組描述"""
        return f"F1T {self.config.display_name}模組 - 基於通用MDI架構"
    
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """初始化模組 - 通用初始化邏輯"""
        try:
            self._debug(f"初始化 {self.config.display_name} 模組")
            
            # 創建數據管理器
            self.data_manager = self.create_data_manager()
            if not self.data_manager:
                self._error("數據管理器創建失敗")
                return False
            
            # 連接數據管理器信號
            self._connect_data_manager_signals()
            
            # 創建圖表組件
            self.chart_widget = self.create_chart_widget()
            if not self.chart_widget:
                self._error("圖表組件創建失敗")
                return False
            
            # 連接圖表組件信號
            self._connect_chart_widget_signals()
            
            # 設置初始參數（如果需要）
            self._setup_initial_parameters()
            
            # 設置主界面
            self._setup_ui()
            
            # 註冊到分析模組管理器
            self._register_to_analysis_manager()
            
            self._initialized = True
            self._debug(f"✅ {self.config.display_name} 模組初始化完成")
            return True
            
        except Exception as e:
            self._error(f"模組初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_widget(self) -> QWidget:
        """返回模組的主要 Widget"""
        return self.main_widget
    
    def update_parameters(self, year: int = None, race: str = None, session: str = None, **kwargs) -> bool:
        """更新參數 - 通用參數更新邏輯"""
        try:
            self._debug(f"========== 更新參數 ==========")
            
            # 更新基本參數
            if year is not None:
                self.current_year = str(year)
            if race is not None:
                self.current_race = race
            if session is not None:
                self.current_session = session
            
            # 更新車手參數（如果支援）
            if self.config.requires_driver_params:
                if 'driver1' in kwargs:
                    self.driver1 = kwargs['driver1']
                if 'driver2' in kwargs:
                    self.driver2 = kwargs['driver2']
            
            # 更新圈數參數（如果支援）
            if self.config.requires_lap_params:
                if 'lap1' in kwargs:
                    self.lap1 = kwargs['lap1']
                if 'lap2' in kwargs:
                    self.lap2 = kwargs['lap2']
            
            self._debug(f"參數: {self.current_year} {self.current_race} {self.current_session}")
            
            if self.config.requires_driver_params:
                self._debug(f"車手: {getattr(self, 'driver1', 'N/A')} vs {getattr(self, 'driver2', 'N/A')}")
            
            if self.config.requires_lap_params:
                self._debug(f"圈數: {getattr(self, 'lap1', 'N/A')} vs {getattr(self, 'lap2', 'N/A')}")
            
            # 發送參數更新信號
            params = {
                'year': self.current_year,
                'race': self.current_race,
                'session': self.current_session
            }
            
            if self.config.requires_driver_params:
                params.update({
                    'driver1': getattr(self, 'driver1', 'VER'),
                    'driver2': getattr(self, 'driver2', 'VER')
                })
            
            if self.config.requires_lap_params:
                params.update({
                    'lap1': getattr(self, 'lap1', 1),
                    'lap2': getattr(self, 'lap2', 1)
                })
            
            self.parameters_updated.emit(params)
            
            # 更新視窗標題
            self.update_window_title()
            
            # 觸發數據載入
            self._load_data_with_current_parameters()
            
            return True
            
        except Exception as e:
            self._error(f"參數更新失敗: {e}")
            self.module_error.emit(f"參數更新失敗: {str(e)}")
            return False
    
    def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
        """獲取視窗標題"""
        year = year or self.current_year
        race = race or self.current_race
        session = session or self.current_session
        
        base_title = f"{self.config.display_name} - {year} {race} {session}"
        
        if self.config.requires_driver_params:
            driver1 = getattr(self, 'driver1', 'VER')
            driver2 = getattr(self, 'driver2', 'VER')
            
            if driver1 == driver2:
                base_title += f" - {driver1}"
            else:
                base_title += f" - {driver1} vs {driver2}"
        
        return base_title
    
    def get_default_size(self) -> Tuple[int, int]:
        """獲取預設視窗大小"""
        return self.config.default_size
    
    def load_data(self, **kwargs) -> bool:
        """載入分析數據 - 實現 IAnalysisModule 抽象方法"""
        try:
            self._debug("🔄 載入數據（從 IAnalysisModule）")
            
            # 更新參數（如果提供）
            if 'year' in kwargs or 'race' in kwargs or 'session' in kwargs:
                self.update_parameters(
                    kwargs.get('year', int(self.current_year)),
                    kwargs.get('race', self.current_race),
                    kwargs.get('session', self.current_session),
                    **{k: v for k, v in kwargs.items() if k not in ['year', 'race', 'session']}
                )
            else:
                # 使用當前參數載入
                self._load_data_with_current_parameters()
            
            return True
            
        except Exception as e:
            self._error(f"載入數據失敗: {e}")
            self.module_error.emit(f"載入數據失敗: {str(e)}")
            return False
    
    def refresh_analysis(self) -> None:
        """重新執行分析 - 實現 IAnalysisModule 抽象方法"""
        self._debug("🔄 重新執行分析")
        self._load_data_with_current_parameters()
    
    def clear_data(self) -> None:
        """清除所有數據 - 實現 IAnalysisModule 抽象方法"""
        try:
            self._debug("🗑️  清除所有數據")
            
            # 清除圖表數據
            if self.chart_widget and hasattr(self.chart_widget, 'clear_data'):
                self.chart_widget.clear_data()
            elif self.chart_widget and hasattr(self.chart_widget, 'clear'):
                self.chart_widget.clear()
            
            # 清除數據管理器數據
            if self.data_manager and hasattr(self.data_manager, 'clear_data'):
                self.data_manager.clear_data()
            
            # 更新狀態
            self._update_status("數據已清除")
            
        except Exception as e:
            self._error(f"清除數據失敗: {e}")
    
    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        """匯出分析數據 - 實現 IAnalysisModule 抽象方法"""
        try:
            self._debug(f"💾 匯出數據到: {export_path} (格式: {export_format})")
            
            # 獲取當前數據
            current_data = self.get_current_data()
            if not current_data:
                self._error("沒有數據可匯出")
                return False
            
            # 根據格式匯出
            if export_format.lower() == 'json':
                import json
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(current_data, f, ensure_ascii=False, indent=2)
                    
            elif export_format.lower() == 'csv':
                import pandas as pd
                # 嘗試將數據轉換為 DataFrame 並匯出
                if isinstance(current_data, dict):
                    df = pd.DataFrame(current_data)
                    df.to_csv(export_path, encoding='utf-8', index=False)
                else:
                    self._error("數據格式不支援 CSV 匯出")
                    return False
                    
            elif export_format.lower() == 'png':
                # 匯出圖表為圖片
                if self.chart_widget and hasattr(self.chart_widget, 'save_plot'):
                    return self.chart_widget.save_plot(export_path)
                else:
                    self._error("圖表組件不支援圖片匯出")
                    return False
            else:
                self._error(f"不支援的匯出格式: {export_format}")
                return False
            
            self._debug(f"✅ 數據匯出成功: {export_path}")
            return True
            
        except Exception as e:
            self._error(f"匯出數據失敗: {e}")
            return False
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """獲取當前分析數據 - 實現 IAnalysisModule 抽象方法"""
        try:
            # 首先嘗試從數據管理器獲取
            if self.data_manager and hasattr(self.data_manager, 'get_current_data'):
                return self.data_manager.get_current_data()
            
            # 如果數據管理器沒有此方法，嘗試從圖表組件獲取
            if self.chart_widget and hasattr(self.chart_widget, 'get_current_data'):
                return self.chart_widget.get_current_data()
            
            # 最後嘗試返回模組級別的數據（如果有的話）
            return getattr(self, '_current_data', None)
            
        except Exception as e:
            self._error(f"獲取當前數據失敗: {e}")
            return None
    
    # ========== 抽象方法 - 子類必須實現 ==========
    
    @abstractmethod
    def create_data_manager(self):
        """
        創建數據管理器
        
        Returns:
            數據管理器實例，必須有 data_loaded 和 error_occurred 信號
        """
        pass
    
    @abstractmethod
    def create_chart_widget(self):
        """
        創建圖表組件
        
        Returns:
            圖表組件實例
        """
        pass
    
    # ========== 可選的擴展方法 ==========
    
    def create_additional_widgets(self) -> List[QWidget]:
        """
        創建額外的 Widget 組件（可選）
        
        Returns:
            List[QWidget]: 額外的 Widget 列表
        """
        return []
    
    def get_status_info(self) -> str:
        """
        獲取狀態信息（可選）
        
        Returns:
            str: 狀態信息字符串
        """
        return f"{self.config.display_name} - 就緒"
    
    # ========== 通用內部方法 ==========
    
    def _connect_data_manager_signals(self):
        """連接數據管理器信號"""
        if hasattr(self.data_manager, 'data_loaded'):
            self.data_manager.data_loaded.connect(self._update_chart)
        if hasattr(self.data_manager, 'error_occurred'):
            self.data_manager.error_occurred.connect(self._handle_error)
        if hasattr(self.data_manager, 'loading_progress'):
            self.data_manager.loading_progress.connect(self._update_progress)
        if hasattr(self.data_manager, 'status_changed'):
            self.data_manager.status_changed.connect(self._update_status)
    
    def _connect_chart_widget_signals(self):
        """連接圖表組件信號"""
        # 如果圖表組件支援圈數變更
        if hasattr(self.chart_widget, 'lap_numbers_changed'):
            self.chart_widget.lap_numbers_changed.connect(self._on_lap_numbers_changed)
        
        # 如果圖表組件支援車手變更
        if hasattr(self.chart_widget, 'drivers_changed'):
            self.chart_widget.drivers_changed.connect(self._on_drivers_changed)
    
    def _setup_initial_parameters(self):
        """設置初始參數"""
        if self.config.requires_lap_params and hasattr(self.chart_widget, 'set_lap_numbers'):
            self.chart_widget.set_lap_numbers(
                getattr(self, 'lap1', 1), 
                getattr(self, 'lap2', 1)
            )
        
        if self.config.requires_driver_params and hasattr(self.chart_widget, 'set_drivers'):
            self.chart_widget.set_drivers(
                getattr(self, 'driver1', 'VER'),
                getattr(self, 'driver2', 'VER')
            )
    
    def _setup_ui(self):
        """設置主界面 - 通用UI架構"""
        self.main_widget = QWidget()
        layout = QVBoxLayout(self.main_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # 主要內容區域
        main_splitter = QSplitter(Qt.Vertical)
        
        # 圖表區域
        if self.chart_widget:
            chart_frame = QFrame()
            chart_frame.setFrameStyle(QFrame.StyledPanel)
            chart_layout = QVBoxLayout(chart_frame)
            chart_layout.setContentsMargins(5, 5, 5, 5)
            chart_layout.addWidget(self.chart_widget)
            main_splitter.addWidget(chart_frame)
        
        # 額外組件區域
        additional_widgets = self.create_additional_widgets()
        for widget in additional_widgets:
            main_splitter.addWidget(widget)
        
        layout.addWidget(main_splitter)
        
        # 狀態列
        self.status_bar = QStatusBar()
        self.status_bar.showMessage(self.get_status_info())
        layout.addWidget(self.status_bar)
        
        # 設置預設比例（圖表佔大部分空間）
        if main_splitter.count() > 1:
            sizes = [800] + [200] * (main_splitter.count() - 1)
            main_splitter.setSizes(sizes)
    
    def _register_to_analysis_manager(self):
        """註冊到分析模組管理器"""
        try:
            from ..lap_analysis.analysis_module_manager import get_analysis_module_manager
            manager = get_analysis_module_manager()
            
            # 註冊模組
            self._module_id = f"{self.analysis_type}_analysis_{id(self)}"
            manager.register_module(self._module_id, self, self.analysis_type)
            
            # 註冊圖表組件
            if self.chart_widget:
                manager.register_chart_widget(self.chart_widget)
            
            self._analysis_manager = manager
            self._debug(f"✅ 已註冊到分析模組管理器: {self._module_id}")
            
        except (ImportError, Exception) as e:
            self._debug(f"⚠️  無法註冊到分析模組管理器: {e}")
            self._analysis_manager = None
            self._module_id = None
    
    def _load_data_with_current_parameters(self):
        """使用當前參數載入數據"""
        if not self.data_manager:
            return
        
        try:
            # 構建載入參數
            load_params = {
                'year': int(self.current_year),
                'race': self.current_race,
                'session': self.current_session
            }
            
            if self.config.requires_driver_params:
                load_params.update({
                    'driver1': getattr(self, 'driver1', 'VER'),
                    'driver2': getattr(self, 'driver2', 'VER')
                })
            
            if self.config.requires_lap_params:
                load_params.update({
                    'lap1': getattr(self, 'lap1', 1),
                    'lap2': getattr(self, 'lap2', 1)
                })
            
            # 呼叫數據管理器的載入方法
            if hasattr(self.data_manager, 'load_data'):
                self.data_manager.load_data(**load_params)
            elif hasattr(self.data_manager, f'load_{self.analysis_type}_data'):
                load_method = getattr(self.data_manager, f'load_{self.analysis_type}_data')
                load_method(**load_params)
            else:
                self._debug("⚠️  數據管理器沒有合適的載入方法")
            
        except Exception as e:
            self._error(f"數據載入失敗: {e}")
            self.module_error.emit(f"數據載入失敗: {str(e)}")
    
    # ========== 信號處理方法 ==========
    
    def _update_chart(self, data: dict):
        """更新圖表數據"""
        try:
            self._debug("📊 更新圖表數據")
            
            if hasattr(self.chart_widget, 'update_data'):
                self.chart_widget.update_data(data)
            elif hasattr(self.chart_widget, 'set_data'):
                self.chart_widget.set_data(data)
            else:
                self._debug("⚠️  圖表組件沒有數據更新方法")
            
            # 發送數據載入完成信號
            self.data_loaded.emit(data)
            
            # 更新狀態
            self._update_status("數據載入完成")
            
        except Exception as e:
            self._error(f"圖表更新失敗: {e}")
            self.module_error.emit(f"圖表更新失敗: {str(e)}")
    
    def _handle_error(self, error_message: str):
        """處理錯誤"""
        self._error(f"數據載入錯誤: {error_message}")
        self.module_error.emit(error_message)
        self._update_status(f"錯誤: {error_message}")
    
    def _update_progress(self, progress: int):
        """更新進度"""
        if self.status_bar:
            self.status_bar.showMessage(f"載入中... {progress}%")
    
    def _update_status(self, message: str):
        """更新狀態"""
        if self.status_bar:
            self.status_bar.showMessage(message)
    
    def _on_lap_numbers_changed(self, lap1: int, lap2: int):
        """處理圈數變更"""
        if self.config.requires_lap_params:
            self.lap1 = lap1
            self.lap2 = lap2
            self._debug(f"圈數更新: {lap1} vs {lap2}")
            self._load_data_with_current_parameters()
    
    def _on_drivers_changed(self, driver1: str, driver2: str):
        """處理車手變更"""
        if self.config.requires_driver_params:
            self.driver1 = driver1
            self.driver2 = driver2
            self._debug(f"車手更新: {driver1} vs {driver2}")
            self._load_data_with_current_parameters()
    
    # ========== MDI 視窗管理 ==========
    
    def set_parent_window(self, parent_window):
        """設置父視窗引用（MDI 子視窗）"""
        self.parent_window = parent_window
        if parent_window:
            self.update_window_title()
    
    def update_window_title(self):
        """更新視窗標題"""
        if self.parent_window:
            title = self.get_window_title()
            self.parent_window.setWindowTitle(title)
    
    def cleanup(self):
        """清理資源"""
        try:
            # 從分析模組管理器取消註冊
            if self._analysis_manager and self._module_id:
                self._analysis_manager.unregister_module(self._module_id)
            
            # 停止數據載入（如果正在進行）
            if hasattr(self.data_manager, 'stop_loading'):
                self.data_manager.stop_loading()
            
            self._debug("✅ 資源清理完成")
            
        except Exception as e:
            self._error(f"資源清理失敗: {e}")


# ========== 預設 MDI 模組類型註冊 ==========

# 註冊遙測分析 MDI 模組
UniversalAnalysisMDI.register_mdi_module_type(
    'telemetry',
    AnalysisMDIConfig(
        analysis_type='telemetry',
        display_name='遙測分析',
        default_size=(1200, 800),
        requires_driver_params=True,
        requires_lap_params=True,
        supports_single_driver=True,
        supports_dual_driver=True
    )
)

# 註冊降雨分析 MDI 模組
UniversalAnalysisMDI.register_mdi_module_type(
    'rain',
    AnalysisMDIConfig(
        analysis_type='rain',
        display_name='降雨分析',
        default_size=(1000, 700),
        requires_driver_params=False,
        requires_lap_params=False,
        supports_single_driver=False,
        supports_dual_driver=False
    )
)

# 註冊事故分析 MDI 模組
UniversalAnalysisMDI.register_mdi_module_type(
    'accident',
    AnalysisMDIConfig(
        analysis_type='accident',
        display_name='事故分析',
        default_size=(1100, 600),
        requires_driver_params=False,
        requires_lap_params=False,
        supports_single_driver=False,
        supports_dual_driver=False
    )
)

# 註冊進站分析 MDI 模組
UniversalAnalysisMDI.register_mdi_module_type(
    'pitstop',
    AnalysisMDIConfig(
        analysis_type='pitstop',
        display_name='進站分析',
        default_size=(1100, 700),
        requires_driver_params=True,
        requires_lap_params=False,
        supports_single_driver=True,
        supports_dual_driver=True
    )
)


# ========== 工廠函數 ==========

def create_analysis_mdi_module(analysis_type: str, parent=None) -> UniversalAnalysisMDI:
    """
    創建分析 MDI 模組的工廠函數
    
    Args:
        analysis_type: 分析類型
        parent: 父級 QObject
        
    Returns:
        UniversalAnalysisMDI: MDI 模組實例
        
    Note:
        這是抽象基類的工廠函數，實際使用時需要具體的實現類
    """
    if analysis_type not in UniversalAnalysisMDI.MDI_MODULE_TYPES:
        raise ValueError(f"不支援的分析類型: {analysis_type}")
    
    # 實際實現中，這裡應該根據 analysis_type 返回對應的具體實現類
    # 例如：SpeedAnalysisMDI, RainAnalysisMDI 等
    class ConcreteMDI(UniversalAnalysisMDI):
        def create_data_manager(self):
            # 這裡需要返回實際的數據管理器
            return None
        
        def create_chart_widget(self):
            # 這裡需要返回實際的圖表組件
            return None
    
    return ConcreteMDI(analysis_type, parent)
