"""
F1T Workspace Serializer
序列化和反序列化 Workspace 配置

版本: 1.0
創建日期: 2025-10-21
"""

from typing import Dict, List, Optional, Tuple, Any
from PyQt5.QtWidgets import QMdiSubWindow, QWidget
from PyQt5.QtCore import Qt

# ✅ 不再需要導入 CustomMdiArea
# 改用主視窗的 create_tab_for_workspace() 方法創建 MDI 區域
# 這樣可以確保使用相同的 CustomMdiArea 類別物件


class WorkspaceSerializer:
    """Workspace 序列化器 - 處理 GUI 狀態與 JSON 之間的轉換"""
    
    # 視窗類型映射（類別名稱 → 類型標識）
    WINDOW_TYPE_MAPPING = {
        # Rain Analysis
        "RainAnalysisModuleAdapter": "rain_analysis",
        "RainAnalysisModule": "rain_analysis",
        
        # Tire Analysis
        "TireAnalysisModuleAdapter": "tire_strategy",
        "TireAnalysisModule": "tire_strategy",
        "TireAnalysisUniversal": "tire_strategy",
        
        # Track Analysis
        "TrackAnalysisUniversal": "track_analysis",
        "TrackAnalysisModule": "track_analysis",
        
        # Accident Analysis
        "AccidentAnalysisModule": "accident_analysis",
        
        # Pitstop Analysis
        "PitstopAnalysisModule": "pitstop_analysis",
        
        # Season Progress
        "SeasonProgressWidget": "season_progress",
        
        # Calendar
        "CalendarWidget": "calendar",
        
        # Ranking Table
        "RankingTableWidget": "ranking_table",
        
        # Lap Analysis
        "LapAnalysisModule": "lap_analysis",
        "driverLapAnalysisMDI": "laptime",           # Detailed Lap Analysis
        "LapTimeBoxPlotAnalysis": "laptime_boxplot", # Lap Time Box Plot
        
        # Speed/Acceleration Analysis
        "SpeedAccelerationModule": "speed_acceleration",
        
        # Brake Analysis
        "BrakeAnalysisModule": "brake_analysis",
        
        # Throttle Analysis
        "ThrottleBoxPlotAnalysis": "throttle_analysis",
        "ThrottleLineChartModule": "throttle_line_chart",
        
        # Ideal Lap Analysis
        "IdealLapRankingTableModule": "ideal_lap_ranking",
        "IdealLapSectorComparisonModule": "ideal_lap_sector_comparison", 
        "IdealLapSectorHeatmapModule": "ideal_lap_sector_heatmap",
        
        # Telemetry Analysis (Lap Analysis)
        # ⚠️ 重要：這些映射必須與模組的 analysis_type 屬性完全匹配
        # 參考：speed_analysis_mdi.py 中的 self.analysis_type = 'speed'
        "SpeedAnalysisModule": "speed",
        "BrakeAnalysisModule": "brake",
        "ThrottleAnalysisModule": "throttle",
        "RPMAnalysisModule": "rpm",
        "accelerationAnalysisModule": "acceleration",
        "GearAnalysisModule": "gear",
        "SpeeddiffAnalysisModule": "Speeddiff",  # 注意：大寫S
        "distancediffAnalysisModule": "distancediff",
        "timediffAnalysisModule": "timediff",
        
        # ============================================================
        # Live Timing 模組 (BaseLiveTimingMDI 子類)
        # ============================================================
        "LiveTimingTrackMap": "live_track_map",
        "LiveTimingCircleMap": "live_circle_map",
        "LiveTimingRankingTower": "live_ranking_tower",
        "LiveTimingPitWindow": "live_pit_window",
        "LiveTimingTyreStrategy": "live_tyre_strategy",
        "LiveTimingDriverStrategy": "live_driver_strategy",
        "LiveTimingLapDistribution": "live_lap_time_distribution",
        "LiveTimingRaceControlMessages": "live_race_control_messages",
        "LiveTimingSpeedTrace": "live_speed_trace",
        "LiveTimingLapHistoryLapTime": "live_lap_history_lap_time",
        "LiveTimingLapHistoryS1": "live_lap_history_s1",
        "LiveTimingLapHistoryS2": "live_lap_history_s2",
        "LiveTimingLapHistoryS3": "live_lap_history_s3",
        "SectorComparisonS1MDI": "live_sector_comparison_s1",
        "SectorComparisonS2MDI": "live_sector_comparison_s2",
        "SectorComparisonS3MDI": "live_sector_comparison_s3",
        "LiveTimingControlPanel": "live_control_panel",
        "BattleInsightMDI": "live_battle_insight",
        "TrackWeatherMDI": "live_track_weather",
        "ChaseStrategyMDI": "live_chase_strategy",
        
        # Gap Evolution Chart (從 Chase Strategy 創建的子視窗)
        "GapEvolutionChartWidget": "gap_evolution_chart",
    }
    
    def __init__(self, main_window):
        """
        初始化序列化器
        
        Args:
            main_window: StyleHMainWindow 實例
        """
        self.main_window = main_window
        # 延遲註冊：暫存 Gap Evolution widgets，等所有視窗載入完成後統一註冊
        self._pending_gap_evolution_widgets = []
    
    # ============================================================================
    # 序列化：GUI → JSON
    # ============================================================================
    
    def serialize_workspace(self) -> Dict:
        """
        將當前 GUI 狀態序列化為 JSON
        
        Returns:
            完整的 Workspace 配置字典
        """
        try:
            config = {
                "version": "1.0",
                "active_tab_index": self.main_window.tab_widget.currentIndex(),
                "tabs": []
            }
            
            # 遍歷所有分頁（排除 HOME）
            for tab_index in range(self.main_window.tab_widget.count()):
                tab_name = self.main_window.tab_widget.tabText(tab_index)
                
                # 跳過 HOME 分頁
                if tab_name == "HOME" or tab_index == 0:
                    continue
                
                tab_config = self._serialize_tab(tab_index, tab_name)
                if tab_config:
                    config["tabs"].append(tab_config)
            
            print(f"[WORKSPACE] ✅ 序列化完成: {len(config['tabs'])} 個分頁")
            return config
            
        except Exception as e:
            print(f"[WORKSPACE] ❌ 序列化失敗: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _serialize_tab(self, tab_index: int, tab_name: str) -> Optional[Dict]:
        """
        序列化單個分頁
        
        Args:
            tab_index: 分頁索引
            tab_name: 分頁名稱
            
        Returns:
            分頁配置字典
        """
        try:
            tab_widget = self.main_window.tab_widget.widget(tab_index)
            
            # 檢查是否為彈出視窗（佔位符）
            is_popped_out = tab_index in self.main_window.popped_out_tabs
            
            tab_config = {
                "tab_index": tab_index,
                "tab_name": tab_name.replace("🔗 ", ""),  # 移除彈出圖標
                "is_popped_out": is_popped_out,
                "mdi_windows": []
            }
            
            # 獲取 MDI 區域
            mdi_area = None
            if is_popped_out:
                # 從彈出視窗追蹤字典獲取 MDI 區域
                popout_info = self.main_window.popped_out_tabs.get(tab_index)
                if popout_info:
                    mdi_area = popout_info['original_widget']
                    # 記錄彈出視窗的幾何資訊
                    standalone_window = popout_info['standalone_window']
                    geometry = standalone_window.geometry()
                    tab_config["popped_window_geometry"] = {
                        "x": geometry.x(),
                        "y": geometry.y(),
                        "width": geometry.width(),
                        "height": geometry.height()
                    }
            else:
                # 從分頁中獲取 MDI 區域
                # CustomMdiArea 定義在 f1t_gui_main.py 中
                from PyQt5.QtWidgets import QMdiArea
                if isinstance(tab_widget, QMdiArea):
                    mdi_area = tab_widget
            
            if not mdi_area:
                print(f"[WORKSPACE] ⚠️ 分頁 {tab_index} 沒有 MDI 區域")
                return tab_config
            
            # 序列化 MDI 視窗
            subwindows = mdi_area.subWindowList()
            for display_order, subwindow in enumerate(subwindows):
                window_config = self._serialize_mdi_window(subwindow, display_order)
                if window_config:
                    tab_config["mdi_windows"].append(window_config)
            
            print(f"[WORKSPACE] 📊 序列化分頁 '{tab_name}': {len(tab_config['mdi_windows'])} 個視窗")
            return tab_config
            
        except Exception as e:
            print(f"[WORKSPACE] ❌ 序列化分頁失敗: {e}")
            return None
    
    def _serialize_mdi_window(self, subwindow: QMdiSubWindow, display_order: int) -> Optional[Dict]:
        """
        序列化單個 MDI 視窗
        
        Args:
            subwindow: QMdiSubWindow 實例
            display_order: 顯示順序
            
        Returns:
            視窗配置字典
        """
        try:
            print(f"[WORKSPACE] 🔍 開始序列化 MDI 視窗")
            print(f"[WORKSPACE]    SubWindow: {subwindow.windowTitle()}")
            print(f"[WORKSPACE]    SubWindow 類型: {subwindow.__class__.__name__}")
            
            # ========== 關鍵修復：從 PopoutSubWindow.analysis_module 獲取模組 ==========
            # 原則 1: 禁止幻覺編碼 - 已驗證 PopoutSubWindow 有 analysis_module 屬性
            # PopoutSubWindow 結構：
            #   - analysis_module: RainAnalysisModuleAdapter (實際模組)
            #   - widget(): UniversalAnalysisMDI.main_widget (UI 容器 QWidget)
            
            window_type = "unknown"
            target_widget = None
            
            # 策略 1: 檢查是否是 PopoutSubWindow 且有 analysis_module
            if hasattr(subwindow, 'analysis_module') and subwindow.analysis_module:
                analysis_module = subwindow.analysis_module
                print(f"[WORKSPACE] ✅ 找到 analysis_module: {analysis_module.__class__.__name__}")
                print(f"[WORKSPACE]    analysis_module 類型: {type(analysis_module)}")
                print(f"[WORKSPACE]    analysis_module 屬性: {[a for a in dir(analysis_module) if not a.startswith('_')][:20]}")
                
                # 從 analysis_module 獲取類型
                if hasattr(analysis_module, 'analysis_type'):
                    window_type = analysis_module.analysis_type
                    print(f"[WORKSPACE] ✅ 直接識別模組類型: '{window_type}' (來自 analysis_module.analysis_type)")
                    target_widget = analysis_module
                else:
                    # 深入搜索
                    print(f"[WORKSPACE] 🔍 analysis_module 沒有 analysis_type，深入搜索")
                    target_widget = self._find_analysis_widget(analysis_module)
                    if target_widget and hasattr(target_widget, 'analysis_type'):
                        window_type = target_widget.analysis_type
                        print(f"[WORKSPACE] ✅ 在子層找到模組類型: {window_type}")
            
            # 策略 2: 備選方案 - 從 widget() 獲取（向後兼容舊代碼）
            else:
                widget = subwindow.widget()
                print(f"[WORKSPACE] ⚠️ SubWindow 沒有 analysis_module，使用 widget() 備選方案")
                print(f"[WORKSPACE]    Widget: {widget.__class__.__name__ if widget else 'None'}")
                
                if not widget:
                    print(f"[WORKSPACE] ⚠️ Widget 為 None，跳過")
                    return None
                
                # 從 widget 搜索
                print(f"[WORKSPACE] 🔍 搜索模組類型 (頂層: {widget.__class__.__name__})")
                target_widget = self._find_analysis_widget(widget)
                
                if target_widget and hasattr(target_widget, 'analysis_type'):
                    window_type = target_widget.analysis_type
                    print(f"[WORKSPACE] ✅ 在子層找到模組類型: {window_type}")
                else:
                    print(f"[WORKSPACE] ⚠️ 未找到 analysis_type 屬性")
            
            # ========== 策略 3: 檢查是否是 Live Timing 模組 ==========
            # 注意：PopoutSubWindow.setWidget() 會包裝原始 widget：
            #   - subwindow.widget() 返回的是 wrapper (QWidget)
            #   - 原始模組保存在 subwindow.content_widget 中
            if window_type == "unknown":
                # 優先檢查 content_widget（這是原始模組）
                content_widget = getattr(subwindow, 'content_widget', None)
                if content_widget:
                    widget_class_name = content_widget.__class__.__name__
                    print(f"[WORKSPACE] 🔍 檢查 content_widget 類名映射: {widget_class_name}")
                    window_type = self.WINDOW_TYPE_MAPPING.get(widget_class_name, "unknown")
                    if window_type != "unknown":
                        print(f"[WORKSPACE] ✅ 使用類名映射: {widget_class_name} → {window_type}")
                        target_widget = content_widget
                    else:
                        print(f"[WORKSPACE] ⚠️ 類名 '{widget_class_name}' 無映射")
                else:
                    # 備選：檢查 widget()（向後兼容）
                    widget = subwindow.widget()
                    if widget:
                        widget_class_name = widget.__class__.__name__
                        print(f"[WORKSPACE] 🔍 檢查 widget() 類名映射: {widget_class_name}")
                        window_type = self.WINDOW_TYPE_MAPPING.get(widget_class_name, "unknown")
                        if window_type != "unknown":
                            print(f"[WORKSPACE] ✅ 使用類名映射: {widget_class_name} → {window_type}")
                        else:
                            print(f"[WORKSPACE] ⚠️ 類名 '{widget_class_name}' 無映射")
            
            # 使用找到的 target_widget（有 data_manager）進行參數提取
            if target_widget is None:
                target_widget = subwindow.widget()
            
            window_config = {
                "window_type": window_type,
                "window_title": subwindow.windowTitle(),
                "is_fixed": subwindow.property("is_welcome_fixed") or False,
                "position": {
                    "x": subwindow.x(),
                    "y": subwindow.y()
                },
                "size": {
                    "width": subwindow.width(),
                    "height": subwindow.height()
                },
                "display_order": display_order,
                "parameters": self._extract_parameters(target_widget),
                "data_file": self._extract_data_file(target_widget)
            }
            
            print(f"[WORKSPACE] 📦 序列化視窗: {window_type} | 參數: {window_config['parameters']}")
            print(f"[WORKSPACE] 🔍 調試信息: 視窗標題='{subwindow.windowTitle()}', 目標widget='{target_widget.__class__.__name__ if target_widget else 'None'}'")
            
            # 🔧 特別調試 Ideal Lap 相關模組
            if "ideal_lap" in window_type:
                print(f"[WORKSPACE] 🎯 IDEAL_LAP_DEBUG: 找到 ideal lap 模組")
                print(f"[WORKSPACE] 🎯 IDEAL_LAP_DEBUG: window_type={window_type}")
                print(f"[WORKSPACE] 🎯 IDEAL_LAP_DEBUG: target_widget 類型={target_widget.__class__.__name__ if target_widget else 'None'}")
                if target_widget and hasattr(target_widget, 'analysis_type'):
                    print(f"[WORKSPACE] 🎯 IDEAL_LAP_DEBUG: analysis_type={target_widget.analysis_type}")
                else:
                    print(f"[WORKSPACE] 🎯 IDEAL_LAP_DEBUG: 沒有 analysis_type 屬性")
                if hasattr(subwindow, 'analysis_module') and subwindow.analysis_module:
                    analysis_module = subwindow.analysis_module
                    print(f"[WORKSPACE] 🎯 IDEAL_LAP_DEBUG: analysis_module 類型={analysis_module.__class__.__name__}")
                    if hasattr(analysis_module, 'analysis_type'):
                        print(f"[WORKSPACE] 🎯 IDEAL_LAP_DEBUG: analysis_module.analysis_type={analysis_module.analysis_type}")
                else:
                    print(f"[WORKSPACE] 🎯 IDEAL_LAP_DEBUG: 沒有 analysis_module")
            return window_config
            
        except Exception as e:
            print(f"[WORKSPACE] ❌ 序列化 MDI 視窗失敗: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _find_analysis_widget(self, root_widget, max_depth: int = 5) -> Optional[Any]:
        """
        遞歸搜索有 analysis_type 並且有參數（current_year 等）的 widget
        
        原則 1: 禁止幻覺編碼 - 已驗證 UniversalAnalysisMDI 有 current_year 等屬性
        
        Args:
            root_widget: 根 widget
            max_depth: 最大遞歸深度
            
        Returns:
            找到的分析 widget（有參數的），或 None
        """
        print(f"[WORKSPACE] 🔍 開始搜索分析 widget（根: {root_widget.__class__.__name__}）")
        
        def search(widget, depth):
            if depth > max_depth:
                print(f"[WORKSPACE]    ⚠️ 達到最大深度 {max_depth}")
                return None
            
            print(f"[WORKSPACE]    檢查深度 {depth}: {widget.__class__.__name__}")
            
            # 優先級 1: 檢查是否有 analysis_type + 參數屬性（最理想）
            if hasattr(widget, 'analysis_type'):
                print(f"[WORKSPACE]    ✅ 找到 analysis_type: {widget.analysis_type}")
                # 檢查是否有參數屬性
                if hasattr(widget, 'current_year') or hasattr(widget, 'current_race'):
                    print(f"[WORKSPACE]    ✅ 有參數屬性，返回此 widget")
                    return widget
                else:
                    print(f"[WORKSPACE]    ⚠️ 沒有參數屬性，繼續搜索")
            
            # 優先級 2: 檢查是否有 _rain_analysis_core（RainAnalysisModule 特有）
            if hasattr(widget, '_rain_analysis_core'):
                print(f"[WORKSPACE]    🔍 發現 _rain_analysis_core，深入檢查")
                core = widget._rain_analysis_core
                # 遞歸檢查 core
                result = search(core, depth + 1)
                if result:
                    return result
            
            # 優先級 3: 檢查是否有 _main_widget（某些 Adapter 特有）
            if hasattr(widget, '_main_widget') and widget._main_widget:
                print(f"[WORKSPACE]    🔍 發現 _main_widget，深入檢查")
                result = search(widget._main_widget, depth + 1)
                if result:
                    return result
            
            # 優先級 4: 檢查是否有 main_widget（UniversalAnalysisMDI 特有）
            if hasattr(widget, 'main_widget') and widget.main_widget:
                print(f"[WORKSPACE]    ⚠️ 發現 main_widget（UI 容器），跳過")
                # main_widget 是 UI 容器，不是我們要的，跳過
                pass
            
            # 優先級 5: 只有 data_manager 也行（最低優先級）
            if hasattr(widget, 'data_manager'):
                print(f"[WORKSPACE]    ✅ 找到 data_manager，返回此 widget")
                return widget
            
            # 優先級 6: 遍歷所有子 widget（使用 findChildren）
            print(f"[WORKSPACE]    🔍 使用 findChildren 搜索子 widget")
            children = widget.findChildren(QWidget)
            print(f"[WORKSPACE]    找到 {len(children)} 個子 widget")
            
            for i, child in enumerate(children[:10]):  # 只顯示前 10 個
                print(f"[WORKSPACE]       子[{i}]: {child.__class__.__name__}")
                if hasattr(child, 'analysis_type') and (hasattr(child, 'current_year') or hasattr(child, 'current_race')):
                    print(f"[WORKSPACE]    ✅ 在子 widget 中找到符合條件的")
                    return child
            
            print(f"[WORKSPACE]    ❌ 深度 {depth} 未找到符合條件的 widget")
            return None
        
        result = search(root_widget, 0)
        if result:
            print(f"[WORKSPACE] ✅ 搜索完成，找到: {result.__class__.__name__}")
        else:
            print(f"[WORKSPACE] ❌ 搜索完成，未找到符合條件的 widget")
        return result
    
    def _extract_parameters(self, widget) -> Dict:
        """
        從 widget 提取參數
        
        原則 1: 禁止幻覺編碼 - 已通過 read_file 驗證 data_manager 屬性存在
        UniversalAnalysisMDI 基類確實有 current_year, current_race, current_session
        
        Args:
            widget: 分析模組 widget
            
        Returns:
            參數字典
        """
        parameters = {}
        
        try:
            # 策略 1: 從 data_manager 提取（最不可靠，通常為空）
            if hasattr(widget, 'data_manager') and widget.data_manager:
                dm = widget.data_manager
                if hasattr(dm, 'year') and dm.year:
                    parameters['year'] = str(dm.year)
                if hasattr(dm, 'race') and dm.race:
                    parameters['race'] = dm.race
                if hasattr(dm, 'session') and dm.session:
                    parameters['session'] = dm.session
                if hasattr(dm, 'driver') and dm.driver:
                    parameters['driver'] = dm.driver
            
            # 策略 2: 直接從 widget 提取（UniversalAnalysisMDI 直接屬性）
            # 原則 1: 已驗證 current_year, current_race, current_session 存在於基類
            if hasattr(widget, 'current_year') and widget.current_year:
                parameters['year'] = str(widget.current_year)
            if hasattr(widget, 'current_race') and widget.current_race:
                parameters['race'] = widget.current_race
            if hasattr(widget, 'current_session') and widget.current_session:
                parameters['session'] = widget.current_session
            
            # 策略 3: 檢查車手參數（某些模組需要）
            if hasattr(widget, 'driver1') and widget.driver1:
                parameters['driver1'] = widget.driver1
            if hasattr(widget, 'driver2') and widget.driver2:
                parameters['driver2'] = widget.driver2
            
            # 策略 4: 檢查圈數參數（某些模組需要）
            if hasattr(widget, 'lap1') and widget.lap1:
                parameters['lap1'] = widget.lap1
            if hasattr(widget, 'lap2') and widget.lap2:
                parameters['lap2'] = widget.lap2
            
            # 策略 5: Gap Evolution Chart 特殊處理
            # Gap Evolution 是從 Chase Strategy 動態創建的子視窗
            if hasattr(widget, 'analysis_type') and widget.analysis_type == 'gap_evolution_chart':
                # 提取 Gap Evolution 特有參數
                if hasattr(widget, 'strategy_id') and widget.strategy_id:
                    parameters['strategy_id'] = widget.strategy_id
                if hasattr(widget, 'p1_tla') and widget.p1_tla:
                    parameters['p1_tla'] = widget.p1_tla
                if hasattr(widget, 'p2_tla') and widget.p2_tla:
                    parameters['p2_tla'] = widget.p2_tla
                if hasattr(widget, 'current_lap'):
                    parameters['current_lap'] = widget.current_lap
                if hasattr(widget, 'current_gap'):
                    parameters['current_gap'] = widget.current_gap
                if hasattr(widget, 'total_laps'):
                    parameters['total_laps'] = widget.total_laps
                if hasattr(widget, 'p1_color'):
                    parameters['p1_color'] = widget.p1_color
                if hasattr(widget, 'p2_color'):
                    parameters['p2_color'] = widget.p2_color
                if hasattr(widget, 'p1_compound'):
                    parameters['p1_compound'] = widget.p1_compound
                if hasattr(widget, 'p2_compound'):
                    parameters['p2_compound'] = widget.p2_compound
                print(f"[WORKSPACE] 📊 Gap Evolution 參數提取: strategy_id={parameters.get('strategy_id')}, p1={parameters.get('p1_tla')}, p2={parameters.get('p2_tla')}")
            
            # 清理 None 值和空字符串
            parameters = {k: v for k, v in parameters.items() if v is not None and v != ""}
            
            print(f"[WORKSPACE] 📊 提取參數成功: {parameters}")
            
        except Exception as e:
            print(f"[WORKSPACE] ⚠️ 提取參數失敗: {e}")
            import traceback
            traceback.print_exc()
        
        return parameters
    
    def _extract_data_file(self, widget) -> Optional[str]:
        """
        從 widget 提取資料檔案路徑
        
        Args:
            widget: 分析模組 widget
            
        Returns:
            資料檔案路徑（相對路徑）
        """
        try:
            if hasattr(widget, 'data_manager') and hasattr(widget.data_manager, 'current_json_file'):
                return widget.data_manager.current_json_file
            elif hasattr(widget, 'current_json_file'):
                return widget.current_json_file
        except:
            pass
        
        return None
    
    # ============================================================================
    # 統計資訊提取
    # ============================================================================
    
    def extract_statistics(self, config: Dict) -> Dict:
        """
        從配置中提取統計資訊
        
        Args:
            config: Workspace 配置字典
            
        Returns:
            統計資訊字典
        """
        statistics = {
            "total_tabs": len(config.get("tabs", [])),
            "total_windows": 0,
            "window_types": {},
            "parameters": {}
        }
        
        for tab in config.get("tabs", []):
            windows = tab.get("mdi_windows", [])
            statistics["total_windows"] += len(windows)
            
            for window in windows:
                # 統計視窗類型
                window_type = window.get("window_type", "unknown")
                statistics["window_types"][window_type] = statistics["window_types"].get(window_type, 0) + 1
                
                # 收集參數
                params = window.get("parameters", {})
                for key, value in params.items():
                    if key not in statistics["parameters"]:
                        statistics["parameters"][key] = []
                    if value not in statistics["parameters"][key]:
                        statistics["parameters"][key].append(value)
        
        return statistics
    
    # ============================================================================
    # 反序列化：JSON → GUI（在下一個檔案中實現，避免檔案過大）
    # ============================================================================
    
    def deserialize_workspace(self, config: Dict) -> bool:
        """
        從 JSON 恢復 Workspace
        
        重建所有分頁和視窗，恢復完整的 GUI 狀態
        
        Args:
            config: Workspace 配置字典
            
        Returns:
            是否恢復成功
        """
        try:
            print(f"[WORKSPACE] 🔄 開始反序列化 Workspace...")
            
            # 步驟 1: 清除當前分頁（除 HOME）
            self._clear_existing_tabs()
            
            # 步驟 2: 遍歷配置中的分頁
            tabs_config = config.get('tabs', [])
            print(f"[WORKSPACE] 📊 需要重建 {len(tabs_config)} 個分頁")
            
            for tab_config in tabs_config:
                success = self._rebuild_tab(tab_config)
                if not success:
                    print(f"[WORKSPACE] ⚠️ 分頁 '{tab_config.get('tab_name')}' 重建失敗")
            
            # 步驟 3: 恢復活動分頁
            active_tab_index = config.get('active_tab_index', 0)
            print(f"[WORKSPACE] [DEBUG] 準備設定活動分頁: index={active_tab_index}, 總分頁數={self.main_window.tab_widget.count()}")
            
            if active_tab_index < self.main_window.tab_widget.count():
                self.main_window.tab_widget.setCurrentIndex(active_tab_index)
                print(f"[WORKSPACE] ✅ 已設定活動分頁: index={active_tab_index}")
                
                # ✅ 關鍵修正：分頁切換後，確保所有 MDI 視窗可見
                current_widget = self.main_window.tab_widget.widget(active_tab_index)
                print(f"[WORKSPACE] [DEBUG] 當前 widget 類型: {type(current_widget).__name__}")
                print(f"[WORKSPACE] [DEBUG] 是否有 subWindowList: {hasattr(current_widget, 'subWindowList')}")
                
                if hasattr(current_widget, 'subWindowList'):
                    try:
                        subwindows = current_widget.subWindowList()
                        print(f"[WORKSPACE] 🔍 檢查活動分頁的 {len(subwindows)} 個子視窗可見性")
                        for subwindow in subwindows:
                            window_title = subwindow.windowTitle()
                            is_visible = subwindow.isVisible()
                            print(f"[WORKSPACE] [DEBUG] 視窗 '{window_title}' 可見性: {is_visible}")
                            
                            if not is_visible:
                                print(f"[WORKSPACE] 👁️ 調用 show() 顯示隱藏的視窗: {window_title}")
                                subwindow.show()
                                # 再次檢查
                                print(f"[WORKSPACE] [DEBUG] show() 後可見性: {subwindow.isVisible()}")
                            else:
                                print(f"[WORKSPACE] ✅ 視窗已可見: {window_title}")
                    except Exception as ex:
                        print(f"[WORKSPACE] ❌ 檢查/顯示視窗時出錯: {ex}")
                        import traceback
                        traceback.print_exc()
                else:
                    print(f"[WORKSPACE] ❌ 當前 widget 沒有 subWindowList 方法")
            
            # ✅ 所有視窗載入完成後，統一註冊 Gap Evolution widgets
            self._register_pending_gap_evolution_widgets()
            
            print(f"[WORKSPACE] ✅ Workspace 反序列化完成！")
            return True
            
        except Exception as e:
            print(f"[WORKSPACE] ❌ 反序列化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _clear_existing_tabs(self):
        """清除當前所有分頁（除 HOME）"""
        try:
            tab_count = self.main_window.tab_widget.count()
            # 從後往前刪除（避免索引變化）
            for i in range(tab_count - 1, 0, -1):  # 跳過 index 0 (HOME)
                tab_name = self.main_window.tab_widget.tabText(i)
                print(f"[WORKSPACE] 🗑️ 移除分頁: {tab_name} (index={i})")
                self.main_window.tab_widget.removeTab(i)
            
            print(f"[WORKSPACE] ✅ 已清除所有分頁（保留 HOME）")
            
        except Exception as e:
            print(f"[WORKSPACE] ❌ 清除分頁失敗: {e}")
    
    def _rebuild_tab(self, tab_config: Dict) -> bool:
        """
        重建單個分頁
        
        Args:
            tab_config: 分頁配置
            
        Returns:
            是否成功
        """
        try:
            tab_name = tab_config.get('tab_name', 'Analysis')
            mdi_windows_config = tab_config.get('mdi_windows', [])
            
            print(f"[WORKSPACE] 🔨 重建分頁: '{tab_name}' ({len(mdi_windows_config)} 個視窗)")
            
            # ✅ 使用主視窗的方法創建分頁，確保 CustomMdiArea 類別物件一致
            # 這樣創建的 MDI 區域與使用者手動創建的完全相同
            mdi_area = self.main_window.create_tab_for_workspace(tab_name)
            
            # 獲取分頁索引（用於調試）
            tab_index = self.main_window.tab_widget.count() - 1
            
            # [深度調試] 驗證分頁和 MDI 創建
            print(f"[WORKSPACE] [DEBUG] ===== 分頁創建驗證 =====")
            print(f"[WORKSPACE] [DEBUG] 分頁名稱: {tab_name}")
            print(f"[WORKSPACE] [DEBUG] 分頁索引: {tab_index}")
            print(f"[WORKSPACE] [DEBUG] MDI ObjectName: {mdi_area.objectName()}")
            print(f"[WORKSPACE] [DEBUG] MDI 類型: {type(mdi_area).__name__}")
            
            # ✅ 不再需要檢查類別 ID，因為現在使用主視窗的方法創建
            # 保證是同一個 CustomMdiArea 類別物件
            
            # 驗證 tab_widget 能否取得該分頁
            retrieved_tab = self.main_window.tab_widget.widget(tab_index)
            print(f"[WORKSPACE] [DEBUG] 取回的分頁 ObjectName: {retrieved_tab.objectName()}")
            print(f"[WORKSPACE] [DEBUG] 取回的分頁類型: {type(retrieved_tab).__name__}")
            print(f"[WORKSPACE] [DEBUG] 取回的分頁 == mdi_area: {retrieved_tab is mdi_area}")
            print(f"[WORKSPACE] [DEBUG] ================================")
            
            # ✅ 不需要追蹤 MDI 區域，因為 create_tab_for_workspace() 已經追蹤了
            print(f"[WORKSPACE] 📌 MDI 區域已由 create_tab_for_workspace() 追蹤")
            
            # 重建每個 MDI 視窗
            # ✅ 加入延遲避免 API 429 錯誤
            import time
            for window_index, window_config in enumerate(mdi_windows_config):
                print(f"[WORKSPACE] 🔨 重建視窗 {window_index + 1}/{len(mdi_windows_config)}")
                
                # ✅ 在每個視窗之間加入延遲（避免 API 限流）
                if window_index > 0:
                    delay_ms = 500  # 500ms 延遲
                    print(f"[WORKSPACE] ⏱️ 延遲 {delay_ms}ms 避免 API 限流...")
                    time.sleep(delay_ms / 1000.0)
                
                try:
                    self._rebuild_mdi_window(mdi_area, window_config)
                except Exception as e:
                    # ✅ 單個視窗失敗不影響其他視窗
                    print(f"[WORKSPACE] ⚠️ 視窗重建失敗，繼續處理下一個: {e}")
                    import traceback
                    traceback.print_exc()
            
            return True
            
        except Exception as e:
            print(f"[WORKSPACE] ❌ 重建分頁失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _rebuild_mdi_window(self, mdi_area, window_config: Dict) -> bool:
        """
        重建單個 MDI 視窗 - 與手動開啟完全一致的流程
        
        ✅ 修改目標：與手動開啟 (create_analysis_window) 完全相同
        - 參數來源：從主視窗 GUI 實時獲取（不再使用配置 JSON）
        - 參數獲取：使用 parameter_provider（不再使用 parameters.get()）
        - 標題生成：動態調用 get_window_title()（不再使用配置中的 window_title）
        - 尺寸設定：使用 analysis_module.get_default_size()（不再使用配置 size）
        - 位置設定：調用 _position_subwindow() 自動計算（不再使用配置 position）
        - 信號連接：連接 window_closed 信號
        - 追蹤列表：添加到 active_subwindows
        
        Args:
            mdi_area: MDI 區域
            window_config: 視窗配置（只用於獲取 window_type）
            
        Returns:
            是否成功
        """
        try:
            print(f"[WORKSPACE] ========== 開始重建 MDI 視窗（與手動開啟一致） ==========")
            
            # 步驟 1: 獲取視窗類型（這是唯一從配置讀取的信息）
            window_type = window_config.get('window_type', 'unknown')
            window_title = window_config.get('window_title', '')
            print(f"[WORKSPACE] 📋 視窗類型: {window_type}, 標題: {window_title}")
            
            # ========================================================
            # 步驟 1.2: 從 window_title 推斷 Live Timing 類型（處理舊數據）
            # ========================================================
            if window_type == 'unknown' and window_title:
                # Live Timing 標題 → 類型映射
                title_to_type_map = {
                    "Track Map": "live_track_map",
                    "Circle Map": "live_circle_map",
                    "Live Ranking": "live_ranking_tower",
                    "live_ranking_tower": "live_ranking_tower",  # 舊格式標題
                    "Pit Window": "live_pit_window",
                    "Tyre Strategy": "live_tyre_strategy",
                    "Driver Strategy": "live_driver_strategy",
                    "Lap Time Distribution": "live_lap_time_distribution",
                    "Race Control Messages": "live_race_control_messages",
                    "Speed Trace": "live_speed_trace",
                    "Lap History - Lap Time": "live_lap_history_lap_time",
                    "Lap History - S1": "live_lap_history_s1",
                    "Lap History - S2": "live_lap_history_s2",
                    "Lap History - S3": "live_lap_history_s3",
                    "S1 Comparison": "live_sector_comparison_s1",
                    "S2 Comparison": "live_sector_comparison_s2",
                    "S3 Comparison": "live_sector_comparison_s3",
                    "Sector Comparison - S1": "live_sector_comparison_s1",
                    "Sector Comparison - S2": "live_sector_comparison_s2",
                    "Sector Comparison - S3": "live_sector_comparison_s3",
                    "Control Panel": "live_control_panel",
                    "Battle Insight": "live_battle_insight",
                    "Track & Weather": "live_track_weather",
                    "Chase Strategy": "live_chase_strategy",
                }
                
                inferred_type = title_to_type_map.get(window_title)
                if inferred_type:
                    print(f"[WORKSPACE] 🔄 從標題推斷類型: '{window_title}' → '{inferred_type}'")
                    window_type = inferred_type
                    # 更新 window_config 以便傳遞給 _rebuild_live_timing_window
                    window_config = dict(window_config)  # 創建副本避免修改原始數據
                    window_config['window_type'] = window_type
            
            # ========================================================
            # 步驟 1.5: 檢查是否為 Gap Evolution Chart
            # Gap Evolution 是 Chase Strategy 的動態子視窗
            # 策略：先創建空視窗，等 Live Timing 播放時透過即時更新機制刷新
            # ========================================================
            if window_type == 'gap_evolution_chart':
                print(f"[WORKSPACE] 🎬 重建 Gap Evolution Chart 視窗...")
                return self._rebuild_gap_evolution_window(mdi_area, window_config)
            
            # ========================================================
            # 步驟 1.6: 檢查是否為 Live Timing 模組
            # ========================================================
            if window_type.startswith('live_'):
                print(f"[WORKSPACE] 🎬 檢測到 Live Timing 模組，使用專用工廠...")
                return self._rebuild_live_timing_window(mdi_area, window_config)
            
            # 步驟 2: 使用與手動開啟完全相同的模組創建方法
            # ✅ 關鍵：調用主視窗的 _create_analysis_module() 方法
            # 這會確保：
            # - 使用 parameter_provider 從主視窗實時獲取參數
            # - 調用 API 而非讀取 JSON
            # - 與手動開啟完全相同的初始化流程
            print(f"[WORKSPACE] 🔧 調用主視窗的 _create_analysis_module() 方法...")
            analysis_module = self.main_window._create_analysis_module(
                window_type,  # 使用 window_type 作為 function_name
                module_type_hint=window_type  # 提供類型提示
            )
            
            if not analysis_module:
                print(f"[WORKSPACE] ❌ 無法創建模組: type={window_type}")
                return False
            
            print(f"[WORKSPACE] ✅ 模組創建成功: {analysis_module.__class__.__name__}")
            
            # 步驟 3: 動態生成視窗標題（與手動開啟一致）
            # ✅ 從主視窗 GUI 實時獲取當前參數
            current_year = self.main_window.year_combo.currentText()
            current_race = self.main_window.race_combo.currentText()
            current_session = self.main_window.session_combo.currentText()
            
            # 清理 race 名稱（移除日期後綴）
            clean_race = self.main_window._get_race_key_from_display(current_race)
            print(f"[WORKSPACE] 📊 當前參數: {current_year} {clean_race} {current_session}")
            
            # 動態生成標題
            if hasattr(analysis_module, 'get_window_title'):
                window_title = analysis_module.get_window_title(
                    current_year,
                    clean_race,
                    current_session
                )
                print(f"[WORKSPACE] 🏷️ 動態生成標題: '{window_title}'")
            else:
                window_title = analysis_module.get_title()
                print(f"[WORKSPACE] 🏷️ 使用預設標題: '{window_title}'")
            
            # 步驟 4: 創建 PopoutSubWindow（與手動開啟一致）
            from f1t_gui_main import PopoutSubWindow
            
            # [DEBUG] 方案A調試：驗證傳入參數
            print(f"[WORKSPACE] [DEBUG] 準備創建 PopoutSubWindow:")
            print(f"[WORKSPACE] [DEBUG]   - window_title: '{window_title}'")
            print(f"[WORKSPACE] [DEBUG]   - mdi_area: {type(mdi_area).__name__}")
            print(f"[WORKSPACE] [DEBUG]   - analysis_module: {type(analysis_module).__name__}")
            print(f"[WORKSPACE] [DEBUG]   - analysis_module.id: {id(analysis_module)}")
            if hasattr(analysis_module, 'analysis_type'):
                print(f"[WORKSPACE] [DEBUG]   - analysis_module.analysis_type: {analysis_module.analysis_type}")
            
            analysis_window = PopoutSubWindow(window_title, mdi_area, analysis_module)
            print(f"[WORKSPACE] 📦 PopoutSubWindow 已創建")
            
            # [DEBUG] 方案A調試：驗證創建後的屬性
            print(f"[WORKSPACE] [DEBUG] PopoutSubWindow 創建後驗證:")
            print(f"[WORKSPACE] [DEBUG]   - analysis_window.analysis_module: {type(analysis_window.analysis_module).__name__ if analysis_window.analysis_module else 'None'}")
            if analysis_window.analysis_module:
                print(f"[WORKSPACE] [DEBUG]   - stored module id: {id(analysis_window.analysis_module)}")
                if hasattr(analysis_window.analysis_module, 'analysis_type'):
                    print(f"[WORKSPACE] [DEBUG]   - stored module type: {analysis_window.analysis_module.analysis_type}")

            
            # 步驟 5: 設置模組 widget（與手動開啟一致）
            content_widget = analysis_module.get_widget()
            analysis_window.setWidget(content_widget)
            print(f"[WORKSPACE] 🎨 Widget 已設置")
            
            # ✅ 步驟 5.5: 設置 parent_window 引用（讓模組能更新標題）
            print(f"[WORKSPACE] 🔍 檢查 set_parent_window 方法...")
            print(f"[WORKSPACE]    - 模組類型: {type(analysis_module).__name__}")
            print(f"[WORKSPACE]    - hasattr(analysis_module, 'set_parent_window'): {hasattr(analysis_module, 'set_parent_window')}")
            
            if hasattr(analysis_module, 'set_parent_window'):
                analysis_module.set_parent_window(analysis_window)
                print(f"[WORKSPACE] 🔗 已設置 parent_window 引用")
            else:
                print(f"[WORKSPACE] ⚠️  模組沒有 set_parent_window 方法")
                # 檢查是否有內部的 MDI 實例
                if hasattr(analysis_module, '_rain_analysis_core'):
                    print(f"[WORKSPACE] 🔍 發現 _rain_analysis_core 屬性")
                    core = analysis_module._rain_analysis_core
                    if core and hasattr(core, 'set_parent_window'):
                        core.set_parent_window(analysis_window)
                        print(f"[WORKSPACE] 🔗 已在 _rain_analysis_core 設置 parent_window")
            
            # 步驟 6: 恢復視窗尺寸（優先使用保存的尺寸，否則使用預設）
            saved_size = window_config.get('size', {})
            saved_width = saved_size.get('width')
            saved_height = saved_size.get('height')
            
            if saved_width and saved_height:
                width, height = saved_width, saved_height
                print(f"[WORKSPACE] 📏 使用保存的尺寸: {width}x{height}")
            else:
                width, height = analysis_module.get_default_size()
                print(f"[WORKSPACE] 📏 使用預設尺寸: {width}x{height}")
            
            analysis_window.resize(width, height)
            
            # 步驟 7: 添加到 MDI（與手動開啟一致）
            mdi_area.addSubWindow(analysis_window)
            print(f"[WORKSPACE] ✅ 已添加到 MDI 區域")
            
            # 步驟 8: 連接關閉信號（與手動開啟一致）
            if hasattr(analysis_window, 'window_closed'):
                analysis_window.window_closed.connect(
                    lambda: self.main_window.on_subwindow_closed(analysis_window)
                )
                print(f"[WORKSPACE] 🔗 已連接 window_closed 信號")
            
            # 步驟 9: 添加到追蹤列表（與手動開啟一致）
            if hasattr(self.main_window, 'active_subwindows'):
                self.main_window.active_subwindows.append(analysis_window)
                print(f"[WORKSPACE] 📋 已添加到 active_subwindows 追蹤列表")
            
            # 步驟 10: 顯示視窗（與手動開啟一致）
            analysis_window.show()
            print(f"[WORKSPACE] 👁️ 視窗已顯示")
            
            # 🔧 重要：show() 後再次設定尺寸，避免被 Qt 自動調整覆蓋
            if saved_width and saved_height:
                analysis_window.resize(saved_width, saved_height)
            
            # 步驟 11: 恢復視窗位置（優先使用保存的位置，否則自動計算）
            saved_position = window_config.get('position', {})
            saved_x = saved_position.get('x')
            saved_y = saved_position.get('y')
            
            if saved_x is not None and saved_y is not None:
                # 使用保存的位置
                analysis_window.move(saved_x, saved_y)
                print(f"[WORKSPACE] 📍 使用保存的位置: ({saved_x}, {saved_y})")
            else:
                # 自動計算位置避免重疊
                self.main_window._position_subwindow(mdi_area, analysis_window)
                print(f"[WORKSPACE] 📍 位置已自動計算")
            
            # 步驟 12: 為所有分析模組設置 analysis_type 屬性
            # ✅ 關鍵修復：確保所有模組都能被 _get_telemetry_analysis_windows() 檢測到
            print(f"[WORKSPACE] 🏷️ 為模組設置 analysis_type 屬性: {window_type}")
            print(f"[WORKSPACE] [DEBUG] 模組類型: {type(analysis_module).__name__}")
            print(f"[WORKSPACE] [DEBUG] 模組 ID: {id(analysis_module)}")
            
            # 設置 analysis_type 到模組
            if not hasattr(analysis_module, 'analysis_type'):
                analysis_module.analysis_type = window_type
                print(f"[WORKSPACE] ✅ 已設置 analysis_module.analysis_type = '{window_type}'")
            else:
                print(f"[WORKSPACE] ℹ️  模組已有 analysis_type = '{analysis_module.analysis_type}'")
            
            # 驗證設置是否成功
            verify_type = getattr(analysis_module, 'analysis_type', None)
            print(f"[WORKSPACE] [VERIFY] 驗證 analysis_type = '{verify_type}'")
            
            # 步驟 13: 註冊遙測分析視窗（如果是遙測模組）
            # ✅ 關鍵修復：確保工具欄控制項顯示
            lap_analysis_types = [
                "speed_analysis", "speed", 
                "rpm_analysis", "rpm",
                "acceleration_analysis", "acceleration",
                "speeddiff_analysis", "Speeddiff", "speed_diff",
                "distancediff_analysis", "distancediff", "distance_diff",
                "timediff_analysis", "timediff", "time_diff",
                "brake_analysis", "brake",
                "throttle_analysis", "throttle",
                "gear_analysis", "gear"
            ]
            
            if window_type in lap_analysis_types:
                print(f"[WORKSPACE] 🎯 檢測到遙測分析模組，註冊到主視窗...")
                # 調用 on_lap_analysis_window_opened 以顯示工具欄控制項
                if hasattr(self.main_window, 'on_lap_analysis_window_opened'):
                    self.main_window.on_lap_analysis_window_opened(analysis_module, window_type)
                    print(f"[WORKSPACE] ✅ 遙測分析視窗已註冊: {window_type}")
                else:
                    print(f"[WORKSPACE] ⚠️ 主視窗沒有 on_lap_analysis_window_opened 方法")
            
            print(f"[WORKSPACE] ========== MDI 視窗重建完成 ==========")
            print(f"[WORKSPACE] ✅ 視窗已重建: '{window_title}'")
            print(f"[WORKSPACE] 📊 使用當前主視窗參數: {current_year} {clean_race} {current_session}")
            print(f"[WORKSPACE] 🔄 此視窗將調用 API 載入數據（不使用 JSON 緩存）")
            
            return True
            
        except Exception as e:
            print(f"[WORKSPACE] ❌ 重建視窗失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _rebuild_gap_evolution_window(self, mdi_area, window_config: Dict) -> bool:
        """
        重建 Gap Evolution MDI 視窗
        
        Gap Evolution 是 Chase Strategy 的動態子視窗。
        策略：使用保存的參數創建視窗，等 Live Timing 播放時透過即時更新機制刷新。
        
        Args:
            mdi_area: MDI 區域
            window_config: 視窗配置
            
        Returns:
            是否成功
        """
        try:
            from f1t_gui_main import PopoutSubWindow
            from modules.gui.live_timing.live_timing_modules.chase_strategy import GapEvolutionChartWidget, StrategyResult
            
            params = window_config.get('parameters', {})
            window_title = window_config.get('window_title', 'Gap Evolution')
            
            print(f"[WORKSPACE] 🎬 重建 Gap Evolution 視窗: {window_title}")
            print(f"[WORKSPACE] 📊 參數: {params}")
            
            # 提取參數
            strategy_id = params.get('strategy_id', 1)
            p1_tla = params.get('p1_tla', 'P1')
            p2_tla = params.get('p2_tla', 'P2')
            current_lap = params.get('current_lap', 1)
            current_gap = params.get('current_gap', 0.0)
            total_laps = params.get('total_laps', 58)
            p1_color = params.get('p1_color', '#3671C6').lstrip('#')
            p2_color = params.get('p2_color', '#FF8800').lstrip('#')
            p1_compound = params.get('p1_compound', '--')
            p2_compound = params.get('p2_compound', '--')
            
            # 創建一個最小化的 StrategyResult（用於初始化）
            # 實際數據會在 Live Timing 播放時透過即時更新機制刷新
            class MinimalStrategy:
                def __init__(self, strategy_id, name):
                    self.strategy_id = strategy_id
                    self.name = name
                    self.feasible = True
                    self.gap_evolution = []  # 空的演變數據，等待更新
                    # GapEvolutionChartWidget 需要的屬性
                    self.advantage_per_lap = 0.0  # 每圈優勢（秒）
                    self.pit_stop_loss = 20.0  # 進站損失（秒）
                    self.pit_loss = 20.0  # 進站損失（秒）- 別名
                    self.sc_lap_offset = 5  # 安全車圈數偏移
                    self.pit_lap = None  # 進站圈數
                    self.catchup_lap = None  # 追上圈數
                    self.final_gap = current_gap  # 最終 Gap
                    self.total_laps = total_laps
            
            minimal_strategy = MinimalStrategy(strategy_id, window_title.replace(" - Gap Evolution", ""))
            
            # 創建 Gap Evolution Widget
            chart_widget = GapEvolutionChartWidget(
                strategy=minimal_strategy,
                current_lap=current_lap,
                current_gap=current_gap,
                total_laps=total_laps,
                p1_tla=p1_tla,
                p2_tla=p2_tla,
                p1_color=p1_color,
                p2_color=p2_color,
                active_pit_lap=None,
                p1_compound=p1_compound,
                p2_compound=p2_compound,
                strategy_id=strategy_id
            )
            
            print(f"[WORKSPACE] ✅ Gap Evolution Widget 創建成功")
            
            # 創建 PopoutSubWindow
            sub_window = PopoutSubWindow(
                window_title,
                mdi_area,
                analysis_module=None,
                sync_enabled=False
            )
            sub_window.setWidget(chart_widget)
            
            # 恢復尺寸
            saved_size = window_config.get('size', {})
            saved_width = saved_size.get('width', 900)
            saved_height = saved_size.get('height', 600)
            sub_window.resize(saved_width, saved_height)
            print(f"[WORKSPACE] 📏 使用保存的尺寸: {saved_width}x{saved_height}")
            
            # 添加到 MDI 區域
            mdi_area.addSubWindow(sub_window)
            sub_window.show()
            
            # 恢復位置
            saved_position = window_config.get('position', {})
            saved_x = saved_position.get('x')
            saved_y = saved_position.get('y')
            
            if saved_x is not None and saved_y is not None:
                sub_window.move(saved_x, saved_y)
                print(f"[WORKSPACE] 📍 使用保存的位置: ({saved_x}, {saved_y})")
            
            # 🔍 延遲註冊：暫存到列表，等所有視窗載入完成後再統一註冊
            # ⚠️ 原因：Gap Evolution 可能比 Chase Strategy 更早載入
            self._pending_gap_evolution_widgets.append(chart_widget)
            print(f"[WORKSPACE] 📋 Gap Evolution 已暫存，等待所有視窗載入完成後註冊")
            
            print(f"[WORKSPACE] ✅ Gap Evolution 視窗重建完成")
            return True
            
        except Exception as e:
            print(f"[WORKSPACE] ❌ 重建 Gap Evolution 視窗失敗: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _register_pending_gap_evolution_widgets(self):
        """
        統一註冊所有暫存的 Gap Evolution widgets
        
        在所有視窗載入完成後調用，確保 Chase Strategy 已經存在
        """
        if not self._pending_gap_evolution_widgets:
            return
        
        print(f"[WORKSPACE] 🔗 開始註冊 {len(self._pending_gap_evolution_widgets)} 個 Gap Evolution widgets...")
        
        # 搜索所有分頁中的 Chase Strategy MDI
        chase_strategy_mdi = None
        
        if hasattr(self.main_window, 'tab_widget'):
            print(f"[WORKSPACE] 🔍 搜索 Chase Strategy MDI，分頁數量: {self.main_window.tab_widget.count()}")
            for tab_index in range(self.main_window.tab_widget.count()):
                tab_widget = self.main_window.tab_widget.widget(tab_index)
                tab_name = self.main_window.tab_widget.tabText(tab_index)
                print(f"[WORKSPACE] 📂 檢查分頁 '{tab_name}' (index={tab_index})")
                
                if hasattr(tab_widget, 'subWindowList'):
                    sub_windows = tab_widget.subWindowList()
                    print(f"[WORKSPACE]   - 此分頁有 {len(sub_windows)} 個子視窗")
                    
                    for sub_win in sub_windows:
                        # ✅ 修復：優先從 content_widget 獲取實際模組
                        # PopoutSubWindow.widget() 返回包裝後的 QWidget
                        # PopoutSubWindow.content_widget 才是實際的模組 (ChaseStrategyMDI)
                        actual_widget = None
                        if hasattr(sub_win, 'content_widget') and sub_win.content_widget:
                            actual_widget = sub_win.content_widget
                            print(f"[WORKSPACE]   - 使用 content_widget: {actual_widget.__class__.__name__}")
                        else:
                            actual_widget = sub_win.widget()
                            if actual_widget:
                                print(f"[WORKSPACE]   - 使用 widget(): {actual_widget.__class__.__name__}")
                        
                        if actual_widget and hasattr(actual_widget, '__class__'):
                            class_name = actual_widget.__class__.__name__
                            window_title = sub_win.windowTitle() if hasattr(sub_win, 'windowTitle') else 'Unknown'
                            print(f"[WORKSPACE]   - 檢查視窗: {class_name} (標題: {window_title})")
                            
                            if class_name == 'ChaseStrategyMDI':
                                chase_strategy_mdi = actual_widget
                                print(f"[WORKSPACE] ✅ 在分頁 '{tab_name}' 找到 Chase Strategy MDI")
                                break
                        else:
                            print(f"[WORKSPACE]   - 跳過無效的 widget")
                    if chase_strategy_mdi:
                        break
                else:
                    print(f"[WORKSPACE]   - 此分頁沒有 subWindowList 方法 (類型: {type(tab_widget).__name__})")
        
        if chase_strategy_mdi and hasattr(chase_strategy_mdi, '_widget'):
            chase_widget = chase_strategy_mdi._widget
            
            # 確保追蹤列表存在
            if not hasattr(chase_widget, '_gap_evolution_widgets'):
                chase_widget._gap_evolution_widgets = []
            
            # 註冊所有暫存的 widgets
            from functools import partial
            for chart_widget in self._pending_gap_evolution_widgets:
                chase_widget._gap_evolution_widgets.append(chart_widget)
                
                # ⚠️ 關鍵修正：設定 StrategyCalculator 以啟用預測曲線
                if hasattr(chase_widget, '_calculator') and chase_widget._calculator:
                    chart_widget.set_strategy_calculator(chase_widget._calculator)
                    print(f"[WORKSPACE] ✅ 已為 Gap Evolution 設定 StrategyCalculator")
                else:
                    print(f"[WORKSPACE] ⚠️ Chase Strategy 的 _calculator 尚未初始化")
                
                # 連接 destroyed 信號
                chart_widget.destroyed.connect(
                    partial(chase_widget._on_gap_widget_closed, chart_widget)
                )
            
            print(f"[WORKSPACE] ✅ 已將 {len(self._pending_gap_evolution_widgets)} 個 Gap Evolution 註冊到 Chase Strategy")
            print(f"[WORKSPACE] 💡 當 Live Timing 播放時，這些視窗會自動更新")
        else:
            print(f"[WORKSPACE] ⚠️ 未找到 Chase Strategy MDI，Gap Evolution 無法自動更新")
            print(f"[WORKSPACE] 💡 請確保 workspace 中包含 Chase Strategy 模組")
        
        # 清空暫存列表
        self._pending_gap_evolution_widgets = []

    def _rebuild_live_timing_window(self, mdi_area, window_config: Dict) -> bool:
        """
        重建 Live Timing MDI 視窗
        
        Live Timing 模組使用專門的 LiveTimingModuleFactory 創建，
        與一般分析模組的創建流程不同。
        
        Args:
            mdi_area: MDI 區域
            window_config: 視窗配置
            
        Returns:
            是否成功
        """
        try:
            from f1t_gui_main import PopoutSubWindow
            from modules.gui.live_timing import LiveTimingModuleFactory
            
            window_type = window_config.get('window_type', 'unknown')
            print(f"[WORKSPACE] 🎬 重建 Live Timing 視窗: {window_type}")
            
            # Live Timing 類型 → 模組名稱映射
            live_timing_name_map = {
                "live_track_map": "Track Map",
                "live_circle_map": "Circle Map",
                "live_ranking_tower": "Live Ranking",
                "live_pit_window": "Pit Window",
                "live_tyre_strategy": "Tyre Strategy",
                "live_driver_strategy": "Driver Strategy",
                "live_lap_time_distribution": "Lap Time Distribution",
                "live_race_control_messages": "Race Control Messages",
                "live_speed_trace": "Speed Trace",
                "live_lap_history_lap_time": "Lap History - Lap Time",
                "live_lap_history_s1": "Lap History - S1",
                "live_lap_history_s2": "Lap History - S2",
                "live_lap_history_s3": "Lap History - S3",
                "live_sector_comparison_s1": "S1 Comparison",
                "live_sector_comparison_s2": "S2 Comparison",
                "live_sector_comparison_s3": "S3 Comparison",
                "live_control_panel": "Control Panel",
                "live_battle_insight": "Battle Insight",
                "live_track_weather": "Track & Weather",
                "live_chase_strategy": "Chase Strategy",
            }
            
            module_name = live_timing_name_map.get(window_type)
            if not module_name:
                print(f"[WORKSPACE] ❌ 未知的 Live Timing 類型: {window_type}")
                return False
            
            print(f"[WORKSPACE] 📦 模組名稱: {module_name}")
            
            # 使用 Live Timing 工廠創建模組
            factory = LiveTimingModuleFactory.get_instance()
            
            # 檢查模組是否已實現
            if not factory.is_implemented(module_name):
                print(f"[WORKSPACE] ⚠️ Live Timing 模組尚未實現: {module_name}")
                return False
            
            # 創建模組實例
            module_instance = factory.create_module(module_name, self.main_window)
            if module_instance is None:
                print(f"[WORKSPACE] ❌ 無法創建 Live Timing 模組: {module_name}")
                return False
            
            print(f"[WORKSPACE] ✅ Live Timing 模組創建成功: {module_instance.__class__.__name__}")
            
            # 獲取視窗標題
            window_title = module_instance.windowTitle() or module_name
            
            # 使用 PopoutSubWindow 包裝模組
            sub_window = PopoutSubWindow(
                window_title,
                mdi_area,
                analysis_module=None,  # Live Timing 不是標準分析模組
                sync_enabled=False
            )
            
            # 設置模組 widget 為內容
            sub_window.setWidget(module_instance)
            
            # 恢復尺寸（優先使用保存的尺寸）
            saved_size = window_config.get('size', {})
            saved_width = saved_size.get('width')
            saved_height = saved_size.get('height')
            
            if saved_width and saved_height:
                sub_window.resize(saved_width, saved_height)
                print(f"[WORKSPACE] 📏 使用保存的尺寸: {saved_width}x{saved_height}")
            else:
                # 使用模組的建議尺寸
                if hasattr(module_instance, 'minimumSize'):
                    min_size = module_instance.minimumSize()
                    if min_size.width() > 0 and min_size.height() > 0:
                        sub_window.resize(min_size.width() + 50, min_size.height() + 50)
                    else:
                        sub_window.resize(500, 500)
                else:
                    sub_window.resize(500, 500)
                print(f"[WORKSPACE] 📏 使用預設尺寸")
            
            # 添加到 MDI 區域
            mdi_area.addSubWindow(sub_window)
            sub_window.show()
            
            # 🔧 重要：show() 後再次設定尺寸，避免被 Qt 自動調整覆蓋
            if saved_width and saved_height:
                sub_window.resize(saved_width, saved_height)
            
            # 恢復位置（優先使用保存的位置）
            saved_position = window_config.get('position', {})
            saved_x = saved_position.get('x')
            saved_y = saved_position.get('y')
            
            if saved_x is not None and saved_y is not None:
                sub_window.move(saved_x, saved_y)
                print(f"[WORKSPACE] 📍 使用保存的位置: ({saved_x}, {saved_y})")
            
            # 自動顯示 Live Timing Control Dock
            if hasattr(self.main_window, '_on_live_timing_module_opened'):
                self.main_window._on_live_timing_module_opened()
            
            # 連接子視窗關閉信號
            if hasattr(self.main_window, '_on_live_timing_module_closed'):
                sub_window.destroyed.connect(self.main_window._on_live_timing_module_closed)
            
            print(f"[WORKSPACE] ✅ Live Timing 視窗重建完成: {window_title}")
            return True
            
        except Exception as e:
            print(f"[WORKSPACE] ❌ 重建 Live Timing 視窗失敗: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _create_module_instance(self, window_type: str, parameters: Dict):
        """
        根據視窗類型創建模組實例
        
        Args:
            window_type: 視窗類型（例如 "rain_analysis"）
            parameters: 參數字典（year, race, session 等）
            
        Returns:
            模組 widget 實例，失敗返回 None
        """
        try:
            year = parameters.get('year')
            race = parameters.get('race')
            session = parameters.get('session')
            
            print(f"[WORKSPACE] 🔧 創建模組: type={window_type}, params={parameters}")
            
            # 🔧 特別調試 Ideal Lap 相關模組
            if "ideal_lap" in window_type:
                print(f"[WORKSPACE] 🎯 IDEAL_LAP_LOAD_DEBUG: 準備載入 ideal lap 模組")
                print(f"[WORKSPACE] 🎯 IDEAL_LAP_LOAD_DEBUG: window_type={window_type}")
                print(f"[WORKSPACE] 🎯 IDEAL_LAP_LOAD_DEBUG: parameters={parameters}")
            
            # Rain Analysis (支援兩種類型名稱)
            if window_type in ("rain_analysis", "rain_weather"):
                from modules.gui.rain_analysis.rain_analysis_module import RainAnalysisModuleAdapter
                module = RainAnalysisModuleAdapter(
                    year=year,
                    race=race,
                    session=session
                )
                print(f"[WORKSPACE] ✅ Rain Analysis 模組已創建 (type={window_type})")
                return module
            
            # Tire Strategy (支援兩種類型名稱)
            elif window_type in ("tire_strategy", "tire"):
                from modules.gui.tire_analysis.tire_analysis_module import TireAnalysisModuleAdapter
                module = TireAnalysisModuleAdapter(
                    year=year,
                    race=race,
                    session=session
                )
                print(f"[WORKSPACE] ✅ Tire Strategy 模組已創建 (type={window_type})")
                return module
            
            # Track Analysis
            elif window_type == "track_analysis":
                from modules.gui.track_analysis import TrackAnalysisUniversal
                module = TrackAnalysisUniversal(
                    year=year,
                    race=race,
                    session=session
                )
                print(f"[WORKSPACE] ✅ Track Analysis 模組已創建")
                return module
            
            # Pitstop Analysis
            elif window_type == "pitstop":
                from modules.gui.pitstop_analysis import PitstopAnalysisModule
                module = PitstopAnalysisModule()
                # 初始化模組（創建 UI）
                module.initialize_module()
                
                # ✅ 關鍵修復：在設置屬性之前調用 update_parameters()
                # 這樣 update_parameters() 才能檢測到參數從 None 變化為實際值
                if hasattr(module, 'update_parameters') and callable(module.update_parameters):
                    try:
                        print(f"[WORKSPACE] [DEBUG] Pitstop 當前參數狀態: year={module.current_year}, race={module.current_race}, session={module.current_session}")
                        print(f"[WORKSPACE] [DEBUG] 準備調用 update_parameters({year}, {race}, {session})")
                        
                        year_int = int(year)
                        success = module.update_parameters(year_int, race, session)
                        
                        print(f"[WORKSPACE] [DEBUG] update_parameters 返回: {success}")
                        
                        if success:
                            print(f"[WORKSPACE] ✅ Pitstop 參數更新成功，已觸發數據載入")
                        else:
                            print(f"[WORKSPACE] ⚠️  Pitstop 參數更新返回 False")
                    except Exception as e:
                        print(f"[WORKSPACE] ❌ Pitstop 參數更新失敗: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    # 如果沒有 update_parameters 方法，回退到設置屬性
                    if hasattr(module, 'current_year'):
                        module.current_year = year
                        module.current_race = race
                        module.current_session = session
                
                print(f"[WORKSPACE] ✅ Pitstop Analysis 模組已創建")
                return module
            
            # Accident Analysis
            elif window_type == "accident":
                from modules.gui.accident_analysis import AccidentAnalysisModule
                module = AccidentAnalysisModule()
                # 初始化模組（創建 UI）
                module.initialize_module()
                
                # ✅ 關鍵修復：在設置屬性之前調用 update_parameters()
                if hasattr(module, 'update_parameters') and callable(module.update_parameters):
                    try:
                        year_int = int(year)
                        success = module.update_parameters(year_int, race, session)
                        if success:
                            print(f"[WORKSPACE] ✅ Accident 參數更新成功，已觸發數據載入")
                        else:
                            print(f"[WORKSPACE] ⚠️  Accident 參數更新返回 False")
                    except Exception as e:
                        print(f"[WORKSPACE] ❌ Accident 參數更新失敗: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    # 如果沒有 update_parameters 方法，回退到設置屬性
                    if hasattr(module, 'current_year'):
                        module.current_year = year
                        module.current_race = race
                        module.current_session = session
                
                print(f"[WORKSPACE] ✅ Accident Analysis 模組已創建")
                return module
            
            # Telemetry Analysis
            elif window_type == "telemetry":
                from modules.gui.telemetry_analysis_mdi import TelemetryAnalysisModule
                module = TelemetryAnalysisModule()
                # 初始化模組（創建 UI）
                module.initialize_module()
                
                # ✅ 關鍵修復：在設置屬性之前調用 update_parameters()
                if hasattr(module, 'update_parameters') and callable(module.update_parameters):
                    try:
                        year_int = int(year)
                        success = module.update_parameters(year_int, race, session)
                        if success:
                            print(f"[WORKSPACE] ✅ Telemetry 參數更新成功，已觸發數據載入")
                        else:
                            print(f"[WORKSPACE] ⚠️  Telemetry 參數更新返回 False")
                    except Exception as e:
                        print(f"[WORKSPACE] ❌ Telemetry 參數更新失敗: {e}")
                        import traceback
                        traceback.print_exc()
                else:
                    # 如果沒有 update_parameters 方法，回退到設置屬性
                    if hasattr(module, 'current_year'):
                        module.current_year = year
                        module.current_race = race
                        module.current_session = session
                
                print(f"[WORKSPACE] ✅ Telemetry Analysis 模組已創建")
                return module
            
            # Ideal Lap Ranking Table
            elif window_type == "ideal_lap_ranking":
                from modules.gui.ideal_lap_analysis.ideal_lap_ranking_table.ideal_lap_ranking_table_module import IdealLapRankingTableModule
                # Module 類型構造函數接受 year/race/session 參數
                module = IdealLapRankingTableModule(
                    parent=None,
                    year=year,
                    race=race,
                    session=session
                )
                # 初始化模組（不傳 parent_widget，因為我們是在 workspace 環境）
                if not module.initialize_module(parent_widget=None):
                    print(f"[WORKSPACE] ❌ Ideal Lap Ranking 初始化失敗")
                    return None
                
                # 🔧 修復：返回 Module 而不是 Widget，保持與 Rain Analysis 一致
                print(f"[WORKSPACE] ✅ Ideal Lap Ranking Table 模組已創建")
                return module
            
            # Ideal Lap Sector Comparison
            elif window_type == "ideal_lap_sector_comparison":
                from modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison.ideal_lap_sector_comparison_module import IdealLapSectorComparisonModule
                module = IdealLapSectorComparisonModule(
                    parent=None,
                    year=year,
                    race=race,
                    session=session
                )
                if not module.initialize_module(parent_widget=None):
                    print(f"[WORKSPACE] ❌ Ideal Lap Sector Comparison 初始化失敗")
                    return None
                
                # 🔧 修復：返回 Module 而不是 Widget，保持與 Rain Analysis 一致
                print(f"[WORKSPACE] ✅ Ideal Lap Sector Comparison 模組已創建")
                return module
            
            # Ideal Lap Sector Heatmap
            elif window_type == "ideal_lap_sector_heatmap":
                from modules.gui.ideal_lap_analysis.ideal_lap_sector_heatmap.ideal_lap_sector_heatmap_module import IdealLapSectorHeatmapModule
                module = IdealLapSectorHeatmapModule(
                    parent=None,
                    year=year,
                    race=race,
                    session=session
                )
                if not module.initialize_module(parent_widget=None):
                    print(f"[WORKSPACE] ❌ Ideal Lap Sector Heatmap 初始化失敗")
                    return None
                
                # 🔧 修復：返回 Module 而不是 Widget，保持與 Rain Analysis 一致
                print(f"[WORKSPACE] ✅ Ideal Lap Sector Heatmap 模組已創建")
                return module
            
            # All Drivers Straight Line Speed
            elif window_type == "all_drivers_straight_line_speed":
                from modules.gui.all_drivers_straight_line_speed_analysis.all_drivers_straight_line_speed_mdi import AllDriversStraightLineSpeedMDI
                # MDI 類型只需要 parent 參數
                module = AllDriversStraightLineSpeedMDI(parent=None)
                # 設置參數
                module.current_year = str(year)
                module.current_race = race
                module.current_session = session
                module.parameter_provider = None  # Workspace 模式不需要 parameter_provider
                # 初始化模組
                if not module.initialize_module():
                    print(f"[WORKSPACE] ❌ All Drivers Straight Line Speed 初始化失敗")
                    return None
                print(f"[WORKSPACE] ✅ All Drivers Straight Line Speed 模組已創建")
                return module
            
            # All Drivers Brake Performance
            elif window_type == "all_drivers_brake_performance":
                from modules.gui.all_drivers_brake_performance_analysis.all_drivers_brake_performance_mdi import AllDriversBrakePerformanceMDI
                module = AllDriversBrakePerformanceMDI(parent=None)
                module.current_year = str(year)
                module.current_race = race
                module.current_session = session
                module.parameter_provider = None
                if not module.initialize_module():
                    print(f"[WORKSPACE] ❌ All Drivers Brake Performance 初始化失敗")
                    return None
                print(f"[WORKSPACE] ✅ All Drivers Brake Performance 模組已創建")
                return module
            
            # Detailed Lap Analysis (Lap Time Table)
            elif window_type == "laptime":
                # ✅ 方案：環境變量控制（最可靠）
                import os
                os.environ['F1T_WORKSPACE_LOADING'] = '1'  # 設置標誌
                
                from modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_mdi import driverLapAnalysisMDI
                
                module = driverLapAnalysisMDI(parent=None)
                
                del os.environ['F1T_WORKSPACE_LOADING']  # 清除標誌
                
                # 設置參數
                module.current_year = str(year)
                module.current_race = race
                module.current_session = session
                module.parameter_provider = None
                
                # 🔧 修復：在 workspace 載入後重新初始化完整的模組組件
                try:
                    # 步驟 1：重新創建 data_manager
                    if not module.data_manager:
                        print(f"[WORKSPACE] 🔧 重新創建 Detailed Lap Analysis data_manager")
                        module.data_manager = module.create_data_manager()
                        if module.data_manager:
                            module._connect_data_manager_signals()
                            print(f"[WORKSPACE] ✅ Detailed Lap Analysis data_manager 創建成功")
                        else:
                            print(f"[WORKSPACE] ❌ Detailed Lap Analysis data_manager 創建失敗")
                    
                    # 步驟 2：重新創建 chart_widget（環境保護模式下被跳過）
                    if not module.chart_widget:
                        print(f"[WORKSPACE] 🔧 重新創建 Detailed Lap Analysis chart_widget")
                        module.chart_widget = module.create_chart_widget()
                        if module.chart_widget:
                            module._connect_chart_widget_signals()
                            print(f"[WORKSPACE] ✅ Detailed Lap Analysis chart_widget 創建成功")
                        else:
                            print(f"[WORKSPACE] ❌ Detailed Lap Analysis chart_widget 創建失敗")
                    
                    # 步驟 3：🔧 關鍵修復：重建完整的 UI 結構（包含 layout 和組件）
                    print(f"[WORKSPACE] 🎨 重建 Detailed Lap Analysis 完整 UI 結構")
                    module._setup_ui()
                    print(f"[WORKSPACE] ✅ Detailed Lap Analysis UI 結構重建完成")
                            
                    # 步驟 4：調用 update_parameters() 觸發數據載入
                    year_int = int(year)
                    success = module.update_parameters(year_int, race, session)
                    if success:
                        print(f"[WORKSPACE] ✅ Detailed Lap Analysis 參數更新成功，已觸發數據載入")
                    else:
                        print(f"[WORKSPACE] ⚠️  Detailed Lap Analysis 參數更新返回 False")
                except Exception as e:
                    print(f"[WORKSPACE] ❌ Detailed Lap Analysis 參數更新失敗: {e}")
                    import traceback
                    traceback.print_exc()
                
                print(f"[WORKSPACE] ✅ Detailed Lap Analysis 模組已創建")
                # ✅ 修復：返回 MDI 實例本身，不是 Widget
                return module
            
            # Lap Time Box Plot
            elif window_type == "laptime_boxplot":
                # ✅ 方案：環境變量控制
                import os
                os.environ['F1T_WORKSPACE_LOADING'] = '1'
                
                from modules.gui.lap_box_plot_analysis.lap_box_plot_analysis_mdi import LapTimeBoxPlotAnalysis
                
                module = LapTimeBoxPlotAnalysis(parent=None)
                
                del os.environ['F1T_WORKSPACE_LOADING']
                
                module.current_year = str(year)
                module.current_race = race
                module.current_session = session
                module.parameter_provider = None
                
                # 🔧 修復：重新初始化完整的模組組件
                try:
                    # 重新創建 data_manager
                    if not module.data_manager:
                        print(f"[WORKSPACE] 🔧 重新創建 Lap Time Box Plot data_manager")
                        module.data_manager = module.create_data_manager()
                        if module.data_manager:
                            module._connect_data_manager_signals()
                            print(f"[WORKSPACE] ✅ Lap Time Box Plot data_manager 創建成功")
                    
                    # 重新創建 chart_widget
                    if not module.chart_widget:
                        print(f"[WORKSPACE] 🔧 重新創建 Lap Time Box Plot chart_widget")
                        module.chart_widget = module.create_chart_widget()
                        if module.chart_widget:
                            module._connect_chart_widget_signals()
                            print(f"[WORKSPACE] ✅ Lap Time Box Plot chart_widget 創建成功")
                    
                    # 🔧 關鍵修復：重建完整的 UI 結構
                    print(f"[WORKSPACE] 🎨 重建 Lap Time Box Plot 完整 UI 結構")
                    module._setup_ui()
                    print(f"[WORKSPACE] ✅ Lap Time Box Plot UI 結構重建完成")
                            
                    year_int = int(year)
                    success = module.update_parameters(year_int, race, session)
                    if success:
                        print(f"[WORKSPACE] ✅ Lap Time Box Plot 參數更新成功，已觸發數據載入")
                    else:
                        print(f"[WORKSPACE] ⚠️  Lap Time Box Plot 參數更新返回 False")
                except Exception as e:
                    print(f"[WORKSPACE] ❌ Lap Time Box Plot 參數更新失敗: {e}")
                    import traceback
                    traceback.print_exc()
                
                print(f"[WORKSPACE] ✅ Lap Time Box Plot 模組已創建")
                # ✅ 修復：返回 MDI 實例本身，不是 Widget
                return module
            
            # Throttle Box Plot
            elif window_type == "throttle_boxplot":
                # ✅ 方案：環境變量控制
                import os
                os.environ['F1T_WORKSPACE_LOADING'] = '1'
                
                from modules.gui.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_mdi import ThrottleBoxPlotAnalysis
                
                module = ThrottleBoxPlotAnalysis(parent=None)
                
                del os.environ['F1T_WORKSPACE_LOADING']
                
                module.current_year = str(year)
                module.current_race = race
                module.current_session = session
                module.parameter_provider = None
                
                # 🔧 修復：重新初始化完整的模組組件
                try:
                    # 重新創建 data_manager
                    if not module.data_manager:
                        print(f"[WORKSPACE] 🔧 重新創建 Throttle Box Plot data_manager")
                        module.data_manager = module.create_data_manager()
                        if module.data_manager:
                            module._connect_data_manager_signals()
                            print(f"[WORKSPACE] ✅ Throttle Box Plot data_manager 創建成功")
                    
                    # 重新創建 chart_widget
                    if not module.chart_widget:
                        print(f"[WORKSPACE] 🔧 重新創建 Throttle Box Plot chart_widget")
                        module.chart_widget = module.create_chart_widget()
                        if module.chart_widget:
                            module._connect_chart_widget_signals()
                            print(f"[WORKSPACE] ✅ Throttle Box Plot chart_widget 創建成功")
                    
                    # 🔧 關鍵修復：重建完整的 UI 結構
                    print(f"[WORKSPACE] 🎨 重建 Throttle Box Plot 完整 UI 結構")
                    module._setup_ui()
                    print(f"[WORKSPACE] ✅ Throttle Box Plot UI 結構重建完成")
                            
                    year_int = int(year)
                    success = module.update_parameters(year_int, race, session)
                    if success:
                        print(f"[WORKSPACE] ✅ Throttle Box Plot 參數更新成功，已觸發數據載入")
                    else:
                        print(f"[WORKSPACE] ⚠️  Throttle Box Plot 參數更新返回 False")
                except Exception as e:
                    print(f"[WORKSPACE] ❌ Throttle Box Plot 參數更新失敗: {e}")
                    import traceback
                    traceback.print_exc()
                
                print(f"[WORKSPACE] ✅ Throttle Box Plot 模組已創建")
                # ✅ 修復：返回 MDI 實例本身，不是 Widget
                return module
            
            # Throttle Line Chart (Single Driver)
            elif window_type == "throttle_line_chart_single_driver":
                # ✅ 方案：環境變量控制
                import os
                os.environ['F1T_WORKSPACE_LOADING'] = '1'
                
                from modules.gui.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_mdi import ThrottleLineChartMDI
                
                module = ThrottleLineChartMDI(parent=None)
                
                del os.environ['F1T_WORKSPACE_LOADING']
                
                module.current_year = str(year)
                module.current_race = race
                module.current_session = session
                module.parameter_provider = None
                
                # 🔧 修復：重新初始化完整的模組組件
                try:
                    # 重新創建 data_manager
                    if not module.data_manager:
                        print(f"[WORKSPACE] 🔧 重新創建 Throttle Line Chart data_manager")
                        module.data_manager = module.create_data_manager()
                        if module.data_manager:
                            module._connect_data_manager_signals()
                            print(f"[WORKSPACE] ✅ Throttle Line Chart data_manager 創建成功")
                    
                    # 重新創建 chart_widget
                    if not module.chart_widget:
                        print(f"[WORKSPACE] 🔧 重新創建 Throttle Line Chart chart_widget")
                        module.chart_widget = module.create_chart_widget()
                        if module.chart_widget:
                            module._connect_chart_widget_signals()
                            print(f"[WORKSPACE] ✅ Throttle Line Chart chart_widget 創建成功")
                    
                    # 🔧 關鍵修復：重建完整的 UI 結構
                    print(f"[WORKSPACE] 🎨 重建 Throttle Line Chart 完整 UI 結構")
                    module._setup_ui()
                    print(f"[WORKSPACE] ✅ Throttle Line Chart UI 結構重建完成")
                            
                    # 注意：Throttle Line Chart 需要 driver 參數
                    year_int = int(year)
                    driver1 = parameters.get('driver1', 'VER')
                    driver2 = parameters.get('driver2', 'VER')
                    success = module.update_parameters(year_int, race, session, driver1=driver1, driver2=driver2)
                    if success:
                        print(f"[WORKSPACE] ✅ Throttle Line Chart 參數更新成功，已觸發數據載入")
                    else:
                        print(f"[WORKSPACE] ⚠️  Throttle Line Chart 參數更新返回 False")
                except Exception as e:
                    print(f"[WORKSPACE] ❌ Throttle Line Chart 參數更新失敗: {e}")
                    import traceback
                    traceback.print_exc()
                
                print(f"[WORKSPACE] ✅ Throttle Line Chart 模組已創建")
                # ✅ 修復：返回 MDI 實例本身，不是 Widget
                return module
            
            # ============================================================================
            # Telemetry Analysis Modules (Lap Analysis)
            # ⚠️ 重要：case 條件必須與模組的 analysis_type 屬性完全匹配
            # ============================================================================
            
            # Speed Analysis
            elif window_type == "speed":
                from modules.gui.lap_analysis.speed_analysis.speed_analysis_mdi import SpeedAnalysisModule
                module = SpeedAnalysisModule(parent=None)
                
                # 設置參數
                module.current_year = str(year)
                module.current_race = race
                module.current_session = session
                module.driver1 = parameters.get('driver1', 'VER')
                module.driver2 = parameters.get('driver2', 'VER')
                module.lap1 = parameters.get('lap1', 1)
                module.lap2 = parameters.get('lap2', 1)
                module.parameter_provider = None
                
                # 初始化模組
                if not module.initialize_module(parent_widget=None):
                    print(f"[WORKSPACE] ❌ Speed Analysis 初始化失敗")
                    return None
                
                print(f"[WORKSPACE] ✅ Speed Analysis 模組已創建")
                return module
            
            # Brake Analysis
            elif window_type == "brake":
                from modules.gui.lap_analysis.brake_analysis.brake_analysis_mdi import BrakeAnalysisModule
                module = BrakeAnalysisModule(parent=None)
                
                module.current_year = str(year)
                module.current_race = race
                module.current_session = session
                module.driver1 = parameters.get('driver1', 'VER')
                module.driver2 = parameters.get('driver2', 'VER')
                module.lap1 = parameters.get('lap1', 1)
                module.lap2 = parameters.get('lap2', 1)
                module.parameter_provider = None
                
                if not module.initialize_module(parent_widget=None):
                    print(f"[WORKSPACE] ❌ Brake Analysis 初始化失敗")
                    return None
                
                print(f"[WORKSPACE] ✅ Brake Analysis 模組已創建")
                return module
            
            # Throttle Analysis
            elif window_type == "throttle":
                from modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_mdi import ThrottleAnalysisModule
                module = ThrottleAnalysisModule(parent=None)
                
                module.current_year = str(year)
                module.current_race = race
                module.current_session = session
                module.driver1 = parameters.get('driver1', 'VER')
                module.driver2 = parameters.get('driver2', 'VER')
                module.lap1 = parameters.get('lap1', 1)
                module.lap2 = parameters.get('lap2', 1)
                module.parameter_provider = None
                
                if not module.initialize_module(parent_widget=None):
                    print(f"[WORKSPACE] ❌ Throttle Analysis 初始化失敗")
                    return None
                
                print(f"[WORKSPACE] ✅ Throttle Analysis 模組已創建")
                return module
            
            # RPM Analysis
            elif window_type == "rpm":
                from modules.gui.lap_analysis.rpm_analysis.rpm_analysis_mdi import RPMAnalysisModule
                module = RPMAnalysisModule(parent=None)
                
                module.current_year = str(year)
                module.current_race = race
                module.current_session = session
                module.driver1 = parameters.get('driver1', 'VER')
                module.driver2 = parameters.get('driver2', 'VER')
                module.lap1 = parameters.get('lap1', 1)
                module.lap2 = parameters.get('lap2', 1)
                module.parameter_provider = None
                
                if not module.initialize_module(parent_widget=None):
                    print(f"[WORKSPACE] ❌ RPM Analysis 初始化失敗")
                    return None
                
                print(f"[WORKSPACE] ✅ RPM Analysis 模組已創建")
                return module
            
            # Acceleration Analysis
            elif window_type == "acceleration":
                from modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_mdi import accelerationAnalysisModule
                module = accelerationAnalysisModule(parent=None)
                
                module.current_year = str(year)
                module.current_race = race
                module.current_session = session
                module.driver1 = parameters.get('driver1', 'VER')
                module.driver2 = parameters.get('driver2', 'VER')
                module.lap1 = parameters.get('lap1', 1)
                module.lap2 = parameters.get('lap2', 1)
                module.parameter_provider = None
                
                if not module.initialize_module(parent_widget=None):
                    print(f"[WORKSPACE] ❌ Acceleration Analysis 初始化失敗")
                    return None
                
                print(f"[WORKSPACE] ✅ Acceleration Analysis 模組已創建")
                return module
            
            # Gear Analysis
            elif window_type == "gear":
                from modules.gui.lap_analysis.gear_analysis.gear_analysis_mdi import GearAnalysisModule
                module = GearAnalysisModule(parent=None)
                
                module.current_year = str(year)
                module.current_race = race
                module.current_session = session
                module.driver1 = parameters.get('driver1', 'VER')
                module.driver2 = parameters.get('driver2', 'VER')
                module.lap1 = parameters.get('lap1', 1)
                module.lap2 = parameters.get('lap2', 1)
                module.parameter_provider = None
                
                if not module.initialize_module(parent_widget=None):
                    print(f"[WORKSPACE] ❌ Gear Analysis 初始化失敗")
                    return None
                
                print(f"[WORKSPACE] ✅ Gear Analysis 模組已創建")
                return module
            
            # Speed Diff Analysis
            # ⚠️ 注意：使用大寫 S 以匹配模組的 analysis_type = 'Speeddiff'
            elif window_type == "Speeddiff":
                from modules.gui.lap_analysis.speeddiff_analysis.speeddiff_analysis_mdi import SpeeddiffAnalysisModule
                module = SpeeddiffAnalysisModule(parent=None)
                
                module.current_year = str(year)
                module.current_race = race
                module.current_session = session
                module.driver1 = parameters.get('driver1', 'VER')
                module.driver2 = parameters.get('driver2', 'VER')
                module.lap1 = parameters.get('lap1', 1)
                module.lap2 = parameters.get('lap2', 1)
                module.parameter_provider = None
                
                if not module.initialize_module(parent_widget=None):
                    print(f"[WORKSPACE] ❌ Speed Diff Analysis 初始化失敗")
                    return None
                
                print(f"[WORKSPACE] ✅ Speed Diff Analysis 模組已創建")
                return module
            
            # Distance Diff Analysis
            elif window_type == "distancediff":
                from modules.gui.lap_analysis.distancediff_analysis.distancediff_analysis_mdi import distancediffAnalysisModule
                module = distancediffAnalysisModule(parent=None)
                
                module.current_year = str(year)
                module.current_race = race
                module.current_session = session
                module.driver1 = parameters.get('driver1', 'VER')
                module.driver2 = parameters.get('driver2', 'VER')
                module.lap1 = parameters.get('lap1', 1)
                module.lap2 = parameters.get('lap2', 1)
                module.parameter_provider = None
                
                if not module.initialize_module(parent_widget=None):
                    print(f"[WORKSPACE] ❌ Distance Diff Analysis 初始化失敗")
                    return None
                
                print(f"[WORKSPACE] ✅ Distance Diff Analysis 模組已創建")
                return module
            
            # Time Diff Analysis
            elif window_type == "timediff":
                from modules.gui.lap_analysis.timediff_analysis.timediff_analysis_mdi import timediffAnalysisModule
                module = timediffAnalysisModule(parent=None)
                
                module.current_year = str(year)
                module.current_race = race
                module.current_session = session
                module.driver1 = parameters.get('driver1', 'VER')
                module.driver2 = parameters.get('driver2', 'VER')
                module.lap1 = parameters.get('lap1', 1)
                module.lap2 = parameters.get('lap2', 1)
                module.parameter_provider = None
                
                if not module.initialize_module(parent_widget=None):
                    print(f"[WORKSPACE] ❌ Time Diff Analysis 初始化失敗")
                    return None
                
                print(f"[WORKSPACE] ✅ Time Diff Analysis 模組已創建")
                return module
            
            # 未知類型
            else:
                print(f"[WORKSPACE] ⚠️ 不支援的視窗類型: {window_type}")
                return None
                
        except Exception as e:
            print(f"[WORKSPACE] ❌ 創建模組失敗: {e}")
            import traceback
            traceback.print_exc()
            return None


# ============================================================================
# 測試代碼
# ============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("WorkspaceSerializer 基本測試")
    print("=" * 60)
    print("\n⚠️ 注意：完整測試需要在 GUI 環境中執行")
    print("此測試僅驗證類別結構和方法簽名")
    
    # 測試視窗類型映射
    print("\n[測試] 視窗類型映射:")
    for class_name, type_id in list(WorkspaceSerializer.WINDOW_TYPE_MAPPING.items())[:5]:
        print(f"  {class_name} → {type_id}")
    print(f"  ... 共 {len(WorkspaceSerializer.WINDOW_TYPE_MAPPING)} 種類型")
    
    # 測試統計資訊提取
    print("\n[測試] 統計資訊提取:")
    test_config = {
        "tabs": [
            {
                "tab_name": "Tab 1",
                "mdi_windows": [
                    {
                        "window_type": "tire_strategy",
                        "parameters": {"year": 2025, "race": "USA", "session": "R"}
                    },
                    {
                        "window_type": "rain_analysis",
                        "parameters": {"year": 2025, "race": "USA", "session": "R"}
                    }
                ]
            }
        ]
    }
    
    serializer = WorkspaceSerializer(main_window=None)  # None for testing
    stats = serializer.extract_statistics(test_config)
    print(f"  總分頁: {stats['total_tabs']}")
    print(f"  總視窗: {stats['total_windows']}")
    print(f"  視窗類型: {stats['window_types']}")
    print(f"  參數: {stats['parameters']}")
    
    print("\n" + "=" * 60)
    print("基本測試完成！")
    print("=" * 60)
