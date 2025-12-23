"""
PopoutChartUpdater - 圖表更新處理器

從 PopoutSubWindow 中提取的圖表更新邏輯。
負責處理各種分析類型的圖表更新操作。

Phase 5.1 重構 - 從 f1t_gui_main.py 提取
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from core.logger import get_logger
from typing import Dict
from typing import List
from typing import Optional
from typing import Any

if TYPE_CHECKING:
    from PyQt5.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class PopoutChartUpdater:
    """
    圖表更新處理器
    
    負責處理 PopoutSubWindow 中各種分析類型的圖表更新操作。
    支援速度、油門、RPM、檔位、加速度等分析類型。
    """
    
    # 視窗標題關鍵字映射到更新方法
    TITLE_KEYWORDS = {
        'acceleration': ['加速度分析', 'Acceleration Analysis', 'アクセラレーション分析'],
        'speed': ['速度分析', 'Speed Analysis'],
        'throttle': ['油門分析', 'Throttle Analysis', 'スロットル分析'],
        'rpm': ['RPM分析', 'RPM Analysis'],
        'gear': ['檔位分析', 'Gear Analysis', 'ギア分析'],
    }
    
    def __init__(self, popout_window: 'QWidget'):
        """
        初始化圖表更新處理器
        
        Args:
            popout_window: PopoutSubWindow 實例
        """
        self.window = popout_window
        
    def update_charts_and_analysis(self, json_data: Dict[str, Any]) -> None:
        """
        更新圖表和分析結果
        
        根據視窗標題自動選擇對應的更新方法。
        
        Args:
            json_data: JSON 格式的分析數據
        """
        logger.debug("[STATS] 開始更新圖表和分析結果...")
        
        try:
            window_title = self.window.windowTitle()
            logger.debug(f"[CHART UPDATE] 更新視窗: {window_title}")
            
            # 根據標題關鍵字選擇更新方法
            # 注意順序：先檢查更具體的「加速度分析」，再檢查「速度分析」（避免誤判）
            if self._title_matches(window_title, 'acceleration'):
                logger.debug("[ACCELERATION UPDATE] 檢測到加速度分析視窗，使用專用更新邏輯")
                self._update_acceleration_analysis_chart(json_data)
            elif self._title_matches(window_title, 'speed'):
                logger.debug("[SPEED UPDATE] 檢測到速度分析視窗，使用專用更新邏輯")
                self._update_speed_analysis_chart(json_data)
            elif self._title_matches(window_title, 'throttle'):
                logger.debug("[THROTTLE UPDATE] 檢測到油門分析視窗，使用專用更新邏輯")
                self._update_throttle_analysis_chart(json_data)
            elif self._title_matches(window_title, 'rpm'):
                logger.debug("[RPM UPDATE] 檢測到RPM分析視窗，使用專用更新邏輯")
                self._update_rpm_analysis_chart(json_data)
            elif self._title_matches(window_title, 'gear'):
                logger.debug("[GEAR UPDATE] 檢測到檔位分析視窗，使用專用更新邏輯")
                self._update_gear_analysis_chart(json_data)
            else:
                # 通用更新邏輯
                self._update_generic_charts(json_data)
                
            logger.debug("[OK] 圖表和分析結果更新完成")
            
        except Exception as e:
            logger.error(f"[ERROR] 圖表更新錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    def _title_matches(self, title: str, chart_type: str) -> bool:
        """檢查視窗標題是否匹配指定的圖表類型"""
        keywords = self.TITLE_KEYWORDS.get(chart_type, [])
        return any(keyword in title for keyword in keywords)
    
    def _update_generic_charts(self, json_data: Dict[str, Any]) -> None:
        """更新通用圖表"""
        # 更新遙測圖表
        if 'telemetry' in json_data:
            self.update_telemetry_chart(json_data['telemetry'])
            
        # 更新軌道地圖
        if 'track_data' in json_data:
            self.update_track_map(json_data['track_data'])
            
        # 更新分析數據
        if 'analysis_results' in json_data:
            self.update_analysis_data(json_data['analysis_results'])
    
    def _get_common_parameters(self) -> Dict[str, Any]:
        """獲取通用參數（年份、賽事、場次等）"""
        w = self.window
        
        year = getattr(w, 'local_year', None) or self._get_year_from_main_window()
        race = getattr(w, 'local_race', None) or self._get_race_from_main_window()
        session = getattr(w, 'local_session', None) or self._get_session_from_main_window()
        
        return {
            'year': year,
            'race': race,
            'session': session,
        }
    
    def _get_driver_lap_parameters(self) -> Dict[str, Any]:
        """獲取車手和圈數參數"""
        w = self.window
        
        # 嘗試從視窗的 combo 獲取
        if hasattr(w, 'driver1_combo'):
            driver1 = w.driver1_combo.currentText()
            driver2_data = w.driver2_combo.currentData() if hasattr(w, 'driver2_combo') else None
            driver2 = w.driver2_combo.currentText() if driver2_data is not None else driver1
            lap1 = w.lap1_spinbox.value() if hasattr(w, 'lap1_spinbox') else 1
            lap2 = w.lap2_spinbox.value() if hasattr(w, 'lap2_spinbox') else 1
            is_fastest = w.fastest_lap_checkbox.isChecked() if hasattr(w, 'fastest_lap_checkbox') else False
        else:
            # 使用本地參數或從主視窗獲取
            driver1 = getattr(w, 'local_driver1', None) or self._get_driver1_from_main_window()
            driver2 = getattr(w, 'local_driver2', None) or self._get_driver2_from_main_window()
            lap1 = getattr(w, 'local_lap1', None) or self._get_lap1_from_main_window()
            lap2 = getattr(w, 'local_lap2', None) or self._get_lap2_from_main_window()
            is_fastest = getattr(w, 'local_is_fastest', False) or self._get_fastest_from_main_window()
        
        return {
            'driver1': driver1,
            'driver2': driver2,
            'lap1': lap1,
            'lap2': lap2,
            'is_fastest_lap': is_fastest,
        }
    
    def _get_year_from_main_window(self) -> str:
        """從主視窗獲取年份"""
        if hasattr(self.window, 'get_current_year_from_main_window'):
            return self.window.get_current_year_from_main_window()
        return "2025"
    
    def _get_race_from_main_window(self) -> str:
        """從主視窗獲取賽事"""
        if hasattr(self.window, 'get_current_race_from_main_window'):
            return self.window.get_current_race_from_main_window()
        return "Japan"
    
    def _get_session_from_main_window(self) -> str:
        """從主視窗獲取場次"""
        if hasattr(self.window, 'get_current_session_from_main_window'):
            return self.window.get_current_session_from_main_window()
        return "R"
    
    def _get_driver1_from_main_window(self) -> str:
        """從主視窗獲取車手1"""
        if hasattr(self.window, 'get_current_driver1_from_main_window'):
            return self.window.get_current_driver1_from_main_window()
        return "VER"
    
    def _get_driver2_from_main_window(self) -> str:
        """從主視窗獲取車手2"""
        if hasattr(self.window, 'get_current_driver2_from_main_window'):
            return self.window.get_current_driver2_from_main_window()
        return "VER"
    
    def _get_lap1_from_main_window(self) -> int:
        """從主視窗獲取圈數1"""
        if hasattr(self.window, 'get_current_lap1_from_main_window'):
            return self.window.get_current_lap1_from_main_window()
        return 1
    
    def _get_lap2_from_main_window(self) -> int:
        """從主視窗獲取圈數2"""
        if hasattr(self.window, 'get_current_lap2_from_main_window'):
            return self.window.get_current_lap2_from_main_window()
        return 1
    
    def _get_fastest_from_main_window(self) -> bool:
        """從主視窗獲取是否使用最速圈"""
        if hasattr(self.window, 'get_current_fastest_from_main_window'):
            return self.window.get_current_fastest_from_main_window()
        return False
    
    def _find_widgets_by_type(self, widget_class: type) -> List['QWidget']:
        """
        遞歸查找指定類型的子組件
        
        Args:
            widget_class: 要查找的組件類型
            
        Returns:
            找到的組件列表
        """
        widgets = []
        
        if isinstance(self.window, widget_class):
            widgets.append(self.window)
        
        if hasattr(self.window, 'findChildren'):
            for child in self.window.findChildren(widget_class):
                widgets.append(child)
        
        return widgets
    
    def _update_speed_analysis_chart(self, json_data: Dict[str, Any]) -> None:
        """更新速度分析圖表"""
        logger.debug("[SPEED UPDATE] ========== 開始更新速度分析圖表 ==========")
        
        try:
            from modules.gui.lap_analysis.speed_analysis.speed_analysis_chart_widget import SpeedAnalysisChartWidget
            
            speed_widgets = self._find_widgets_by_type(SpeedAnalysisChartWidget)
            logger.debug(f"[SPEED UPDATE] 找到 {len(speed_widgets)} 個速度分析圖表組件")
            
            if speed_widgets:
                params = {**self._get_common_parameters(), **self._get_driver_lap_parameters()}
                
                for i, widget in enumerate(speed_widgets):
                    logger.debug(f"[SPEED UPDATE] 更新第 {i+1} 個速度分析圖表")
                    
                    if hasattr(widget, 'speed_loader'):
                        logger.debug(f"[SPEED UPDATE] 找到數據載入器，觸發重新載入")
                        logger.debug(f"[SPEED UPDATE] 使用參數: {params['driver1']} vs {params['driver2']}, "
                                   f"第{params['lap1']}圈 vs 第{params['lap2']}圈, 最速圈: {params['is_fastest_lap']}")
                        
                        widget.speed_loader.load_speed_data(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=params['driver1'],
                            driver2=params['driver2'],
                            lap1=params['lap1'],
                            lap2=params['lap2'],
                            is_fastest_lap=params['is_fastest_lap']
                        )
                        logger.debug("[SPEED UPDATE] 已觸發數據重新載入")
                    elif json_data and hasattr(widget, 'update_speed_data'):
                        logger.debug("[SPEED UPDATE] 嘗試直接使用JSON數據更新")
                        widget.update_speed_data(json_data)
                    else:
                        logger.debug("[SPEED UPDATE] 未找到數據載入器")
            else:
                logger.debug("[SPEED UPDATE] 未找到速度分析圖表組件")
                
            logger.debug("[SPEED UPDATE] ========== 速度分析圖表更新完成 ==========")
            
        except Exception as e:
            logger.error(f"[ERROR] [SPEED UPDATE] 速度分析圖表更新失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_throttle_analysis_chart(self, json_data: Dict[str, Any]) -> None:
        """更新油門分析圖表"""
        logger.debug("[THROTTLE UPDATE] ========== 開始更新油門分析圖表 ==========")
        
        try:
            from modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_chart_widget import ThrottleAnalysisChartWidget
            
            throttle_widgets = self._find_widgets_by_type(ThrottleAnalysisChartWidget)
            logger.debug(f"[THROTTLE UPDATE] 找到 {len(throttle_widgets)} 個油門分析圖表組件")
            
            if throttle_widgets:
                params = {**self._get_common_parameters(), **self._get_driver_lap_parameters()}
                
                for i, widget in enumerate(throttle_widgets):
                    logger.debug(f"[THROTTLE UPDATE] 更新第 {i+1} 個油門分析圖表")
                    
                    if hasattr(widget, 'throttle_loader'):
                        logger.debug(f"[THROTTLE UPDATE] 找到數據載入器，觸發重新載入")
                        logger.debug(f"[THROTTLE UPDATE] 使用參數: {params['driver1']} vs {params['driver2']}")
                        
                        widget.throttle_loader.load_throttle_data(
                            year=params['year'],
                            race=params['race'],
                            session=params['session'],
                            driver1=params['driver1'],
                            driver2=params['driver2'],
                            lap1=params['lap1'],
                            lap2=params['lap2'],
                            is_fastest_lap=params['is_fastest_lap']
                        )
                        logger.debug("[THROTTLE UPDATE] 已觸發數據重新載入")
                    elif json_data and hasattr(widget, 'update_throttle_data'):
                        logger.debug("[THROTTLE UPDATE] 嘗試直接使用JSON數據更新")
                        widget.update_throttle_data(json_data)
                    else:
                        logger.debug("[THROTTLE UPDATE] 未找到數據載入器")
            else:
                logger.debug("[THROTTLE UPDATE] 未找到油門分析圖表組件")
                
            logger.debug("[THROTTLE UPDATE] ========== 油門分析圖表更新完成 ==========")
            
        except Exception as e:
            logger.error(f"[ERROR] [THROTTLE UPDATE] 油門分析圖表更新失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_rpm_analysis_chart(self, json_data: Dict[str, Any]) -> None:
        """更新RPM分析圖表"""
        logger.debug("[RPM UPDATE] ========== 開始更新RPM分析圖表 ==========")
        
        try:
            from modules.gui.lap_analysis.rpm_analysis.rpm_analysis_chart_widget import RPMAnalysisChartWidget
            
            rpm_widgets = self._find_widgets_by_type(RPMAnalysisChartWidget)
            logger.debug(f"[RPM UPDATE] 找到 {len(rpm_widgets)} 個RPM分析圖表組件")
            
            if rpm_widgets:
                params = {**self._get_common_parameters(), **self._get_driver_lap_parameters()}
                
                for i, widget in enumerate(rpm_widgets):
                    logger.debug(f"[RPM UPDATE] 更新第 {i+1} 個RPM分析圖表")
                    
                    if hasattr(widget, 'rpm_loader'):
                        logger.debug(f"[RPM UPDATE] 找到數據載入器，觸發重新載入")
                        logger.debug(f"[RPM UPDATE] 使用參數: {params['driver1']} vs {params['driver2']}")
                        
                        widget.rpm_loader.load_rpm_data(
                            year=int(params['year']),
                            race=params['race'],
                            session=params['session'],
                            driver1=params['driver1'],
                            driver2=params['driver2'],
                            lap1=params['lap1'],
                            lap2=params['lap2'],
                            is_fastest_lap=params['is_fastest_lap']
                        )
                        logger.debug("[RPM UPDATE] 已觸發數據重新載入")
                    elif json_data and hasattr(widget, 'update_rpm_data'):
                        logger.debug("[RPM UPDATE] 嘗試直接使用JSON數據更新")
                        widget.update_rpm_data(json_data)
                    else:
                        logger.debug("[RPM UPDATE] 未找到數據載入器")
            else:
                logger.debug("[RPM UPDATE] 未找到RPM分析圖表組件")
                
            logger.debug("[RPM UPDATE] ========== RPM分析圖表更新完成 ==========")
            
        except Exception as e:
            logger.error(f"[ERROR] [RPM UPDATE] RPM分析圖表更新失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_gear_analysis_chart(self, json_data: Dict[str, Any]) -> None:
        """更新檔位分析圖表"""
        logger.debug("[GEAR UPDATE] ========== 開始更新檔位分析圖表 ==========")
        
        try:
            from modules.gui.lap_analysis.gear_analysis.gear_analysis_chart_widget import GearAnalysisChartWidget
            
            gear_widgets = self._find_widgets_by_type(GearAnalysisChartWidget)
            logger.debug(f"[GEAR UPDATE] 找到 {len(gear_widgets)} 個檔位分析圖表組件")
            
            if gear_widgets:
                params = {**self._get_common_parameters(), **self._get_driver_lap_parameters()}
                
                for i, widget in enumerate(gear_widgets):
                    logger.debug(f"[GEAR UPDATE] 更新第 {i+1} 個檔位分析圖表")
                    
                    if hasattr(widget, 'gear_loader'):
                        logger.debug(f"[GEAR UPDATE] 找到數據載入器，觸發重新載入")
                        logger.debug(f"[GEAR UPDATE] 使用參數: {params['driver1']} vs {params['driver2']}")
                        
                        widget.gear_loader.load_gear_data(
                            year=int(params['year']),
                            race=params['race'],
                            session=params['session'],
                            driver1=params['driver1'],
                            driver2=params['driver2'],
                            lap1=params['lap1'],
                            lap2=params['lap2'],
                            is_fastest_lap=params['is_fastest_lap']
                        )
                        logger.debug("[GEAR UPDATE] 已觸發數據重新載入")
                    elif json_data and hasattr(widget, 'update_gear_data'):
                        logger.debug("[GEAR UPDATE] 嘗試直接使用JSON數據更新")
                        widget.update_gear_data(json_data)
                    else:
                        logger.debug("[GEAR UPDATE] 未找到數據載入器")
            else:
                logger.debug("[GEAR UPDATE] 未找到檔位分析圖表組件")
                
            logger.debug("[GEAR UPDATE] ========== 檔位分析圖表更新完成 ==========")
            
        except Exception as e:
            logger.error(f"[ERROR] [GEAR UPDATE] 檔位分析圖表更新失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _update_acceleration_analysis_chart(self, json_data: Dict[str, Any]) -> None:
        """更新加速度分析圖表"""
        logger.debug("[ACCELERATION UPDATE] ========== 開始更新加速度分析圖表 ==========")
        
        try:
            from modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_chart_widget import accelerationAnalysisChartWidget
            
            acceleration_widgets = self._find_widgets_by_type(accelerationAnalysisChartWidget)
            logger.debug(f"[ACCELERATION UPDATE] 找到 {len(acceleration_widgets)} 個加速度分析圖表組件")
            
            if acceleration_widgets:
                params = {**self._get_common_parameters(), **self._get_driver_lap_parameters()}
                
                for i, widget in enumerate(acceleration_widgets):
                    logger.debug(f"[ACCELERATION UPDATE] 更新第 {i+1} 個加速度分析圖表")
                    
                    if hasattr(widget, 'acceleration_loader'):
                        logger.debug(f"[ACCELERATION UPDATE] 找到數據載入器，觸發重新載入")
                        logger.debug(f"[ACCELERATION UPDATE] 使用參數: {params['year']} {params['race']} {params['session']}")
                        logger.debug(f"[ACCELERATION UPDATE] 車手: {params['driver1']} vs {params['driver2']}, "
                                   f"圈數: {params['lap1']} vs {params['lap2']}, 最速圈: {params['is_fastest_lap']}")
                        
                        widget.acceleration_loader.load_acceleration_data(
                            year=int(params['year']),
                            race=params['race'],
                            session=params['session'],
                            driver1=params['driver1'],
                            driver2=params['driver2'],
                            lap1=params['lap1'],
                            lap2=params['lap2'],
                            is_fastest_lap=params['is_fastest_lap']
                        )
                        logger.debug("[ACCELERATION UPDATE] 已觸發數據重新載入")
                    elif json_data and hasattr(widget, 'update_acceleration_data'):
                        logger.debug("[ACCELERATION UPDATE] 嘗試直接使用JSON數據更新")
                        widget.update_acceleration_data(json_data)
                    else:
                        logger.debug("[ACCELERATION UPDATE] 未找到數據載入器")
            else:
                logger.debug("[ACCELERATION UPDATE] 未找到加速度分析圖表組件")
                
            logger.debug("[ACCELERATION UPDATE] ========== 加速度分析圖表更新完成 ==========")
            
        except Exception as e:
            logger.error(f"[ERROR] [ACCELERATION UPDATE] 加速度分析圖表更新失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def update_telemetry_chart(self, telemetry_data: Dict[str, Any]) -> None:
        """更新遙測圖表"""
        logger.debug("[CHART] 更新遙測圖表資料")
        # 實現具體的遙測圖表更新邏輯
        pass
    
    def update_track_map(self, track_data: Dict[str, Any]) -> None:
        """更新軌道地圖"""
        logger.debug("[MAP] 更新軌道地圖資料")
        # 實現具體的軌道地圖更新邏輯
        pass
    
    def update_analysis_data(self, analysis_data: Dict[str, Any]) -> None:
        """更新分析數據"""
        logger.debug("[STATS] 更新分析數據")
        # 實現具體的分析數據更新邏輯
        pass
