#!/usr/bin/env python3
"""
RainAnalysisUniversal - F1T 通用下雨分析模組
=============================================

基於通用 MDI 架構實現的下雨分析模組，支援：
- 降雨狀態分析（有雨/無雨）
- 溫度變化分析（氣溫、賽道溫度）
- 濕度和風速分析
- 雙Y軸圖表顯示
- 圈數對應天氣數據

數據來源：enhanced_rain_analysis JSON 檔案
圖表類型：雙Y軸折線圖、柱狀圖

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


class RainAnalysisDataManager(UniversalDataLoader):
    """下雨分析數據管理器"""
    
    def __init__(self, parent=None):
        # 註冊下雨分析類型（如果尚未註冊）
        if "rain_weather" not in UniversalDataLoader.ANALYSIS_TYPES:
            rain_config = AnalysisConfig(
                display_name="下雨分析",
                debug_prefix="[RAIN_ANALYSIS]",
                data_source="json",
                cli_function="run_rain_intensity_analysis_json",
                file_patterns=[
                    "enhanced_rain_analysis_{year}_{race}_{session}.json",
                    "rain_analysis_{year}_{race}_{session}.json",
                    "weather_data_{year}_{race}_{session}.json"
                ],
                search_directories=["json", "json_exports", "cache"],
                supports_realtime=False,
                cache_enabled=True
            )
            UniversalDataLoader.register_analysis_type("rain_weather", rain_config)
        
        super().__init__("rain_weather", parent)
        
        # 下雨分析特定屬性
        self.weather_data = {}
        self.lap_weather_mapping = {}
        self.summary_stats = {}
        
    def _validate_load_parameters(self, year: str, race: str, session: str, **kwargs) -> bool:
        """驗證載入參數"""
        if not year or not race or not session:
            self._debug("參數不完整：需要年份、比賽和賽段")
            return False
        return True
        
    def _build_filename_patterns(self, year: str, race: str, session: str, **kwargs) -> List[str]:
        """構建檔案名稱模式"""
        patterns = []
        for pattern in self.config.file_patterns:
            filename = pattern.format(year=year, race=race, session=session)
            patterns.append(filename)
        return patterns
        
    def _validate_data_format(self, data: Any) -> bool:
        """驗證數據格式"""
        if not isinstance(data, dict):
            self._debug("數據格式錯誤：必須是字典格式")
            return False
            
        if "lap_weather_data" not in data:
            self._debug("數據格式錯誤：缺少 lap_weather_data 欄位")
            return False
            
        return True
        
    def _process_data(self, data: Any) -> Dict[str, Any]:
        """處理數據的具體實現"""
        return self.process_loaded_data(data)
        
    def _generate_data_via_cli(self, year: str, race: str, session: str, **kwargs) -> Optional[Dict[str, Any]]:
        """通過 CLI 生成數據"""
        # 下雨分析通常不需要即時生成，直接返回 None
        self._debug("下雨分析不支援 CLI 數據生成")
        return None
        
    def process_loaded_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """處理載入的下雨分析數據"""
        try:
            if not isinstance(data, dict):
                raise ValueError("數據格式不正確：必須是字典格式")
                
            # 解析 JSON 結構
            if "lap_weather_data" in data:
                self.lap_weather_mapping = data["lap_weather_data"]
            else:
                raise ValueError("找不到圈數天氣數據：lap_weather_data")
                
            if "summary" in data:
                self.summary_stats = data["summary"]
            else:
                self.summary_stats = {}
                
            # 轉換為分析用數據格式
            processed_data = {
                "lap_data": self._process_lap_weather_data(),
                "summary": self.summary_stats,
                "metadata": data.get("metadata", {}),
                "charts_data": self._prepare_chart_data()
            }
            
            self._debug(f"成功處理 {len(self.lap_weather_mapping)} 圈天氣數據")
            
            return processed_data
            
        except Exception as e:
            self._debug(f"數據處理失敗: {str(e)}")
            raise
            
    def _process_lap_weather_data(self) -> Dict[str, List]:
        """處理圈數天氣數據"""
        laps = []
        rainfall = []
        air_temp = []
        track_temp = []
        humidity = []
        wind_speed = []
        pressure = []
        
        # 按圈數順序處理數據
        lap_numbers = sorted([int(lap) for lap in self.lap_weather_mapping.keys()])
        
        for lap_num in lap_numbers:
            lap_str = str(lap_num)
            lap_data = self.lap_weather_mapping[lap_str]
            
            laps.append(lap_num)
            
            # 降雨狀態（布林值轉數值）
            rainfall_status = lap_data.get("weather", {}).get("rainfall", False)
            rainfall.append(1 if rainfall_status else 0)
            
            # 溫度數據
            temp_data = lap_data.get("temperature", {})
            air_temp.append(temp_data.get("air_temp", 0))
            track_temp.append(temp_data.get("track_temp", 0))
            
            # 其他天氣數據
            humidity.append(lap_data.get("humidity", 0))
            
            wind_data = lap_data.get("wind", {})
            wind_speed.append(wind_data.get("speed", 0))
            
            weather_data = lap_data.get("weather", {})
            pressure.append(weather_data.get("pressure", 0))
            
        return {
            "laps": laps,
            "rainfall": rainfall,
            "air_temp": air_temp,
            "track_temp": track_temp,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "pressure": pressure
        }
        
    def _prepare_chart_data(self) -> Dict[str, Any]:
        """準備圖表數據"""
        lap_data = self._process_lap_weather_data()
        
        return {
            # 主要圖表數據（降雨 + 溫度）
            "primary": {
                "x_data": lap_data["laps"],
                "y1_data": lap_data["rainfall"],  # 左Y軸：降雨狀態
                "y2_data": lap_data["air_temp"],  # 右Y軸：氣溫
                "y1_label": "降雨狀態",
                "y2_label": "氣溫 (°C)",
                "title": "降雨狀態與氣溫變化"
            },
            
            # 溫度對比圖表
            "temperature": {
                "x_data": lap_data["laps"],
                "y1_data": lap_data["air_temp"],
                "y2_data": lap_data["track_temp"],
                "y1_label": "氣溫 (°C)",
                "y2_label": "賽道溫度 (°C)",
                "title": "氣溫與賽道溫度對比"
            },
            
            # 濕度與風速圖表
            "humidity_wind": {
                "x_data": lap_data["laps"],
                "y1_data": lap_data["humidity"],
                "y2_data": lap_data["wind_speed"],
                "y1_label": "濕度 (%)",
                "y2_label": "風速 (m/s)",
                "title": "濕度與風速變化"
            },
            
            # 氣壓圖表
            "pressure": {
                "x_data": lap_data["laps"],
                "y_data": lap_data["pressure"],
                "y_label": "氣壓 (hPa)",
                "title": "氣壓變化"
            }
        }
        
    def get_rain_summary(self) -> Dict[str, Any]:
        """獲取降雨摘要統計"""
        return {
            "total_laps": self.summary_stats.get("total_laps", 0),
            "rain_laps": self.summary_stats.get("rain_laps", 0),
            "rain_percentage": self.summary_stats.get("rain_percentage", 0.0),
            "has_rain_data": self.summary_stats.get("has_rain_data", False),
            "rain_timing": self.summary_stats.get("rain_timing_analysis", {})
        }


class RainAnalysisChartWidget(TelemetryChartWidgetBase):
    """下雨分析圖表組件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 下雨分析特定配置
        self.chart_types = ["primary", "temperature", "humidity_wind", "pressure"]
        self.current_chart_type = "primary"
        
        # 圖表數據
        self.charts_data = {}
        
        # 設定圖表樣式
        self.setup_rain_chart_style()
        
    def setup_rain_chart_style(self):
        """設定下雨分析圖表樣式"""
        # 降雨相關顏色配置
        self.rain_colors = {
            "rainfall": "#3498db",      # 藍色 - 降雨
            "air_temp": "#e74c3c",      # 紅色 - 氣溫
            "track_temp": "#e67e22",    # 橙色 - 賽道溫度
            "humidity": "#2ecc71",      # 綠色 - 濕度
            "wind_speed": "#9b59b6",    # 紫色 - 風速
            "pressure": "#34495e"       # 深灰色 - 氣壓
        }
        
    def update_chart_data(self, data: Dict[str, Any]):
        """更新圖表數據"""
        if "charts_data" in data:
            self.charts_data = data["charts_data"]
            self.refresh_chart()
            
    def refresh_chart(self):
        """刷新當前圖表"""
        if not self.charts_data or self.current_chart_type not in self.charts_data:
            return
            
        chart_data = self.charts_data[self.current_chart_type]
        
        # 根據圖表類型繪制不同的圖表
        if self.current_chart_type == "primary":
            self._draw_dual_axis_chart(chart_data)
        elif self.current_chart_type == "temperature":
            self._draw_dual_axis_chart(chart_data)
        elif self.current_chart_type == "humidity_wind":
            self._draw_dual_axis_chart(chart_data)
        elif self.current_chart_type == "pressure":
            self._draw_single_axis_chart(chart_data)
            
        self.update()
        
    def _draw_dual_axis_chart(self, chart_data: Dict[str, Any]):
        """繪制雙Y軸圖表"""
        # 實現雙Y軸圖表繪制
        # 這裡使用基類的繪圖方法
        pass
        
    def _draw_single_axis_chart(self, chart_data: Dict[str, Any]):
        """繪制單Y軸圖表"""
        # 實現單Y軸圖表繪制
        pass
        
    def switch_chart_type(self, chart_type: str):
        """切換圖表類型"""
        if chart_type in self.chart_types:
            self.current_chart_type = chart_type
            self.refresh_chart()


class RainAnalysisControlWidget(QWidget):
    """下雨分析控制面板"""
    
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
            "主要圖表 (降雨+氣溫)",
            "溫度對比 (氣溫vs賽道溫度)",
            "濕度風速 (濕度+風速)",
            "氣壓變化"
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


class RainAnalysisUniversal(UniversalAnalysisMDI):
    """
    通用下雨分析 MDI 模組
    
    基於通用 MDI 架構實現的完整下雨分析功能，
    支援多種天氣數據的視覺化和分析。
    """
    
    def __init__(self, parent=None):
        # 註冊下雨分析模組類型
        if "rain" not in UniversalAnalysisMDI.MDI_MODULE_TYPES:
            rain_config = AnalysisMDIConfig(
                analysis_type="rain",
                display_name="下雨分析",
                default_size=(1400, 900),
                requires_driver_params=False,  # 下雨分析不需要車手參數
                requires_lap_params=False,     # 下雨分析不需要圈數參數
                supports_single_driver=False,
                supports_dual_driver=False,
                chart_types=["primary", "temperature", "humidity_wind", "pressure"]
            )
            UniversalAnalysisMDI.register_mdi_module_type("rain", rain_config)
            
        super().__init__("rain", parent)
        
    def create_data_manager(self) -> RainAnalysisDataManager:
        """創建下雨分析數據管理器"""
        return RainAnalysisDataManager(self)
        
    def create_chart_widget(self) -> RainAnalysisChartWidget:
        """創建下雨分析圖表組件"""
        return RainAnalysisChartWidget(self)
        
    def create_control_widget(self) -> RainAnalysisControlWidget:
        """創建下雨分析控制面板"""
        control_widget = RainAnalysisControlWidget(self)
        
        # 連接信號
        control_widget.chart_type_changed.connect(self._on_chart_type_changed)
        control_widget.parameter_changed.connect(self._on_parameter_changed)
        
        return control_widget
    
    def update_lap_parameters(self, year: str, race: str, session: str, **kwargs) -> bool:
        """更新降雨分析參數"""
        try:
            print(f"[RAIN_UNIVERSAL] ========== 降雨參數更新 ==========")
            print(f"[RAIN_UNIVERSAL] 收到參數: {year} {race} {session}")
            
            # 更新當前參數
            self.current_year = int(year) if isinstance(year, str) else year
            self.current_race = race
            self.current_session = session
            
            # 更新數據管理器參數
            if hasattr(self, 'data_manager') and self.data_manager:
                self.data_manager.year = self.current_year
                self.data_manager.race = self.current_race
                self.data_manager.session = self.current_session
            
            print(f"[RAIN_UNIVERSAL] 參數更新完成")
            return True
            
        except Exception as e:
            print(f"[RAIN_UNIVERSAL] 參數更新失敗: {str(e)}")
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
                return self.data_manager.load_data()
            
            return True
            
        except Exception as e:
            self._debug(f"更新分析參數失敗: {str(e)}")
            return False

    def get_module_info(self) -> Dict[str, Any]:
        """獲取模組信息"""
        return {
            "name": "下雨分析",
            "type": "rain",
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
            rain_summary = self.data_manager.get_rain_summary()
            
            return {
                "module": "下雨分析",
                "parameters": {
                    "year": self.current_year,
                    "race": self.current_race,
                    "session": self.current_session
                },
                "data_info": {
                    "total_laps": rain_summary.get("total_laps", 0),
                    "rain_laps": rain_summary.get("rain_laps", 0),
                    "rain_percentage": rain_summary.get("rain_percentage", 0.0),
                    "has_weather_data": rain_summary.get("has_rain_data", False)
                },
                "generated_at": self.get_current_timestamp()
            }
            
        except Exception as e:
            self._debug(f"獲取分析摘要失敗: {str(e)}")
            return {}


# 模組註冊 - 確保在導入時自動註冊
def register_rain_analysis_module():
    """註冊下雨分析模組"""
    try:
        # 這裡可以添加到全局模組註冊表
        pass
    except Exception as e:
        print(f"[WARNING] 下雨分析模組註冊失敗: {str(e)}")


# 自動註冊
register_rain_analysis_module()
