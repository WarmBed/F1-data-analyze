#!/usr/bin/env python3
"""
F1T 油門分析模組 (MDI)
====================

主要功能:
- 油門數據載入與處理
- 雙車手油門對比分析
- 與主程式參數同步
- 實現 IAnalysisModule 介面
- 完全參照速度分析模組架構

Author: F1T Team
Date: 2025-09-04
Version: 2.0.0 (架構重構版)
"""

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import os
import json
import glob
import subprocess
import threading
import time
from typing import Optional, Dict, Any

# 導入分析模組介面
from modules.gui.interfaces.analysis_module import IAnalysisModule

from core.logger import get_logger
logger = get_logger(__name__)

class ThrottleDataManager(QObject):
    """油門數據管理器 - 參照 SpeedDataManager 架構"""
    
    # 信號定義
    data_loaded = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_loading = False
    
    def load_throttle_data(self, year: str, race: str, session: str,
                          driver1: str, driver2: str = None,
                          lap1: int = 1, lap2: int = 1, is_fastest_lap: bool = False) -> bool:
        """載入油門數據 - 參照速度分析模組"""
        try:
            logger.debug(f"[THROTTLE_DATA_MANAGER] ========== 載入油門數據 ==========")
            logger.debug(f"[THROTTLE_DATA_MANAGER] 📊 基本參數: {year} {race} {session}")
            logger.debug(f"[THROTTLE_DATA_MANAGER] 🏎️ 車手參數: {driver1} vs {driver2}")
            logger.debug(f"[THROTTLE_DATA_MANAGER] 🏁 圈數參數: 第{lap1}圈 vs 第{lap2}圈")
            
            if self._is_loading:
                logger.warning(f"[THROTTLE_DATA_MANAGER] ⚠️ 數據載入中，跳過重複請求")
                return False
            
            self._is_loading = True
            
            # 解析圈數參數（處理最速圈）
            resolved_lap1, resolved_lap2 = self._resolve_lap_numbers(
                lap1, lap2, driver1, driver2, is_fastest_lap
            )
            
            # 在背景線程中載入數據
            worker_thread = threading.Thread(
                target=self._load_data_in_background,
                args=(year, race, session, driver1, driver2, resolved_lap1, resolved_lap2)
            )
            worker_thread.daemon = True
            worker_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"[THROTTLE_DATA_MANAGER] 載入油門數據失敗: {e}")
            self._is_loading = False
            self.error_occurred.emit(f"載入油門數據失敗: {str(e)}")
            return False
    
    def _load_data_in_background(self, year: str, race: str, session: str,
                                driver1: str, driver2: str, lap1: int, lap2: int):
        """在背景線程中載入數據"""
        try:
            # 模擬油門數據載入過程
            logger.debug(f"[THROTTLE_DATA_MANAGER] 🔄 背景載入油門數據...")
            time.sleep(1)  # 模擬載入時間
            
            # 構建模擬數據
            data = {
                'metadata': {
                    'year': year,
                    'race': race,
                    'session': session,
                    'drivers': [
                        {
                            'code': driver1,
                            'lap_time': '1:23.456',
                            'compound': 'MEDIUM',
                            'lap_number': lap1
                        }
                    ]
                },
                'throttle_data': {
                    'driver1': driver1,
                    'driver2': driver2,
                    'lap1': lap1,
                    'lap2': lap2
                }
            }
            
            if driver2 and driver2 != driver1:
                data['metadata']['drivers'].append({
                    'code': driver2,
                    'lap_time': '1:23.789',
                    'compound': 'SOFT',
                    'lap_number': lap2
                })
            
            # 發送數據載入完成信號
            self._on_data_loaded(data)
            
        except Exception as e:
            logger.error(f"[THROTTLE_DATA_MANAGER] 背景載入失敗: {e}")
            self._on_load_error(f"背景載入失敗: {str(e)}")
    
    def _get_fastest_lap_number(self, driver: str) -> int:
        """獲取車手最速圈數 - 參照速度分析模組邏輯"""
        try:
            logger.debug(f"[THROTTLE_DATA_MANAGER] 🏁 獲取 {driver} 最速圈數據...")
            
            # 搜尋遙測分析檔案
            telemetry_patterns = [
                f"json/telemetry_analysis_*.json",
                f"json_exports/telemetry_analysis_*.json"
            ]
            
            telemetry_file = None
            for pattern in telemetry_patterns:
                matching_files = glob.glob(pattern)
                if matching_files:
                    telemetry_file = matching_files[0]
                    logger.debug(f"📁 [THROTTLE_DATA_MANAGER] 找到遙測檔案: {telemetry_file}")
                    break
            
            if not telemetry_file:
                logger.error(f"[THROTTLE_DATA_MANAGER] 找不到遙測分析檔案，使用預設圈數 1")
                return 1
            
            # 讀取並解析遙測分析數據
            with open(telemetry_file, 'r', encoding='utf-8') as f:
                telemetry_data = json.load(f)
            
            logger.debug(f"[THROTTLE_DATA_MANAGER] 遙測檔案讀取成功，開始解析最速圈數據...")
            
            # 提取最速圈數據
            fastest_lap_num = None
            
            # 格式1: data.all_drivers_telemetry[driver].fastest_lap
            if 'data' in telemetry_data and 'all_drivers_telemetry' in telemetry_data['data']:
                driver_data = telemetry_data['data']['all_drivers_telemetry'].get(driver)
                if driver_data and 'fastest_lap' in driver_data:
                    fastest_lap_num = driver_data['fastest_lap'].get('lap_number')
                    if fastest_lap_num:
                        logger.info(f"[THROTTLE_DATA_MANAGER] 從格式1找到 {driver} 最速圈: 第{fastest_lap_num}圈")
                        return int(fastest_lap_num)
            
            # 格式2: data.fastest_laps中的列表
            if 'data' in telemetry_data and 'fastest_laps' in telemetry_data['data']:
                for fastest_data in telemetry_data['data']['fastest_laps']:
                    if fastest_data.get('driver') == driver:
                        fastest_lap_num = fastest_data.get('lap_number')
                        if fastest_lap_num:
                            logger.info(f"[THROTTLE_DATA_MANAGER] 從格式2找到 {driver} 最速圈: 第{fastest_lap_num}圈")
                            return int(fastest_lap_num)
            
            logger.warning(f"[THROTTLE_DATA_MANAGER] 無法找到 {driver} 的最速圈數據，使用預設圈數 1")
            return 1
            
        except Exception as e:
            logger.error(f"[THROTTLE_DATA_MANAGER] 解析最速圈數據時發生錯誤: {e}")
            return 1
    
    def _resolve_lap_numbers(self, lap1, lap2, driver1, driver2, is_fastest):
        """解析圈數參數，將'fastest'轉換為實際圈數"""
        try:
            resolved_lap1 = lap1
            resolved_lap2 = lap2
            
            # 處理lap1
            if lap1 == "fastest" or is_fastest:
                logger.debug(f"[THROTTLE_DATA_MANAGER] 解析 {driver1} 的最速圈...")
                resolved_lap1 = self._get_fastest_lap_number(driver1)
                
            # 處理lap2
            if lap2 == "fastest" or is_fastest:
                logger.debug(f"[THROTTLE_DATA_MANAGER] 解析 {driver2} 的最速圈...")
                resolved_lap2 = self._get_fastest_lap_number(driver2)
            
            logger.debug(f"[THROTTLE_DATA_MANAGER] 圈數解析結果: {driver1}=第{resolved_lap1}圈, {driver2}=第{resolved_lap2}圈")
            
            return int(resolved_lap1), int(resolved_lap2)
            
        except Exception as e:
            logger.error(f"[THROTTLE_DATA_MANAGER] 解析圈數時發生錯誤: {e}")
            return 1, 1
    
    def _on_data_loaded(self, data: dict):
        """處理數據載入完成"""
        try:
            logger.debug(f"[THROTTLE_DATA_MANAGER] 數據載入完成")
            self._is_loading = False
            self.data_loaded.emit(data)
        except Exception as e:
            logger.error(f"[THROTTLE_DATA_MANAGER] 數據處理失敗: {e}")
            self.error_occurred.emit(f"數據處理失敗: {str(e)}")
    
    def _on_load_error(self, error_message: str):
        """處理載入錯誤"""
        logger.error(f"[THROTTLE_DATA_MANAGER] 載入錯誤: {error_message}")
        self._is_loading = False
        self.error_occurred.emit(error_message)

class ThrottleAnalysisModule(IAnalysisModule):
    """油門分析主模組 - 完全參照速度分析模組架構"""
    
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
        self.driver1 = "ALO"
        self.driver2 = "ALO"
        self.lap1 = 1
        self.lap2 = 1
        
        # 組件
        self.data_manager = None
        self.throttle_chart_widget = None
        self.main_widget = None  # 主容器 widget
        self.parent_window = None  # MDI 子視窗引用
        
        # 初始化狀態
        self._initialized = False
        
    def initialize_module(self, parent_widget=None, **kwargs) -> bool:
        """初始化模組 - 實現抽象方法"""
        try:
            logger.debug(f"[THROTTLE_MDI] 初始化油門分析模組")
            
            # 創建數據管理器
            self.data_manager = ThrottleDataManager()
            self.data_manager.data_loaded.connect(self._update_chart)
            self.data_manager.error_occurred.connect(self._handle_error)
            
            # 創建油門圖表組件
            from .throttle_analysis_chart_widget import ThrottleAnalysisChartWidget
            self.throttle_chart_widget = ThrottleAnalysisChartWidget()
            
            # 連接圈數變更信號（如果圖表組件支援）
            if hasattr(self.throttle_chart_widget, 'lap_numbers_changed'):
                self.throttle_chart_widget.lap_numbers_changed.connect(self._on_lap_numbers_changed)
            
            # 設置初始圈數（如果圖表組件支援）
            if hasattr(self.throttle_chart_widget, 'set_lap_numbers'):
                self.throttle_chart_widget.set_lap_numbers(self.lap1, self.lap2)
            
            # 設置主界面
            self._setup_ui()
            
            self._initialized = True
            logger.info(f"[THROTTLE_MDI] 油門分析模組初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"[THROTTLE_MDI] 模組初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def set_parent_window(self, parent_window):
        """設置父視窗引用（MDI 子視窗）"""
        self.parent_window = parent_window
        
        if parent_window:
            # 立即設置正確的標題
            self.update_window_title()
    
    def _setup_ui(self):
        """設置用戶界面 - 與速度分析模組保持一致（無手動控制面板）"""
        # 創建主容器 widget
        self.main_widget = QWidget()
        layout = QVBoxLayout()
        
        # 添加油門圖表
        if self.throttle_chart_widget:
            layout.addWidget(self.throttle_chart_widget)
        
        # 設置佈局到主 widget
        self.main_widget.setLayout(layout)
    
    def _update_chart(self, data: dict):
        """更新圖表"""
        try:
            logger.debug(f"[THROTTLE_MDI] 更新油門圖表")
            if self.throttle_chart_widget:
                # 檢查圖表組件是否有更新方法
                if hasattr(self.throttle_chart_widget, 'update_throttle_data'):
                    self.throttle_chart_widget.update_throttle_data(data)
                elif hasattr(self.throttle_chart_widget, 'update_chart_data'):
                    self.throttle_chart_widget.update_chart_data(data)
                
                # 更新工具欄狀態信息
                self._update_toolbar_status(data)
                
        except Exception as e:
            logger.error(f"[THROTTLE_MDI] 圖表更新失敗: {e}")
            self.module_error.emit(f"圖表更新失敗: {str(e)}")
    
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
            
            module_name = "油門分析"
            lap_time = ""
            tyre_compound = ""
            lap_numbers = ""
            
            if drivers:
                if len(drivers) >= 2:
                    # 雙車手模式
                    driver1 = drivers[0]
                    driver2 = drivers[1]
                    
                    lap_time1 = driver1.get('lap_time', 'N/A')
                    lap_time2 = driver2.get('lap_time', 'N/A')
                    lap_time = f"{lap_time1} | {lap_time2}"
                    
                    compound1 = driver1.get('compound', 'N/A')
                    compound2 = driver2.get('compound', 'N/A')
                    tyre_compound = f"{compound1} | {compound2}"
                    
                    driver1_code = driver1.get('code', self.driver1)
                    driver2_code = driver2.get('code', self.driver2)
                    lap_numbers = f"{driver1_code} 第{self.lap1}圈 vs {driver2_code} 第{self.lap2}圈"
                    
                elif len(drivers) >= 1:
                    # 單車手模式
                    driver1 = drivers[0]
                    lap_time = driver1.get('lap_time', 'N/A')
                    tyre_compound = driver1.get('compound', 'N/A')
                    
                    driver1_code = driver1.get('code', self.driver1)
                    lap_numbers = f"{driver1_code} 第{self.lap1}圈"
            else:
                # 無車手數據時顯示基本信息
                lap_numbers = f"第{self.lap1}圈 vs 第{self.lap2}圈"
            
            # 更新工具欄狀態
            main_window.update_toolbar_status(
                module_name=module_name,
                lap_time=lap_time,
                tyre_compound=tyre_compound,
                lap_numbers=lap_numbers
            )
            
            logger.debug(f"[THROTTLE_MDI] 已更新工具欄狀態: {module_name}")
            
        except Exception as e:
            logger.error(f"[THROTTLE_MDI] 更新工具欄狀態失敗: {e}")
    
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
            logger.error(f"[THROTTLE_MDI] 獲取主視窗失敗: {e}")
            return None
    
    def _handle_error(self, error_message: str):
        """處理錯誤"""
        logger.error(f"[THROTTLE_MDI] {error_message}")
        self.module_error.emit(error_message)
    
    def _on_lap_numbers_changed(self, lap1: int, lap2: int):
        """處理圈數變更 - 參照速度分析模組"""
        try:
            logger.debug(f"[THROTTLE_MDI] ========== 圈數變更處理 ==========")
            logger.debug(f"[THROTTLE_MDI] 新圈數: 第{lap1}圈 vs 第{lap2}圈")
            
            # 更新模組的圈數參數
            old_lap1, old_lap2 = self.lap1, self.lap2
            self.lap1 = lap1
            self.lap2 = lap2
            
            logger.debug(f"[THROTTLE_MDI] 圈數變更: 第{old_lap1}圈 vs 第{old_lap2}圈 → 第{lap1}圈 vs 第{lap2}圈")
            
            # 重新載入數據
            if self.data_manager:
                logger.debug(f"[THROTTLE_MDI] 🔄 因圈數變更重新載入數據...")
                success = self.data_manager.load_throttle_data(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session,
                    driver1=self.driver1,
                    driver2=self.driver2,
                    lap1=self.lap1,
                    lap2=self.lap2
                )
                
                if success:
                    logger.info(f"[THROTTLE_MDI] ✅ 圈數變更後數據重載成功")
                else:
                    logger.error(f"[THROTTLE_MDI] ❌ 圈數變更後數據重載失敗")
            else:
                logger.error(f"[THROTTLE_MDI] ❌ 數據管理器未初始化，無法重載數據")
                
        except Exception as e:
            logger.error(f"[THROTTLE_MDI] 處理圈數變更失敗: {e}")
            import traceback
            traceback.print_exc()
            self.module_error.emit(f"處理圈數變更失敗: {str(e)}")
    
    def update_parameters(self, year: int = None, race: str = None, session: str = None, **kwargs) -> bool:
        """更新參數 - 實現抽象方法，參照速度分析模組"""
        try:
            # 準備更新的參數
            new_year = str(year) if year is not None else self.current_year
            new_race = race if race is not None else self.current_race
            new_session = session if session is not None else self.current_session
            
            # 檢查參數是否有變化（基於當前的模組參數）
            params_changed = (
                self.current_year != new_year or 
                self.current_race != new_race or 
                self.current_session != new_session
            )
            
            # 更新本地參數（如果調用者沒有提前更新的話）
            self.current_year = new_year
            self.current_race = new_race
            self.current_session = new_session
            
            # 確保視窗標題是最新的
            self.update_window_title()
            
            if params_changed:
                # 載入新數據
                if self.data_manager:
                    success = self.data_manager.load_throttle_data(
                        year=self.current_year,
                        race=self.current_race,
                        session=self.current_session,
                        driver1=self.driver1,
                        driver2=self.driver2,
                        lap1=self.lap1,
                        lap2=self.lap2
                    )
                    
                    if success:
                        # 數據載入成功後再次確保標題正確
                        self.update_window_title()
                        self.parameters_updated.emit({
                            'year': int(new_year),
                            'race': new_race,
                            'session': new_session
                        })
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                # 如果是首次載入或沒有數據，仍然需要載入
                if self.data_manager and not hasattr(self, '_data_loaded'):
                    success = self.data_manager.load_throttle_data(
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
                        return True
                    else:
                        return False
                else:
                    return True
                
        except Exception as e:
            logger.error(f"[THROTTLE_PARAMS_DEBUG] 參數更新失敗: {e}")
            import traceback
            traceback.print_exc()
            self.module_error.emit(f"參數更新失敗: {str(e)}")
            return False
    
    def update_lap_parameters(self, year: str, race: str, session: str, 
                            driver1: str, driver2: str = None, 
                            lap1: int = 1, lap2: int = 1, 
                            is_fastest: bool = False) -> bool:
        """更新圈速分析參數（包含車手和圈數）- 參照速度分析模組"""
        try:
            logger.debug(f"[THROTTLE_MDI] ========== 圈速參數更新 ==========")
            logger.debug(f"[THROTTLE_MDI] 收到參數: {year} {race} {session}")
            logger.debug(f"[THROTTLE_MDI] 車手: {driver1} vs {driver2}")
            logger.debug(f"[THROTTLE_MDI] 圈數: 第{lap1}圈 vs 第{lap2}圈")
            logger.debug(f"[THROTTLE_MDI] 最速圈: {is_fastest}")
            
            # 檢查是否需要最速圈數據
            if is_fastest:
                logger.debug(f"[THROTTLE_MDI] 🏁 用戶選擇了最速圈選項，檢查遙測分析數據...")
                fastest_laps = self._ensure_telemetry_data_for_fastest_laps()
                if fastest_laps:
                    # 使用最速圈數據更新圈數
                    if driver1 in fastest_laps:
                        lap1 = fastest_laps[driver1]
                        logger.debug(f"[THROTTLE_MDI] 🏁 車手 {driver1} 最速圈: 第{lap1}圈")
                    if driver2 and driver2 in fastest_laps:
                        lap2 = fastest_laps[driver2]
                        logger.debug(f"[THROTTLE_MDI] 🏁 車手 {driver2} 最速圈: 第{lap2}圈")
                else:
                    logger.warning(f"[THROTTLE_MDI] ⚠️ 無法獲取最速圈數據，使用預設圈數")
            
            # 檢查參數是否有變化
            params_changed = (
                self.current_year != str(year) or 
                self.current_race != race or 
                self.current_session != session or
                self.driver1 != driver1 or
                self.driver2 != driver2 or  # 正確處理 None 值比較
                self.lap1 != lap1 or
                self.lap2 != lap2
            )
            
            logger.debug(f"[THROTTLE_MDI] 參數是否變化: {params_changed}")
            
            # 更新所有參數 - 保持 driver2 的原始值（包括 None）
            self.current_year = str(year)
            self.current_race = race
            self.current_session = session
            self.driver1 = driver1
            self.driver2 = driver2  # 保持原始值，支援單場賽事車手分析
            self.lap1 = lap1
            self.lap2 = lap2
            
            # 更新圖表組件的圈數顯示（如果支援）
            if self.throttle_chart_widget and hasattr(self.throttle_chart_widget, 'set_lap_numbers'):
                self.throttle_chart_widget.set_lap_numbers(lap1, lap2)
                logger.info(f"[THROTTLE_MDI] ✅ 已更新圖表組件的圈數顯示")
            
            if params_changed:
                logger.debug(f"[THROTTLE_MDI] 🔄 參數已變化，開始重載數據...")
                
                # 載入新數據
                if self.data_manager:
                    logger.debug(f"[THROTTLE_MDI] 📡 調用數據管理器載入新數據...")
                    success = self.data_manager.load_throttle_data(
                        year=self.current_year,
                        race=self.current_race,
                        session=self.current_session,
                        driver1=self.driver1,
                        driver2=self.driver2,
                        lap1=self.lap1,
                        lap2=self.lap2
                    )
                    
                    if success:
                        logger.info(f"[THROTTLE_MDI] ✅ 圈速參數更新後數據重載成功")
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
                            logger.debug(f"[THROTTLE_MDI] 🏷️ 視窗標題已更新為: {new_title}")
                        else:
                            logger.warning(f"[THROTTLE_MDI] ⚠️ 無法更新視窗標題 - 父視窗引用未設置")
                        
                        return True
                    else:
                        logger.error(f"[THROTTLE_MDI] ❌ 圈速參數更新後數據重載失敗")
                        return False
                else:
                    logger.error(f"[THROTTLE_MDI] ❌ 數據管理器未初始化")
                    return False
            else:
                logger.debug(f"[THROTTLE_MDI] ℹ️ 圈速參數未變化，保持現有數據")
                
                # 即使參數未變化，也確保視窗標題是正確的 - 使用統一的 get_window_title
                parent = getattr(self, 'parent_window', None)
                if parent and hasattr(parent, 'setWindowTitle'):
                    current_title = parent.windowTitle()
                    expected_title = self.get_window_title(self.current_year, self.current_race, self.current_session)
                    if current_title != expected_title:
                        parent.setWindowTitle(expected_title)
                        logger.debug(f"[THROTTLE_MDI] 🏷️ 同步視窗標題: {expected_title}")
                else:
                    logger.warning(f"[THROTTLE_MDI] ⚠️ 無法同步視窗標題 - 父視窗引用未設置")
                
                return True
                
        except Exception as e:
            logger.error(f"[THROTTLE_MDI] ❌ 圈速參數更新失敗: {e}")
            import traceback
            traceback.print_exc()
            self.module_error.emit(f"圈速參數更新失敗: {str(e)}")
            return False
    
    def get_window_title(self, year: str = None, race: str = None, session: str = None) -> str:
        """獲取視窗標題 - 統一格式，不包含車手資訊以保持模組兼容性"""
        # 如果提供了參數，使用傳入的參數；否則使用內部狀態
        use_year = year if year is not None else self.current_year
        use_race = race if race is not None else self.current_race
        use_session = session if session is not None else self.current_session
        
        # 使用統一的簡潔標題格式，與其他模組保持一致
        title = f"油門分析_{use_year}_{use_race}_{use_session}"
        return title
    
    def update_window_title(self) -> None:
        """更新視窗標題"""
        try:
            # 檢查 parent_window 屬性（MDI 子視窗引用）
            parent = getattr(self, 'parent_window', None)
            
            if parent and hasattr(parent, 'setWindowTitle'):
                new_title = self.get_window_title(self.current_year, self.current_race, self.current_session)
                parent.setWindowTitle(new_title)
                
                # 強制刷新視窗顯示
                parent.update()
                parent.repaint()
        except Exception as e:
            logger.error(f"[THROTTLE_TITLE_DEBUG] 更新視窗標題失敗: {e}")
            import traceback
            traceback.print_exc()
    
    # 實現 IAnalysisModule 抽象方法
    @property
    def module_name(self) -> str:
        """模組名稱"""
        return "throttle_analysis"
    
    @property
    def display_name(self) -> str:
        """顯示名稱"""
        return "油門分析"
    
    @property
    def description(self) -> str:
        """模組描述"""
        return "F1賽車油門分析模組，支援雙車手圈速對比"
    
    @property
    def version(self) -> str:
        """模組版本"""
        return "2.0.0"
    
    def get_widget(self):
        """獲取主要組件"""
        if hasattr(self, 'main_widget'):
            return self.main_widget
        else:
            # 如果主 widget 還沒創建，返回圖表組件作為後備
            return self.throttle_chart_widget
    
    def get_default_size(self):
        """獲取預設尺寸"""
        return (900, 600)
    
    def get_title(self) -> str:
        """返回模組標題 - 實現抽象方法"""
        return f"油門分析 - {self.current_year} {self.current_race} {self.current_session}"
    
    def supports_sync(self) -> bool:
        """是否支援主程式同步 - 實現抽象方法"""
        return True
    
    def get_parameter_interface(self) -> Optional[QWidget]:
        """返回參數設定介面 - 實現抽象方法"""
        # 油門分析模組暫時不提供參數設定介面
        return None
    
    def cleanup(self):
        """清理資源 - 實現抽象方法"""
        try:
            if hasattr(self, 'data_manager') and self.data_manager:
                # 清理數據管理器
                if hasattr(self.data_manager, 'cleanup'):
                    self.data_manager.cleanup()
                    
            if hasattr(self, 'throttle_chart_widget') and self.throttle_chart_widget:
                # 清理圖表組件
                if hasattr(self.throttle_chart_widget, 'cleanup'):
                    self.throttle_chart_widget.cleanup()
                self.throttle_chart_widget.deleteLater()
                
            if hasattr(self, 'main_widget') and self.main_widget:
                # 清理主要組件
                self.main_widget.deleteLater()
                
            logger.debug(f"[CLEANUP] 油門分析模組資源清理完成")
        except Exception as e:
            logger.error(f"油門分析模組清理失敗: {e}")
    
    def load_data(self, **kwargs) -> bool:
        """載入數據 - 實現抽象方法"""
        try:
            year = str(kwargs.get('year', self.current_year))
            race = kwargs.get('race', self.current_race)
            session = kwargs.get('session', self.current_session)
            
            return self.data_manager.load_throttle_data(
                year=year,
                race=race,
                session=session,
                driver1=kwargs.get('driver1', 'ALO'),
                driver2=kwargs.get('driver2', 'ALO'),
                lap1=kwargs.get('lap1', 1),
                lap2=kwargs.get('lap2', 1)
            )
        except Exception as e:
            logger.error(f"[THROTTLE_MDI] load_data 失敗: {e}")
            return False
    
    def refresh_analysis(self) -> None:
        """刷新分析 - 實現抽象方法"""
        try:
            self.data_manager.load_throttle_data(
                year=self.current_year,
                race=self.current_race,
                session=self.current_session,
                driver1="ALO",
                driver2="ALO",
                lap1=1,
                lap2=1
            )
        except Exception as e:
            logger.error(f"[THROTTLE_MDI] refresh_analysis 失敗: {e}")
    
    def clear_data(self):
        """清除數據 - 實現抽象方法"""
        try:
            if self.throttle_chart_widget:
                # 清除油門圖表數據
                if hasattr(self.throttle_chart_widget, 'reset_data'):
                    self.throttle_chart_widget.reset_data()
                elif hasattr(self.throttle_chart_widget, 'clear_chart'):
                    self.throttle_chart_widget.clear_chart()
            logger.debug(f"[THROTTLE_MDI] 數據已清除")
        except Exception as e:
            logger.error(f"[THROTTLE_MDI] clear_data 失敗: {e}")
    
    def get_current_data(self) -> Optional[Dict[str, Any]]:
        """獲取當前數據 - 實現抽象方法"""
        try:
            return {
                'module': 'throttle_analysis',
                'year': self.current_year,
                'race': self.current_race,
                'session': self.current_session,
                'initialized': self._initialized,
                'data_loaded': self.data_manager is not None
            }
        except Exception as e:
            logger.error(f"[THROTTLE_MDI] get_current_data 失敗: {e}")
            return None

    def _ensure_telemetry_data_for_fastest_laps(self) -> Optional[Dict[str, int]]:
        """確保遙測分析數據存在，並獲取最速圈數據 - 參照速度分析模組
        
        Returns:
            Dict[str, int]: 車手代碼到最速圈數的映射，例如 {'ALO': 15, 'LEC': 23}
        """
        try:
            logger.debug(f"[THROTTLE_MDI] 🔍 檢查遙測分析數據: {self.current_year} {self.current_race} {self.current_session}")
            
            # 檢查遙測分析JSON檔案是否存在
            telemetry_file = self._find_telemetry_analysis_file()
            
            if not telemetry_file:
                logger.debug(f"[THROTTLE_MDI] 📡 遙測分析數據不存在，開始自動載入...")
                success = self._trigger_telemetry_analysis()
                if success:
                    # 重新檢查檔案
                    telemetry_file = self._find_telemetry_analysis_file()
                else:
                    logger.error(f"[THROTTLE_MDI] ❌ 遙測分析載入失敗")
                    return None
            
            if telemetry_file:
                logger.debug(f"[THROTTLE_MDI] 📂 找到遙測分析檔案: {telemetry_file}")
                return self._extract_fastest_laps_from_telemetry(telemetry_file)
            else:
                logger.error(f"[THROTTLE_MDI] ❌ 無法獲取遙測分析數據")
                return None
                
        except Exception as e:
            logger.error(f"[THROTTLE_MDI] _ensure_telemetry_data_for_fastest_laps 失敗: {e}")
            return None

    def _find_telemetry_analysis_file(self) -> Optional[str]:
        """尋找遙測分析JSON檔案"""
        try:
            import glob
            
            # 搜尋可能的檔案位置
            search_patterns = [
                f"json/telemetry_analysis_{self.current_year}_{self.current_race}_{self.current_session}.json",
                f"json/telemetry_analysis_{self.current_year}_{self.current_race}.json",
                f"json_exports/telemetry_analysis_{self.current_year}_{self.current_race}_{self.current_session}.json",
                f"json_exports/telemetry_analysis_{self.current_year}_{self.current_race}.json"
            ]
            
            for pattern in search_patterns:
                matching_files = glob.glob(pattern)
                if matching_files:
                    logger.debug(f"[THROTTLE_MDI] 🎯 找到遙測分析檔案: {matching_files[0]}")
                    return matching_files[0]
            
            # 如果沒找到精確匹配，嘗試模糊搜尋
            fuzzy_pattern = f"json*/telemetry_analysis*{self.current_year}*{self.current_race}*.json"
            matching_files = glob.glob(fuzzy_pattern)
            if matching_files:
                logger.debug(f"[THROTTLE_MDI] 🔍 模糊搜尋找到遙測分析檔案: {matching_files[0]}")
                return matching_files[0]
            
            logger.error(f"[THROTTLE_MDI] ❌ 未找到遙測分析檔案")
            return None
            
        except Exception as e:
            logger.error(f"[THROTTLE_MDI] _find_telemetry_analysis_file 失敗: {e}")
            return None

    def _trigger_telemetry_analysis(self) -> bool:
        """觸發遙測分析載入/生成"""
        try:
            logger.debug(f"[THROTTLE_MDI] 🚀 觸發遙測分析載入: {self.current_year} {self.current_race} {self.current_session}")
            
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
                            logger.debug(f"[THROTTLE_MDI] 🎯 找到現有遙測分析視窗: {window_title}")
                            # 激活並刷新遙測分析視窗
                            main_window.mdi_area.setActiveSubWindow(sub_window)
                            return True
                    
                    # 如果沒有遙測分析視窗，嘗試創建一個
                    logger.debug(f"[THROTTLE_MDI] 📡 嘗試創建遙測分析視窗...")
                    if hasattr(main_window, 'create_telemetry_analysis'):
                        main_window.create_telemetry_analysis()
                        return True
            
            logger.warning("[THROTTLE_MDI] API-ONLY 模式：已停用 CLI 生成遙測分析數據")
            return False
            
        except Exception as e:
            logger.error(f"[THROTTLE_MDI] _trigger_telemetry_analysis 失敗: {e}")
            return False

    def _generate_telemetry_via_cli(self) -> bool:
        """通過CLI生成遙測分析數據（Function 12）"""
        logger.warning("[THROTTLE_MDI] API-ONLY 模式：CLI 生成已停用")
        return False

    def _extract_fastest_laps_from_telemetry(self, telemetry_file: str) -> Optional[Dict[str, int]]:
        """從遙測分析JSON檔案中提取最速圈數據"""
        try:
            import json
            
            logger.debug(f"[THROTTLE_MDI] 📊 讀取遙測分析檔案: {telemetry_file}")
            
            with open(telemetry_file, 'r', encoding='utf-8') as f:
                telemetry_data = json.load(f)
            
            fastest_laps = {}
            
            # 檢查數據結構
            if 'data' in telemetry_data:
                driver_data = telemetry_data['data']
            else:
                driver_data = telemetry_data
            
            # 提取每個車手的最速圈數
            for driver_code, driver_info in driver_data.items():
                if isinstance(driver_info, dict):
                    lap_analysis = driver_info.get('lap_time_analysis', {})
                    fastest_lap = lap_analysis.get('fastest_lap', {})
                    lap_number = fastest_lap.get('lap_number')
                    
                    if lap_number and lap_number != 'N/A':
                        try:
                            fastest_laps[driver_code] = int(lap_number)
                            logger.debug(f"[THROTTLE_MDI] 🏁 {driver_code} 最速圈: 第{lap_number}圈")
                        except (ValueError, TypeError):
                            logger.warning(f"[THROTTLE_MDI] ⚠️ {driver_code} 最速圈數無效: {lap_number}")
            
            if fastest_laps:
                logger.info(f"[THROTTLE_MDI] ✅ 成功提取 {len(fastest_laps)} 個車手的最速圈數據")
                return fastest_laps
            else:
                logger.error(f"[THROTTLE_MDI] ❌ 未找到有效的最速圈數據")
                return None
                
        except Exception as e:
            logger.error(f"[THROTTLE_MDI] _extract_fastest_laps_from_telemetry 失敗: {e}")
            return None

    def receive_main_window_update_notification(self, param_type, value):
        """接收主視窗參數更新通知 - 參照速度分析模組
        
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
            logger.debug(f"[THROTTLE_NOTIFICATION_DEBUG] ========== 收到主視窗更新通知 ==========")
            logger.debug(f"[THROTTLE_NOTIFICATION_DEBUG] 📝 原始參數:")
            logger.debug(f"[THROTTLE_NOTIFICATION_DEBUG] - param_type: {param_type}")
            logger.debug(f"[THROTTLE_NOTIFICATION_DEBUG] - value: {value}")
            
            # 簡化的參數處理
            # 直接處理參數更新
            if param_type == 'year':
                self.current_year = str(value)
                logger.debug(f"[UPDATE] 年份更新為: {self.current_year}")
            elif param_type == 'race':
                self.current_race = str(value)
                logger.debug(f"[UPDATE] 賽事更新為: {self.current_race}")
            elif param_type == 'session':
                self.current_session = str(value)
                logger.debug(f"[UPDATE] 場次更新為: {self.current_session}")
            
            logger.debug(f"[THROTTLE_NOTIFICATION_DEBUG] 📊 當前模組狀態:")
            logger.debug(f"[THROTTLE_NOTIFICATION_DEBUG] - 當前年份: {self.current_year}")
            logger.debug(f"[THROTTLE_NOTIFICATION_DEBUG] - 當前賽事: {self.current_race}")
            logger.debug(f"[THROTTLE_NOTIFICATION_DEBUG] - 當前賽段: {self.current_session}")
            logger.debug(f"[THROTTLE_NOTIFICATION_DEBUG] - 當前車手: {self.driver1} vs {self.driver2}")
            logger.debug(f"[THROTTLE_NOTIFICATION_DEBUG] - 當前圈數: 第{self.lap1}圈 vs 第{self.lap2}圈")
            
            # [TOOL] 更新窗口標題（如果有父窗口）- 使用統一的 get_window_title
            parent = getattr(self, 'parent_window', None)
            if parent and hasattr(parent, 'setWindowTitle'):
                title = self.get_window_title(self.current_year, self.current_race, self.current_session)
                parent.setWindowTitle(title)
                logger.debug(f"[TITLE] 窗口標題更新為: {title}")
            else:
                logger.warning(f"無法更新視窗標題 - 父視窗引用未設置")
            
            # 重新載入數據
            if self.data_manager:
                logger.debug(f"[REFRESH] 重新載入油門數據...")
                self.data_manager.load_throttle_data(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session,
                    driver1=self.driver1,
                    driver2=self.driver2,
                    lap1=self.lap1,
                    lap2=self.lap2
                )
            logger.info(f"[NOTIFICATION] ⚡ 油門分析模組內容更新成功")
                
        except Exception as e:
            logger.error(f"[NOTIFICATION] ⚡ 油門分析模組內容更新失敗: {e}")
            import traceback

            traceback.print_exc()

    def export_data(self, export_path: str, export_format: str = "json") -> bool:
        """匯出數據 - 實現抽象方法"""
        try:
            logger.debug(f"[THROTTLE_MDI] 匯出數據功能尚未實現 (路徑: {export_path}, 格式: {export_format})")
            return False
        except Exception as e:
            logger.error(f"[THROTTLE_MDI] export_data 失敗: {e}")
            return False

# 註冊油門分析模組到工廠
try:
    from modules.gui.interfaces.analysis_module import ModuleFactory, ModuleTypes
    ModuleFactory.register_module(ModuleTypes.TELEMETRY_THROTTLE, ThrottleAnalysisModule)
    logger.info(f"[MODULE_FACTORY] Throttle analysis module registered")
except ImportError as e:
    logger.warning(f"[MODULE_FACTORY] 油門分析模組註冊失敗: {e}")
