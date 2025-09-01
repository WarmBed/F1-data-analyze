#!/usr/bin/env python3
"""
F1T 速度分析 MDI 模組
基於進站分析模組的成功架構設計
支援雙車手速度對比的 GUI 模組，使用新版模組更新機制
"""

import sys
import os
import json
import datetime
import traceback
from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QProgressBar, QStatusBar, QToolBar, QAction,
    QHeaderView, QDialog, QDialogButtonBox, QComboBox, QCheckBox,
    QGroupBox, QGridLayout, QTextEdit, QMessageBox, QFrame, QScrollArea, QSplitter
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QObject
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor

# 導入分析模組介面
try:
    from .interfaces.analysis_module import IAnalysisModule
except ImportError:
    # 如果相對導入失敗，嘗試絕對導入
    try:
        from modules.interfaces.analysis_module import IAnalysisModule
    except ImportError:
        # 如果都失敗，定義一個基本的接口
        from PyQt5.QtCore import QObject
        class IAnalysisModule(QObject):
            def __init__(self, parent=None):
                super().__init__(parent)

class SpeedDataManager(QObject):
    """速度數據管理器 - 負責JSON緩存和CLI備援"""
    
    # 信號定義
    data_loaded = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    loading_progress = pyqtSignal(int)
    status_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_year = None
        self.current_race = None
        self.current_session = None
        self.loading = False
        self._is_loading = False
        
    def load_speed_data(self, year: str, race: str, session: str, 
                       driver1: str = "VER", driver2: str = "VER",
                       lap1: int = 1, lap2: int = 1) -> bool:
        """載入速度對比數據"""
        try:
            print(f"[SPEED_MDI_DATA] ========== 載入速度數據 ==========")
            print(f"[SPEED_MDI_DATA] 參數: {year} {race} {session}")
            print(f"[SPEED_MDI_DATA] 車手: {driver1} vs {driver2}, 圈數: {lap1} vs {lap2}")
            
            if self._is_loading:
                print(f"[SPEED_MDI_DATA] ⚠️ 數據載入中，忽略新請求")
                self.error_occurred.emit("載入器正忙，請稍後再試")
                return False
                
            self._is_loading = True
            self.loading_progress.emit(0)
            self.status_changed.emit("開始載入速度數據...")
            
            print(f"[SPEED_MDI_DATA] 🔗 創建 SpeedAnalysisDataLoader...")
            
            # 使用現有的速度分析數據載入器
            from modules.speed_analysis_data_loader import SpeedAnalysisDataLoader
            
            print(f"[SPEED_MDI_DATA] 🚀 調用 load_speed_data...")
            
            # 創建數據載入器
            speed_loader = SpeedAnalysisDataLoader()
            speed_loader.data_loaded.connect(self._on_data_loaded)
            speed_loader.load_error.connect(self._on_load_error)
            speed_loader.status_changed.connect(self.status_changed.emit)
            speed_loader.load_progress.connect(self.loading_progress.emit)
            
            # 開始載入數據
            success = speed_loader.load_speed_data(
                year=int(year),
                race=race,
                session=session,
                driver1=driver1,
                driver2=driver2,
                lap1=lap1,
                lap2=lap2,
                is_fastest_lap=False
            )
            
            # 保存載入器引用避免被回收
            self._speed_loader = speed_loader
            
            return success
            
        except Exception as e:
            print(f"[ERROR] [SPEED_MDI] 速度數據載入失敗: {e}")
            self.error_occurred.emit(f"載入失敗: {str(e)}")
            self._is_loading = False
            return False
    
    def _on_data_loaded(self, data: dict):
        """處理數據載入完成"""
        try:
            print(f"[SPEED_MDI] 數據載入完成")
            self._is_loading = False
            self.data_loaded.emit(data)
        except Exception as e:
            print(f"[ERROR] [SPEED_MDI] 數據處理失敗: {e}")
            self.error_occurred.emit(f"數據處理失敗: {str(e)}")
    
    def _on_load_error(self, error_message: str):
        """處理載入錯誤"""
        print(f"[ERROR] [SPEED_MDI] 載入錯誤: {error_message}")
        self._is_loading = False
        self.error_occurred.emit(error_message)

class SpeedAnalysisModule(IAnalysisModule):
    """速度分析主模組"""
    
    # 信號定義
    module_error = pyqtSignal(str)
    parameters_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 參數狀態
        self.current_year = "2025"
        self.current_race = "Japan"
        self.current_session = "R"
        self.parameter_provider = None
        
        # 車手和圈數參數
        self.driver1 = "VER"
        self.driver2 = "VER" 
        self.lap1 = 1
        self.lap2 = 1
        
        # 組件
        self.data_manager = None
        self.speed_chart_widget = None
        self.main_widget = None  # 主容器 widget
        self.parent_window = None  # MDI 子視窗引用
        
        # 初始化狀態
        self._initialized = False
        
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """初始化模組 - 實現抽象方法"""
        try:
            print(f"[SPEED_MDI] 初始化速度分析模組")
            
            # 創建數據管理器
            self.data_manager = SpeedDataManager()
            self.data_manager.data_loaded.connect(self._update_chart)
            self.data_manager.error_occurred.connect(self._handle_error)
            
            # 創建速度圖表組件
            from modules.speed_analysis_chart_widget import SpeedAnalysisChartWidget
            self.speed_chart_widget = SpeedAnalysisChartWidget()
            
            # 連接圈數變更信號
            self.speed_chart_widget.lap_numbers_changed.connect(self._on_lap_numbers_changed)
            
            # 設置初始圈數
            self.speed_chart_widget.set_lap_numbers(self.lap1, self.lap2)
            
            # 設置主界面
            self._setup_ui()
            
            self._initialized = True
            print(f"[OK] [SPEED_MDI] 速度分析模組初始化完成")
            return True
            
        except Exception as e:
            print(f"[ERROR] [SPEED_MDI] 模組初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def set_parent_window(self, parent_window):
        """設置父視窗引用（MDI 子視窗）"""
        print(f"[SPEED_TITLE_DEBUG] 🔗 設置父視窗引用...")
        print(f"[SPEED_TITLE_DEBUG]   - 父視窗類型: {type(parent_window).__name__}")
        print(f"[SPEED_TITLE_DEBUG]   - 父視窗是否為None: {parent_window is None}")
        
        self.parent_window = parent_window
        
        if parent_window:
            # 獲取當前標題以供調試
            current_title = parent_window.windowTitle()
            print(f"[SPEED_TITLE_DEBUG]   - 當前父視窗標題: '{current_title}'")
            
            # 立即設置正確的標題
            print(f"[SPEED_TITLE_DEBUG] 🏷️ 父視窗設置後立即更新標題...")
            self.update_window_title()
        else:
            print(f"[SPEED_TITLE_DEBUG] ⚠️ 父視窗為None，無法設置標題")
        
        print(f"[SPEED_TITLE_DEBUG] ✅ 父視窗引用設置完成")
    
    def _setup_ui(self):
        """設置用戶界面"""
        # 創建主容器 widget
        self.main_widget = QWidget()
        layout = QVBoxLayout()
        
        # 添加速度圖表
        if self.speed_chart_widget:
            layout.addWidget(self.speed_chart_widget)
        
        # 設置佈局到主 widget
        self.main_widget.setLayout(layout)
    
    def _update_chart(self, data: dict):
        """更新圖表"""
        try:
            print(f"[SPEED_MDI] 更新速度圖表")
            if self.speed_chart_widget:
                self.speed_chart_widget.update_speed_data(data)
        except Exception as e:
            print(f"[ERROR] [SPEED_MDI] 圖表更新失敗: {e}")
            self.module_error.emit(f"圖表更新失敗: {str(e)}")
    
    def _handle_error(self, error_message: str):
        """處理錯誤"""
        print(f"[ERROR] [SPEED_MDI] {error_message}")
        self.module_error.emit(error_message)
    
    def _on_lap_numbers_changed(self, lap1: int, lap2: int):
        """處理圈數變更"""
        try:
            print(f"[SPEED_MDI] ========== 圈數變更處理 ==========")
            print(f"[SPEED_MDI] 新圈數: 第{lap1}圈 vs 第{lap2}圈")
            
            # 更新模組的圈數參數
            old_lap1, old_lap2 = self.lap1, self.lap2
            self.lap1 = lap1
            self.lap2 = lap2
            
            print(f"[SPEED_MDI] 圈數變更: 第{old_lap1}圈 vs 第{old_lap2}圈 → 第{lap1}圈 vs 第{lap2}圈")
            
            # 重新載入數據
            if self.data_manager:
                print(f"[SPEED_MDI] 🔄 因圈數變更重新載入數據...")
                success = self.data_manager.load_speed_data(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session,
                    driver1=self.driver1,
                    driver2=self.driver2,
                    lap1=self.lap1,
                    lap2=self.lap2
                )
                
                if success:
                    print(f"[SPEED_MDI] ✅ 圈數變更後數據重載成功")
                else:
                    print(f"[SPEED_MDI] ❌ 圈數變更後數據重載失敗")
            else:
                print(f"[SPEED_MDI] ❌ 數據管理器未初始化，無法重載數據")
                
        except Exception as e:
            print(f"[ERROR] [SPEED_MDI] 處理圈數變更失敗: {e}")
            import traceback
            traceback.print_exc()
            self.module_error.emit(f"處理圈數變更失敗: {str(e)}")
    
    def update_parameters(self, year: int = None, race: str = None, session: str = None, **kwargs) -> bool:
        """更新參數 - 實現抽象方法"""
        try:
            print(f"[SPEED_PARAMS_DEBUG] ========== 參數更新請求 ==========")
            print(f"[SPEED_PARAMS_DEBUG] 📋 收到更新請求:")
            print(f"[SPEED_PARAMS_DEBUG]   - 年份: {year}")
            print(f"[SPEED_PARAMS_DEBUG]   - 賽事: {race}")
            print(f"[SPEED_PARAMS_DEBUG]   - 賽段: {session}")
            print(f"[SPEED_PARAMS_DEBUG] 📊 當前模組狀態:")
            print(f"[SPEED_PARAMS_DEBUG]   - 當前年份: {self.current_year}")
            print(f"[SPEED_PARAMS_DEBUG]   - 當前賽事: {self.current_race}")
            print(f"[SPEED_PARAMS_DEBUG]   - 當前賽段: {self.current_session}")
            
            # 準備更新的參數
            new_year = str(year) if year is not None else self.current_year
            new_race = race if race is not None else self.current_race
            new_session = session if session is not None else self.current_session
            
            print(f"[SPEED_PARAMS_DEBUG] 🎯 計算後的新參數:")
            print(f"[SPEED_PARAMS_DEBUG]   - 新年份: {new_year}")
            print(f"[SPEED_PARAMS_DEBUG]   - 新賽事: {new_race}")
            print(f"[SPEED_PARAMS_DEBUG]   - 新賽段: {new_session}")
            
            # 檢查參數是否有變化（基於當前的模組參數）
            params_changed = (
                self.current_year != new_year or 
                self.current_race != new_race or 
                self.current_session != new_session
            )
            
            print(f"[SPEED_PARAMS_DEBUG] 🔍 參數變化檢查:")
            print(f"[SPEED_PARAMS_DEBUG]   - 年份變化: {self.current_year} → {new_year} ({self.current_year != new_year})")
            print(f"[SPEED_PARAMS_DEBUG]   - 賽事變化: {self.current_race} → {new_race} ({self.current_race != new_race})")
            print(f"[SPEED_PARAMS_DEBUG]   - 賽段變化: {self.current_session} → {new_session} ({self.current_session != new_session})")
            print(f"[SPEED_PARAMS_DEBUG]   - 整體參數是否變化: {params_changed}")
            
            # 更新本地參數（如果調用者沒有提前更新的話）
            old_year, old_race, old_session = self.current_year, self.current_race, self.current_session
            self.current_year = new_year
            self.current_race = new_race
            self.current_session = new_session
            
            print(f"[SPEED_PARAMS_DEBUG] 🔄 參數已更新至模組:")
            print(f"[SPEED_PARAMS_DEBUG]   - 年份: {old_year} → {self.current_year}")
            print(f"[SPEED_PARAMS_DEBUG]   - 賽事: {old_race} → {self.current_race}")
            print(f"[SPEED_PARAMS_DEBUG]   - 賽段: {old_session} → {self.current_session}")
            
            # 確保視窗標題是最新的（防止任何可能的延遲更新）
            print(f"[SPEED_PARAMS_DEBUG] 🏷️ 確保視窗標題最新...")
            self.update_window_title()
            
            if params_changed:
                print(f"[SPEED_PARAMS_DEBUG] 🔄 參數已變化，開始重載數據...")
                
                # 載入新數據
                if self.data_manager:
                    print(f"[SPEED_PARAMS_DEBUG] 📡 調用數據管理器載入新數據...")
                    print(f"[SPEED_PARAMS_DEBUG] 📊 載入參數:")
                    print(f"[SPEED_PARAMS_DEBUG]   - 年份: {self.current_year}")
                    print(f"[SPEED_PARAMS_DEBUG]   - 賽事: {self.current_race}")
                    print(f"[SPEED_PARAMS_DEBUG]   - 賽段: {self.current_session}")
                    print(f"[SPEED_PARAMS_DEBUG]   - 車手1: {self.driver1} (第{self.lap1}圈)")
                    print(f"[SPEED_PARAMS_DEBUG]   - 車手2: {self.driver2} (第{self.lap2}圈)")
                    
                    success = self.data_manager.load_speed_data(
                        year=self.current_year,
                        race=self.current_race,
                        session=self.current_session,
                        driver1=self.driver1,
                        driver2=self.driver2,
                        lap1=self.lap1,
                        lap2=self.lap2
                    )
                    
                    if success:
                        print(f"[SPEED_PARAMS_DEBUG] ✅ 數據載入成功")
                        # 數據載入成功後再次確保標題正確
                        print(f"[SPEED_PARAMS_DEBUG] 🏷️ 數據載入後再次確認標題正確...")
                        self.update_window_title()
                        self.parameters_updated.emit({
                            'year': int(new_year),
                            'race': new_race,
                            'session': new_session
                        })
                        print(f"[SPEED_PARAMS_DEBUG] ✅ 參數更新完全成功")
                        return True
                    else:
                        print(f"[SPEED_PARAMS_DEBUG] ❌ 數據載入失敗")
                        print(f"[SPEED_PARAMS_DEBUG] ❌ 數據載入失敗")
                        return False
                else:
                    print(f"[SPEED_PARAMS_DEBUG] ❌ 數據管理器未初始化")
                    return False
            else:
                print(f"[SPEED_PARAMS_DEBUG] ℹ️ 參數未變化，檢查是否需要首次載入...")
                # 如果是首次載入或沒有數據，仍然需要載入
                if self.data_manager and not hasattr(self, '_data_loaded'):
                    print(f"[SPEED_PARAMS_DEBUG] 🔄 首次載入數據...")
                    success = self.data_manager.load_speed_data(
                        year=self.current_year,
                        race=self.current_race,
                        session=self.current_session,
                        driver1=self.driver1,
                        driver2=self.driver2,
                        lap1=self.lap1,
                        lap2=self.lap2
                    )
                    if success:
                        self._data_loaded = True
                        print(f"[SPEED_PARAMS_DEBUG] ✅ 首次數據載入成功")
                        return True
                    else:
                        print(f"[SPEED_PARAMS_DEBUG] ❌ 首次數據載入失敗")
                        return False
                else:
                    print(f"[SPEED_PARAMS_DEBUG] ℹ️ 數據已存在或未初始化，跳過載入")
                    return True
            
            print(f"[SPEED_PARAMS_DEBUG] ========== 參數更新完成 ==========")
                
        except Exception as e:
            print(f"[ERROR] [SPEED_PARAMS_DEBUG] 參數更新失敗: {e}")
            import traceback
            traceback.print_exc()
            self.module_error.emit(f"參數更新失敗: {str(e)}")
            return False
            import traceback
            traceback.print_exc()
            self.module_error.emit(f"參數更新失敗: {str(e)}")
            return False
    
    def update_lap_parameters(self, year: str, race: str, session: str, 
                            driver1: str, driver2: str = None, 
                            lap1: int = 1, lap2: int = 1, 
                            is_fastest: bool = False) -> bool:
        """更新圈速分析參數（包含車手和圈數）"""
        try:
            print(f"[SPEED_MDI] ========== 圈速參數更新 ==========")
            print(f"[SPEED_MDI] 收到參數: {year} {race} {session}")
            print(f"[SPEED_MDI] 車手: {driver1} vs {driver2}")
            print(f"[SPEED_MDI] 圈數: 第{lap1}圈 vs 第{lap2}圈")
            print(f"[SPEED_MDI] 最速圈: {is_fastest}")
            
            # 檢查參數是否有變化
            params_changed = (
                self.current_year != str(year) or 
                self.current_race != race or 
                self.current_session != session or
                self.driver1 != driver1 or
                self.driver2 != (driver2 or "VER") or  # 處理 None 值
                self.lap1 != lap1 or
                self.lap2 != lap2
            )
            
            print(f"[SPEED_MDI] 參數是否變化: {params_changed}")
            
            # 更新所有參數
            self.current_year = str(year)
            self.current_race = race
            self.current_session = session
            self.driver1 = driver1
            self.driver2 = driver2 or "VER"  # 如果沒有第二個車手，預設為 VER
            self.lap1 = lap1
            self.lap2 = lap2
            
            # 更新圖表組件的圈數顯示
            if self.speed_chart_widget:
                self.speed_chart_widget.set_lap_numbers(lap1, lap2)
                print(f"[SPEED_MDI] ✅ 已更新圖表組件的圈數顯示")
            
            if params_changed:
                print(f"[SPEED_MDI] 🔄 參數已變化，開始重載數據...")
                
                # 載入新數據
                if self.data_manager:
                    print(f"[SPEED_MDI] 📡 調用數據管理器載入新數據...")
                    success = self.data_manager.load_speed_data(
                        year=self.current_year,
                        race=self.current_race,
                        session=self.current_session,
                        driver1=self.driver1,
                        driver2=self.driver2,
                        lap1=self.lap1,
                        lap2=self.lap2
                    )
                    
                    if success:
                        print(f"[SPEED_MDI] ✅ 圈速參數更新後數據重載成功")
                        # 發送參數更新信號
                        self.parameters_updated.emit({
                            'year': self.current_year,
                            'race': self.current_race,
                            'session': self.current_session,
                            'driver1': self.driver1,
                            'driver2': self.driver2,
                            'lap1': self.lap1,
                            'lap2': self.lap2
                        })
                        
                        # 更新視窗標題以反映新的參數 - 使用統一的 get_window_title
                        parent = getattr(self, 'parent_window', None)
                        if parent and hasattr(parent, 'setWindowTitle'):
                            new_title = self.get_window_title(self.current_year, self.current_race, self.current_session)
                            parent.setWindowTitle(new_title)
                            print(f"[SPEED_MDI] 🏷️ 視窗標題已更新為: {new_title}")
                        else:
                            print(f"[SPEED_MDI] ⚠️ 無法更新視窗標題 - 父視窗引用未設置")
                        
                        return True
                    else:
                        print(f"[SPEED_MDI] ❌ 圈速參數更新後數據重載失敗")
                        return False
                else:
                    print(f"[SPEED_MDI] ❌ 數據管理器未初始化")
                    return False
            else:
                print(f"[SPEED_MDI] ℹ️ 圈速參數未變化，保持現有數據")
                
                # 即使參數未變化，也確保視窗標題是正確的 - 使用統一的 get_window_title
                parent = getattr(self, 'parent_window', None)
                if parent and hasattr(parent, 'setWindowTitle'):
                    current_title = parent.windowTitle()
                    expected_title = self.get_window_title(self.current_year, self.current_race, self.current_session)
                    if current_title != expected_title:
                        parent.setWindowTitle(expected_title)
                        print(f"[SPEED_MDI] 🏷️ 同步視窗標題: {expected_title}")
                else:
                    print(f"[SPEED_MDI] ⚠️ 無法同步視窗標題 - 父視窗引用未設置")
                
                return True
                
        except Exception as e:
            print(f"[SPEED_MDI] ❌ 圈速參數更新失敗: {e}")
            import traceback
            traceback.print_exc()
            self.module_error.emit(f"圈速參數更新失敗: {str(e)}")
            return False
    
    def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
        """獲取視窗標題 - 兼容其他模組的接口"""
        # 如果提供了參數，使用傳入的參數；否則使用內部狀態
        use_year = year if year is not None else self.current_year
        use_race = race if race is not None else self.current_race
        use_session = session if session is not None else self.current_session
        
        # 簡化標題格式，只顯示基本信息
        title = f"⚡ 速度分析 - {use_year} {use_race} {use_session}"
        print(f"[SPEED_TITLE_DEBUG] 🏷️ 生成視窗標題: '{title}'")
        print(f"[SPEED_TITLE_DEBUG]   📊 參數詳情:")
        print(f"[SPEED_TITLE_DEBUG]     - 年份: {use_year}")
        print(f"[SPEED_TITLE_DEBUG]     - 賽事: {use_race}")
        print(f"[SPEED_TITLE_DEBUG]     - 賽段: {use_session}")
        return title
    
    def update_window_title(self) -> None:
        """更新視窗標題"""
        try:
            print(f"[SPEED_TITLE_DEBUG] 🔄 開始更新視窗標題...")
            print(f"[SPEED_TITLE_DEBUG] 📋 當前狀態檢查:")
            
            # 檢查 parent_window 屬性（MDI 子視窗引用）
            parent = getattr(self, 'parent_window', None)
            print(f"[SPEED_TITLE_DEBUG]   - parent_window 存在: {parent is not None}")
            
            if parent and hasattr(parent, 'setWindowTitle'):
                old_title = parent.windowTitle()
                print(f"[SPEED_TITLE_DEBUG]   - 舊標題: '{old_title}'")
                
                new_title = self.get_window_title(self.current_year, self.current_race, self.current_session)
                print(f"[SPEED_TITLE_DEBUG]   - 新標題: '{new_title}'")
                print(f"[SPEED_TITLE_DEBUG]   - 標題是否變化: {old_title != new_title}")
                
                parent.setWindowTitle(new_title)
                
                # 強制刷新視窗顯示
                parent.update()
                parent.repaint()
                
                # 驗證標題是否真的被設置
                actual_title = parent.windowTitle()
                print(f"[SPEED_TITLE_DEBUG]   - 設置後實際標題: '{actual_title}'")
                print(f"[SPEED_TITLE_DEBUG]   - 設置是否成功: {actual_title == new_title}")
                
                if actual_title == new_title:
                    print(f"[SPEED_TITLE_DEBUG] ✅ 視窗標題更新成功")
                else:
                    print(f"[SPEED_TITLE_DEBUG] ❌ 視窗標題更新可能失敗，嘗試延遲更新...")
                    print(f"[SPEED_TITLE_DEBUG]   預期: '{new_title}'")
                    print(f"[SPEED_TITLE_DEBUG]   實際: '{actual_title}'")
                    
                    # 嘗試延遲設置
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(100, lambda: self._delayed_title_update(new_title))
            else:
                print(f"[SPEED_TITLE_DEBUG] ⚠️ 無法更新視窗標題 - 父視窗引用未設置")
                print(f"[SPEED_TITLE_DEBUG]   📋 模組內部參數狀態:")
                print(f"[SPEED_TITLE_DEBUG]     - current_year: {getattr(self, 'current_year', 'NOT_SET')}")
                print(f"[SPEED_TITLE_DEBUG]     - current_race: {getattr(self, 'current_race', 'NOT_SET')}")
                print(f"[SPEED_TITLE_DEBUG]     - current_session: {getattr(self, 'current_session', 'NOT_SET')}")
                print(f"[SPEED_TITLE_DEBUG]     - driver1: {getattr(self, 'driver1', 'NOT_SET')}")
                print(f"[SPEED_TITLE_DEBUG]     - driver2: {getattr(self, 'driver2', 'NOT_SET')}")
        except Exception as e:
            print(f"[ERROR] [SPEED_TITLE_DEBUG] 更新視窗標題失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _delayed_title_update(self, title: str) -> None:
        """延遲標題更新 - 採用進站分析模式"""
        try:
            # 使用 parent_window 屬性而不是 parent() 方法
            parent = getattr(self, 'parent_window', None)
            if parent and hasattr(parent, 'setWindowTitle'):
                print(f"[SPEED_TITLE_DEBUG] 🔄 延遲標題更新: '{title}'")
                parent.setWindowTitle(title)
                parent.update()
                parent.repaint()
                
                # 再次驗證
                actual_title = parent.windowTitle()
                success = (actual_title == title)
                print(f"[SPEED_TITLE_DEBUG] 延遲更新結果: {success}, 實際標題: '{actual_title}'")
                
                if not success:
                    print(f"[ERROR] [SPEED_TITLE_DEBUG] ❌ 延遲更新也失敗了！可能是視窗引用問題")
                    print(f"[SPEED_TITLE_DEBUG] 視窗類型: {type(parent)}")
                    print(f"[SPEED_TITLE_DEBUG] 視窗是否可見: {parent.isVisible()}")
        except Exception as e:
            print(f"[ERROR] [SPEED_MDI] 延遲標題更新失敗: {e}")
    
    # 實現 IAnalysisModule 抽象方法
    @property
    def module_name(self) -> str:
        """模組名稱"""
        return "speed_analysis"
    
    @property
    def display_name(self) -> str:
        """顯示名稱"""
        return "速度分析"
    
    @property
    def description(self) -> str:
        """模組描述"""
        return "F1賽車速度分析模組，支援雙車手圈速對比"
    
    @property
    def version(self) -> str:
        """模組版本"""
        return "1.0.0"
    
    def get_widget(self):
        """獲取主要組件"""
        if hasattr(self, 'main_widget'):
            return self.main_widget
        else:
            # 如果主 widget 還沒創建，返回圖表組件作為後備
            return self.speed_chart_widget
    
    def get_default_size(self):
        """獲取預設尺寸"""
        return (900, 600)
    
    def load_data(self, **kwargs) -> bool:
        """載入數據 - 實現抽象方法"""
        try:
            year = str(kwargs.get('year', self.current_year))
            race = kwargs.get('race', self.current_race)
            session = kwargs.get('session', self.current_session)
            
            return self.data_manager.load_speed_data(
                year=year,
                race=race,
                session=session,
                driver1=kwargs.get('driver1', 'VER'),
                driver2=kwargs.get('driver2', 'VER'),
                lap1=kwargs.get('lap1', 1),
                lap2=kwargs.get('lap2', 1)
            )
        except Exception as e:
            print(f"[ERROR] [SPEED_MDI] load_data 失敗: {e}")
            return False
    
    def refresh_analysis(self) -> None:
        """刷新分析 - 實現抽象方法"""
        try:
            self.data_manager.load_speed_data(
                year=self.current_year,
                race=self.current_race,
                session=self.current_session,
                driver1="VER",
                driver2="VER",
                lap1=1,
                lap2=1
            )
        except Exception as e:
            print(f"[ERROR] [SPEED_MDI] refresh_analysis 失敗: {e}")
    
    def clear_data(self):
        """清除數據 - 實現抽象方法"""
        try:
            if self.speed_chart_widget:
                # 清除速度圖表數據
                self.speed_chart_widget.reset_data()
            print(f"[SPEED_MDI] 數據已清除")
        except Exception as e:
            print(f"[ERROR] [SPEED_MDI] clear_data 失敗: {e}")
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """獲取當前數據 - 實建抽象方法"""
        try:
            return {
                'module': 'speed_analysis',
                'year': self.current_year,
                'race': self.current_race,
                'session': self.current_session,
                'initialized': self._initialized,
                'data_loaded': self.data_manager is not None
            }
        except Exception as e:
            print(f"[ERROR] [SPEED_MDI] get_current_data 失敗: {e}")
            return None
    
    def receive_main_window_update_notification(self, param_type, value):
        """接收主視窗參數更新通知
        
        支援兩種調用方式：
        1. 主視窗格式: receive_main_window_update_notification(param_type, value)
        2. 直接參數格式: receive_main_window_update_notification(year=xxx, race=xxx, session=xxx)
        
        Args:
            param_type_or_year: 參數類型('year'/'race'/'session') 或直接的年份值
            value_or_race: 參數值 或直接的賽事名稱
            session: 賽段 (當使用直接參數格式時)
            **kwargs: 其他可能的參數
        """
        try:
            print(f"[SPEED_NOTIFICATION_DEBUG] ========== 收到主視窗更新通知 ==========")
            print(f"[SPEED_NOTIFICATION_DEBUG] � 原始參數:")
            print(f"[SPEED_NOTIFICATION_DEBUG]   - param_type: {param_type}")
            print(f"[SPEED_NOTIFICATION_DEBUG]   - value: {value}")
            
            # 簡化的參數處理
            # 直接處理參數更新
            if param_type == 'year':
                self.current_year = str(value)
                print(f"[UPDATE] 年份更新為: {self.current_year}")
            elif param_type == 'race':
                self.current_race = str(value)
                print(f"[UPDATE] 賽事更新為: {self.current_race}")
            elif param_type == 'session':
                self.current_session = str(value)
                print(f"[UPDATE] 場次更新為: {self.current_session}")
            
            print(f"[SPEED_NOTIFICATION_DEBUG] 📊 當前模組狀態:")
            print(f"[SPEED_NOTIFICATION_DEBUG]   - 當前年份: {self.current_year}")
            print(f"[SPEED_NOTIFICATION_DEBUG]   - 當前賽事: {self.current_race}")
            print(f"[SPEED_NOTIFICATION_DEBUG]   - 當前賽段: {self.current_session}")
            print(f"[SPEED_NOTIFICATION_DEBUG]   - 當前車手: {self.driver1} vs {self.driver2}")
            print(f"[SPEED_NOTIFICATION_DEBUG]   - 當前圈數: 第{self.lap1}圈 vs 第{self.lap2}圈")
            
            # [TOOL] 更新窗口標題（如果有父窗口）- 使用統一的 get_window_title
            parent = getattr(self, 'parent_window', None)
            if parent and hasattr(parent, 'setWindowTitle'):
                title = self.get_window_title(self.current_year, self.current_race, self.current_session)
                parent.setWindowTitle(title)
                print(f"[TITLE] 窗口標題更新為: {title}")
            else:
                print(f"[WARNING] 無法更新視窗標題 - 父視窗引用未設置")
            
            # 重新載入數據
            if self.data_manager:
                print(f"[REFRESH] 重新載入速度數據...")
                self.data_manager.load_speed_data(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session,
                    driver1=self.driver1,
                    driver2=self.driver2,
                    lap1=self.lap1,
                    lap2=self.lap2
                )
            print(f"[OK] [NOTIFICATION] ⚡ 速度分析模組內容更新成功")
                
        except Exception as e:
            print(f"[ERROR] [NOTIFICATION] ⚡ 速度分析模組內容更新失敗: {e}")
            import traceback
            traceback.print_exc()

    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        """匯出數據 - 實現抽象方法"""
        try:
            print(f"[SPEED_MDI] 匯出數據功能尚未實現 (路徑: {export_path}, 格式: {export_format})")
            return False
        except Exception as e:
            print(f"[ERROR] [SPEED_MDI] export_data 失敗: {e}")
            return False
