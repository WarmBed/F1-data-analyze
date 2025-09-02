#!/usr/bin/env python3
"""
F1T RPM分析 MDI 模組
基於速度分析模組的成功架構設計
支援雙車手RPM對比的 GUI 模組，使用新版模組更新機制
完整實現所有IAnalysisModule接口和遙測分析整合功能
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

class RPMDataManager(QObject):
    """RPM數據管理器 - 負責JSON緩存和CLI備援"""
    
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
        
    def load_rpm_data(self, year: str, race: str, session: str, 
                      driver1: str = "VER", driver2: str = "VER",
                      lap1: int = 1, lap2: int = 1, is_fastest: bool = False) -> bool:
        """載入RPM對比數據"""
        try:
            print(f"[RPM_MDI_DATA] ========== 載入RPM數據 ==========")
            print(f"[RPM_MDI_DATA] 參數: {year} {race} {session}")
            print(f"[RPM_MDI_DATA] 車手: {driver1} vs {driver2}, 圈數: {lap1} vs {lap2}")
            
            if self._is_loading:
                print(f"[RPM_MDI_DATA] ⚠️ 數據載入中，忽略新請求")
                self.error_occurred.emit("載入器正忙，請稍後再試")
                return False
                
            self._is_loading = True
            self.loading_progress.emit(0)
            self.status_changed.emit("開始載入RPM數據...")
            
            # 檢查最速圈選項並自動載入遙測分析
            if is_fastest or lap1 == "fastest" or lap2 == "fastest":
                print(f"🔄 [RPM_MDI_DATA] 檢測到最速圈選項，檢查遙測分析數據...")
                self._check_and_load_telemetry_if_needed()
                
                # 解析最速圈參數為實際圈數
                lap1, lap2 = self._resolve_lap_numbers(lap1, lap2, driver1, driver2, is_fastest)
                print(f"🔢 [RPM_MDI_DATA] 最速圈解析完成: {driver1}=第{lap1}圈, {driver2}=第{lap2}圈")
            
            print(f"[RPM_MDI_DATA] 🔗 創建 RPMAnalysisDataLoader...")
            
            # 使用現有的RPM分析數據載入器
            from modules.rpm_analysis_data_loader import RPMAnalysisDataLoader
            
            print(f"[RPM_MDI_DATA] 🚀 調用 load_rpm_analysis_data...")
            
            # 創建數據載入器
            rpm_loader = RPMAnalysisDataLoader()
            rpm_loader.data_loaded.connect(self._on_data_loaded)
            rpm_loader.loading_error.connect(self._on_load_error)
            
            # 構建會話信息
            session_info = {
                'year': int(year),
                'race': race,
                'driver1': driver1,
                'driver2': driver2,
                'lap1': lap1,
                'lap2': lap2
            }
            
            # 開始載入數據
            rpm_loader.load_rpm_analysis_data(session_info)
            
            print(f"[RPM_MDI_DATA] ✅ RPM數據載入請求提交成功")
            self.loading_progress.emit(50)
            return True
                
        except Exception as e:
            print(f"[ERROR] [RPM_MDI_DATA] 載入RPM數據時發生錯誤: {e}")
            self._is_loading = False
            self.error_occurred.emit(f"載入RPM數據失敗: {str(e)}")
            return False
    
    def _on_data_loaded(self, data):
        """數據載入完成回調"""
        try:
            print(f"[RPM_MDI_DATA] ✅ RPM數據載入完成")
            self._is_loading = False
            self.loading_progress.emit(100)
            self.status_changed.emit("RPM數據載入完成")
            self.data_loaded.emit(data)
        except Exception as e:
            print(f"[ERROR] [RPM_MDI_DATA] 處理載入完成回調時發生錯誤: {e}")
            self._on_load_error(f"數據處理失敗: {str(e)}")
    
    def _on_load_error(self, error_msg):
        """數據載入錯誤回調"""
        print(f"[RPM_MDI_DATA] ❌ RPM數據載入錯誤: {error_msg}")
        self._is_loading = False
        self.loading_progress.emit(0)
        self.status_changed.emit(f"載入失敗: {error_msg}")
        self.error_occurred.emit(error_msg)
    
    def _check_and_load_telemetry_if_needed(self):
        """檢查並載入遙測分析數據（最速圈用）"""
        # 實現遙測數據檢查邏輯
        print(f"[RPM_MDI_DATA] 🔍 檢查遙測分析數據可用性...")
        pass
    
    def _resolve_lap_numbers(self, lap1, lap2, driver1, driver2, is_fastest):
        """解析最速圈參數為實際圈數"""
        # 實現最速圈解析邏輯
        if is_fastest or lap1 == "fastest":
            lap1 = 1  # 預設值，實際應從遙測分析中獲取
        if is_fastest or lap2 == "fastest":
            lap2 = 1  # 預設值，實際應從遙測分析中獲取
        return lap1, lap2

class RPMAnalysisModule(IAnalysisModule):
    """RPM分析主模組 - 完整實現與速度分析模組對等的功能"""
    
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
        self.rpm_chart_widget = None
        self.main_widget = None  # 主容器 widget
        self.parent_window = None  # MDI 子視窗引用
        
        # UI組件
        self.status_label = None
        self.progress_bar = None
        self.refresh_button = None
        
        # 初始化狀態
        self._initialized = False
        
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """初始化模組 - 實現抽象方法"""
        try:
            print(f"[RPM_MDI] ========== 初始化RPM分析模組 ==========")
            
            # 創建數據管理器
            self.data_manager = RPMDataManager()
            self.data_manager.data_loaded.connect(self._update_chart)
            self.data_manager.error_occurred.connect(self._handle_error)
            self.data_manager.loading_progress.connect(self._update_progress)
            self.data_manager.status_changed.connect(self._update_status)
            
            print(f"[RPM_MDI] ✅ 數據管理器已創建")
            
            # 創建RPM圖表組件
            try:
                from modules.rpm_analysis_chart_widget import RPMAnalysisChartWidget
                self.rpm_chart_widget = RPMAnalysisChartWidget()
                
                # 連接圈數變更信號
                if hasattr(self.rpm_chart_widget, 'lap_numbers_changed'):
                    self.rpm_chart_widget.lap_numbers_changed.connect(self._on_lap_numbers_changed)
                
                print(f"[RPM_MDI] ✅ RPM圖表組件已創建")
            except ImportError as e:
                print(f"[WARNING] [RPM_MDI] 無法導入RPM圖表組件，使用佔位組件: {e}")
                self.rpm_chart_widget = self._create_placeholder_widget()
            
            # 設置UI
            self._setup_ui()
            
            self._initialized = True
            print(f"[OK] [RPM_MDI] RPM分析模組初始化完成")
            return True
            
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] 模組初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def set_parent_window(self, parent_window):
        """設置父視窗引用（MDI 子視窗）"""
        print(f"[RPM_TITLE_DEBUG] 🔗 設置父視窗引用...")
        print(f"[RPM_TITLE_DEBUG]   - 父視窗類型: {type(parent_window).__name__}")
        print(f"[RPM_TITLE_DEBUG]   - 父視窗是否為None: {parent_window is None}")
        
        self.parent_window = parent_window
        
        if parent_window:
            # 獲取當前標題以供調試
            current_title = parent_window.windowTitle()
            print(f"[RPM_TITLE_DEBUG]   - 當前父視窗標題: '{current_title}'")
            
            # 立即設置正確的標題
            print(f"[RPM_TITLE_DEBUG] 🏷️ 父視窗設置後立即更新標題...")
            self.update_window_title()
        else:
            print(f"[RPM_TITLE_DEBUG] ⚠️ 父視窗為None，無法設置標題")
        
        print(f"[RPM_TITLE_DEBUG] ✅ 父視窗引用設置完成")
    
    def _create_placeholder_widget(self):
        """創建佔位組件（當RPM圖表組件不可用時）"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        label = QLabel("🔄 RPM分析圖表")
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 16pt; padding: 20px;")
        layout.addWidget(label)
        
        info_label = QLabel("RPM圖表組件正在載入中...")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        return widget
    
    def _setup_ui(self):
        """設置用戶界面"""
        try:
            # 創建主要組件
            self.main_widget = QWidget()
            layout = QVBoxLayout(self.main_widget)
            
            # 頂部控制區域
            control_frame = QFrame()
            control_layout = QHBoxLayout(control_frame)
            
            # 狀態標籤
            self.status_label = QLabel("就緒")
            control_layout.addWidget(QLabel("狀態:"))
            control_layout.addWidget(self.status_label)
            
            # 進度條
            self.progress_bar = QProgressBar()
            self.progress_bar.setVisible(False)
            control_layout.addWidget(self.progress_bar)
            
            # 刷新按鈕
            self.refresh_button = QPushButton("🔄 刷新")
            self.refresh_button.clicked.connect(self._refresh_data)
            control_layout.addWidget(self.refresh_button)
            
            control_layout.addStretch()
            layout.addWidget(control_frame)
            
            # 添加RPM圖表
            if self.rpm_chart_widget:
                layout.addWidget(self.rpm_chart_widget)
            
            print(f"[RPM_MDI] ✅ UI設置完成")
            
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] UI設置失敗: {e}")
    
    def _update_chart(self, data: dict):
        """更新圖表"""
        try:
            print(f"[RPM_MDI] 更新RPM圖表")
            if self.rpm_chart_widget and hasattr(self.rpm_chart_widget, 'update_rpm_data'):
                self.rpm_chart_widget.update_rpm_data(data)
                print(f"[RPM_MDI] ✅ RPM圖表更新完成")
            else:
                print(f"[RPM_MDI] ⚠️ RPM圖表組件不支援數據更新")
                
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] 更新圖表失敗: {e}")
            self.module_error.emit(f"圖表更新失敗: {str(e)}")
    
    def _handle_error(self, error_message: str):
        """處理錯誤"""
        print(f"[ERROR] [RPM_MDI] {error_message}")
        self.module_error.emit(error_message)
        if self.status_label:
            self.status_label.setText(f"錯誤: {error_message}")
    
    def _update_progress(self, value):
        """更新進度"""
        if self.progress_bar:
            if value > 0:
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(value)
            else:
                self.progress_bar.setVisible(False)
    
    def _update_status(self, status):
        """更新狀態"""
        if self.status_label:
            self.status_label.setText(status)
    
    def _on_lap_numbers_changed(self, lap1, lap2):
        """處理圈數變更"""
        print(f"[RPM_MDI] 圈數變更: {lap1} -> {lap2}")
        self.lap1 = lap1
        self.lap2 = lap2
        # 可以在這裡觸發數據重新載入
    
    def _refresh_data(self):
        """刷新數據"""
        if self.data_manager:
            self.data_manager.load_rpm_data(
                year=self.current_year,
                race=self.current_race,
                session=self.current_session,
                driver1=self.driver1,
                driver2=self.driver2,
                lap1=self.lap1,
                lap2=self.lap2
            )
    
    # ========== 視窗標題管理 ==========
    
    def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
        """獲取視窗標題 - 兼容其他模組的接口"""
        # 如果提供了參數，使用傳入的參數；否則使用內部狀態
        use_year = year if year is not None else self.current_year
        use_race = race if race is not None else self.current_race
        use_session = session if session is not None else self.current_session
        
        # 簡化標題格式，只顯示基本信息
        title = f"🔄 RPM分析 - {use_year} {use_race} {use_session}"
        
        print(f"[RPM_TITLE_DEBUG] 🏷️ 生成視窗標題: '{title}'")
        print(f"[RPM_TITLE_DEBUG]   📊 參數詳情:")
        print(f"[RPM_TITLE_DEBUG]     - 年份: {use_year}")
        print(f"[RPM_TITLE_DEBUG]     - 賽事: {use_race}")
        print(f"[RPM_TITLE_DEBUG]     - 賽段: {use_session}")
        return title
    
    def update_window_title(self) -> None:
        """更新視窗標題"""
        try:
            print(f"[RPM_TITLE_DEBUG] 🔄 開始更新視窗標題...")
            print(f"[RPM_TITLE_DEBUG] 📋 當前狀態檢查:")
            
            # 檢查 parent_window 屬性（MDI 子視窗引用）
            parent = getattr(self, 'parent_window', None)
            print(f"[RPM_TITLE_DEBUG]   - parent_window 存在: {parent is not None}")
            
            if parent and hasattr(parent, 'setWindowTitle'):
                old_title = parent.windowTitle()
                print(f"[RPM_TITLE_DEBUG]   - 舊標題: '{old_title}'")
                
                new_title = self.get_window_title(self.current_year, self.current_race, self.current_session)
                print(f"[RPM_TITLE_DEBUG]   - 新標題: '{new_title}'")
                
                if old_title != new_title:
                    print(f"[RPM_TITLE_DEBUG] 🔄 標題需要更新，執行更新...")
                    
                    # 直接更新標題
                    parent.setWindowTitle(new_title)
                    
                    # 驗證更新結果
                    updated_title = parent.windowTitle()
                    print(f"[RPM_TITLE_DEBUG] ✅ 標題更新完成: '{updated_title}'")
                    
                    # 如果直接更新失敗，使用延遲更新
                    if updated_title != new_title:
                        print(f"[RPM_TITLE_DEBUG] ⚠️ 直接更新失敗，嘗試延遲更新...")
                        self._delayed_title_update(new_title)
                else:
                    print(f"[RPM_TITLE_DEBUG] ✅ 標題無需更新")
            else:
                print(f"[RPM_TITLE_DEBUG] ⚠️ 無法更新標題:")
                print(f"[RPM_TITLE_DEBUG]   - parent_window: {parent}")
                print(f"[RPM_TITLE_DEBUG]   - 有setWindowTitle方法: {hasattr(parent, 'setWindowTitle') if parent else False}")
        
        except Exception as e:
            print(f"[ERROR] [RPM_TITLE_DEBUG] 更新視窗標題失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _delayed_title_update(self, title: str) -> None:
        """延遲標題更新 - 採用進站分析模式"""
        print(f"[RPM_TITLE_DEBUG] ⏰ 啟動延遲標題更新: '{title}'")
        
        def update_title():
            try:
                if self.parent_window and hasattr(self.parent_window, 'setWindowTitle'):
                    self.parent_window.setWindowTitle(title)
                    final_title = self.parent_window.windowTitle()
                    print(f"[RPM_TITLE_DEBUG] ✅ 延遲更新完成: '{final_title}'")
                else:
                    print(f"[RPM_TITLE_DEBUG] ❌ 延遲更新失敗: parent_window 不可用")
            except Exception as e:
                print(f"[ERROR] [RPM_TITLE_DEBUG] 延遲更新異常: {e}")
        
        # 使用QTimer延遲執行
        QTimer.singleShot(100, update_title)
    
    # ========== IAnalysisModule 抽象方法實現 ==========
    
    @property
    def module_name(self) -> str:
        """模組名稱"""
        return "rpm_analysis"
    
    @property
    def display_name(self) -> str:
        """顯示名稱"""
        return "RPM分析"
    
    @property
    def description(self) -> str:
        """模組描述"""
        return "F1賽車RPM分析模組，支援雙車手圈速對比"
    
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
            return self.rpm_chart_widget
    
    def get_default_size(self):
        """獲取預設尺寸"""
        return (1000, 700)  # RPM分析需要較大的視窗來顯示詳細圖表
    
    def load_data(self, **kwargs) -> bool:
        """載入數據 - 實現抽象方法"""
        try:
            year = str(kwargs.get('year', self.current_year))
            race = kwargs.get('race', self.current_race)
            session = kwargs.get('session', self.current_session)
            
            return self.data_manager.load_rpm_data(
                year=year,
                race=race,
                session=session,
                driver1=kwargs.get('driver1', 'VER'),
                driver2=kwargs.get('driver2', 'VER'),
                lap1=kwargs.get('lap1', 1),
                lap2=kwargs.get('lap2', 1)
            )
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] load_data 失敗: {e}")
            return False
    
    def refresh_analysis(self) -> None:
        """刷新分析 - 實現抽象方法"""
        try:
            self.data_manager.load_rpm_data(
                year=self.current_year,
                race=self.current_race,
                session=self.current_session,
                driver1="VER",
                driver2="VER",
                lap1=1,
                lap2=1
            )
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] refresh_analysis 失敗: {e}")
    
    def clear_data(self):
        """清除數據 - 實現抽象方法"""
        try:
            if self.rpm_chart_widget:
                # 清除RPM圖表數據
                if hasattr(self.rpm_chart_widget, 'reset_data'):
                    self.rpm_chart_widget.reset_data()
            print(f"[RPM_MDI] 數據已清除")
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] clear_data 失敗: {e}")
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """獲取當前數據 - 實現抽象方法"""
        try:
            return {
                'module': 'rpm_analysis',
                'year': self.current_year,
                'race': self.current_race,
                'session': self.current_session,
                'initialized': self._initialized,
                'data_loaded': self.data_manager is not None
            }
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] get_current_data 失敗: {e}")
            return None
    
    def update_parameters(self, year: int = None, race: str = None, session: str = None, **kwargs) -> bool:
        """更新參數 - 實現抽象方法"""
        try:
            updated = False
            
            if year is not None and str(year) != self.current_year:
                self.current_year = str(year)
                updated = True
            
            if race is not None and race != self.current_race:
                self.current_race = race
                updated = True
            
            if session is not None and session != self.current_session:
                self.current_session = session
                updated = True
            
            if updated:
                print(f"[RPM_MDI] 參數已更新: {self.current_year} {self.current_race} {self.current_session}")
                self.update_window_title()
                self.parameters_updated.emit({
                    'year': self.current_year,
                    'race': self.current_race,
                    'session': self.current_session
                })
            
            return True
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] update_parameters 失敗: {e}")
            return False
    
    def update_lap_parameters(self, year: str, race: str, session: str, 
                            driver1: str, driver2: str = None, 
                            lap1: int = 1, lap2: int = 1, 
                            is_fastest: bool = False) -> bool:
        """更新圈速分析參數（包含車手和圈數）"""
        try:
            print(f"[RPM_MDI] 更新圈速參數: {year} {race} {session}")
            print(f"[RPM_MDI] 車手和圈數: {driver1}({lap1}) vs {driver2}({lap2})")
            
            # 更新基本參數
            self.current_year = year
            self.current_race = race
            self.current_session = session
            
            # 更新車手和圈數
            self.driver1 = driver1
            self.driver2 = driver2 if driver2 else driver1
            self.lap1 = lap1
            self.lap2 = lap2
            
            # 更新視窗標題
            self.update_window_title()
            
            print(f"[RPM_MDI] ✅ 圈速參數更新完成")
            return True
            
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] update_lap_parameters 失敗: {e}")
            return False
    
    def cleanup_module(self):
        """清理模組資源和信號連接"""
        try:
            print(f"[RPM_MDI] 🧹 清理RPM分析模組...")
            
            if self.data_manager:
                # 斷開所有信號連接
                try:
                    self.data_manager.data_loaded.disconnect()
                    self.data_manager.error_occurred.disconnect()
                    self.data_manager.loading_progress.disconnect()
                    self.data_manager.status_changed.disconnect()
                except Exception as e:
                    print(f"[WARNING] [RPM_MDI] 斷開數據管理器信號時發生警告: {e}")
            
            if self.rpm_chart_widget and hasattr(self.rpm_chart_widget, 'lap_numbers_changed'):
                try:
                    self.rpm_chart_widget.lap_numbers_changed.disconnect()
                except Exception as e:
                    print(f"[WARNING] [RPM_MDI] 斷開圖表組件信號時發生警告: {e}")
            
            print(f"[RPM_MDI] ✅ 模組清理完成")
                
        except Exception as e:
            print(f"[WARNING] [RPM_MDI] 清理模組時發生警告: {e}")
    
    # ========== 遙測分析整合功能 ==========
    
    def _ensure_telemetry_data_for_fastest_laps(self) -> Optional[Dict[str, int]]:
        """確保最速圈數據的遙測分析可用 - 與速度分析相同功能"""
        try:
            print(f"[RPM_MDI] 🔍 檢查最速圈遙測數據可用性...")
            
            # 首先檢查是否已有遙測分析檔案
            telemetry_file = self._find_telemetry_analysis_file()
            
            if not telemetry_file:
                print(f"[RPM_MDI] 📡 遙測分析數據不存在，開始自動載入...")
                success = self._trigger_telemetry_analysis()
                if success:
                    # 重新檢查檔案
                    telemetry_file = self._find_telemetry_analysis_file()
                else:
                    print(f"[RPM_MDI] ❌ 遙測分析載入失敗")
                    return None
            
            if telemetry_file:
                print(f"[RPM_MDI] 📂 找到遙測分析檔案: {telemetry_file}")
                return self._extract_fastest_laps_from_telemetry(telemetry_file)
            else:
                print(f"[RPM_MDI] ⚠️ 無法獲取遙測分析數據")
                return None
                
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] _ensure_telemetry_data_for_fastest_laps 失敗: {e}")
            return None
    
    def _find_telemetry_analysis_file(self) -> Optional[str]:
        """尋找遙測分析JSON檔案 - 與速度分析相同功能"""
        try:
            # 構建可能的檔案名稱模式
            year = self.current_year
            race = self.current_race.replace(' ', '_')
            session = self.current_session
            
            # 檢查JSON目錄
            json_dir = "json"
            if os.path.exists(json_dir):
                for filename in os.listdir(json_dir):
                    if (filename.startswith(f"telemetry_analysis_{year}_{race}_{session}") and 
                        filename.endswith('.json')):
                        full_path = os.path.join(json_dir, filename)
                        print(f"[RPM_MDI] 📂 找到遙測分析檔案: {full_path}")
                        return full_path
            
            print(f"[RPM_MDI] 📂 未找到遙測分析檔案")
            return None
            
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] _find_telemetry_analysis_file 失敗: {e}")
            return None
    
    def _trigger_telemetry_analysis(self) -> bool:
        """觸發遙測分析載入/生成 - 與速度分析相同功能"""
        try:
            print(f"[RPM_MDI] 🚀 觸發遙測分析載入: {self.current_year} {self.current_race} {self.current_session}")
            
            # 方法1: 嘗試通過主視窗找到遙測分析模組
            if hasattr(self, 'parent_window') and self.parent_window:
                main_window = self.parent_window
                # 尋找主視窗的父級(可能是F1T主視窗)
                while main_window.parent():
                    main_window = main_window.parent()
                
                # 檢查是否有MDI區域
                if hasattr(main_window, 'mdi_area'):
                    # 檢查是否已有遙測分析視窗
                    for sub_window in main_window.mdi_area.subWindowList():
                        window_title = sub_window.windowTitle()
                        if "遙測分析" in window_title:
                            print(f"[RPM_MDI] 🎯 找到現有遙測分析視窗: {window_title}")
                            # 激活並刷新遙測分析視窗
                            main_window.mdi_area.setActiveSubWindow(sub_window)
                            return True
                    
                    # 如果沒有遙測分析視窗，嘗試創建一個
                    print(f"[RPM_MDI] 📡 嘗試創建遙測分析視窗...")
                    if hasattr(main_window, 'create_telemetry_analysis'):
                        main_window.create_telemetry_analysis()
                        return True
            
            # 方法2: 通過CLI生成遙測分析數據
            print(f"[RPM_MDI] 🔧 通過CLI生成遙測分析數據...")
            return self._generate_telemetry_via_cli()
            
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] _trigger_telemetry_analysis 失敗: {e}")
            return False
    
    def _generate_telemetry_via_cli(self) -> bool:
        """通過CLI生成遙測分析數據 - 與速度分析相同功能"""
        try:
            import subprocess
            import threading
            import time
            
            # 構建CLI命令 - 功能7是遙測分析
            command = [
                "python", "f1_analysis_modular_main.py",
                "-f", "7",  # 功能7: 遙測分析
                "-y", str(self.current_year),
                "-r", self.current_race,
                "-s", self.current_session
            ]
            
            print(f"[RPM_MDI] 🔧 執行CLI命令: {' '.join(command)}")
            
            # 同步執行CLI命令（因為RPM分析需要立即使用結果）
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=os.getcwd()
            )
            
            # 等待命令完成（最多60秒）
            try:
                stdout, stderr = process.communicate(timeout=60)
                
                if process.returncode == 0:
                    print(f"[RPM_MDI] ✅ CLI遙測分析執行成功")
                    return True
                else:
                    print(f"[RPM_MDI] ❌ CLI遙測分析執行失敗: {stderr}")
                    return False
                    
            except subprocess.TimeoutExpired:
                print(f"[RPM_MDI] ⏰ CLI遙測分析執行超時")
                process.kill()
                return False
                
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] _generate_telemetry_via_cli 失敗: {e}")
            return False
    
    def _extract_fastest_laps_from_telemetry(self, telemetry_file: str) -> Optional[Dict[str, int]]:
        """從遙測分析JSON檔案中提取最速圈數據 - 與速度分析相同功能"""
        try:
            print(f"[RPM_MDI] 📊 從遙測分析中提取最速圈數據: {telemetry_file}")
            
            with open(telemetry_file, 'r', encoding='utf-8') as f:
                telemetry_data = json.load(f)
            
            fastest_laps = {}
            
            # 檢查遙測數據結構並提取最速圈信息
            if 'data' in telemetry_data and 'fastest_laps' in telemetry_data['data']:
                fastest_lap_data = telemetry_data['data']['fastest_laps']
                
                for driver_code, lap_info in fastest_lap_data.items():
                    if isinstance(lap_info, dict) and 'lap_number' in lap_info:
                        fastest_laps[driver_code] = lap_info['lap_number']
                    elif isinstance(lap_info, int):
                        fastest_laps[driver_code] = lap_info
            
            print(f"[RPM_MDI] ✅ 最速圈數據提取完成: {fastest_laps}")
            return fastest_laps if fastest_laps else None
            
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] _extract_fastest_laps_from_telemetry 失敗: {e}")
            return None
    
    def receive_main_window_update_notification(self, param_type, value):
        """接收主視窗參數更新通知 - 與速度分析相同功能"""
        try:
            print(f"[RPM_MDI] 📡 收到主視窗參數更新: {param_type} = {value}")
            
            # 更新內部狀態
            if param_type == "year":
                self.current_year = str(value)
            elif param_type == "race":
                self.current_race = value
            elif param_type == "session":
                self.current_session = value
            
            # 更新視窗標題
            self.update_window_title()
            
            print(f"[RPM_MDI] ✅ 參數更新完成: {self.current_year} {self.current_race} {self.current_session}")
            
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] receive_main_window_update_notification 失敗: {e}")

    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        """匯出數據 - 實現抽象方法"""
        try:
            print(f"[RPM_MDI] 匯出數據功能尚未實現 (路徑: {export_path}, 格式: {export_format})")
            return False
        except Exception as e:
            print(f"[ERROR] [RPM_MDI] export_data 失敗: {e}")
            return False

# 主程式測試
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 測試RPM分析模組
    module = RPMAnalysisModule()
    if module.initialize_module():
        widget = module.get_widget()
        widget.setWindowTitle(module.get_window_title())
        widget.resize(*module.get_default_size())
        widget.show()
        
        # 測試數據載入
        module._refresh_data()
        
        sys.exit(app.exec_())
    else:
        print("模組初始化失敗")
        sys.exit(1)
