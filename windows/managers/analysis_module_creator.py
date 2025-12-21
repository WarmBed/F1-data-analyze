# -*- coding: utf-8 -*-
"""
AnalysisModuleCreator - 從 f1t_gui_main.py 提取
"""

from core.gui_i18n import tr
from core.logger import get_logger
from typing import Optional, Tuple
from windows.workers.cli_workers import MainWindowParameterProvider

logger = get_logger(__name__)


class AnalysisModuleCreator:
    """從 f1t_gui_main.py 提取的 _create_analysis_module 處理器"""
    
    def __init__(self, main_window):
        self.main_window = main_window

    def _create_analysis_module(self, function_name, module_type_hint: Optional[str] = None):
        """創建分析模組實例"""
        # ✅ 🔥🔥🔥 調試點 0：方法入口 🔥🔥🔥
        logger.debug(f"🔥🔥🔥 [MODULE_FACTORY] _create_analysis_module 被調用！")
        logger.debug(f"🔥 function_name = {function_name}")
        logger.debug(f"🔥 module_type_hint = {module_type_hint}")
        
        try:
            # 導入模組工廠和類型定義
            from modules.gui.interfaces.analysis_module import ModuleFactory, ModuleTypes
            
            # 確保所有模組都被導入
            import modules.gui.race_analysis.rain.rain_analysis_module  # 降雨分析模組
            import modules.gui.tire_analysis.tire_analysis_module  # 輪胎策略分析模組
            import modules.gui.race_analysis.accident.accident_analysis_mdi  # 事故分析模組
            import modules.gui.lap_analysis.gear_analysis.gear_analysis_mdi  # 檔位分析模組
            import modules.gui.lap_analysis.brake_analysis.brake_analysis_mdi  # 煞車分析模組
            import modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_module  # 詳細圈速分析模組
            import modules.gui.race_analysis.position.driver_position_analysis_mdi  # 車手比賽排名分析模組 (F25)
            import modules.gui.race_analysis.track_map.historical_track_map_mdi  # 歷年賽道旗幟統計模組 (F100)
            
            # 賽道分析模組導入與註冊
            try:
                from modules.gui.race_analysis.track import TrackAnalysisUniversal
                TRACK_ANALYSIS_AVAILABLE = True
                logger.debug("[OK] [MODULE_IMPORT] TrackAnalysisUniversal 載入完成")
            except ImportError as e:
                TRACK_ANALYSIS_AVAILABLE = False
                logger.debug(f"警告: TrackAnalysisUniversal 不可用: {e}")
            
            # 🔥 調試點：確認到達映射邏輯前
            logger.debug(f"🔥🔥 [MODULE_FACTORY] TrackAnalysisUniversal 導入後，準備進入映射邏輯")
            
            # ✅ 調試訊息：確認進入映射邏輯
            logger.debug(f"[DEBUG] [MODULE_FACTORY] 開始映射邏輯")
            logger.debug(f"[DEBUG] [MODULE_FACTORY] function_name={function_name}, module_type_hint={module_type_hint}")
            
            # 🔥🔥🔥 調試點：字典定義前
            logger.debug(f"🔥🔥🔥 [MODULE_FACTORY] 準備定義 module_alias_groups 字典")
            
            # 根據功能名稱映射到模組類型，支援多語系顯示文字
            module_alias_groups = {
                "pitstop_analysis": [
                    ("pitstop_analysis", "Pitstop Analysis"),
                    "pitstop",  # ✅ Workspace 使用的原始 key（模組的 analysis_type）
                    "進站分析",
                    "Pitstop Analysis",
                    "ピットストップ分析",
                ],
                "accident_analysis": [
                    ("accident_analysis", "Accident Analysis"),
                    "accident",  # ✅ Workspace 使用的原始 key（模組的 analysis_type）
                    "事故分析",
                    "Accident Analysis",
                ],
                "speed_analysis": [
                    ("speed_analysis", "Speed Analysis"),
                    "speed",  # ✅ Workspace 使用的原始 key（模組的 analysis_type）
                    "速度分析",
                ],
                "throttle_analysis": [
                    ("throttle_analysis", "Throttle Analysis"),
                    "throttle",  # ✅ Workspace 使用的原始 key（模組的 analysis_type）
                    "油門分析",
                    "スロットル分析",
                ],
                "throttle_box_plot": [
                    ("throttle_box_plot", "Throttle Box Plot"),
                    ("throttle_box_plot_analysis", "Throttle Box Plot Analysis"),
                    "throttle_boxplot",  # ✅ Workspace 使用的原始 key（模組的 analysis_type）
                    "油門箱型圖",
                    "油門箱線圖",  # 樹節點別名
                    "Throttle Box Plot",
                    "スロットル箱ひげ図",
                ],
                "throttle_line_chart": [
                    ("throttle_line_chart", "Throttle Line Chart"),
                    "throttle_line_chart_single_driver",  # ✅ Workspace 使用的原始 key（模組的 analysis_type）
                    "油門折線圖",  # 樹節點別名
                    "スロットル折れ線グラフ",
                ],
                "rpm_analysis": [
                    ("rpm_analysis", "RPM Analysis"),
                    "rpm",  # ✅ Workspace 使用的原始 key（模組的 analysis_type）
                    "RPM分析",
                ],
                "gear_analysis": [
                    ("gear_analysis", "Gear Analysis"),
                    "gear",  # ✅ Workspace 使用的原始 key（模組的 analysis_type）
                    "檔位分析",
                    "ギア分析",
                ],
                "brake_analysis": [
                    ("brake_analysis", "Brake Analysis"),
                    "brake",  # ✅ Workspace 使用的原始 key（模組的 analysis_type）
                    "煞車分析",
                    "ブレーキ分析",
                ],
                "acceleration_analysis": [  # ✅ 新增：加速度分析
                    ("acceleration_analysis", "Acceleration Analysis"),
                    "acceleration",  # ✅ Workspace 使用的原始 key（模組的 analysis_type）
                    "加速度分析",
                    "アクセラレーション分析",
                ],
                "speeddiff_analysis": [  # ✅ 新增：速度差分析
                    ("speeddiff_analysis", "Speed Diff Analysis"),
                    "Speeddiff",  # ✅ Workspace 使用的原始 key（模組的 analysis_type，注意大寫S）
                    "speed_diff",  # ✅ 額外別名
                    "速度差分析",
                    "速度差異分析",
                ],
                "distancediff_analysis": [  # ✅ 新增：距離差分析
                    ("distancediff_analysis", "Distance Diff Analysis"),
                    "distancediff",  # ✅ Workspace 使用的原始 key（模組的 analysis_type）
                    "distance_diff",  # ✅ 額外別名
                    "距離差分析",
                    "距離差異分析",
                ],
                "timediff_analysis": [  # ✅ 新增：時間差分析
                    ("timediff_analysis", "Time Diff Analysis"),
                    "timediff",  # ✅ Workspace 使用的原始 key（模組的 analysis_type）
                    "time_diff",  # ✅ 額外別名
                    "時間差分析",
                    "時間差異分析",
                ],
                "rain_analysis": [
                    ("rain_analysis", "Rain Analysis"),
                    "rain_weather",  # ✅ Workspace 使用的原始 key（不翻譯）
                    "雨況分析",
                    "降雨分析",
                ],
                "telemetry_analysis": [
                    ("telemetry_analysis", "Telemetry Analysis"),
                    ("driver_analysis", "Driver Analysis"),
                    ("driver_ranking", "Driver Ranking"),
                    "車手分析",
                    "車手排名",
                    "單場賽事總攬",
                ],
                "track_analysis": [
                    ("track_analysis", "Track Analysis"),
                    "賽道分析",
                    "トラック分析",
                ],
                "tire_analysis": [
                    ("tire_analysis", "Tire Analysis"),
                    ("tire_strategy_analysis", "Tire Strategy Analysis"),
                    "tire",  # ✅ Workspace 使用的原始 key（模組的 analysis_type）
                    "輪胎分析",
                    "輪胎策略分析",
                    "タイヤ戦略分析",
                ],
                "driverlap_analysis": [
                    ("detailed_lap_analysis", "Detailed Lap Analysis"),
                    ("detailed_lap_table", "Detailed Lap Table"),  # 樹節點別名
                    "laptime",  # ✅ Workspace 使用的原始 key（模組的 analysis_type）
                    "詳細圈速分析",
                    "詳細圈速表格",  # 中文樹節點
                    "詳細ラップ分析",
                ],
                "laptime_box_plot": [
                    ("laptime_box_plot", "Lap Time Box Plot"),
                    ("lap_time_boxplot", "Lap Time BoxPlot"),
                    "laptime_boxplot",  # ✅ Workspace 使用的原始 key（模組的 analysis_type）
                    "圈速箱線圖",  # 樹節點別名
                    "圈速箱型圖",
                ],
                "ideal_lap_ranking": [
                    ("ideal_lap_ranking", "Ideal Lap Ranking"),
                    ("ideal_lap_ranking_table", "Ideal Lap Ranking Table"),  # ✅ 添加新名稱
                    ("ranking_table", "Ranking Table"),
                    "排名表格",  # 樹節點別名
                    "理想圈排名",
                ],
                "qualifying_prediction_table": [  # ✅ F74 排位賽預測（修正 key）
                    ("qualifying_prediction", "Qualifying Prediction"),
                    ("qualifying_prediction_table", "FP3 → Q Prediction Table"),
                    "排位賽預測",
                    "FP3 → Q Prediction Table",
                ],
                "race_prediction_table": [  # ✅ F80 正賽預測
                    ("race_prediction", "Race Prediction"),
                    ("race_prediction_table", "Q → R Prediction Table"),
                    "正賽預測",
                    "Q → R Prediction Table",
                ],
                "ideal_lap_sector_heatmap": [
                    ("ideal_lap_sector_heatmap", "Ideal Lap Sector Heatmap"),
                    ("sector_heatmap", "Sector Heat Map"),
                    "分段熱力圖",
                    "セクターヒートマップ",
                ],
                "ideal_lap_sector_comparison": [
                    ("ideal_lap_sector_comparison", "Ideal Lap Sector Comparison"),
                    ("sector_comparison", "Sector Comparison"),
                    "分段對比",  # 樹節點別名
                    "分段比較",
                    "理想圈分段對比",
                ],
                "all_drivers_straight_line_speed": [  # ⭐ 新增
                    ("all_drivers_straight_speed", "All Drivers Speed & Acceleration"),
                    ("straight_speed_analysis", "Straight Speed Analysis (Experimental)"),
                    "全車手速度與加速",
                    "全車手直線速度",
                    "直線速度分析(實驗)",
                    "All Drivers Speed & Acceleration",
                ],
                "all_drivers_max_speed": [  # ⭐ F121 全車手最高速度分析
                    ("all_drivers_max_speed", "All Drivers Max Speed"),
                    ("max_speed_analysis", "Max Speed Analysis (All Laps)"),
                    "全車手最高速度",
                    "全車手最速分析",
                    "最高速度分析",
                    "All Drivers Max Speed",
                ],
                "all_drivers_acceleration_chart": [  # ⭐ F121 全車手加速度圖表
                    ("all_drivers_acceleration_chart", "Acceleration Chart"),
                    ("acceleration_chart", "Speed vs Acceleration Chart"),
                    "加速度圖表",
                    "全車手加速度圖表",
                    "速度加速度圖",
                    "Acceleration Chart",
                ],
                "all_drivers_brake_chart": [  # ⭐ F122 全車手煞車圖表
                    ("all_drivers_brake_chart", "Brake Chart"),
                    ("brake_chart", "Entry Speed vs Deceleration Chart"),
                    "煞車圖表",
                    "全車手煞車圖表",
                    "煞車性能圖",
                    "Brake Chart",
                ],
                "all_drivers_brake_performance": [  # ⭐ F34 煞車性能分析
                    ("all_drivers_brake_perf", "All Drivers Brake Performance"),
                    ("brake_performance_analysis", "Brake Performance Analysis"),
                    "全車手煞車性能",
                    "全車手煞車分析",
                    "All Drivers Brake Performance",
                ],
                "all_drivers_brake_all_laps": [  # ⭐ F122 全車手煞車全圈數分析
                    ("all_drivers_brake_all_laps_analysis", "All Drivers Brake All Laps Analysis"),
                    "全車手煞車全圈數分析",
                    "All Drivers Brake All Laps Analysis",
                ],
                "corner_performance": [  # ⭐ F47 彎道性能分析（統一 analysis_type）
                    ("low_speed_corner_analysis", "Low-Speed Corner Analysis"),
                    ("mid_speed_corner_analysis", "Mid-Speed Corner Analysis"),
                    ("high_speed_corner_analysis", "High-Speed Corner Analysis"),
                    ("corner_low_speed", "Corner Low Speed"),
                    ("corner_mid_speed", "Corner Mid Speed"),
                    ("corner_high_speed", "Corner High Speed"),
                    "低速彎分析",
                    "中速彎分析",
                    "高速彎分析",
                    "Low-Speed Corner Analysis",
                    "Mid-Speed Corner Analysis",
                    "High-Speed Corner Analysis",
                    "低速コーナー分析",
                    "中速コーナー分析",
                    "高速コーナー分析",
                ],
                "driver_position_analysis": [  # ⭐ F25 車手比賽排名分析
                    ("driver_position_analysis", "Driver Race Position"),
                    "driver_position",  # ✅ Workspace 使用的原始 key（模組的 analysis_type）
                    "車手比賽排名",
                    "Driver Race Position",
                    "ドライバーポジション",
                ],
                "parts_analysis": [  # ⭐ F29 FIA 部件分析
                    ("parts_analysis", "FIA Parts Analysis"),
                    "parts",  # ✅ Workspace 使用的原始 key（模組的 analysis_type）
                    "部件分析",
                    "FIA 部件分析",
                    "FIA Parts Analysis",
                    "部品解析",
                ],
                "historical_track_map": [  # ⭐ F100 歷年賽道旗幟統計
                    ("historical_track_map", "Historical Track Map"),
                    "historical_flags",  # ✅ 別名
                    "歷年賽道旗幟統計",
                    "Historical Track Map",
                    "歴年トラック旗統計",
                ],
            }

            # 🔥🔥🔥 調試點：字典定義完成
            logger.debug(f"🔥🔥🔥 [MODULE_FACTORY] module_alias_groups 字典定義完成！共 {len(module_alias_groups)} 個模組類型")
            logger.debug(f"🔥🔥🔥 [MODULE_FACTORY] rain_analysis 在字典中: {'rain_analysis' in module_alias_groups}")
            if 'rain_analysis' in module_alias_groups:
                logger.debug(f"🔥🔥🔥 [MODULE_FACTORY] rain_analysis 別名數量: {len(module_alias_groups['rain_analysis'])}")

            module_mapping = {}
            
            # ✅ 調試點 1：確認開始建立映射表
            logger.debug(f"[DEBUG] [MODULE_FACTORY] 步驟1: 開始建立映射表")
            logger.debug(f"[DEBUG] [MODULE_FACTORY] rain_analysis 原始別名數量: {len(module_alias_groups.get('rain_analysis', []))}")

            def _register_module_alias(alias_value, module_type):
                # 🔥🔥🔥 調試：顯示註冊過程
                if module_type == "rain_analysis":
                    logger.debug(f"🔥 [REGISTER] 嘗試註冊: alias_value='{alias_value}' (type={type(alias_value).__name__}), module_type='{module_type}'")
                    logger.debug(f"🔥 [REGISTER] isinstance(alias_value, str) = {isinstance(alias_value, str)}")
                    logger.debug(f"🔥 [REGISTER] bool(alias_value) = {bool(alias_value) if isinstance(alias_value, str) else 'N/A'}")
                
                if isinstance(alias_value, str) and alias_value:
                    module_mapping[alias_value] = module_type
                    if module_type == "rain_analysis":
                        logger.debug(f"🔥 [REGISTER] ✅ 已註冊: '{alias_value}' → '{module_type}'")
                else:
                    if module_type == "rain_analysis":
                        logger.debug(f"🔥 [REGISTER] ❌ 跳過註冊（不是字串或為空）")


            for module_type, aliases in module_alias_groups.items():
                # ✅ 調試點 2：顯示正在處理的模組類型
                if module_type == "rain_analysis":
                    logger.debug(f"[DEBUG] [MODULE_FACTORY] 步驟2: 處理 rain_analysis，別名數量={len(aliases)}")
                    logger.debug(f"[DEBUG] [MODULE_FACTORY] rain_analysis 別名內容: {aliases}")
                    
                for alias in aliases:
                    if isinstance(alias, tuple):
                        translated_value = tr(alias[0], alias[1])
                        # 🔥🔥🔥 調試：顯示翻譯結果
                        if module_type == "rain_analysis":
                            logger.debug(f"🔥 [TRANSLATE] Tuple {alias} → tr() 返回: '{translated_value}' (type={type(translated_value).__name__})")
                        _register_module_alias(translated_value, module_type)
                        # ✅ 調試點 3：顯示 tuple 翻譯結果
                        if module_type == "rain_analysis":
                            logger.debug(f"[DEBUG] [MODULE_FACTORY]   - Tuple {alias} -> '{translated_value}'")
                    else:
                        _register_module_alias(alias, module_type)
                        # ✅ 調試點 4：顯示字串別名
                        if module_type == "rain_analysis":
                            logger.debug(f"[DEBUG] [MODULE_FACTORY]   - String '{alias}'")
            
            # ✅ 調試：確認映射表已建立
            logger.debug(f"[DEBUG] [MODULE_FACTORY] 映射表已建立，共 {len(module_mapping)} 個條目")
            if 'rain_weather' in module_mapping:
                logger.debug(f"[DEBUG] [MODULE_FACTORY] ✅ 'rain_weather' 在映射表中: {module_mapping['rain_weather']}")
            else:
                logger.debug(f"[DEBUG] [MODULE_FACTORY] ❌ 'rain_weather' 不在映射表中！")
                logger.debug(f"[DEBUG] [MODULE_FACTORY] rain_analysis 別名: {module_alias_groups.get('rain_analysis', [])}")
            
            # 尋找匹配的模組類型
            module_type = None
            matched_keyword = None
            
            # ✅ 修正：優先檢查 module_type_hint 是否在映射表中
            if module_type_hint:
                logger.debug(f"[DEBUG]    [MODULE_FACTORY] 收到模組類型提示: {module_type_hint}")
                # 先嘗試在映射表中查找
                if module_type_hint in module_mapping:
                    module_type = module_mapping[module_type_hint]
                    matched_keyword = module_type_hint
                    logger.debug(f"[DEBUG]    [MODULE_FACTORY] ✅ 類型提示在映射表中找到: '{module_type_hint}' -> '{module_type}'")
                else:
                    # 如果不在映射表中，假設它本身就是模組類型
                    module_type = module_type_hint
                    logger.debug(f"[DEBUG]    [MODULE_FACTORY] 使用類型提示作為模組類型: {module_type}")
            else:
                # 沒有提供 module_type_hint，從 function_name 中搜索
                normalized_function_name = function_name.casefold() if isinstance(function_name, str) else ""
                logger.debug(f"[DEBUG]    [MODULE_FACTORY] 開始尋找匹配的模組類型，功能名稱: '{function_name}'")
                
                # ✅ 修正：按關鍵字長度排序，優先匹配更長的關鍵字（避免 "speed" 搶先匹配到 "all drivers speed"）
                sorted_mapping = sorted(module_mapping.items(), key=lambda x: len(x[0]) if isinstance(x[0], str) else 0, reverse=True)
                
                for keyword, mod_type in sorted_mapping:
                    normalized_keyword = keyword.casefold() if isinstance(keyword, str) else ""
                    if normalized_keyword and normalized_keyword in normalized_function_name:
                        module_type = mod_type
                        matched_keyword = keyword
                        logger.debug(f"[DEBUG]    [MODULE_FACTORY] 🎯 匹配成功! 關鍵字: '{keyword}' ({len(keyword)} 字元)")
                        break
                if module_type and matched_keyword:
                    logger.debug(f"[DEBUG]    [MODULE_FACTORY] ✅ 找到匹配! 關鍵字: '{matched_keyword}' -> 模組類型: '{module_type}'")
                else:
                    logger.debug(f"[DEBUG]    [MODULE_FACTORY] ⚠️ 功能 '{function_name}' 未找到對應模組別名，將保持預設流程")
            
            if module_type:
                logger.debug(f"[DEBUG]    [MODULE_FACTORY] 最終確定的模組類型: {module_type}")
                # 創建參數提供者
                parameter_provider = MainWindowParameterProvider(self.main_window)
                logger.debug(f"[DEBUG]    [MODULE_FACTORY] 開始處理模組類型: {module_type} (來自功能: {function_name})")
                
                # 處理進站分析模組
                if module_type == "pitstop_analysis":
                    try:
                        from modules.gui.race_analysis.pitstop.pitstop_analysis_mdi import PitstopAnalysisModule
                        logger.debug(f"[OK] [MODULE_FACTORY] 創建進站分析模組實例")
                        
                        # 創建模組實例並設置參數提供者
                        module = PitstopAnalysisModule()
                        module.parameter_provider = parameter_provider
                        
                        # 在初始化前先設置當前參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            # 直接設置模組參數，避免Unknown標題
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 進站分析模組參數預設為: {current_year} {current_race} {current_session}")
                        
                        # 初始化模組
                        if module.initialize_module():
                            logger.debug(f"[OK] [MODULE_FACTORY] 進站分析模組初始化成功")
                            return self.main_window._mark_module_factory_type(module, module_type)
                        else:
                            logger.error(f"[ERROR] [MODULE_FACTORY] 進站分析模組初始化失敗")
                            return None
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 進站分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理事故分析模組
                elif module_type == "accident_analysis":
                    try:
                        from modules.gui.race_analysis.accident.accident_analysis_mdi import AccidentAnalysisModule
                        logger.debug(f"[OK] [MODULE_FACTORY] 創建事故分析模組實例")
                        
                        # 創建模組實例並設置參數提供者
                        module = AccidentAnalysisModule()
                        module.parameter_provider = parameter_provider
                        
                        # 在初始化前先設置當前參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            # 直接設置模組參數，避免Unknown標題
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 事故分析模組參數預設為: {current_year} {current_race} {current_session}")
                        
                        # 初始化模組
                        if module.initialize_module():
                            logger.debug(f"[OK] [MODULE_FACTORY] 事故分析模組初始化成功")
                            return self.main_window._mark_module_factory_type(module, module_type)
                        else:
                            logger.error(f"[ERROR] [MODULE_FACTORY] 事故分析模組初始化失敗")
                            return None
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 事故分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理單場賽事總攬模組
                elif module_type == "telemetry_analysis":
                    try:
                        from modules.gui.telemetry_analysis_mdi import TelemetryAnalysisModule
                        logger.debug(f"[OK] [MODULE_FACTORY] 創建單場賽事總攬模組實例")
                        
                        # 創建模組實例並設置參數提供者
                        module = TelemetryAnalysisModule()
                        module.parameter_provider = parameter_provider
                        
                        # 在初始化前先設置當前參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            # 直接設置模組參數，避免Unknown標題
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 單場賽事總攬模組參數預設為: {current_year} {current_race} {current_session}")
                        
                        # 初始化模組
                        if module.initialize_module():
                            logger.debug(f"[OK] [MODULE_FACTORY] 單場賽事總攬模組初始化成功")
                            return self.main_window._mark_module_factory_type(module, module_type)
                        else:
                            logger.error(f"[ERROR] [MODULE_FACTORY] 單場賽事總攬模組初始化失敗")
                            return None
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 單場賽事總攬模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理賽道分析模組
                elif module_type == "track_analysis":
                    if not TRACK_ANALYSIS_AVAILABLE:
                        logger.debug(f"[INFO] [MODULE_FACTORY] TrackAnalysisUniversal 不可用，返回舊版流程")
                        return None

                    try:
                        current_year = parameter_provider.get_current_year()
                        current_race = parameter_provider.get_current_race()
                        current_session = parameter_provider.get_current_session()

                        module = TrackAnalysisUniversal(main_window=self)
                        module.parameter_provider = parameter_provider

                        # 轉換年份為整數，失敗時保持原值
                        try:
                            year_value = int(current_year)
                        except (TypeError, ValueError):
                            year_value = current_year

                        module.update_parameters(
                            year=year_value,
                            race=current_race,
                            session=current_session
                        )

                        logger.debug(f"[OK] [MODULE_FACTORY] 賽道分析模組初始化成功: {current_year} {current_race} {current_session}")
                        return self.main_window._mark_module_factory_type(module, module_type)
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 賽道分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None

                # 處理油門分析模組
                elif module_type == "throttle_analysis":
                    try:
                        from modules.gui.lap_analysis.Throttle_analysis.throttle_analysis_mdi import ThrottleAnalysisModule
                        logger.debug(f"[OK] [MODULE_FACTORY] 創建油門分析模組實例")
                        
                        # 創建模組實例並設置參數提供者
                        module = ThrottleAnalysisModule()
                        module.parameter_provider = parameter_provider
                        
                        # 在初始化前先設置當前參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            # 直接設置模組參數，避免Unknown標題
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 油門分析模組參數預設為: {current_year} {current_race} {current_session}")
                        
                        # 初始化模組
                        if module.initialize_module():
                            logger.debug(f"[OK] [MODULE_FACTORY] 油門分析模組初始化成功")
                            return self.main_window._mark_module_factory_type(module, module_type)
                        else:
                            logger.error(f"[ERROR] [MODULE_FACTORY] 油門分析模組初始化失敗")
                            return None
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 油門分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None

                # 油門箱型圖分析模組
                elif module_type == "throttle_box_plot":
                    try:
                        from modules.gui.lap_analysis.Throttle_analysis.throttle_box_plot_analysis.throttle_box_plot_analysis_module import (
                            ThrottleBoxPlotAnalysisModule,
                        )

                        logger.debug(f"[OK] [MODULE_FACTORY] 創建油門箱型圖分析模組實例")

                        module = ThrottleBoxPlotAnalysisModule(parent=self.main_window)
                        module.parameter_provider = parameter_provider

                        current_year_value = None
                        current_race = None
                        current_session = None

                        if parameter_provider:
                            current_year_value = parameter_provider.get_current_year()
                            try:
                                current_year = int(current_year_value)
                            except (TypeError, ValueError):
                                current_year = current_year_value

                            current_race = parameter_provider.get_current_race()
                            current_session = parameter_provider.get_current_session()

                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session

                            logger.debug(
                                f"[INIT] [MODULE_FACTORY] 油門箱型圖模組參數預設為: {module.current_year} {module.current_race} {module.current_session}"
                            )

                        if module.initialize_module():
                            logger.debug(f"[OK] [MODULE_FACTORY] 油門箱型圖模組初始化成功")
                            if parameter_provider:
                                sync_year = current_year_value
                                try:
                                    sync_year_int = int(sync_year)
                                except (TypeError, ValueError):
                                    sync_year_int = sync_year

                                update_year = sync_year_int if sync_year_int is not None else module.current_year

                                try:
                                    module.update_parameters(update_year, current_race, current_session)
                                except Exception as sync_exc:
                                    logger.debug(f"[WARN] [MODULE_FACTORY] 油門箱型圖模組參數同步失敗: {sync_exc}")

                            return self.main_window._mark_module_factory_type(module, module_type)
                        else:
                            logger.error(f"[ERROR] [MODULE_FACTORY] 油門箱型圖模組初始化失敗")
                            return None
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 油門箱型圖模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # ✅ 圈速箱型圖分析模組（新增 - 2025-11-13）
                elif module_type == "laptime_box_plot":
                    try:
                        from modules.gui.driver_race.lap_box_plot_analysis.lap_box_plot_analysis_module import (
                            LapTimeBoxPlotAnalysisModule,
                        )

                        logger.debug(f"[OK] [MODULE_FACTORY] 創建圈速箱型圖分析模組實例")

                        module = LapTimeBoxPlotAnalysisModule(parent=self.main_window)
                        module.parameter_provider = parameter_provider

                        current_year_value = None
                        current_race = None
                        current_session = None

                        if parameter_provider:
                            current_year_value = parameter_provider.get_current_year()
                            try:
                                current_year = int(current_year_value)
                            except (TypeError, ValueError):
                                current_year = current_year_value

                            current_race = parameter_provider.get_current_race()
                            current_session = parameter_provider.get_current_session()

                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session

                            logger.debug(
                                f"[INIT] [MODULE_FACTORY] 圈速箱型圖模組參數預設為: {module.current_year} {module.current_race} {module.current_session}"
                            )

                        if module.initialize_module():
                            logger.debug(f"[OK] [MODULE_FACTORY] 圈速箱型圖模組初始化成功")
                            if parameter_provider:
                                sync_year = current_year_value
                                try:
                                    sync_year_int = int(sync_year)
                                except (TypeError, ValueError):
                                    sync_year_int = sync_year

                                update_year = sync_year_int if sync_year_int is not None else module.current_year

                                try:
                                    module.update_parameters(update_year, current_race, current_session)
                                except Exception as sync_exc:
                                    logger.debug(f"[WARN] [MODULE_FACTORY] 圈速箱型圖模組參數同步失敗: {sync_exc}")

                            return self.main_window._mark_module_factory_type(module, module_type)
                        else:
                            logger.error(f"[ERROR] [MODULE_FACTORY] 圈速箱型圖模組初始化失敗")
                            return None
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 圈速箱型圖模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 油門折線圖分析模組
                elif module_type == "throttle_line_chart":
                    try:
                        logger.debug(f"[DEBUG]    [MODULE_FACTORY] 開始創建油門折線圖模組...")
                        from modules.gui.lap_analysis.Throttle_analysis.throttle_line_chart_analysis.throttle_line_chart_mdi import (
                            ThrottleLineChartMDI
                        )
                        logger.debug(f"[OK] [MODULE_FACTORY] 油門折線圖 MDI 導入成功")
                        
                        # 創建 MDI 實例
                        module = ThrottleLineChartMDI(parent=self.main_window)
                        logger.debug(f"✅ [MODULE_FACTORY] 油門折線圖 MDI 實例創建成功")
                        
                        # 設置參數提供者
                        module.parameter_provider = parameter_provider
                        
                        # 設置參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race()
                            current_session = parameter_provider.get_current_session()
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 油門折線圖模組參數預設為: {current_year} {current_race} {current_session}")
                            
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                        
                        # 初始化模組
                        if not module.initialize_module():
                            logger.error(f"[ERROR] [MODULE_FACTORY] 油門折線圖模組初始化失敗")
                            return None
                        
                        logger.debug(f"[OK] [MODULE_FACTORY] 油門折線圖模組初始化成功")
                        return self.main_window._mark_module_factory_type(module, module_type)
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 油門折線圖模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理檔位分析模組
                elif module_type == "gear_analysis":
                    try:
                        from modules.gui.lap_analysis.gear_analysis.gear_analysis_mdi import GearAnalysisModule
                        logger.debug(f"[OK] [MODULE_FACTORY] 創建檔位分析模組實例")
                        
                        # 創建模組實例並設置參數提供者
                        module = GearAnalysisModule()
                        module.parameter_provider = parameter_provider
                        
                        # 在初始化前先設置當前參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            # 直接設置模組參數，避免Unknown標題
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 檔位分析模組參數預設為: {current_year} {current_race} {current_session}")
                        
                        # 初始化模組
                        if module.initialize_module():
                            logger.debug(f"[OK] [MODULE_FACTORY] 檔位分析模組初始化成功")
                            return self.main_window._mark_module_factory_type(module, module_type)
                        else:
                            logger.error(f"[ERROR] [MODULE_FACTORY] 檔位分析模組初始化失敗")
                            return None
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 檔位分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理煞車分析模組
                elif module_type == "brake_analysis":
                    try:
                        from modules.gui.lap_analysis.brake_analysis.brake_analysis_mdi import BrakeAnalysisModule
                        logger.debug(f"[OK] [MODULE_FACTORY] 創建煞車分析模組實例")
                        
                        # 創建模組實例並設置參數提供者
                        module = BrakeAnalysisModule()
                        module.parameter_provider = parameter_provider
                        
                        # 在初始化前先設置當前參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            # 直接設置模組參數，避免Unknown標題
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 煞車分析模組參數預設為: {current_year} {current_race} {current_session}")
                        
                        # 初始化模組
                        if module.initialize_module():
                            logger.debug(f"[OK] [MODULE_FACTORY] 煞車分析模組初始化成功")
                            return self.main_window._mark_module_factory_type(module, module_type)
                        else:
                            logger.error(f"[ERROR] [MODULE_FACTORY] 煞車分析模組初始化失敗")
                            return None
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 煞車分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理降雨分析模組
                elif module_type == "rain_analysis":
                    try:
                        logger.debug(f"[DEBUG]    [MODULE_FACTORY] 開始創建降雨分析模組...")
                        from modules.gui.race_analysis.rain.rain_analysis_mdi import RainAnalysisUniversal
                        logger.debug(f"[OK] [MODULE_FACTORY] 降雨分析模組導入成功（使用新版 Universal）")
                        
                        # 獲取當前參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 降雨分析模組參數: {current_year} {current_race} {current_session}")
                            
                            # 創建模組實例（使用新版 Universal MDI）
                            module = RainAnalysisUniversal(
                                year=current_year,
                                race=current_race,
                                session=current_session
                            )
                            logger.debug(f"[OK] 降雨分析模組初始化成功（Universal MDI）")
                            return self.main_window._mark_module_factory_type(module, module_type)
                        else:
                            logger.error(f"[ERROR] 降雨分析模組創建失敗：無參數")
                            return None
                    except Exception as e:
                        logger.error(f"[ERROR] 降雨分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理輪胎策略分析模組
                elif module_type == "tire_analysis":
                    try:
                        logger.debug(f"[DEBUG]    [MODULE_FACTORY] 開始創建輪胎策略分析模組...")
                        from modules.gui.tire_analysis.tire_analysis_module import TireAnalysisModuleAdapter
                        logger.debug(f"[OK] [MODULE_FACTORY] 輪胎策略分析適配器導入成功")
                        
                        # 獲取當前參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 輪胎策略分析模組參數: {current_year} {current_race} {current_session}")
                            
                            # 創建模組實例
                            module = TireAnalysisModuleAdapter(
                                year=current_year,
                                race=current_race,
                                session=current_session
                            )
                            logger.debug(f"[OK] 輪胎策略分析模組初始化成功")
                            return self.main_window._mark_module_factory_type(module, module_type)
                        else:
                            logger.error(f"[ERROR] 輪胎策略分析模組創建失敗：無參數")
                            return None
                    except Exception as e:
                        logger.error(f"[ERROR] 輪胎策略分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理詳細圈速分析模組
                elif module_type == "driverlap_analysis":
                    try:
                        logger.debug(f"[DEBUG]    [MODULE_FACTORY] 開始創建詳細圈速分析模組...")
                        from modules.gui.driver_race.detailed_lap_analysis.driverlap_analysis_mdi import driverLapAnalysisMDI
                        logger.debug(f"[OK] [MODULE_FACTORY] 詳細圈速分析 MDI 導入成功")
                        
                        # 直接創建 MDI 實例，不再需要包裝模組
                        module = driverLapAnalysisMDI(parent=self.main_window)
                        logger.debug(f"✅ [MODULE_FACTORY] 詳細圈速分析 MDI 實例創建成功")
                        
                        # 設置參數提供者
                        module.parameter_provider = parameter_provider
                        
                        # 設置參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 詳細圈速分析模組參數預設為: {current_year} {current_race} {current_session}")
                            
                            # 直接設置參數（與直接模式一致）
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                        
                        # ✅ 初始化模組（關鍵步驟）
                        if not module.initialize_module():
                            logger.error(f"[ERROR] [MODULE_FACTORY] 詳細圈速分析模組初始化失敗")
                            return None
                        
                        logger.debug(f"[OK] [MODULE_FACTORY] 詳細圈速分析模組初始化成功")
                        return self.main_window._mark_module_factory_type(module, module_type)
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 詳細圈速分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理圈速箱線圖模組
                elif module_type == "laptime_box_plot":
                    try:
                        logger.debug(f"[DEBUG]    [MODULE_FACTORY] 開始創建圈速箱線圖模組...")
                        from modules.gui.lap_analysis.lap_box_plot.lap_box_plot_analysis_mdi import (
                            LapTimeBoxPlotAnalysis
                        )
                        logger.debug(f"[OK] [MODULE_FACTORY] 圈速箱線圖 MDI 導入成功")
                        
                        # 創建 MDI 實例
                        module = LapTimeBoxPlotAnalysis(parent=self.main_window)
                        logger.debug(f"✅ [MODULE_FACTORY] 圈速箱線圖 MDI 實例創建成功")
                        
                        # 設置參數提供者
                        module.parameter_provider = parameter_provider
                        
                        # 設置參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race()
                            current_session = parameter_provider.get_current_session()
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 圈速箱線圖模組參數預設為: {current_year} {current_race} {current_session}")
                            
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                        
                        # 初始化模組
                        if not module.initialize_module():
                            logger.error(f"[ERROR] [MODULE_FACTORY] 圈速箱線圖模組初始化失敗")
                            return None
                        
                        logger.debug(f"[OK] [MODULE_FACTORY] 圈速箱線圖模組初始化成功")
                        return self.main_window._mark_module_factory_type(module, module_type)
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 圈速箱線圖模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理理想圈排名表格模組
                elif module_type == "ideal_lap_ranking":
                    try:
                        logger.debug(f"[DEBUG]    [MODULE_FACTORY] 開始創建理想圈排名表格模組...")
                        from modules.gui.lap_analysis.ideal_lap.ideal_lap_ranking_table.ideal_lap_ranking_table_mdi import (
                            IdealLapRankingTableMDI
                        )
                        logger.debug(f"[OK] [MODULE_FACTORY] 理想圈排名表格 MDI 導入成功")
                        
                        # 創建 MDI 實例
                        module = IdealLapRankingTableMDI(parent=self.main_window)
                        logger.debug(f"✅ [MODULE_FACTORY] 理想圈排名表格 MDI 實例創建成功")
                        
                        # 設置參數提供者
                        module.parameter_provider = parameter_provider
                        
                        # 設置參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race()
                            current_session = parameter_provider.get_current_session()
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 理想圈排名表格模組參數預設為: {current_year} {current_race} {current_session}")
                            
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                        
                        # 初始化模組
                        if not module.initialize_module():
                            logger.error(f"[ERROR] [MODULE_FACTORY] 理想圈排名表格模組初始化失敗")
                            return None
                        
                        logger.debug(f"[OK] [MODULE_FACTORY] 理想圈排名表格模組初始化成功")
                        return self.main_window._mark_module_factory_type(module, module_type)
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 理想圈排名表格模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理排位賽預測表格模組 ⭐ F74 v3.8 新增
                elif module_type == "qualifying_prediction_table":
                    try:
                        logger.debug(f"[DEBUG]    [MODULE_FACTORY] 開始創建排位賽預測表格模組 (v3.8)...")
                        from modules.gui.qualifying_prediction.qualifying_prediction_mdi import (
                            QualifyingPredictionMDI
                        )
                        logger.debug(f"[OK] [MODULE_FACTORY] 排位賽預測 MDI 導入成功")
                        
                        # 創建 MDI 實例
                        module = QualifyingPredictionMDI(parent=self.main_window)
                        logger.debug(f"✅ [MODULE_FACTORY] 排位賽預測 MDI 實例創建成功")
                        
                        # 設置參數提供者
                        module.parameter_provider = parameter_provider
                        
                        # 設置參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race()
                            current_session = parameter_provider.get_current_session()
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 排位賽預測模組參數預設為: {current_year} {current_race} {current_session}")
                            
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                        
                        # 初始化模組
                        if not module.initialize_module():
                            logger.error(f"[ERROR] [MODULE_FACTORY] 排位賽預測模組初始化失敗")
                            return None
                        
                        logger.debug(f"[OK] [MODULE_FACTORY] 排位賽預測模組初始化成功")
                        return self.main_window._mark_module_factory_type(module, module_type)
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 排位賽預測模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理正賽預測表格模組 ⭐ F80 新增
                elif module_type == "race_prediction_table":
                    try:
                        logger.debug(f"[DEBUG]    [MODULE_FACTORY] 開始創建正賽預測表格模組 (F80)...")
                        from modules.gui.race_prediction.race_prediction_mdi import (
                            RacePredictionMDI
                        )
                        logger.debug(f"[OK] [MODULE_FACTORY] 正賽預測 MDI 導入成功")
                        
                        # 創建 MDI 實例
                        module = RacePredictionMDI(parent=self.main_window)
                        logger.debug(f"✅ [MODULE_FACTORY] 正賽預測 MDI 實例創建成功")
                        
                        # 設置參數提供者
                        module.parameter_provider = parameter_provider
                        
                        # 設置參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race()
                            current_session = parameter_provider.get_current_session()
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 正賽預測模組參數預設為: {current_year} {current_race} {current_session}")
                            
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                        
                        # 初始化模組
                        if not module.initialize_module():
                            logger.error(f"[ERROR] [MODULE_FACTORY] 正賽預測模組初始化失敗")
                            return None
                        
                        logger.debug(f"[OK] [MODULE_FACTORY] 正賽預測模組初始化成功")
                        return self.main_window._mark_module_factory_type(module, module_type)
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 正賽預測模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理理想圈分段熱力圖模組
                elif module_type == "ideal_lap_sector_heatmap":
                    try:
                        logger.debug(f"[DEBUG]    [MODULE_FACTORY] 開始創建理想圈分段熱力圖模組...")
                        from modules.gui.lap_analysis.ideal_lap.ideal_lap_sector_heatmap.ideal_lap_sector_heatmap_mdi import (
                            IdealLapSectorHeatmapMDI
                        )
                        logger.debug(f"[OK] [MODULE_FACTORY] 理想圈分段熱力圖 MDI 導入成功")
                        
                        module = IdealLapSectorHeatmapMDI(parent=self.main_window)
                        logger.debug(f"✅ [MODULE_FACTORY] 理想圈分段熱力圖 MDI 實例創建成功")
                        
                        module.parameter_provider = parameter_provider
                        
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race()
                            current_session = parameter_provider.get_current_session()
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 理想圈分段熱力圖模組參數預設為: {current_year} {current_race} {current_session}")
                            
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                        
                        if not module.initialize_module():
                            logger.error(f"[ERROR] [MODULE_FACTORY] 理想圈分段熱力圖模組初始化失敗")
                            return None
                        
                        logger.debug(f"[OK] [MODULE_FACTORY] 理想圈分段熱力圖模組初始化成功")
                        return self.main_window._mark_module_factory_type(module, module_type)
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 理想圈分段熱力圖模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理理想圈分段對比模組
                elif module_type == "ideal_lap_sector_comparison":
                    try:
                        logger.debug(f"[DEBUG]    [MODULE_FACTORY] 開始創建理想圈分段對比模組...")
                        from modules.gui.lap_analysis.ideal_lap.ideal_lap_sector_comparison.ideal_lap_sector_comparison_mdi import (
                            IdealLapSectorComparisonMDI
                        )
                        logger.debug(f"[OK] [MODULE_FACTORY] 理想圈分段對比 MDI 導入成功")
                        
                        # 創建 MDI 實例
                        module = IdealLapSectorComparisonMDI(parent=self.main_window)
                        logger.debug(f"✅ [MODULE_FACTORY] 理想圈分段對比 MDI 實例創建成功")
                        
                        # 設置參數提供者
                        module.parameter_provider = parameter_provider
                        
                        # 設置參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race()
                            current_session = parameter_provider.get_current_session()
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 理想圈分段對比模組參數預設為: {current_year} {current_race} {current_session}")
                            
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                        
                        # 初始化模組
                        if not module.initialize_module():
                            logger.error(f"[ERROR] [MODULE_FACTORY] 理想圈分段對比模組初始化失敗")
                            return None
                        
                        logger.debug(f"[OK] [MODULE_FACTORY] 理想圈分段對比模組初始化成功")
                        return self.main_window._mark_module_factory_type(module, module_type)
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 理想圈分段對比模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理全車手直線速度分析模組 ⭐ 新增
                elif module_type == "all_drivers_straight_line_speed":
                    try:
                        logger.debug(f"[DEBUG]    [MODULE_FACTORY] 開始創建全車手直線速度分析模組...")
                        from modules.gui.all_drivers.straight_line_speed.all_drivers_straight_line_speed_mdi import (
                            AllDriversStraightLineSpeedMDI
                        )
                        logger.debug(f"[OK] [MODULE_FACTORY] 全車手直線速度 MDI 導入成功")
                        
                        # 創建 MDI 實例
                        module = AllDriversStraightLineSpeedMDI(parent=self.main_window)
                        logger.debug(f"✅ [MODULE_FACTORY] 全車手直線速度 MDI 實例創建成功")
                        
                        # 設置參數提供者
                        module.parameter_provider = parameter_provider
                        
                        # 設置參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race()
                            current_session = parameter_provider.get_current_session()
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 全車手直線速度模組參數預設為: {current_year} {current_race} {current_session}")
                            
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                        
                        # 初始化模組
                        if not module.initialize_module():
                            logger.error(f"[ERROR] [MODULE_FACTORY] 全車手直線速度模組初始化失敗")
                            return None
                        
                        logger.debug(f"[OK] [MODULE_FACTORY] 全車手直線速度模組初始化成功")
                        return self.main_window._mark_module_factory_type(module, module_type)
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 全車手直線速度模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理全車手最高速度分析模組 ⭐ F121 新增
                elif module_type == "all_drivers_max_speed":
                    try:
                        logger.debug(f"[DEBUG] [MODULE_FACTORY] 開始創建全車手最高速度分析模組...")
                        from modules.gui.all_drivers.max_speed.all_drivers_max_speed_mdi import (
                            AllDriversMaxSpeedMDI
                        )
                        logger.debug(f"[OK] [MODULE_FACTORY] 全車手最高速度 MDI 導入成功")
                        
                        # 創建 MDI 實例
                        module = AllDriversMaxSpeedMDI(parent=self.main_window)
                        logger.debug(f"[OK] [MODULE_FACTORY] 全車手最高速度 MDI 實例創建成功")
                        
                        # 設置參數提供者
                        module.parameter_provider = parameter_provider
                        
                        # 設置參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race()
                            current_session = parameter_provider.get_current_session()
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 全車手最高速度模組參數預設為: {current_year} {current_race} {current_session}")
                            
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                        
                        # 初始化模組
                        if not module.initialize_module():
                            logger.error(f"[ERROR] [MODULE_FACTORY] 全車手最高速度模組初始化失敗")
                            return None
                        
                        logger.debug(f"[OK] [MODULE_FACTORY] 全車手最高速度模組初始化成功")
                        return self.main_window._mark_module_factory_type(module, module_type)
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 全車手最高速度模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理全車手加速度圖表模組 ⭐ F121 新增
                elif module_type == "all_drivers_acceleration_chart":
                    try:
                        logger.debug(f"[DEBUG] [MODULE_FACTORY] 開始創建全車手加速度圖表模組...")
                        from modules.gui.all_drivers.acceleration.acceleration_chart_mdi import (
                            AllDriversAccelerationChartMDI
                        )
                        logger.debug(f"[OK] [MODULE_FACTORY] 全車手加速度圖表 MDI 導入成功")
                        
                        # 創建 MDI 實例
                        module = AllDriversAccelerationChartMDI(parent=self.main_window)
                        logger.debug(f"[OK] [MODULE_FACTORY] 全車手加速度圖表 MDI 實例創建成功")
                        
                        # 設置參數提供者
                        module.parameter_provider = parameter_provider
                        
                        # 設置參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race()
                            current_session = parameter_provider.get_current_session()
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 全車手加速度圖表模組參數預設為: {current_year} {current_race} {current_session}")
                            
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                        
                        # 初始化模組
                        if not module.initialize_module():
                            logger.error(f"[ERROR] [MODULE_FACTORY] 全車手加速度圖表模組初始化失敗")
                            return None
                        
                        logger.debug(f"[OK] [MODULE_FACTORY] 全車手加速度圖表模組初始化成功")
                        return self.main_window._mark_module_factory_type(module, module_type)
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 全車手加速度圖表模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理全車手煞車圖表模組 ⭐ F122 新增
                elif module_type == "all_drivers_brake_chart":
                    try:
                        logger.debug(f"[DEBUG] [MODULE_FACTORY] 開始創建全車手煞車圖表模組...")
                        from modules.gui.all_drivers.brake.brake_chart_mdi import (
                            AllDriversBrakeChartMDI
                        )
                        logger.debug(f"[OK] [MODULE_FACTORY] 全車手煞車圖表 MDI 導入成功")
                        
                        # 創建 MDI 實例
                        module = AllDriversBrakeChartMDI(parent=self.main_window)
                        logger.debug(f"[OK] [MODULE_FACTORY] 全車手煞車圖表 MDI 實例創建成功")
                        
                        # 設置參數提供者
                        module.parameter_provider = parameter_provider
                        
                        # 設置參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race()
                            current_session = parameter_provider.get_current_session()
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 全車手煞車圖表模組參數預設為: {current_year} {current_race} {current_session}")
                            
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                        
                        # 初始化模組
                        if not module.initialize_module():
                            logger.error(f"[ERROR] [MODULE_FACTORY] 全車手煞車圖表模組初始化失敗")
                            return None
                        
                        logger.debug(f"[OK] [MODULE_FACTORY] 全車手煞車圖表模組初始化成功")
                        return self.main_window._mark_module_factory_type(module, module_type)
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 全車手煞車圖表模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理全車手煞車性能分析模組 ⭐ F34 新增
                elif module_type == "all_drivers_brake_performance":
                    try:
                        logger.debug(f"[DEBUG] [MODULE_FACTORY] 開始創建全車手煞車性能分析模組...")
                        from modules.gui.all_drivers.brake.all_drivers_brake_performance_mdi import (
                            AllDriversBrakePerformanceMDI
                        )
                        logger.debug(f"[OK] [MODULE_FACTORY] 全車手煞車性能 MDI 導入成功")
                        
                        # 創建 MDI 實例
                        module = AllDriversBrakePerformanceMDI(parent=self.main_window)
                        logger.debug(f"✅ [MODULE_FACTORY] 全車手煞車性能 MDI 實例創建成功")
                        
                        # 設置參數提供者
                        module.parameter_provider = parameter_provider
                        
                        # 設置參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race()
                            current_session = parameter_provider.get_current_session()
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 全車手煞車性能模組參數預設為: {current_year} {current_race} {current_session}")
                            
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                        
                        # 初始化模組
                        if not module.initialize_module():
                            logger.error(f"[ERROR] [MODULE_FACTORY] 全車手煞車性能模組初始化失敗")
                            return None
                        
                        logger.debug(f"[OK] [MODULE_FACTORY] 全車手煞車性能模組初始化成功")
                        return self.main_window._mark_module_factory_type(module, module_type)
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 全車手煞車性能模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理全車手煞車全圈數分析模組 ⭐ F122 新增
                elif module_type == "all_drivers_brake_all_laps":
                    try:
                        logger.debug(f"[DEBUG] [MODULE_FACTORY] 開始創建全車手煞車全圈數分析模組...")
                        from modules.gui.all_drivers.brake.all_drivers_brake_all_laps_mdi import (
                            AllDriversBrakeAllLapsMDI
                        )
                        logger.debug(f"[OK] [MODULE_FACTORY] 全車手煞車全圈數 MDI 導入成功")
                        
                        # 創建 MDI 實例
                        module = AllDriversBrakeAllLapsMDI(parent=self.main_window)
                        logger.debug(f"[OK] [MODULE_FACTORY] 全車手煞車全圈數 MDI 實例創建成功")
                        
                        # 設置參數提供者
                        module.parameter_provider = parameter_provider
                        
                        # 設置參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race()
                            current_session = parameter_provider.get_current_session()
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 全車手煞車全圈數模組參數預設為: {current_year} {current_race} {current_session}")
                            
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                        
                        # 初始化模組
                        if not module.initialize_module():
                            logger.error(f"[ERROR] [MODULE_FACTORY] 全車手煞車全圈數模組初始化失敗")
                            return None
                        
                        logger.debug(f"[OK] [MODULE_FACTORY] 全車手煞車全圈數模組初始化成功")
                        return self.main_window._mark_module_factory_type(module, module_type)
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 全車手煞車全圈數模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理車手比賽排名分析模組 ⭐ F25 新增
                elif module_type == "driver_position_analysis":
                    try:
                        logger.debug(f"[DEBUG] [MODULE_FACTORY] 開始創建車手比賽排名分析模組...")
                        from modules.gui.race_analysis.position.driver_position_analysis_mdi import (
                            DriverPositionAnalysisMDI
                        )
                        logger.debug(f"[OK] [MODULE_FACTORY] 車手比賽排名 MDI 導入成功")
                        
                        # 創建 MDI 實例
                        module = DriverPositionAnalysisMDI(parent=self.main_window)
                        logger.debug(f"✅ [MODULE_FACTORY] 車手比賽排名 MDI 實例創建成功")
                        
                        # 設置參數提供者
                        module.parameter_provider = parameter_provider
                        
                        # 設置參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race()
                            current_session = parameter_provider.get_current_session()
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 車手比賽排名模組參數預設為: {current_year} {current_race} {current_session}")
                            
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                        
                        # 初始化模組
                        if not module.initialize_module():
                            logger.error(f"[ERROR] [MODULE_FACTORY] 車手比賽排名模組初始化失敗")
                            return None
                        
                        logger.debug(f"[OK] [MODULE_FACTORY] 車手比賽排名模組初始化成功")
                        return self.main_window._mark_module_factory_type(module, module_type)
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 車手比賽排名模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理 FIA Parts Analysis 模組 ⭐ 新增
                elif module_type == "parts_analysis":
                    try:
                        logger.debug(f"[DEBUG] [MODULE_FACTORY] 開始創建 FIA Parts Analysis 模組...")
                        from modules.gui.partupdated_analysis.parts_analysis_mdi import PartsAnalysisMDI
                        logger.debug(f"[OK] [MODULE_FACTORY] FIA Parts Analysis MDI 導入成功")
                        
                        # 創建 MDI 實例
                        mdi_module = PartsAnalysisMDI(parent=self.main_window)
                        logger.debug(f"✅ [MODULE_FACTORY] FIA Parts Analysis MDI 實例創建成功")
                        
                        # 設置參數提供者
                        mdi_module.parameter_provider = parameter_provider
                        
                        # 設置參數
                        if parameter_provider:
                            current_year = parameter_provider.get_current_year()
                            logger.debug(f"[INIT] [MODULE_FACTORY] FIA Parts Analysis 模組參數預設為: 年份={current_year}")
                            mdi_module.year = str(current_year)
                        else:
                            mdi_module.year = "2025"
                        
                        # ✅ 初始化模組（UniversalAnalysisMDI 要求）
                        logger.debug(f"[INIT] [MODULE_FACTORY] 初始化 FIA Parts Analysis 模組...")
                        if not mdi_module.initialize_module(parent_widget=self):
                            raise RuntimeError("Module initialization failed")
                        logger.debug(f"✅ [MODULE_FACTORY] FIA Parts Analysis 模組初始化成功")
                        
                        # ✅ 返回 MDI 模組本身（它實現了 get_widget() 方法）
                        logger.debug(f"[OK] [MODULE_FACTORY] FIA Parts Analysis 模組創建成功（返回 MDI 模組）")
                        return self.main_window._mark_module_factory_type(mdi_module, module_type)
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] FIA Parts Analysis 模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理彎道性能分析模組 (F47) - 統一處理所有類型
                elif module_type == "corner_performance":
                    try:
                        # 🔑 根據 matched_keyword 判斷彎道類型
                        corner_type = "low_speed"  # 預設
                        if matched_keyword:
                            keyword_lower = matched_keyword.lower()
                            if "mid" in keyword_lower or "中速" in keyword_lower:
                                corner_type = "mid_speed"
                            elif "high" in keyword_lower or "高速" in keyword_lower:
                                corner_type = "high_speed"
                            # 其他情況保持 low_speed
                        
                        logger.debug(f"[DEBUG] [MODULE_FACTORY] 開始創建彎道性能分析模組 (corner_type={corner_type})...")
                        from modules.gui.all_drivers.corner_performance.all_drivers_corner_performance_mdi import (
                            AllDriversCornerPerformanceMDI
                        )
                        logger.debug(f"[OK] [MODULE_FACTORY] 彎道性能分析 MDI 導入成功")
                        
                        # 創建 MDI 實例（傳遞彎道類型）
                        module = AllDriversCornerPerformanceMDI(parent=self.main_window, corner_type=corner_type)
                        logger.debug(f"✅ [MODULE_FACTORY] 彎道性能分析 MDI 實例創建成功 (corner_type={corner_type})")
                        
                        # 設置參數提供者
                        module.parameter_provider = parameter_provider
                        
                        # 設置參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race()
                            current_session = parameter_provider.get_current_session()
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 彎道性能分析模組參數預設為: {current_year} {current_race} {current_session}")
                            
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                        
                        # 初始化模組
                        if not module.initialize_module():
                            logger.error(f"[ERROR] [MODULE_FACTORY] 彎道性能分析模組初始化失敗")
                            return None
                        
                        logger.debug(f"[OK] [MODULE_FACTORY] 彎道性能分析模組初始化成功")
                        return self.main_window._mark_module_factory_type(module, module_type)
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 彎道性能分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理速度分析模組
                elif module_type == "speed_analysis":
                    try:
                        from modules.gui.lap_analysis.speed_analysis.speed_analysis_mdi import SpeedAnalysisModule
                        logger.debug(f"[OK] [MODULE_FACTORY] 創建速度分析模組實例")
                        
                        # 創建模組實例並設置參數提供者
                        module = SpeedAnalysisModule()
                        module.parameter_provider = parameter_provider
                        
                        # 在初始化前先設置當前參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            # 直接設置模組參數，避免Unknown標題
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 速度分析模組參數預設為: {current_year} {current_race} {current_session}")
                        
                        # 初始化模組
                        if module.initialize_module():
                            logger.debug(f"[OK] [MODULE_FACTORY] 速度分析模組初始化成功")
                            return self.main_window._mark_module_factory_type(module, module_type)
                        else:
                            logger.error(f"[ERROR] [MODULE_FACTORY] 速度分析模組初始化失敗")
                            return None
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 速度分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理RPM分析模組
                elif module_type == "rpm_analysis":
                    try:
                        from modules.gui.lap_analysis.rpm_analysis.rpm_analysis_mdi import RPMAnalysisModule
                        logger.debug(f"[OK] [MODULE_FACTORY] 創建RPM分析模組實例")
                        
                        # 創建模組實例並設置參數提供者
                        module = RPMAnalysisModule()
                        module.parameter_provider = parameter_provider
                        
                        # 在初始化前先設置當前參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            # 直接設置模組參數，避免Unknown標題
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] RPM分析模組參數預設為: {current_year} {current_race} {current_session}")
                        
                        # 初始化模組
                        if module.initialize_module():
                            logger.debug(f"[OK] [MODULE_FACTORY] RPM分析模組初始化成功")
                            return self.main_window._mark_module_factory_type(module, module_type)
                        else:
                            logger.error(f"[ERROR] [MODULE_FACTORY] RPM分析模組初始化失敗")
                            return None
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] RPM分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理加速度分析模組
                elif module_type == "acceleration_analysis":
                    try:
                        from modules.gui.lap_analysis.acceleration_analysis.acceleration_analysis_mdi import accelerationAnalysisModule
                        logger.debug(f"[OK] [MODULE_FACTORY] 創建加速度分析模組實例")
                        
                        # 創建模組實例並設置參數提供者
                        module = accelerationAnalysisModule()
                        module.parameter_provider = parameter_provider
                        
                        # 在初始化前先設置當前參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            # 直接設置模組參數，避免Unknown標題
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 加速度分析模組參數預設為: {current_year} {current_race} {current_session}")
                        
                        # 初始化模組
                        if module.initialize_module():
                            logger.debug(f"[OK] [MODULE_FACTORY] 加速度分析模組初始化成功")
                            return self.main_window._mark_module_factory_type(module, module_type)
                        else:
                            logger.error(f"[ERROR] [MODULE_FACTORY] 加速度分析模組初始化失敗")
                            return None
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 加速度分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理速度差分析模組
                elif module_type == "speeddiff_analysis":
                    try:
                        from modules.gui.lap_analysis.speeddiff_analysis.speeddiff_analysis_mdi import SpeeddiffAnalysisModule
                        logger.debug(f"[OK] [MODULE_FACTORY] 創建速度差分析模組實例")
                        
                        # 創建模組實例並設置參數提供者
                        module = SpeeddiffAnalysisModule()
                        module.parameter_provider = parameter_provider
                        
                        # 在初始化前先設置當前參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            # 直接設置模組參數，避免Unknown標題
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 速度差分析模組參數預設為: {current_year} {current_race} {current_session}")
                        
                        # 初始化模組
                        if module.initialize_module():
                            logger.debug(f"[OK] [MODULE_FACTORY] 速度差分析模組初始化成功")
                            return self.main_window._mark_module_factory_type(module, module_type)
                        else:
                            logger.error(f"[ERROR] [MODULE_FACTORY] 速度差分析模組初始化失敗")
                            return None
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 速度差分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理距離差分析模組
                elif module_type == "distancediff_analysis":
                    try:
                        from modules.gui.lap_analysis.distancediff_analysis.distancediff_analysis_mdi import distancediffAnalysisModule
                        logger.debug(f"[OK] [MODULE_FACTORY] 創建距離差分析模組實例")
                        
                        # 創建模組實例並設置參數提供者
                        module = distancediffAnalysisModule()
                        module.parameter_provider = parameter_provider
                        
                        # 在初始化前先設置當前參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            # 直接設置模組參數，避免Unknown標題
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 距離差分析模組參數預設為: {current_year} {current_race} {current_session}")
                        
                        # 初始化模組
                        if module.initialize_module():
                            logger.debug(f"[OK] [MODULE_FACTORY] 距離差分析模組初始化成功")
                            return self.main_window._mark_module_factory_type(module, module_type)
                        else:
                            logger.error(f"[ERROR] [MODULE_FACTORY] 距離差分析模組初始化失敗")
                            return None
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 距離差分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理時間差分析模組
                elif module_type == "timediff_analysis":
                    try:
                        from modules.gui.lap_analysis.timediff_analysis.timediff_analysis_mdi import timediffAnalysisModule
                        logger.debug(f"[OK] [MODULE_FACTORY] 創建時間差分析模組實例")
                        
                        # 創建模組實例並設置參數提供者
                        module = timediffAnalysisModule()
                        module.parameter_provider = parameter_provider
                        
                        # 在初始化前先設置當前參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            # 直接設置模組參數，避免Unknown標題
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 時間差分析模組參數預設為: {current_year} {current_race} {current_session}")
                        
                        # 初始化模組
                        if module.initialize_module():
                            logger.debug(f"[OK] [MODULE_FACTORY] 時間差分析模組初始化成功")
                            return self.main_window._mark_module_factory_type(module, module_type)
                        else:
                            logger.error(f"[ERROR] [MODULE_FACTORY] 時間差分析模組初始化失敗")
                            return None
                    except Exception as e:
                        logger.error(f"[ERROR] [MODULE_FACTORY] 時間差分析模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理歷年賽道旗幟統計模組 (F100)
                elif module_type == "historical_track_map":
                    try:
                        logger.debug(f"[DEBUG]    [MODULE_FACTORY] 開始創建歷年賽道旗幟統計模組...")
                        from modules.gui.race_analysis.track_map.historical_track_map_mdi import HistoricalTrackMapMDI
                        logger.debug(f"[OK] [MODULE_FACTORY] 歷年賽道旗幟統計模組導入成功")
                        
                        # 獲取當前參數
                        if parameter_provider:
                            current_year = int(parameter_provider.get_current_year())
                            current_race = parameter_provider.get_current_race() 
                            current_session = parameter_provider.get_current_session()
                            
                            logger.debug(f"[INIT] [MODULE_FACTORY] 歷年賽道旗幟統計模組參數: {current_year} {current_race} {current_session}")
                            
                            # 創建模組實例
                            module = HistoricalTrackMapMDI(parent=None)
                            
                            # ✅ 關鍵修復：在初始化前設置參數
                            module.current_year = str(current_year)
                            module.current_race = current_race
                            module.current_session = current_session
                            logger.debug(f"[INIT] [MODULE_FACTORY] ✅ 參數已預設: {module.current_year} {module.current_race} {module.current_session}")
                            
                            # 初始化模組
                            if module.initialize_module():
                                logger.debug(f"[OK] [MODULE_FACTORY] 歷年賽道旗幟統計模組初始化成功")
                                
                                # ❌ 移除重複調用：initialize_module() 已經調用 load_initial_data()
                                # 再次調用 update_lap_parameters() 會導致數據被載入兩次，
                                # 第二次載入可能返回不完整的 track_data，導致 sector_boundaries 被清空
                                # 
                                # module.update_lap_parameters(current_year, current_race, current_session)
                                # print(f"[OK] [MODULE_FACTORY] 歷年賽道旗幟統計模組參數已設置")
                                
                                logger.debug(f"[OK] [MODULE_FACTORY] 歷年賽道旗幟統計模組已就緒（跳過重複參數設置）")
                                
                                return self.main_window._mark_module_factory_type(module, module_type)
                            else:
                                logger.error(f"[ERROR] [MODULE_FACTORY] 歷年賽道旗幟統計模組初始化失敗")
                                return None
                        else:
                            logger.error(f"[ERROR] 歷年賽道旗幟統計模組創建失敗：無參數")
                            return None
                    except Exception as e:
                        logger.error(f"[ERROR] 歷年賽道旗幟統計模組創建失敗: {e}")
                        import traceback
                        traceback.print_exc()
                        return None
                
                # 處理其他模組類型...
                else:
                    logger.debug(f"[INFO] [MODULE_FACTORY] 模組類型 {module_type} 尚未實現")
                    return None
            
            logger.debug(f"[INFO] [MODULE_FACTORY] 無法找到匹配的模組類型: {function_name}")
            return None
            
        except Exception as e:
            logger.error(f"[ERROR] [MODULE_FACTORY] 模組創建失敗: {e}")
            import traceback
            traceback.print_exc()  # ✅ 添加完整的異常追蹤
            return None
        return None
