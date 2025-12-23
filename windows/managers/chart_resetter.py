# -*- coding: utf-8 -*-
"""
ChartResetter - 從 f1t_gui_main.py 提取
"""

from PyQt5.QtWidgets import QWidget
from core.logger import get_logger

from core.logger import get_logger

logger = get_logger(__name__)


class ChartResetter:
    """從 f1t_gui_main.py 提取的 reset_all_charts 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def reset_all_charts(self, mdi_area):
        """重置MDI區域中所有圖表以顯示完整數據範圍"""
        try:
            logger.debug(f"[REFRESH] 開始調整 MDI 區域中的所有圖表以顯示完整數據...")
            
            # 獲取所有子視窗
            subwindows = mdi_area.subWindowList()
            reset_count = 0
            
            logger.debug(f"[STATS] MDI區域中共有 {len(subwindows)} 個子視窗")
            
            def find_telemetry_widgets(widget):
                """遞歸查找 TelemetryChartWidget"""
                telemetry_widgets = []
                
                # 檢查當前widget
                if isinstance(widget, TelemetryChartWidget):
                    telemetry_widgets.append(widget)
                
                # 遞歸檢查所有子widget
                if hasattr(widget, 'children'):
                    for child in widget.children():
                        if isinstance(child, QWidget):
                            telemetry_widgets.extend(find_telemetry_widgets(child))
                
                return telemetry_widgets
            
            def find_universal_chart_widgets(widget):
                """遞歸查找 UniversalChartWidget"""
                from modules.gui.universal_chart_widget import UniversalChartWidget
                universal_widgets = []
                
                # 檢查當前widget
                if isinstance(widget, UniversalChartWidget):
                    universal_widgets.append(widget)
                
                # 遞歸檢查所有子widget
                if hasattr(widget, 'children'):
                    for child in widget.children():
                        if isinstance(child, QWidget):
                            universal_widgets.extend(find_universal_chart_widgets(child))
                
                return universal_widgets
            
            def find_speed_analysis_widgets(widget):
                """遞歸查找 SpeedAnalysisChartWidget"""
                from modules.gui.lap_analysis.speed_analysis.speed_analysis_chart_widget import SpeedAnalysisChartWidget
                speed_widgets = []
                
                # 檢查當前widget
                if isinstance(widget, SpeedAnalysisChartWidget):
                    speed_widgets.append(widget)
                
                # 遞歸檢查所有子widget
                if hasattr(widget, 'children'):
                    for child in widget.children():
                        if isinstance(child, QWidget):
                            speed_widgets.extend(find_speed_analysis_widgets(child))
                
                return speed_widgets
            
            def find_brake_analysis_widgets(widget):
                """遞歸查找 BrakeAnalysisChartWidget"""
                try:
                    from modules.gui.lap_analysis.brake_analysis.brake_analysis_chart_widget import BrakeAnalysisChartWidget
                    brake_widgets = []
                    
                    # 檢查當前widget
                    if isinstance(widget, BrakeAnalysisChartWidget):
                        brake_widgets.append(widget)
                    
                    # 遞歸檢查所有子widget
                    if hasattr(widget, 'children'):
                        for child in widget.children():
                            if isinstance(child, QWidget):
                                brake_widgets.extend(find_brake_analysis_widgets(child))
                    
                    return brake_widgets
                except ImportError:
                    return []
            
            def find_rpm_analysis_widgets(widget):
                """遞歸查找 RPMAnalysisChartWidget"""
                try:
                    from modules.gui.lap_analysis.rpm_analysis.rpm_analysis_chart_widget import RPMAnalysisChartWidget
                    rpm_widgets = []
                    
                    # 檢查當前widget
                    if isinstance(widget, RPMAnalysisChartWidget):
                        rpm_widgets.append(widget)
                    
                    # 遞歸檢查所有子widget
                    if hasattr(widget, 'children'):
                        for child in widget.children():
                            if isinstance(child, QWidget):
                                rpm_widgets.extend(find_rpm_analysis_widgets(child))
                    
                    return rpm_widgets
                except ImportError:
                    return []
            
            def find_gear_analysis_widgets(widget):
                """遞歸查找 GearAnalysisChartWidget"""
                try:
                    from modules.gui.lap_analysis.gear_analysis.gear_analysis_chart_widget import GearAnalysisChartWidget
                    gear_widgets = []
                    
                    # 檢查當前widget
                    if isinstance(widget, GearAnalysisChartWidget):
                        gear_widgets.append(widget)
                    
                    # 遞歸檢查所有子widget
                    if hasattr(widget, 'children'):
                        for child in widget.children():
                            if isinstance(child, QWidget):
                                gear_widgets.extend(find_gear_analysis_widgets(child))
                    
                    return gear_widgets
                except ImportError:
                    return []
            
            def find_throttle_analysis_widgets(widget):
                """遞歸查找 ThrottleAnalysisChartWidget"""
                try:
                    from modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_chart_widget import ThrottleAnalysisChartWidget
                    throttle_widgets = []
                    
                    # 檢查當前widget
                    if isinstance(widget, ThrottleAnalysisChartWidget):
                        throttle_widgets.append(widget)
                    
                    # 遞歸檢查所有子widget
                    if hasattr(widget, 'children'):
                        for child in widget.children():
                            if isinstance(child, QWidget):
                                throttle_widgets.extend(find_throttle_analysis_widgets(child))
                    
                    return throttle_widgets
                except ImportError:
                    return []
            
            def find_speeddiff_analysis_widgets(widget):
                """遞歸查找 SpeeddiffAnalysisChartWidget"""
                try:
                    from modules.gui.lap_analysis.speeddiff_analysis.speeddiff_analysis_chart_widget import SpeeddiffAnalysisChartWidget
                    speeddiff_widgets = []
                    
                    # 檢查當前widget
                    if isinstance(widget, SpeeddiffAnalysisChartWidget):
                        speeddiff_widgets.append(widget)
                    
                    # 遞歸檢查所有子widget
                    if hasattr(widget, 'children'):
                        for child in widget.children():
                            if isinstance(child, QWidget):
                                speeddiff_widgets.extend(find_speeddiff_analysis_widgets(child))
                    
                    return speeddiff_widgets
                except ImportError:
                    return []
            
            def find_distancediff_analysis_widgets(widget):
                """遞歸查找 distancediffAnalysisChartWidget"""
                try:
                    from modules.gui.lap_analysis.distancediff_analysis.distancediff_analysis_chart_widget import distancediffAnalysisChartWidget
                    distancediff_widgets = []
                    
                    # 檢查當前widget
                    if isinstance(widget, distancediffAnalysisChartWidget):
                        distancediff_widgets.append(widget)
                    
                    # 遞歸檢查所有子widget
                    if hasattr(widget, 'children'):
                        for child in widget.children():
                            if isinstance(child, QWidget):
                                distancediff_widgets.extend(find_distancediff_analysis_widgets(child))
                    
                    return distancediff_widgets
                except ImportError:
                    return []
            
            def find_acceleration_analysis_widgets(widget):
                """遞歸查找 accelerationAnalysisChartWidget"""
                try:
                    from modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_chart_widget import accelerationAnalysisChartWidget
                    acceleration_widgets = []
                    
                    # 檢查當前widget
                    if isinstance(widget, accelerationAnalysisChartWidget):
                        acceleration_widgets.append(widget)
                    
                    # 遞歸檢查所有子widget
                    if hasattr(widget, 'children'):
                        for child in widget.children():
                            if isinstance(child, QWidget):
                                acceleration_widgets.extend(find_acceleration_analysis_widgets(child))
                    
                    return acceleration_widgets
                except ImportError:
                    return []
            
            for i, subwindow in enumerate(subwindows):
                if subwindow and subwindow.widget():
                    widget = subwindow.widget()
                    widget_type = type(widget).__name__
                    logger.debug(f"[SEARCH] 檢查視窗 {i+1}: {widget_type}")
                    
                    # 遞歸查找所有 TelemetryChartWidget
                    telemetry_widgets = find_telemetry_widgets(widget)
                    # 遞歸查找所有 UniversalChartWidget
                    universal_widgets = find_universal_chart_widgets(widget)
                    # 遞歸查找所有分析模組組件
                    speed_widgets = find_speed_analysis_widgets(widget)
                    brake_widgets = find_brake_analysis_widgets(widget)
                    rpm_widgets = find_rpm_analysis_widgets(widget)
                    gear_widgets = find_gear_analysis_widgets(widget)
                    throttle_widgets = find_throttle_analysis_widgets(widget)
                    speeddiff_widgets = find_speeddiff_analysis_widgets(widget)
                    distancediff_widgets = find_distancediff_analysis_widgets(widget)
                    acceleration_widgets = find_acceleration_analysis_widgets(widget)
                    
                    logger.debug(f"  找到 {len(telemetry_widgets)} 個遙測圖表, {len(universal_widgets)} 個通用圖表")
                    logger.debug(f"  分析模組: 速度={len(speed_widgets)}, 煞車={len(brake_widgets)}, RPM={len(rpm_widgets)}, 檔位={len(gear_widgets)}, 油門={len(throttle_widgets)}")
                    logger.debug(f"  差異分析: 速度差={len(speeddiff_widgets)}, 距離差={len(distancediff_widgets)}, 加速度={len(acceleration_widgets)}")
                    
                    if telemetry_widgets:
                        for telemetry_widget in telemetry_widgets:
                            #print(f"[TARGET] 調整遙測圖表以顯示完整數據: {telemetry_widget.chart_type}")
                            
                            # 獲取圖表的實際尺寸
                            chart_width = telemetry_widget.width()
                            chart_height = telemetry_widget.height()
                            
                            if chart_width > 0 and chart_height > 0:
                                # [SEARCH] 根據實際數據範圍動態計算最佳縮放比例
                                
                                # 獲取實際數據範圍
                                x_data = getattr(telemetry_widget, 'x_data', None)
                                y_data = getattr(telemetry_widget, 'y_data', None)
                                
                                if x_data is not None and y_data is not None and len(x_data) > 0 and len(y_data) > 0:
                                    # 計算數據的實際範圍
                                    x_min, x_max = min(x_data), max(x_data)
                                    y_min, y_max = min(y_data), max(y_data)
                                    
                                    x_range = x_max - x_min if x_max != x_min else 1.0
                                    y_range = y_max - y_min if y_max != y_min else 1.0
                                    
                                    # 計算縮放比例，讓數據填滿90%的視窗空間
                                    # 假設視窗的基礎顯示範圍是 X: 0-100, Y: 0-100
                                    base_x_range = 100.0
                                    base_y_range = 100.0
                                    
                                    # 計算縮放比例
                                    optimal_x_scale = (base_x_range * 0.9) / x_range
                                    optimal_y_scale = (base_y_range * 0.9) / y_range
                                    
                                    # 限制縮放範圍，避免過度縮放
                                    optimal_x_scale = max(0.1, min(20.0, optimal_x_scale))
                                    optimal_y_scale = max(0.1, min(20.0, optimal_y_scale))
                                    
                                    # 計算偏移，讓數據居中顯示
                                    data_center_x = (x_min + x_max) / 2
                                    data_center_y = (y_min + y_max) / 2
                                    
                                    # 將數據中心移到視窗中心 (50, 50)
                                    optimal_x_offset = 50.0 - (data_center_x * optimal_x_scale)
                                    optimal_y_offset = 50.0 - (data_center_y * optimal_y_scale)
                                    
                                    # 應用計算出的縮放和偏移
                                    telemetry_widget.x_scale = optimal_x_scale
                                    telemetry_widget.y_scale = optimal_y_scale
                                    telemetry_widget.x_offset = optimal_x_offset
                                    telemetry_widget.y_offset = optimal_y_offset
                                    
                                    #print(f"[STATS] 數據範圍分析 {telemetry_widget.chart_type}:")
                                    #print(f"   X範圍: {x_min:.2f} ~ {x_max:.2f} (差值: {x_range:.2f})")
                                    #print(f"   Y範圍: {y_min:.2f} ~ {y_max:.2f} (差值: {y_range:.2f})")
                                    #print(f"   最佳縮放: X={optimal_x_scale:.2f}, Y={optimal_y_scale:.2f}")
                                    #print(f"   居中偏移: X={optimal_x_offset:.2f}, Y={optimal_y_offset:.2f}")
                                    
                                else:
                                    # 如果沒有數據，使用預設值
                                    telemetry_widget.x_scale = 1.0
                                    telemetry_widget.y_scale = 1.0
                                    telemetry_widget.x_offset = 0.0
                                    telemetry_widget.y_offset = 0.0
                                    #print(f"[WARNING] 無法獲取 {telemetry_widget.chart_type} 的數據範圍，使用預設縮放")
                                
                                # 重置拖拽狀態
                                telemetry_widget.is_dragging = False
                                telemetry_widget.last_mouse_pos = None
                                
                                # 重新繪製圖表
                                telemetry_widget.update()
                                reset_count += 1
                                
                                #print(f"[OK] 調整完成 {telemetry_widget.chart_type} - X縮放: {telemetry_widget.x_scale:.2f}, Y縮放: {telemetry_widget.y_scale:.2f}, X偏移: {telemetry_widget.x_offset:.1f}, Y偏移: {telemetry_widget.y_offset:.1f}")
                            else:
                                #print(f"[WARNING] 圖表 {telemetry_widget.chart_type} 尺寸無效，跳過調整")
                                pass
                    
                    # 處理通用圖表 (UniversalChartWidget)
                    if universal_widgets:
                        for universal_widget in universal_widgets:
                            logger.debug(f"[TARGET] 重置通用圖表: {universal_widget.title}")
                            universal_widget.reset_view()
                            reset_count += 1
                            logger.debug(f"[OK] 通用圖表重置完成: {universal_widget.title}")
                    
                    # 處理速度分析圖表 (SpeedAnalysisChartWidget)
                    if speed_widgets:
                        for speed_widget in speed_widgets:
                            logger.debug(f"[TARGET] 重置速度分析圖表")
                            speed_widget.reset_chart_view()
                            reset_count += 1
                            logger.debug(f"[OK] 速度分析圖表重置完成")
                    
                    # 處理煞車分析圖表 (BrakeAnalysisChartWidget) 
                    if brake_widgets:
                        for brake_widget in brake_widgets:
                            logger.debug(f"[TARGET] 重置煞車分析圖表")
                            if hasattr(brake_widget, 'reset_chart_view'):
                                brake_widget.reset_chart_view()
                            elif hasattr(brake_widget, 'chart_widget') and hasattr(brake_widget.chart_widget, 'reset_view'):
                                brake_widget.chart_widget.reset_view()
                            reset_count += 1
                            logger.debug(f"[OK] 煞車分析圖表重置完成")
                    
                    # 處理RPM分析圖表 (RPMAnalysisChartWidget)
                    if rpm_widgets:
                        for rpm_widget in rpm_widgets:
                            logger.debug(f"[TARGET] 重置RPM分析圖表")
                            if hasattr(rpm_widget, 'reset_chart_view'):
                                rpm_widget.reset_chart_view()
                            elif hasattr(rpm_widget, 'chart_widget') and hasattr(rpm_widget.chart_widget, 'reset_view'):
                                rpm_widget.chart_widget.reset_view()
                            reset_count += 1
                            logger.debug(f"[OK] RPM分析圖表重置完成")
                    
                    # 處理檔位分析圖表 (GearAnalysisChartWidget)
                    if gear_widgets:
                        for gear_widget in gear_widgets:
                            logger.debug(f"[TARGET] 重置檔位分析圖表")
                            if hasattr(gear_widget, 'reset_chart_view'):
                                gear_widget.reset_chart_view()
                            elif hasattr(gear_widget, 'chart_widget') and hasattr(gear_widget.chart_widget, 'reset_view'):
                                gear_widget.chart_widget.reset_view()
                            reset_count += 1
                            logger.debug(f"[OK] 檔位分析圖表重置完成")
                    
                    # 處理油門分析圖表 (ThrottleAnalysisChartWidget)
                    if throttle_widgets:
                        for throttle_widget in throttle_widgets:
                            logger.debug(f"[TARGET] 重置油門分析圖表")
                            throttle_widget.reset_chart_view()
                            reset_count += 1
                            logger.debug(f"[OK] 油門分析圖表重置完成")
                    
                    # 處理速度差異分析圖表 (SpeedDiffAnalysisChartWidget)
                    if speeddiff_widgets:
                        for speeddiff_widget in speeddiff_widgets:
                            logger.debug(f"[TARGET] 重置速度差異分析圖表")
                            if hasattr(speeddiff_widget, 'reset_chart_view'):
                                speeddiff_widget.reset_chart_view()
                            elif hasattr(speeddiff_widget, 'chart_widget') and hasattr(speeddiff_widget.chart_widget, 'reset_view'):
                                speeddiff_widget.chart_widget.reset_view()
                            reset_count += 1
                            logger.debug(f"[OK] 速度差異分析圖表重置完成")
                    
                    # 處理距離差異分析圖表 (DistanceDiffAnalysisChartWidget)
                    if distancediff_widgets:
                        for distancediff_widget in distancediff_widgets:
                            logger.debug(f"[TARGET] 重置距離差異分析圖表")
                            if hasattr(distancediff_widget, 'reset_chart_view'):
                                distancediff_widget.reset_chart_view()
                            elif hasattr(distancediff_widget, 'chart_widget') and hasattr(distancediff_widget.chart_widget, 'reset_view'):
                                distancediff_widget.chart_widget.reset_view()
                            reset_count += 1
                            logger.debug(f"[OK] 距離差異分析圖表重置完成")
                    
                    # 處理加速度分析圖表 (AccelerationAnalysisChartWidget)
                    if acceleration_widgets:
                        for acceleration_widget in acceleration_widgets:
                            logger.debug(f"[TARGET] 重置加速度分析圖表")
                            if hasattr(acceleration_widget, 'reset_chart_view'):
                                acceleration_widget.reset_chart_view()
                            elif hasattr(acceleration_widget, 'chart_widget') and hasattr(acceleration_widget.chart_widget, 'reset_view'):
                                acceleration_widget.chart_widget.reset_view()
                            reset_count += 1
                            logger.debug(f"[OK] 加速度分析圖表重置完成")
                    
                    # 檢查是否為其他類型的圖表或可縮放小部件
                    elif hasattr(widget, 'fit_to_view'):
                        # 如果小部件有適合視圖的方法
                        #print(f"[TOOL] 使用 fit_to_view 方法調整: {widget_type}")
                        widget.fit_to_view()
                        reset_count += 1
                        
                    elif hasattr(widget, 'zoom_to_fit'):
                        # 如果小部件有縮放適應方法
                        #print(f"[TOOL] 使用 zoom_to_fit 方法調整: {widget_type}")
                        widget.zoom_to_fit()
                        reset_count += 1
                    else:
                        #print(f"[WARNING] 視窗 {i+1} 中沒有找到可調整的圖表組件")
                        pass
                else:
                    #print(f"[WARNING] 視窗 {i+1} 沒有有效的widget")
                    pass
            
            logger.debug(f"[OK] 調整完成！共調整了 {reset_count} 個圖表以顯示完整數據")
            
        except Exception as e:
            logger.error(f"[ERROR] 調整圖表時發生錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    # 事件處理方法
