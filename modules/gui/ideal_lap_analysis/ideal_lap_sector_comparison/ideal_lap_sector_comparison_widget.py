#!/usr/bin/env python3
"""
理想圈分段對比圖表元件 - 簡潔條狀圖版本
Ideal Lap Sector Comparison Chart Widget - Compact Bar Chart Version

✅ 版本 2: 簡潔條狀圖
✅ 表格式佈局 + 分段差異指示器 + 累積差異棒狀圖

作者: F1T Team
日期: 2025-10-10
版本: 2.0.0 (簡潔條狀圖)
"""

from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QRect, QPoint, pyqtSignal, QRectF
from PyQt5.QtGui import (
    QPainter, QPen, QColor, QBrush, QFont, QFontMetrics,
    QMouseEvent, QImage
)
from typing import List, Dict, Optional, Any

# ✅ 導入國際化和車隊配色
from core.gui_i18n import tr
from modules.gui.themes import color_palette_provider


class IdealLapSectorComparisonWidget(QWidget):
    """
    理想圈分段對比圖表元件 - 簡潔條狀圖版本
    
    特點：
    - 表格式佈局
    - 分段差異顏色指示器 (綠/黃/紅)
    - 累積差異棒狀圖
    - 清晰易讀
    """
    
    # 信號定義
    bar_clicked = pyqtSignal(str)  # 點擊時發射車手代碼
    sort_changed = pyqtSignal(str)  # 排序變更
    
    def __init__(self, parent=None):
        """初始化圖表元件"""
        super().__init__(parent)
        
        # ✅ 啟用滑鼠追蹤和設定最小尺寸
        self.setMouseTracking(True)
        self.setMinimumSize(800, 400)
        
        # 數據屬性
        self.comparison_data: List[Dict] = []
        self.statistics: Dict[str, Any] = {}
        self.current_data: Optional[Dict] = None
        self.current_sort = "position"
        
        # 領先者分段時間 (用於計算差異)
        self.leader_s1 = 0.0
        self.leader_s2 = 0.0
        self.leader_s3 = 0.0
        
        # 累積差異範圍 (用於計算棒狀圖相對長度)
        self.max_cumulative = 0.0
        
        # 懸停狀態
        self.hover_driver = None
        self.hover_row = -1
        
        # 🆕 數據過濾管理
        self.hidden_drivers = set()  # 儲存被隱藏的車手代碼集合
        
        # 佈局參數
        self.header_height = 60
        self.row_height = 45
        self.margin_left = 10
        self.margin_right = 10
        
        # 列寬定義
        self.col_pos_width = 40
        self.col_driver_width = 70
        self.col_sector_width = 80
        self.col_cumulative_start = 380
        
    def update_data(self, data: Dict[str, Any]):
        """
        更新數據並觸發重繪
        
        Args:
            data: 包含 analysis_result.ranking 或 comparison_data 的字典
        """
        try:
            if not data or not isinstance(data, dict):
                print("[WARNING] [SECTOR_COMPARISON_V2] 無效的數據格式")
                return
            
            self.current_data = data
            
            # ✅ 提取排名數據
            if 'analysis_result' in data:
                self.comparison_data = data['analysis_result'].get('ranking', [])
                self.statistics = data['analysis_result'].get('summary', {})
            else:
                self.comparison_data = data.get('comparison_data', [])
                self.statistics = data.get('statistics', {})
            
            self._ensure_palette_for_data(data)
            
            if not self.comparison_data:
                print("[WARNING] [SECTOR_COMPARISON_V2] 沒有對比數據")
                self.update()
                return
            
            # 計算領先者的分段時間
            self._calculate_leader_times()
            
            print(f"[SECTOR_COMPARISON_V2] 更新數據: {len(self.comparison_data)} 位車手")
            self.update()  # 觸發重繪
            
        except Exception as e:
            print(f"[ERROR] [SECTOR_COMPARISON_V2] 更新數據失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _ensure_palette_for_data(self, data: Dict[str, Any]) -> None:
        """確保車隊配色匹配數據的賽季"""
        if not isinstance(data, dict):
            return

        metadata = data.get("metadata", {}) or {}
        target_year = metadata.get("year")

        try:
            if target_year is not None:
                color_palette_provider.ensure_loaded(year=int(target_year))
            else:
                color_palette_provider.ensure_loaded()
        except Exception:
            pass
    
    def _calculate_leader_times(self):
        """
        計算領先者(第一名)的分段時間和最大累積差異
        
        ⚠️ 重要變更：不再使用領先者的分段作為基準
        改為比較每個車手自己的 "理想圈分段 vs 最速圈分段"
        """
        if not self.comparison_data:
            return
        
        # 計算最大累積差異（用於棒狀圖比例）
        max_cumulative = 0.0
        for driver_data in self.comparison_data:
            # 提取該車手的理想圈和最速圈分段時間
            ideal_s1, ideal_s2, ideal_s3, fastest_s1, fastest_s2, fastest_s3 = self._extract_sector_deltas(driver_data)
            
            # 計算累積差異（最速圈 - 理想圈）
            delta_s1 = fastest_s1 - ideal_s1 if (fastest_s1 and ideal_s1) else 0
            delta_s2 = fastest_s2 - ideal_s2 if (fastest_s2 and ideal_s2) else 0
            delta_s3 = fastest_s3 - ideal_s3 if (fastest_s3 and ideal_s3) else 0
            cumulative = delta_s1 + delta_s2 + delta_s3
            
            if cumulative > max_cumulative:
                max_cumulative = cumulative
        
        self.max_cumulative = max_cumulative
        print(f"[SECTOR_COMPARISON_V2] 最大累積差異: {self.max_cumulative:.3f}s")
    
    def _extract_sector_deltas(self, driver_data: Dict[str, Any]) -> tuple:
        """
        提取理想圈和最速圈的分段時間
        
        Returns:
            tuple: (ideal_s1, ideal_s2, ideal_s3, fastest_s1, fastest_s2, fastest_s3)
        """
        sector_breakdown = driver_data.get("sector_breakdown", {})
        
        if not sector_breakdown:
            return (0, 0, 0, 0, 0, 0)
        
        # 新格式：同時包含 ideal_time 和 fastest_time
        if "ideal_time" in sector_breakdown.get("sector_1", {}):
            ideal_s1 = sector_breakdown.get("sector_1", {}).get("ideal_time", 0)
            ideal_s2 = sector_breakdown.get("sector_2", {}).get("ideal_time", 0)
            ideal_s3 = sector_breakdown.get("sector_3", {}).get("ideal_time", 0)
            
            fastest_s1 = sector_breakdown.get("sector_1", {}).get("fastest_time", 0)
            fastest_s2 = sector_breakdown.get("sector_2", {}).get("fastest_time", 0)
            fastest_s3 = sector_breakdown.get("sector_3", {}).get("fastest_time", 0)
        else:
            # 舊格式：只有 time（理想圈時間），需要從 laps 中找最速圈
            ideal_s1 = sector_breakdown.get("sector_1", {}).get("time", 0)
            ideal_s2 = sector_breakdown.get("sector_2", {}).get("time", 0)
            ideal_s3 = sector_breakdown.get("sector_3", {}).get("time", 0)
            
            # 從 laps 中找最速圈的分段時間
            fastest_s1, fastest_s2, fastest_s3 = self._find_fastest_lap_sectors(driver_data)
        
        return (ideal_s1, ideal_s2, ideal_s3, fastest_s1, fastest_s2, fastest_s3)
    
    def _find_fastest_lap_sectors(self, driver_data: Dict[str, Any]) -> tuple:
        """
        從 laps 中找到最速圈的分段時間（向下相容舊格式）
        
        Returns:
            tuple: (s1, s2, s3)
        """
        laps = driver_data.get("laps", [])
        if not laps:
            return (0, 0, 0)
        
        # 找到最速圈
        valid_laps = [lap for lap in laps if lap.get("is_valid", False)]
        if not valid_laps:
            return (0, 0, 0)
        
        fastest_lap = min(valid_laps, key=lambda x: x.get("lap_time_seconds", float('inf')))
        sector_times = fastest_lap.get("sector_times", {})
        
        s1 = sector_times.get("s1", 0) or 0
        s2 = sector_times.get("s2", 0) or 0
        s3 = sector_times.get("s3", 0) or 0
        
        return (s1, s2, s3)
    
    def paintEvent(self, event):
        """繪製簡潔條狀圖"""
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)
            
            # 繪製背景
            painter.fillRect(self.rect(), QBrush(QColor(255, 255, 255)))
            
            if not self.comparison_data:
                self._draw_no_data(painter)
                return
            
            # 繪製標題
            self._draw_title(painter)
            
            # 繪製表頭
            self._draw_header(painter)
            
            # 繪製分隔線
            self._draw_header_separator(painter)
            
            # 繪製每個車手的行
            for idx, driver_data in enumerate(self.comparison_data):
                y_pos = self.header_height + 20 + idx * self.row_height
                self._draw_driver_row(painter, driver_data, idx + 1, y_pos)
                
        finally:
            painter.end()
    
    def _draw_title(self, painter: QPainter):
        """繪製標題"""
        painter.setFont(QFont("Microsoft JhengHei", 14, QFont.Bold))
        painter.setPen(QPen(QColor(50, 50, 50)))
        title = tr("sector_comparison.title", "理想圈分段對比 - 累積差異條狀圖")
        painter.drawText(20, 30, title)
    
    def _draw_header(self, painter: QPainter):
        """繪製表頭"""
        y = self.header_height
        painter.setFont(QFont("Arial", 8, QFont.Bold))
        painter.setPen(QPen(QColor(80, 80, 80)))
        
        # 列標題
        x = self.margin_left
        painter.drawText(x, y, "Pos")
        
        x += self.col_pos_width
        painter.drawText(x, y, "Driver")
        
        x += self.col_driver_width
        painter.drawText(x, y, "S1 差異")
        
        x += self.col_sector_width
        painter.drawText(x, y, "S2 差異")
        
        x += self.col_sector_width
        painter.drawText(x, y, "S3 差異")
        
        x = self.col_cumulative_start
        painter.drawText(x, y, "累積總差異")
    
    def _draw_header_separator(self, painter: QPainter):
        """繪製表頭分隔線"""
        y = self.header_height + 5
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawLine(self.margin_left, y, self.width() - self.margin_right, y)
    
    def _draw_driver_row(self, painter: QPainter, driver_data: Dict, position: int, y: int):
        """
        繪製單個車手的行
        
        ⚠️ 重要變更：顯示 "理想圈分段 vs 最速圈分段" 的差異
        """
        driver = driver_data.get("driver", "???")
        
        # ✅ 提取理想圈和最速圈的分段時間
        ideal_s1, ideal_s2, ideal_s3, fastest_s1, fastest_s2, fastest_s3 = self._extract_sector_deltas(driver_data)
        
        # 計算差異（最速圈 - 理想圈）
        delta_s1 = fastest_s1 - ideal_s1 if (fastest_s1 and ideal_s1) else 0
        delta_s2 = fastest_s2 - ideal_s2 if (fastest_s2 and ideal_s2) else 0
        delta_s3 = fastest_s3 - ideal_s3 if (fastest_s3 and ideal_s3) else 0
        cumulative = delta_s1 + delta_s2 + delta_s3
        
        # 提取 is_optimal 標記
        sector_breakdown = driver_data.get("sector_breakdown", {})
        s1_opt = sector_breakdown.get("sector_1", {}).get("is_optimal_in_fastest", False)
        s2_opt = sector_breakdown.get("sector_2", {}).get("is_optimal_in_fastest", False)
        s3_opt = sector_breakdown.get("sector_3", {}).get("is_optimal_in_fastest", False)
        
        # 檢查是否懸停
        is_hovered = (self.hover_row == position - 1)
        
        # 繪製位置
        x = self.margin_left
        painter.setFont(QFont("Arial", 8))
        painter.setPen(QPen(QColor(50, 50, 50)))
        painter.drawText(x + 5, y + 15, f"{position}")
        
        # 繪製車手代碼（使用車隊背景色，與 Ranking Table 一致）
        x += self.col_pos_width
        team = driver_data.get("team", "Unknown")
        team_color = self._get_team_color(team)
        
        # 繪製背景色
        painter.fillRect(QRectF(x, y, self.col_driver_width, 25), QBrush(team_color))
        
        # 繪製邊框
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRect(QRectF(x, y, self.col_driver_width, 25))
        
        # 繪製車手代碼（黑色文字）
        painter.setFont(QFont("Arial", 8, QFont.Bold))
        painter.setPen(QPen(QColor(0, 0, 0)))
        text_width = painter.fontMetrics().width(driver)
        text_x = x + (self.col_driver_width - text_width) / 2
        painter.drawText(int(text_x), y + 16, driver)
        
        # 繪製分段差異指示器
        x += self.col_driver_width
        self._draw_delta_indicator(painter, delta_s1, s1_opt, x, y, self.col_sector_width - 5, 20)
        
        x += self.col_sector_width
        self._draw_delta_indicator(painter, delta_s2, s2_opt, x, y, self.col_sector_width - 5, 20)
        
        x += self.col_sector_width
        self._draw_delta_indicator(painter, delta_s3, s3_opt, x, y, self.col_sector_width - 5, 20)
        
        # 繪製累積差異棒狀圖
        x = self.col_cumulative_start
        self._draw_cumulative_bar(painter, cumulative, x, y, is_hovered)
        
        # 繪製行分隔線
        if position < len(self.comparison_data):
            painter.setPen(QPen(QColor(240, 240, 240), 1))
            painter.drawLine(self.margin_left, y + 25, self.width() - self.margin_right, y + 25)
    
    def _draw_delta_indicator(self, painter: QPainter, delta: float, is_optimal: bool, 
                              x: int, y: int, width: int, height: int):
        """
        繪製分段差異指示器
        
        改進：
        - 完美分段（delta ≈ 0）使用深綠色背景
        - 其他分段使用梯度配色（綠/黃/紅）
        - 移除重複的打勾符號（只在完美時顯示一個勾）
        """
        # 背景顏色 - 完美分段使用深綠色
        if abs(delta) < 0.001:
            bg_color = QColor(34, 139, 34)  # 深綠色（森林綠）
        else:
            bg_color = self._get_delta_color(delta)
        
        painter.fillRect(QRectF(x, y, width, height), QBrush(bg_color))
        
        # 邊框
        painter.setPen(QPen(QColor(200, 200, 200), 1))
        painter.drawRect(QRectF(x, y, width, height))
        
        # 文字
        painter.setFont(QFont("Arial", 8))
        if abs(delta) < 0.001:
            # 完美分段：白色打勾符號
            text = "✓"
            painter.setPen(QPen(QColor(255, 255, 255)))
        else:
            # 非完美分段：顯示差異數值
            text = f"+{delta:.3f}" if delta > 0 else f"{delta:.3f}"
            painter.setPen(QPen(QColor(50, 50, 50)))
        
        # 居中顯示
        text_width = painter.fontMetrics().width(text)
        text_x = x + (width - text_width) / 2
        painter.drawText(int(text_x), y + 14, text)
    
    def _draw_cumulative_bar(self, painter: QPainter, cumulative: float, x: int, y: int, is_hovered: bool):
        """
        繪製累積差異棒狀圖 - 使用相對長度
        
        改進：
        - 0s = 0% 長度
        - max_cumulative = 100% 長度
        - 其他按比例縮放
        """
        bar_max_width = self.width() - x - 120  # 預留文字空間
        
        if cumulative > 0 and self.max_cumulative > 0:
            # ✅ 改進：使用相對比例計算長度
            # bar_width = (cumulative / max_cumulative) * bar_max_width
            percentage = cumulative / self.max_cumulative
            bar_width = percentage * bar_max_width
            
            # 顏色 - 保持原有的梯度配色
            bar_color = self._get_cumulative_color(cumulative)
            if is_hovered:
                bar_color = bar_color.lighter(120)
            
            # 繪製棒狀圖
            painter.fillRect(QRectF(x, y, bar_width, 20), QBrush(bar_color))
            
            # 邊框
            painter.setPen(QPen(QColor(150, 150, 150), 1))
            painter.drawRect(QRectF(x, y, bar_width, 20))
            
            # 數值文字
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            painter.setPen(QPen(QColor(200, 50, 50)))
            text_x = x + bar_width + 5
            painter.drawText(int(text_x), y + 15, f"+{cumulative:.3f}s")
            
        else:
            # 完美圈
            painter.setFont(QFont("Arial", 8, QFont.Bold))
            painter.setPen(QPen(QColor(0, 150, 0)))
            painter.drawText(x, y + 15, "0.000s ✓")
    
    def _get_driver_color(self, driver: str) -> QColor:
        """獲取車手配色"""
        color = color_palette_provider.get_driver_color(driver, format="qcolor")
        if isinstance(color, QColor):
            return color
        return QColor(100, 100, 100)
    
    def _get_team_color(self, team: str) -> QColor:
        """
        獲取車隊顏色（與 Ranking Table 一致）
        
        Args:
            team: 車隊名稱
            
        Returns:
            QColor: 車隊顏色
        """
        team_colors = {
            "Red Bull Racing": QColor("#3671C6"),
            "Ferrari": QColor("#E8002D"),
            "Mercedes": QColor("#27F4D2"),
            "McLaren": QColor("#FF8000"),
            "Aston Martin": QColor("#229971"),
            "Alpine": QColor("#FF87BC"),
            "Williams": QColor("#64C4FF"),
            "RB": QColor("#6692FF"),
            "Kick Sauber": QColor("#52E252"),
            "Haas F1 Team": QColor("#B6BABD"),
        }
        return team_colors.get(team, QColor(128, 128, 128))  # 預設灰色
    
    def _get_delta_color(self, delta: float) -> QColor:
        """
        分段差異顏色 - 使用 Ideal Lap Ranking 的梯度配色
        
        參考: ideal_lap_ranking_table_widget.py _get_gap_color()
        - delta < 0.2s: 淺綠色 (接近完美)
        - delta < 0.5s: 淺黃色 (中等提升空間)
        - delta >= 0.5s: 淺紅色 (有明顯改善空間)
        """
        abs_delta = abs(delta)
        
        if abs_delta < 0.2:
            return QColor(144, 238, 144)  # 淺綠色 (接近完美)
        elif abs_delta < 0.5:
            return QColor(255, 255, 153)  # 淺黃色 (中等提升空間)
        else:
            return QColor(255, 182, 193)  # 淺紅色 (有明顯改善空間)
    
    def _get_cumulative_color(self, cumulative: float) -> QColor:
        """累積差異顏色"""
        if cumulative <= 0.050:
            return QColor(100, 200, 100, 200)  # 綠色
        elif cumulative <= 0.200:
            return QColor(255, 200, 100, 200)  # 黃色
        else:
            return QColor(255, 100, 100, 200)  # 紅色
    
    def _draw_no_data(self, painter: QPainter):
        """繪製無數據訊息"""
        painter.setPen(QPen(QColor(150, 150, 150)))
        painter.setFont(QFont("Arial", 12))
        
        message = tr("sector_comparison.no_data", "📊 No Data Available - Please load data first.")
        
        # 居中顯示
        text_width = painter.fontMetrics().width(message)
        x = (self.width() - text_width) / 2
        y = self.height() / 2
        
        painter.drawText(int(x), int(y), message)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """處理滑鼠移動事件"""
        # 計算懸停的行
        if event.y() > self.header_height + 20:
            row = int((event.y() - self.header_height - 20) / self.row_height)
            if 0 <= row < len(self.comparison_data):
                if self.hover_row != row:
                    self.hover_row = row
                    self.hover_driver = self.comparison_data[row].get("driver")
                    self.update()
            else:
                if self.hover_row != -1:
                    self.hover_row = -1
                    self.hover_driver = None
                    self.update()
        else:
            if self.hover_row != -1:
                self.hover_row = -1
                self.hover_driver = None
                self.update()
    
    def mousePressEvent(self, event: QMouseEvent):
        """處理滑鼠點擊事件"""
        if event.button() == Qt.LeftButton and self.hover_driver:
            self.bar_clicked.emit(self.hover_driver)
            print(f"[SECTOR_COMPARISON_V2] 點擊車手: {self.hover_driver}")
    
    def leaveEvent(self, event):
        """滑鼠離開事件"""
        if self.hover_row != -1:
            self.hover_row = -1
            self.hover_driver = None
            self.update()
    
    def sort_data(self, sort_key: str):
        """排序資料並重繪"""
        if not self.comparison_data:
            return
        
        print(f"[SECTOR_COMPARISON_V2] 依據 {sort_key} 排序")
        
        # 排序邏輯
        if sort_key == "position":
            sorted_data = sorted(self.comparison_data, key=lambda x: x.get("position", 99))
        elif sort_key == "ideal_lap":
            sorted_data = sorted(self.comparison_data, 
                               key=lambda x: x.get("ideal_lap_time", 999))
        elif sort_key == "fastest_lap":
            sorted_data = sorted(self.comparison_data, 
                               key=lambda x: x.get("fastest_lap_time", 999))
        elif sort_key == "delta":
            # 按累積差異排序
            def get_cumulative_delta(x):
                s1, s2, s3, _, _, _ = self._extract_sector_times(x)
                return (s1 - self.leader_s1) + (s2 - self.leader_s2) + (s3 - self.leader_s3)
            sorted_data = sorted(self.comparison_data, key=get_cumulative_delta)
        else:
            sorted_data = self.comparison_data
        
        self.comparison_data = sorted_data
        self.current_sort = sort_key
        self._calculate_leader_times()  # 重新計算領先者時間
        self.update()
        
        print(f"[SECTOR_COMPARISON_V2] ✅ 排序完成")
    
    def clear_chart(self):
        """清空圖表"""
        self.comparison_data = []
        self.statistics = {}
        self.current_data = None
        self.hover_row = -1
        self.hover_driver = None
        self.update()
        print("[SECTOR_COMPARISON_V2] 圖表已清空")
    
    def export_chart(self, file_path: str) -> bool:
        """匯出圖表為圖片"""
        try:
            # 創建圖片
            image = QImage(self.size(), QImage.Format_ARGB32)
            image.fill(Qt.white)
            
            # 繪製到圖片
            painter = QPainter(image)
            self.render(painter)
            painter.end()
            
            # 儲存
            success = image.save(file_path)
            
            if success:
                print(f"[SECTOR_COMPARISON_V2] ✅ 圖表已匯出: {file_path}")
            else:
                print(f"[ERROR] [SECTOR_COMPARISON_V2] 匯出失敗: {file_path}")
            
            return success
            
        except Exception as e:
            print(f"[ERROR] [SECTOR_COMPARISON_V2] 匯出圖表失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
