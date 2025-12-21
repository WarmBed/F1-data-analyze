# -*- coding: utf-8 -*-
"""
LegacyContentCreator - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLabel
from core.logger import get_logger
from windows.workers.cli_workers import MainWindowParameterProvider
from windows.widgets.telemetry_chart_widget import TelemetryChartWidget

logger = get_logger(__name__)


class LegacyContentCreator:
    """從 f1t_gui_main.py 提取的 _create_legacy_content 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _create_legacy_content(self, function_name):
        """創建舊版內容 - 保持向後相容性"""
        # 根據功能類型創建相應的內容
        if "降雨分析" in function_name:
            # 使用新的雨量分析模組 (Universal MDI 架構)
            try:
                from modules.gui.race_analysis.rain.rain_analysis_mdi import RainAnalysisUniversal
                params = self.main_window.get_current_parameters()
                content = RainAnalysisUniversal(
                    year=params['year'],
                    race=params['race'],
                    session=params['session']
                )
                logger.debug(f"[OK] 已載入降雨分析模組 (Universal MDI) - {params['year']} {params['race']} {params['session']}")
                return content
                
            except ImportError as e:
                logger.error(f"[ERROR] 模組導入失敗: {e}")
                return TelemetryChartWidget("speed")  # 後備方案
        elif "遙測" in function_name:
            return TelemetryChartWidget("speed")
        elif "煞車" in function_name or "制動" in function_name:
            # 使用新的煞車分析模組
            try:
                from modules.gui.lap_analysis.brake_analysis.brake_analysis_mdi import BrakeAnalysisModule
                
                # 創建參數提供者
                parameter_provider = MainWindowParameterProvider(self.main_window)
                
                # 創建模組實例並設置參數提供者
                module = BrakeAnalysisModule()
                module.parameter_provider = parameter_provider
                
                # 在初始化前先設置當前參數
                if parameter_provider:
                    current_year = int(parameter_provider.get_current_year())
                    current_race = parameter_provider.get_current_race() 
                    current_session = parameter_provider.get_current_session()
                    
                    # 直接設置模組參數
                    module.current_year = str(current_year)
                    module.current_race = current_race
                    module.current_session = current_session
                    
                    logger.debug(f"[INIT] 煞車分析模組參數預設為: {current_year} {current_race} {current_session}")
                
                # 初始化模組
                if module.initialize_module():
                    logger.debug(f"[OK] 煞車分析模組初始化成功")
                    return module
                else:
                    logger.error(f"[ERROR] 煞車分析模組初始化失敗")
                    return TelemetryChartWidget("brake")  # 後備方案
                    
            except ImportError as e:
                logger.error(f"[ERROR] 煞車分析模組導入失敗: {e}")
                return TelemetryChartWidget("brake")  # 後備方案
            except Exception as e:
                logger.error(f"[ERROR] 煞車分析模組創建失敗: {e}")
                return TelemetryChartWidget("brake")  # 後備方案
        elif "油門" in function_name or "節流" in function_name:
            return TelemetryChartWidget("throttle")
        elif "轉向" in function_name or "方向盤" in function_name:
            return TelemetryChartWidget("steering")
        elif "賽道" in function_name:
            params = self.main_window.get_current_parameters()
            parameter_provider = MainWindowParameterProvider(self.main_window)

            try:
                from modules.gui.race_analysis.track import TrackAnalysisUniversal

                module = TrackAnalysisUniversal(main_window=self.main_window)
                module.parameter_provider = parameter_provider

                try:
                    year_value = int(params['year'])
                except (TypeError, ValueError):
                    year_value = params['year']

                module.update_parameters(
                    year=year_value,
                    race=params['race'],
                    session=params['session']
                )

                logger.debug(f"[OK] [LEGACY->UNIVERSAL] 使用 TrackAnalysisUniversal: {params['year']} {params['race']} {params['session']}")
                return module.get_widget(), module

            except ImportError as e:
                logger.error(f"[ERROR] TrackAnalysisUniversal 導入失敗: {e}")
            except Exception as e:
                logger.error(f"[ERROR] TrackAnalysisUniversal 初始化失敗: {e}")
                import traceback
                traceback.print_exc()

            # 如果新模組失敗，退回舊版 Widget 提示
            placeholder = QLabel("[WARNING] 賽道分析模組不可用\n\n請使用菜單中的\n'[FINISH] 賽道軌跡分析'")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("""
                QLabel {
                    color: #666666;
                    font-size: 14px;
                    padding: 20px;
                    background: #F8F8F8;
                    border: 2px dashed #CCCCCC;
                    border-radius: 8px;
                }
            """)
            return placeholder
        elif "圈速" in function_name and "詳細圈速分析" not in function_name:
            return self.main_window.create_lap_analysis_table()
        elif "進站分析" in function_name:
            # 使用新的進站分析模組
            try:
                from modules.gui.race_analysis.pitstop import PitstopAnalysisModule
                logger.debug(f"[OK] [LEGACY] 創建進站分析模組")
                
                # 創建模組實例
                module = PitstopAnalysisModule()
                
                # 初始化模組
                if module.initialize_module():
                    logger.debug(f"[OK] [LEGACY] 進站分析模組初始化成功")
                    return module.get_widget(), module  # 返回 (widget, module) tuple
                else:
                    logger.error(f"[ERROR] [LEGACY] 進站分析模組初始化失敗")
                    raise Exception("模組初始化失敗")
                
            except ImportError as e:
                logger.error(f"[ERROR] 進站分析模組導入失敗: {e}")
                # 後備方案 - 顯示錯誤提示
                placeholder = QLabel("[ERROR] 進站分析模組不可用\n\n請檢查模組是否正確安裝")
                placeholder.setAlignment(Qt.AlignCenter)
                placeholder.setStyleSheet("""
                    QLabel {
                        color: #ff6666;
                        font-size: 14px;
                        padding: 20px;
                        background: #fff8f8;
                        border: 2px dashed #ffcccc;
                        border-radius: 8px;
                    }
                """)
                return placeholder
            except Exception as e:
                logger.error(f"[ERROR] 進站分析模組創建失敗: {e}")
                # 後備方案 - 顯示錯誤提示
                placeholder = QLabel(f"[ERROR] 進站分析模組錯誤\n\n{str(e)}")
                placeholder.setAlignment(Qt.AlignCenter)
                placeholder.setStyleSheet("""
                    QLabel {
                        color: #ff6666;
                        font-size: 14px;
                        padding: 20px;
                        background: #fff8f8;
                        border: 2px dashed #ffcccc;
                        border-radius: 8px;
                    }
                """)
                return placeholder
        else:
            # 預設創建速度遙測圖表
            return TelemetryChartWidget("speed")
