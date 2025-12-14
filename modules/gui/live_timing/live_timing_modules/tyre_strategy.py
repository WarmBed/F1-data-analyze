"""
Live Timing Tyre Strategy
=========================

顯示所有車手的輪胎策略視覺化（長條圖形式）。

參考: Live_timing_test/demo_live_position_tracking.py TyreStrategyChartWidget

Author: F1T Team
Date: 2025-12-04
"""

from typing import Dict, List, Any

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QColor, QPen, QFont

from ..core.base_live_mdi import BaseLiveTimingMDI
from core.gui_i18n import tr
from core.logger import get_logger

logger = get_logger("live_timing.tyre_strategy", component="gui")

# 嘗試導入通用顏色系統
try:
    from modules.gui.themes.color_palette_provider import color_palette_provider
    COLOR_PALETTE_AVAILABLE = True
except ImportError:
    COLOR_PALETTE_AVAILABLE = False
    logger.warning("[TYRE_STRATEGY] color_palette_provider not available")


# 輪胎顏色常量
TYRE_COLORS = {
    'SOFT': '#FF3333',
    'MEDIUM': '#FFDD00',
    'HARD': '#FFFFFF',
    'INTERMEDIATE': '#43B02A',
    'WET': '#0066FF',
    'UNKNOWN': '#888888'
}

TYRE_ABBREV = {
    'SOFT': 'S',
    'MEDIUM': 'M',
    'HARD': 'H',
    'INTERMEDIATE': 'I',
    'WET': 'W',
    'UNKNOWN': '?'
}


class TyreStrategyChartWidget(QWidget):
    """
    Tyre Strategy Chart Widget - 使用 QPainter 繪製
    
    顯示所有車手的輪胎策略：
    - Y 軸：車手代碼（按排名排序）
    - X 軸：圈數 (0 ~ 總圈數)
    - 每個 stint 用對應顏色的長條表示
    - 進站點用垂直線標記
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 設定 Live Timing 識別屬性 (供 force_white_background 排除使用)
        self.setProperty("is_live_timing_widget", True)
        self.setStyleSheet("background-color: #1a1a1a;")
        
        # 數據
        self._driver_stints: Dict[str, List[Dict]] = {}
        self._driver_info: Dict[str, Dict] = {}
        self._driver_positions: Dict[str, int] = {}
        self._total_laps: int = 53
        self._current_lap: int = 0
        
        # 繪圖參數
        self._margin_left = 50
        self._margin_right = 20
        self._margin_top = 30
        self._margin_bottom = 25  # 增加底部邊距以容納 X 軸標籤
        self._row_height = 22
        self._row_spacing = 3
        
        self.setMinimumSize(400, 300)
        
        logger.info("[TYRE_STRATEGY] TyreStrategyChartWidget initialized")
    
    def set_data(self, driver_stints: Dict[str, List[Dict]], 
                 driver_info: Dict[str, Dict],
                 driver_positions: Dict[str, int],
                 total_laps: int,
                 current_lap: int = 0):
        """
        設置數據
        
        Args:
            driver_stints: {driver_num: [{compound, start_lap, end_lap, new}, ...]}
            driver_info: {driver_num: {tla, team_color, ...}}
            driver_positions: {driver_num: position}
            total_laps: 總圈數
            current_lap: 當前圈數
        """
        self._driver_stints = driver_stints
        self._driver_info = driver_info
        self._driver_positions = driver_positions
        self._total_laps = total_laps
        self._current_lap = current_lap
        self.update()
    
    def update_current_lap(self, current_lap: int):
        """更新當前圈數"""
        self._current_lap = current_lap
        self.update()
    
    def set_total_laps(self, total_laps: int):
        """設置總圈數"""
        if total_laps > 0:
            self._total_laps = total_laps
    
    def paintEvent(self, event):
        """繪製事件"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        painter.fillRect(0, 0, width, height, QColor('#1a1a1a'))
        
        chart_left = self._margin_left
        chart_right = width - self._margin_right
        chart_top = self._margin_top
        chart_bottom = height - self._margin_bottom
        chart_width = chart_right - chart_left
        chart_height = chart_bottom - chart_top
        
        if chart_width <= 0 or chart_height <= 0:
            return
        
        sorted_drivers = sorted(
            self._driver_positions.items(),
            key=lambda x: x[1]
        )
        
        if not sorted_drivers:
            painter.setPen(QColor('#888888'))
            painter.setFont(QFont('Arial', 12))
            painter.drawText(self.rect(), Qt.AlignCenter, tr("no_tyre_data", "No tyre data available"))
            return
        
        num_drivers = len(sorted_drivers)
        row_height = min(self._row_height, (chart_height - (num_drivers - 1) * self._row_spacing) / num_drivers)
        
        # 繪製 X 軸
        self._draw_x_axis(painter, chart_left, chart_right, chart_bottom, chart_width)
        
        # 繪製每位車手的輪胎策略
        for i, (driver_num, position) in enumerate(sorted_drivers):
            y = chart_top + i * (row_height + self._row_spacing)
            self._draw_driver_row(painter, driver_num, chart_left, y, chart_width, row_height)
        
        # 繪製當前圈數指示線
        if self._current_lap > 0 and self._total_laps > 0:
            progress = self._current_lap / self._total_laps
            x = chart_left + progress * chart_width
            painter.setPen(QPen(QColor('#00FF00'), 2, Qt.DashLine))
            painter.drawLine(int(x), chart_top - 5, int(x), chart_bottom + 5)
            
            painter.setPen(QColor('#00FF00'))
            painter.setFont(QFont('Arial', 9))
            painter.drawText(int(x) - 15, chart_top - 8, f"L{self._current_lap}")
        
        # 圖例已禁用以節省空間
    
    def _draw_x_axis(self, painter: QPainter, left: int, right: int, bottom: int, width: float):
        """繪製 X 軸（圈數）"""
        # 防禦性檢查：如果總圈數為 0 或負數，不繪製 X 軸
        if self._total_laps <= 0:
            return
        
        painter.setPen(QColor('#666666'))
        painter.drawLine(left, bottom, right, bottom)
        
        painter.setFont(QFont('Arial', 9))
        painter.setPen(QColor('#AAAAAA'))
        
        step = 10
        if self._total_laps <= 30:
            step = 5
        elif self._total_laps >= 70:
            step = 15
        
        for lap in range(0, self._total_laps + 1, step):
            x = left + (lap / self._total_laps) * width
            painter.drawLine(int(x), bottom, int(x), bottom + 5)
            painter.drawText(int(x) - 10, bottom + 18, str(lap))
        
        if self._total_laps % step != 0:
            x = right
            painter.drawLine(int(x), bottom, int(x), bottom + 5)
            painter.drawText(int(x) - 10, bottom + 18, str(self._total_laps))
    
    def _draw_driver_row(self, painter: QPainter, driver_num: str, 
                         left: int, y: float, width: float, height: float):
        """繪製單個車手的輪胎策略行"""
        # 防禦性檢查：如果總圈數為 0 或負數，不繪製
        if self._total_laps <= 0:
            return
        
        driver_info = self._driver_info.get(driver_num, {})
        tla = driver_info.get('tla', driver_num)
        
        # 獲取車隊顏色 (優先使用 color_palette_provider)
        team_color = None
        if COLOR_PALETTE_AVAILABLE:
            try:
                color_qcolor = color_palette_provider.get_driver_color(tla, fallback=True)
                if color_qcolor:
                    team_color = color_qcolor.name()
            except Exception:
                pass
        
        # 備選：使用 driver_info 中的 team_color
        if not team_color:
            team_color = driver_info.get('team_color', 'CCCCCC')
            if not team_color.startswith('#'):
                team_color = f'#{team_color}'
        
        # 車手標籤背景
        painter.fillRect(2, int(y), self._margin_left - 5, int(height), 
                        QColor(team_color))
        
        # 車手名稱文字
        text_color = '#000000' if self._is_light_color(team_color) else '#FFFFFF'
        painter.setPen(QColor(text_color))
        painter.setFont(QFont('Arial', 9, QFont.Bold))
        painter.drawText(5, int(y) + int(height) - 5, tla)
        
        # 繪製輪胎 stint 長條
        stints = self._driver_stints.get(driver_num, [])
        
        for stint in stints:
            compound = stint.get('compound', 'UNKNOWN')
            start_lap = stint.get('start_lap', 0)
            end_lap = stint.get('end_lap', self._total_laps)
            is_new = stint.get('new', True)  # 預設為新胎
            
            x1 = left + (start_lap / self._total_laps) * width
            x2 = left + (end_lap / self._total_laps) * width
            bar_width = max(x2 - x1, 2)
            
            color = TYRE_COLORS.get(compound, TYRE_COLORS['UNKNOWN'])
            painter.fillRect(int(x1), int(y) + 1, int(bar_width), int(height) - 2, QColor(color))
            
            # 進站標記
            if start_lap > 0:
                painter.setPen(QPen(QColor('#FFFFFF'), 2))
                painter.drawLine(int(x1), int(y), int(x1), int(y) + int(height))
            
            # 輪胎縮寫 - 舊胎顯示 (U)
            if bar_width > 25:
                abbrev = TYRE_ABBREV.get(compound, '?')
                # 如果是舊胎，加上 (U) 標記
                if not is_new:
                    abbrev = f"{abbrev}(U)"
                text_color = '#000000' if compound in ['HARD', 'MEDIUM'] else '#FFFFFF'
                painter.setPen(QColor(text_color))
                painter.setFont(QFont('Arial', 8, QFont.Bold))
                # 調整文字位置，讓較長的文字居中
                text_offset = 4 if is_new else 10
                painter.drawText(int(x1 + bar_width / 2 - text_offset), int(y + height / 2 + 4), abbrev)
    
    def _draw_legend(self, painter: QPainter, width: int, height: int):
        """繪製圖例 - 已禁用以節省空間"""
        pass
    
    def _is_light_color(self, color_hex: str) -> bool:
        """判斷顏色是否為淺色"""
        if not color_hex.startswith('#'):
            color_hex = f'#{color_hex}'
        
        try:
            r = int(color_hex[1:3], 16)
            g = int(color_hex[3:5], 16)
            b = int(color_hex[5:7], 16)
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            return luminance > 0.5
        except:
            return False


class LiveTimingTyreStrategy(BaseLiveTimingMDI):
    """
    Live Timing Tyre Strategy MDI Window
    
    顯示所有車手的輪胎策略視覺化。
    動態根據當前時間點顯示輪胎策略變化。
    
    性能優化: 只在車手換胎時更新 (檢測 compound 變化)
    """
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent, data_manager)
        
        self.setWindowTitle(tr("tyre_strategy", "Tyre Strategy"))
        self.setMinimumSize(500, 400)
        self.resize(600, 500)
        
        self._total_laps = 53
        self._driver_info: Dict[str, Dict] = {}  # 車手資訊
        
        # 性能優化: 追蹤上次的輪胎狀態和圈數
        self._last_tyre_state: Dict[str, str] = {}  # {driver_num: compound}
        self._last_lap: int = 0  # 上次的最大圈數
        
        logger.info("[TYRE_STRATEGY_MDI] LiveTimingTyreStrategy initialized")
    
    def _setup_ui(self):
        """Setup UI components"""
        self.strategy_widget = TyreStrategyChartWidget()
        self._main_layout.addWidget(self.strategy_widget)
    
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """Race loaded"""
        year = race_info.get('year', 2025)
        race_key = race_info.get('race', '')
        self._total_laps = race_info.get('total_laps', 53)
        
        # 獲取車手資訊
        self._driver_info = race_info.get('driver_info', {})
        
        self.strategy_widget.set_total_laps(self._total_laps)
        
        logger.info("[TYRE_STRATEGY_MDI] Race loaded: %s %s, total laps: %s", year, race_key, self._total_laps)
    
    def _on_race_unloaded(self):
        """Race unloaded"""
        logger.info("[TYRE_STRATEGY_MDI] Race unloaded")
        self._driver_info = {}
        self.strategy_widget._driver_stints = {}
        self.strategy_widget._driver_positions = {}
        self.strategy_widget.update()
    
    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        """
        Snapshot updated - 動態更新輪胎策略圖
        
        性能優化: 在圈數變化或換胎時更新顯示
        
        關鍵邏輯：
        1. 從 DataManager 的 get_tyre_state_at_time() 獲取當前時間點的輪胎狀態
        2. 檢查是否有圈數變化或 compound 變化
        3. 有變化時才重繪
        """
        drivers = snapshot.get('drivers', {})
        current_timestamp = snapshot.get('race_time', '')
        
        # 從 DataManager 獲取當前時間點的輪胎狀態
        tyre_state = {}
        if self._data_manager and current_timestamp:
            tyre_state = self._data_manager.get_tyre_state_at_time(current_timestamp)
        
        # 獲取當前最大圈數
        current_max_lap = 0
        for driver_data in drivers.values():
            lap = driver_data.get('lap', 0)
            if lap and lap > current_max_lap:
                current_max_lap = lap
        
        # 性能優化: 檢查是否有圈數變化或 compound 變化
        current_compounds = {}
        for driver_num, state in tyre_state.items():
            stints = state.get('stints', [])
            if stints:
                current_compounds[driver_num] = stints[-1].get('compound', 'UNKNOWN')
        
        # 比較與上次的差異 - 圈數或配方變化
        has_change = False
        
        # 檢查圈數變化
        if current_max_lap != self._last_lap:
            has_change = True
            self._last_lap = current_max_lap
        
        # 檢查配方變化
        if not has_change:
            for driver_num, compound in current_compounds.items():
                if self._last_tyre_state.get(driver_num) != compound:
                    has_change = True
                    break
        
        # 如果沒有變化且已經有數據，跳過更新
        if not has_change and self._last_tyre_state:
            return
        
        # 更新狀態追蹤
        self._last_tyre_state = current_compounds
        
        # 從 drivers 數據獲取排名和當前圈數
        driver_positions = {}
        driver_info = {}
        current_lap = 0
        
        for driver_num, data in drivers.items():
            # 過濾 DNF/Retired/Stopped 車手
            status = data.get('status', '')
            if status and status.upper() in ('DNF', 'RETIRED', 'OUT', 'STOPPED'):
                continue
            
            position = data.get('position', 99)
            driver_positions[driver_num] = position
            
            driver_info[driver_num] = {
                'tla': data.get('driver_tla', driver_num),
                'team_color': data.get('team_color', 'CCCCCC')
            }
            
            # 獲取當前圈數（取最大值）
            lap = data.get('lap', 0)
            if lap and lap > current_lap:
                current_lap = lap
        
        # 使用合併的車手資訊（優先使用 race_info 中的）
        for driver_num in driver_info:
            if driver_num in self._driver_info:
                info = self._driver_info[driver_num]
                if 'tla' in info:
                    driver_info[driver_num]['tla'] = info['tla']
                if 'team_color' in info:
                    driver_info[driver_num]['team_color'] = info['team_color']
        
        # 從 DataManager 獲取當前時間點的輪胎狀態
        tyre_state = {}
        if self._data_manager and current_timestamp:
            tyre_state = self._data_manager.get_tyre_state_at_time(current_timestamp)
        
        # 從 tyre_state 構建動態 stint 數據
        driver_stints = self._build_dynamic_stints(tyre_state, current_lap)
        
        self.strategy_widget.set_data(
            driver_stints,
            driver_info,
            driver_positions,
            self._total_laps,
            current_lap
        )
    
    def _build_dynamic_stints(self, tyre_state: Dict[str, Dict], current_lap: int) -> Dict[str, List[Dict]]:
        """
        從即時輪胎狀態構建動態 stint 數據
        
        Args:
            tyre_state: 即時輪胎狀態 {driver_num: {compound, new, stint_count, stints, tyre_age}}
            current_lap: 當前圈數
            
        Returns:
            {driver_num: [{compound, start_lap, end_lap, new}, ...]}
        """
        driver_stints = {}
        
        for driver_num, state in tyre_state.items():
            stints_raw = state.get('stints', [])
            driver_stints[driver_num] = []
            current_start = 0
            
            for stint in stints_raw:
                compound = stint.get('compound', 'UNKNOWN')
                is_new = stint.get('new', False)
                total_laps = stint.get('total_laps', 0)
                
                end_lap = current_start + total_laps
                
                # 如果這個 stint 的起點已經超過當前圈數，跳過
                if current_start > current_lap:
                    break
                
                # 截斷到當前圈數
                display_end_lap = min(end_lap, current_lap)
                
                if display_end_lap > current_start:
                    driver_stints[driver_num].append({
                        'compound': compound,
                        'start_lap': current_start,
                        'end_lap': display_end_lap,
                        'new': is_new
                    })
                
                current_start = end_lap
        
        return driver_stints
