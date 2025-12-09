"""
Live Timing Battle Insight
==========================

即時顯示可能發生 Fight 的車手配對及超車分析。
使用 F83 超車預測 + F84 規則引擎解說。

Author: F1T Team
Date: 2025-12-05
"""

from typing import Dict, List, Any, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QAbstractItemView, QHeaderView, QLabel
)
from PyQt5.QtGui import QColor, QFont

from ..core.base_live_mdi import BaseLiveTimingMDI
from core.gui_i18n import tr

# 導入車手顏色
try:
    from modules.gui.themes.color_palette_provider import color_palette_provider
    COLOR_PALETTE_AVAILABLE = True
except ImportError:
    COLOR_PALETTE_AVAILABLE = False
    color_palette_provider = None

# 延遲導入 F84 規則引擎
RuleBasedExplainer = None
EXPLAINER_AVAILABLE = False


def _lazy_import_explainer():
    """延遲導入 F84 規則引擎"""
    global EXPLAINER_AVAILABLE, RuleBasedExplainer
    if EXPLAINER_AVAILABLE:
        return True
    try:
        from CLI_modules.cli.prediction.overtake_prediction.explainer import RuleBasedExplainer as _Explainer
        RuleBasedExplainer = _Explainer
        EXPLAINER_AVAILABLE = True
        print("[BATTLE_INSIGHT] F84 RuleBasedExplainer loaded")
        return True
    except Exception as e:
        print(f"[BATTLE_INSIGHT] F84 explainer not available: {e}")
        return False


class BattleInsightWidget(QWidget):
    """
    Battle Insight Widget - 顯示即時戰鬥分析
    
    功能：
    - 識別 OT% >= 閾值的車手對
    - 使用 F84 規則引擎生成解說
    - 顯示關鍵要點和建議
    """
    
    # 超車機率閾值（顯示 Battle 的最低機率）
    BATTLE_THRESHOLD = 40  # 40% (降低閾值，更早發現戰鬥)
    
    # 連續追近閾值
    CATCHING_THRESHOLD = -0.04  # 每秒追近 0.04 秒以上視為追近
    CONSECUTIVE_CATCHING_HIGHLIGHT = 3  # 連續追近 3 次以上顯著標示
    CATCHING_RESET_TOLERANCE = 3  # 連續 3 次未追近才重置計數
    
    # 歷史戰鬥保留時間（秒）
    HISTORY_RETENTION_SECONDS = 10  # 超車後保留 10 秒顯示
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 設定 Widget 背景為黑色
        self.setStyleSheet("QWidget { background-color: #1a1a1a; }")
        
        # 初始化 F84 解說器
        self._explainer = None
        if _lazy_import_explainer():
            self._explainer = RuleBasedExplainer(language="zh-TW")
        
        # 當前快照
        self._current_snapshot: Optional[Dict] = None
        self._tyre_state: Dict[str, Dict] = {}
        
        # 連續追近計數器 {"attacker_num:defender_num": count}
        self._consecutive_catching: Dict[str, int] = {}
        
        # 未追近計數器（用於容錯重置）{"attacker_num:defender_num": not_catching_count}
        self._not_catching_count: Dict[str, int] = {}
        
        # 歷史戰鬥記錄（超車後保留顯示）{"attacker_num:defender_num": {"timestamp": float, "battle_info": dict}}
        self._battle_history: Dict[str, Dict] = {}
        
        self._init_ui()
        
        print("[BattleInsightWidget] initialized")
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)
        
        # 提示標籤（lap 1,2 時顯示）
        self.info_label = QLabel()
        self.info_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                color: #888888;
                font-size: 12px;
                padding: 8px;
            }
        """)
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.hide()
        layout.addWidget(self.info_label)
        
        # Battle 列表
        self.battle_table = QTableWidget()
        self.battle_table.setColumnCount(4)
        self.battle_table.setHorizontalHeaderLabels([
            tr("battle", "Battle"),
            "OT%",
            tr("status", "Status"),
            tr("insight", "Insight")
        ])
        self.battle_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.battle_table.setSelectionMode(QAbstractItemView.NoSelection)
        self.battle_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        
        # 欄位寬度
        self.battle_table.setColumnWidth(0, 200)  # Battle
        self.battle_table.setColumnWidth(1, 45)   # OT%
        self.battle_table.setColumnWidth(2, 70)   # Status
        self.battle_table.horizontalHeader().setStretchLastSection(True)  # Insight
        
        # 啟用自動換行
        self.battle_table.setWordWrap(True)
        self.battle_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.battle_table.verticalHeader().setVisible(False)
        
        # 深色主題樣式
        self.battle_table.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a1a;
                color: #E0E0E0;
                gridline-color: #333333;
                border: none;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #2a2a2a;
                color: #E0E0E0;
                padding: 4px;
                border: 1px solid #333333;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.battle_table)
    
    def clear_catching_history(self):
        """清除連續追近記錄（賽事切換時調用）"""
        self._consecutive_catching.clear()
        self._not_catching_count.clear()
        self._battle_history.clear()
    
    def update_snapshot(self, snapshot: Dict[str, Any], tyre_state: Dict[str, Dict] = None):
        """
        更新快照數據
        
        Args:
            snapshot: 包含 drivers 的快照
            tyre_state: 輪胎狀態 {driver_num: {compound, age}}
        """
        self._current_snapshot = snapshot
        self._tyre_state = tyre_state or {}
        self._update_battles()
    
    def _update_battles(self):
        """更新 Battle 列表"""
        if not self._current_snapshot:
            return
        
        # 檢查當前圈數 - lap 1, 2 不顯示
        current_lap = self._current_snapshot.get('current_lap', 0)
        if current_lap <= 2:
            self.battle_table.setRowCount(0)
            self.info_label.setText(tr("battle_insight_early_lap", 
                f"Lap {current_lap}: OT% not available (data collecting...)"))
            self.info_label.show()
            self.battle_table.hide()
            return
        else:
            self.info_label.hide()
            self.battle_table.show()
        
        drivers = self._current_snapshot.get('drivers', {})
        if not drivers:
            return
        
        # 獲取當前時間戳
        import time
        current_time = time.time()
        
        # 清理過期的歷史戰鬥
        expired_keys = []
        for battle_key, history in self._battle_history.items():
            if current_time - history['timestamp'] > self.HISTORY_RETENTION_SECONDS:
                expired_keys.append(battle_key)
        for key in expired_keys:
            del self._battle_history[key]
        
        # 收集所有可能的 Battle
        battles = []
        
        # 按位置排序
        sorted_drivers = []
        for driver_num, driver_data in drivers.items():
            pos = driver_data.get('position', 99)
            ot_prob = driver_data.get('overtake_probability', 0)
            sorted_drivers.append((driver_num, driver_data, pos, ot_prob))
        sorted_drivers.sort(key=lambda x: x[2])
        
        # 識別 Battle
        for i, (driver_num, driver_data, position, ot_prob) in enumerate(sorted_drivers):
            # 跳過 P1
            if position == 1 or i == 0:
                continue
            
            # 獲取前車資訊
            ahead_num, ahead_data, ahead_pos, _ = sorted_drivers[i - 1]
            battle_key = f"{driver_num}:{ahead_num}"
            
            # 檢查是否超過閾值或有歷史記錄
            if ot_prob >= self.BATTLE_THRESHOLD:
                # 構建 Battle 資訊
                battle_info = self._build_battle_info(
                    attacker_num=driver_num,
                    attacker_data=driver_data,
                    defender_num=ahead_num,
                    defender_data=ahead_data,
                    ot_prob=ot_prob
                )
                battles.append(battle_info)
                
                # 更新歷史記錄
                self._battle_history[battle_key] = {
                    'timestamp': current_time,
                    'battle_info': battle_info
                }
            elif battle_key in self._battle_history:
                # 已超車但仍在保留期內，顯示歷史記錄並標註
                history = self._battle_history[battle_key]
                battle_info = history['battle_info'].copy()
                battle_info['status'] = 'DONE'
                battle_info['status_color'] = '#666666'
                elapsed = int(current_time - history['timestamp'])
                battle_info['insight'] = f"[完成超車 {elapsed}s前]" + battle_info.get('insight', '')
                battles.append(battle_info)
        
        # 排序：優先按位置（越前面越重要），相同位置再按 OT% 排序
        # attacker_pos 小的在前（P2 vs P1 優先於 P10 vs P9）
        # 相同位置時，OT% 高的在前（負號實現降序）
        battles.sort(key=lambda x: (x['attacker_pos'], -x['ot_prob']))
        
        # 更新表格
        self._populate_table(battles)
    
    def _build_battle_info(self, attacker_num: str, attacker_data: Dict,
                           defender_num: str, defender_data: Dict,
                           ot_prob: float) -> Dict[str, Any]:
        """構建單個 Battle 的資訊"""
        attacker_tla = attacker_data.get('driver_tla', attacker_num)
        defender_tla = defender_data.get('driver_tla', defender_num)
        attacker_pos = attacker_data.get('position', 0)
        defender_pos = defender_data.get('position', 0)
        
        # 獲取間距
        gap_str = attacker_data.get('gap_to_ahead', '') or attacker_data.get('gap_to_ahead_display', '')
        gap_seconds = self._parse_gap(gap_str)
        
        # 獲取 gap_trend（間距變化趨勢）
        gap_trend = attacker_data.get('gap_trend', 0.0)
        
        # 更新連續追近計數器
        battle_key = f"{attacker_num}:{defender_num}"
        consecutive_catching = self._update_consecutive_catching(battle_key, gap_trend)
        
        # 獲取輪胎資訊
        attacker_tyre = self._tyre_state.get(attacker_num, {})
        defender_tyre = self._tyre_state.get(defender_num, {})
        tyre_age_diff = defender_tyre.get('age', 0) - attacker_tyre.get('age', 0)
        
        # 判斷狀態
        drs_ready = gap_seconds is not None and gap_seconds < 1.0
        
        # 狀態文字
        if drs_ready:
            status = "DRS"
            status_color = "#00FF00"
        elif gap_seconds is not None and gap_seconds < 1.5:
            status = tr("closing", "Closing")
            status_color = "#FFFF00"
        else:
            status = tr("hunting", "Hunting")
            status_color = "#E0E0E0"
        
        # 生成簡潔 Insight（多國語言化）
        insight = self._generate_insight(
            attacker_tla, defender_tla,
            ot_prob, gap_seconds, tyre_age_diff, drs_ready,
            attacker_tyre.get('compound', ''),
            defender_tyre.get('compound', '')
        )
        
        # 獲取車手顏色
        attacker_color = self._get_driver_color(attacker_tla, attacker_data)
        defender_color = self._get_driver_color(defender_tla, defender_data)
        
        return {
            'battle_text': f"P{attacker_pos} {attacker_tla} vs P{defender_pos} {defender_tla}",
            'attacker_tla': attacker_tla,
            'defender_tla': defender_tla,
            'attacker_pos': attacker_pos,
            'defender_pos': defender_pos,
            'attacker_color': attacker_color,
            'defender_color': defender_color,
            'ot_prob': ot_prob,
            'status': status,
            'status_color': status_color,
            'insight': insight,
            'gap_seconds': gap_seconds,
            'gap_trend': gap_trend,
            'consecutive_catching': consecutive_catching,
            'tyre_diff': tyre_age_diff,
            'drs_ready': drs_ready,
            'attacker_compound': attacker_tyre.get('compound', ''),
            'defender_compound': defender_tyre.get('compound', ''),
            'attacker_num': attacker_num,
            'defender_num': defender_num
        }
    
    def _update_consecutive_catching(self, battle_key: str, gap_trend: float) -> int:
        """
        更新連續追近計數器（容錯機制：連續 3 次未追近才重置）
        
        Args:
            battle_key: 戰鬥配對鍵 (attacker:defender)
            gap_trend: 間距趨勢（負值 = 追近）
            
        Returns:
            連續追近次數
        """
        if gap_trend < self.CATCHING_THRESHOLD:
            # 正在追近，增加計數並重置未追近計數
            self._consecutive_catching[battle_key] = self._consecutive_catching.get(battle_key, 0) + 1
            self._not_catching_count[battle_key] = 0
        else:
            # 未追近，增加未追近計數
            not_catching = self._not_catching_count.get(battle_key, 0) + 1
            self._not_catching_count[battle_key] = not_catching
            
            # 連續 3 次未追近才重置追近計數（容錯機制）
            if not_catching >= self.CATCHING_RESET_TOLERANCE:
                self._consecutive_catching[battle_key] = 0
                self._not_catching_count[battle_key] = 0
        
        return self._consecutive_catching.get(battle_key, 0)
    
    def _get_driver_color(self, driver_tla: str, driver_data: Dict) -> str:
        """獲取車手顏色"""
        team_color = None
        
        if COLOR_PALETTE_AVAILABLE and color_palette_provider:
            try:
                team_color_qcolor = color_palette_provider.get_driver_color(driver_tla, fallback=True)
                if team_color_qcolor:
                    team_color = team_color_qcolor.name()
            except Exception:
                pass
        
        if not team_color:
            team_color = driver_data.get('team_color', 'CCCCCC')
            if team_color and not team_color.startswith('#'):
                team_color = f'#{team_color}'
        
        return team_color
    
    def _get_text_color_for_bg(self, bg_color: str) -> str:
        """根據背景色計算合適的文字顏色"""
        try:
            # 解析 hex 顏色
            color = bg_color.lstrip('#')
            if len(color) == 6:
                r = int(color[0:2], 16)
                g = int(color[2:4], 16)
                b = int(color[4:6], 16)
                # 計算亮度
                luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
                return '#000000' if luminance > 0.5 else '#FFFFFF'
        except Exception:
            pass
        return '#FFFFFF'
    
    def _generate_insight(self, attacker: str, defender: str,
                          ot_prob: float, gap: Optional[float],
                          tyre_diff: int, drs_ready: bool,
                          attacker_compound: str, defender_compound: str) -> str:
        """生成簡潔多國語言化解說"""
        parts = []
        
        # 1. 間距
        if gap is not None:
            gap_text = tr("battle_gap", "Gap") + f": {gap:.2f}s"
            parts.append(gap_text)
        
        # 2. 輪胎狀況
        if tyre_diff > 3:
            tyre_text = tr("battle_tyre_advantage", "Tyre") + f": +{tyre_diff}"
            parts.append(tyre_text)
        elif tyre_diff < -3:
            tyre_text = tr("battle_tyre_disadvantage", "Tyre") + f": {tyre_diff}"
            parts.append(tyre_text)
        elif attacker_compound or defender_compound:
            # 顯示輪胎化合物
            a_comp = attacker_compound[:1].upper() if attacker_compound else "?"
            d_comp = defender_compound[:1].upper() if defender_compound else "?"
            parts.append(f"{a_comp} vs {d_comp}")
        
        return " | ".join(parts)
    
    def _parse_gap(self, gap_str: str) -> Optional[float]:
        """解析間距字串"""
        if not gap_str:
            return None
        gap_str = str(gap_str).strip().upper()
        if 'LAP' in gap_str:
            return None
        gap_str = gap_str.replace('+', '').replace('S', '').strip()
        try:
            return float(gap_str)
        except ValueError:
            return None
    
    def _get_tyre_color(self, compound: str) -> str:
        """獲取輪胎化合物顏色"""
        compound = compound.upper() if compound else ""
        tyre_colors = {
            'SOFT': '#FF3333',      # 紅色
            'S': '#FF3333',
            'MEDIUM': '#FFFF00',    # 黃色
            'M': '#FFFF00',
            'HARD': '#FFFFFF',      # 白色
            'H': '#FFFFFF',
            'INTERMEDIATE': '#00FF00',  # 綠色
            'I': '#00FF00',
            'WET': '#00BFFF',       # 藍色
            'W': '#00BFFF',
        }
        return tyre_colors.get(compound, '#CCCCCC')
    
    def _populate_table(self, battles: List[Dict]):
        """填充表格"""
        self.battle_table.setRowCount(len(battles))
        
        for row, battle in enumerate(battles):
            # Battle 欄位 - 使用 QLabel 實現車手名稱背景色（與 Ranking Tower 一致）
            attacker_tla = battle['attacker_tla']
            defender_tla = battle['defender_tla']
            attacker_pos = battle['attacker_pos']
            defender_pos = battle['defender_pos']
            attacker_color = battle['attacker_color']
            defender_color = battle['defender_color']
            
            # 計算車手名稱的文字顏色（根據背景亮度）
            attacker_text_color = self._get_text_color_for_bg(attacker_color)
            defender_text_color = self._get_text_color_for_bg(defender_color)
            
            # 創建 HTML 富文字 Label - 車手名稱帶背景色
            battle_label = QLabel()
            battle_html = (
                f'<span style="color:#888888;">P{attacker_pos} </span>'
                f'<span style="background-color:{attacker_color}; color:{attacker_text_color}; '
                f'font-weight:bold; padding:1px 3px; border-radius:2px;">{attacker_tla}</span>'
                f'<span style="color:#888888;"> -> P{defender_pos} </span>'
                f'<span style="background-color:{defender_color}; color:{defender_text_color}; '
                f'font-weight:bold; padding:1px 3px; border-radius:2px;">{defender_tla}</span>'
            )
            battle_label.setText(battle_html)
            battle_label.setStyleSheet("background-color: transparent; padding: 2px;")
            self.battle_table.setCellWidget(row, 0, battle_label)
            
            # OT% 欄位
            ot_text = f"{int(battle['ot_prob'])}%"
            ot_item = QTableWidgetItem(ot_text)
            ot_item.setTextAlignment(Qt.AlignCenter)
            if battle['ot_prob'] >= 80:
                # 只有 >= 80% 才標註黃色底色
                ot_item.setBackground(QColor('#FFFF00'))
                ot_item.setForeground(QColor('#000000'))
            else:
                ot_item.setForeground(QColor('#E0E0E0'))
            self.battle_table.setItem(row, 1, ot_item)
            
            # Status 欄位
            status_item = QTableWidgetItem(battle['status'])
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setForeground(QColor(battle['status_color']))
            if battle['status'] == 'DRS':
                font = status_item.font()
                font.setBold(True)
                status_item.setFont(font)
            self.battle_table.setItem(row, 2, status_item)
            
            # Insight 欄位 - 使用 QLabel 實現輪胎顏色
            insight_label = QLabel()
            insight_html = self._build_insight_html(battle)
            insight_label.setText(insight_html)
            insight_label.setStyleSheet("background-color: transparent; padding: 2px;")
            insight_label.setWordWrap(True)
            self.battle_table.setCellWidget(row, 3, insight_label)
    
    def _build_insight_html(self, battle: Dict) -> str:
        """構建 Insight 的 HTML 富文字"""
        gap = battle.get('gap_seconds')
        tyre_diff = battle.get('tyre_diff', 0)
        attacker_compound = battle.get('attacker_compound', '')
        defender_compound = battle.get('defender_compound', '')
        consecutive_catching = battle.get('consecutive_catching', 0)
        gap_trend = battle.get('gap_trend', 0.0)
        
        parts = []
        
        # 1. 連續追近標記（只顯示 3 次和 5 次以上）
        if consecutive_catching >= 5:
            # 連續追近 5 次以上，強烈醒目標記
            catching_text = tr("battle_consecutive_catching", "Catching")
            parts.append(
                f'<span style="color:#00FF00; font-weight:bold; '
                f'background-color:#004400; padding:1px 4px; border-radius:3px;">'
                f'>>>>> {catching_text} x{consecutive_catching}</span>'
            )
        elif consecutive_catching >= 3:
            # 連續追近 3-4 次，一般醒目標記
            catching_text = tr("battle_consecutive_catching", "Catching")
            parts.append(
                f'<span style="color:#66FF66; font-weight:bold; '
                f'background-color:#002200; padding:1px 4px; border-radius:3px;">'
                f'>>> {catching_text} x{consecutive_catching}</span>'
            )
        # 其他情況不顯示追近標記
        
        # 2. 間距
        if gap is not None:
            gap_text = tr("battle_gap", "Gap") + f": {gap:.2f}s"
            parts.append(f'<span style="color:#E0E0E0;">{gap_text}</span>')
        
        # 3. 輪胎狀況（帶顏色）
        if attacker_compound or defender_compound:
            a_comp = attacker_compound[:1].upper() if attacker_compound else "?"
            d_comp = defender_compound[:1].upper() if defender_compound else "?"
            a_color = self._get_tyre_color(attacker_compound)
            d_color = self._get_tyre_color(defender_compound)
            
            tyre_html = (
                f'<span style="color:{a_color}; font-weight:bold;">{a_comp}</span>'
                f'<span style="color:#888888;"> vs </span>'
                f'<span style="color:{d_color}; font-weight:bold;">{d_comp}</span>'
            )
            
            # 如果有輪胎年齡差異，也顯示
            if tyre_diff > 3:
                tyre_html += f'<span style="color:#00FF00;"> (+{tyre_diff})</span>'
            elif tyre_diff < -3:
                tyre_html += f'<span style="color:#FF6666;"> ({tyre_diff})</span>'
            
            parts.append(tyre_html)
        
        return ' <span style="color:#666666;">|</span> '.join(parts)


class BattleInsightMDI(BaseLiveTimingMDI):
    """
    Battle Insight MDI 視窗
    
    繼承 BaseLiveTimingMDI 以自動訂閱 DataManager 信號。
    """
    
    _window_title_key = "battle_insight"
    _default_title = "Battle Insight"
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent, data_manager)
        
        self.setWindowTitle(tr(self._window_title_key, self._default_title))
        self.setMinimumSize(400, 200)
        self.resize(500, 300)
        
        print(f"[BATTLE_INSIGHT_MDI] initialized")
    
    def _setup_ui(self):
        """Setup UI components"""
        self._widget = BattleInsightWidget(self)
        self._main_layout.addWidget(self._widget)
    
    def _on_snapshot_updated(self, snapshot: Dict[str, Any]):
        """處理快照更新"""
        # 獲取輪胎狀態
        tyre_state = None
        if self._data_manager:
            tyre_state = self._data_manager.get_tyre_state()
        
        self._widget.update_snapshot(snapshot, tyre_state)
    
    def _on_race_loaded(self, race_info: Dict[str, Any]):
        """處理賽事載入"""
        print(f"[BATTLE_INSIGHT_MDI] Race loaded: {race_info.get('race', 'Unknown')}")
        # 清除連續追近記錄
        self._widget.clear_catching_history()
    
    def _on_race_unloaded(self):
        """處理賽事卸載"""
        self._widget.battle_table.setRowCount(0)
        # 清除連續追近記錄
        self._widget.clear_catching_history()
