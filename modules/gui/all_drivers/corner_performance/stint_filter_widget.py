#!/usr/bin/env python3
"""
Stint 篩選器 Widget
Stint Filter Widget for Corner Performance Analysis

提供 Stint 選擇的 TreeWidget，支援按車手/Stint 分層篩選
仿照 Long Run Analysis 的 Stint 選擇器設計

作者: F1T Team
日期: 2025-10-11
版本: 1.0.0
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import (
    QCheckBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.gui_i18n import tr
from core.logger import get_logger

logger = get_logger(component="gui")


class StintFilterWidget(QWidget):
    """
    Stint 篩選器 Widget
    
    提供 QTreeWidget 進行 Stint 選擇，支援：
    - 按車手/Stint 分層顯示
    - Compound 顏色編碼
    - 勾選框進行批量選擇
    - 發射篩選變更信號
    
    Signals:
        filter_changed: 篩選條件變更時發射
            payload: Dict[str, List[int]] - {driver: [stint_ids...]}
        selection_changed: 選擇變更時發射（包含完整狀態）
            payload: Dict[str, Any] - 完整的選擇狀態
    """
    
    # 信號定義
    filter_changed = pyqtSignal(dict)  # {driver: [stint_ids...]}
    selection_changed = pyqtSignal(dict)  # 完整選擇狀態
    
    def __init__(self, parent: Optional[QWidget] = None):
        """
        初始化 Stint 篩選器
        
        Args:
            parent: 父級 Widget
        """
        super().__init__(parent)
        
        # 狀態變數
        self._stints_data: Dict[str, List[Dict]] = {}  # {driver: [stint...]}
        self._selected_stints: Dict[str, Set[int]] = {}  # {driver: {stint_ids...}}
        self._driver_items: Dict[str, QTreeWidgetItem] = {}  # {driver: item}
        
        # 初始化 UI
        self._init_ui()
        
        logger.debug("[STINT_FILTER] Widget 初始化完成")
    
    def _init_ui(self):
        """初始化 UI 組件"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        
        # 標題
        title_label = QLabel(tr("stint_filter_title", "Stint Filter"))
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        layout.addWidget(title_label)
        
        # 控制按鈕區
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(0, 0, 0, 0)
        
        # 全選按鈕
        self.select_all_btn = QPushButton(tr("stint_select_all", "Select All"))
        self.select_all_btn.clicked.connect(self._on_select_all)
        control_layout.addWidget(self.select_all_btn)
        
        # 取消全選按鈕
        self.deselect_all_btn = QPushButton(tr("stint_deselect_all", "Deselect All"))
        self.deselect_all_btn.clicked.connect(self._on_deselect_all)
        control_layout.addWidget(self.deselect_all_btn)
        
        # Long Run Only 複選框
        self.long_run_only_cb = QCheckBox(tr("stint_long_run_only", "Long Run Only"))
        self.long_run_only_cb.setToolTip(tr("stint_long_run_only_tip", 
            "Only show stints classified as Long Run (>=4 consecutive laps)"))
        self.long_run_only_cb.stateChanged.connect(self._on_long_run_filter_changed)
        control_layout.addWidget(self.long_run_only_cb)
        
        control_layout.addStretch()
        layout.addWidget(control_frame)
        
        # Stint TreeWidget
        self.stint_tree = QTreeWidget()
        self.stint_tree.setColumnCount(5)
        self.stint_tree.setHeaderLabels([
            tr("stint_col_driver_stint", "Driver / Stint"),
            tr("stint_col_laps", "Laps"),
            tr("stint_col_compound", "Compound"),
            tr("stint_col_type", "Type"),
            tr("stint_col_corners", "Corners")
        ])
        self.stint_tree.setAlternatingRowColors(True)
        self.stint_tree.setRootIsDecorated(True)
        self.stint_tree.itemChanged.connect(self._on_item_changed)
        
        # 設置列寬
        header = self.stint_tree.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        layout.addWidget(self.stint_tree, 1)
        
        # 佔位符（無資料時顯示）
        self.placeholder_label = QLabel(tr("stint_placeholder", 
            "Stint filter will be available after data loads"))
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.placeholder_label)
        
        # 初始狀態：顯示佔位符，隱藏 TreeWidget
        self.stint_tree.hide()
    
    def _get_driver_color(self, driver_code: str) -> str:
        """
        獲取車手顏色
        
        Args:
            driver_code: 車手代碼
            
        Returns:
            str: 十六進制顏色碼
        """
        try:
            from modules.gui.themes import color_palette_provider
            color = color_palette_provider.get_driver_color(driver_code, format='hex')
            return color if color else '#CCCCCC'
        except Exception:
            return '#CCCCCC'
    
    def _get_compound_color(self, compound: str) -> QColor:
        """
        獲取 Compound 顏色
        
        Args:
            compound: Compound 名稱（SOFT/MEDIUM/HARD）
            
        Returns:
            QColor: 對應顏色
        """
        compound_upper = compound.upper() if compound else ""
        if compound_upper == "SOFT":
            return QColor(255, 100, 100)  # 紅色
        elif compound_upper == "MEDIUM":
            return QColor(255, 255, 100)  # 黃色
        elif compound_upper == "HARD":
            return QColor(255, 255, 255)  # 白色
        else:
            return QColor(200, 200, 200)  # 灰色
    
    def populate_stints(self, stints_data: Dict[str, List[Dict]], stints_available: bool = True):
        """
        填充 Stint TreeWidget
        
        Args:
            stints_data: {driver: [stint_info...]} 格式的 Stint 資料
            stints_available: Stint 資料是否可用
        """
        logger.debug(f"[STINT_FILTER] 填充 Stint 資料: {len(stints_data)} 位車手")
        
        # 暫時阻斷信號
        self.stint_tree.blockSignals(True)
        
        try:
            # 清空現有資料
            self.stint_tree.clear()
            self._stints_data = stints_data
            self._selected_stints = {}
            self._driver_items = {}
            
            if not stints_available or not stints_data:
                # 無 Stint 資料時顯示佔位符
                self.stint_tree.hide()
                self.placeholder_label.show()
                self.placeholder_label.setText(tr("stint_not_available", 
                    "Stint data not available for this session"))
                return
            
            # 隱藏佔位符，顯示 TreeWidget
            self.placeholder_label.hide()
            self.stint_tree.show()
            
            # 處理每個車手
            for driver_code, driver_stints in sorted(stints_data.items()):
                if not driver_stints:
                    continue
                
                # 初始化選擇集合（預設全選）
                self._selected_stints[driver_code] = set()
                
                # 獲取車手顏色
                driver_color = self._get_driver_color(driver_code)
                
                # 創建車手項目（父級）
                driver_item = QTreeWidgetItem()
                driver_item.setText(0, driver_code)
                driver_item.setData(0, Qt.UserRole, {
                    "type": "driver",
                    "code": driver_code
                })
                driver_item.setCheckState(0, Qt.Checked)
                
                # 設置車手背景色
                color = QColor(driver_color)
                color.setAlpha(60)
                driver_item.setBackground(0, QBrush(color))
                
                # 統計 Stint 資訊
                long_run_count = sum(1 for s in driver_stints if s.get("type") == "long_run")
                driver_item.setText(3, f"{long_run_count} Long Runs")
                
                # 記錄車手項目
                self._driver_items[driver_code] = driver_item
                
                # 創建 Stint 子項目
                for stint_info in driver_stints:
                    stint_id = stint_info.get("stint_id", 0)
                    compound = stint_info.get("compound", "UNKNOWN")
                    lap_range = stint_info.get("lap_range", [0, 0])
                    lap_count = stint_info.get("lap_count", 0)
                    stint_type = stint_info.get("type", "unknown")
                    corners = stint_info.get("corners", {})
                    
                    # 創建 Stint 項目
                    stint_item = QTreeWidgetItem(driver_item)
                    stint_item.setData(0, Qt.UserRole, {
                        "type": "stint",
                        "driver": driver_code,
                        "stint_id": stint_id,
                        "stint_info": stint_info
                    })
                    
                    # Stint 名稱
                    stint_item.setText(0, f"Stint {stint_id}")
                    
                    # 預設勾選
                    stint_item.setCheckState(0, Qt.Checked)
                    self._selected_stints[driver_code].add(stint_id)
                    
                    # Laps 範圍
                    if lap_range and len(lap_range) >= 2:
                        stint_item.setText(1, f"Lap {lap_range[0]}-{lap_range[1]} ({lap_count})")
                    else:
                        stint_item.setText(1, f"{lap_count} laps")
                    
                    # Compound（帶顏色）
                    stint_item.setText(2, compound)
                    compound_color = self._get_compound_color(compound)
                    stint_item.setBackground(2, QBrush(compound_color))
                    
                    # Type（顯示類型）
                    type_display = "Long Run" if stint_type == "long_run" else "Quali Sim"
                    stint_item.setText(3, type_display)
                    
                    # Corners 數量
                    corners_count = len(corners) if isinstance(corners, dict) else 0
                    stint_item.setText(4, f"{corners_count} corners" if corners_count > 0 else "-")
                
                # 添加到 TreeWidget
                self.stint_tree.addTopLevelItem(driver_item)
                driver_item.setExpanded(True)
            
            logger.debug(f"[STINT_FILTER] Stint TreeWidget 填充完成")
            
        finally:
            # 恢復信號
            self.stint_tree.blockSignals(False)
    
    def _on_item_changed(self, item: QTreeWidgetItem, column: int):
        """
        處理項目變更事件（勾選框狀態變更）
        
        Args:
            item: 變更的項目
            column: 變更的列
        """
        if column != 0:  # 只處理第一列（勾選框）
            return
        
        item_data = item.data(0, Qt.UserRole)
        if not item_data:
            return
        
        item_type = item_data.get("type")
        
        # 暫時阻斷信號以避免遞迴
        self.stint_tree.blockSignals(True)
        
        try:
            if item_type == "driver":
                # 車手項目變更 → 同步子項目
                driver_code = item_data.get("code")
                check_state = item.checkState(0)
                
                for i in range(item.childCount()):
                    child = item.child(i)
                    child.setCheckState(0, check_state)
                    
                    # 更新選擇集合
                    child_data = child.data(0, Qt.UserRole)
                    if child_data and child_data.get("type") == "stint":
                        stint_id = child_data.get("stint_id")
                        if check_state == Qt.Checked:
                            self._selected_stints.setdefault(driver_code, set()).add(stint_id)
                        else:
                            self._selected_stints.get(driver_code, set()).discard(stint_id)
                
            elif item_type == "stint":
                # Stint 項目變更
                driver_code = item_data.get("driver")
                stint_id = item_data.get("stint_id")
                check_state = item.checkState(0)
                
                # 更新選擇集合
                if check_state == Qt.Checked:
                    self._selected_stints.setdefault(driver_code, set()).add(stint_id)
                else:
                    self._selected_stints.get(driver_code, set()).discard(stint_id)
                
                # 更新父級（車手）勾選狀態
                parent = item.parent()
                if parent:
                    self._update_parent_check_state(parent)
                    
        finally:
            # 恢復信號
            self.stint_tree.blockSignals(False)
        
        # 發射篩選變更信號
        self._emit_filter_changed()
    
    def _update_parent_check_state(self, parent: QTreeWidgetItem):
        """
        更新父級項目的勾選狀態（根據子項目狀態）
        
        Args:
            parent: 父級項目
        """
        checked_count = 0
        total_count = parent.childCount()
        
        for i in range(total_count):
            if parent.child(i).checkState(0) == Qt.Checked:
                checked_count += 1
        
        if checked_count == 0:
            parent.setCheckState(0, Qt.Unchecked)
        elif checked_count == total_count:
            parent.setCheckState(0, Qt.Checked)
        else:
            parent.setCheckState(0, Qt.PartiallyChecked)
    
    def _on_select_all(self):
        """全選所有 Stint"""
        self.stint_tree.blockSignals(True)
        try:
            for i in range(self.stint_tree.topLevelItemCount()):
                driver_item = self.stint_tree.topLevelItem(i)
                driver_item.setCheckState(0, Qt.Checked)
                
                driver_data = driver_item.data(0, Qt.UserRole)
                driver_code = driver_data.get("code") if driver_data else None
                
                for j in range(driver_item.childCount()):
                    stint_item = driver_item.child(j)
                    stint_item.setCheckState(0, Qt.Checked)
                    
                    if driver_code:
                        stint_data = stint_item.data(0, Qt.UserRole)
                        if stint_data:
                            stint_id = stint_data.get("stint_id")
                            self._selected_stints.setdefault(driver_code, set()).add(stint_id)
        finally:
            self.stint_tree.blockSignals(False)
        
        self._emit_filter_changed()
    
    def _on_deselect_all(self):
        """取消全選"""
        self.stint_tree.blockSignals(True)
        try:
            for i in range(self.stint_tree.topLevelItemCount()):
                driver_item = self.stint_tree.topLevelItem(i)
                driver_item.setCheckState(0, Qt.Unchecked)
                
                driver_data = driver_item.data(0, Qt.UserRole)
                driver_code = driver_data.get("code") if driver_data else None
                
                for j in range(driver_item.childCount()):
                    stint_item = driver_item.child(j)
                    stint_item.setCheckState(0, Qt.Unchecked)
                
                if driver_code:
                    self._selected_stints[driver_code] = set()
        finally:
            self.stint_tree.blockSignals(False)
        
        self._emit_filter_changed()
    
    def _on_long_run_filter_changed(self, state: int):
        """
        Long Run Only 篩選器變更
        
        Args:
            state: Qt.Checked or Qt.Unchecked
        """
        long_run_only = state == Qt.Checked
        
        self.stint_tree.blockSignals(True)
        try:
            for i in range(self.stint_tree.topLevelItemCount()):
                driver_item = self.stint_tree.topLevelItem(i)
                driver_data = driver_item.data(0, Qt.UserRole)
                driver_code = driver_data.get("code") if driver_data else None
                
                for j in range(driver_item.childCount()):
                    stint_item = driver_item.child(j)
                    stint_data = stint_item.data(0, Qt.UserRole)
                    
                    if stint_data and stint_data.get("type") == "stint":
                        stint_info = stint_data.get("stint_info", {})
                        is_long_run = stint_info.get("type") == "long_run"
                        
                        if long_run_only:
                            # 只顯示 Long Run
                            if is_long_run:
                                stint_item.setCheckState(0, Qt.Checked)
                                if driver_code:
                                    self._selected_stints.setdefault(driver_code, set()).add(
                                        stint_data.get("stint_id")
                                    )
                            else:
                                stint_item.setCheckState(0, Qt.Unchecked)
                                if driver_code:
                                    self._selected_stints.get(driver_code, set()).discard(
                                        stint_data.get("stint_id")
                                    )
                
                # 更新父級狀態
                self._update_parent_check_state(driver_item)
        finally:
            self.stint_tree.blockSignals(False)
        
        self._emit_filter_changed()
    
    def _emit_filter_changed(self):
        """發射篩選變更信號"""
        # 轉換為 {driver: [stint_ids...]} 格式
        filter_result = {
            driver: list(stint_ids)
            for driver, stint_ids in self._selected_stints.items()
            if stint_ids  # 只包含有選擇的車手
        }
        
        logger.debug(f"[STINT_FILTER] 篩選變更: {len(filter_result)} 位車手被選中")
        
        self.filter_changed.emit(filter_result)
        
        # 同時發射完整狀態
        self.selection_changed.emit({
            "selected_stints": filter_result,
            "total_drivers": len(self._stints_data),
            "selected_drivers": len(filter_result),
            "stints_available": bool(self._stints_data)
        })
    
    def get_selected_stints(self) -> Dict[str, List[int]]:
        """
        獲取當前選擇的 Stint
        
        Returns:
            Dict[str, List[int]]: {driver: [stint_ids...]}
        """
        return {
            driver: list(stint_ids)
            for driver, stint_ids in self._selected_stints.items()
            if stint_ids
        }
    
    def is_stint_selected(self, driver: str, stint_id: int) -> bool:
        """
        檢查特定 Stint 是否被選中
        
        Args:
            driver: 車手代碼
            stint_id: Stint ID
            
        Returns:
            bool: 是否被選中
        """
        return stint_id in self._selected_stints.get(driver, set())
    
    def clear(self):
        """清空篩選器"""
        self.stint_tree.clear()
        self._stints_data = {}
        self._selected_stints = {}
        self._driver_items = {}
        self.stint_tree.hide()
        self.placeholder_label.show()
        self.placeholder_label.setText(tr("stint_placeholder", 
            "Stint filter will be available after data loads"))
