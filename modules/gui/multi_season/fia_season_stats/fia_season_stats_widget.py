#!/usr/bin/env python3
"""
FIA Season Stats Widget
========================

FIA 賽季統計主要元件 - 表格+詳情混合佈局

功能特點：
- 左側: PU 元件使用統計表格 (車手/ICE/TC/MGU-H/MGU-K/ES/CE/狀態)
- 右側: 選中車手的詳細資訊面板
- 頂部: 年份選擇/篩選/圖例說明
- 底部: 統計摘要

狀態圖例:
- 正常 (未達限制): 綠色
- 達限 (=限制): 橘色
- 超限 (>限制): 紅色

作者: F1T Team
日期: 2026-01-22
版本: 1.0.0
"""

from __future__ import annotations

import sys
from typing import Dict, List, Any, Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QBrush, QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLabel, QComboBox, QPushButton, QFrame,
    QGroupBox, QScrollArea, QProgressBar,
    QApplication, QMessageBox
)

from core.gui_i18n import tr, get_team_name_text
from core.logger import get_logger
from modules.gui.themes.color_palette_provider import color_palette_provider

logger = get_logger(__name__)


# =============================================================================
# 常量定義
# =============================================================================

# PU 元件規則限制 (每賽季)
PU_LIMITS = {
    "ICE": 4,      # Internal Combustion Engine
    "TC": 4,       # Turbocharger
    "MGU-H": 4,    # Motor Generator Unit - Heat
    "MGU-K": 3,    # Motor Generator Unit - Kinetic
    "ES": 3,       # Energy Store
    "CE": 3,       # Control Electronics
}

# 狀態顏色定義
STATUS_COLORS = {
    "normal": "#4CAF50",    # 綠色 - 正常
    "warning": "#FF9800",   # 橘色 - 達限
    "exceeded": "#F44336",  # 紅色 - 超限
}

# 狀態符號
STATUS_SYMBOLS = {
    "normal": "",
    "warning": "",
    "exceeded": "",
}


class FiaSeasonStatsWidget(QWidget):
    """FIA 賽季統計主要元件"""
    
    # 信號
    driver_selected = pyqtSignal(str)  # 車手選中信號
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logger
        
        # 數據
        self._data: Dict[str, Any] = {}
        self._drivers_data: Dict[str, Dict] = {}
        self._raw_parts_data: Dict[str, List] = {}
        self._current_driver: Optional[str] = None
        
        # UI 元件
        self._table: Optional[QTableWidget] = None
        self._detail_panel: Optional[QWidget] = None
        self._stats_label: Optional[QLabel] = None
        self._filter_combo: Optional[QComboBox] = None
        
        self._setup_ui()
        self._setup_connections()
        
        logger.info("[FIA_STATS_WIDGET] Widget initialized")
    
    def _setup_ui(self):
        """設置使用者界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # 頂部: 圖例說明 + 篩選
        self._setup_header(main_layout)
        
        # 中間: 分割面板 (左表格 + 右詳情)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        
        # 左側: 表格
        left_widget = self._create_table_panel()
        splitter.addWidget(left_widget)
        
        # 右側: 詳情面板
        right_widget = self._create_detail_panel()
        splitter.addWidget(right_widget)
        
        # 設置分割比例 (60:40)
        splitter.setSizes([600, 400])
        main_layout.addWidget(splitter, 1)
        
        # 底部: 統計摘要
        self._setup_footer(main_layout)
    
    def _setup_header(self, layout: QVBoxLayout):
        """設置頂部區域"""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_frame.setFixedHeight(50)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        # 圖例
        legend_label = QLabel(
            f"<b>{tr('legend', 'Legend')}:</b> "
            f"<span style='color:{STATUS_COLORS['normal']}'>{STATUS_SYMBOLS['normal']} {tr('normal', 'Normal')}</span> | "
            f"<span style='color:{STATUS_COLORS['warning']}'>{STATUS_SYMBOLS['warning']} {tr('at_limit', 'At Limit')}</span> | "
            f"<span style='color:{STATUS_COLORS['exceeded']}'>{STATUS_SYMBOLS['exceeded']} {tr('exceeded', 'Exceeded')}</span>"
        )
        header_layout.addWidget(legend_label)
        
        header_layout.addStretch()
        
        # 規則說明
        rules_label = QLabel(
            f"<b>{tr('rules', 'Rules')}:</b> ICE/TC/MGU-H={PU_LIMITS['ICE']}, MGU-K/ES/CE={PU_LIMITS['MGU-K']}"
        )
        rules_label.setStyleSheet("color: #666;")
        header_layout.addWidget(rules_label)
        
        header_layout.addStretch()
        
        # 篩選
        filter_label = QLabel(tr('filter', 'Filter') + ":")
        header_layout.addWidget(filter_label)
        
        self._filter_combo = QComboBox()
        self._filter_combo.addItems([
            tr('all', 'All'),
            tr('exceeded_only', 'Exceeded Only'),
            tr('at_limit_only', 'At Limit Only'),
            tr('normal_only', 'Normal Only')
        ])
        self._filter_combo.setFixedWidth(150)
        header_layout.addWidget(self._filter_combo)
        
        layout.addWidget(header_frame)
    
    def _create_table_panel(self) -> QWidget:
        """創建左側表格面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 表格
        self._table = QTableWidget()
        self._table.setColumnCount(10)  # 新增 Team + Status 欄位
        self._table.setHorizontalHeaderLabels([
            "#",
            tr('driver', 'Driver'),
            tr('team', 'Team'),
            "ICE", "TC", "MGU-H", "MGU-K", "ES", "CE",
            tr('status', 'Status')
        ])
        
        # 表格屬性
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setSelectionMode(QTableWidget.SingleSelection)
        self._table.setSortingEnabled(True)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # 列寬設定
        header = self._table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Fixed)   # #
        header.setSectionResizeMode(1, QHeaderView.Stretch) # Driver
        header.setSectionResizeMode(2, QHeaderView.Stretch) # Team
        for i in range(3, 9):
            header.setSectionResizeMode(i, QHeaderView.Fixed)  # PU 元件
        header.setSectionResizeMode(9, QHeaderView.Fixed)  # Status 欄位
        
        self._table.setColumnWidth(0, 40)   # #
        for i in range(3, 9):
            self._table.setColumnWidth(i, 60)  # PU 元件欄位
        self._table.setColumnWidth(9, 90)  # Status 欄位
        
        layout.addWidget(self._table)
        return panel
    
    def _create_detail_panel(self) -> QWidget:
        """創建右側詳情面板"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameStyle(QFrame.NoFrame)
        
        self._detail_panel = QWidget()
        detail_layout = QVBoxLayout(self._detail_panel)
        detail_layout.setContentsMargins(10, 10, 10, 10)
        detail_layout.setSpacing(10)
        
        # 車手標題
        self._detail_title = QLabel(tr('select_driver', 'Select a driver to view details'))
        self._detail_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        self._detail_title.setAlignment(Qt.AlignCenter)
        detail_layout.addWidget(self._detail_title)
        
        # PU 詳情區域
        pu_group = QGroupBox(tr('pu_usage', 'PU Element Usage'))
        self._pu_layout = QVBoxLayout(pu_group)
        detail_layout.addWidget(pu_group)
        
        # 零件更換記錄區域
        parts_group = QGroupBox(tr('parts_changes', 'Parts Changes'))
        self._parts_layout = QVBoxLayout(parts_group)
        self._parts_list = QLabel(tr('no_data', 'No data'))
        self._parts_list.setWordWrap(True)
        self._parts_layout.addWidget(self._parts_list)
        detail_layout.addWidget(parts_group)
        
        # 總體狀態
        status_group = QGroupBox(tr('overall_status', 'Overall Status'))
        self._status_layout = QVBoxLayout(status_group)
        self._status_label = QLabel(tr('no_data', 'No data'))
        self._status_label.setStyleSheet("font-size: 14px;")
        self._status_layout.addWidget(self._status_label)
        detail_layout.addWidget(status_group)
        
        detail_layout.addStretch()
        
        scroll.setWidget(self._detail_panel)
        return scroll
    
    def _setup_footer(self, layout: QVBoxLayout):
        """設置底部統計區域"""
        footer_frame = QFrame()
        footer_frame.setFrameStyle(QFrame.StyledPanel)
        footer_frame.setFixedHeight(35)
        
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(10, 5, 10, 5)
        
        self._stats_label = QLabel(tr('loading', 'Loading...'))
        self._stats_label.setStyleSheet("font-weight: bold; color: #495057;")
        footer_layout.addWidget(self._stats_label)
        
        footer_layout.addStretch()
        
        layout.addWidget(footer_frame)
    
    def _setup_connections(self):
        """設置信號連接"""
        self._table.itemSelectionChanged.connect(self._on_table_selection_changed)
        self._filter_combo.currentIndexChanged.connect(self._on_filter_changed)
    
    def _on_table_selection_changed(self):
        """表格選擇變更"""
        selected_items = self._table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            driver_item = self._table.item(row, 1)
            if driver_item:
                driver_code = driver_item.text().split()[0]  # 取得車手代碼 (VER, NOR, etc.)
                self._current_driver = driver_code
                self._update_detail_panel(driver_code)
                self.driver_selected.emit(driver_code)
    
    def _on_filter_changed(self, index: int):
        """篩選變更"""
        self._populate_table()
    
    def update_data(self, data: Dict[str, Any]):
        """更新數據"""
        logger.info(f"[FIA_STATS_WIDGET] Updating data: keys={list(data.keys())}")
        
        self._data = data
        self._drivers_data = data.get("drivers", {})
        self._raw_parts_data = data.get("raw_parts_data", {})
        
        self._populate_table()
        self._update_statistics()
        
        # 清除詳情面板
        if self._table and self._table.rowCount() > 0:
            self._table.selectRow(0)
            self._on_table_selection_changed()
        else:
            self._detail_title.setText(tr('select_driver', 'Select a driver to view details'))
            self._clear_pu_bars()
            self._parts_list.setText(tr('no_data', 'No data'))
            self._status_label.setText(tr('no_data', 'No data'))
    
    def _populate_table(self):
        """填充表格"""
        self._table.setSortingEnabled(False)
        self._table.setRowCount(0)
        
        if not self._drivers_data:
            logger.warning("[FIA_STATS_WIDGET] No driver data to populate")
            return
        
        # 獲取篩選條件
        filter_index = self._filter_combo.currentIndex() if self._filter_combo else 0
        
        # 排序車手 (按車號)
        sorted_drivers = sorted(
            self._drivers_data.items(),
            key=lambda x: int(x[1].get("number", "999")) if str(x[1].get("number", "999")).isdigit() else 999
        )
        
        row = 0
        for driver_code, driver_info in sorted_drivers:
            # 過濾掉 Unknown 車手
            actual_driver_code = driver_info.get("code", "???")
            if actual_driver_code == "UNK" or driver_info.get("name", "") == "Unknown":
                continue
            
            # 計算車手狀態
            pu_data = driver_info.get("pu_elements", {})
            driver_status = self._get_driver_status(pu_data)
            
            # 篩選
            if filter_index == 1 and driver_status != "exceeded":
                continue
            elif filter_index == 2 and driver_status != "warning":
                continue
            elif filter_index == 3 and driver_status != "normal":
                continue
            
            self._table.insertRow(row)
            
            # 獲取車手顏色（車隊顏色）
            driver_color = self._get_driver_color(actual_driver_code)
            
            # 序號（帶車隊顏色）
            seq_item = self._create_colored_item(str(row + 1), driver_color)
            self._table.setItem(row, 0, seq_item)
            
            # 車手 (代碼 + 名稱)（帶車隊顏色）
            driver_name = driver_info.get("name", "Unknown")
            driver_text = f"{actual_driver_code} ({driver_name})"
            driver_item = self._create_colored_item(driver_text, driver_color)
            driver_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self._table.setItem(row, 1, driver_item)
            
            # 車隊（帶車隊顏色，使用多國語言翻譯）
            team_name = driver_info.get("team", "Unknown")
            team_translated = get_team_name_text(team_name)
            team_item = self._create_colored_item(team_translated, driver_color)
            team_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            team_item.setToolTip(team_translated)
            self._table.setItem(row, 2, team_item)
            
            # PU 元件欄位
            for col, element in enumerate(["ICE", "TC", "MGU-H", "MGU-K", "ES", "CE"], start=3):
                count = pu_data.get(element, 0)
                limit = PU_LIMITS.get(element, 4)
                element_status = self._get_element_status(count, limit)
                
                item = QTableWidgetItem(str(count))
                item.setTextAlignment(Qt.AlignCenter)
                
                # 設置顏色
                color = STATUS_COLORS.get(element_status, STATUS_COLORS["normal"])
                item.setForeground(QBrush(QColor(color)))
                
                # 超限加粗
                if element_status == "exceeded":
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                
                self._table.setItem(row, col, item)
            
            # 狀態欄位
            status_text, status_color = self._get_status_display(driver_status)
            status_item = QTableWidgetItem(status_text)
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QBrush(QColor(status_color)))
            font = status_item.font()
            font.setBold(True)
            status_item.setFont(font)
            self._table.setItem(row, 9, status_item)
            
            row += 1
        
        self._table.setSortingEnabled(True)
        logger.info(f"[FIA_STATS_WIDGET] Populated {row} drivers")
    
    def _update_detail_panel(self, driver_code: str):
        """更新詳情面板"""
        # 找到車手數據
        driver_data = None
        car_number = None
        for num, info in self._drivers_data.items():
            if info.get("code") == driver_code:
                driver_data = info
                car_number = num
                break
        
        if not driver_data:
            logger.warning(f"[FIA_STATS_WIDGET] Driver {driver_code} not found")
            return
        
        # 更新標題
        driver_name = driver_data.get("name", "Unknown")
        team = driver_data.get("team", "Unknown Team")
        self._detail_title.setText(f"{driver_name} ({driver_code})\n{team}")
        
        # 更新 PU 進度條
        self._update_pu_bars(driver_data.get("pu_elements", {}))
        
        # 更新零件更換記錄
        self._update_parts_list(car_number)
        
        # 更新總體狀態
        self._update_overall_status(driver_data.get("pu_elements", {}))
    
    def _update_pu_bars(self, pu_data: Dict[str, int]):
        """更新 PU 進度條"""
        # 清除舊的進度條
        self._clear_pu_bars()
        
        for element in ["ICE", "TC", "MGU-H", "MGU-K", "ES", "CE"]:
            count = pu_data.get(element, 0)
            limit = PU_LIMITS.get(element, 4)
            status = self._get_element_status(count, limit)
            color = STATUS_COLORS.get(status, STATUS_COLORS["normal"])
            
            # 創建行
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 2, 0, 2)
            
            # 元件名稱
            name_label = QLabel(f"{element}:")
            name_label.setFixedWidth(60)
            row_layout.addWidget(name_label)
            
            # 進度條
            progress = QProgressBar()
            progress.setMinimum(0)
            progress.setMaximum(limit)
            progress.setValue(min(count, limit))
            progress.setFormat(f"{count}/{limit}")
            progress.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    text-align: center;
                    background: #f0f0f0;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                    border-radius: 2px;
                }}
            """)
            row_layout.addWidget(progress, 1)
            
            # 狀態標籤
            status_label = QLabel(STATUS_SYMBOLS.get(status, ""))
            status_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            status_label.setFixedWidth(30)
            row_layout.addWidget(status_label)
            
            self._pu_layout.addWidget(row_widget)
    
    def _clear_pu_bars(self):
        """清除 PU 進度條"""
        while self._pu_layout.count():
            item = self._pu_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _update_parts_list(self, car_number: str):
        """更新零件更換記錄"""
        parts_data = self._raw_parts_data.get(car_number, [])
        
        if not parts_data:
            self._parts_list.setText(tr('no_parts_changes', 'No parts changes recorded'))
            return
        
        # 格式化零件列表
        parts_text = ""
        for race_name, parts in parts_data:
            parts_str = ", ".join(parts) if isinstance(parts, list) else str(parts)
            parts_text += f"<b>{race_name}:</b> {parts_str}<br>"
        
        if parts_text:
            total = sum(len(p) if isinstance(p, list) else 1 for _, p in parts_data)
            parts_text = f"<b>{tr('total_changes', 'Total')}: {total}</b><br><br>" + parts_text
        
        self._parts_list.setText(parts_text)
    
    def _update_overall_status(self, pu_data: Dict[str, int]):
        """更新總體狀態"""
        exceeded = []
        at_limit = []
        
        for element in ["ICE", "TC", "MGU-H", "MGU-K", "ES", "CE"]:
            count = pu_data.get(element, 0)
            limit = PU_LIMITS.get(element, 4)
            
            if count > limit:
                exceeded.append(element)
            elif count == limit:
                at_limit.append(element)
        
        if exceeded:
            status_text = f"<span style='color:{STATUS_COLORS['exceeded']}'><b>{STATUS_SYMBOLS['exceeded']} {tr('exceeded', 'EXCEEDED')}</b></span><br>"
            status_text += f"{tr('exceeded_elements', 'Exceeded')}: {', '.join(exceeded)}"
            
            # 計算罰退格數 (每超限一個 = 10 格)
            penalty = len(exceeded) * 10
            status_text += f"<br>{tr('estimated_penalty', 'Estimated Penalty')}: {penalty} {tr('grid_positions', 'grid positions')}"
        elif at_limit:
            status_text = f"<span style='color:{STATUS_COLORS['warning']}'><b>{STATUS_SYMBOLS['warning']} {tr('at_limit', 'AT LIMIT')}</b></span><br>"
            status_text += f"{tr('at_limit_elements', 'At Limit')}: {', '.join(at_limit)}"
        else:
            status_text = f"<span style='color:{STATUS_COLORS['normal']}'><b>{STATUS_SYMBOLS['normal']} {tr('normal', 'NORMAL')}</b></span><br>"
            status_text += tr('all_within_limit', 'All elements within limit')
        
        self._status_label.setText(status_text)
    
    def _update_statistics(self):
        """更新統計摘要"""
        if not self._drivers_data:
            self._stats_label.setText(tr('no_data', 'No data'))
            return
        
        total = len(self._drivers_data)
        normal_count = 0
        warning_count = 0
        exceeded_count = 0
        
        for driver_info in self._drivers_data.values():
            pu_data = driver_info.get("pu_elements", {})
            status = self._get_driver_status(pu_data)
            
            if status == "normal":
                normal_count += 1
            elif status == "warning":
                warning_count += 1
            else:
                exceeded_count += 1
        
        stats_text = (
            f"{tr('total', 'Total')}: {total} | "
            f"<span style='color:{STATUS_COLORS['normal']}'>{STATUS_SYMBOLS['normal']} {normal_count}</span> | "
            f"<span style='color:{STATUS_COLORS['warning']}'>{STATUS_SYMBOLS['warning']} {warning_count}</span> | "
            f"<span style='color:{STATUS_COLORS['exceeded']}'>{STATUS_SYMBOLS['exceeded']} {exceeded_count}</span>"
        )
        self._stats_label.setText(stats_text)
    
    def _get_element_status(self, count: int, limit: int) -> str:
        """獲取元件狀態"""
        if count > limit:
            return "exceeded"
        elif count == limit:
            return "warning"
        else:
            return "normal"
    
    def _get_driver_status(self, pu_data: Dict[str, int]) -> str:
        """獲取車手總體狀態 (任一超限即為 exceeded)"""
        for element in ["ICE", "TC", "MGU-H", "MGU-K", "ES", "CE"]:
            count = pu_data.get(element, 0)
            limit = PU_LIMITS.get(element, 4)
            
            if count > limit:
                return "exceeded"
        
        for element in ["ICE", "TC", "MGU-H", "MGU-K", "ES", "CE"]:
            count = pu_data.get(element, 0)
            limit = PU_LIMITS.get(element, 4)
            
            if count == limit:
                return "warning"
        
        return "normal"
    
    def _get_driver_color(self, driver_code: str) -> QColor:
        """
        獲取車手顏色（使用通用顏色系統）
        
        Args:
            driver_code: 車手代碼（例如: "VER", "HAM"）
            
        Returns:
            QColor: 車手顏色
        """
        return color_palette_provider.get_driver_color(driver_code, fallback=True)
    
    def _create_colored_item(self, text: str, bg_color: QColor) -> QTableWidgetItem:
        """
        創建帶背景色的表格項目，自動選擇文字顏色
        
        Args:
            text: 顯示文字
            bg_color: 背景顏色
            
        Returns:
            QTableWidgetItem: 帶顏色的表格項目
        """
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setBackground(QBrush(bg_color))
        
        # 根據背景色亮度決定文字顏色
        luminance = (0.299 * bg_color.red() + 0.587 * bg_color.green() + 0.114 * bg_color.blue())
        text_color = QColor(255, 255, 255) if luminance < 128 else QColor(0, 0, 0)
        item.setForeground(QBrush(text_color))
        item.setTextAlignment(Qt.AlignCenter)
        return item
    
    def _get_status_display(self, status: str) -> tuple:
        """
        獲取狀態顯示文字和顏色
        
        Args:
            status: 狀態字串 ("normal", "warning", "exceeded")
            
        Returns:
            tuple: (顯示文字, 狀態顏色)
        """
        if status == "exceeded":
            return (tr("exceeded", "EXCEEDED"), STATUS_COLORS["exceeded"])
        elif status == "warning":
            return (tr("at_limit", "AT LIMIT"), STATUS_COLORS["warning"])
        else:
            return (tr("normal", "NORMAL"), STATUS_COLORS["normal"])
    
    def clear_data(self):
        """清除數據"""
        self._data = {}
        self._drivers_data = {}
        self._raw_parts_data = {}
        self._current_driver = None
        
        self._table.setRowCount(0)
        self._detail_title.setText(tr('select_driver', 'Select a driver to view details'))
        self._clear_pu_bars()
        self._parts_list.setText(tr('no_data', 'No data'))
        self._status_label.setText(tr('no_data', 'No data'))
        self._stats_label.setText(tr('no_data', 'No data'))


# =============================================================================
# 測試程式
# =============================================================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 測試數據
    test_data = {
        "year": 2025,
        "drivers": {
            "1": {
                "code": "VER",
                "name": "Max Verstappen",
                "team": "Red Bull Racing",
                "pu": {"ICE": 3, "TC": 3, "MGU-H": 3, "MGU-K": 3, "ES": 2, "CE": 2}
            },
            "4": {
                "code": "NOR",
                "name": "Lando Norris",
                "team": "McLaren",
                "pu": {"ICE": 4, "TC": 4, "MGU-H": 4, "MGU-K": 3, "ES": 2, "CE": 3}
            },
            "16": {
                "code": "LEC",
                "name": "Charles Leclerc",
                "team": "Ferrari",
                "pu": {"ICE": 5, "TC": 4, "MGU-H": 4, "MGU-K": 4, "ES": 3, "CE": 3}
            },
        },
        "raw_parts_data": {
            "16": [
                ("Abu Dhabi", ["Front Wing", "Floor"]),
                ("Singapore", ["Rear Wing"]),
            ]
        }
    }
    
    widget = FiaSeasonStatsWidget()
    widget.setWindowTitle("FIA Season Stats Widget - Test")
    widget.resize(1000, 600)
    widget.update_data(test_data)
    widget.show()
    
    sys.exit(app.exec_())
