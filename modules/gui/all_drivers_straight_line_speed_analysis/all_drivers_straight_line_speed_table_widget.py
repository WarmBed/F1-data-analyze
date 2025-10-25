#!/usr/bin/env python3
"""
全車手直線速度分析表格元件 - QTableWidget 版本
All Drivers Straight Line Speed Table Widget

✅ 復刻 ideal_lap_sector_comparison 的 QTableWidget 架構
✅ 使用自定義 Delegate 繪製加速時間棒狀圖

作者: F1T Team
日期: 2025-10-14
版本: 2.0.0 (表格版本)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QStyledItemDelegate,
    QStyleOptionViewItem, QStyle, QMessageBox, QLabel, QHBoxLayout
)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QColor, QBrush, QFont, QPen
from typing import Dict, List, Any, Optional

# 導入翻譯和配色
from core.gui_i18n import tr
from modules.gui.themes.color_palette_provider import color_palette_provider
from core.gui_settings_manager import gui_settings_manager


class AccelerationBarDelegate(QStyledItemDelegate):
    """
    加速時間棒狀圖委託
    
    ⭐ 視覺化邏輯：
    - 棒狀圖長度 = 基於賽道段加速時間（segment_accel_time_seconds）
    - 時間越短 = 棒狀圖越短 = 性能越好
    - 使用相對時間範圍計算，使差異更明顯
    
    ⭐ 數據來源：
    - UserRole: segment_accel_time（用於排序和繪圖）
    - UserRole+1: max_speed（最高速度，用於顯示）
    - UserRole+2: segment_accel_time（重複，保持一致性）
    """
    
    def __init__(self, min_time: float = 0.0, max_time: float = 10.0, parent=None):
        super().__init__(parent)
        self.min_time = min_time  # 最快車手的時間（例如 9.480s）
        self.max_time = max_time  # 最慢車手的時間（例如 10.120s）
        self.time_range = max_time - min_time  # 時間範圍（例如 0.640s）
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        """
        繪製加速視覺化圖表
        
        ⭐ 視覺化設計邏輯：
        ┌─────────────────────────────────────────────────────┐
        │  最快車手                    最慢車手                │
        │    ↓                          ↓                      │
        │    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  9.480s (SAI)       │
        │    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  9.759s (HAM)   │
        │    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  10.120s (LEC)│
        └─────────────────────────────────────────────────────┘
        
        ⭐ 關鍵邏輯：
        - 棒狀圖長度 ∝ 加速時間（時間越長，棒越長）
        - 時間短 = 性能好 = 棒短 ✅
        - 相對比例 = (車手時間 - 最快時間) / (最慢時間 - 最快時間)
        """
        # ✅ 獲取賽道段加速時間數據
        segment_accel_time = index.data(Qt.UserRole)  # 賽道段加速時間（排序和繪圖依據）
        max_speed = index.data(Qt.UserRole + 1)  # 最高速度（顯示用）
        
        # 檢查數據有效性
        if segment_accel_time is None or segment_accel_time == 9999:
            # N/A 數據，顯示灰色 N/A
            super().paint(painter, option, index)
            return
        
        if segment_accel_time <= 0:
            super().paint(painter, option, index)
            return
        
        painter.save()
        
        # 繪製背景（選中狀態）
        if option.state & QStyle.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            painter.fillRect(option.rect, QBrush(QColor(255, 255, 255)))
        
        # ===== 計算關鍵位置（使用相對時間比例）=====
        base_x = option.rect.x() + 10
        base_y = option.rect.y() + 10
        
        # ✅ 文字和棒狀圖佈局
        text_reserved_width = 80  # 預留文字寬度
        left_margin = 10  # 左邊距
        text_margin = 10  # 棒狀圖與文字的間距
        
        # 計算棒狀圖最大可用寬度
        total_width = option.rect.width()
        bar_max_width = total_width - left_margin - text_reserved_width
        bar_height = 20
        
        # ⭐ 使用相對時間計算棒狀圖長度（關鍵邏輯）
        if self.time_range > 0:
            # 相對於最快車手的時間差異比例
            # 例如：最快 9.480s，最慢 10.120s，範圍 0.640s
            # HAM 9.759s: (9.759 - 9.480) / 0.640 = 0.436 (43.6%)
            # LEC 10.120s: (10.120 - 9.480) / 0.640 = 1.000 (100%)
            relative_ratio = (segment_accel_time - self.min_time) / self.time_range
        else:
            # 所有車手時間相同
            relative_ratio = 0.0
        
        # ✅ 棒狀圖寬度（按比例縮放）
        # 時間短 = relative_ratio 小 = 棒狀圖短 = 性能好 ✅
        bar_width = min(bar_max_width * relative_ratio, bar_max_width)
        
        # ===== 繪製加速棒（簡化設計：單一深藍色實心棒）=====
        # ⭐ 棒狀圖設計：
        # - 深藍色實心棒，長度代表加速時間
        # - 棒越短 = 時間越短 = 性能越好
        # - 無需分段顯示（已移除速度範圍概念）
        
        bar_rect = QRectF(base_x, base_y, bar_width, bar_height)
        painter.fillRect(bar_rect, QBrush(QColor(50, 100, 180)))  # 深藍色實心
        painter.setPen(QPen(QColor(30, 70, 140), 2))  # 深藍邊框
        painter.drawRect(bar_rect)
        
        # ===== 繪製時間標籤（固定位置）=====
        # ✅ 文字使用固定起始位置（棒狀圖最大寬度後）
        text_x = int(base_x + bar_max_width + text_margin)
        
        # 顯示賽道段加速時間
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.setPen(QPen(QColor(50, 100, 180)))  # 深藍色
        text_y = int(base_y + 15)
        painter.drawText(text_x, text_y, f"{segment_accel_time:.3f} s")
        
        painter.restore()
    
    def _get_time_color(self, time: float) -> QColor:
        """
        根據加速時間返回顏色
        
        綠色: < 7.0 秒 (快)
        黃色: 7.0 - 8.0 秒 (中等)
        橙色: > 8.0 秒 (慢)
        """
        if time < 7.0:
            return QColor(100, 200, 100)  # 綠色
        elif time < 8.0:
            return QColor(255, 220, 100)  # 黃色
        else:
            return QColor(255, 150, 100)  # 橙色
    
    def sizeHint(self, option: QStyleOptionViewItem, index):
        """設定單元格大小"""
        return super().sizeHint(option, index)


class AllDriversStraightLineSpeedTableWidget(QWidget):
    """
    全車手直線速度分析表格元件 - QTableWidget 版本
    
    特點：
    - 使用 QTableWidget（與 Ideal Lap Sector Comparison 一致）
    - 車手欄位顯示車隊背景色
    - 最高速度使用顏色編碼
    - 加速時間使用棒狀圖 + 虛線（自定義委託）
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 數據屬性
        self.driver_speeds_data: List[Dict] = []
        self.min_time_to_max = 0.0  # 最快車手的時間
        self.max_time_to_max = 0.0  # 最慢車手的時間
        
        # ✅ 統一速度範圍（從 metadata 讀取）
        self.unified_start_speed = 100.0  # 預設值
        self.unified_end_speed = 300.0    # 預設值
        
        # ✅ Distance 範圍資訊（從 reference_segment 讀取）
        self.segment_distance_start = None
        self.segment_distance_end = None
        self.segment_length = None
        
        # ✅ 動態欄位設定
        self._settings_manager = gui_settings_manager
        self._column_visibility = self._get_column_visibility()
        
        # 初始化 UI
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # ✅ 創建 Distance 範圍資訊標籤
        self.info_label = QLabel()
        self.info_label.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 11pt;
                font-weight: bold;
                color: #333333;
            }
        """)
        self.info_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._update_info_label()  # 初始化顯示
        layout.addWidget(self.info_label)
        
        # 創建表格
        self.table = self._create_table()
        layout.addWidget(self.table)
    
    def _update_info_label(self):
        """
        更新資訊標籤顯示分析距離範圍
        
        格式: 分析範圍: {start}m → {end}m (長度: {length}m) | 參考車手: {driver}
        """
        if self.segment_distance_start is None or self.segment_distance_end is None:
            self.info_label.setText(tr("straight_speed_info_no_data", "分析範圍: 未載入資料"))
            return
        
        # 格式化距離資訊
        start_m = f"{self.segment_distance_start:.1f}"
        end_m = f"{self.segment_distance_end:.1f}"
        length_m = f"{self.segment_length:.1f}" if self.segment_length else "N/A"
        
        # 組合顯示文字
        info_text = tr("straight_speed_info_range", "分析範圍: {start}m → {end}m (長度: {length}m)").format(
            start=start_m, end=end_m, length=length_m
        )
        
        # 如果有參考車手資訊，添加到標籤
        if hasattr(self, 'reference_driver') and self.reference_driver:
            info_text += tr("straight_speed_info_reference", " | 參考車手: {driver}").format(
                driver=self.reference_driver
            )
        
        self.info_label.setText(info_text)
        print(f"[SPEED_TABLE] 資訊標籤更新: {info_text}")
    
    def _get_column_visibility(self) -> Dict[str, bool]:
        """
        從 settings manager 獲取欄位顯示設定
        
        Returns:
            Dict: 欄位顯示狀態 {欄位名稱: 是否顯示}
        """
        settings = self._settings_manager.get_straight_speed_analysis_settings()
        
        visibility = {
            'driver': True,  # 永遠顯示
            'team': True,    # 永遠顯示
            'max_speed': settings.get('speed_show_max_speed', True),  # ✅ 預設開啟最高速度欄位
            'accel_time': True,  # 永遠顯示（必須）
            'avg_accel': True,   # 永遠顯示（必須）
            'start_speed': settings.get('speed_show_start_speed', False),
            'max_speed_time': settings.get('speed_show_max_speed_time', False),
            'performance_bar': settings.get('speed_show_performance_bar', True),
        }
        
        return visibility
    
    def _get_visible_columns(self) -> List[tuple]:
        """
        根據設定返回可見欄位列表
        
        Returns:
            List[tuple]: [(邏輯欄位名, 欄位標題), ...]
        """
        all_columns = [
            ('driver', tr('speed_analysis_header_driver', '車手')),
            ('team', tr('speed_analysis_header_team', '車隊')),
            ('max_speed', tr('speed_analysis_header_max_speed', '最高速度 (km/h)')),
            ('accel_time', tr('speed_analysis_header_segment_accel_time', '加速時間 (s)')),
            ('avg_accel', tr('speed_analysis_header_segment_avg_accel', '平均加速度 (m/s²)')),
            ('start_speed', tr('speed_analysis_header_segment_start_speed', '起始速度 (km/h)')),
            ('max_speed_time', tr('speed_analysis_header_max_speed_time', '最高速度時間 (s)')),
            ('performance_bar', tr('speed_analysis_header_accel_bar', '加速性能視覺化')),
        ]
        
        # 只返回可見的欄位
        visible_columns = [
            (col_name, col_title)
            for col_name, col_title in all_columns
            if self._column_visibility.get(col_name, True)
        ]
        
        return visible_columns
    
    def _get_column_index(self, logical_column: str) -> Optional[int]:
        """
        獲取邏輯欄位的實際欄位索引
        
        Args:
            logical_column: 邏輯欄位名稱 (例如: 'max_speed')
            
        Returns:
            int: 實際欄位索引，如果欄位不可見則返回 None
        """
        if not self._column_visibility.get(logical_column, False):
            return None
        
        visible_columns = self._get_visible_columns()
        for idx, (col_name, _) in enumerate(visible_columns):
            if col_name == logical_column:
                return idx
        
        return None
    
    def _create_table(self) -> QTableWidget:
        """創建表格（根據設定動態顯示欄位）"""
        table = QTableWidget()
        
        # ✅ 動態獲取可見欄位
        visible_columns = self._get_visible_columns()
        column_titles = [title for _, title in visible_columns]
        
        table.setColumnCount(len(column_titles))
        table.setHorizontalHeaderLabels(column_titles)
        
        # 設置表格屬性
        table.setSortingEnabled(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.NoSelection)  # ✅ 禁用選擇（避免高亮覆蓋背景色）
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # ✅ 動態設置欄位寬度（根據可見欄位）
        column_widths = {
            'driver': 100,
            'team': 160,
            'max_speed': 120,
            'accel_time': 120,
            'avg_accel': 120,
            'start_speed': 120,
            'max_speed_time': 120,
            'performance_bar': 350,
        }
        
        for idx, (col_name, _) in enumerate(visible_columns):
            width = column_widths.get(col_name, 100)
            table.setColumnWidth(idx, width)
        
        # ✅ 最後一個欄位拉伸填充剩餘空間
        # 欄位 6（視覺化）使用 stretch 填滿剩餘空間
        
        # 設置行高
        table.verticalHeader().setDefaultSectionSize(40)
        
        # 設置表頭（只讓最後一欄自動拉伸）
        header = table.horizontalHeader()
        header.setStretchLastSection(True)  # 最後一欄（視覺化）拉伸填滿剩餘空間
        
        # ✅ 取消點擊信號連接（禁用左鍵點擊彈窗功能）
        # table.cellClicked.connect(self._on_cell_clicked)
        
        return table
    
    def update_data(self, data: Dict[str, Any]):
        """
        更新數據並填充表格
        
        Args:
            data: 包含 driver_speeds 和 metadata 的字典
        """
        try:
            print(f"[SPEED_TABLE] update_data 被調用，data keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
            
            if not data or not isinstance(data, dict):
                print("[WARNING] [SPEED_TABLE] 無效的數據格式")
                return
            
            # ✅ 提取 metadata 並讀取統一速度範圍
            metadata = data.get("metadata", {})
            unified_speed_range = metadata.get("unified_speed_range", {})
            
            if unified_speed_range:
                self.unified_start_speed = unified_speed_range.get("start_speed_kmh", 100.0)
                self.unified_end_speed = unified_speed_range.get("end_speed_kmh", 300.0)
                print(f"[SPEED_TABLE] 統一速度範圍: {self.unified_start_speed:.0f}→{self.unified_end_speed:.0f} km/h")
            else:
                print("[WARNING] [SPEED_TABLE] 未找到 unified_speed_range，使用預設值 100→300 km/h")
            
            # ✅ 提取 reference_segment 距離範圍資訊
            reference_segment = data.get("reference_segment", {})
            if reference_segment:
                self.segment_distance_start = reference_segment.get("segment_distance_start")
                self.segment_distance_end = reference_segment.get("segment_distance_end")
                self.segment_length = reference_segment.get("segment_length")
                self.reference_driver = reference_segment.get("driver", "")
                print(f"[SPEED_TABLE] 距離範圍: {self.segment_distance_start:.1f}m → {self.segment_distance_end:.1f}m (長度: {self.segment_length:.1f}m)")
                
                # ✅ 更新資訊標籤
                self._update_info_label()
            else:
                print("[WARNING] [SPEED_TABLE] 未找到 reference_segment 資訊")
            
            # 提取車手數據
            self.driver_speeds_data = data.get("driver_speeds", [])
            print(f"[SPEED_TABLE] driver_speeds 數量: {len(self.driver_speeds_data)}")
            
            if not self.driver_speeds_data:
                print("[WARNING] [SPEED_TABLE] 無 driver_speeds 數據")
                return
            
            # ✅ 學習 Ideal Lap Ranking：只更新內容，不重建表格
            # 計算時間範圍（用於委託）
            self._calculate_max_time()
            
            # 填充表格（_populate_table 內部會處理排序和行數）
            self._populate_table()
            
            print(f"[SPEED_TABLE] 表格更新完成：{len(self.driver_speeds_data)} 位車手")
            
        except Exception as e:
            print(f"[ERROR] [SPEED_TABLE] 更新數據失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _calculate_max_time(self):
        """計算時間範圍（用於視覺化棒狀圖）"""
        min_time = float('inf')
        max_time = 0.0
        
        for driver_data in self.driver_speeds_data:
            # ⭐ 使用新的 segment_accel_time_seconds
            segment_accel_time = driver_data.get("segment_accel_time_seconds", None)
            
            if segment_accel_time is not None and segment_accel_time > 0:
                min_time = min(min_time, segment_accel_time)
                max_time = max(max_time, segment_accel_time)
        
        # 儲存時間範圍
        self.min_time_to_max = min_time if min_time != float('inf') else 0.0
        self.max_time_to_max = max_time if max_time > 0 else 10.0
        
        print(f"[SPEED_TABLE] 時間範圍: {self.min_time_to_max:.3f}s ~ {self.max_time_to_max:.3f}s")
    
    def _calculate_time_to_max_speed(self, max_speed: float, accel_100_300_time: float) -> float:
        """
        計算從統一起始速度加速到最高速度所需時間
        
        ✅ 修正：使用統一速度範圍計算
        假設線性加速:
        time_to_max = (max_speed - unified_start) / (unified_end - unified_start) × accel_time
        """
        # ✅ 防止 None 值導致 TypeError
        if accel_100_300_time is None or accel_100_300_time <= 0:
            return 0.0
        
        if max_speed <= self.unified_start_speed:
            return 0.0
        
        # ✅ 使用統一速度範圍計算
        speed_range_unified = self.unified_end_speed - self.unified_start_speed
        speed_range_to_max = max_speed - self.unified_start_speed
        
        time_to_max = (speed_range_to_max / speed_range_unified) * accel_100_300_time
        return time_to_max
    
    def _populate_table(self):
        """填充表格數據"""
        row_count = len(self.driver_speeds_data)
        
        self.table.setSortingEnabled(False)
        self.table.setRowCount(row_count)
        
        # ✅ 修正：學習 Ranking Table - 不預先排序，讓 Qt 內建排序功能處理
        # ❌ 舊代碼：預先按最高速度排序，導致 Qt 排序功能混亂
        # sorted_data = sorted(
        #     self.driver_speeds_data, 
        #     key=lambda x: x.get("max_speed_kmh", 0), 
        #     reverse=True
        # )
        
        # ✅ 直接按原始順序填充（通常是按車手代碼字母順序）
        for row, driver_data in enumerate(self.driver_speeds_data):
            self._populate_row(row, row + 1, driver_data)
        
        # ✅ 設置加速棒狀圖欄位的委託（動態獲取欄位索引）
        bar_col_index = self._get_column_index('performance_bar')
        if bar_col_index is not None:
            bar_delegate = AccelerationBarDelegate(self.min_time_to_max, self.max_time_to_max, self.table)
            self.table.setItemDelegateForColumn(bar_col_index, bar_delegate)
            print(f"[SPEED_TABLE] 委託已設置，欄位 {bar_col_index}（加速性能視覺化），時間範圍 {self.min_time_to_max:.3f}s ~ {self.max_time_to_max:.3f}s")
        else:
            print("[WARNING] [SPEED_TABLE] Performance Bar 欄位不可見，跳過委託設置")
        
        self.table.setSortingEnabled(True)
    
    def _set_item_at_column(self, row: int, column_name: str, item: QTableWidgetItem):
        """設置指定邏輯欄位的項目（處理動態欄位索引）"""
        col_index = self._get_column_index(column_name)
        if col_index is not None:  # ✅ 修正：檢查 None 而非 -1
            self.table.setItem(row, col_index, item)
    
    def _populate_row(self, row: int, position: int, driver_data: Dict):
        """填充單行數據（✅ 移除排名欄位，所有欄位索引減 1）"""
        driver = driver_data.get("driver", "")
        team = driver_data.get("team", "")
        max_speed = driver_data.get("max_speed_kmh", 0)
        
        # ⭐ v3.5 修正欄位對應（2025-10-19）✅ 移除錯誤的交換邏輯
        # CLI 修正後，JSON 數據已經正確：
        #   - segment_accel_time_seconds = 到統一終點速度的時間（較短）✅
        #   - max_speed_time_seconds = 到個人最高速度的時間（較長）✅
        # 用戶需求：
        #   - "Accel Time" = 到統一速度的時間（較短）
        #   - "Max Speed Time" = 到個人最高速度的時間（較長）
        # ✅ JSON 已正確，GUI 直接使用，不需交換！
        
        segment_accel_time_raw = driver_data.get("segment_accel_time_seconds", None)  # 統一速度時間（較短）✅
        max_speed_time_raw = driver_data.get("max_speed_time_seconds", None)  # 個人最高速度時間（較長）✅
        
        # ✅ 直接使用，不交換
        accel_time_display = segment_accel_time_raw  # GUI 欄位 "Accel Time" 顯示統一速度時間（較短）
        max_speed_time_display = max_speed_time_raw  # GUI 欄位 "Max Speed Time" 顯示個人最高速度時間（較長）
        
        # 其他數據保持不變
        segment_accel_distance = driver_data.get("segment_accel_distance_meters", None)
        segment_avg_accel = driver_data.get("segment_avg_acceleration_ms2", None)
        segment_start_speed = driver_data.get("segment_start_speed_kmh", None)
        segment_end_speed = driver_data.get("segment_end_speed_kmh", None)
        segment_speed_gain = driver_data.get("segment_speed_gain_kmh", None)
        
        # ✅ 標記是否有有效數據
        has_segment_data = accel_time_display is not None  # 使用 accel_time_display 判斷
        
        # 轉換為浮點數（None → 0.0）
        accel_time_display = float(accel_time_display) if accel_time_display is not None else 0.0
        max_speed_time_display = float(max_speed_time_display) if max_speed_time_display is not None else 0.0
        segment_avg_accel = float(segment_avg_accel) if segment_avg_accel is not None else 0.0
        segment_speed_gain = float(segment_speed_gain) if segment_speed_gain is not None else 0.0
        
        # 調試輸出
        if row == 0:  # 只輸出第一行
            print(f"[DEBUG] 第一行數據: driver={driver}, max_speed={max_speed}")
            print(f"[DEBUG] accel_time_display={accel_time_display}, max_speed_time_display={max_speed_time_display}")
        
        # ❌ 移除：0. 排名（Qt 動態排序會改變順序，固定排名會誤導用戶）
        
        # ✅ 0. 車手（車隊背景色）
        driver_item = QTableWidgetItem(driver)
        driver_item.setTextAlignment(Qt.AlignCenter)
        driver_item.setFont(QFont("Arial", 10))  # ✅ 移除粗體
        
        # ✅ 設置車隊背景色（與 driver_standings 一致使用 color_palette_provider）
        driver_color = color_palette_provider.get_driver_color(driver, fallback=True)
        driver_item.setBackground(driver_color)
        
        # 根據背景色亮度決定文字顏色
        luminance = (0.299 * driver_color.red() + 0.587 * driver_color.green() + 0.114 * driver_color.blue())
        text_color = QColor(255, 255, 255) if luminance < 128 else QColor(0, 0, 0)
        driver_item.setForeground(QBrush(text_color))
        driver_item.setToolTip(tr("straight_speed_driver_tooltip", "{driver} - {team}").format(
            driver=driver, team=team
        ))
        
        self._set_item_at_column(row, 'driver', driver_item)
        
        # ✅ 1. 車隊（車隊背景色）
        team_item = QTableWidgetItem(team)
        team_item.setTextAlignment(Qt.AlignCenter)
        team_item.setFont(QFont("Arial", 9))
        # ✅ 設置車隊背景色（與車手欄位一致）
        team_item.setBackground(driver_color)
        team_item.setForeground(QBrush(text_color))
        team_item.setToolTip(tr("straight_speed_team_tooltip", "{team}").format(team=team))
        self._set_item_at_column(row, 'team', team_item)
        
        # ✅ 2. 最高速度（顏色編碼）
        speed_item = QTableWidgetItem(f"{max_speed:.1f} km/h")
        speed_item.setTextAlignment(Qt.AlignCenter)
        speed_item.setFont(QFont("Arial", 9))
        # ✅ 設置數值用於排序（避免字串排序問題）
        speed_item.setData(Qt.DisplayRole, max_speed)  # ✅ 設置數字用於排序
        speed_item.setData(Qt.UserRole, max_speed)     # ✅ 保留 UserRole
        
        # 速度顏色編碼
        speed_color = self._get_speed_color(max_speed)
        speed_item.setForeground(QBrush(speed_color))
        
        self._set_item_at_column(row, 'max_speed', speed_item)
        
        # ⭐ 3. 加速時間（到達統一終點速度的時間，較短）
        # ✅ v3.4 修正: 使用 accel_time_display (來自 max_speed_time_seconds)
        if has_segment_data:
            seg_time_item = QTableWidgetItem(f"{accel_time_display:.3f} s")
            seg_time_item.setData(Qt.DisplayRole, accel_time_display)  # ✅ 設置數字用於排序
            seg_time_item.setData(Qt.UserRole, accel_time_display)     # ✅ 保留 UserRole 供其他功能使用
            seg_time_item.setFont(QFont("Arial", 9, QFont.Bold))
            seg_time_item.setForeground(QBrush(QColor(0, 100, 200)))  # 深藍色
        else:
            seg_time_item = QTableWidgetItem("N/A")
            seg_time_item.setData(Qt.DisplayRole, 9999)  # ✅ N/A 排序時放最後
            seg_time_item.setData(Qt.UserRole, 9999)
            seg_time_item.setForeground(QBrush(QColor(150, 150, 150)))
        seg_time_item.setTextAlignment(Qt.AlignCenter)
        self._set_item_at_column(row, 'accel_time', seg_time_item)
        
        # ⭐ 4. 平均加速度（賽道段平均加速度）
        if has_segment_data:
            seg_accel_item = QTableWidgetItem(f"{segment_avg_accel:.2f} m/s²")
            seg_accel_item.setData(Qt.DisplayRole, segment_avg_accel)  # ✅ 設置數字用於排序
            seg_accel_item.setData(Qt.UserRole, segment_avg_accel)
            seg_accel_item.setFont(QFont("Arial", 9, QFont.Bold))
            seg_accel_item.setForeground(QBrush(QColor(0, 150, 0)))  # 深綠色
        else:
            seg_accel_item = QTableWidgetItem("N/A")
            seg_accel_item.setData(Qt.DisplayRole, 0)
            seg_accel_item.setData(Qt.UserRole, 0)
            seg_accel_item.setForeground(QBrush(QColor(150, 150, 150)))
        seg_accel_item.setTextAlignment(Qt.AlignCenter)
        self._set_item_at_column(row, 'avg_accel', seg_accel_item)
        
        # ⭐ 5. 起始速度（賽道段起始速度）
        if has_segment_data and segment_start_speed is not None:
            start_speed_item = QTableWidgetItem(f"{segment_start_speed:.0f} km/h")
            start_speed_item.setData(Qt.DisplayRole, segment_start_speed)  # ✅ 設置數字用於排序
            start_speed_item.setData(Qt.UserRole, segment_start_speed)
            start_speed_item.setFont(QFont("Arial", 9))
            # Tooltip 顯示速度變化範圍
            if segment_end_speed:
                start_speed_item.setToolTip(tr("straight_speed_start_speed_tooltip", "起始→結束: {start} → {end} km/h").format(
                    start=f"{segment_start_speed:.0f}", end=f"{segment_end_speed:.0f}"
                ))
        else:
            start_speed_item = QTableWidgetItem("N/A")
            start_speed_item.setData(Qt.DisplayRole, 0)
            start_speed_item.setData(Qt.UserRole, 0)
            start_speed_item.setForeground(QBrush(QColor(150, 150, 150)))
        start_speed_item.setTextAlignment(Qt.AlignCenter)
        self._set_item_at_column(row, 'start_speed', start_speed_item)
        
        # ⭐ 6. 最高速度時間（到達個人最高速度所需時間，較長）
        # ✅ v3.4 修正: 使用 max_speed_time_display (來自 segment_accel_time_seconds)
        if has_segment_data and max_speed_time_display is not None and max_speed_time_display > 0:
            max_speed_time_item = QTableWidgetItem(f"{max_speed_time_display:.2f} s")
            max_speed_time_item.setData(Qt.DisplayRole, max_speed_time_display)  # ✅ 設置數字用於排序
            max_speed_time_item.setData(Qt.UserRole, max_speed_time_display)
            max_speed_time_item.setFont(QFont("Arial", 9, QFont.Bold))
            max_speed_time_item.setForeground(QBrush(QColor(0, 100, 200)))  # 藍色
            # Tooltip 顯示與加速時間的對比
            if accel_time_display and accel_time_display > 0:
                time_diff = max_speed_time_display - accel_time_display
                max_speed_time_item.setToolTip(tr("straight_speed_max_speed_time_tooltip", "到達個人最高速度時間: {max_time}s\n加速時間（到統一終點）: {accel_time}s\n時間差: +{diff}s").format(
                    max_time=f"{max_speed_time_display:.2f}",
                    accel_time=f"{accel_time_display:.2f}",
                    diff=f"{time_diff:.2f}"
                ))
        else:
            max_speed_time_item = QTableWidgetItem("N/A")
            max_speed_time_item.setData(Qt.DisplayRole, 0)
            max_speed_time_item.setData(Qt.UserRole, 0)
            max_speed_time_item.setForeground(QBrush(QColor(150, 150, 150)))
        max_speed_time_item.setTextAlignment(Qt.AlignCenter)
        self._set_item_at_column(row, 'max_speed_time', max_speed_time_item)
        
        # ✅ 7. 加速性能視覺化（使用委託繪製）
        bar_item = QTableWidgetItem()
        # ✅ v3.4 修正: 使用 accel_time_display 作為排序依據（到統一速度的時間）
        if has_segment_data:
            bar_item.setData(Qt.DisplayRole, accel_time_display)  # ✅ 排序依據：統一速度時間
            bar_item.setData(Qt.UserRole, accel_time_display)     # ✅ 保留 UserRole
            bar_item.setData(Qt.UserRole + 2, accel_time_display)  # 繪圖用：統一速度時間
        else:
            bar_item.setData(Qt.DisplayRole, 9999)  # N/A 排序時放最後
            bar_item.setData(Qt.UserRole, 9999)
            bar_item.setData(Qt.UserRole + 2, 0)
        bar_item.setData(Qt.UserRole + 1, max_speed)  # 最高速度（繪圖用）
        bar_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self._set_item_at_column(row, 'performance_bar', bar_item)
        
        # ✅ 儲存額外數據（用於點擊詳情）- 使用 driver_item 而非已移除的 pos_item
        driver_item.setData(Qt.UserRole, {
            "driver": driver,
            "team": team,
            "max_speed": max_speed,
            "accel_time": accel_time_display,  # ✅ 修正：統一速度時間
            "max_speed_time": max_speed_time_display,  # ✅ 修正：個人最高速度時間
            "segment_avg_accel": segment_avg_accel,
            "segment_speed_gain": segment_speed_gain,
            "segment_start_speed": segment_start_speed,
            "segment_end_speed": segment_end_speed
        })
    
    def _get_speed_color(self, speed: float) -> QColor:
        """
        根據最高速度返回顏色
        
        綠色: > 325 km/h (快)
        黃色: 320 - 325 km/h (中等)
        橙色: < 320 km/h (慢)
        """
        if speed > 325:
            return QColor(0, 150, 0)  # 綠色
        elif speed > 320:
            return QColor(200, 150, 0)  # 黃色
        else:
            return QColor(255, 100, 0)  # 橙色
    
    def _on_cell_clicked(self, row: int, column: int):
        """處理單元格點擊事件"""
        try:
            # 獲取車手數據
            pos_item = self.table.item(row, 0)
            if not pos_item:
                return
            
            driver_data = pos_item.data(Qt.UserRole)
            if not driver_data:
                return
            
            # 顯示詳細資訊
            self._show_driver_details(driver_data)
            
        except Exception as e:
            print(f"[ERROR] [SPEED_TABLE] 點擊處理失敗: {e}")
    
    def _show_driver_details(self, driver_data: Dict):
        """顯示車手詳細資訊彈窗"""
        driver = driver_data.get("driver", "")
        team = driver_data.get("team", "")
        max_speed = driver_data.get("max_speed", 0)
        time_to_max = driver_data.get("time_to_max", 0)
        accel_100_300_time = driver_data.get("accel_100_300_time", 0)
        accel_distance = driver_data.get("accel_distance", 0)
        accel_avg = driver_data.get("accel_avg", 0)
        
        details = tr("straight_speed_driver_details", 
"""車手詳細資訊 - {driver}

車手: {driver}
車隊: {team}

最高速度: {max_speed} km/h

加速性能 (100 → 300 km/h):
  時間: {accel_100_300_time} s
  距離: {accel_distance} m
  平均加速度: {accel_avg} m/s²

加速性能 (100 → {max_speed_full} km/h):
  時間: {time_to_max} s""").format(
            driver=driver,
            team=team,
            max_speed=f"{max_speed:.1f}",
            accel_100_300_time=f"{accel_100_300_time:.3f}",
            accel_distance=f"{accel_distance:.1f}",
            accel_avg=f"{accel_avg:.2f}",
            max_speed_full=f"{max_speed:.1f}",
            time_to_max=f"{time_to_max:.2f}"
        ).strip()
        
        QMessageBox.information(
            self, 
            tr("straight_speed_driver_info_title", "車手資訊 - {driver}").format(driver=driver), 
            details
        )
    
    def sort_data(self, sort_key: str):
        """
        排序數據
        
        Args:
            sort_key: 排序鍵 ('max_speed', 'accel_time', 'accel_distance')
        """
        if sort_key == "max_speed":
            self.table.sortItems(2, Qt.DescendingOrder)
        elif sort_key == "accel_time":
            self.table.sortItems(3, Qt.AscendingOrder)
        elif sort_key == "accel_distance":
            # 需要重新排序數據
            pass
    
    def export_chart(self, file_path: str) -> bool:
        """
        匯出表格為圖片
        
        Args:
            file_path: 匯出檔案路徑
            
        Returns:
            bool: 匯出是否成功
        """
        try:
            # TODO: 實現表格截圖功能
            print(f"[SPEED_TABLE] 匯出功能開發中: {file_path}")
            return False
        except Exception as e:
            print(f"[ERROR] [SPEED_TABLE] 匯出失敗: {e}")
            return False
