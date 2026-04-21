#!/usr/bin/env python3
"""
UniversalStintSelector - 通用 Stint 選擇器組件

提供可重用的 Stint 偵測與選擇功能，支援：
- 自動偵測 Stint（基於進站標記）
- 樹狀結構顯示（按車手分組）
- 合併/分組模式切換
- 可被 LapTimeBoxPlot、ThrottleBoxPlot 等模組共用

數據來源：Function 28 API (detailed_laptime_analysis)
判斷標準：smart_markers.pit_stop_detection.is_pit_lap = True

Author: F1T Team
Date: 2026-01-12
Version: 1.0.0
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QCheckBox, QGroupBox, QHeaderView,
    QAbstractItemView, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QBrush

from core.gui_i18n import tr
from core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class StintInfo:
    """Stint 資訊數據類"""
    driver: str
    stint_number: int
    start_lap: int
    end_lap: int
    lap_count: int
    compound: str
    lap_times: List[float] = field(default_factory=list)
    avg_time: float = 0.0
    selected: bool = True
    
    def get_display_text(self) -> str:
        """獲取顯示文字"""
        return f"Stint {self.stint_number} (Lap {self.start_lap}-{self.end_lap}, {self.compound}, {self.lap_count} laps)"


class UniversalStintSelector(QWidget):
    """
    通用 Stint 選擇器組件
    
    Signals:
        selection_changed: 當選擇的 Stint 變更時發射，攜帶選中的 Stint 列表
        merge_mode_changed: 當合併模式切換時發射，攜帶是否合併的布林值
    """
    
    # 信號定義
    selection_changed = pyqtSignal(list)  # List[StintInfo]
    merge_mode_changed = pyqtSignal(bool)  # is_merge_mode
    
    def __init__(self, parent=None, module_id: str = None):
        super().__init__(parent)
        
        # 數據存儲
        self._raw_data: Optional[Dict[str, Any]] = None
        self._driver_stints: Dict[str, List[StintInfo]] = {}  # driver -> List[StintInfo]
        self._all_stints: List[StintInfo] = []
        
        # 狀態
        self._is_merge_mode = True  # 預設合併模式（每個車手一個 Box）
        self._block_signals = False  # 用於暫時阻止信號發射
        
        # Global Sync 狀態 (V0.15.1)
        self._global_sync_enabled = False  # 預設關閉，由 Linkage 按鈕控制
        self._module_id = module_id or f"stint_selector_{id(self)}"
        self._session_year: Optional[str] = None
        self._session_race: Optional[str] = None
        self._session_name: Optional[str] = None
        self._is_applying_external = False  # 防止迴圈更新
        
        # 連接全局同步信號
        self._connect_global_sync()
        
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        """設置 UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # 頂部控制區域（單行）
        control_layout = QHBoxLayout()
        control_layout.setSpacing(8)
        
        # ===== 1. 合併模式 CheckBox =====
        self.merge_mode_cb = QCheckBox(tr("stint.merge_mode", "Merge Mode (One Box per Driver)"))
        self.merge_mode_cb.setChecked(True)  # 預設勾選（合併模式）
        self.merge_mode_cb.setToolTip(tr("stint.merge_mode_tooltip", 
            "When checked, all selected stints for each driver are merged into one box.\n"
            "When unchecked, each stint is shown as a separate box."))
        self.merge_mode_cb.stateChanged.connect(self._on_merge_mode_changed)
        control_layout.addWidget(self.merge_mode_cb)
        
        # 分隔線
        control_layout.addWidget(self._create_separator())
        
        # ===== 2. 快速選擇按鈕（初期/中期/後期）=====
        self.early_btn = QPushButton(tr("stint.early", "Early"))
        self.early_btn.setToolTip(tr("stint.early_tooltip", "Select stints covering Lap 1 to 1/3 of race"))
        self.early_btn.setFixedWidth(60)
        self.early_btn.clicked.connect(lambda: self._on_phase_select('early'))
        control_layout.addWidget(self.early_btn)
        
        self.mid_btn = QPushButton(tr("stint.mid", "Mid"))
        self.mid_btn.setToolTip(tr("stint.mid_tooltip", "Select stints covering 1/3 to 2/3 of race"))
        self.mid_btn.setFixedWidth(60)
        self.mid_btn.clicked.connect(lambda: self._on_phase_select('mid'))
        control_layout.addWidget(self.mid_btn)
        
        self.late_btn = QPushButton(tr("stint.late", "Late"))
        self.late_btn.setToolTip(tr("stint.late_tooltip", "Select stints covering 2/3 to end of race"))
        self.late_btn.setFixedWidth(60)
        self.late_btn.clicked.connect(lambda: self._on_phase_select('late'))
        control_layout.addWidget(self.late_btn)
        
        # 分隔線
        control_layout.addWidget(self._create_separator())
        
        # ===== 3. 輪胎選擇 CheckBox =====
        self.tire_soft_cb = QCheckBox("SOFT")
        self.tire_soft_cb.setStyleSheet("QCheckBox { color: #FF3333; font-weight: bold; }")
        self.tire_soft_cb.setChecked(True)
        self.tire_soft_cb.stateChanged.connect(self._on_tire_filter_changed)
        control_layout.addWidget(self.tire_soft_cb)
        
        self.tire_medium_cb = QCheckBox("MEDIUM")
        self.tire_medium_cb.setStyleSheet("QCheckBox { color: #FFCC00; font-weight: bold; }")
        self.tire_medium_cb.setChecked(True)
        self.tire_medium_cb.stateChanged.connect(self._on_tire_filter_changed)
        control_layout.addWidget(self.tire_medium_cb)
        
        self.tire_hard_cb = QCheckBox("HARD")
        self.tire_hard_cb.setStyleSheet("QCheckBox { color: #CCCCCC; font-weight: bold; }")
        self.tire_hard_cb.setChecked(True)
        self.tire_hard_cb.stateChanged.connect(self._on_tire_filter_changed)
        control_layout.addWidget(self.tire_hard_cb)
        
        # INTERMEDIATE checkbox (綠色)
        self.tire_intermediate_cb = QCheckBox("INTER")
        self.tire_intermediate_cb.setStyleSheet("QCheckBox { color: #33FF33; font-weight: bold; }")
        self.tire_intermediate_cb.setChecked(True)
        self.tire_intermediate_cb.stateChanged.connect(self._on_tire_filter_changed)
        control_layout.addWidget(self.tire_intermediate_cb)
        
        # WET checkbox (藍色)
        self.tire_wet_cb = QCheckBox("WET")
        self.tire_wet_cb.setStyleSheet("QCheckBox { color: #3399FF; font-weight: bold; }")
        self.tire_wet_cb.setChecked(True)
        self.tire_wet_cb.stateChanged.connect(self._on_tire_filter_changed)
        control_layout.addWidget(self.tire_wet_cb)
        
        # 分隔線
        control_layout.addWidget(self._create_separator())
        
        control_layout.addStretch()
        
        # ===== 4. 全選/取消全選按鈕 =====
        self.select_all_btn = QPushButton(tr("stint.select_all", "Select All"))
        self.select_all_btn.clicked.connect(self._on_select_all)
        control_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QPushButton(tr("stint.deselect_all", "Deselect All"))
        self.deselect_all_btn.clicked.connect(self._on_deselect_all)
        control_layout.addWidget(self.deselect_all_btn)
        
        layout.addLayout(control_layout)
        
        # Stint 樹狀結構
        stints_group = QGroupBox(tr("stint.detected_stints", "Detected Stints"))
        stints_layout = QVBoxLayout(stints_group)
        
        self.stint_tree = QTreeWidget()
        self.stint_tree.setHeaderLabels([
            tr("stint.col.driver", "Driver / Stint"),
            tr("stint.col.laps", "Lap Range"),
            tr("stint.col.compound", "Compound"),
            tr("stint.col.count", "Laps"),
            tr("stint.col.avg_time", "Avg Time"),
        ])
        
        # 表格設定
        self.stint_tree.setSelectionMode(QAbstractItemView.NoSelection)
        self.stint_tree.setAlternatingRowColors(True)
        self.stint_tree.setRootIsDecorated(True)
        self.stint_tree.setExpandsOnDoubleClick(True)
        
        # 設置列寬
        header = self.stint_tree.header()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        # 連接 checkbox 變更信號
        self.stint_tree.itemChanged.connect(self._on_item_changed)
        
        stints_layout.addWidget(self.stint_tree)
        
        # 說明文字
        legend_label = QLabel(tr("stint.legend", 
            "Stints are detected by pit stop markers. Check/uncheck to include in analysis."))
        legend_label.setStyleSheet("color: gray; font-style: italic; font-size: 11px;")
        legend_label.setWordWrap(True)
        stints_layout.addWidget(legend_label)
        
        layout.addWidget(stints_group, 1)
        
        # 統計資訊
        self.stats_label = QLabel(tr("stint.waiting", "Waiting for data..."))
        self.stats_label.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(self.stats_label)
    
    def _create_separator(self) -> QLabel:
        """創建分隔線"""
        sep = QLabel("|")
        sep.setStyleSheet("color: #ccc; font-size: 14px;")
        return sep
    
    def _get_total_laps(self) -> int:
        """獲取比賽總圈數"""
        max_lap = 0
        for stint in self._all_stints:
            if stint.end_lap > max_lap:
                max_lap = stint.end_lap
        return max_lap
    
    def _on_phase_select(self, phase: str) -> None:
        """處理快速選擇按鈕（初期/中期/後期）"""
        total_laps = self._get_total_laps()
        if total_laps == 0:
            return
        
        # 計算圈數範圍
        one_third = total_laps / 3
        
        if phase == 'early':
            lap_start, lap_end = 1, one_third
        elif phase == 'mid':
            lap_start, lap_end = one_third, one_third * 2
        else:  # late
            lap_start, lap_end = one_third * 2, total_laps
        
        logger.info(f"[STINT_SELECTOR] Phase select: {phase} (Lap {lap_start:.0f}-{lap_end:.0f})")
        
        # 獲取當前輪胎過濾條件
        allowed_compounds = self._get_allowed_compounds()
        
        # 選中符合條件的 Stint
        self._block_signals = True
        for stint in self._all_stints:
            # 檢查 Stint 是否在圈數範圍內（任何部分重疊即可）
            in_range = stint.start_lap <= lap_end and stint.end_lap >= lap_start
            # 檢查輪胎類型
            tire_ok = stint.compound.upper() in allowed_compounds
            
            stint.selected = in_range and tire_ok
        
        self._block_signals = False
        
        # 更新樹狀結構顯示
        self._update_tree_checkboxes()
        self._update_stats()
        self._emit_selection_changed()
    
    def _get_allowed_compounds(self) -> Set[str]:
        """獲取當前允許的輪胎類型"""
        allowed = set()
        if self.tire_soft_cb.isChecked():
            allowed.add('SOFT')
        if self.tire_medium_cb.isChecked():
            allowed.add('MEDIUM')
        if self.tire_hard_cb.isChecked():
            allowed.add('HARD')
        if hasattr(self, 'tire_intermediate_cb') and self.tire_intermediate_cb.isChecked():
            allowed.add('INTERMEDIATE')
        if hasattr(self, 'tire_wet_cb') and self.tire_wet_cb.isChecked():
            allowed.add('WET')
        return allowed
    
    def _on_tire_filter_changed(self) -> None:
        """處理輪胎過濾變更"""
        allowed_compounds = self._get_allowed_compounds()
        
        logger.info(f"[STINT_SELECTOR] Tire filter changed: {allowed_compounds}")
        
        # 更新 Stint 選中狀態
        self._block_signals = True
        for stint in self._all_stints:
            if stint.compound.upper() in allowed_compounds:
                stint.selected = True
            else:
                stint.selected = False
        
        self._block_signals = False
        
        # 更新樹狀結構顯示
        self._update_tree_checkboxes()
        self._update_stats()
        self._emit_selection_changed()
    
    def _update_tree_checkboxes(self) -> None:
        """更新樹狀結構中的 checkbox 狀態"""
        root = self.stint_tree.invisibleRootItem()
        for i in range(root.childCount()):
            driver_item = root.child(i)
            for j in range(driver_item.childCount()):
                stint_item = driver_item.child(j)
                item_data = stint_item.data(0, Qt.UserRole)
                if item_data and isinstance(item_data, dict):
                    stint_info = item_data.get('stint')
                    if stint_info and hasattr(stint_info, 'selected'):
                        stint_item.setCheckState(0, Qt.Checked if stint_info.selected else Qt.Unchecked)
            
            # 更新車手項目的 checkbox 狀態
            self._update_parent_check_state(driver_item)
        
    def set_data(self, data: Dict[str, Any]) -> None:
        """
        設置數據並自動偵測 Stint
        
        Args:
            data: API 返回的數據，應包含 all_drivers_detailed_laptime
        """
        self._raw_data = data
        self._detect_stints(data)
        self._populate_tree()
        self._update_stats()
        
        # 發射初始選擇狀態
        self._emit_selection_changed()
        
    def _detect_stints(self, data: Dict[str, Any]) -> None:
        """
        從數據中偵測 Stint
        
        使用進站標記 (is_pit_lap) 作為 Stint 切分點
        
        支援的數據格式：
        1. Function 28 (detailed_laptime_analysis): all_drivers_detailed_laptime
        2. Function 54 (throttle_ratio): analysis.drivers[]
        """
        self._driver_stints.clear()
        self._all_stints.clear()
        
        if not isinstance(data, dict):
            logger.warning("[STINT_SELECTOR] Invalid data format")
            return
        
        # 嘗試格式 1: Function 28 (all_drivers_detailed_laptime)
        all_drivers = data.get('all_drivers_detailed_laptime', {})
        if not all_drivers:
            # 嘗試從 data 包裝層提取
            if 'data' in data and isinstance(data['data'], dict):
                all_drivers = data['data'].get('all_drivers_detailed_laptime', {})
        
        if all_drivers:
            self._detect_stints_format_f28(all_drivers)
            return
        
        # 嘗試格式 2: Function 54 (analysis.drivers[])
        analysis = data.get('analysis', {})
        if not analysis and 'data' in data:
            analysis = data['data'].get('analysis', {})
        
        drivers_list = analysis.get('drivers', [])
        if drivers_list:
            self._detect_stints_format_f54(drivers_list)
            return
        
        # 嘗試格式 3: Function 120 (F120 corner_performance)
        # 格式: mode_a_unified.drivers[{driver, stints: [...]}]
        mode_a = data.get('mode_a_unified', {})
        if not mode_a and 'data' in data:
            mode_a = data['data'].get('mode_a_unified', {})
        
        f120_drivers = mode_a.get('drivers', [])
        if f120_drivers and data.get('stints_available', False):
            self._detect_stints_format_f120(f120_drivers)
            return
        
        logger.warning("[STINT_SELECTOR] No driver data found in any supported format")
    
    def _detect_stints_format_f28(self, all_drivers: Dict[str, Any]) -> None:
        """
        從 Function 28 格式數據中偵測 Stint
        
        格式: {driver_code: {detailed_lap_data: [...]}}
        """
        for driver_code, driver_data in all_drivers.items():
            if not isinstance(driver_data, dict):
                continue
                
            detailed_laps = driver_data.get('detailed_lap_data', [])
            if not isinstance(detailed_laps, list) or not detailed_laps:
                continue
                
            stints = self._detect_driver_stints(driver_code, detailed_laps)
            if stints:
                self._driver_stints[driver_code] = stints
                self._all_stints.extend(stints)
                
        logger.debug(f"[STINT_SELECTOR] F28 format: Detected {len(self._all_stints)} stints for {len(self._driver_stints)} drivers")
    
    def _detect_stints_format_f54(self, drivers_list: List[Dict]) -> None:
        """
        從 Function 54 格式數據中偵測 Stint
        
        格式: [{"driver_code": "VER", "laps": [...]}]
        """
        for driver_data in drivers_list:
            if not isinstance(driver_data, dict):
                continue
            
            driver_code = driver_data.get('driver_code', '')
            if not driver_code:
                continue
            
            laps = driver_data.get('laps', [])
            if not isinstance(laps, list) or not laps:
                continue
            
            # 轉換 F54 格式的圈數據為通用格式
            converted_laps = []
            for lap in laps:
                converted_lap = {
                    'lap_number': lap.get('lap_number', 0),
                    'lap_time_seconds': lap.get('lap_time_seconds'),
                    'tire_compound': lap.get('tire_compound', lap.get('compound', 'UNKNOWN')),
                    'smart_markers': lap.get('smart_markers', {}),
                    # F54 特有欄位，用於獲取油門百分比
                    'full_throttle_ratio': lap.get('full_throttle_ratio'),
                    'full_throttle_duration_s': lap.get('full_throttle_duration_s'),
                }
                converted_laps.append(converted_lap)
            
            stints = self._detect_driver_stints(driver_code, converted_laps)
            if stints:
                self._driver_stints[driver_code] = stints
                self._all_stints.extend(stints)
        
        logger.debug(f"[STINT_SELECTOR] F54 format: Detected {len(self._all_stints)} stints for {len(self._driver_stints)} drivers")
    
    def _detect_stints_format_f120(self, drivers_list: List[Dict]) -> None:
        """
        From Function 120 (corner_performance) format
        
        Format: [{"driver": "VER", "stints": [{stint_id, compound, lap_range, ...}]}]
        
        F120 already has pre-detected stint data, so we just need to convert it
        """
        for driver_data in drivers_list:
            if not isinstance(driver_data, dict):
                continue
            
            driver_code = driver_data.get('driver', '')
            if not driver_code:
                continue
            
            stints_raw = driver_data.get('stints', [])
            if not isinstance(stints_raw, list) or not stints_raw:
                continue
            
            driver_stints: List[StintInfo] = []
            
            for stint_raw in stints_raw:
                if not isinstance(stint_raw, dict):
                    continue
                
                stint_id = stint_raw.get('stint_id', 0)
                compound = stint_raw.get('compound', 'UNKNOWN')
                if compound:
                    compound = compound.upper()
                
                lap_range = stint_raw.get('lap_range', [0, 0])
                start_lap = lap_range[0] if len(lap_range) > 0 else 0
                end_lap = lap_range[1] if len(lap_range) > 1 else start_lap
                
                lap_count = stint_raw.get('lap_count', end_lap - start_lap + 1)
                stint_type = stint_raw.get('type', 'unknown')
                
                # Extract lap times from laps_detail if available
                lap_times = []
                laps_detail = stint_raw.get('laps_detail', [])
                for lap_info in laps_detail:
                    if isinstance(lap_info, dict):
                        lap_time = lap_info.get('lap_time_seconds')
                        if lap_time and lap_time > 0:
                            lap_times.append(float(lap_time))
                
                avg_time = sum(lap_times) / len(lap_times) if lap_times else 0.0
                
                stint_info = StintInfo(
                    driver=driver_code,
                    stint_number=stint_id,
                    start_lap=start_lap,
                    end_lap=end_lap,
                    lap_count=lap_count,
                    compound=compound,
                    lap_times=lap_times,
                    avg_time=avg_time,
                    selected=True
                )
                driver_stints.append(stint_info)
            
            if driver_stints:
                self._driver_stints[driver_code] = driver_stints
                self._all_stints.extend(driver_stints)
        
        logger.info(f"[STINT_SELECTOR] F120 format: Loaded {len(self._all_stints)} stints for {len(self._driver_stints)} drivers")
        
    def _detect_driver_stints(self, driver_code: str, laps: List[Dict]) -> List[StintInfo]:
        """
        偵測單一車手的 Stint
        
        判斷邏輯：
        1. 每當遇到 is_pit_lap=True 的圈，將其視為 Stint 結束點
        2. 下一圈開始新的 Stint
        """
        stints: List[StintInfo] = []
        current_stint_laps: List[Dict] = []
        current_compound: Optional[str] = None
        stint_counter = 1
        
        for i, lap in enumerate(laps):
            lap_number = lap.get('lap_number', i + 1)
            compound = lap.get('tire_compound', lap.get('compound', 'UNKNOWN'))
            if compound:
                compound = compound.upper()
            
            lap_time = lap.get('lap_time_seconds')
            if lap_time is None:
                # 嘗試解析字串格式
                lap_time_str = lap.get('lap_time', '')
                lap_time = self._parse_lap_time(lap_time_str)
            
            # 檢查是否為進站圈
            is_pit_lap = self._is_pit_lap(lap)
            
            # 添加到當前 Stint
            current_stint_laps.append({
                'lap_number': lap_number,
                'lap_time': lap_time,
                'compound': compound,
                'is_pit_lap': is_pit_lap
            })
            
            if current_compound is None:
                current_compound = compound
            
            # 如果是進站圈，結束當前 Stint
            if is_pit_lap:
                # 創建 Stint（不包含進站圈的圈速）
                stint = self._create_stint_info(
                    driver_code, stint_counter, current_stint_laps, current_compound
                )
                if stint:
                    stints.append(stint)
                    stint_counter += 1
                
                # 重置
                current_stint_laps = []
                current_compound = None
                
        # 處理最後一個 Stint（沒有以進站結束的）
        if current_stint_laps:
            stint = self._create_stint_info(
                driver_code, stint_counter, current_stint_laps, current_compound
            )
            if stint:
                stints.append(stint)
                
        return stints
        
    def _is_pit_lap(self, lap: Dict) -> bool:
        """檢查是否為進站圈"""
        smart_markers = lap.get('smart_markers', {})
        if isinstance(smart_markers, dict):
            pit_detection = smart_markers.get('pit_stop_detection', {})
            if isinstance(pit_detection, dict):
                return pit_detection.get('is_pit_lap', False)
        
        # 備用：檢查 pit_status 欄位
        pit_status = lap.get('pit_status', '')
        if pit_status and 'pit' in str(pit_status).lower():
            return True
            
        return False
        
    def _parse_lap_time(self, lap_time_str: str) -> Optional[float]:
        """解析圈速字串為秒數"""
        if not lap_time_str or lap_time_str == 'N/A':
            return None
            
        try:
            # 格式: "1:32.456" 或 "92.456"
            if ':' in str(lap_time_str):
                parts = str(lap_time_str).split(':')
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            else:
                return float(lap_time_str)
        except (ValueError, IndexError):
            return None
            
    def _create_stint_info(self, driver: str, stint_num: int, 
                           laps: List[Dict], compound: Optional[str]) -> Optional[StintInfo]:
        """創建 StintInfo 對象"""
        if not laps:
            return None
            
        # 過濾有效圈速（排除進站圈和無效值）
        valid_times = []
        valid_laps = []
        for lap in laps:
            if lap.get('is_pit_lap'):
                continue
            lap_time = lap.get('lap_time')
            if lap_time and lap_time > 0:
                valid_times.append(lap_time)
                valid_laps.append(lap.get('lap_number'))
                
        if not valid_laps:
            return None
            
        start_lap = min(valid_laps) if valid_laps else laps[0].get('lap_number', 1)
        end_lap = max(valid_laps) if valid_laps else laps[-1].get('lap_number', 1)
        
        avg_time = sum(valid_times) / len(valid_times) if valid_times else 0.0
        
        return StintInfo(
            driver=driver,
            stint_number=stint_num,
            start_lap=start_lap,
            end_lap=end_lap,
            lap_count=len(valid_times),
            compound=compound or 'UNKNOWN',
            lap_times=valid_times,
            avg_time=avg_time,
            selected=True  # 預設全選
        )
        
    def _populate_tree(self) -> None:
        """填充樹狀結構"""
        # 暫時斷開信號以避免重複觸發
        self.stint_tree.blockSignals(True)
        self.stint_tree.clear()
        
        # 按車手分組
        for driver_code in sorted(self._driver_stints.keys()):
            stints = self._driver_stints[driver_code]
            if not stints:
                continue
                
            # 創建車手父節點
            driver_item = QTreeWidgetItem()
            driver_item.setText(0, driver_code)
            driver_item.setData(0, Qt.UserRole, {'type': 'driver', 'code': driver_code})
            driver_item.setFlags(driver_item.flags() | Qt.ItemIsUserCheckable)
            
            # 判斷車手節點的選中狀態
            all_selected = all(s.selected for s in stints)
            none_selected = not any(s.selected for s in stints)
            
            if all_selected:
                driver_item.setCheckState(0, Qt.Checked)
            elif none_selected:
                driver_item.setCheckState(0, Qt.Unchecked)
            else:
                driver_item.setCheckState(0, Qt.PartiallyChecked)
            
            # 設置車手顏色背景
            driver_color = self._get_driver_color(driver_code)
            if driver_color:
                color = QColor(driver_color)
                color.setAlpha(60)
                driver_item.setBackground(0, QBrush(color))
            
            # 統計信息
            total_laps = sum(s.lap_count for s in stints)
            driver_item.setText(3, str(total_laps))
            
            # 添加 Stint 子節點
            for stint in stints:
                stint_item = QTreeWidgetItem(driver_item)
                stint_item.setData(0, Qt.UserRole, {
                    'type': 'stint',
                    'driver': driver_code,
                    'stint': stint
                })
                stint_item.setFlags(stint_item.flags() | Qt.ItemIsUserCheckable)
                stint_item.setCheckState(0, Qt.Checked if stint.selected else Qt.Unchecked)
                
                # 填充列
                stint_item.setText(0, f"Stint {stint.stint_number}")
                stint_item.setText(1, f"{stint.start_lap}-{stint.end_lap}")
                stint_item.setText(2, stint.compound)
                stint_item.setText(3, str(stint.lap_count))
                stint_item.setText(4, f"{stint.avg_time:.3f}s" if stint.avg_time > 0 else "-")
                
                # 輪胎顏色
                compound_color = self._get_compound_color(stint.compound)
                if compound_color:
                    stint_item.setBackground(2, QBrush(compound_color))
            
            self.stint_tree.addTopLevelItem(driver_item)
            driver_item.setExpanded(True)
        
        self.stint_tree.blockSignals(False)
        
    def _get_driver_color(self, driver_code: str) -> Optional[str]:
        """獲取車手顏色"""
        try:
            from modules.gui.themes import color_palette_provider
            color = color_palette_provider.get_driver_color(driver_code, format="hex")
            return color
        except Exception:
            return None
            
    def _get_compound_color(self, compound: str) -> Optional[QColor]:
        """獲取輪胎顏色"""
        compound_colors = {
            'SOFT': QColor(255, 100, 100, 180),
            'MEDIUM': QColor(255, 255, 100, 180),
            'HARD': QColor(255, 255, 255, 180),
            'INTERMEDIATE': QColor(100, 255, 100, 180),
            'WET': QColor(100, 100, 255, 180),
        }
        return compound_colors.get(compound.upper())
        
    def _update_stats(self) -> None:
        """更新統計標籤"""
        total_drivers = len(self._driver_stints)
        total_stints = len(self._all_stints)
        selected_stints = sum(1 for s in self._all_stints if s.selected)
        
        self.stats_label.setText(
            tr("stint.stats", "Drivers: {drivers} | Stints: {selected}/{total}").format(
                drivers=total_drivers,
                selected=selected_stints,
                total=total_stints
            )
        )
        
    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        """處理樹狀結構項目變更"""
        if column != 0:
            return
            
        data = item.data(0, Qt.UserRole)
        if not data:
            return
            
        item_type = data.get('type')
        check_state = item.checkState(0)
        is_checked = check_state == Qt.Checked
        
        if item_type == 'driver':
            # 車手節點：更新所有子 Stint
            driver_code = data.get('code')
            if driver_code in self._driver_stints:
                for stint in self._driver_stints[driver_code]:
                    stint.selected = is_checked
                    
            # 更新子節點 UI
            self.stint_tree.blockSignals(True)
            for i in range(item.childCount()):
                child = item.child(i)
                child.setCheckState(0, Qt.Checked if is_checked else Qt.Unchecked)
            self.stint_tree.blockSignals(False)
            
        elif item_type == 'stint':
            # Stint 節點：更新單個 Stint
            stint: StintInfo = data.get('stint')
            if stint:
                stint.selected = is_checked
                
            # 更新父節點狀態
            parent = item.parent()
            if parent:
                self._update_parent_check_state(parent)
                
        self._update_stats()
        self._emit_selection_changed()
        
    def _update_parent_check_state(self, parent_item: QTreeWidgetItem) -> None:
        """更新父節點的選中狀態"""
        child_count = parent_item.childCount()
        checked_count = 0
        
        for i in range(child_count):
            if parent_item.child(i).checkState(0) == Qt.Checked:
                checked_count += 1
                
        self.stint_tree.blockSignals(True)
        if checked_count == 0:
            parent_item.setCheckState(0, Qt.Unchecked)
        elif checked_count == child_count:
            parent_item.setCheckState(0, Qt.Checked)
        else:
            parent_item.setCheckState(0, Qt.PartiallyChecked)
        self.stint_tree.blockSignals(False)
        
    def _on_merge_mode_changed(self, state: int) -> None:
        """合併模式切換"""
        self._is_merge_mode = (state == Qt.Checked)
        self.merge_mode_changed.emit(self._is_merge_mode)
        self._emit_selection_changed()
        
    def _on_select_all(self) -> None:
        """全選所有 Stint"""
        for stint in self._all_stints:
            stint.selected = True
        self._populate_tree()
        self._update_stats()
        self._emit_selection_changed()
        
    def _on_deselect_all(self) -> None:
        """取消全選"""
        for stint in self._all_stints:
            stint.selected = False
        self._populate_tree()
        self._update_stats()
        self._emit_selection_changed()
        
    def _emit_selection_changed(self) -> None:
        """發射選擇變更信號"""
        if self._block_signals:
            return
        selected = [s for s in self._all_stints if s.selected]
        self.selection_changed.emit(selected)
        
        # V0.15.1: 觸發全局同步
        self._emit_global_sync()
        
    def get_selected_stints(self) -> List[StintInfo]:
        """獲取選中的 Stint 列表"""
        return [s for s in self._all_stints if s.selected]
        
    def get_selected_lap_times_by_driver(self) -> Dict[str, List[float]]:
        """
        獲取按車手分組的選中圈速
        
        Returns:
            Dict[str, List[float]]: driver_code -> lap_times
        """
        result: Dict[str, List[float]] = {}
        
        for stint in self._all_stints:
            if not stint.selected:
                continue
                
            if stint.driver not in result:
                result[stint.driver] = []
            result[stint.driver].extend(stint.lap_times)
            
        return result
        
    def get_lap_times_by_stint(self) -> Dict[str, Dict[int, List[float]]]:
        """
        獲取按車手和 Stint 分組的圈速
        
        Returns:
            Dict[str, Dict[int, List[float]]]: driver_code -> {stint_number -> lap_times}
        """
        result: Dict[str, Dict[int, List[float]]] = {}
        
        for stint in self._all_stints:
            if not stint.selected:
                continue
                
            if stint.driver not in result:
                result[stint.driver] = {}
            result[stint.driver][stint.stint_number] = stint.lap_times
            
        return result
        
    def is_merge_mode(self) -> bool:
        """是否為合併模式"""
        return self._is_merge_mode
        
    def get_all_drivers(self) -> List[str]:
        """獲取所有車手列表"""
        return list(self._driver_stints.keys())
        
    def get_driver_stints(self, driver: str) -> List[StintInfo]:
        """獲取指定車手的 Stint 列表"""
        return self._driver_stints.get(driver, [])
    
    # ========== Global Sync Methods (V0.15.1) ==========
    
    def _connect_global_sync(self) -> None:
        """連接全局同步信號"""
        try:
            from .global_chart_sync_signal import get_global_chart_sync
            sync = get_global_chart_sync()
            sync.stint_selection_changed.connect(self._on_global_stint_selection_changed)
            logger.debug(f"[STINT_SELECTOR] {self._module_id}: Global sync connected")
        except Exception as e:
            logger.warning(f"[STINT_SELECTOR] Failed to connect global sync: {e}")
    
    def set_session_info(self, year: str, race: str, session: str) -> None:
        """
        設置 Session 資訊（用於 Global Sync 過濾）
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 場次 (FP1, FP2, Q, R, etc.)
        """
        self._session_year = year
        self._session_race = race
        self._session_name = session
        logger.debug(f"[STINT_SELECTOR] {self._module_id}: Session set to {year} {race} {session}")
    
    def enable_global_sync(self, enabled: bool) -> None:
        """
        啟用或停用全局同步（由 Linkage 按鈕控制）
        
        Args:
            enabled: 是否啟用
        """
        self._global_sync_enabled = enabled
        logger.info(f"[STINT_SELECTOR] {self._module_id}: Global sync {'enabled' if enabled else 'disabled'}")
    
    def is_global_sync_enabled(self) -> bool:
        """是否啟用全局同步"""
        return self._global_sync_enabled
    
    def _on_global_stint_selection_changed(
        self,
        selected_stints_data: List[Dict[str, Any]],
        is_merge_mode: bool,
        year: str,
        race: str,
        session: str,
        source: str
    ) -> None:
        """
        處理來自其他模組的 Stint 選擇變更
        
        Args:
            selected_stints_data: 選中的 Stint 列表
            is_merge_mode: 是否為合併模式
            year, race, session: Session 資訊
            source: 信號來源模組
        """
        # 忽略自己發出的信號
        if source == self._module_id:
            return
        
        # 如果全局同步未啟用，忽略
        if not self._global_sync_enabled:
            return
        
        # 檢查 Session 是否匹配
        if (self._session_year != year or 
            self._session_race != race or 
            self._session_name != session):
            logger.debug(
                f"[STINT_SELECTOR] {self._module_id}: Ignoring sync from {source} "
                f"(session mismatch: {self._session_year}/{self._session_race}/{self._session_name} "
                f"vs {year}/{race}/{session})"
            )
            return
        
        # 應用外部選擇
        self.apply_external_selection(selected_stints_data, is_merge_mode)
    
    def apply_external_selection(
        self, 
        selected_stints_data: List[Dict[str, Any]], 
        is_merge_mode: bool
    ) -> None:
        """
        應用來自外部的 Stint 選擇（Global Sync 用）
        
        Args:
            selected_stints_data: 選中的 Stint 列表，格式:
                [{'driver': str, 'stint_number': int, ...}, ...]
            is_merge_mode: 是否為合併模式
        """
        if self._is_applying_external:
            return
        
        self._is_applying_external = True
        logger.info(f"[STINT_SELECTOR] {self._module_id}: Applying external selection "
                   f"({len(selected_stints_data)} stints, merge={is_merge_mode})")
        
        try:
            # 建立 lookup set: (driver, stint_number)
            selected_keys = set()
            for stint_data in selected_stints_data:
                driver = stint_data.get('driver', '')
                stint_num = stint_data.get('stint_number', 0)
                if driver and stint_num:
                    selected_keys.add((driver, stint_num))
            
            # 更新本地選擇狀態
            for stint in self._all_stints:
                key = (stint.driver, stint.stint_number)
                stint.selected = key in selected_keys
            
            # 更新 merge mode
            self._is_merge_mode = is_merge_mode
            
            # 更新 UI（暫時阻止信號）
            self._block_signals = True
            self.merge_mode_cb.setChecked(is_merge_mode)
            self._update_tree_checkboxes()
            self._update_stats()
            self._block_signals = False
            
            # 發射本地 selection_changed（供 MDI 更新圖表）
            # 但不觸發全局同步（因為 _is_applying_external = True）
            selected = [s for s in self._all_stints if s.selected]
            self.selection_changed.emit(selected)
            
        except Exception as e:
            logger.error(f"[STINT_SELECTOR] {self._module_id}: Failed to apply external selection: {e}")
        finally:
            self._is_applying_external = False
    
    def _emit_global_sync(self) -> None:
        """發射全局同步信號"""
        if not self._global_sync_enabled:
            return
        
        if self._is_applying_external:
            return  # 防止迴圈
        
        if not all([self._session_year, self._session_race, self._session_name]):
            logger.debug(f"[STINT_SELECTOR] {self._module_id}: Skipping global sync (session info not set)")
            return
        
        try:
            from .global_chart_sync_signal import get_global_chart_sync
            sync = get_global_chart_sync()
            
            # 準備選中的 Stint 資料
            selected_stints_data = []
            for stint in self._all_stints:
                if stint.selected:
                    selected_stints_data.append({
                        'driver': stint.driver,
                        'stint_number': stint.stint_number,
                        'start_lap': stint.start_lap,
                        'end_lap': stint.end_lap,
                        'compound': stint.compound
                    })
            
            sync.emit_stint_selection_changed(
                selected_stints=selected_stints_data,
                is_merge_mode=self._is_merge_mode,
                year=self._session_year,
                race=self._session_race,
                session=self._session_name,
                source=self._module_id
            )
        except Exception as e:
            logger.error(f"[STINT_SELECTOR] {self._module_id}: Failed to emit global sync: {e}")
