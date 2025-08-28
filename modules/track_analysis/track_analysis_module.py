"""
TrackAnalysisModule - 賽道分析模組
=================================

這個模組實現賽道位置分析功能，基於 JSON 數據載入車手在賽道上的位置軌跡，
並提供互動式的賽道地圖視覺化。

功能特色：
1. JSON 賽道數據載入與解析
2. 基於 PyQtGraph 的高效能賽道繪圖
3. 互動式縮放、平移、點選功能
4. 原點標註 (紅色圓圈標記第一個信號點)
5. 與現有 MDI 系統完美整合

Author: F1T Team
Date: 2025-08-28
Version: 1.0.0
"""

import json
import os
from typing import Dict, Any, Optional, List, Tuple
from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox, QProgressBar

from ..interfaces import IAnalysisModule
from .track_plot_widget import TrackPlotWidget
from .track_data_loader import TrackDataLoader


class TrackAnalysisModule(IAnalysisModule):
    """
    賽道分析模組
    
    提供賽道位置軌跡的載入、分析和視覺化功能。
    完全兼容現有的 PopoutSubWindow MDI 架構。
    """
    
    # 額外的模組特定信號
    track_data_loaded = pyqtSignal(dict)  # 賽道數據載入完成
    position_selected = pyqtSignal(dict)  # 位置點被選中
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 模組基本資訊
        self._module_name = "TrackAnalysis"
        self._display_name = "賽道分析"
        self._version = "1.0.0"
        self._description = "F1 賽道位置軌跡分析與視覺化"
        
        # 數據相關
        self._current_year = None
        self._current_race = None
        self._current_session = None
        self._track_data = None
        
        # UI 組件
        self._main_widget = None
        self._track_plot = None
        self._data_loader = None
        self._status_label = None
        self._progress_bar = None
        self._refresh_button = None
        
        # 初始化數據載入器
        self._data_loader = TrackDataLoader()
        
    @property
    def module_name(self) -> str:
        """返回模組名稱"""
        return self._module_name
        
    @property
    def display_name(self) -> str:
        """返回顯示名稱"""
        return self._display_name
        
    @property
    def version(self) -> str:
        """返回模組版本"""
        return self._version
        
    @property
    def description(self) -> str:
        """返回模組描述"""
        return self._description
        
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """
        初始化模組
        
        Args:
            parent_widget: 父級 widget (PopoutSubWindow)
            **kwargs: 額外參數
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 創建主要 Widget
            self._main_widget = QWidget(parent_widget)
            layout = QVBoxLayout(self._main_widget)
            layout.setContentsMargins(0, 0, 0, 0)  # 移除邊距
            layout.setSpacing(0)  # 移除間距
            
            # 直接創建賽道繪圖組件，不添加控制面板
            self._track_plot = TrackPlotWidget(self._main_widget)
            layout.addWidget(self._track_plot)
            
            # 連接信號
            self._connect_signals()
            
            # 設置初始狀態（內部狀態，不顯示UI）
            print(f"✅ [TRACK_MODULE] 模組已初始化，等待數據載入...")
            
            self.set_initialized(True)
            return True
            
        except Exception as e:
            self.emit_error(f"模組初始化失敗: {str(e)}")
            return False
            
    def _create_control_panel(self) -> QWidget:
        """創建控制面板（已停用 - 不再使用）"""
        # 這個方法不再被使用，保留以避免潛在的引用錯誤
        panel = QWidget()
        return panel
        
    def _connect_signals(self) -> None:
        """連接信號"""
        # 數據載入器信號
        if self._data_loader:
            self._data_loader.data_loaded.connect(self._on_data_loaded)
            self._data_loader.load_progress.connect(self._on_load_progress)
            self._data_loader.load_error.connect(self._on_load_error)
            
        # 繪圖組件信號
        if self._track_plot:
            self._track_plot.position_clicked.connect(self._on_position_clicked)
            
    def get_widget(self):
        """返回模組的主要 Widget"""
        return self._main_widget
        
    def update_parameters(self, year: int, race: str, session: str) -> bool:
        """
        更新分析參數
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 賽段
            
        Returns:
            bool: 更新是否成功
        """
        try:
            # 驗證參數
            if not self.validate_parameters(year, race, session):
                self.emit_error(f"無效的參數: {year}, {race}, {session}")
                return False
                
            # 檢查參數是否有變化
            params_changed = (
                self._current_year != year or 
                self._current_race != race or 
                self._current_session != session
            )
            
            # 更新內部參數
            self._current_year = year
            self._current_race = race  
            self._current_session = session
            
            # 如果參數有變化，重新載入數據
            if params_changed:
                print(f"🔄 [TRACK_MODULE] 參數變更觸發數據重載: {year} {race} {session}")
                self._update_status(f"參數已更新: {year} {race} {session}")
                
                # 清除現有數據和繪圖
                self._track_data = None
                if self._track_plot:
                    self._track_plot.clear_plot()
                
                # 發出參數更新信號
                params = {
                    'year': year,
                    'race': race,
                    'session': session,
                    'module': self.module_name
                }
                self.emit_parameters_updated(params)
                
                # 立即載入數據（增加延遲確保UI更新完成）
                QTimer.singleShot(200, self.load_data)
                print(f"📅 [TRACK_MODULE] 已安排數據載入任務: {year} {race} {session}")
                
            return True
                
        except Exception as e:
            self.emit_error(f"參數更新失敗: {str(e)}")
            return False
            
    def load_data(self, **kwargs) -> bool:
        """
        載入分析數據
        
        Args:
            **kwargs: 載入參數
            
        Returns:
            bool: 載入是否成功
        """
        try:
            print(f"📂 [TRACK_MODULE] 開始載入數據請求: {self._current_year} {self._current_race} {self._current_session}")
            
            # 檢查參數是否完整
            if not all([self._current_year, self._current_race, self._current_session]):
                error_msg = f"缺少必要參數，無法載入數據: year={self._current_year}, race={self._current_race}, session={self._current_session}"
                print(f"❌ [TRACK_MODULE] {error_msg}")
                self.emit_error(error_msg)
                return False
                
            # 更新UI狀態  
            self._update_status("正在載入賽道數據...")
            if self._progress_bar:
                self._progress_bar.setVisible(True)
                self._progress_bar.setValue(0)
            
            print(f"📂 [TRACK_MODULE] 呼叫數據載入器: {self._current_year} {self._current_race} {self._current_session}")
            
            # 開始載入數據
            success = self._data_loader.load_track_data(
                year=self._current_year,
                race=self._current_race,
                session=self._current_session,
                **kwargs
            )
            
            if not success:
                error_msg = f"數據載入器返回失敗: {self._current_year} {self._current_race} {self._current_session}"
                print(f"❌ [TRACK_MODULE] {error_msg}")
                self._update_status("數據載入失敗")
                if self._progress_bar:
                    self._progress_bar.setVisible(False)
                return False
                
            print(f"✅ [TRACK_MODULE] 數據載入請求已提交成功")
            return True
            
        except Exception as e:
            self.emit_error(f"數據載入失敗: {str(e)}")
            if self._progress_bar:
                self._progress_bar.setVisible(False)
            return False
            
    def _on_data_loaded(self, track_data: dict) -> None:
        """當數據載入完成時的回調"""
        try:
            print(f"🎯 [TRACK_MODULE] 數據載入完成回調，數據類型: {type(track_data)}")
            
            self._track_data = track_data
            
            # 檢查數據內容
            if track_data:
                data_points = len(track_data.get('detailed_position_records', []))
                session_info = track_data.get('session_info', {})
                print(f"🗺️ [TRACK_MODULE] 載入的數據點數: {data_points}")
                print(f"🗺️ [TRACK_MODULE] 賽段資訊: {session_info}")
            else:
                print(f"⚠️ [TRACK_MODULE] 載入的數據為空或無效")
            
            # 更新繪圖組件
            if self._track_plot:
                print(f"🗺️ [TRACK_MODULE] 將數據傳遞給繪圖組件")
                self._track_plot.set_track_data(track_data)
            else:
                print(f"⚠️ [TRACK_MODULE] 繪圖組件不存在")
                
            # 更新狀態
            data_points = len(track_data.get('detailed_position_records', []))
            status_msg = f"載入完成：{data_points} 個位置點"
            print(f"✅ [TRACK_MODULE] {status_msg}")
            self._update_status(status_msg)
            
            if self._progress_bar:
                self._progress_bar.setVisible(False)
            
            # 發出信號
            self.data_loaded.emit(track_data)
            self.track_data_loaded.emit(track_data)
            print(f"📡 [TRACK_MODULE] 已發出數據載入完成信號")
            
        except Exception as e:
            error_msg = f"數據處理失敗: {str(e)}"
            print(f"❌ [TRACK_MODULE] {error_msg}")
            self.emit_error(error_msg)
            
    def _on_load_progress(self, progress: int) -> None:
        """載入進度回調"""
        if self._progress_bar:
            self._progress_bar.setValue(progress)
        
    def _on_load_error(self, error_msg: str) -> None:
        """載入錯誤回調"""
        self.emit_error(f"數據載入錯誤: {error_msg}")
        if self._progress_bar:
            self._progress_bar.setVisible(False)
        self._update_status("載入失敗")
        
    def _on_position_clicked(self, position_data: dict) -> None:
        """當位置點被點擊時的回調"""
        self.position_selected.emit(position_data)
        
    def refresh_analysis(self) -> None:
        """重新執行分析"""
        if not all([self._current_year, self._current_race, self._current_session]):
            QMessageBox.warning(
                self._main_widget,
                "警告",
                "請先設定年份、賽事和賽段參數"
            )
            return
            
        self.load_data()
        
    def clear_data(self) -> None:
        """清除所有數據"""
        self._track_data = None
        if self._track_plot:
            self._track_plot.clear_plot()
        self._update_status("數據已清除")
        
    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        """
        匯出分析數據
        
        Args:
            export_path: 匯出路徑
            export_format: 匯出格式
            
        Returns:
            bool: 匯出是否成功
        """
        try:
            if not self._track_data:
                self.emit_error("沒有可匯出的數據")
                return False
                
            if export_format.lower() == "json":
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(self._track_data, f, ensure_ascii=False, indent=2)
                    
            elif export_format.lower() == "png":
                if self._track_plot:
                    return self._track_plot.export_plot(export_path)
                else:
                    self.emit_error("無法匯出圖片：繪圖組件未初始化")
                    return False
                    
            else:
                self.emit_error(f"不支援的匯出格式: {export_format}")
                return False
                
            return True
            
        except Exception as e:
            self.emit_error(f"匯出失敗: {str(e)}")
            return False
            
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """獲取當前分析數據"""
        return self._track_data
        
    def _update_status(self, message: str) -> None:
        """更新狀態顯示（僅輸出到控制台）"""
        print(f"📊 [TRACK_MODULE] {message}")


# 註冊到模組工廠
def register_track_analysis_module():
    """註冊賽道分析模組到工廠"""
    try:
        from ..gui.base_analysis_module import ModuleFactory, ModuleTypes, BaseAnalysisModule
        
        class TrackAnalysisModuleAdapter(BaseAnalysisModule):
            """TrackAnalysisModule 的模組工廠適配器"""
            
            def __init__(self, parameter_provider=None, **kwargs):
                super().__init__("賽道分析", parameter_provider)
                
                # 從參數提供者或kwargs獲取初始參數
                if parameter_provider:
                    self.year = int(parameter_provider.get_current_year())
                    self.race = parameter_provider.get_current_race()
                    self.session = parameter_provider.get_current_session()
                    print(f"🔧 [TRACK_ADAPTER] 從參數提供者獲取: {self.year} {self.race} {self.session}")
                else:
                    self.year = kwargs.get('year', 2025)
                    self.race = kwargs.get('race', 'Japan')
                    self.session = kwargs.get('session', 'R')
                    print(f"🔧 [TRACK_ADAPTER] 使用預設參數: {self.year} {self.race} {self.session}")
                
                print("🔧 [TRACK_ADAPTER] 開始創建 TrackAnalysisModule...")
                try:
                    self._track_module = TrackAnalysisModule()
                    print("✅ [TRACK_ADAPTER] TrackAnalysisModule 實例創建成功")
                except Exception as e:
                    print(f"❌ [TRACK_ADAPTER] TrackAnalysisModule 實例創建失敗: {e}")
                    raise
                
                # 初始化模組
                print("🔧 [TRACK_ADAPTER] 開始初始化模組...")
                try:
                    if not self._track_module.initialize_module():
                        print("❌ [TRACK_ADAPTER] TrackAnalysisModule 初始化失敗")
                    else:
                        print("✅ [TRACK_ADAPTER] TrackAnalysisModule 初始化成功")
                except Exception as e:
                    print(f"❌ [TRACK_ADAPTER] TrackAnalysisModule 初始化異常: {e}")
                
                # 設定初始參數並開始分析
                print("🔧 [TRACK_ADAPTER] 設定初始參數...")
                try:
                    self._update_track_module_parameters()
                except Exception as e:
                    print(f"⚠️ [TRACK_ADAPTER] 初始參數設定失敗: {e}")
                
                # 如果有參數提供者，後續會通過參數同步更新
                if parameter_provider:
                    print("🔧 [TRACK_ADAPTER] 參數提供者可用，等待後續同步")
                
            def _update_track_module_parameters(self):
                """更新核心模組參數並觸發分析"""
                try:
                    print(f"🔧 [TRACK_ADAPTER] 準備更新核心模組參數: {self.year} {self.race} {self.session}")
                    
                    success = self._track_module.update_parameters(
                        year=self.year, race=self.race, session=self.session
                    )
                    if success:
                        print(f"✅ [TRACK_ADAPTER] 核心模組參數更新成功: {self.year} {self.race} {self.session}")
                        # 觸發數據載入
                        print("🔧 [TRACK_ADAPTER] 開始載入數據...")
                        load_success = self._track_module.load_data()
                        if load_success:
                            print("✅ [TRACK_ADAPTER] 數據載入成功")
                        else:
                            print("⚠️ [TRACK_ADAPTER] 數據載入失敗")
                    else:
                        print(f"⚠️ [TRACK_ADAPTER] 核心模組參數更新失敗")
                except Exception as e:
                    print(f"❌ [TRACK_ADAPTER] 核心模組參數更新異常: {e}")
                    import traceback
                    traceback.print_exc()
                
            def get_widget(self):
                """返回賽道分析的 widget"""
                return self._track_module.get_widget()
                
            def get_title(self) -> str:
                """返回動態標題"""
                year = getattr(self, 'year', 'Unknown')
                race = getattr(self, 'race', 'Unknown') 
                session = getattr(self, 'session', 'Unknown')
                return f"賽道分析 - {year} {race} ({session})"
                
            def update_parameters(self, **params):
                """更新參數 - 參考降雨模組實現"""
                try:
                    # 更新內部參數
                    old_year, old_race, old_session = getattr(self, 'year', None), getattr(self, 'race', None), getattr(self, 'session', None)
                    
                    if 'year' in params:
                        self.year = int(params['year'])
                    if 'race' in params:
                        self.race = params['race']
                    if 'session' in params:
                        self.session = params['session']
                    
                    print(f"🔄 [TRACK_ADAPTER] 參數更新: {old_year}/{old_race}/{old_session} → {self.year}/{self.race}/{self.session}")
                    
                    # 檢查是否有實質改變
                    if (old_year == self.year and old_race == self.race and old_session == self.session):
                        print(f"📋 [TRACK_ADAPTER] 參數無變化，跳過更新")
                        return True
                    
                    # 更新基類參數（只發送信號，不觸發載入）
                    super().update_parameters(**params)
                    
                    # 統一在此觸發核心模組更新
                    if self._track_module:
                        print(f"🔄 [TRACK_ADAPTER] 重新執行分析流程...")
                        self._update_track_module_parameters()
                        return True
                    else:
                        print(f"⚠️ [TRACK_ADAPTER] 模組不存在")
                        return False
                        
                except Exception as e:
                    print(f"❌ [TRACK_ADAPTER] 參數更新異常: {e}")
                    self.signals.module_error.emit(f"參數更新失敗: {e}")
                    return False
                    
            def get_parameter_interface(self):
                """暫時返回 None，未來可擴展"""
                return None
                
            def get_default_size(self):
                """返回適合的賽道分析視窗大小"""
                return (800, 600)
                
            def cleanup(self):
                """清理資源"""
                if self._track_module:
                    self._track_module.cleanup()
                super().cleanup()
        
        # 註冊模組到工廠
        ModuleFactory.register_module(ModuleTypes.TRACK_MAP, TrackAnalysisModuleAdapter)
        print("✅ [TRACK_MODULE] TrackAnalysisModule 已註冊到模組工廠")
        return True
        
    except ImportError as e:
        print(f"⚠️ [TRACK_MODULE] 模組工廠不可用: {e}")
        return False
    except Exception as e:
        print(f"❌ [TRACK_MODULE] 註冊失敗: {e}")
        return False


# 自動註冊（當模組被導入時）
register_track_analysis_module()
