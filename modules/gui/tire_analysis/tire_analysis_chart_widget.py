#!/usr/bin/env python3
"""
TireAnalysisChartWidget - F1T 輪胎策略分析圖表組件        # 佈局參數
        self.left_margin = 60   # 左邊距：車手標籤需要的空間
        self.right_margin = 20  # 右邊距：最小留白
        self.top_margin = 40    # 頂部邊距：座標軸標籤
        self.bottom_margin = 50 # 底部邊距：圖例空間
        self.driver_height = 40
        self.stint_margin = 2=============================================

專門用於輪胎策略分析的圖表組件，支援：
- 橫向長條圖顯示 Stint
- 輪胎配方顏色編碼（SOFT=紅色, MEDIUM=黃色, HARD=白色）
- X軸圈數, Y軸車手
- Stint 中間顯示最快圈數
- 互動式數據提示

Author: F1T Team
Date: 2025-09-10
Version: 1.0.0
"""

import sys
import math
import logging
from typing import Dict, List, Any, Optional, Tuple
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QPoint
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QFont, QFontMetrics, QMouseEvent

# 導入翻譯函數
from core.gui_i18n import tr
# 導入集中式 logger
from core.logger import get_logger


class TireChartTheme:
    """輪胎策略分析專用圖表主題"""
    
    # 背景顏色
    BACKGROUND = QColor(250, 251, 252)
    MAIN_BACKGROUND = QColor(250, 251, 252)
    CHART_BACKGROUND = QColor(248, 249, 250)
    
    # 文字和標籤顏色
    LABEL_COLOR = QColor(50, 50, 50)
    TEXT_COLOR = QColor(50, 50, 50)
    AXIS_COLOR = QColor(50, 50, 50)
    GRID_COLOR = QColor(200, 200, 200)
    
    # 輪胎配方顏色
    SOFT_COLOR = QColor(220, 53, 69)           # 紅色 - 軟胎
    MEDIUM_COLOR = QColor(255, 193, 7)         # 黃色 - 中胎  
    HARD_COLOR = QColor(248, 249, 250)         # 白色 - 硬胎
    INTERMEDIATE_COLOR = QColor(40, 167, 69)   # 綠色 - 中性胎
    WET_COLOR = QColor(0, 123, 255)            # 藍色 - 雨胎
    
    # 邊框顏色
    HARD_BORDER_COLOR = QColor(108, 117, 125)  # 硬胎邊框
    DEFAULT_BORDER_COLOR = QColor(108, 117, 125)
    
    # Stint 相關顏色
    STINT_TEXT_COLOR = QColor(33, 37, 41)
    FASTEST_LAP_COLOR = QColor(220, 53, 69)
    FASTEST_LAP_TEXT_COLOR = QColor(0, 123, 255)  # 藍色：用於顯示最快圈速


class TireAnalysisChartWidget(QWidget):
    """輪胎策略分析圖表組件"""
    
    # 信號定義
    stint_selected = pyqtSignal(int, dict)  # Stint編號, Stint數據
    lap_selected = pyqtSignal(int, dict)    # 圈數, 圈數據
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 使用集中式 logger (符合 f1.* 命名空間)
        self._logger = get_logger("tire_chart", component="gui")
        
        # 數據存儲
        self.stint_data = []
        self.driver_data = {}
        self.chart_data = {}
        
        # 圖表參數
        self.margin = 50
        self.driver_height = 40
        self.stint_margin = 2
        
        # 輪胎配方顏色映射
        self.tire_colors = {
            'SOFT': TireChartTheme.SOFT_COLOR,
            'MEDIUM': TireChartTheme.MEDIUM_COLOR,
            'HARD': TireChartTheme.HARD_COLOR,
            'INTERMEDIATE': TireChartTheme.INTERMEDIATE_COLOR,
            'WET': TireChartTheme.WET_COLOR
        }
        
        # 座標軸範圍
        self.min_lap = 1
        self.max_lap = 60
        
        # 設置最小尺寸 - 與降雨分析一致
        self.setMinimumSize(200, 100)
        
        self._logger.debug("[TIRE_CHART] 輪胎策略圖表組件初始化完成")
    
    def update_data(self, data: Dict[str, Any], selected_driver: str = None):
        """更新圖表數據"""
        try:
            # 兼容 processed_data 格式：若上層傳入的是包含 charts_data 的包裝結構
            if isinstance(data, dict) and 'charts_data' in data and 'all_drivers_tire_strategy' not in data:
                data = data.get('charts_data', {})
                self._logger.debug("[TIRE_CHART] 解包 charts_data -> 原始 JSON")

            self._logger.debug("[TIRE_CHART] 收到數據更新: %s", type(data))
            self._logger.debug("[TIRE_CHART] 選中車手: %s", selected_driver)
            
            self.chart_data = data
            self.stint_data = []
            
            # 保存完整的車手數據，以便後續修正使用
            self.all_drivers_data = (data.get('drivers_analysis', {}) or      # 新格式 v2
                                   data.get('all_drivers_tire_strategy', {}) or 
                                   data.get('tire_timing_corrected', {}) or 
                                   data.get('tire_analysis', {}))
            
            # 從輪胎策略分析數據中提取所有車手的 Stint 數據
            # 支援多種 JSON 結構格式，優先支援新格式
            tire_analysis = (data.get('drivers_analysis', {}) or           # 新格式 v2
                           data.get('all_drivers_tire_strategy', {}) or 
                           data.get('tire_timing_corrected', {}) or 
                           data.get('tire_analysis', {}))
            drivers_analyzed = data.get('drivers_analyzed', list(tire_analysis.keys()))
            
            self._logger.debug(
                "[TIRE_CHART] 可用車手: %s (共 %s 位)",
                drivers_analyzed,
                len(drivers_analyzed),
            )
            
            # 處理所有車手的數據，不只是單一車手
            self.all_drivers_stint_data = {}
            
            for driver in drivers_analyzed:
                if driver in tire_analysis:
                    driver_data = tire_analysis[driver]
                    # 支援多種 stint 分析格式，優先使用修正後的數據
                    driver_stints = (driver_data.get('corrected_stint_analysis', []) or 
                                   driver_data.get('original_stint_analysis', []) or 
                                   driver_data.get('stint_analysis', []) or 
                                   driver_data.get('stints', []))
                    
                    # 為每個 Stint 添加 stint_number（如果沒有的話）
                    for i, stint in enumerate(driver_stints):
                        if 'stint_number' not in stint:
                            stint['stint_number'] = i + 1
                        # 添加最快圈數（估算為每個 Stint 的中間圈數）
                        if 'fastest_lap' not in stint:
                            stint['fastest_lap'] = (stint['start_lap'] + stint['end_lap']) // 2
                        # 添加車手名稱到 stint 數據中
                        stint['driver'] = driver
                    
                    self.all_drivers_stint_data[driver] = driver_stints
                    self._logger.debug("  %s: %s 個 Stint", driver, len(driver_stints))

                    # 調試：檢查數據來源和品質
                    if len(driver_stints) > 0:
                        first_stint = driver_stints[0]
                        compound = first_stint.get('compound') or first_stint.get('tire_compound')
                        self._logger.debug(
                            "    [%s] 第一個Stint配方: %s, 圈數: %s-%s",
                            driver,
                            compound,
                            first_stint.get('start_lap', '?'),
                            first_stint.get('end_lap', '?'),
                        )
                    else:
                        self._logger.warning("    [%s] 沒有有效的Stint數據", driver)
            
            # 為了向後相容性，設定第一個車手的數據為主要顯示數據
            if selected_driver and selected_driver in self.all_drivers_stint_data:
                self.stint_data = self.all_drivers_stint_data[selected_driver]
                self.chart_data['current_driver'] = selected_driver
            elif drivers_analyzed:
                # 如果沒有指定車手，使用第一個車手
                selected_driver = drivers_analyzed[0]
                self.stint_data = self.all_drivers_stint_data.get(selected_driver, [])
                self.chart_data['current_driver'] = selected_driver
            
            self._logger.debug("[TIRE_CHART] 主要顯示車手: %s", selected_driver)
            self._logger.debug(
                "[TIRE_CHART] 總共載入 %s 位車手的輪胎策略數據",
                len(self.all_drivers_stint_data),
            )
            
            # 如果沒有 Stint 數據，使用示例數據
            if not self.stint_data:
                self._logger.warning("[TIRE_CHART] 沒有找到 Stint 數據，使用示例數據")
                self.stint_data = [
                    {
                        'stint_number': 1,
                        'start_lap': 1,
                        'end_lap': 21,
                        'compound': 'MEDIUM',
                        'fastest_lap': 15,
                        'fastest_time': 93.064,
                        'avg_time': 93.672
                    },
                    {
                        'stint_number': 2,
                        'start_lap': 22,
                        'end_lap': 53,
                        'compound': 'HARD',
                        'fastest_lap': 35,
                        'fastest_time': 91.041,
                        'avg_time': 92.496
                    }
                ]
                selected_driver = "VER"
                self.chart_data['current_driver'] = selected_driver
            
            # 更新範圍 - 基於所有車手的數據
            if hasattr(self, 'all_drivers_stint_data') and self.all_drivers_stint_data:
                all_stints = []
                for driver_stints in self.all_drivers_stint_data.values():
                    all_stints.extend(driver_stints)

                if all_stints:
                    start_candidates = []
                    end_candidates = []
                    for stint in all_stints:
                        start_val = self._safe_lap_value(stint.get('start_lap'))
                        end_val = self._safe_lap_value(stint.get('end_lap'))
                        if start_val is not None:
                            start_candidates.append(start_val)
                        if start_val is not None and end_val is not None and end_val >= start_val:
                            end_candidates.append(end_val)

                    total_lap_candidates = self._collect_total_laps()

                    if start_candidates:
                        self.min_lap = min(start_candidates)
                    else:
                        self.min_lap = 1

                    lap_candidates = list(end_candidates)
                    lap_candidates.extend(total_lap_candidates)

                    if lap_candidates:
                        self.max_lap = max(lap_candidates)
                    else:
                        self.max_lap = max(self.min_lap, 60)
            elif self.stint_data:
                start_candidates = [
                    self._safe_lap_value(stint.get('start_lap'))
                    for stint in self.stint_data
                ]
                start_candidates = [lap for lap in start_candidates if lap is not None]

                end_candidates = [
                    self._safe_lap_value(stint.get('end_lap'))
                    for stint in self.stint_data
                ]
                end_candidates = [lap for lap in end_candidates if lap is not None]

                if start_candidates:
                    self.min_lap = min(start_candidates)
                else:
                    self.min_lap = 1

                if end_candidates:
                    self.max_lap = max(end_candidates)
                else:
                    self.max_lap = max(self.min_lap, 60)

            self.max_lap = max(self.min_lap, self.max_lap)
            
            self._logger.debug("[TIRE_CHART] 圈數範圍: %s-%s", self.min_lap, self.max_lap)
            self._logger.debug(
                "[TIRE_CHART] 顯示 %s 位車手的輪胎策略",
                len(self.all_drivers_stint_data) if hasattr(self, 'all_drivers_stint_data') else 0,
            )
            
            self.update()
            
        except Exception:  # noqa: BLE001
            self._logger.exception("[TIRE_CHART] 數據更新錯誤")
    
    def _safe_lap_value(self, value: Any) -> Optional[int]:
        """將圈數值轉換為整數，忽略無效資料。"""
        try:
            if value is None or isinstance(value, bool):
                return None
            if isinstance(value, (int, float)):
                return int(value)
            if isinstance(value, str):
                cleaned = value.strip()
                if cleaned.isdigit():
                    return int(cleaned)
            return None
        except Exception:  # noqa: BLE001 - 防禦性處理
            return None

    def _collect_total_laps(self) -> List[int]:
        """收集各資料來源的總圈數作為 X 軸範圍候選。"""
        totals: List[int] = []

        driver_source = getattr(self, 'all_drivers_data', None)
        if isinstance(driver_source, dict):
            for driver_data in driver_source.values():
                if not isinstance(driver_data, dict):
                    continue
                summary = driver_data.get('driver_summary') or {}
                candidate = self._safe_lap_value(summary.get('total_laps'))
                if candidate is not None:
                    totals.append(candidate)

        if isinstance(self.chart_data, dict):
            metadata = self.chart_data.get('metadata', {}) or {}
            analysis_info = self.chart_data.get('analysis_info', {}) or {}
            for value in (
                analysis_info.get('total_laps'),
                metadata.get('total_laps'),
                metadata.get('race_total_laps'),
            ):
                candidate = self._safe_lap_value(value)
                if candidate is not None:
                    totals.append(candidate)

        return totals

    def paintEvent(self, event):
        """繪製圖表"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            
            # 清空背景
            painter.fillRect(self.rect(), TireChartTheme.BACKGROUND)
            
            # 計算圖表區域 - 優化邊距
            chart_rect = QRect(
                35,  # 左邊距：車手標籤需要空間
                15,  # 上邊距：減少不必要的空白
                self.width() - 45,  # 右邊距：只留10px
                self.height() - 70  # 下邊距：為X軸標籤和標題預留空間
            )
            
            # 繪製圖表背景
            painter.fillRect(chart_rect, TireChartTheme.CHART_BACKGROUND)
            
            if not self.stint_data:
                # 沒有數據時顯示提示
                painter.setPen(QPen(TireChartTheme.TEXT_COLOR))
                painter.drawText(chart_rect, Qt.AlignCenter, "等待輪胎策略數據...")
                return
            
            # 繪製座標軸
            self._draw_axes(painter, chart_rect)
            
            # 繪製 Stint 長條
            self._draw_stints(painter, chart_rect)
            
            # 繪製圖例 (已取消顯示)
            # self._draw_legend(painter)
        finally:
            # 🔑 確保總是釋放 QPainter 資源
            painter.end()
    
    def _draw_axes(self, painter: QPainter, chart_rect: QRect):
        """繪製座標軸"""
        painter.setPen(QPen(TireChartTheme.AXIS_COLOR, 2))
        
        # X軸 (底部)
        painter.drawLine(chart_rect.bottomLeft(), chart_rect.bottomRight())
        
        # Y軸 (左側)  
        painter.drawLine(chart_rect.bottomLeft(), chart_rect.topLeft())
        
        # 繪製X軸刻度 (圈數)
        painter.setPen(QPen(TireChartTheme.LABEL_COLOR))
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)
        
        # X軸標籤
        lap_range = max(1, self.max_lap - self.min_lap)
        step = max(1, lap_range // 10)  # 大約10個刻度

        for lap in range(self.min_lap, self.max_lap + 1, step):
            lap_position = (lap - self.min_lap) / lap_range
            x = chart_rect.left() + lap_position * chart_rect.width()
            painter.drawLine(int(x), chart_rect.bottom(), int(x), chart_rect.bottom() + 5)
            painter.drawText(int(x - 10), chart_rect.bottom() + 20, str(lap))
        
        # 繪製X軸標題
        painter.drawText(chart_rect.center().x() - 30, chart_rect.bottom() + 40, tr("lap_number_axis", "圈數 (Lap)"))
    
    def _draw_stints(self, painter: QPainter, chart_rect: QRect):
        """繪製所有車手的 Stint 長條"""
        if not hasattr(self, 'all_drivers_stint_data') or not self.all_drivers_stint_data:
            return
        
        lap_range = self.max_lap - self.min_lap
        drivers = list(self.all_drivers_stint_data.keys())
        num_drivers = len(drivers)
        
        if num_drivers == 0:
            return
        
        # 預先計算每種輪胎配方的最快車手
        fastest_per_compound = self._calculate_fastest_per_compound()
        
        # 計算每個車手行的高度
        available_height = chart_rect.height() - 20  # 減少預留空間
        driver_row_height = available_height // num_drivers
        stint_height = min(25, driver_row_height - 5)  # 限制最大高度並留出間距
        
        painter.setPen(QPen(TireChartTheme.LABEL_COLOR))
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        
        # 為每位車手繪製一行
        for driver_index, driver in enumerate(drivers):
            driver_stints = self.all_drivers_stint_data[driver]
            y_base = chart_rect.top() + 10 + driver_index * driver_row_height  # 減少頂部偏移
            
            # 繪製車手名稱標籤 - 統一字體設置
            painter.setPen(QPen(TireChartTheme.LABEL_COLOR))
            font = QFont()
            font.setPointSize(8)   # 統一車手名稱字體大小
            painter.setFont(font)
            # 計算車手名稱的垂直中心位置，與 stint 矩形中心對齊
            name_y = y_base + stint_height // 2 + 3  # 微調字體基準線位置
            painter.drawText(chart_rect.left() - 30, name_y, driver)
            
            # 為該車手的每個 Stint 繪製長條
            for stint in driver_stints:
                start_lap = stint['start_lap']
                end_lap = stint['end_lap']
                
                # 數據驗證：修正明顯錯誤的 end_lap
                if end_lap <= start_lap:
                    # 改為 DEBUG 級別，避免在正常修正流程中產生警告噪音
                    self._logger.debug(
                        "[TIRE_CHART] 檢測到需要修正的 end_lap: driver=%s, start=%s, end=%s",
                        driver,
                        start_lap,
                        stint['end_lap'],
                    )
                    
                    if 'length' in stint and stint['length'] > 0:
                        # 使用 length 字段重新計算 end_lap
                        length = stint.get('length', 1)
                        end_lap = start_lap + length - 1
                        self._logger.debug(
                            "[TIRE_CHART] 使用 length 修正: driver=%s, length=%s, 新end=%s",
                            driver,
                            length,
                            end_lap,
                        )
                    else:
                        # 嘗試根據車手在該配方上的總圈數估算
                        compound = (stint.get('compound') or 
                                   stint.get('tire_compound') or 
                                   stint.get('tyre_compound', 'MEDIUM'))
                        
                        # 從 tire_performance 獲取該配方的總圈數
                        if hasattr(self, 'all_drivers_data') and driver in self.all_drivers_data:
                            tire_perf = self.all_drivers_data[driver].get('tire_performance', {})
                            if compound in tire_perf:
                                laps_used = tire_perf[compound].get('laps_used', 15)
                                end_lap = start_lap + laps_used - 1
                                self._logger.debug("[TIRE_CHART] 使用 tire_performance 修正: driver=%s, compound=%s, laps_used=%s, 新end=%s", driver, compound, laps_used, end_lap)
                            else:
                                # 最後的備用方案：估算合理圈數
                                end_lap = start_lap + 15
                                self._logger.debug("[TIRE_CHART] 使用默認估算: driver=%s, 新end=%s", driver, end_lap)
                        else:
                            end_lap = start_lap + 15
                            self._logger.debug("[TIRE_CHART] 使用默認估算: driver=%s, 新end=%s", driver, end_lap)
                    
                    # 確保修正後的 end_lap 不會超過比賽總圈數（通常是53圈）
                    if end_lap > 60:
                        end_lap = 53
                        self._logger.debug("[TIRE_CHART] 限制最大圈數: driver=%s, 最終end=%s", driver, end_lap)
                    
                    # 如果修正後仍然無效，強制設置一個最小值
                    if end_lap < start_lap:
                        self._logger.debug(
                            "[TIRE_CHART] 修正異常stint範圍: driver=%s, start=%s, end=%s -> end調整為單圈", 
                            driver,
                            start_lap,
                            end_lap,
                        )
                        end_lap = start_lap
                
                # 支援多種配方字段格式
                compound = (stint.get('compound') or 
                           stint.get('tire_compound') or 
                           stint.get('tyre_compound', 'MEDIUM'))
                fastest_lap = stint.get('fastest_lap', start_lap)
                
                # 計算水平位置
                x_start = chart_rect.left() + (start_lap - self.min_lap) * chart_rect.width() / lap_range
                x_end = chart_rect.left() + (end_lap - self.min_lap + 1) * chart_rect.width() / lap_range
                width = x_end - x_start
                
                # 選擇顏色
                color = self.tire_colors.get(compound, TireChartTheme.MEDIUM_COLOR)
                
                # 繪製長條
                stint_rect = QRect(int(x_start), y_base, int(width), stint_height)
                painter.fillRect(stint_rect, color)
                
                # 繪製邊框 (硬胎需要黑邊框)
                if compound == 'HARD':
                    painter.setPen(QPen(TireChartTheme.HARD_BORDER_COLOR, 2))
                else:
                    painter.setPen(QPen(TireChartTheme.DEFAULT_BORDER_COLOR, 1))
                painter.drawRect(stint_rect)
                
                # 在長條中間顯示該輪胎配方使用的圈數
                # 智能顯示邏輯：根據視窗大小和stint尺寸決定是否顯示文字
                min_width_for_text = 30  # 降低最小寬度需求，因為圈數文字較短
                min_height_for_text = 15  # 最小高度需求
                
                if width > min_width_for_text and stint_height > min_height_for_text:
                    # 計算該 stint 使用的圈數
                    laps_used = end_lap - start_lap + 1
                    
                    # 設置文字顏色
                    painter.setPen(QPen(TireChartTheme.STINT_TEXT_COLOR))  # 普通黑色
                    
                    # 根據可用空間調整字體大小
                    font = QFont()
                    if stint_height < 20:
                        font_size = 7  # 稍微加大字體，因為只顯示數字
                    elif stint_height < 25:
                        font_size = 8  # 中等字體
                    else:
                        font_size = 9  # 較大字體
                    
                    font.setPointSize(font_size)
                    font.setBold(True)
                    painter.setFont(font)
                    
                    # 顯示圈數（只顯示數字）
                    laps_text = str(laps_used)
                    # 調整文字位置，稍微向下偏移以獲得更好的視覺中心
                    text_rect = QRect(int(x_start), y_base + 2, int(width), stint_height - 4)
                    painter.drawText(text_rect, Qt.AlignCenter, laps_text)
    
    def _calculate_fastest_per_compound(self) -> Dict[str, str]:
        """計算每種輪胎配方的最快車手"""
        fastest_per_compound = {}
        
        try:
            if not self.all_drivers_data:
                return fastest_per_compound
            
            # 收集每種配方的所有車手最佳圈速
            compound_times = {}  # {compound: [(driver, best_time), ...]}
            
            for driver in self.all_drivers_data:
                driver_data = self.all_drivers_data[driver]
                if 'tire_performance' in driver_data:
                    tire_perf = driver_data['tire_performance']
                    for compound, perf_data in tire_perf.items():
                        if 'fastest_lap_time' in perf_data and perf_data['fastest_lap_time'] > 0:
                            if compound not in compound_times:
                                compound_times[compound] = []
                            compound_times[compound].append((driver, perf_data['fastest_lap_time']))
            
            # 找出每種配方的最快車手
            for compound, driver_times in compound_times.items():
                if driver_times:
                    fastest_driver = min(driver_times, key=lambda x: x[1])  # 找最快時間
                    fastest_per_compound[compound] = fastest_driver[0]  # 只保存車手名
                    self._logger.debug(
                        "[TIRE_CHART] %s 最快車手: %s (%.3fs)",
                        compound,
                        fastest_driver[0],
                        fastest_driver[1],
                    )
            
        except Exception:  # noqa: BLE001
            self._logger.exception("[TIRE_CHART] 計算最快車手失敗")
        
        return fastest_per_compound
    
    def _get_best_lap_time(self, driver: str, compound: str) -> float:
        """獲取指定車手指定輪胎配方的最佳圈速"""
        try:
            if not self.all_drivers_data or driver not in self.all_drivers_data:
                return None
                
            driver_data = self.all_drivers_data[driver]
            
            # 檢查 tire_performance 數據
            if 'tire_performance' in driver_data:
                tire_perf = driver_data['tire_performance']
                if compound in tire_perf and 'fastest_lap_time' in tire_perf[compound]:
                    return tire_perf[compound]['fastest_lap_time']
            
            return None
        except Exception:  # noqa: BLE001
            self._logger.exception(
                "[TIRE_CHART] 獲取最佳圈速失敗: driver=%s, compound=%s",
                driver,
                compound,
            )
            return None
    
    def _format_lap_time(self, lap_time_seconds: float) -> str:
        """將圈速秒數格式化為 M:SS.00 格式"""
        try:
            if lap_time_seconds is None or lap_time_seconds <= 0:
                return ""
            
            # 計算分鐘和秒數
            minutes = int(lap_time_seconds // 60)
            seconds = lap_time_seconds % 60
            
            # 格式化為 M:SS.00
            return f"{minutes}:{seconds:05.2f}"
        except Exception:  # noqa: BLE001
            self._logger.exception(
                "[TIRE_CHART] 格式化圈速失敗: %s",
                lap_time_seconds,
            )
            return ""

    def _draw_legend(self, painter: QPainter):
        """繪製圖例"""
        legend_y = self.height() - 30
        legend_x = 35  # 調整圖例位置
        
        painter.setPen(QPen(TireChartTheme.TEXT_COLOR))
        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        
        # 輪胎配方圖例
        compounds = ['SOFT', 'MEDIUM', 'HARD']
        for i, compound in enumerate(compounds):
            x = legend_x + i * 80
            color = self.tire_colors[compound]
            
            # 繪製色塊
            painter.fillRect(x, legend_y, 15, 15, color)
            if compound == 'HARD':
                painter.setPen(QPen(TireChartTheme.HARD_BORDER_COLOR, 1))
                painter.drawRect(x, legend_y, 15, 15)
            
            # 繪製標籤
            painter.setPen(QPen(TireChartTheme.TEXT_COLOR))
            painter.drawText(x + 20, legend_y + 12, compound)
    
    def mousePressEvent(self, event: QMouseEvent):
        """處理滑鼠點擊事件"""
        if event.button() == Qt.LeftButton:
            # 檢查是否點擊在 Stint 上
            clicked_stint = self._get_stint_at_position(event.pos())
            if clicked_stint:
                self.stint_selected.emit(clicked_stint['stint_number'], clicked_stint)
                self._logger.debug(
                    "[TIRE_CHART] 選中 Stint %s",
                    clicked_stint['stint_number'],
                )
    
    def _get_stint_at_position(self, pos: QPoint) -> Optional[Dict]:
        """獲取指定位置的 Stint 數據"""
        if not self.stint_data:
            return None
        
        chart_rect = QRect(
            self.margin,
            self.margin, 
            self.width() - 2 * self.margin,
            self.height() - 2 * self.margin
        )
        
        lap_range = self.max_lap - self.min_lap
        y_base = chart_rect.top() + 20
        stint_height = self.driver_height - 2 * self.stint_margin
        
        # 檢查Y座標是否在 Stint 範圍內
        if not (y_base <= pos.y() <= y_base + stint_height):
            return None
        
        # 檢查X座標對應的 Stint
        for stint in self.stint_data:
            start_lap = stint['start_lap']
            end_lap = stint['end_lap']
            
            x_start = chart_rect.left() + (start_lap - self.min_lap) * chart_rect.width() / lap_range
            x_end = chart_rect.left() + (end_lap - self.min_lap + 1) * chart_rect.width() / lap_range
            
            if x_start <= pos.x() <= x_end:
                return stint
        
        return None


if __name__ == "__main__":
    """測試用例"""
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # 創建測試視窗
    widget = TireAnalysisChartWidget()
    
    # 模擬測試數據
    test_data = {
        'driver': 'VER',
        'stint_analysis': {
            'stints': [
                {
                    'stint_number': 1,
                    'start_lap': 1,
                    'end_lap': 21,
                    'compound': 'MEDIUM',
                    'fastest_lap': 15,
                    'fastest_time': '1:33.064',
                    'avg_time': '1:33.672'
                },
                {
                    'stint_number': 2, 
                    'start_lap': 22,
                    'end_lap': 53,
                    'compound': 'HARD',
                    'fastest_lap': 35,
                    'fastest_time': '1:31.041',
                    'avg_time': '1:32.496'
                }
            ]
        }
    }
    
    # 連接測試信號
    demo_logger = get_logger("tire_chart.demo", component="gui")

    def on_stint_selected(stint_num, stint_data):
        demo_logger.debug("選中 Stint %s: %s", stint_num, stint_data)
    
    widget.stint_selected.connect(on_stint_selected)
    
    # 更新數據並顯示
    widget.update_data(test_data)
    widget.show()
    
    demo_logger.info("輪胎策略圖表組件測試啟動")
    sys.exit(app.exec_())
