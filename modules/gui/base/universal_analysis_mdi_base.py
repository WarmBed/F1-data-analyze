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

import sip

# 導入國際化函數
from core.gui_i18n import tr

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

    @classmethod
    def get_registered_types(cls) -> List[str]:
        """返回目前已註冊的分析模組類型列表"""
        return list(cls.MDI_MODULE_TYPES.keys())

    @classmethod
    def get_mdi_config(cls, module_type: str) -> Optional[AnalysisMDIConfig]:
        """取得指定分析模組類型的設定，若不存在則回傳 None"""
        return cls.MDI_MODULE_TYPES.get(module_type)
    
    def __init__(self, analysis_type: str, parent=None):
        """
        初始化通用分析 MDI 模組
        
        Args:
            analysis_type: 分析類型
            parent: 父級 QObject
        """
        super().__init__(parent)
        
        # 驗證分析類型
        print(f"🚨 [MDI_INIT] 請求分析類型: {analysis_type}")
        print(f"🚨 [MDI_INIT] 可用的MDI模組類型: {list(self.MDI_MODULE_TYPES.keys())}")
        print(f"🚨 [MDI_INIT] laptime是否在MDI_MODULE_TYPES中: {'laptime' in self.MDI_MODULE_TYPES}")
        
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
        self._cleanup_performed = False
        self._destroyed = False
        
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
    
    def receive_main_window_update_notification(self, param_type: str, value):
        """
        接收主視窗參數更新通知
        
        這個方法被主視窗的同步機制調用，用於響應主視窗參數變更
        
        Args:
            param_type: 參數類型 ('year', 'race', 'session')
            value: 新的參數值
        """
        try:
            self._debug(f"收到主視窗參數更新通知: {param_type} = {value}")
            
            # 根據參數類型更新對應參數
            if param_type == 'year':
                self.update_parameters(year=int(value))
            elif param_type == 'race':
                self.update_parameters(race=value)
            elif param_type == 'session':
                self.update_parameters(session=value)
            else:
                self._debug(f"未知的參數類型: {param_type}")
                
        except Exception as e:
            self._error(f"處理主視窗參數更新通知失敗: {e}")
            self.module_error.emit(f"參數同步失敗: {str(e)}")
    
    def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
        """獲取視窗標題（支援多國語言）"""
        year = year or self.current_year
        race = race or self.current_race
        session = session or self.current_session
        
        # 使用 tr() 翻譯 display_name（支援多國語言）
        # 從 config.analysis_type 取得翻譯鍵，從 config.display_name 取得預設值
        translated_name = tr(self.config.analysis_type, self.config.display_name)
        base_title = f"{translated_name} - {year} {race} {session}"
        
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

    def _disconnect_data_manager_signals(self):
        """斷開數據管理器信號以避免已銷毀物件被回呼"""
        if not hasattr(self, 'data_manager') or not self.data_manager:
            return

        signal_mapping = {
            'data_loaded': self._update_chart,
            'error_occurred': self._handle_error,
            'loading_progress': self._update_progress,
            'status_changed': self._update_status,
        }

        for signal_name, slot in signal_mapping.items():
            try:
                signal = getattr(self.data_manager, signal_name, None)
                if signal:
                    signal.disconnect(slot)
            except (TypeError, RuntimeError):  # signal already disconnected or deleted
                continue

    def _disconnect_chart_widget_signals(self):
        """斷開圖表組件信號"""
        if not hasattr(self, 'chart_widget') or not self.chart_widget:
            return

        if hasattr(self.chart_widget, 'lap_numbers_changed'):
            try:
                self.chart_widget.lap_numbers_changed.disconnect(self._on_lap_numbers_changed)
            except (TypeError, RuntimeError):
                pass

        if hasattr(self.chart_widget, 'drivers_changed'):
            try:
                self.chart_widget.drivers_changed.disconnect(self._on_drivers_changed)
            except (TypeError, RuntimeError):
                pass

    @staticmethod
    def _is_widget_valid(widget) -> bool:
        if widget is None:
            return False
        try:
            return not sip.isdeleted(widget)
        except Exception:
            return True
    
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
        
        # 額外組件區域（控制面板）- 移到圖表上方
        additional_widgets = self.create_additional_widgets()
        for widget in additional_widgets:
            main_splitter.addWidget(widget)
        
        # 圖表區域
        if self.chart_widget and not self._is_widget_valid(self.chart_widget):
            self._debug("🛠️  檢測到已失效的圖表組件，重新建立")
            self._disconnect_chart_widget_signals()
            try:
                self.chart_widget = self.create_chart_widget()
            except Exception as create_exc:
                self._error(f"重新建立圖表組件失敗: {create_exc}")
                self.chart_widget = None
            else:
                self._connect_chart_widget_signals()

        if self.chart_widget:
            chart_frame = QFrame()
            chart_frame.setFrameStyle(QFrame.StyledPanel)
            chart_layout = QVBoxLayout(chart_frame)
            chart_layout.setContentsMargins(5, 5, 5, 5)
            chart_layout.addWidget(self.chart_widget)
            main_splitter.addWidget(chart_frame)
        
        layout.addWidget(main_splitter)
        
        # 狀態列已隱藏 - 提供更簡潔的界面
        self.status_bar = None
        
        # 設置預設比例（控制面板小，圖表佔大部分空間）
        if main_splitter.count() > 1:
            # 第一個是控制面板（50px），其餘是圖表（平分剩餘空間）
            sizes = [50] + [800 // (main_splitter.count() - 1)] * (main_splitter.count() - 1)
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
        if getattr(self, '_cleanup_performed', False):
            self._debug("🛑 模組已釋放，略過數據載入")
            return

        print(f"🚨 [BASE_CRITICAL] _load_data_with_current_parameters 被調用")
        print(f"🚨 [BASE_CRITICAL] self.data_manager = {self.data_manager}")
        print(f"🚨 [BASE_CRITICAL] type(self.data_manager) = {type(self.data_manager)}")
        
        if not self.data_manager:
            print(f"🚨 [BASE_CRITICAL] data_manager 為 None，返回")
            return

        if not self._is_widget_valid(getattr(self, 'main_widget', None)):
            self._debug("🛑 主要視窗已被釋放，取消數據載入")
            return
        
        try:
            # 構建載入參數
            load_params = {
                'year': int(self.current_year),
                'race': self.current_race,
                'session': self.current_session
            }
            
            print(f"🚨 [BASE_CRITICAL] 載入參數: {load_params}")
            
            if self.config.requires_driver_params:
                load_params.update({
                    'driver1': getattr(self, 'driver1', 'VER'),
                    'driver2': getattr(self, 'driver2', 'VER')
                })
                print(f"🚨 [BASE_CRITICAL] 添加車手參數: {load_params}")
            
            if self.config.requires_lap_params:
                load_params.update({
                    'lap1': getattr(self, 'lap1', 1),
                    'lap2': getattr(self, 'lap2', 1)
                })
                print(f"🚨 [BASE_CRITICAL] 添加圈數參數: {load_params}")
            
            # 呼叫數據管理器的載入方法
            has_load_data = hasattr(self.data_manager, 'load_data')
            print(f"🚨 [BASE_CRITICAL] data_manager 是否有 load_data 方法: {has_load_data}")
            
            if has_load_data:
                print(f"🚨 [BASE_CRITICAL] 調用 data_manager.load_data({load_params})")
                self.data_manager.load_data(**load_params)
                print(f"🚨 [BASE_CRITICAL] data_manager.load_data 調用完成")
            elif hasattr(self.data_manager, f'load_{self.analysis_type}_data'):
                load_method = getattr(self.data_manager, f'load_{self.analysis_type}_data')
                print(f"🚨 [BASE_CRITICAL] 調用 load_{self.analysis_type}_data 方法")
                load_method(**load_params)
            else:
                print(f"🚨 [BASE_CRITICAL] ⚠️ 數據管理器沒有合適的載入方法")
                self._debug("⚠️  數據管理器沒有合適的載入方法")
            
        except Exception as e:
            print(f"🚨 [BASE_CRITICAL] 異常: {e}")
            import traceback
            traceback.print_exc()
            self._error(f"數據載入失敗: {e}")
            self.module_error.emit(f"數據載入失敗: {str(e)}")
    
    # ========== 信號處理方法 ==========
    
    def _update_chart(self, data: dict):
        """更新圖表數據"""
        try:
            if getattr(self, '_cleanup_performed', False):
                self._debug("🛑 已清理的模組忽略圖表更新")
                return

            if not self._is_widget_valid(self.chart_widget):
                self._debug("🛑 圖表組件已被釋放，忽略更新")
                return

            self._debug("📊 更新圖表數據")
            self._debug(f"🔍 圖表組件詳細信息:")
            self._debug(f"   - 組件類型: {type(self.chart_widget)}")
            self._debug(f"   - 組件模組: {type(self.chart_widget).__module__}")
            self._debug(f"   - 有 update_data: {hasattr(self.chart_widget, 'update_data')}")
            self._debug(f"   - 有 set_data: {hasattr(self.chart_widget, 'set_data')}")
            
            if hasattr(self.chart_widget, 'update_data'):
                self._debug(f"✅ 使用 update_data 方法")
                self._debug(f"   - update_data 方法來源: {type(self.chart_widget).update_data}")
                self.chart_widget.update_data(data)
            elif hasattr(self.chart_widget, 'set_data'):
                self._debug(f"⚠️ 使用 set_data 方法")
                self._debug(f"   - set_data 方法來源: {type(self.chart_widget).set_data}")
                self._debug(f"   - 數據類型: {type(data)}")
                self._debug(f"   - 數據鍵: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                self.chart_widget.set_data(data)
            else:
                self._debug("⚠️  圖表組件沒有數據更新方法")
            
            # 發送數據載入完成信號
            self.data_loaded.emit(data)
            
            # 更新工具欄狀態信息
            self._update_toolbar_status(data)
            
            # 更新狀態
            self._update_status("數據載入完成")
            
        except Exception as e:
            self._error(f"圖表更新失敗: {e}")
            self.module_error.emit(f"圖表更新失敗: {str(e)}")
    
    def _handle_error(self, error_message: str):
        """處理錯誤"""
        if getattr(self, '_cleanup_performed', False):
            return
        self._error(f"數據載入錯誤: {error_message}")
        self.module_error.emit(error_message)
        self._update_status(f"錯誤: {error_message}")
    
    def _update_progress(self, progress: int):
        """更新進度（狀態列已隱藏）"""
        if getattr(self, '_cleanup_performed', False):
            return
        # 狀態列已隱藏，不顯示進度訊息
        if self.status_bar:
            self.status_bar.showMessage(f"載入中... {progress}%")
    
    def _update_status(self, message: str):
        """更新狀態（狀態列已隱藏）"""
        if getattr(self, '_cleanup_performed', False):
            return
        # 狀態列已隱藏，不顯示狀態訊息
        if self.status_bar:
            self.status_bar.showMessage(message)
    
    def _on_lap_numbers_changed(self, lap1: int, lap2: int):
        """處理圈數變更"""
        if self.config.requires_lap_params:
            if getattr(self, '_cleanup_performed', False):
                return
            self.lap1 = lap1
            self.lap2 = lap2
            self._debug(f"圈數更新: {lap1} vs {lap2}")
            self._load_data_with_current_parameters()
    
    def _on_drivers_changed(self, driver1: str, driver2: str):
        """處理車手變更"""
        if self.config.requires_driver_params:
            if getattr(self, '_cleanup_performed', False):
                return
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
    
    def update_window_title(self) -> None:
        """更新視窗標題 - 參照速度分析模組增強版"""
        try:
            # 檢查 parent_window 屬性（MDI 子視窗引用）
            parent = getattr(self, 'parent_window', None)
            
            if parent and hasattr(parent, 'setWindowTitle'):
                new_title = self.get_window_title(self.current_year, self.current_race, self.current_session)
                parent.setWindowTitle(new_title)
                
                # 強制刷新視窗顯示
                parent.update()
                parent.repaint()
                
                self._debug(f"🏷️ 視窗標題已更新為: {new_title}")
        except Exception as e:
            self._error(f"更新視窗標題失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def cleanup(self):
        """清理資源 - 參照速度分析模組增強版"""
        try:
            if getattr(self, '_cleanup_performed', False):
                return

            self._cleanup_performed = True
            self._destroyed = True

            self._disconnect_data_manager_signals()
            self._disconnect_chart_widget_signals()

            # 從分析模組管理器解除註冊
            if hasattr(self, '_analysis_manager') and self._analysis_manager and hasattr(self, '_module_id'):
                try:
                    # 解除註冊圖表組件
                    if hasattr(self, 'chart_widget') and self.chart_widget:
                        self._analysis_manager.unregister_chart_widget(self.chart_widget)
                    
                    # 解除註冊模組
                    self._analysis_manager.unregister_module(self._module_id)
                    self._debug(f"✅ 已從分析模組管理器解除註冊: {self._module_id}")
                    
                except Exception as e:
                    self._error(f"從分析模組管理器解除註冊失敗: {e}")
            
            if hasattr(self, 'data_manager') and self.data_manager:
                # 停止數據載入（如果正在進行）
                if hasattr(self.data_manager, 'stop_loading'):
                    self.data_manager.stop_loading()
                # 清理數據管理器
                if hasattr(self.data_manager, 'cleanup'):
                    self.data_manager.cleanup()
                self.data_manager = None
                    
            if hasattr(self, 'chart_widget') and self.chart_widget:
                # 🔧 修復：從連動管理器中取消註冊圖表組件
                try:
                    from modules.gui.lap_analysis.linkage import linkage_manager
                    if linkage_manager:
                        linkage_manager.unregister_module(self.chart_widget)
                        self._debug("✅ 已從連動管理器解除註冊圖表組件")
                except Exception as e:
                    self._error(f"從連動管理器解除註冊失敗: {e}")
                
                # 清理圖表組件
                if hasattr(self.chart_widget, 'cleanup'):
                    self.chart_widget.cleanup()
                self.chart_widget.deleteLater()
                self.chart_widget = None
                
            if hasattr(self, 'main_widget') and self.main_widget:
                # 清理主要組件
                self.main_widget.deleteLater()
                self.main_widget = None

            self.parent_window = None
            
            self._debug("✅ 基礎資源清理完成")
            
            # 🔴 新增步驟 7: 徹底斷開所有 Qt 連接（修復洩漏）
            try:
                self.disconnect()
                print(f"[{self.config.display_name}] ✅ Qt 連接已斷開")
            except Exception as e:
                print(f"[{self.config.display_name}] ⚠️ 斷開 Qt 連接警告: {e}")
            
            # 🔴 新增步驟 8: 徹底清理 __dict__（修復洩漏）
            try:
                module_name = self.config.display_name if hasattr(self, 'config') else "UniversalMDI"
                all_attrs = list(self.__dict__.keys())
                cleaned_count = 0
                
                for attr in all_attrs:
                    if not attr.startswith('__'):
                        try:
                            delattr(self, attr)
                            cleaned_count += 1
                        except Exception:
                            pass
                
                print(f"[{module_name}] ✅ __dict__ 已清理（{cleaned_count} 個屬性）")
                print(f"[{module_name}] ✅ 完整資源清理完成")
            except Exception as e:
                print(f"[UniversalMDI] ⚠️ __dict__ 清理警告: {e}")
            
        except Exception as e:
            if hasattr(self, '_error'):
                self._error(f"資源清理失敗: {e}")
            else:
                print(f"[UniversalMDI] ❌ 資源清理失敗: {e}")
    
    # ========== IAnalysisModule 額外方法實現 ==========
    
    def get_title(self) -> str:
        """返回模組標題 - 實現 IAnalysisModule 抽象方法"""
        return f"{self.config.display_name} - {self.current_year} {self.current_race} {self.current_session}"
    
    def supports_sync(self) -> bool:
        """是否支援主程式同步 - 實現 IAnalysisModule 抽象方法"""
        return True
    
    def get_parameter_interface(self) -> Optional[QWidget]:
        """返回參數設定介面 - 實現 IAnalysisModule 抽象方法"""
        # 預設不提供參數設定介面，子類可覆寫
        return None
    
    # ========== 工具欄狀態管理 ==========
    
    def _update_toolbar_status(self, data: dict):
        """更新工具欄狀態信息 - 參照速度分析模組"""
        try:
            # 獲取主視窗引用
            main_window = self._get_main_window()
            if not main_window or not hasattr(main_window, 'update_toolbar_status'):
                return
            
            # 提取狀態信息
            metadata = data.get('metadata', {})
            drivers = metadata.get('drivers', [])
            
            module_name = self.config.display_name
            lap_time = ""
            tyre_compound = ""
            lap_numbers = ""
            
            if drivers:
                if len(drivers) >= 2 and self.config.requires_driver_params:
                    # 雙車手模式
                    driver1 = drivers[0]
                    driver2 = drivers[1]
                    
                    lap_time1 = driver1.get('lap_time', 'N/A')
                    lap_time2 = driver2.get('lap_time', 'N/A')
                    lap_time = f"{lap_time1} | {lap_time2}"
                    
                    compound1 = driver1.get('compound', 'N/A')
                    compound2 = driver2.get('compound', 'N/A')
                    tyre_compound = f"{compound1} | {compound2}"
                    
                    driver1_code = driver1.get('code', getattr(self, 'driver1', 'VER'))
                    driver2_code = driver2.get('code', getattr(self, 'driver2', 'VER'))
                    
                    if self.config.requires_lap_params:
                        lap1 = getattr(self, 'lap1', 1)
                        lap2 = getattr(self, 'lap2', 1)
                        lap_numbers = f"{driver1_code} 第{lap1}圈 vs {driver2_code} 第{lap2}圈"
                    else:
                        lap_numbers = f"{driver1_code} vs {driver2_code}"
                    
                elif len(drivers) >= 1 and self.config.requires_driver_params:
                    # 單車手模式
                    driver1 = drivers[0]
                    lap_time = driver1.get('lap_time', 'N/A')
                    tyre_compound = driver1.get('compound', 'N/A')
                    
                    driver1_code = driver1.get('code', getattr(self, 'driver1', 'VER'))
                    
                    if self.config.requires_lap_params:
                        lap1 = getattr(self, 'lap1', 1)
                        lap_numbers = f"{driver1_code} 第{lap1}圈"
                    else:
                        lap_numbers = f"{driver1_code}"
                        
            else:
                # 無車手數據時顯示基本信息
                if self.config.requires_lap_params:
                    lap1 = getattr(self, 'lap1', 1)
                    lap2 = getattr(self, 'lap2', 1)
                    lap_numbers = f"第{lap1}圈 vs 第{lap2}圈"
            
            # 更新工具欄狀態
            main_window.update_toolbar_status(
                module_name=module_name,
                lap_time=lap_time,
                tyre_compound=tyre_compound,
                lap_numbers=lap_numbers
            )
            
            self._debug(f"已更新工具欄狀態: {module_name}")
            
        except Exception as e:
            self._error(f"更新工具欄狀態失敗: {e}")
    
    def _get_main_window(self):
        """獲取主視窗引用 - 參照速度分析模組"""
        try:
            # 通過MDI子視窗獲取主視窗
            if self.parent_window:
                mdi_area = self.parent_window.parent()
                if mdi_area:
                    # 查找主視窗
                    widget = mdi_area
                    while widget and not hasattr(widget, 'update_toolbar_status'):
                        widget = widget.parent()
                    return widget
            return None
        except Exception as e:
            self._error(f"獲取主視窗失敗: {e}")
            return None


# ========== 預設 MDI 模組類型註冊 ==========

# 註冊遙測分析 MDI 模組
UniversalAnalysisMDI.register_mdi_module_type(
    'telemetry',
    AnalysisMDIConfig(
        analysis_type='telemetry',
        display_name=tr('telemetry_analysis', '遙測分析'),
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
        display_name=tr('rain_analysis', '降雨分析'),
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
        display_name=tr('accident_analysis', 'Accident Analysis'),
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
        display_name=tr('pitstop_analysis', '進站分析'),
        default_size=(1100, 700),
        requires_driver_params=True,
        requires_lap_params=False,
        supports_single_driver=True,
        supports_dual_driver=True
    )
)

# 註冊速度分析 MDI 模組
UniversalAnalysisMDI.register_mdi_module_type(
    'speed',
    AnalysisMDIConfig(
        analysis_type='speed',
        display_name=tr('speed_analysis', '速度分析'),
        default_size=(900, 600),
        requires_driver_params=True,
        requires_lap_params=True,
        supports_single_driver=True,
        supports_dual_driver=True
    )
)

# 註冊煞車分析 MDI 模組
UniversalAnalysisMDI.register_mdi_module_type(
    'brake',
    AnalysisMDIConfig(
        analysis_type='brake',
        display_name=tr('brake_analysis', '煞車分析'),
        default_size=(900, 600),
        requires_driver_params=True,
        requires_lap_params=True,
        supports_single_driver=True,
        supports_dual_driver=True
    )
)

# 註冊齒輪分析 MDI 模組
UniversalAnalysisMDI.register_mdi_module_type(
    'gear',
    AnalysisMDIConfig(
        analysis_type='gear',
        display_name=tr('gear_analysis', '檔位分析'),
        default_size=(900, 600),
        requires_driver_params=True,
        requires_lap_params=True,
        supports_single_driver=True,
        supports_dual_driver=True
    )
)

# 註冊RPM分析 MDI 模組
UniversalAnalysisMDI.register_mdi_module_type(
    'rpm',
    AnalysisMDIConfig(
        analysis_type='rpm',
        display_name=tr('rpm_analysis', 'RPM分析'),
        default_size=(900, 600),
        requires_driver_params=True,
        requires_lap_params=True,
        supports_single_driver=True,
        supports_dual_driver=True
    )
)

# 註冊節流閥分析 MDI 模組
UniversalAnalysisMDI.register_mdi_module_type(
    'throttle',
    AnalysisMDIConfig(
        analysis_type='throttle',
        display_name=tr('throttle_analysis', '油門分析'),
        default_size=(900, 600),
        requires_driver_params=True,
        requires_lap_params=True,
        supports_single_driver=True,
        supports_dual_driver=True
    )
)

# 註冊加速度分析 MDI 模組
UniversalAnalysisMDI.register_mdi_module_type(
    'acceleration',
    AnalysisMDIConfig(
        analysis_type='acceleration',
        display_name=tr('acceleration_analysis', '加速度分析'),
        default_size=(900, 600),
        requires_driver_params=True,
        requires_lap_params=True,
        supports_single_driver=True,
        supports_dual_driver=True
    )
)

# 註冊速度差分析 MDI 模組
UniversalAnalysisMDI.register_mdi_module_type(
    'speeddiff',
    AnalysisMDIConfig(
        analysis_type='speeddiff',
        display_name=tr('speeddiff_analysis', '速度差異分析'),
        default_size=(900, 600),
        requires_driver_params=True,
        requires_lap_params=True,
        supports_single_driver=True,
        supports_dual_driver=True
    )
)

# 註冊距離差分析 MDI 模組
UniversalAnalysisMDI.register_mdi_module_type(
    'distancediff',
    AnalysisMDIConfig(
        analysis_type='distancediff',
        display_name=tr('distancediff_analysis', '距離差異分析'),
        default_size=(900, 600),
        requires_driver_params=True,
        requires_lap_params=True,
        supports_single_driver=True,
        supports_dual_driver=True
    )
)

# 註冊詳細圈速分析 MDI 模組
UniversalAnalysisMDI.register_mdi_module_type(
    'laptime',
    AnalysisMDIConfig(
        analysis_type='laptime',
        display_name=tr('detailed_lap_analysis', 'Detailed Lap Analysis'),
        default_size=(1200, 800),
        requires_driver_params=True,
        requires_lap_params=False,
        supports_single_driver=True,
        supports_dual_driver=True
    )
)

# 註冊油門折線圖分析 MDI 模組
UniversalAnalysisMDI.register_mdi_module_type(
    'throttle_line',
    AnalysisMDIConfig(
        analysis_type='throttle_line',
        display_name=tr('throttle_line_chart', 'Throttle Line Chart'),
        default_size=(1400, 900),
        requires_driver_params=True,
        requires_lap_params=False,
        supports_single_driver=True,
        supports_dual_driver=False
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
