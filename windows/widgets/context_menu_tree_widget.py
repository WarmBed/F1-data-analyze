# -*- coding: utf-8 -*-
"""
F1T GUI - ContextMenuTreeWidget
================================

支援右鍵選單和多選功能的功能樹。

從 f1t_gui_main.py 提取 (原始行號: 5305-5782, 477 行)
提取日期: 2025-06-14
"""

import time
import logging
from typing import Dict, Any

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidget, QMenu

# 引入翻譯函數
try:
    from core.gui_i18n import tr
except ImportError:
    def tr(key, default=None, *args, **kwargs):
        return default if default else key

# 設定日誌
logger = logging.getLogger(__name__)


class ContextMenuTreeWidget(QTreeWidget):
    """支援右鍵選單和多選功能的功能樹"""
    
    def __init__(self, main_window=None):
        super().__init__()
        self.main_window = main_window
        
        # 啟用多選功能
        self.setSelectionMode(QTreeWidget.ExtendedSelection)  # 支援 Ctrl 和 Shift 多選
        
        # 設置右鍵選單
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        # 修復洩漏：使用 Qt.UniqueConnection 防止信號重複連接
        self.customContextMenuRequested.connect(self.show_context_menu, Qt.UniqueConnection)
        
        # 修復洩漏：使用 Qt.UniqueConnection 防止信號風暴
        # 性能優化：添加防抖機制
        self._last_click_time = 0
        self._click_debounce_ms = 100  # 100ms 防抖
        self.itemClicked.connect(self.on_item_clicked, Qt.UniqueConnection)
        
        # 自適應列寬：當項目展開/收合時自動調整寬度
        self.itemExpanded.connect(self._adjust_column_width, Qt.UniqueConnection)
        self.itemCollapsed.connect(self._adjust_column_width, Qt.UniqueConnection)
        
        # 記錄用戶是否手動調整過寬度（由主窗口的 Splitter 設置）
        self._user_resized = False
        
    def _adjust_column_width(self):
        """當樹狀圖展開/收合時自動調整列寬（除非用戶已手動調整 Splitter）"""
        if not self._user_resized:
            old_width = self.columnWidth(0)
            self.resizeColumnToContents(0)
            new_width = self.columnWidth(0)
            
            # 如果寬度有變化，通知主窗口調整 Splitter
            if new_width != old_width and self.main_window:
                self.main_window._adjust_splitter_for_tree(new_width)
    
    def mark_user_resized(self):
        """標記用戶已手動調整寬度（由主窗口調用）"""
        self._user_resized = True
        
    def on_item_clicked(self, item, column):
        """處理項目點擊事件 - 僅用於選擇，不觸發分析
        
        性能優化 (2025-10-12):
        - 添加防抖機制，避免信號風暴
        - 減少 selectedItems() 調用次數
        """
        # 防抖機制：避免頻繁觸發（100ms 內只處理一次）
        current_time = time.time() * 1000  # 轉換為毫秒
        if current_time - self._last_click_time < self._click_debounce_ms:
            return  # 忽略過於頻繁的點擊
        self._last_click_time = current_time
        
        # 檢查是否為葉節點（可分析的項目）
        if item.childCount() == 0:
            # 優化：只調用一次 selectedItems()
            selected_items = self.selectedItems()
            selected_count = len(selected_items)
            
            if selected_count > 1:
                # 多選模式：顯示選中的項目數量
                logger.debug(f"[MULTI_SELECT] 已選擇 {selected_count} 個分析模組")
                # 優化：只在少於 10 個時詳細列出
                if selected_count <= 10:
                    for selected_item in selected_items:
                        if selected_item.childCount() == 0:  # 確保是葉節點
                            logger.debug(f"  - {selected_item.text(0)}")
                else:
                    logger.debug(f"  (項目過多，不詳細列出)")
                logger.debug(f"[MULTI_SELECT] 提示：右鍵點擊可執行批量分析")
            else:
                # 單選模式：僅顯示選中項目，不直接執行分析
                logger.debug(f"[SINGLE_SELECT] 已選擇分析模組: {item.text(0)}")
                logger.debug(f"[SINGLE_SELECT] 提示：右鍵點擊可執行分析")
    
    def show_context_menu(self, position):
        """顯示右鍵選單"""
        item = self.itemAt(position)
        if item is None:
            return
        
        selected_items = self.selectedItems()
        
        # 過濾出葉節點（可分析的項目）- 排除父項目和禁用項目
        analyzable_items = [
            item for item in selected_items 
            if item.childCount() == 0 and (item.flags() & Qt.ItemIsEnabled)
        ]
        
        # 檢查是否有頂層項目（父項目）
        has_parent_items = any(item.childCount() > 0 for item in selected_items)
        
        menu = QMenu(self)
        menu.setObjectName("ContextMenu")
        
        if len(analyzable_items) == 1:
            # 單選選單（葉節點）
            analyze_action = menu.addAction(f"{tr('execute_analysis', '執行分析')} - {analyzable_items[0].text(0).strip()}")
            analyze_action.triggered.connect(lambda: self.analyze_function(analyzable_items[0].text(0)))
            
            menu.addSeparator()
            
            # 全展開樹狀圖
            expand_action = menu.addAction(tr('expand_all_tree', '全展開樹狀圖'))
            expand_action.triggered.connect(self.expandAll)
            
            # 全關閉樹狀圖
            collapse_action = menu.addAction(tr('collapse_all_tree', '全關閉樹狀圖'))
            collapse_action.triggered.connect(self.collapseAll)
            
            menu.addSeparator()
            
            help_action = menu.addAction(f"{tr('help', '說明')} - {analyzable_items[0].text(0).strip()}")
            help_action.triggered.connect(lambda: self.show_help(analyzable_items[0].text(0)))
            
        elif len(analyzable_items) > 1:
            # 多選選單（多個葉節點）
            analyze_action = menu.addAction(f"{tr('batch_execute_analysis', '批量執行分析')} ({len(analyzable_items)} {tr('modules', '個模組')})")
            analyze_action.triggered.connect(lambda: self.analyze_multiple_functions(analyzable_items))
            
            menu.addSeparator()
            
            # 全展開樹狀圖
            expand_action = menu.addAction(tr('expand_all_tree', '全展開樹狀圖'))
            expand_action.triggered.connect(self.expandAll)
            
            # 全關閉樹狀圖
            collapse_action = menu.addAction(tr('collapse_all_tree', '全關閉樹狀圖'))
            collapse_action.triggered.connect(self.collapseAll)
            
            menu.addSeparator()
            
            # 顯示選中的項目列表
            selected_submenu = menu.addMenu(f"{tr('selected_modules', '已選擇的模組')} ({len(analyzable_items)} {tr('items', '個')})")
            for item in analyzable_items:
                clean_name = item.text(0).strip()
                item_action = selected_submenu.addAction(f"{clean_name}")
                item_action.setEnabled(False)  # 僅用於顯示，不可點擊
        
        else:
            # 只選中了父項目或禁用項目
            # 顯示灰色的執行分析選項
            if len(selected_items) == 1:
                item_name = selected_items[0].text(0).strip()
                analyze_action = menu.addAction(f"{tr('execute_analysis', '執行分析')} - {item_name}")
                analyze_action.setEnabled(False)  # 設為灰色不可點擊
            else:
                analyze_action = menu.addAction(tr('select_specific_module', '請選擇具體的分析模組'))
                analyze_action.setEnabled(False)
            
            menu.addSeparator()
            
            # 全展開樹狀圖（可用）
            expand_action = menu.addAction(tr('expand_all_tree', '全展開樹狀圖'))
            expand_action.triggered.connect(self.expandAll)
            
            # 全關閉樹狀圖（可用）
            collapse_action = menu.addAction(tr('collapse_all_tree', '全關閉樹狀圖'))
            collapse_action.triggered.connect(self.collapseAll)
            
            menu.addSeparator()
            
            # 說明（灰色）
            if len(selected_items) == 1:
                help_action = menu.addAction(f"{tr('help', '說明')} - {selected_items[0].text(0).strip()}")
                help_action.setEnabled(False)
        
        menu.exec_(self.mapToGlobal(position))
    
    def analyze_multiple_functions(self, items):
        """批量分析多個功能（智能過濾父項目）"""
        # 二次過濾：確保只處理葉節點（沒有子項目的項目）
        leaf_items = [item for item in items if item.childCount() == 0]
        
        if not leaf_items:
            logger.debug(f"[BATCH_ANALYSIS] 沒有可執行的葉節點")
            return
        
        # 計算被過濾掉的父項目數量
        filtered_count = len(items) - len(leaf_items)
        if filtered_count > 0:
            logger.debug(f"[BATCH_ANALYSIS] 已過濾掉 {filtered_count} 個父項目")
        
        logger.debug(f"[BATCH_ANALYSIS] 開始批量分析 {len(leaf_items)} 個模組")
        
        for item in leaf_items:
            function_name = item.text(0).strip()
            logger.debug(f"[BATCH_ANALYSIS] 正在創建: {function_name}")
            # 傳遞 batch_mode=True 防止彈出對話框
            self.analyze_function(function_name, batch_mode=True)
            
        logger.debug(f"[BATCH_ANALYSIS] 批量分析完成，共創建了 {len(leaf_items)} 個分析視窗")
    
    def export_multiple_functions(self, items):
        """批量匯出多個功能的數據"""
        # 只處理葉節點
        leaf_items = [item for item in items if item.childCount() == 0]
        
        logger.debug(f"[BATCH_EXPORT] 開始批量匯出 {len(leaf_items)} 個模組的數據")
        
        for item in leaf_items:
            function_name = item.text(0).strip()
            logger.debug(f"[BATCH_EXPORT] 正在匯出: {function_name}")
            self.export_function(function_name)
            
        logger.debug(f"[BATCH_EXPORT] 批量匯出完成")
    
    def cleanup(self):
        """
        清理資源和信號連接
        
        資源洩漏修復: 斷開所有信號，防止循環引用
        """
        try:
            logger.debug("[CLEANUP] 開始清理 ContextMenuTreeWidget 資源...")
            
            # 斷開所有信號連接
            try:
                self.customContextMenuRequested.disconnect()
                logger.debug("[CLEANUP]   斷開 customContextMenuRequested")
            except TypeError:
                pass  # 信號已經斷開
            
            try:
                self.itemClicked.disconnect()
                logger.debug("[CLEANUP]   斷開 itemClicked")
            except TypeError:
                pass  # 信號已經斷開
            
            # 清除 main_window 引用
            self.main_window = None
            
            logger.debug("[CLEANUP] ContextMenuTreeWidget 資源清理完成")
            
        except Exception as e:
            logger.warning(f"[WARNING] ContextMenuTreeWidget cleanup 失敗: {e}")
    
    def analyze_function(self, function_name, batch_mode=False):
        """分析單個功能（支援批量模式）
        
        父項目政策 (2025-10-03):
        - 父項目是路標（導航元素），不應觸發任何分析模組
        - 只有葉節點（子項目）才會開啟實際的分析視窗
        - 批量操作已通過 childCount() == 0 過濾掉父項目
        """
        if not self.main_window:
            return
        
        # 清理項目名稱（移除前綴和多餘空白）
        original_name = function_name.strip()
        clean_name = original_name
        
        # 移除前綴標記: (L), (D), (T)
        item_prefix = None  # 記錄前綴類型
        for prefix in ["(L) ", "(D) ", "(T) "]:
            if clean_name.startswith(prefix):
                item_prefix = prefix.strip("() ")  # 保存前綴類型: "L", "D", "T"
                clean_name = clean_name[len(prefix):]
                break
        
        logger.debug(f"[TREE_CLICK] 項目: {clean_name} (原始: {original_name}, 前綴: {item_prefix}), 批量模式: {batch_mode}")
        
        # ========== 父項目禁用政策 ==========
        # 父項目清單（這些項目只作為導航，不觸發任何操作）
        # 使用前綴區分：
        #    - (T) Throttle Analysis = 父項目（有子選單）
        #    - (L) Throttle Analysis = 實際功能（Lap Analysis 子模組）
        parent_items = [
            "Lap Analysis", "Lap Analysis (Telemetry)", "圈速分析", "圈速分析（遙測）",
            "Detailed Lap Analysis", "詳細圈速分析",
            "Ideal Lap Analysis", "理想圈分析"
        ]
        
        # 關鍵修復：只有 (T) Throttle Analysis 是父項目
        if clean_name in ["Throttle Analysis", "油門分析"] and item_prefix == "T":
            parent_items.append(clean_name)
        
        if not batch_mode and clean_name in parent_items:
            logger.debug(f"[TREE_CLICK] 父項目 '{clean_name}' (前綴: {item_prefix}) 不執行任何操作（僅作為路標）")
            return
        
        # ========== 子項目處理（直接開啟對應模組）==========
        params = self.main_window.get_current_parameters()
        lap_params: Dict[str, Any] = {}

        if hasattr(self.main_window, 'get_current_lap_toolbar_parameters'):
            try:
                lap_params = self.main_window.get_current_lap_toolbar_parameters() or {}
            except Exception as exc:
                logger.debug(f"[TREE_CLICK] 讀取圈速工具欄參數失敗: {exc}")

        if not isinstance(lap_params, dict):
            lap_params = {}

        driver1 = lap_params.get('driver1') or "VER"
        driver2 = lap_params.get('driver2')
        if isinstance(driver2, str) and not driver2.strip():
            driver2 = None

        lap1_number = lap_params.get('lap1_number')
        lap1_number = lap1_number if isinstance(lap1_number, int) and lap1_number > 0 else 1

        lap2_number = lap_params.get('lap2_number')
        if driver2 is None:
            lap2_number = None
        elif not isinstance(lap2_number, int) or lap2_number <= 0:
            lap2_number = 1

        lap_type = lap_params.get('lap_type') or tr('specific_lap', 'Specific Lap')
        is_fastest_lap = bool(lap_params.get('is_fastest_lap'))
        use_time_axis = bool(lap_params.get('use_time_axis', False))
        
        logger.debug(f"[TREE_CLICK] 參數: driver1={driver1}, driver2={driver2}, lap1={lap1_number}, lap2={lap2_number}, fastest={is_fastest_lap}, time_axis={use_time_axis}")
        
        # Lap Analysis 子模組 - 使用預設車手
        if clean_name in ["Speed Analysis", "速度分析"]:
            self.main_window.create_telemetry_window(
                "speed_analysis", params,
                driver1=driver1, driver2=driver2,
                lap1_number=lap1_number, lap2_number=lap2_number,
                lap_type=lap_type, is_fastest_lap=is_fastest_lap,
                use_time_axis=use_time_axis
            )
        
        elif clean_name in ["Brake Analysis", "煞車分析"]:
            self.main_window.create_telemetry_window(
                "brake", params,
                driver1=driver1, driver2=driver2,
                lap1_number=lap1_number, lap2_number=lap2_number,
                lap_type=lap_type, is_fastest_lap=is_fastest_lap,
                use_time_axis=use_time_axis
            )
        
        elif clean_name in ["Gear Analysis", "檔位分析"]:
            self.main_window.create_telemetry_window(
                "gear", params,
                driver1=driver1, driver2=driver2,
                lap1_number=lap1_number, lap2_number=lap2_number,
                lap_type=lap_type, is_fastest_lap=is_fastest_lap,
                use_time_axis=use_time_axis
            )
        
        elif clean_name in ["RPM Analysis", "轉速分析"]:
            self.main_window.create_telemetry_window(
                "rpm", params,
                driver1=driver1, driver2=driver2,
                lap1_number=lap1_number, lap2_number=lap2_number,
                lap_type=lap_type, is_fastest_lap=is_fastest_lap,
                use_time_axis=use_time_axis
            )
        
        elif clean_name in ["Acceleration Analysis", "加速度分析"]:
            self.main_window.create_telemetry_window(
                "acceleration", params,
                driver1=driver1, driver2=driver2,
                lap1_number=lap1_number, lap2_number=lap2_number,
                lap_type=lap_type, is_fastest_lap=is_fastest_lap,
                use_time_axis=use_time_axis
            )
        
        elif clean_name in ["Speed Diff Analysis", "速度差分析"]:
            self.main_window.create_telemetry_window(
                "speed_diff", params,
                driver1=driver1, driver2=driver2,
                lap1_number=lap1_number, lap2_number=lap2_number,
                lap_type=lap_type, is_fastest_lap=is_fastest_lap,
                use_time_axis=use_time_axis
            )
        
        elif clean_name in ["Distance Diff Analysis", "距離差分析"]:
            self.main_window.create_telemetry_window(
                "distancediff", params,
                driver1=driver1, driver2=driver2,
                lap1_number=lap1_number, lap2_number=lap2_number,
                lap_type=lap_type, is_fastest_lap=is_fastest_lap,
                use_time_axis=use_time_axis
            )
        
        elif clean_name in ["Time Diff Analysis", "時間差分析"]:
            self.main_window.create_telemetry_window(
                "timediff", params,
                driver1=driver1, driver2=driver2,
                lap1_number=lap1_number, lap2_number=lap2_number,
                lap_type=lap_type, is_fastest_lap=is_fastest_lap,
                use_time_axis=use_time_axis
            )
        
        elif clean_name in ["Throttle Analysis", "油門分析"]:
            # Lap Analysis 下的 Throttle Analysis 子模組（不是父項目）
            logger.debug(f"[TREE_CLICK] 開啟油門遙測分析（Lap Analysis 子模組）")
            self.main_window.create_telemetry_window(
                "throttle", params,
                driver1=driver1, driver2=driver2,
                lap1_number=lap1_number, lap2_number=lap2_number,
                lap_type=lap_type, is_fastest_lap=is_fastest_lap,
                use_time_axis=use_time_axis
            )
        
        # Detailed Lap Analysis 子模組
        elif clean_name in ["Detailed Lap Table", "詳細圈速表格"]:
            logger.debug(f"[TREE_CLICK] 開啟詳細圈速表格（模組工廠模式）")
            # 使用統一的 create_analysis_window 入口（支援模組工廠）
            self.main_window.create_analysis_window(clean_name)
        
        elif clean_name in ["Lap Time Box Plot", "圈速箱線圖", "圈速箱型圖"]:
            logger.debug(f"[TREE_CLICK] 開啟圈速箱線圖（模組工廠模式）")
            self.main_window.create_analysis_window(clean_name)
        
        # Throttle Analysis 子模組（父項目的子視圖）
        elif clean_name in ["Throttle Box Plot", "油門箱線圖", "油門箱型圖"]:
            logger.debug(f"[TREE_CLICK] 開啟油門箱線圖（模組工廠模式）")
            self.main_window.create_analysis_window(clean_name)
        
        elif clean_name in ["Throttle Line Chart", "油門折線圖"]:
            logger.debug(f"[TREE_CLICK] 開啟油門折線圖（模組工廠模式）")
            self.main_window.create_analysis_window(clean_name)
        
        # Ideal Lap Analysis 子模組
        elif clean_name in ["Ideal Lap Ranking Table", "Ranking Table", "排名表格", "理想圈排名"]:
            logger.debug(f"[TREE_CLICK] 開啟理想圈排名表格（模組工廠模式）")
            self.main_window.create_analysis_window(clean_name)
        
        elif clean_name in ["Sector Comparison", "分段對比", "分段比較", "理想圈分段對比"]:
            logger.debug(f"[TREE_CLICK] 開啟理想圈分段對比（模組工廠模式）")
            self.main_window.create_analysis_window(clean_name)
        
        elif clean_name in ["Sector Heat Map", "Sector Heatmap", "分段熱力圖", "セクターヒートマップ"]:
            logger.debug(f"[TREE_CLICK] 開啟理想圈分段熱力圖（模組工廠模式）")
            self.main_window.create_analysis_window(clean_name)
        
        # Straight Speed Analysis 子模組
        elif clean_name in ["All Drivers Speed & Acceleration", "全車手速度與加速", "全車手直線速度"]:
            logger.debug(f"[TREE_CLICK] 開啟全車手直線速度與加速性能分析（模組工廠模式）")
            self.main_window.create_analysis_window(clean_name)
        
        # All Drivers Max Speed 子模組
        elif clean_name in ["All Drivers Max Speed", "全車手最高速度", "全車手最速分析", "最高速度分析"]:
            logger.debug(f"[TREE_CLICK] 開啟全車手最高速度分析（模組工廠模式）")
            self.main_window.create_analysis_window(clean_name)
        
        # All Drivers Acceleration Chart 子模組
        elif clean_name in ["Acceleration Chart", "加速度圖表", "全車手加速度圖表", "速度加速度圖"]:
            logger.debug(f"[TREE_CLICK] 開啟全車手加速度圖表（模組工廠模式）")
            self.main_window.create_analysis_window(clean_name)
        
        elif clean_name in ["All Drivers Brake Performance", "全車手煞車性能", "全車手煞車分析"]:
            logger.debug(f"[TREE_CLICK] 開啟全車手煞車性能分析（模組工廠模式）")
            self.main_window.create_analysis_window(clean_name)
        
        elif clean_name in ["All Drivers Brake All Laps Analysis", "全車手煞車全圈數分析"]:
            logger.debug(f"[TREE_CLICK] 開啟全車手煞車全圈數分析（模組工廠模式）")
            self.main_window.create_analysis_window(clean_name)
        
        # Track Analysis 特殊處理
        elif clean_name in ["Track Analysis", "賽道分析"]:
            logger.debug(f"[TRACK] 檢測到賽道分析請求，使用專門的開啟方法")
            self.main_window.open_track_analysis_window()
        
        # FIA Parts Analysis / 車輛零件變動
        elif clean_name in ["FIA Parts Analysis", "車輛零件變動", "Vehicle Parts Changes", "車両部品変更", "部件分析", "FIA 部件分析", "部品解析"]:
            logger.debug(f"[TREE_CLICK] 開啟 Parts Analysis（模組工廠模式）")
            self.main_window.create_analysis_window(clean_name)
        
        # Season Start Reaction 年度起跑反應分析
        elif clean_name in ["Season Start Reaction", "年度起跑反應", "シーズンスタート反応"]:
            logger.debug(f"[TREE_CLICK] 開啟 Season Start Reaction 模組")
            self.main_window._open_season_start_reaction_module()
        
        # Pole Defense Statistics 桿位防守統計
        elif clean_name in ["Pole Defense Statistics", "桿位防守統計", "ポールディフェンス統計"]:
            logger.debug(f"[TREE_CLICK] 開啟 Pole Defense Statistics 模組")
            self.main_window._open_pole_defense_module()
        
        # Traffic Analysis 車流分析 (Historical 版本，位於 Race Overview)
        elif clean_name in ["Traffic Analysis", "車流分析", "トラフィック分析"]:
            logger.debug(f"[TREE_CLICK] 開啟 Traffic Analysis 模組 (Historical)")
            self.main_window._open_traffic_timeline_module()
        
        # Traffic Timeline 車流時間線 (Live Timing 版本)
        elif clean_name in ["Traffic Timeline", "車流時間線", "トラフィックタイムライン"]:
            logger.debug(f"[TREE_CLICK] 開啟 Live Timing Traffic Timeline 模組")
            self.main_window._open_live_timing_module(clean_name)
        
        else:
            # ========== 檢查是否為 Live Timing 模組 ==========
            try:
                from modules.gui.live_timing import is_live_timing_module
                
                if is_live_timing_module(clean_name):
                    logger.debug(f"[TREE_CLICK] 開啟 Live Timing 模組（工廠模式）: {clean_name}")
                    self.main_window._open_live_timing_module(clean_name)
                else:
                    # 未知模組，使用原有邏輯
                    logger.debug(f"[TREE_CLICK] 使用原有邏輯處理: {clean_name}")
                    self.main_window.create_analysis_window(function_name)
            except ImportError:
                # 如果 live_timing 模組不存在，使用原有邏輯
                logger.debug(f"[TREE_CLICK] 使用原有邏輯處理: {clean_name}")
                self.main_window.create_analysis_window(function_name)
        
    def export_function(self, function_name):
        """匯出單個功能的數據"""
        pass
        
    def show_help(self, function_name):
        """顯示功能說明"""
        pass
