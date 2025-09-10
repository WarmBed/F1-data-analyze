#!/usr/bin/env python3
"""
TireAnalysisUniversal - F1T 通用輪胎策略分析模組
===============================================

基於通用 MDI 架構實現的輪胎策略分析模組，支援：
- 輪胎配方策略分析（SOFT/MEDIUM/HARD）
- Stint 時間分析和比較
- 橫向長條圖顯示
- CLI -f26 數據生成
- 車手輪胎策略視覺化

數據來源：CLI -f26 生成的 tire_strategy JSON 檔案
圖表類型：橫向長條圖

Author: F1T Team
Date: 2025-09-10
Version: 1.0.0
"""

import sys
import os
from typing import Dict, List, Any, Optional, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGroupBox, QGridLayout, QPushButton, QComboBox,
    QCheckBox, QSpinBox, QSlider
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

# 導入通用基礎類別
try:
    from ..base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
    from ..base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig
    from ..base.universal_chart_widget_base import TelemetryChartWidgetBase, ChartTheme
except ImportError:
    from modules.gui.base.universal_analysis_mdi_base import UniversalAnalysisMDI, AnalysisMDIConfig
    from modules.gui.base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig
    from modules.gui.base.universal_chart_widget_base import TelemetryChartWidgetBase, ChartTheme


class TireAnalysisDataManager(UniversalDataLoader):
    """輪胎策略分析數據管理器"""
    
    def __init__(self, parent=None):
        # 註冊輪胎策略分析類型（如果尚未註冊）
        if "tire_strategy" not in UniversalDataLoader.ANALYSIS_TYPES:
            tire_config = AnalysisConfig(
                display_name="輪胎策略分析",
                debug_prefix="[TIRE_ANALYSIS]",
                data_source="json",
                cli_function="26",  # CLI -f26: 輪胎換胎時機推論
                file_patterns=[
                    "tire_timing_inference_{year}_{race_full}_None_all_drivers.json"
                ],
                search_directories=["json", "json_exports", "cache"],
                supports_realtime=False,
                cache_enabled=True
            )
            UniversalDataLoader.register_analysis_type("tire_strategy", tire_config)
        
        super().__init__("tire_strategy", parent)
        
        # 輪胎策略分析特定屬性
        self.tire_data = {}
        self.stint_mapping = {}
        self.strategy_stats = {}
        
        print(f"[TIRE_ANALYSIS] 初始化完成, 搜索目錄: {self.config.search_directories}")
        print(f"[TIRE_ANALYSIS] 文件模式: {self.config.file_patterns}")
        
    def _validate_load_parameters(self, params: Dict[str, Any]) -> bool:
        """驗證載入參數"""
        year = params.get('year')
        race = params.get('race') 
        session = params.get('session')
        
        if not year or not race or not session:
            self._debug("參數不完整：需要年份、比賽和賽段")
            return False
        return True
        
    def _build_filename_patterns(self, year: str, race: str, session: str, **kwargs) -> List[str]:
        """構建檔案名稱模式 - 精確使用 CLI -f26 格式"""
        patterns = []
        
        # 將賽事名稱轉換為完整格式
        if race == "Japan":
            race_full = "Japanese_Grand_Prix"
        else:
            # 其他賽事可能需要特殊處理，暫時使用 {race}_Grand_Prix 格式
            race_full = f"{race}_Grand_Prix"
        
        for pattern in self.config.file_patterns:
            try:
                filename = pattern.format(
                    year=year, 
                    race_full=race_full
                )
                patterns.append(filename)
                self._debug(f"生成精確模式: {filename}")
            except KeyError as e:
                self._debug(f"模式格式錯誤: {pattern}, 錯誤: {e}")
                continue
        
        self._debug(f"總共生成 {len(patterns)} 個搜尋模式")
        return patterns

    def _start_generation_monitoring(self):
        """重寫監控方法，處理 race_full 參數"""
        self._debug("========== 啟動監控系統 ==========")
        
        if not hasattr(self, '_generation_params') or not self._generation_params:
            self._debug("❌ 沒有生成參數，無法啟動監控")
            return
            
        # 擴展生成參數，添加 race_full
        expanded_params = self._generation_params.copy()
        race = expanded_params.get('race', '')
        if race == "Japan":
            expanded_params['race_full'] = "Japanese_Grand_Prix"
        else:
            expanded_params['race_full'] = f"{race}_Grand_Prix"
        
        self._debug(f"生成參數: {self._generation_params}")
        self._debug(f"擴展參數: {expanded_params}")
        
        # 檢查預期生成的檔案路徑
        if expanded_params:
            expected_patterns = []
            for pattern in self.config.file_patterns:
                try:
                    formatted_pattern = pattern.format(**expanded_params)
                    expected_patterns.append(formatted_pattern)
                except KeyError as e:
                    self._debug(f"⚠️ 格式化模式失敗: {pattern}, 錯誤: {e}")
                    continue
            self._debug(f"📋 預期檔案模式: {expected_patterns}")
        
        # 啟動監控 (每5秒檢查一次，最多等待180秒)
        self._debug("啟動主監控計時器 (每5秒檢查)")
        if hasattr(self, '_generation_timer'):
            self._generation_timer.start(5000)
        
        self._debug("啟動超時計時器 (180秒)")
        if hasattr(self, '_generation_timeout_timer'):
            self._generation_timeout_timer.start(180000)
        
        self._debug("✅ 監控系統已啟動")
        
    def _validate_data_format(self, data: Any) -> bool:
        """驗證數據格式 - 支援多種輪胎分析 JSON 格式"""
        if not isinstance(data, dict):
            self._debug("數據格式錯誤：必須是字典格式")
            return False
        
        # 支援多種 JSON 格式
        valid_formats = [
            "tire_timing_corrected",      # CLI -f26 新格式
            "all_drivers_tire_strategy",  # 舊格式
            "corrected_stint_analysis"    # 另一種格式
        ]
        
        has_valid_format = any(key in data for key in valid_formats)
        if not has_valid_format:
            self._debug(f"數據格式錯誤：缺少必要欄位，支援格式: {valid_formats}")
            self._debug(f"實際數據鍵值: {list(data.keys())}")
            return False
            
        return True
        
    def _process_data(self, data: Any) -> Dict[str, Any]:
        """處理數據的具體實現"""
        return self.process_loaded_data(data)
        
    def _generate_data_via_cli(self, **kwargs) -> bool:
        """通過 CLI 生成數據"""
        try:
            year = kwargs.get('year')
            race = kwargs.get('race') 
            session = kwargs.get('session')
            
            self._debug(f"🚀 啟動 CLI 輪胎策略數據生成")
            self._debug(f"   參數: year={year}, race={race}, session={session}")
            
            # 檢查配置中的 CLI 函數
            cli_function = self.config.cli_function
            if not cli_function:
                self._debug("❌ 配置中沒有 CLI 函數")
                return False
            
            # 使用標準化的 CliAnalysisWorker
            force_mode = 26  # 功能26: 輪胎策略分析
            
            self._debug(f"🔧 CLI 命令參數: -f {force_mode} -y {year} -r {race} -s {session}")
            
            # 創建並啟動 CLI 工作器
            self.cli_worker = self.create_cli_worker(year, race, session, force_mode)
            
            # 連接信號
            def on_cli_finished():
                self._debug("✅ CLI 工作器執行完成")
                if hasattr(self, 'cli_worker') and self.cli_worker:
                    self.cli_worker.deleteLater()
                    self.cli_worker = None
            
            def on_cli_completed(success, message):
                self._debug(f"✅ CLI 分析完成: {'成功' if success else '失敗'} - {message}")
                if hasattr(self, 'cli_worker') and self.cli_worker:
                    self.cli_worker.deleteLater()
                    self.cli_worker = None
            
            def on_cli_output(output):
                self._debug(f"📤 CLI 輸出: {output}")
            
            self.cli_worker.finished.connect(on_cli_finished)
            self.cli_worker.analysis_completed.connect(on_cli_completed)
            self.cli_worker.output_received.connect(on_cli_output)
            
            # 啟動工作器
            self.cli_worker.start()
            self._debug(f"✅ CLI 工作器已啟動")
            
            return True
            
        except Exception as e:
            self._error(f"CLI 生成失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    def process_loaded_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """處理載入的輪胎策略數據 - 支援多種 JSON 格式"""
        try:
            if not isinstance(data, dict):
                raise ValueError("數據格式不正確：必須是字典格式")
                
            # 儲存完整的原始數據
            self.data = data
            
            # 支援多種 JSON 格式的數據解析
            if "tire_timing_corrected" in data:
                # CLI -f26 新格式
                self.tire_data = data["tire_timing_corrected"]
                self._debug("使用 tire_timing_corrected 格式")
            elif "all_drivers_tire_strategy" in data:
                # 舊格式
                self.tire_data = data["all_drivers_tire_strategy"]
                self._debug("使用 all_drivers_tire_strategy 格式")
            elif "corrected_stint_analysis" in data:
                # 另一種格式
                self.tire_data = data["corrected_stint_analysis"]
                self._debug("使用 corrected_stint_analysis 格式")
            else:
                raise ValueError("找不到支援的輪胎策略數據格式")
                
            # 獲取摘要數據
            if "summary" in data:
                self.strategy_stats = data["summary"]
            else:
                self.strategy_stats = {}
                
            # 轉換為分析用數據格式
            processed_data = {
                "tire_data": self._process_tire_strategy_data(),
                "summary": self.strategy_stats,
                "metadata": data.get("metadata", {}),
                "analysis_mode": data.get("analysis_mode", "unknown"),
                "drivers_analyzed": data.get("drivers_analyzed", []),
                "charts_data": self._prepare_tire_chart_data()
            }
            
            self._debug(f"成功處理 {len(self.tire_data)} 車手輪胎策略數據")
            
            return processed_data
            
        except Exception as e:
            self._debug(f"數據處理失敗: {str(e)}")
            raise
    
    def _calculate_compound_statistics(self, drivers_data) -> Dict[str, int]:
        """計算輪胎配方使用統計"""
        compound_count = {}
        
        for driver_info in drivers_data:
            for compound in driver_info["compounds_used"]:
                compound_count[compound] = compound_count.get(compound, 0) + 1
        
        return compound_count
            
    def _process_tire_strategy_data(self) -> Dict[str, List]:
        """處理輪胎策略數據"""
        drivers_data = []
        
        # 處理所有車手的輪胎策略數據
        for driver_code, driver_data in self.tire_data.items():
            if isinstance(driver_data, dict) and "stint_analysis" in driver_data:
                stint_data = driver_data["stint_analysis"]
                
                driver_info = {
                    "driver": driver_code,
                    "stints": [],
                    "total_laps": 0,
                    "compounds_used": set()
                }
                
                for stint in stint_data:
                    stint_info = {
                        "stint_number": stint.get("stint", 1),
                        "compound": stint.get("compound", "UNKNOWN"),
                        "start_lap": stint.get("start_lap", 1),
                        "end_lap": stint.get("end_lap", 1),
                        "laps": stint.get("laps", 0),
                        "avg_laptime": stint.get("avg_laptime", 0.0)
                    }
                    driver_info["stints"].append(stint_info)
                    driver_info["compounds_used"].add(stint_info["compound"])
                
                driver_info["total_laps"] = sum(stint["laps"] for stint in driver_info["stints"])
                driver_info["compounds_used"] = list(driver_info["compounds_used"])
                drivers_data.append(driver_info)
        
        return {
            "drivers": drivers_data,
            "total_drivers": len(drivers_data)
        }
        
    def _prepare_tire_chart_data(self) -> Dict[str, Any]:
        """準備輪胎圖表數據 - 直接返回原始 JSON 數據結構"""
        if not hasattr(self, 'data') or not self.data:
            return {}
        
        # 直接返回原始 JSON 數據，讓圖表組件處理
        # 這樣圖表組件就能正確讀取 drivers_analyzed 和 all_drivers_tire_strategy
        return self.data
        
    def get_tire_summary(self) -> Dict[str, Any]:
        """獲取輪胎策略摘要統計"""
        return {
            "total_drivers": len(self.tire_data),
            "total_stints": sum(len(driver_data.get("stint_analysis", [])) 
                              for driver_data in self.tire_data.values() 
                              if isinstance(driver_data, dict)),
            "compounds_used": list(set(
                stint.get("compound", "UNKNOWN")
                for driver_data in self.tire_data.values()
                if isinstance(driver_data, dict)
                for stint in driver_data.get("stint_analysis", [])
            )),
            "has_tire_data": len(self.tire_data) > 0,
            "strategy_analysis": self.strategy_stats.get("strategy_analysis", {})
        }


# 導入專用圖表組件
from .tire_analysis_chart_widget import TireAnalysisChartWidget


class TireAnalysisControlWidget(QWidget):
    """輪胎策略分析控制面板"""
    
    # 信號定義
    chart_type_changed = pyqtSignal(str)
    parameter_changed = pyqtSignal(str, object)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """設置UI"""
        layout = QVBoxLayout(self)
        
        # 圖表選擇群組
        chart_group = QGroupBox("圖表類型")
        chart_layout = QGridLayout(chart_group)
        
        self.chart_combo = QComboBox()
        self.chart_combo.addItems([
            "輪胎策略分析",
            "輪胎配方使用統計"
        ])
        self.chart_combo.currentTextChanged.connect(self._on_chart_type_changed)
        
        chart_layout.addWidget(QLabel("選擇圖表:"), 0, 0)
        chart_layout.addWidget(self.chart_combo, 0, 1)
        
        layout.addWidget(chart_group)
        
        # 顯示選項群組
        display_group = QGroupBox("顯示選項")
        display_layout = QGridLayout(display_group)
        
        self.show_grid_cb = QCheckBox("顯示網格")
        self.show_grid_cb.setChecked(True)
        self.show_grid_cb.toggled.connect(lambda x: self.parameter_changed.emit("show_grid", x))
        
        self.show_legend_cb = QCheckBox("顯示圖例")
        self.show_legend_cb.setChecked(True)
        self.show_legend_cb.toggled.connect(lambda x: self.parameter_changed.emit("show_legend", x))
        
        display_layout.addWidget(self.show_grid_cb, 0, 0)
        display_layout.addWidget(self.show_legend_cb, 0, 1)
        
        layout.addWidget(display_group)
        
        layout.addStretch()
        
    def _on_chart_type_changed(self, text: str):
        """圖表類型改變處理"""
        chart_type_map = {
            "主要圖表 (降雨+氣溫)": "primary",
            "溫度對比 (氣溫vs賽道溫度)": "temperature",
            "濕度風速 (濕度+風速)": "humidity_wind",
            "氣壓變化": "pressure"
        }
        
        if text in chart_type_map:
            self.chart_type_changed.emit(chart_type_map[text])


class TireAnalysisUniversal(UniversalAnalysisMDI):
    """
    通用輪胎策略分析 MDI 模組
    
    基於通用 MDI 架構實現的完整輪胎策略分析功能，
    支援輪胎配方、Stint 和進站策略的視覺化和分析。
    """
    
    def __init__(self, parent=None):
        print(f"[TIRE_MDI] TireAnalysisUniversal 開始初始化...")
        
        # 註冊輪胎策略分析模組類型
        if "tire_analysis" not in UniversalAnalysisMDI.MDI_MODULE_TYPES:
            tire_config = AnalysisMDIConfig(
                analysis_type="tire_analysis",
                display_name="輪胎策略分析",
                default_size=(1400, 900),
                requires_driver_params=False,  # 輪胎策略分析不需要車手參數
                requires_lap_params=False,     # 輪胎策略分析不需要圈數參數
                supports_single_driver=False,
                supports_dual_driver=False,
                chart_types=["primary", "stint_comparison", "compound_analysis", "strategy_overview"]
            )
            UniversalAnalysisMDI.register_mdi_module_type("tire_analysis", tire_config)
            
        super().__init__("tire_analysis", parent)
        print(f"[TIRE_MDI] 基類初始化完成, 數據管理器: {self.data_manager}")
        
        # 初始化模組組件
        print(f"[TIRE_MDI] 開始初始化模組組件...")
        if not self.initialize_module():
            print(f"[TIRE_MDI] ❌ 模組組件初始化失敗")
            return
        
        print(f"[TIRE_MDI] ✅ 模組組件初始化完成")
        print(f"[TIRE_MDI] 數據管理器: {self.data_manager}")
        print(f"[TIRE_MDI] 圖表組件: {self.chart_widget}")
        
        # 參照遙測分析：設置響應式佈局
        self.set_responsive_layout()
        
    def create_data_manager(self) -> TireAnalysisDataManager:
        """創建輪胎策略分析數據管理器"""
        return TireAnalysisDataManager(self)
        
    def create_chart_widget(self) -> TireAnalysisChartWidget:
        """創建輪胎策略分析圖表組件"""
        return TireAnalysisChartWidget(parent=None)
        
    def create_control_widget(self) -> TireAnalysisControlWidget:
        """創建輪胎策略分析控制面板"""
        control_widget = TireAnalysisControlWidget(self)
        
        # 連接信號
        control_widget.chart_type_changed.connect(self._on_chart_type_changed)
        control_widget.parameter_changed.connect(self._on_parameter_changed)
        
        return control_widget
        
    def update_lap_parameters(self, year: str, race: str, session: str, **kwargs) -> bool:
        """更新輪胎策略分析參數"""
        try:
            print(f"[TIRE_MDI] ========== 輪胎策略參數更新 ==========")
            print(f"[TIRE_MDI] 收到參數: {year} {race} {session}")
            
            # 更新當前參數
            self.current_year = int(year) if isinstance(year, str) else year
            self.current_race = race
            self.current_session = session
            
            # 更新數據管理器參數
            if hasattr(self, 'data_manager') and self.data_manager:
                print(f"[TIRE_MDI] 更新數據管理器參數...")
                self.data_manager.year = self.current_year
                self.data_manager.race = self.current_race
                self.data_manager.session = self.current_session
                
                # 載入數據 - 傳遞正確的參數
                print(f"[TIRE_MDI] 開始載入數據...")
                result = self.data_manager.load_data(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session
                )
                print(f"[TIRE_MDI] 數據載入結果: {result}")
                
                # 注意：此處不直接更新圖表，等待 data_manager 發送 data_loaded 信號
                # 基類已綁定 data_loaded -> _update_chart -> chart_widget.update_data
                # 這可以避免非同步載入尚未完成時傳遞空資料
                if result:
                    print("[TIRE_MDI] 等待 data_loaded 信號進行圖表更新 (非同步載入) ...")
            
            print(f"[TIRE_MDI] 參數更新完成")
            return True
            
        except Exception as e:
            print(f"[TIRE_MDI] 參數更新失敗: {str(e)}")
            import traceback
            print(f"[TIRE_MDI] 錯誤詳情:")
            traceback.print_exc()
            return False
    
    def update_analysis_parameters(self, year: str, race: str, session: str) -> bool:
        """更新分析參數"""
        try:
            # 更新當前參數
            self.update_lap_parameters(
                year=int(year) if isinstance(year, str) else year,
                race=race,
                session=session
            )
            
            # 觸發數據重新載入
            if hasattr(self, 'data_manager') and self.data_manager:
                return self.data_manager.load_data(
                    year=self.current_year,
                    race=self.current_race,
                    session=self.current_session
                )
            
            return True
            
        except Exception as e:
            self._debug(f"更新分析參數失敗: {str(e)}")
            return False
    
    def resizeEvent(self, event):
        """參照遙測分析：MDI視窗大小調整時的響應邏輯"""
        try:
            # 調用基類的 resizeEvent
            super().resizeEvent(event)
            
            # 記錄尺寸變化
            old_size = event.oldSize()
            new_size = event.size()
            
            print(f"[tire_MDI] resizeEvent: MDI視窗縮放 {old_size.width()}x{old_size.height()} -> {new_size.width()}x{new_size.height()}")
            
            # 通知圖表組件更新佈局
            if hasattr(self, 'chart_widget') and self.chart_widget:
                if hasattr(self.chart_widget, 'update_chart_layout'):
                    print("[tire_MDI] resizeEvent: 觸發圖表重新佈局")
                    self.chart_widget.update_chart_layout()
                else:
                    print("[tire_MDI] resizeEvent: 圖表組件不支援動態佈局更新")
            else:
                print("[tire_MDI] resizeEvent: 圖表組件尚未初始化")
                
        except Exception as e:
            print(f"[ERROR] [tire_MDI] resizeEvent 處理失敗: {e}")
    
    def set_responsive_layout(self):
        """參照遙測分析：設置響應式佈局"""
        try:
            # 設置大小策略
            from PyQt5.QtWidgets import QSizePolicy
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            
            # 確保圖表組件也有正確的大小策略
            if hasattr(self, 'chart_widget') and self.chart_widget:
                self.chart_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                
            print("[tire_MDI] 響應式佈局已設置")
            
        except Exception as e:
            print(f"[ERROR] [tire_MDI] 設置響應式佈局失敗: {e}")

    def get_module_info(self) -> Dict[str, Any]:
        """獲取模組信息"""
        return {
            "name": "下雨分析",
            "type": "tire",
            "version": "1.0.0",
            "description": "F1 比賽降雨天氣分析模組",
            "author": "F1T Team",
            "supports_realtime": False,
            "data_sources": ["JSON"],
            "chart_types": ["雙Y軸折線圖", "柱狀圖", "趨勢圖"],
            "parameters": {
                "requires_year": True,
                "requires_race": True,
                "requires_session": True,
                "requires_driver": False,
                "requires_lap": False
            }
        }
        
    def _on_chart_type_changed(self, chart_type: str):
        """處理圖表類型改變"""
        if hasattr(self.chart_widget, 'switch_chart_type'):
            self.chart_widget.switch_chart_type(chart_type)
            
    def _on_parameter_changed(self, param_name: str, value):
        """處理參數改變"""
        self._debug(f"參數改變: {param_name} = {value}")
        
        # 根據參數類型進行處理
        if param_name in ["show_grid", "show_legend"]:
            # 更新圖表顯示選項
            if hasattr(self.chart_widget, 'update_display_options'):
                self.chart_widget.update_display_options(param_name, value)
                
    def validate_parameters(self) -> Tuple[bool, str]:
        """驗證模組參數"""
        if not self.current_year:
            return False, "請選擇年份"
            
        if not self.current_race:
            return False, "請選擇比賽"
            
        if not self.current_session:
            return False, "請選擇賽段"
            
        return True, ""
        
    def get_analysis_summary(self) -> Dict[str, Any]:
        """獲取分析摘要"""
        if not self.data_manager:
            return {}
            
        try:
            tire_summary = self.data_manager.get_tire_summary()
            
            return {
                "module": "下雨分析",
                "parameters": {
                    "year": self.current_year,
                    "race": self.current_race,
                    "session": self.current_session
                },
                "data_info": {
                    "total_laps": tire_summary.get("total_laps", 0),
                    "tire_laps": tire_summary.get("tire_laps", 0),
                    "tire_percentage": tire_summary.get("tire_percentage", 0.0),
                    "has_weather_data": tire_summary.get("has_tire_data", False)
                },
                "generated_at": self.get_current_timestamp()
            }
            
        except Exception as e:
            self._debug(f"獲取分析摘要失敗: {str(e)}")
            return {}


# 模組註冊 - 確保在導入時自動註冊
def register_tire_analysis_module():
    """註冊下雨分析模組"""
    try:
        # 這裡可以添加到全局模組註冊表
        pass
    except Exception as e:
        print(f"[WARNING] 下雨分析模組註冊失敗: {str(e)}")


# 自動註冊
register_tire_analysis_module()
