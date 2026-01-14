# -*- coding: utf-8 -*-
"""
TelemetryWindowsGetter - 從 f1t_gui_main.py 提取
"""

from core.logger import get_logger

from core.logger import get_logger
from windows.widgets.custom_mdi_area import CustomMdiArea

logger = get_logger(__name__)


class TelemetryWindowsGetter:
    """從 f1t_gui_main.py 提取的 _get_telemetry_analysis_windows 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _get_telemetry_analysis_windows(self):
        """
        獲取所有需要更新的分析視窗（包含遙測類型和賽事級類型）
        
        Returns:
            list: 分析視窗列表
        """
        logger.info("=" * 80)
        logger.info("[DEBUG] _get_telemetry_analysis_windows() - 開始搜尋視窗")
        logger.debug("=" * 80)
        logger.debug("[DEBUG] _get_telemetry_analysis_windows() - 開始搜尋視窗")
        
        # 定義所有支援的分析類型
        all_analysis_types = {
            # 遙測分析類型
            'speed_analysis',  # 速度分析
            'speed',          # 速度圖表
            'brake',          # 煞車分析
            'throttle',       # 油門分析
            'steering',       # 轉向分析
            'gear',           # 檔位分析
            'rpm',            # RPM分析
            'acceleration',   # 加速度分析
            'speed_diff',     # 速度差分析
            'Speeddiff',      # 速度差分析（大寫變體）
            'distancediff',   # 累積距離差分析
            'Distancediff',   # 累積距離差分析（大寫變體）
            'timediff',       # 累積時間差分析
            'Timediff',       # 累積時間差分析（大寫變體）
            'laptime',        # 詳細圈速分析
            'laptime_boxplot',  # 圈速箱型圖
            'throttle_boxplot',  # 油門箱型圖
            'throttle_line_chart_single_driver',  # 油門折線圖（單車手）
            # 賽事級分析類型
            'rain_weather',   # 天氣分析 (舊名稱，向後相容)
            'temp_weather',   # 溫度分析 (Temperature Analysis)
            'long_run',       # 長距離與輪胎衰退分析 (Long Run Analysis)
            'pitstop',        # 進站分析
            'accident',       # 事故分析
            'tire',           # 輪胎分析
            'ideal_lap',      # 理想圈速分析
            'ideal_lap_ranking',           # 理想圈排名表格
            'ideal_lap_sector_comparison', # 理想圈分段對比
            'ideal_lap_sector_heatmap',    # 理想圈分段熱力圖
            'track_analysis',  # 賽道分析
            'driver_position',  # 車手比賽排名分析 (F25)
            'qualifying_prediction',  # ✅ 排位賽預測 (F74 v3.8) - 新增
            'race_prediction',  # ✅ 正賽預測 (F80) Q → R - 修復參數更新問題
            'all_drivers_straight_line_speed',  # 全車手直線速度分析
            'all_drivers_max_speed',            # 全車手最高速度分析 (F121)
            'all_drivers_acceleration_chart',   # 全車手加速度圖表 (F121)
            'all_drivers_brake_chart',          # 全車手煞車圖表 (F122)
            'all_drivers_brake_performance',    # 全車手煞車性能分析 (F34)
            'all_drivers_brake_all_laps',       # 全車手煞車全圈數分析 (F122)
            'corner_performance',  # 彎道性能分析 (F47) - Low/Mid/High Speed Corners
            'historical_track_map',  # ✅ 歷年賽道旗幟統計 (F100) - 修復參數更新問題
            'traffic_timeline',  # ✅ 車流時間線分析 (F127) - Traffic Analysis
            'pedal_behavior',  # ✅ 油門/煞車行為分析 (F54) - Pedal Behavior Analysis
        }
        
        analysis_windows = []
        seen_ids = set()
        
        logger.debug(f"[DEBUG] 📊 lap_analysis_windows 集合大小: {len(self.main_window.lap_analysis_windows)}")
        logger.info(f"[DEBUG] 📊 lap_analysis_windows 集合大小: {len(self.main_window.lap_analysis_windows)}")
        
        # ✅ 1. 檢查 MDI 視窗（遙測分析）
        logger.info("[DEBUG]    檢查 lap_analysis_windows: %d 個", len(self.main_window.lap_analysis_windows))
        logger.debug(f"[DEBUG] 檢查 lap_analysis_windows: {len(self.main_window.lap_analysis_windows)} 個")
        
        for window in self.main_window.lap_analysis_windows:
            if hasattr(window, 'analysis_type') and window.analysis_type in all_analysis_types:
                # 🔧 修復洩漏: 使用 seen_ids 防止重複添加
                window_id = id(window)
                if window_id not in seen_ids:
                    analysis_windows.append(window)
                    seen_ids.add(window_id)
                    logger.info(f"  ✅ 找到 MDI 視窗: {window.analysis_type} (id={window_id})")
                    logger.debug(f"  ✅ 找到 MDI 視窗: {window.analysis_type} (id={window_id})")
                else:
                    logger.info(f"  ⏭️  跳過重複 MDI 視窗: {window.analysis_type} (id={window_id})")
                    logger.debug(f"  ⏭️  跳過重複 MDI 視窗: {window.analysis_type} (id={window_id})")
        
        # ✅ 2. 檢查 Tab 視窗（賽事級分析）
        logger.info(f"🔵 [DEBUG]    檢查 tab_widget: {self.main_window.tab_widget.count()} 個標籤")
        logger.debug(f"🔵 [DEBUG]    檢查 tab_widget: {self.main_window.tab_widget.count()} 個標籤")
        
        for i in range(self.main_window.tab_widget.count()):
            widget = self.main_window.tab_widget.widget(i)
            tab_text = self.main_window.tab_widget.tabText(i)
            
            # ✅ 跳過 Welcome Tab 和 Home Tab
            if not widget or widget.objectName() in ["welcome_tab", "home_tab"]:
                logger.info(f"  ⏭️  跳過 Tab {i} (Welcome/Home): '{tab_text}'")
                logger.debug(f"  ⏭️  跳過 Tab {i} (Welcome/Home): '{tab_text}'")
                continue
            
            if widget:
                # 🔍 詳細調試：檢查 widget 類型和屬性
                widget_type = type(widget).__name__
                widget_module = type(widget).__module__
                
                logger.info(f"  🔍 Tab {i}: '{tab_text}'")
                logger.info(f"     類型: {widget_type}")
                logger.info(f"     模組: {widget_module}")
                
                # 🔍 檢查 analysis_type 屬性（多層檢查）
                has_analysis_type = hasattr(widget, 'analysis_type')
                logger.info(f"     hasattr(widget, 'analysis_type'): {has_analysis_type}")
                
                if has_analysis_type:
                    analysis_type_value = widget.analysis_type
                    logger.info(f"     Widget.analysis_type = '{analysis_type_value}'")
                else:
                    logger.info(f"     Widget 沒有 analysis_type 屬性")
                    
                    # 🔍 如果是 CustomMdiArea，檢查其子視窗
                    if widget_type == 'CustomMdiArea':
                        logger.info(f"     發現 CustomMdiArea，檢查子視窗...")
                        
                        # 獲取所有子視窗
                        sub_windows = widget.subWindowList()
                        logger.info(f"     子視窗數量: {len(sub_windows)}")
                        
                        for sub_win in sub_windows:
                            # [FIX] 不應該跳過隱藏的視窗！
                            # 隱藏的視窗可能只是在不活動的 Tab 中，它們仍然需要更新
                            # 只跳過真正已關閉的視窗（isVisible() 和 parent() 都為 None）
                            if not sub_win or (hasattr(sub_win, 'parent') and sub_win.parent() is None):
                                logger.info("       ⏭️  跳過已關閉/刪除的子視窗")
                                continue

                            # [DEBUG] 方案A調試：檢查 PopoutSubWindow 屬性
                            sub_win_title = sub_win.windowTitle() if hasattr(sub_win, 'windowTitle') else 'Unknown'
                            sub_win_type = type(sub_win).__name__
                            is_visible = sub_win.isVisible() if hasattr(sub_win, 'isVisible') else 'N/A'
                            logger.debug(f"       [SUB_WIN_CHECK] 檢查子視窗: '{sub_win_title}' (type={sub_win_type}, visible={is_visible})")
                            logger.info(f"       [SUB_WIN_CHECK] 檢查子視窗: '{sub_win_title}' (type={sub_win_type}, visible={is_visible})")
                            
                            # 優先使用 PopoutSubWindow 上綁定的 analysis_module
                            # 🔴 關鍵修復：使用 try-finally 確保 candidate_modules 被清理
                            candidate_modules = []
                            try:
                                analysis_module = getattr(sub_win, 'analysis_module', None)
                                
                                # [DEBUG] 方案A調試：驗證 analysis_module 屬性
                                logger.debug(f"       [SUB_WIN_CHECK] sub_win.analysis_module: {type(analysis_module).__name__ if analysis_module else 'None'}")
                                logger.info(f"       [SUB_WIN_CHECK] sub_win.analysis_module: {type(analysis_module).__name__ if analysis_module else 'None'}")
                                if analysis_module:
                                    module_id = id(analysis_module)
                                    has_type = hasattr(analysis_module, 'analysis_type')
                                    type_value = getattr(analysis_module, 'analysis_type', 'N/A')
                                    logger.debug(f"       [SUB_WIN_CHECK]   - module_id: {module_id}")
                                    logger.debug(f"       [SUB_WIN_CHECK]   - has analysis_type: {has_type}")
                                    logger.debug(f"       [SUB_WIN_CHECK]   - analysis_type value: {type_value}")
                                    logger.info(f"       [SUB_WIN_CHECK]   - module_id: {module_id}, has_type: {has_type}, type: {type_value}")
                                
                                if analysis_module is not None:
                                    candidate_modules.append(analysis_module)
                                    if not hasattr(analysis_module, '_sub_window'):
                                        try:
                                            setattr(analysis_module, '_sub_window', sub_win)
                                        except Exception:  # noqa: BLE001 - 防禦性
                                            pass

                                sub_widget = sub_win.widget()
                                if sub_widget is not None:
                                    candidate_modules.append(sub_widget)

                                    embedded_module = getattr(sub_widget, 'analysis_module', None)
                                    if embedded_module is not None and embedded_module not in candidate_modules:
                                        candidate_modules.append(embedded_module)

                                for candidate in candidate_modules:
                                    if candidate is None:
                                        continue

                                    analysis_type_value = getattr(candidate, 'analysis_type', None)
                                    logger.info(
                                        "       找到子視窗候選: %s (analysis_type=%s)",
                                        type(candidate).__name__,
                                        analysis_type_value,
                                    )

                                    if analysis_type_value in all_analysis_types:
                                        candidate_id = id(candidate)
                                        if candidate_id not in seen_ids:
                                            analysis_windows.append(candidate)
                                            seen_ids.add(candidate_id)
                                            logger.info(
                                                "  ✅ 找到 Tab 視窗 (CustomMdiArea 子視窗): %s",
                                                analysis_type_value,
                                            )
                                            logger.debug(
                                                f"  ✅ 找到 Tab 視窗 (CustomMdiArea 子視窗): {analysis_type_value}"
                                            )
                                        continue
                            finally:
                                # 🔴 強制清理 candidate_modules list，避免 frame 持有引用
                                candidate_modules.clear()
                                candidate_modules = None
                                analysis_module = None
                                sub_widget = None
                                embedded_module = None
                    
                    # 🔍 嘗試檢查基類屬性
                    for base in type(widget).__mro__:
                        logger.info(f"       基類: {base.__name__}")
                        if base.__name__ == 'UniversalAnalysisMDI':
                            logger.info(f"       發現 UniversalAnalysisMDI 基類")
                            break
                
                # ✅ 檢查 widget 本身是否是分析模組
                if hasattr(widget, 'analysis_type'):
                    analysis_type_value = widget.analysis_type
                    logger.info(f"     Widget 有 analysis_type: {analysis_type_value}")
                    logger.debug(f"     [DEBUG] Widget 有 analysis_type: {analysis_type_value}")
                    
                    if analysis_type_value in all_analysis_types:
                        candidate_id = id(widget)
                        if candidate_id not in seen_ids:
                            analysis_windows.append(widget)
                            seen_ids.add(candidate_id)
                            logger.info(f"  ✅ 找到 Tab 視窗 (widget): {analysis_type_value}")
                            logger.debug(f"  ✅ 找到 Tab 視窗 (widget): {analysis_type_value}")
                        else:
                            logger.debug(f"  ⏭️  跳過重複 (widget): {analysis_type_value}")
                        continue
                    else:
                        logger.debug(f"  ⚠️  Widget 的 analysis_type '{analysis_type_value}' 不在 all_analysis_types 中")
                
                # ✅ 檢查是否是 RainAnalysisModuleAdapter 等包裝類型
                # 這些類型的 widget 是通過 get_widget() 返回的
                # 我們需要找到它們的父對象
                if hasattr(widget, 'parent') and widget.parent():
                    parent = widget.parent()
                    # 檢查父對象是否在 active_analysis_tabs 中
                    # 或者檢查父對象是否有 analysis_type
                    if hasattr(parent, 'analysis_type'):
                        analysis_type_value = parent.analysis_type
                        logger.info(f"     父對象有 analysis_type: {analysis_type_value}")
                        
                        if analysis_type_value in all_analysis_types:
                            # 使用父對象（實際的分析模組）
                            candidate_id = id(parent)
                            if candidate_id not in seen_ids:
                                analysis_windows.append(parent)
                                seen_ids.add(candidate_id)
                                logger.info(f"  找到 Tab 視窗 (父對象): {analysis_type_value}")
                            continue
                
                # ✅ 最後的嘗試：檢查 active_analysis_tabs 中的標題
                # 從標題推斷分析類型
                tab_text = self.main_window.tab_widget.tabText(i)
                logger.info(f"     Tab 文字: '{tab_text}'")
                
                # 從 active_analysis_tabs 中查找匹配的標題
                if i < len(self.main_window.active_analysis_tabs):
                    tab_title = self.main_window.active_analysis_tabs[i]
                    logger.info(f"     Tab 標題: '{tab_title}'")
                    
                    # 根據標題推斷類型
                    if 'Rain' in tab_title:
                        # 假設這是 Rain Analysis，添加臨時標記
                        widget.analysis_type = 'rain_weather'
                        candidate_id = id(widget)
                        if candidate_id not in seen_ids:
                            analysis_windows.append(widget)
                            seen_ids.add(candidate_id)
                            logger.info(f"  找到 Tab 視窗 (推斷): rain_weather")
                    elif 'Pitstop' in tab_title:
                        widget.analysis_type = 'pitstop'
                        candidate_id = id(widget)
                        if candidate_id not in seen_ids:
                            analysis_windows.append(widget)
                            seen_ids.add(candidate_id)
                            logger.info(f"  找到 Tab 視窗 (推斷): pitstop")
                    elif 'Accident' in tab_title:
                        widget.analysis_type = 'accident'
                        candidate_id = id(widget)
                        if candidate_id not in seen_ids:
                            analysis_windows.append(widget)
                            seen_ids.add(candidate_id)
                            logger.info(f"  找到 Tab 視窗 (推斷): accident")
                    elif 'Tire' in tab_title:
                        widget.analysis_type = 'tire'
                        candidate_id = id(widget)
                        if candidate_id not in seen_ids:
                            analysis_windows.append(widget)
                            seen_ids.add(candidate_id)
                            logger.info(f"  找到 Tab 視窗 (推斷): tire")
                    elif 'Ideal' in tab_title:
                        widget.analysis_type = 'ideal_lap'
                        candidate_id = id(widget)
                        if candidate_id not in seen_ids:
                            analysis_windows.append(widget)
                            seen_ids.add(candidate_id)
                            logger.info(f"  找到 Tab 視窗 (推斷): ideal_lap")
                    elif 'Track' in tab_title:
                        widget.analysis_type = 'track_analysis'
                        candidate_id = id(widget)
                        if candidate_id not in seen_ids:
                            analysis_windows.append(widget)
                            seen_ids.add(candidate_id)
                            logger.info(f"  找到 Tab 視窗 (推斷): track_analysis")
                    else:
                        logger.info(f"  無法識別 Tab 類型")
        
        logger.debug("=" * 80)
        logger.debug(f"[DEBUG] ✅ 搜尋完成！總共找到 {len(analysis_windows)} 個分析視窗")
        logger.info("=" * 80)
        logger.info(f"[DEBUG] ✅ 搜尋完成！總共找到 {len(analysis_windows)} 個分析視窗")
        
        # 列出所有找到的視窗
        for idx, win in enumerate(analysis_windows):
            win_type = getattr(win, 'analysis_type', 'unknown')
            win_id = id(win)
            win_class = type(win).__name__
            logger.debug(f"  [{idx+1}] {win_type} (class={win_class}, id={win_id})")
            logger.info(f"  [{idx+1}] {win_type} (class={win_class}, id={win_id})")
        
        logger.debug("=" * 80)
        logger.info("=" * 80)
        
        return analysis_windows
