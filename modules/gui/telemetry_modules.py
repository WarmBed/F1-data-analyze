#!/usr/bin/env python3
"""
遙測模組 - 基於通用介面的實現
Telemetry Module - Implementation based on universal interface
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox
from PyQt5.QtCore import Qt
from .base import BaseAnalysisModule, IParameterProvider, ModuleTypes, ModuleFactory


class TelemetryModule(BaseAnalysisModule):
    """遙測分析模組"""
    
    def __init__(self, telemetry_type="speed", parameter_provider: IParameterProvider = None):
        super().__init__(f"{self._get_telemetry_name(telemetry_type)}遙測", parameter_provider)
        self.telemetry_type = telemetry_type
        
    def _get_telemetry_name(self, telemetry_type):
        """獲取遙測類型名稱"""
        names = {
            "speed": "速度",
            "brake": "煞車壓力", 
            "throttle": "節流閥",
            "steering": "方向盤角度"
        }
        return names.get(telemetry_type, "遙測")
    
    def get_widget(self) -> QWidget:
        """創建遙測圖表Widget"""
        if not self._widget:
            # 導入現有的TelemetryChartWidget
            try:
                # 這裡我們重用現有的TelemetryChartWidget
                # 在實際使用中，這會從主模組導入
                from ...f1t_gui_main import TelemetryChartWidget
                self._widget = TelemetryChartWidget(self.telemetry_type)
            except ImportError:
                # 如果導入失敗，創建一個佔位符
                self._widget = self._create_placeholder_widget()
                
        return self._widget
    
    def _create_placeholder_widget(self) -> QWidget:
        """創建佔位符Widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title_label = QLabel(f"{self.get_title()}")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        info_label = QLabel("遙測圖表將在此顯示")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        return widget
    
    def get_parameter_interface(self) -> QWidget:
        """返回參數設定介面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 遙測類型選擇
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("遙測類型:"))
        
        type_combo = QComboBox()
        type_combo.addItems(["速度", "煞車壓力", "節流閥", "方向盤角度"])
        type_combo.setCurrentText(self._get_telemetry_name(self.telemetry_type))
        type_layout.addWidget(type_combo)
        
        layout.addLayout(type_layout)
        layout.addStretch()
        
        return widget
    
    def update_parameters(self, **params) -> bool:
        """更新分析參數"""
        try:
            # 更新基礎參數
            success = super().update_parameters(**params)
            
            if success and self._widget:
                # 觸發widget更新（如果有的話）
                if hasattr(self._widget, 'update'):
                    self._widget.update()
                    
            return success
        except Exception as e:
            self.signals.module_error.emit(f"遙測模組參數更新失敗: {e}")
            return False
    
    def get_default_size(self) -> tuple:
        """遙測圖表的預設大小"""
        return (500, 250)


class StatisticsModule(BaseAnalysisModule):
    """統計數據模組"""
    
    def __init__(self, parameter_provider: IParameterProvider = None):
        super().__init__("統計數據", parameter_provider)
    
    def get_widget(self) -> QWidget:
        """創建統計數據Widget"""
        if not self._widget:
            self._widget = self._create_statistics_widget()
        return self._widget
    
    def _create_statistics_widget(self) -> QWidget:
        """創建統計數據Widget"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        title_label = QLabel("賽季統計數據")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        stats_text = """• 總圈數: 1,247
• 平均圈速: 1:18.456
• 最快圈速: 1:16.123
• 完賽率: 94.2%"""
        
        stats_label = QLabel(stats_text)
        stats_label.setAlignment(Qt.AlignLeft)
        layout.addWidget(stats_label)
        
        layout.addStretch()
        
        return widget
    
    def get_parameter_interface(self) -> QWidget:
        """統計數據的參數介面"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        layout.addWidget(QLabel("統計數據設定"))
        layout.addWidget(QLabel("顯示範圍: 完整賽季"))
        layout.addStretch()
        
        return widget
    
    def update_parameters(self, **params) -> bool:
        """更新統計參數"""
        return super().update_parameters(**params)
    
    def get_default_size(self) -> tuple:
        return (300, 200)


# 註冊模組到工廠
ModuleFactory.register_module(ModuleTypes.TELEMETRY_SPEED, lambda **kwargs: TelemetryModule("speed", **kwargs))
ModuleFactory.register_module(ModuleTypes.TELEMETRY_BRAKE, lambda **kwargs: TelemetryModule("brake", **kwargs))
ModuleFactory.register_module(ModuleTypes.TELEMETRY_THROTTLE, lambda **kwargs: TelemetryModule("throttle", **kwargs))
ModuleFactory.register_module(ModuleTypes.TELEMETRY_STEERING, lambda **kwargs: TelemetryModule("steering", **kwargs))
ModuleFactory.register_module(ModuleTypes.STATISTICS, StatisticsModule)
