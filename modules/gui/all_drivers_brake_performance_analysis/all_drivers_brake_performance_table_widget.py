#!/usr/bin/env python3
"""
全車手煞車性能分析表格元件 - QTableWidget 版本
All Drivers Brake Performance Table Widget

✅ 復刻 ideal_lap_sector_comparison 的 QTableWidget 架構
✅ 使用自定義 Delegate 繪製煞車時間棒狀圖

作者: F1T Team
日期: 2025-10-18
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
from modules.gui.ideal_lap_analysis.shared_colors import (
    get_team_color,
)


class DecelerationBarDelegate(QStyledItemDelegate):
    """
    減速時間棒狀圖委託
    
    ⭐ 視覺化邏輯：
    - 棒狀圖長度 = 基於賽道段煞車時間（brake_time_seconds）
    - 時間越短 = 棒狀圖越短 = 性能越好
    - 使用相對時間範圍計算，使差異更明顯
    
    ⭐ 數據來源：
    - UserRole: brake_time（用於排序和繪圖）
    - UserRole+1: max_deceleration（最大減速度，用於顯示）
    - UserRole+2: brake_time（重複，保持一致性）
    """
    
    def __init__(self, min_time: float = 0.0, max_time: float = 10.0, parent=None):
        super().__init__(parent)
        self.min_time = min_time  # 最快車手的時間（例如 9.480s）
        self.max_time = max_time  # 最慢車手的時間（例如 10.120s）
        self.time_range = max_time - min_time  # 時間範圍（例如 0.640s）
    
    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        """
        繪製減速視覺化圖表
        
        ⭐ 視覺化設計邏輯：
        ┌─────────────────────────────────────────────────────┐
        │  最快車手                    最慢車手                │
        │    ↓                          ↓                      │
        │    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  1.480s (SAI)       │
        │    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  1.659s (HAM)   │
        │    ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  1.820s (LEC)│
        └─────────────────────────────────────────────────────┘
        
        ⭐ 關鍵邏輯：
        - 棒狀圖長度 ∝ 煞車時間（時間越長，棒越長）
        - 時間短 = 性能好 = 棒短 ✅
        - 相對比例 = (車手時間 - 最快時間) / (最慢時間 - 最快時間)
        """
        # ✅ 獲取賽道段煞車時間數據
        brake_time = index.data(Qt.UserRole)  # 賽道段煞車時間（排序和繪圖依據）
        max_deceleration = index.data(Qt.UserRole + 1)  # 最大減速度（顯示用）
        
        # 檢查數據有效性
        if brake_time is None or brake_time == 9999:
            # N/A 數據，顯示灰色 N/A
            super().paint(painter, option, index)
            return
        
        if brake_time <= 0:
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
            # 例如：最快 1.480s，最慢 1.820s，範圍 0.340s
            # HAM 1.659s: (1.659 - 1.480) / 0.340 = 0.526 (52.6%)
            # LEC 1.820s: (1.820 - 1.480) / 0.340 = 1.000 (100%)
            relative_ratio = (brake_time - self.min_time) / self.time_range
        else:
            # 所有車手時間相同
            relative_ratio = 0.0
        
        # ✅ 棒狀圖寬度（按比例縮放）
        # 時間短 = relative_ratio 小 = 棒狀圖短 = 性能好 ✅
        bar_width = min(bar_max_width * relative_ratio, bar_max_width)
        
        # ===== 繪製減速棒（簡化設計：單一暖紅色實心棒）=====
        # ⭐ 棒狀圖設計：
        # - 暖紅色實心棒，長度代表煞車時間
        # - 棒越短 = 時間越短 = 性能越好
        # - 無需分段顯示（已移除速度範圍概念）
        
        bar_rect = QRectF(base_x, base_y, bar_width, bar_height)
        painter.fillRect(bar_rect, QBrush(QColor(220, 80, 60)))  # 暖紅色實心
        painter.setPen(QPen(QColor(180, 40, 20), 2))  # 深紅邊框
        painter.drawRect(bar_rect)
        
        # ===== 繪製時間標籤（固定位置）=====
        # ✅ 文字使用固定起始位置（棒狀圖最大寬度後）
        text_x = int(base_x + bar_max_width + text_margin)
        
        # 顯示賽道段煞車時間
        painter.setFont(QFont("Arial", 10, QFont.Bold))
        painter.setPen(QPen(QColor(220, 80, 60)))  # 暖紅色
        text_y = int(base_y + 15)
        painter.drawText(text_x, text_y, f"{brake_time:.3f} s")
        
        painter.restore()
    
    def _get_time_color(self, time: float) -> QColor:
        """
        根據煞車時間返回顏色
        
        綠色: < 1.5 秒 (快)
        黃色: 1.5 - 1.7 秒 (中等)
        橙色: > 1.7 秒 (慢)
        """
        if time < 1.5:
            return QColor(100, 200, 100)  # 綠色
        elif time < 1.7:
            return QColor(255, 220, 100)  # 黃色
        else:
            return QColor(255, 150, 100)  # 橙色
    
    def sizeHint(self, option: QStyleOptionViewItem, index):
        """設定單元格大小"""
        return super().sizeHint(option, index)


class AllDriversBrakePerformanceTableWidget(QWidget):
    """
    全車手煞車性能分析表格元件 - QTableWidget 版本
    
    特點：
    - 使用 QTableWidget（與 Ideal Lap Sector Comparison 一致）
    - 車手欄位顯示車隊背景色
    - 最大減速度使用顏色編碼
    - 煞車時間使用棒狀圖 + 虛線（自定義委託）
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 數據屬性
        self.driver_brakes_data: List[Dict] = []
        self.min_time_to_max = 0.0  # 最快車手的時間
        self.max_time_to_max = 0.0  # 最慢車手的時間
        
        # ✅ 統一速度範圍（從 metadata 讀取）
        self.unified_start_speed = 100.0  # 預設值
        self.unified_end_speed = 300.0    # 預設值
        
        # ✅ Distance 範圍資訊（從 reference_brake_zone 讀取）
        self.segment_distance_start = None
        self.segment_distance_end = None
        self.segment_length = None
        
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
        
        格式: 煞車範圍: {start}m → {end}m (長度: {length}m) | 參考車手: {driver}
        """
        if self.segment_distance_start is None or self.segment_distance_end is None:
            self.info_label.setText(tr("brake_performance_info_no_data", "煞車範圍: 未載入資料"))
            return
        
        # 格式化距離資訊
        start_m = f"{self.segment_distance_start:.1f}"
        end_m = f"{self.segment_distance_end:.1f}"
        length_m = f"{self.segment_length:.1f}" if self.segment_length else "N/A"
        
        # 組合顯示文字
        info_text = tr("brake_performance_info_range", "煞車範圍: {start}m → {end}m (長度: {length}m)").format(
            start=start_m, end=end_m, length=length_m
        )
        
        # 如果有參考車手資訊，添加到標籤
        if hasattr(self, 'reference_driver') and self.reference_driver:
            info_text += tr("brake_performance_info_reference", " | 參考車手: {driver}").format(
                driver=self.reference_driver
            )
        
        self.info_label.setText(info_text)
        print(f"[BRAKE_TABLE] 資訊標籤更新: {info_text}")
    
    def _create_table(self) -> QTableWidget:
        """創建表格"""
        table = QTableWidget()
        
        # ⭐ 簡化欄位標題（只保留 segment brake 欄位）
        # 
        # 欄位說明：
        # 1. ❌ 移除「排名」- Qt 動態排序會改變順序，固定排名會誤導
        # 1. 車手 - 3字母代碼（車隊背景色）
        # 2. 車隊 - 車隊名稱（車隊背景色）
        # 3. 最大減速度 - 賽道段內最大減速度（G）
        # 4. ⭐ 煞車時間 - 賽道段煞車時間（秒）
        #    - 計算：brake_end_time - brake_start_time
        #    - 邏輯：時間越短 = 性能越好 ✅
        #    - 排序：升序（最短在前）
        # 5. ⭐ 平均減速度 - 賽道段平均減速度（m/s²）
        #    - 計算：(起始速度 - 結束速度) / 煞車時間 / 3.6
        #    - 邏輯：減速度越大 = 性能越好 ✅
        #    - 排序：降序（最大在前）
        # 6. ⭐ 起始速度 - 賽道段開始時的速度（km/h）
        #    - 來源：brake_start_speed_kmh
        #    - 說明：車手進入煞車區時的速度
        #    - 範例：HAM 310 km/h，LEC 305 km/h
        #    - 意義：起始速度高 = 入彎速度快
        #    - 排序：降序（最高在前）
        #    - Tooltip：顯示「起始→結束速度」（例如：310→103 km/h）
        # 7. ⭐ 煞車性能視覺化 - 棒狀圖顯示煞車時間
        #    - 視覺：棒越短 = 時間越短 = 性能越好 ✅
        #    - 數據來源：brake_time_seconds
        columns = [
            tr('brake_header_driver', '車手'),
            tr('brake_header_team', '車隊'),
            tr('brake_header_max_deceleration_g', '最大減速度 (G)'),
            tr('brake_header_brake_time', '煞車時間 (s)'),
            tr('brake_header_avg_deceleration', '平均減速度 (m/s²)'),
            tr('brake_header_brake_start_speed', '起始速度 (km/h)'),
            tr('brake_header_brake_bar', '煞車性能視覺化')
        ]
        
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        
        # 設置表格屬性
        table.setSortingEnabled(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setSelectionMode(QAbstractItemView.NoSelection)  # ✅ 禁用選擇（避免高亮覆蓋背景色）
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # ✅ 設置固定欄位寬度
        table.setColumnWidth(0, 100)  # 車手（車隊背景色）
        table.setColumnWidth(1, 130)  # 車隊（車隊背景色）
        table.setColumnWidth(2, 110)  # 最高速度
        table.setColumnWidth(3, 120)  # 加速時間
        table.setColumnWidth(4, 140)  # 平均加速度
        table.setColumnWidth(5, 120)  # 起始速度
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
            data: 包含 driver_brakes 和 metadata 的字典
        """
        try:
            print(f"[BRAKE_TABLE] update_data 被調用，data keys: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
            
            if not data or not isinstance(data, dict):
                print("[WARNING] [BRAKE_TABLE] 無效的數據格式")
                return
            
            # ✅ 提取 metadata 並讀取統一速度範圍
            metadata = data.get("metadata", {})
            unified_speed_range = metadata.get("unified_speed_range", {})
            
            if unified_speed_range:
                self.unified_start_speed = unified_speed_range.get("start_speed_kmh", 100.0)
                self.unified_end_speed = unified_speed_range.get("end_speed_kmh", 300.0)
                print(f"[BRAKE_TABLE] 統一速度範圍: {self.unified_start_speed:.0f}→{self.unified_end_speed:.0f} km/h")
            else:
                print("[WARNING] [BRAKE_TABLE] 未找到 unified_speed_range，使用預設值 100→300 km/h")
            
            # ✅ 提取 reference_brake_zone 距離範圍資訊
            reference_brake_zone = data.get("reference_brake_zone", {})
            if reference_brake_zone:
                self.segment_distance_start = reference_brake_zone.get("brake_start_distance")
                self.segment_distance_end = reference_brake_zone.get("brake_end_distance")
                self.segment_length = reference_brake_zone.get("brake_distance")
                self.reference_driver = reference_brake_zone.get("driver", "")
                print(f"[BRAKE_TABLE] 距離範圍: {self.segment_distance_start:.1f}m → {self.segment_distance_end:.1f}m (長度: {self.segment_length:.1f}m)")
                
                # ✅ 更新資訊標籤
                self._update_info_label()
            else:
                print("[WARNING] [BRAKE_TABLE] 未找到 reference_brake_zone 資訊")
            
            # 提取車手數據
            self.driver_brakes_data = data.get("driver_brakes", [])
            print(f"[BRAKE_TABLE] driver_brakes 數量: {len(self.driver_brakes_data)}")
            
            if not self.driver_brakes_data:
                print("[WARNING] [BRAKE_TABLE] 無 driver_brakes 數據")
                return
            
            # ✅ 學習 Ideal Lap Ranking：只更新內容，不重建表格
            # 計算時間範圍（用於委託）
            self._calculate_max_time()
            
            # 填充表格（_populate_table 內部會處理排序和行數）
            self._populate_table()
            
            print(f"[BRAKE_TABLE] 表格更新完成：{len(self.driver_brakes_data)} 位車手")
            
        except Exception as e:
            print(f"[ERROR] [SPEED_TABLE] 更新數據失敗: {e}")
            import traceback
            traceback.print_exc()
    
    def _calculate_max_time(self):
        """計算時間範圍（用於視覺化棒狀圖）"""
        min_time = float('inf')
        max_time = 0.0
        
        for driver_data in self.driver_brakes_data:
            # ⭐ 使用正確的 brake_time_s 鍵名（與 CLI 輸出一致）
            brake_time = driver_data.get("brake_time_s", None)
            
            if brake_time is not None and brake_time > 0:
                min_time = min(min_time, brake_time)
                max_time = max(max_time, brake_time)
        
        # 儲存時間範圍
        self.min_time_to_max = min_time if min_time != float('inf') else 0.0
        self.max_time_to_max = max_time if max_time > 0 else 10.0
        
        print(f"[BRAKE_TABLE] 時間範圍: {self.min_time_to_max:.3f}s ~ {self.max_time_to_max:.3f}s")
    
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
        row_count = len(self.driver_brakes_data)
        
        self.table.setSortingEnabled(False)
        self.table.setRowCount(row_count)
        
        # ✅ 修正：學習 Ranking Table - 不預先排序，讓 Qt 內建排序功能處理
        # ❌ 舊代碼：預先按最大減速度排序，導致 Qt 排序功能混亂
        # sorted_data = sorted(
        #     self.driver_brakes_data, 
        #     key=lambda x: x.get("max_deceleration_g", 0), 
        #     reverse=True
        # )
        
        # ✅ 直接按原始順序填充（通常是按車手代碼字母順序）
        for row, driver_data in enumerate(self.driver_brakes_data):
            self._populate_row(row, row + 1, driver_data)
        
        # ✅ 設置減速棒狀圖欄位的委託（現在是欄位 6，傳遞時間範圍）
        bar_delegate = DecelerationBarDelegate(self.min_time_to_max, self.max_time_to_max, self.table)
        self.table.setItemDelegateForColumn(6, bar_delegate)
        print(f"[BRAKE_TABLE] 委託已設置，欄位 6，時間範圍 {self.min_time_to_max:.3f}s ~ {self.max_time_to_max:.3f}s")
        
        self.table.setSortingEnabled(True)
    
    def _populate_row(self, row: int, position: int, driver_data: Dict):
        """填充單行數據 - 煞車性能"""
        driver = driver_data.get("driver", "")
        team = driver_data.get("team", "")
        
        # ⭐ 修正：使用煞車數據鍵名
        max_deceleration_g = driver_data.get("max_deceleration_g", 0)  # G 單位
        max_deceleration_ms2 = driver_data.get("max_deceleration_ms2", 0)  # m/s² 單位
        
        # ⭐ 讀取新的 brake performance 數據（賽道段煞車性能）
        brake_start_speed = driver_data.get("brake_start_speed_kmh", None)
        brake_end_speed = driver_data.get("brake_end_speed_kmh", None)
        speed_reduction = driver_data.get("speed_reduction_kmh", None)
        brake_distance = driver_data.get("brake_distance_m", None)
        brake_time = driver_data.get("brake_time_s", None)
        brake_start_position = driver_data.get("brake_start_position", None)
        brake_end_position = driver_data.get("brake_end_position", None)
        
        # ✅ 標記是否有有效數據
        has_brake_data = brake_time is not None and brake_distance is not None
        
        # 轉換為浮點數（None → 0.0）
        brake_time_val = float(brake_time) if brake_time is not None else 0.0
        brake_distance_val = float(brake_distance) if brake_distance is not None else 0.0
        speed_reduction_val = float(speed_reduction) if speed_reduction is not None else 0.0
        brake_start_speed_val = float(brake_start_speed) if brake_start_speed is not None else 0.0
        brake_end_speed_val = float(brake_end_speed) if brake_end_speed is not None else 0.0
        
        # 調試輸出
        if row == 0:  # 只輸出第一行
            print(f"[DEBUG] 第一行數據: driver={driver}, max_deceleration_g={max_deceleration_g}")
            print(f"[DEBUG] brake_time={brake_time_val}, brake_distance={brake_distance_val}, speed_reduction={speed_reduction_val}")
        
        # ❌ 移除：0. 排名（Qt 動態排序會改變順序，固定排名會誤導用戶）
        
        # ✅ 0. 車手（車隊背景色）
        driver_item = QTableWidgetItem(driver)
        driver_item.setTextAlignment(Qt.AlignCenter)
        driver_item.setFont(QFont("Arial", 10, QFont.Bold))
        
        # ✅ 設置車隊背景色（使用共用配色模組）
        team_color = get_team_color(team)
        driver_item.setBackground(team_color)  # ✅ 直接傳 QColor
        driver_item.setForeground(QBrush(QColor(0, 0, 0)))  # 黑色文字
        driver_item.setToolTip(tr("brake_performance_driver_tooltip", "{driver} - {team}").format(
            driver=driver, team=team
        ))
        
        self.table.setItem(row, 0, driver_item)
        
        # ✅ 1. 車隊（車隊背景色）
        team_item = QTableWidgetItem(team)
        team_item.setTextAlignment(Qt.AlignCenter)
        team_item.setFont(QFont("Arial", 9))
        # ✅ 設置車隊背景色（與車手欄位一致）
        team_item.setBackground(team_color)
        team_item.setForeground(QBrush(QColor(0, 0, 0)))  # 黑色文字
        team_item.setToolTip(tr("brake_performance_team_tooltip", "{team}").format(team=team))
        self.table.setItem(row, 1, team_item)
        
        # ✅ 2. 最大減速度（G 單位，顏色編碼）
        decel_item = QTableWidgetItem(f"{max_deceleration_g:.2f} G")
        decel_item.setTextAlignment(Qt.AlignCenter)
        decel_item.setFont(QFont("Arial", 9))
        # ✅ 設置數值用於排序（避免字串排序問題）
        decel_item.setData(Qt.DisplayRole, max_deceleration_g)  # ✅ 設置數字用於排序
        decel_item.setData(Qt.UserRole, max_deceleration_g)     # ✅ 保留 UserRole
        
        # 減速度顏色編碼（G 值越高越好，閾值: >2.5G 綠色, >2.0G 橙色, <2.0G 紅色）
        decel_color = self._get_deceleration_color(max_deceleration_g)
        decel_item.setForeground(QBrush(decel_color))
        
        # Tooltip 顯示 m/s² 單位
        decel_item.setToolTip(
            tr("brake_deceleration_tooltip", "{g:.2f} G ({ms2:.2f} m/s²)").format(
                g=max_deceleration_g, ms2=max_deceleration_ms2
            )
        )
        
        self.table.setItem(row, 2, decel_item)
        
        # ⭐ 3. 煞車時間（煞車區間時間）
        if has_brake_data:
            brake_time_item = QTableWidgetItem(f"{brake_time_val:.3f} s")
            brake_time_item.setData(Qt.DisplayRole, brake_time_val)  # ✅ 設置數字用於排序
            brake_time_item.setData(Qt.UserRole, brake_time_val)     # ✅ 保留 UserRole 供其他功能使用
            brake_time_item.setFont(QFont("Arial", 9, QFont.Bold))
            brake_time_item.setForeground(QBrush(QColor(200, 0, 0)))  # 深紅色（煞車）
        else:
            brake_time_item = QTableWidgetItem("N/A")
            brake_time_item.setData(Qt.DisplayRole, 9999)  # ✅ N/A 排序時放最後
            brake_time_item.setData(Qt.UserRole, 9999)
            brake_time_item.setForeground(QBrush(QColor(150, 150, 150)))
        brake_time_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 3, brake_time_item)
        
        # ⭐ 4. 平均減速度（煞車區間平均減速度 = 速度差 / 時間）
        if has_brake_data and brake_time_val > 0:
            # 計算平均減速度（km/h → m/s，再除以時間）
            avg_decel = (speed_reduction_val / 3.6) / brake_time_val  # m/s²
            avg_decel_item = QTableWidgetItem(f"{avg_decel:.2f} m/s²")
            avg_decel_item.setData(Qt.DisplayRole, avg_decel)  # ✅ 設置數字用於排序
            avg_decel_item.setData(Qt.UserRole, avg_decel)
            avg_decel_item.setFont(QFont("Arial", 9, QFont.Bold))
            avg_decel_item.setForeground(QBrush(QColor(150, 0, 0)))  # 深紅色
        else:
            avg_decel_item = QTableWidgetItem("N/A")
            avg_decel_item.setData(Qt.DisplayRole, 0)
            avg_decel_item.setData(Qt.UserRole, 0)
            avg_decel_item.setForeground(QBrush(QColor(150, 150, 150)))
        avg_decel_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 4, avg_decel_item)
        
        # ⭐ 5. 煞車前速度（煞車區間起始速度）
        if has_brake_data and brake_start_speed_val > 0:
            start_speed_item = QTableWidgetItem(f"{brake_start_speed_val:.0f} km/h")
            start_speed_item.setData(Qt.DisplayRole, brake_start_speed_val)  # ✅ 設置數字用於排序
            start_speed_item.setData(Qt.UserRole, brake_start_speed_val)
            start_speed_item.setFont(QFont("Arial", 9))
            # Tooltip 顯示速度變化範圍
            if brake_end_speed_val > 0:
                start_speed_item.setToolTip(tr("brake_speed_range", "煞車前→煞車後: {start} → {end} km/h (減速 {reduction} km/h)").format(
                    start=f"{brake_start_speed_val:.0f}", 
                    end=f"{brake_end_speed_val:.0f}",
                    reduction=f"{speed_reduction_val:.0f}"
                ))
        else:
            start_speed_item = QTableWidgetItem("N/A")
            start_speed_item.setData(Qt.DisplayRole, 0)
            start_speed_item.setData(Qt.UserRole, 0)
            start_speed_item.setForeground(QBrush(QColor(150, 150, 150)))
        start_speed_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 5, start_speed_item)
        
        # ✅ 6. 煞車性能視覺化（使用委託繪製減速度棒狀圖）
        bar_item = QTableWidgetItem()
        # ✅ 使用 brake_time 作為排序依據
        if has_brake_data:
            bar_item.setData(Qt.DisplayRole, brake_time_val)  # ✅ 排序依據：煞車時間
            bar_item.setData(Qt.UserRole, brake_time_val)     # ✅ 保留 UserRole
            bar_item.setData(Qt.UserRole + 2, brake_time_val)  # 繪圖用：煞車時間
        else:
            bar_item.setData(Qt.DisplayRole, 9999)  # N/A 排序時放最後
            bar_item.setData(Qt.UserRole, 9999)
            bar_item.setData(Qt.UserRole + 2, 0)
        bar_item.setData(Qt.UserRole + 1, max_deceleration_g)  # 最大減速度（繪圖用）
        bar_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.table.setItem(row, 6, bar_item)
        
        # ✅ 儲存額外數據（用於點擊詳情）- 使用 driver_item 而非已移除的 pos_item
        driver_item.setData(Qt.UserRole, {
            "driver": driver,
            "team": team,
            "max_deceleration_g": max_deceleration_g,
            "max_deceleration_ms2": max_deceleration_ms2,
            "brake_time": brake_time,
            "brake_distance": brake_distance,
            "speed_reduction": speed_reduction,
            "brake_start_speed": brake_start_speed,
            "brake_end_speed": brake_end_speed,
            "brake_start_position": brake_start_position,
            "brake_end_position": brake_end_position
        })
    
    def _get_deceleration_color(self, decel_g: float) -> QColor:
        """
        根據最大減速度（G）返回顏色
        
        綠色: > 2.5 G (強煞車)
        橙色: 2.0 - 2.5 G (中等煞車)
        紅色: < 2.0 G (弱煞車)
        """
        if decel_g > 2.5:
            return QColor(0, 150, 0)  # 綠色
        elif decel_g > 2.0:
            return QColor(255, 150, 0)  # 橙色
        else:
            return QColor(200, 0, 0)  # 紅色
    
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
            print(f"[ERROR] [BRAKE_TABLE] 點擊處理失敗: {e}")
    
    def _show_driver_details(self, driver_data: Dict):
        """顯示車手煞車性能詳細資訊彈窗"""
        driver = driver_data.get("driver", "")
        team = driver_data.get("team", "")
        max_deceleration_g = driver_data.get("max_deceleration_g", 0)
        max_deceleration_ms2 = driver_data.get("max_deceleration_ms2", 0)
        brake_time = driver_data.get("brake_time", 0)
        brake_distance = driver_data.get("brake_distance", 0)
        speed_reduction = driver_data.get("speed_reduction", 0)
        brake_start_speed = driver_data.get("brake_start_speed", 0)
        brake_end_speed = driver_data.get("brake_end_speed", 0)
        brake_start_position = driver_data.get("brake_start_position", 0)
        brake_end_position = driver_data.get("brake_end_position", 0)
        
        # 計算平均減速度
        avg_decel = 0
        if brake_time and brake_time > 0:
            avg_decel = (speed_reduction / 3.6) / brake_time  # m/s²
        
        details = tr("brake_performance_driver_details", 
"""車手煞車性能詳情 - {driver}

車手: {driver}
車隊: {team}

最大減速度: {max_decel_g} G ({max_decel_ms2} m/s²)

煞車性能:
  煞車時間: {brake_time} s
  煞車距離: {brake_distance} m
  平均減速度: {avg_decel} m/s²

速度變化:
  煞車前速度: {brake_start_speed} km/h
  煞車後速度: {brake_end_speed} km/h
  速度減少: {speed_reduction} km/h

位置範圍:
  開始位置: {brake_start_pos} m
  結束位置: {brake_end_pos} m""").format(
            driver=driver,
            team=team,
            max_decel_g=f"{max_deceleration_g:.2f}",
            max_decel_ms2=f"{max_deceleration_ms2:.2f}",
            brake_time=f"{brake_time:.3f}" if brake_time else "N/A",
            brake_distance=f"{brake_distance:.1f}" if brake_distance else "N/A",
            avg_decel=f"{avg_decel:.2f}",
            brake_start_speed=f"{brake_start_speed:.0f}" if brake_start_speed else "N/A",
            brake_end_speed=f"{brake_end_speed:.0f}" if brake_end_speed else "N/A",
            speed_reduction=f"{speed_reduction:.0f}" if speed_reduction else "N/A",
            brake_start_pos=f"{brake_start_position:.1f}" if brake_start_position else "N/A",
            brake_end_pos=f"{brake_end_position:.1f}" if brake_end_position else "N/A"
        ).strip()
        
        QMessageBox.information(
            self, 
            tr("brake_performance_driver_info_title", "車手煞車資訊 - {driver}").format(driver=driver), 
            details
        )
    
    def sort_data(self, sort_key: str):
        """
        排序數據
        
        Args:
            sort_key: 排序鍵 ('max_deceleration', 'brake_time', 'brake_distance')
        """
        if sort_key == "max_deceleration":
            self.table.sortItems(2, Qt.DescendingOrder)  # 欄位 2: 最大減速度（降序）
        elif sort_key == "brake_time":
            self.table.sortItems(3, Qt.AscendingOrder)  # 欄位 3: 煞車時間（升序）
        elif sort_key == "brake_distance":
            # 需要重新排序數據（如果有距離欄位）
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
            print(f"[BRAKE_TABLE] 匯出功能開發中: {file_path}")
            return False
        except Exception as e:
            print(f"[ERROR] [BRAKE_TABLE] 匯出失敗: {e}")
            return False
