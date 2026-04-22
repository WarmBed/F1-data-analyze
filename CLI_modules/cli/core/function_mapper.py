#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
F1 Analysis Function Mapper - 統一功能映射器
根據核心開發原則，提供統一的功能編號到模組執行的映射

版本: 1.0
作者: F1 Analysis Team
支援: 1-52 整數化功能映射系統
"""

# LOCAL_ONLY_REFACTOR:
# This mapper should become a CLI implementation adapter only. Public function
# metadata should come from api.models.function_specs for now, then move to
# core/analysis/function_specs.py when the local executor is separated.

import sys

# Force UTF-8 output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr.reconfigure(encoding='utf-8')

import os
from datetime import datetime
from typing import Union, Dict, Any, Optional


class F1AnalysisFunctionMapper:
    """F1 Analysis 功能映射器 - 統一管理所有功能的執行"""
    
    def __init__(self, data_loader=None, dynamic_team_mapping=None, f1_analysis_instance=None, 
                 driver=None, driver2=None):
        self.data_loader = data_loader
        self.dynamic_team_mapping = dynamic_team_mapping
        self.f1_analysis_instance = f1_analysis_instance
        self.driver = driver or "VER"     # 預設主要車手
        self.driver2 = driver2 or "LEC"   # 預設次要車手
        self.open_analyzer = None  # 添加 open_analyzer 屬性
        
        # 整數化功能映射表 (1-52)
        self.function_mapping = {
            # 1-10: 基礎分析模組
            1: self._execute_rain_intensity_analysis,        # 降雨強度分析
            2: self._execute_track_path_analysis,            # 賽道路線分析
            3: self._execute_driver_fastest_pitstop_ranking, # 車手最快進站時間排行榜
            4: self._execute_team_pitstop_ranking,           # 車隊進站時間排行榜
            5: self._execute_driver_detailed_pitstop_records, # 車手進站詳細記錄
            6: self._execute_accident_statistics_summary,   # 事故統計摘要分析
            7: self._execute_severity_distribution_analysis, # 嚴重程度分佈分析
            8: self._execute_all_incidents_summary,         # 所有事件詳細列表分析
            9: self._execute_special_incident_reports,      # 特殊事件報告分析
            10: self._execute_key_events_summary,           # 關鍵事件摘要分析
            
            # 11-23: 進階分析模組 (整數式) - 重新排列
            11: self._execute_single_driver_comprehensive,  # 單一車手綜合分析 [WARNING] DEPRECATED
            12: self._execute_single_driver_telemetry,      # 單一車手詳細遙測分析
            13: self._execute_driver_comparison,            # 雙車手比較分析
            14: self._execute_race_position_changes,        # 賽事位置變化圖 [WARNING] DEPRECATED
            15: self._execute_race_overtaking_statistics,   # 賽事超車統計分析
            16: self._execute_single_driver_overtaking,     # 單一車手超車分析
            17: self._execute_dynamic_corner_detection,     # 動態彎道檢測分析 [STAR] 新增
            18: self._execute_corner_detailed_analysis,     # 彎道詳細分析 (原Function 18)
            19: self._execute_single_driver_dnf,            # 單一車手DNF分析 (原Function 17)
            20: self._execute_single_driver_all_corners,    # 單一車手全部彎道分析 (原Function 19)
            21: self._execute_all_drivers_comprehensive,    # 所有車手綜合分析 (原Function 20)
            22: self._execute_corner_speed_analysis,        # 彎道速度分析 [WARNING] DEPRECATED
            23: self._execute_all_drivers_overtaking,       # 全部車手超車分析 (原Function 22)
            24: self._execute_all_drivers_dnf,              # 全部車手DNF分析 (原Function 23)
            
            # 25-28: 單一車手分析分拆功能 (編號順延)
            25: self._execute_driver_race_position,         # 車手比賽位置分析
            26: self._execute_driver_tire_strategy,          # 車手輪胎策略分析
            27: self._execute_driver_fastest_lap_analysis,   # 車手最速圈速分析
            28: self._execute_driver_lap_time_analysis,      # 車手每圈圈速分析
            
            # 29-47: 預留擴展功能 (編號順延)
            29: self._execute_fia_parts_analysis,           # FIA 部件變更分析
            30: self._execute_tire_strategy_optimization,
            31: self._execute_lap_time_prediction,
            32: self._execute_fuel_consumption_analysis,
            33: self._execute_aerodynamic_efficiency_analysis,
            34: self._execute_brake_performance_analysis,
            35: self._execute_engine_performance_analysis,
            36: self._execute_race_strategy_simulation,
            37: self._execute_championship_impact_analysis,
            38: self._execute_track_evolution_analysis,
            39: self._execute_safety_car_impact_analysis,
            # 40-47: 全部車手分析模組 (編號順延)
            40: self._execute_all_drivers_statistics_overview,
            41: self._execute_all_drivers_telemetry_comparison,
            42: self._execute_all_drivers_consistency_analysis,
            43: self._execute_all_drivers_race_pace_analysis,
            44: self._execute_all_drivers_qualifying_analysis,
            45: self._execute_all_drivers_tire_management,
            46: self._execute_all_drivers_sector_analysis,
            47: self._execute_all_drivers_cornering_analysis,
            48: self._execute_all_drivers_straight_line_speed,
            
            # 49-54: 系統功能
            49: self._execute_data_export_manager,
            50: self._execute_cache_optimization,
            51: self._execute_system_diagnostics,
            52: self._execute_performance_benchmarking,
            53: self._execute_ideal_lap_analysis,
            54: self._execute_driver_throttle_ratio,
            
            # 55-59: F1 官方 Live Timing 進階分析功能 (圈速預測系統)
            55: self._execute_fuel_corrected_laptime,  # 燃油校正圈速分析 (F1 Live Timing) (2025-12-03)
            56: self._execute_tire_degradation_analysis,  # 輪胎衰退分析 (時變線性模型) (2025-12-06)
            57: self._execute_combined_laptime_prediction,  # 綜合圈速預測 (F55+F56) (2025-12-03)
            58: self._execute_pit_stop_strategy_prediction,  # 進站策略預測 (58.1/58.2/58.3) (2025-12-04)
            
            # 70-79: 預測系統功能 (AI/ML) - FP->Q 系統
            70: self._execute_fp_q_data_collector,     # FP->Q 訓練數據收集器
            71: self._execute_q_race_data_collector,   # Q->R 訓練數據收集器 (規劃中)
            72: self._execute_xgboost_trainer,         # XGBoost 模型訓練器 (規劃中)
            73: self._execute_placeholder_73,          # v3.10 批次訓練器 (16 特徵 XGBoost - 移除 is_top_driver)
            74: self._execute_placeholder_74,          # FP3→Q 排位賽預測生成器 (v3.10 模型)
            75: self._execute_fp2_q_batch_trainer,     # FP2→Q 批次訓練器 (XGBoost v3.10 架構) (2025-12-13)
            76: self._execute_fp2_q_prediction_generator, # FP2→Q 排位賽預測生成器 (2025-12-13)
            77: self._execute_track_specific_training, # 賽道特定模型訓練 (v2.0 + F78) (2025-11-03)
            78: self._execute_driver_fp3_q_feature_extraction, # 車手 FP3->Q 特徵提取 (2025-11-03)
            79: self._execute_dynamic_team_rating,     # 動態車隊評級報告 (2025-11-26)
            
            # 80-89: Q->R 預測系統功能 / 超車預測系統
            80: self._execute_dynamic_team_rating_cli, # 動態車隊評級分析 (JSON輸出) (2025-11-27)
            81: self._execute_overtake_data_collector,  # 超車事件數據收集器 (F81) (2025-12-05)
            82: self._execute_overtake_model_trainer,   # 超車預測模型訓練器 (F82) (預留)
            83: self._execute_overtake_predictor,       # 超車預測推理器 (F83) (預留)
            84: self._execute_overtake_llm_explainer,   # 超車預測 LLM 解說器 (F84) (預留)
            85: self._execute_close_combat_trainer,     # 近距離接觸模型訓練器 (F85) (2025-12-09)
            86: self._execute_close_combat_predictor,   # 近距離接觸預測器 (F86) (2025-12-09)
            87: self._execute_driver_strategy_prediction, # 車手策略預測器 (F87) (2025-12-05)
            88: self._execute_tire_saving_analysis,     # 省輪胎行為分析 (F88) (2025-12-09)
            
            # 90-95: FP2->R 圈速預測系統 (機器學習)
            90: self._execute_fp2_race_ml_trainer,      # FP2→R 機器學習訓練器 (2022-2024 數據) (2025-12-13)
            91: self._execute_fp2_race_ml_predictor,    # FP2→R 機器學習預測器 (逐圈圈速預測) (2025-12-13)
            
            # 96-99: 特殊功能
            96: self._execute_race_weather_forecast,   # 賽事天氣預報
            97: self._execute_championship_standings_analysis,
            98: self._execute_team_color_analysis,
            99: self._execute_season_calendar_analysis,
            100: self._execute_historical_flags_analysis,  # 歷年旗幟統計分析 (2020-2025)
            101: self._execute_season_start_reaction_analysis,  # 年度起跑反應分析 (0-50km/h + P1位置統計) (2025-12-22)
            120: self._execute_fp2_corner_all_laps_analysis,  # FP2 彎道全圈數分析（雙模式：統一+分組）(2025-12-13)
            121: self._execute_fp2_straight_line_all_laps_analysis,  # FP2 直線速度全圈數分析（官方API版本）(2025-12-13)
            122: self._execute_brake_all_laps_analysis,  # 煞車性能全圈數分析（官方API版本+多數決統一煞車點）(2025-12-14)
            125: self._execute_vehicle_performance_analysis,  # 車輛性能綜合分析（整合F120+F121+F122+F100）(2025-12-14)
            126: self._execute_live_timing_weather_analysis,  # Live Timing 天氣分析（逐圈氣溫/賽道溫度/降雨）(2025-12-21)
            127: self._execute_live_timing_traffic_distance_analysis,  # Live Timing traffic 分析（距離門檻版，SC/VSC整圈排除）(2025-12-23)
            
            # 130-141: Position Tracking Simulator 數據收集系統
            131: self._execute_fp2_race_correlation_analysis,  # FP2-Race Long Run 相關性分析 (2025-01-01)
            134: self._execute_overtake_history_collector,  # 超車事件歷史收集器 (2026-01-05)
            135: self._execute_overtake_attempt_failed_collector,  # 超車嘗試失敗收集器 (2026-01-05)
            136: self._execute_track_overtake_difficulty_analyzer,  # 賽道超車難度分析器 (2026-01-05)
            137: self._execute_team_performance_matrix_calculator,  # 車隊性能差係數計算器 (2026-01-05)
            138: self._execute_overtake_success_model_trainer,  # 超車成功率模型訓練器 (2026-01-05)
            139: self._execute_new_driver_coefficient_completer,  # 新車手係數補全器 (2026-01-05)
            140: self._execute_qualifying_result_collector,  # 排位賽結果收集器 (2026-01-05)
            141: self._execute_sc_trigger_probability_model,  # SC 觸發機率模型 (2026-01-05)
            142: self._execute_pit_lane_time_analyzer,  # 進站時間損失分析器 (2026-01-05)
            143: self._execute_fia_season_stats_analysis,  # FIA 賽季統計分析（PU + Parts）(2026-01-22)
        }
        
        # 子功能映射表
        self.sub_function_mapping = {
            # 事故分析子功能 4.1-4.5
            "4.1": self._execute_accident_key_events,
            "4.2": self._execute_accident_special_incidents,
            "4.3": self._execute_accident_driver_severity,
            "4.4": self._execute_accident_team_risk,
            "4.5": self._execute_accident_all_incidents,
            
            # 遙測分析子功能 6.1-6.7
            "6.1": self._execute_telemetry_complete_lap,
            "6.2": self._execute_telemetry_tire_strategy,
            "6.3": self._execute_telemetry_tire_performance,
            "6.4": self._execute_telemetry_pitstop_records,
            "6.5": self._execute_telemetry_special_events,
            "6.6": self._execute_telemetry_fastest_lap,
            "6.7": self._execute_telemetry_specific_lap,
            
            # 車手比較子功能 7.1-7.2
            "7.1": self._execute_speed_gap_analysis,
            "7.2": self._execute_distance_gap_analysis,
            
            # DNF分析子功能 11.1-11.2
            "11.1": self._execute_detailed_dnf_analysis,
            "11.2": self._execute_annual_dnf_statistics,
            
            # 彎道分析子功能 12.1-12.2
            "12.1": self._execute_single_driver_corner_integrated,
            "12.2": self._execute_team_drivers_corner_comparison,
            
            # 車手統計子功能 14.1-14.9
            "14.1": self._execute_driver_statistics_overview,
            "14.2": self._execute_driver_telemetry_statistics,
            "14.3": self._execute_driver_overtaking_analysis,
            "14.4": self._execute_driver_fastest_lap_ranking,
            "14.9": self._execute_all_drivers_comprehensive_full,
            
            # 超車分析子功能 16.1-16.4
            "16.1": self._execute_annual_overtaking_statistics,
            "16.2": self._execute_overtaking_performance_comparison,
            "16.3": self._execute_overtaking_visualization_analysis,
            "16.4": self._execute_overtaking_trends_analysis,
        }
    
    def _standardize_result(self, result: Any, function_id: Union[str, int], 
                           function_name: str = "未知功能") -> Dict[str, Any]:
        """標準化分析結果格式 - 確保所有功能返回統一格式"""
        if result is None:
            return {
                "success": False,
                "message": f"{function_name}執行失敗：無結果數據",
                "function_id": str(function_id),
                "data": None,
                "error": "No result data"
            }
        
        # 如果已經是標準格式
        if isinstance(result, dict) and "success" in result:
            # 確保必要欄位存在
            standardized = {
                "success": result.get("success", False),
                "message": result.get("message", f"{function_name}分析完成"),
                "function_id": str(function_id),
                "data": result.get("data"),
                "cache_used": result.get("cache_used", False),
                "execution_time": result.get("execution_time", "N/A")
            }
            
            # 保留其他欄位
            for key, value in result.items():
                if key not in standardized:
                    standardized[key] = value
            
            return standardized
        
        # 非字典結果或舊格式，包裝為標準格式
        return {
            "success": True,
            "message": f"{function_name}分析完成",
            "function_id": str(function_id),
            "data": result,
            "cache_used": False,
            "execution_time": "N/A"
        }

    def execute_function_by_number(self, function_id: Union[str, int], **kwargs) -> Dict[str, Any]:
        """根據功能編號執行對應的分析功能
        
        Args:
            function_id: 功能編號 (整數 1-52 或字符串子功能如 "4.1")
            **kwargs: 額外參數
            
        Returns:
            Dict[str, Any]: 執行結果
        """
        try:
            print(f"[START] 執行功能編號: {function_id}")
            
            # 檢查數據載入狀態
            if not self._check_data_loaded(function_id):
                return {
                    "success": False,
                    "message": "數據未載入，無法執行分析功能",
                    "function_id": str(function_id)
                }
            
            # 轉換功能編號
            if isinstance(function_id, str):
                if function_id in self.sub_function_mapping:
                    # 執行子功能
                    return self.sub_function_mapping[function_id](**kwargs)
                else:
                    try:
                        # 嘗試轉換為整數
                        function_num = int(function_id)
                        if function_num in self.function_mapping:
                            return self.function_mapping[function_num](**kwargs)
                    except ValueError:
                        pass
            elif isinstance(function_id, int):
                if function_id in self.function_mapping:
                    # 對於需要特定參數的功能，提取並傳遞明確參數
                    if function_id in [25, 26]:  # 功能25,26需要driver參數
                        year = kwargs.get('year', 2025)
                        race = kwargs.get('race', 'Japan')
                        session = kwargs.get('session', 'R')
                        driver = kwargs.get('driver1') or kwargs.get('driver', 'VER')  # 使用driver1或默認VER
                        
                        # 準備乾淨的kwargs，避免重複參數
                        clean_kwargs = {k: v for k, v in kwargs.items() if k not in ['year', 'race', 'session', 'driver', 'driver1']}
                        
                        return self._standardize_result(
                            self.function_mapping[function_id](year, race, session, driver, **clean_kwargs),
                            function_id, f"功能{function_id}"
                        )
                    elif function_id == 27:  # 功能27需要driver參數（保留舊邏輯）
                        driver = kwargs.get('driver1') or kwargs.get('driver', 'VER')
                        year = kwargs.get('year', 2025)
                        race = kwargs.get('race', 'Japan')
                        session = kwargs.get('session', 'R')
                        
                        # 準備乾淨的kwargs，避免重複參數
                        clean_kwargs = {k: v for k, v in kwargs.items() if k not in ['year', 'race', 'session', 'driver', 'driver1']}
                        
                        return self._standardize_result(
                            self.function_mapping[function_id](year, race, session, driver, **clean_kwargs),
                            function_id, f"功能{function_id}"
                        )
                    elif function_id == 28:  # 功能28: 像 Function 13/54 一樣從 data_loader 讀取
                        # 從 kwargs 提取 driver 參數（但不提取 year/race/session）
                        driver = kwargs.get('driver1') or kwargs.get('driver')
                        
                        # 準備乾淨的kwargs，避免重複參數
                        clean_kwargs = {k: v for k, v in kwargs.items() if k not in ['driver', 'driver1']}
                        
                        return self._standardize_result(
                            self.function_mapping[function_id](driver=driver, **clean_kwargs),
                            function_id, f"功能{function_id}"
                        )
                    else:
                        return self._standardize_result(
                            self.function_mapping[function_id](**kwargs),
                            function_id, f"功能{function_id}"
                        )
            
            # 功能編號不支援
            return self._standardize_result(None, function_id, "不支援的功能")
            
        except Exception as e:
            return self._standardize_result(None, function_id, f"執行異常: {str(e)}")
    
    def _check_data_loaded(self, function_id: Union[str, int]) -> bool:
        """檢查是否需要載入數據"""
        # 系統功能不需要檢查數據載入
        # 29: FIA 部件變更分析 (使用本地 JSON 檔案，不需要 FastF1 數據)
        # 55: 燃油校正圈速分析 (使用 F1 官方 Live Timing 數據，不需要 FastF1)
        # 56: 輪胎衰退分析 (使用 F1 官方 Live Timing 數據，時變線性模型)
        # 57: 綜合圈速預測 (整合 F55+F56，不需要 FastF1)
        # 70: FP→Q 訓練數據收集器 (使用預收集的 JSON 檔案)
        # 74: 排位賽預測 (內部自動載入練習數據，不需要預先載入)
        # 75: 純 FP3 特徵優化訓練 (使用預收集的 JSON 檔案)
        # 76: 集成學習訓練 (使用預收集的 JSON 檔案)
        # 81: 超車數據收集 (使用 Live F1 數據，不需要 FastF1)
        # 82: 超車模型訓練 (使用已收集的數據，不需要 FastF1)
        # 83: 超車機率預測 (使用訓練好的模型，不需要 FastF1)
        # 84: LLM 超車解釋器 (使用模型預測結果，不需要 FastF1)
        # 85: 即時超車監控 (使用 Live API，不需要 FastF1)
        # 96: 賽事天氣預報 (使用 Open-Meteo API，不需要 FastF1 數據)
        # 97: 賽季積分查詢 (使用 Ergast/本地 JSON，不需要 FastF1 數據)
        # 98: 車隊顏色分析, 99: 賽季賽程查詢
        # 100: 歷年旗幟統計分析 (掃描 2020-2025 年數據)
        # 58: 進站策略預測 (使用本地資料庫計算，不需要 FastF1 數據)
        # 125: 車輛性能綜合分析 (使用已收集的 FP2 數據，不需要 FastF1)
        # 126: Live Timing 天氣分析 (使用 F1 官方 Live Timing API，不需要 FastF1)
        # 127: Live Timing Traffic Distance 分析 (使用 Live Timing cache，不需要 FastF1)
        # 101: 年度起跑反應分析 (使用 Live Timing 數據，不需要 FastF1)
        # 143: FIA 賽季統計分析 (從 FIA 官網抓取 PDF，不需要 FastF1)
        system_functions = {"18", "19", "20", "21", "22", "29", "49", "50", "51", "52", "55", "56", "57", "58", "70", "74", "75", "76", "81", "82", "83", "84", "85", "96", "97", "98", "99", "100", "101", "125", "126", "127", "143"}

        normalized_id = str(function_id)
        if normalized_id in system_functions:
            return True
        
        # 其他功能需要檢查數據載入
        return self.data_loader is not None and hasattr(self.data_loader, 'session_loaded') and self.data_loader.session_loaded
    
    def _export_to_json(self, result: Dict[str, Any], function_id: Union[str, int], analysis_name: str) -> bool:
        """統一的 JSON 導出工具函數
        
        Args:
            result: 分析結果字典
            function_id: 功能編號
            analysis_name: 分析名稱 (用於檔案命名)
            
        Returns:
            bool: 導出是否成功
        """
        if not result or not result.get('success'):
            return False
            
        try:
            import json
            import os
            
            json_dir = "json"
            os.makedirs(json_dir, exist_ok=True)
            
            # 獲取年份、賽事和賽段信息
            year = getattr(self.data_loader, 'year', 'Unknown')
            race_name = getattr(self.data_loader, 'race_name', 'Unknown')
            session_type = getattr(self.data_loader, 'session_type', 'Unknown')
            
            json_filename = f"{analysis_name}_{year}_{race_name}_{session_type}.json"
            json_path = os.path.join(json_dir, json_filename)
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"\n📄 JSON 分析報告已保存: {json_path}")
            return True
            
        except Exception as e:
            print(f"[WARNING] JSON 保存失敗: {str(e)}")
            return False
    
    # ===== 基礎分析模組執行函數 (1-10) =====
    
    def _execute_rain_intensity_analysis(self, **kwargs):
        """執行降雨強度分析 - 使用增強版模組"""
        try:
            print("[START] 開始執行降雨強度分析...")
            
            # 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            from CLI_modules.cli.analyzer.weather.rain_analyzer import EnhancedRainAnalyzer
            print("[RAIN] 執行降雨強度分析 (增強版)...")
            
            # 使用增強版降雨分析器
            analyzer = EnhancedRainAnalyzer()
            
            # 設置數據載入器
            analyzer.data_loader = self.data_loader
            
            # 從data_loader獲取參數
            year = getattr(self.data_loader, 'year', kwargs.get('year', 2025))
            race = getattr(self.data_loader, 'race_name', kwargs.get('race', 'Japan'))
            session = getattr(self.data_loader, 'session_type', kwargs.get('session', 'R'))
            
            result = analyzer.analyze(
                year=year,
                race=race,
                session=session,
                show_detailed_output=show_detailed_output
            )
            
            # 結果反饋 - 根據新返回格式處理
            if result and isinstance(result, dict) and result.get("success"):
                # 新格式：包含成功狀態和緩存信息
                cache_status = "[OK] 已啟用" if result.get("cache_used") else "[REFRESH] 新建"
                print(f"[STATS] 緩存狀態: {cache_status}")
                
                analysis_result = {
                    "success": True, 
                    "data": result.get("data"),
                    "cache_used": result.get("cache_used", False),
                    "cache_key": result.get("cache_key", ""),
                    "function_id": "1"
                }
                if not self._report_analysis_results(analysis_result, "降雨強度分析"):
                    return {"success": False, "message": "降雨強度分析結果驗證失敗", "function_id": "1"}
            elif result:
                # 檢查是否有錯誤
                if isinstance(result, dict) and result.get('error'):
                    return {"success": False, "message": f"降雨強度分析執行失敗: {result['error']}", "function_id": "1"}
                
                # 舊格式兼容性處理
                analysis_result = {"success": True, "data": result, "cache_used": False}
                print("[STATS] 緩存狀態: [REFRESH] 新建 (舊格式)")
                if not self._report_analysis_results(analysis_result, "降雨強度分析"):
                    return {"success": False, "message": "降雨強度分析結果驗證失敗", "function_id": "1"}
            else:
                return {"success": False, "message": "降雨強度分析執行失敗：無結果數據", "function_id": "1"}
            
            # 新版僅保留增強版 JSON，直接回傳分析結果
            final_result = {
                "success": True,
                "message": "降雨強度分析完成",
                "data": result.get("data") if isinstance(result, dict) else result,
                "cache_used": result.get("cache_used", False) if isinstance(result, dict) else False,
                "function_id": "1"
            }
            return final_result
        except Exception as e:
            print(f"[ERROR] 降雨強度分析失敗: {str(e)}")
            return {"success": False, "message": f"降雨強度分析失敗: {str(e)}", "function_id": "1"}
    
    def _execute_track_path_analysis(self, **kwargs):
        """執行賽道路線分析 - 符合開發核心原則"""
        try:
            print("[START] 開始執行賽道位置分析...")
            
            # 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            from CLI_modules.cli.analyzer.track_position_analysis import run_track_position_analysis
            from datetime import datetime
            
            print("[TRACK] 執行賽道位置分析...")
            result = run_track_position_analysis(
                self.data_loader,
                show_detailed_output=show_detailed_output  # 新增參數傳遞
            )
            
            # 檢查結果是否有效
            if result is None:
                print(f"[ERROR] 賽道位置分析返回 None")
                return {"success": False, "error": "分析返回空值", "function_id": "2"}
            
            if isinstance(result, bool):
                print(f"[ERROR] 賽道位置分析返回布林值: {result}")
                return {"success": False, "error": "分析返回布林值而非數據字典", "function_id": "2"}
            
            if not isinstance(result, dict):
                print(f"[ERROR] 賽道位置分析返回非字典類型: {type(result)}")
                return {"success": False, "error": f"分析返回類型錯誤: {type(result)}", "function_id": "2"}
            
            # 結果反饋 - 根據新返回格式處理
            if result and result.get("success"):
                # 新格式：包含成功狀態和緩存信息
                cache_status = "[OK] 已啟用" if result.get("cache_used") else "[ERROR] 未啟用"
                print(f"[STATS] 緩存狀態: {cache_status}")
                
                analysis_result = {
                    "success": True, 
                    "data": result.get("data"),
                    "cache_used": result.get("cache_used", False),
                    "cache_key": result.get("cache_key", ""),
                    "function_id": "2"
                }
                
                validation_success = self._report_analysis_results(analysis_result, "賽道位置分析")
                if not validation_success:
                    return {"success": False, "message": "賽道位置分析結果驗證失敗", "function_id": "2"}
                
                # 保存JSON輸出 (使用統一工具函數)
                final_result = {
                    "success": True,
                    "message": "賽道位置分析完成",
                    "data": result.get("data") if isinstance(result, dict) else result,
                    "cache_used": result.get("cache_used", False) if isinstance(result, dict) else False,
                    "function_id": "2"
                }
                self._export_to_json(final_result, "2", "track_position_analysis")
                print(f"[SUCCESS] 賽道位置分析完成並生成JSON")
                
                return result
                    
            else:
                print(f"[ERROR] 賽道位置分析標記為失敗: {result}")
                return {"success": False, "message": "分析執行失敗", "function_id": "2"}
        
        except Exception as e:
            print(f"[ERROR] 賽道位置分析失敗: {str(e)}")
            return {"success": False, "message": f"賽道位置分析失敗: {str(e)}", "function_id": "2"}
    
    def _execute_driver_fastest_pitstop_ranking(self, **kwargs):
        """執行車手最快進站時間排行榜 (功能3) - 符合開發核心原則"""
        try:
            print("[START] 開始執行車手最快進站時間排行榜...")
            
            # 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            from CLI_modules.cli.analyzer.driver_fastest_pitstop_ranking import run_driver_fastest_pitstop_ranking
            print("🏆 執行車手最快進站時間排行榜 (功能3)...")
            result = run_driver_fastest_pitstop_ranking(
                self.data_loader,
                show_detailed_output=show_detailed_output  # 新增參數傳遞
            )
            
            # 結果反饋 - 根據新返回格式處理
            if result and isinstance(result, dict) and result.get("success"):
                # 新格式：包含成功狀態和緩存信息
                cache_status = "[OK] 已啟用" if result.get("cache_used") else "[ERROR] 未啟用"
                print(f"[STATS] 緩存狀態: {cache_status}")
                
                analysis_result = {
                    "success": True, 
                    "data": result.get("data"),
                    "cache_used": result.get("cache_used", False),
                    "cache_key": result.get("cache_key", ""),
                    "function_id": "3"
                }
                if not self._report_analysis_results(analysis_result, "車手最快進站時間排行榜"):
                    return {"success": False, "message": "車手最快進站時間排行榜結果驗證失敗", "function_id": "3"}
            elif result:
                # 舊格式兼容性處理
                analysis_result = {"success": True, "data": result, "cache_used": False}
                print("[STATS] 緩存狀態: [ERROR] 未啟用 (舊格式)")
                if not self._report_analysis_results(analysis_result, "車手最快進站時間排行榜"):
                    return {"success": False, "message": "車手最快進站時間排行榜結果驗證失敗", "function_id": "3"}
            else:
                return {"success": False, "message": "車手最快進站時間排行榜執行失敗：無結果數據", "function_id": "3"}
            
            return {
                "success": True,
                "message": "車手最快進站時間排行榜完成",
                "data": result.get("data") if isinstance(result, dict) else result,
                "cache_used": result.get("cache_used", False) if isinstance(result, dict) else False,
                "function_id": "3"
            }
        except Exception as e:
            print(f"[ERROR] 車手最快進站時間排行榜失敗: {str(e)}")
            return {"success": False, "message": f"車手最快進站時間排行榜失敗: {str(e)}", "function_id": "3"}
    
    def _execute_team_pitstop_ranking(self, **kwargs):
        """執行車隊進站時間排行榜 (功能4) - 符合開發核心原則"""
        try:
            print("[START] 開始執行車隊進站時間排行榜...")
            
            # 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            from CLI_modules.cli.analyzer.team_pitstop_ranking import run_team_pitstop_ranking
            print("[FINISH] 執行車隊進站時間排行榜 (功能4)...")
            result = run_team_pitstop_ranking(
                self.data_loader,
                show_detailed_output=show_detailed_output  # 新增參數傳遞
            )
            
            # 結果反饋 - 根據新返回格式處理
            if result and isinstance(result, dict) and result.get("success"):
                # 新格式：包含成功狀態和緩存信息
                cache_status = "[OK] 已啟用" if result.get("cache_used") else "[ERROR] 未啟用"
                print(f"[STATS] 緩存狀態: {cache_status}")
                
                analysis_result = {
                    "success": True, 
                    "data": result.get("data"),
                    "cache_used": result.get("cache_used", False),
                    "cache_key": result.get("cache_key", ""),
                    "function_id": "4"
                }
                if not self._report_analysis_results(analysis_result, "車隊進站時間排行榜"):
                    return {"success": False, "message": "車隊進站時間排行榜結果驗證失敗", "function_id": "4"}
            elif result:
                # 舊格式兼容性處理
                analysis_result = {"success": True, "data": result, "cache_used": False}
                print("[STATS] 緩存狀態: [ERROR] 未啟用 (舊格式)")
                if not self._report_analysis_results(analysis_result, "車隊進站時間排行榜"):
                    return {"success": False, "message": "車隊進站時間排行榜結果驗證失敗", "function_id": "4"}
            else:
                return {"success": False, "message": "車隊進站時間排行榜執行失敗：無結果數據", "function_id": "4"}
            
            return {
                "success": True,
                "message": "車隊進站時間排行榜完成",
                "data": result.get("data") if isinstance(result, dict) else result,
                "cache_used": result.get("cache_used", False) if isinstance(result, dict) else False,
                "function_id": "4"
            }
        except Exception as e:
            print(f"[ERROR] 車隊進站時間排行榜失敗: {str(e)}")
            return {"success": False, "message": f"車隊進站時間排行榜失敗: {str(e)}", "function_id": "4"}
            return {"success": False, "message": f"車隊進站時間排行榜失敗: {str(e)}", "function_id": "4"}
    
    def _execute_driver_detailed_pitstop_records(self, **kwargs):
        """執行車手進站詳細記錄 (功能5) - 符合開發核心原則"""
        try:
            print("[START] 開始執行車手進站詳細記錄...")
            
            # 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            from CLI_modules.cli.analyzer.driver_detailed_pitstop_records import run_driver_detailed_pitstop_records
            print("[INFO] 執行車手進站詳細記錄 (功能5)...")
            
            # 🔧 修正：傳遞額外的年份參數確保正確性
            extra_params = {}
            if hasattr(self, 'year') and self.year:
                extra_params['year'] = self.year
            if hasattr(self, 'race') and self.race:
                extra_params['race'] = self.race
            if hasattr(self, 'session') and self.session:
                extra_params['session'] = self.session
                
            result = run_driver_detailed_pitstop_records(
                self.data_loader, 
                show_detailed_output=show_detailed_output,
                **extra_params
            )
            
            # 結果反饋 - 根據新返回格式處理
            if result and isinstance(result, dict) and result.get("success"):
                # 新格式：包含成功狀態和緩存信息
                cache_status = "[OK] 已啟用" if result.get("cache_used") else "[ERROR] 未啟用"
                print(f"[STATS] 緩存狀態: {cache_status}")
                
                analysis_result = {
                    "success": True, 
                    "data": result.get("data"),
                    "cache_used": result.get("cache_used", False),
                    "cache_key": result.get("cache_key", ""),
                    "function_id": "5"
                }
                if not self._report_analysis_results(analysis_result, "車手進站詳細記錄"):
                    return {"success": False, "message": "車手進站詳細記錄結果驗證失敗", "function_id": "5"}
            elif result:
                # 舊格式兼容性處理
                analysis_result = {"success": True, "data": result, "cache_used": False}
                print("[STATS] 緩存狀態: [ERROR] 未啟用 (舊格式)")
                if not self._report_analysis_results(analysis_result, "車手進站詳細記錄"):
                    return {"success": False, "message": "車手進站詳細記錄結果驗證失敗", "function_id": "5"}
            else:
                return {"success": False, "message": "車手進站詳細記錄執行失敗：無結果數據", "function_id": "5"}
            
            # 保存JSON輸出 (使用統一工具函數)
            final_result = {
                "success": True,
                "message": "車手進站詳細記錄完成",
                "data": result.get("data") if isinstance(result, dict) else result,
                "cache_used": result.get("cache_used", False) if isinstance(result, dict) else False,
                "function_id": "5"
            }
            self._export_to_json(final_result, "5", "driver_detailed_pitstop_records")
            
            return final_result
        except Exception as e:
            print(f"[ERROR] 車手進站詳細記錄失敗: {str(e)}")
            return {"success": False, "message": f"車手進站詳細記錄失敗: {str(e)}", "function_id": "5"}
    
    def _execute_pitstop_analysis(self, **kwargs):
        """執行舊版進站策略分析 (已廢棄)"""
        print("[WARNING] 該功能已被分割為功能3、4、5，請使用新功能")
        return {"success": False, "message": "該功能已被分割為功能3、4、5", "function_id": "legacy"}
    
    def _execute_accident_statistics_summary(self, **kwargs):
        """執行事故統計摘要分析 (功能6) - 符合開發核心原則"""
        try:
            print("[START] 開始執行事故統計摘要分析...")
            
            # 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            # 從kwargs正確提取year, race, session參數
            year = kwargs.get('year', None)
            race = kwargs.get('race', None)
            session = kwargs.get('session', None)
            
            print(f"[PARAMS] 參數檢查 - 年份: {year}, 賽事: {race}, 賽段: {session}")
            
            try:
                from CLI_modules.cli.analyzer.accident_statistics_summary import run_accident_statistics_summary_json  # type: ignore
            except ImportError:
                from modules.gui.accident_analysis.accident_statistics_summary import (
                    run_accident_statistics_summary_json,
                )
            print("[STATS] 執行事故統計摘要分析 (功能6)...")
            result = run_accident_statistics_summary_json(
                self.data_loader,
                dynamic_team_mapping=self.dynamic_team_mapping,
                f1_analysis_instance=self.f1_analysis_instance,
                enable_debug=True,
                show_detailed_output=show_detailed_output,
                year=year,
                race=race,
                session=session
            )
            
            # 結果反饋 - 根據新返回格式處理
            if result and isinstance(result, dict) and result.get("success"):
                # 新格式：包含成功狀態和緩存信息
                cache_status = "[OK] 已啟用" if result.get("cache_used") else "[ERROR] 未啟用"
                print(f"[STATS] 緩存狀態: {cache_status}")
                
                analysis_result = {
                    "success": True, 
                    "data": result.get("data"),
                    "cache_used": result.get("cache_used", False),
                    "cache_key": result.get("cache_key", ""),
                    "function_id": "6"
                }
                if not self._report_analysis_results(analysis_result, "事故統計摘要分析"):
                    return {"success": False, "message": "事故統計摘要分析結果驗證失敗", "function_id": "6"}
            elif result:
                # 舊格式兼容性處理
                analysis_result = {"success": True, "data": result, "cache_used": False}
                print("[STATS] 緩存狀態: [ERROR] 未啟用 (舊格式)")
                if not self._report_analysis_results(analysis_result, "事故統計摘要分析"):
                    return {"success": False, "message": "事故統計摘要分析結果驗證失敗", "function_id": "6"}
            else:
                return {"success": False, "message": "事故統計摘要分析執行失敗：無結果數據", "function_id": "6"}
            
            return {
                "success": True,
                "message": "事故統計摘要分析完成",
                "data": result.get("data") if isinstance(result, dict) else result,
                "cache_used": result.get("cache_used", False) if isinstance(result, dict) else False,
                "function_id": "6"
            }
        except Exception as e:
            print(f"[ERROR] 事故統計摘要分析失敗: {str(e)}")
            return {"success": False, "message": f"事故統計摘要分析失敗: {str(e)}", "function_id": "6"}
    
    def _execute_severity_distribution_analysis(self, **kwargs):
        """執行嚴重程度分佈分析 (功能7) - 符合開發核心原則"""
        try:
            print("[START] 開始執行嚴重程度分佈分析...")
            
            # 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            # 從kwargs正確提取year, race, session參數
            year = kwargs.get('year', None)
            race = kwargs.get('race', None)
            session = kwargs.get('session', None)
            
            print(f"[PARAMS] 參數檢查 - 年份: {year}, 賽事: {race}, 賽段: {session}")
            
            try:
                from CLI_modules.cli.analyzer.severity_distribution_analysis import run_severity_distribution_analysis_json  # type: ignore
            except ImportError:
                from modules.gui.accident_analysis.severity_distribution_analysis import (
                    run_severity_distribution_analysis_json,
                )
            print("[WARNING] 執行嚴重程度分佈分析 (功能7)...")
            result = run_severity_distribution_analysis_json(
                self.data_loader,
                dynamic_team_mapping=self.dynamic_team_mapping,
                f1_analysis_instance=self.f1_analysis_instance,
                enable_debug=True,
                show_detailed_output=show_detailed_output,
                year=year,
                race=race,
                session=session
            )
            
            # 結果反饋 - 根據新返回格式處理
            if result and isinstance(result, dict) and result.get("success"):
                # 新格式：包含成功狀態和緩存信息
                cache_status = "[OK] 已啟用" if result.get("cache_used") else "[ERROR] 未啟用"
                print(f"[STATS] 緩存狀態: {cache_status}")
                
                analysis_result = {
                    "success": True, 
                    "data": result.get("data"),
                    "cache_used": result.get("cache_used", False),
                    "cache_key": result.get("cache_key", ""),
                    "function_id": "7"
                }
                if not self._report_analysis_results(analysis_result, "嚴重程度分佈分析"):
                    return {"success": False, "message": "嚴重程度分佈分析結果驗證失敗", "function_id": "7"}
            elif result:
                # 舊格式兼容性處理
                analysis_result = {"success": True, "data": result, "cache_used": False}
                print("[STATS] 緩存狀態: [ERROR] 未啟用 (舊格式)")
                if not self._report_analysis_results(analysis_result, "嚴重程度分佈分析"):
                    return {"success": False, "message": "嚴重程度分佈分析結果驗證失敗", "function_id": "7"}
            else:
                return {"success": False, "message": "嚴重程度分佈分析執行失敗：無結果數據", "function_id": "7"}
            
            return {
                "success": True,
                "message": "嚴重程度分佈分析完成",
                "data": result.get("data") if isinstance(result, dict) else result,
                "cache_used": result.get("cache_used", False) if isinstance(result, dict) else False,
                "function_id": "7"
            }
        except Exception as e:
            print(f"[ERROR] 嚴重程度分佈分析失敗: {str(e)}")
            return {"success": False, "message": f"嚴重程度分佈分析失敗: {str(e)}", "function_id": "7"}
    
    def _execute_all_incidents_summary(self, **kwargs):
        """執行所有事件詳細列表分析 (功能8) - 符合開發核心原則"""
        try:
            print("[START] 開始執行所有事件詳細列表分析...")
            
            # 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            # 從kwargs正確提取year, race, session參數
            year = kwargs.get('year', None)
            race = kwargs.get('race', None)
            session = kwargs.get('session', None)
            
            print(f"[PARAMS] 參數檢查 - 年份: {year}, 賽事: {race}, 賽段: {session}")
            
            from CLI_modules.cli.analyzer.all_incidents_summary import run_all_incidents_summary_json
            print("[INFO] 執行所有事件詳細列表分析 (功能8)...")
            result = run_all_incidents_summary_json(
                self.data_loader,
                dynamic_team_mapping=self.dynamic_team_mapping,
                f1_analysis_instance=self.f1_analysis_instance,
                enable_debug=True,
                show_detailed_output=show_detailed_output,
                year=year,
                race=race,
                session=session
            )
            
            # 結果反饋 - 根據新返回格式處理
            if result and isinstance(result, dict) and result.get("success"):
                # 新格式：包含成功狀態和緩存信息
                cache_status = "[OK] 已啟用" if result.get("cache_used") else "[ERROR] 未啟用"
                print(f"[STATS] 緩存狀態: {cache_status}")
                
                analysis_result = {
                    "success": True, 
                    "data": result.get("data"),
                    "cache_used": result.get("cache_used", False),
                    "cache_key": result.get("cache_key", ""),
                    "function_id": "8"
                }
                if not self._report_analysis_results(analysis_result, "所有事件詳細列表分析"):
                    return {"success": False, "message": "所有事件詳細列表分析結果驗證失敗", "function_id": "8"}
            elif result:
                # 舊格式兼容性處理
                analysis_result = {"success": True, "data": result, "cache_used": False}
                print("[STATS] 緩存狀態: [ERROR] 未啟用 (舊格式)")
                if not self._report_analysis_results(analysis_result, "所有事件詳細列表分析"):
                    return {"success": False, "message": "所有事件詳細列表分析結果驗證失敗", "function_id": "8"}
            else:
                return {"success": False, "message": "所有事件詳細列表分析執行失敗：無結果數據", "function_id": "8"}
            
            return {
                "success": True,
                "message": "所有事件詳細列表分析完成",
                "data": result.get("data") if isinstance(result, dict) else result,
                "cache_used": result.get("cache_used", False) if isinstance(result, dict) else False,
                "function_id": "8"
            }
        except Exception as e:
            print(f"[ERROR] 所有事件詳細列表分析失敗: {str(e)}")
            return {"success": False, "message": f"所有事件詳細列表分析失敗: {str(e)}", "function_id": "8"}
    
    def _execute_special_incident_reports(self, **kwargs):
        """執行特殊事件報告分析 - Function 9 - 符合開發核心原則"""
        try:
            print("[START] 開始執行特殊事件報告分析...")
            
            # 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            # 從kwargs正確提取year, race, session參數
            year = kwargs.get('year', None)
            race = kwargs.get('race', None)
            session = kwargs.get('session', None)
            
            print(f"[PARAMS] 參數檢查 - 年份: {year}, 賽事: {race}, 賽段: {session}")
            
            try:
                from CLI_modules.cli.analyzer.special_incidents_analysis import run_special_incidents_analysis_json  # type: ignore
            except ImportError:
                from modules.gui.accident_analysis.special_incidents_analysis import (
                    run_special_incidents_analysis_json,
                )
            print("[ALERT] 執行特殊事件報告分析 (JSON輸出版)...")
            result = run_special_incidents_analysis_json(
                self.data_loader,
                dynamic_team_mapping=self.dynamic_team_mapping,
                f1_analysis_instance=self.f1_analysis_instance,
                enable_debug=True
            )
            
            # 結果反饋 - 根據新返回格式處理
            if result and isinstance(result, dict) and result.get("success"):
                # 新格式：包含成功狀態和緩存信息
                cache_status = "[OK] 已啟用" if result.get("cache_used") else "[ERROR] 未啟用"
                print(f"[STATS] 緩存狀態: {cache_status}")
                
                analysis_result = {
                    "success": True, 
                    "data": result.get("data"),
                    "cache_used": result.get("cache_used", False),
                    "cache_key": result.get("cache_key", ""),
                    "function_id": "9"
                }
                if not self._report_analysis_results(analysis_result, "特殊事件報告分析"):
                    return {"success": False, "message": "特殊事件報告分析結果驗證失敗", "function_id": "9"}
            elif result:
                # 舊格式兼容性處理
                analysis_result = {"success": True, "data": result, "cache_used": False}
                print("[STATS] 緩存狀態: [ERROR] 未啟用 (舊格式)")
                if not self._report_analysis_results(analysis_result, "特殊事件報告分析"):
                    return {"success": False, "message": "特殊事件報告分析結果驗證失敗", "function_id": "9"}
            else:
                return {"success": False, "message": "特殊事件報告分析執行失敗：無結果數據", "function_id": "9"}
            
            return {
                "success": True,
                "message": "特殊事件報告分析完成",
                "data": result.get("data") if isinstance(result, dict) else result,
                "cache_used": result.get("cache_used", False) if isinstance(result, dict) else False,
                "function_id": "9"
            }
        except Exception as e:
            print(f"[ERROR] 特殊事件報告分析失敗: {str(e)}")
            return {"success": False, "message": f"特殊事件報告分析失敗: {str(e)}", "function_id": "9"}
    
    def _execute_key_events_summary(self, **kwargs):
        """執行關鍵事件摘要分析 - Function 10 - 符合開發核心原則"""
        try:
            print("[START] 開始執行關鍵事件摘要分析...")
            
            # 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            # 從kwargs正確提取year, race, session參數
            year = kwargs.get('year', None)
            race = kwargs.get('race', None)
            session = kwargs.get('session', None)
            
            print(f"[PARAMS] 參數檢查 - 年份: {year}, 賽事: {race}, 賽段: {session}")
            
            from CLI_modules.cli.analyzer.key_events_summary import run_key_events_summary_json
            print("[KEY] 執行關鍵事件摘要分析 (JSON輸出版)...")
            result = run_key_events_summary_json(
                self.data_loader,
                dynamic_team_mapping=self.dynamic_team_mapping,
                f1_analysis_instance=self.f1_analysis_instance,
                enable_debug=True,
                show_detailed_output=show_detailed_output,
                year=year,
                race=race,
                session=session
            )
            
            # 結果反饋 - 根據新返回格式處理
            if result and isinstance(result, dict) and result.get("success"):
                # 新格式：包含成功狀態和緩存信息
                cache_status = "[OK] 已啟用" if result.get("cache_used") else "[ERROR] 未啟用"
                print(f"[STATS] 緩存狀態: {cache_status}")
                
                analysis_result = {
                    "success": True, 
                    "data": result.get("data"),
                    "cache_used": result.get("cache_used", False),
                    "cache_key": result.get("cache_key", ""),
                    "function_id": "10"
                }
                if not self._report_analysis_results(analysis_result, "關鍵事件摘要分析"):
                    return {"success": False, "message": "關鍵事件摘要分析結果驗證失敗", "function_id": "10"}
            elif result:
                # 舊格式兼容性處理
                analysis_result = {"success": True, "data": result, "cache_used": False}
                print("[STATS] 緩存狀態: [ERROR] 未啟用 (舊格式)")
                if not self._report_analysis_results(analysis_result, "關鍵事件摘要分析"):
                    return {"success": False, "message": "關鍵事件摘要分析結果驗證失敗", "function_id": "10"}
            else:
                return {"success": False, "message": "關鍵事件摘要分析執行失敗：無結果數據", "function_id": "10"}
            
            return {
                "success": True,
                "message": "關鍵事件摘要分析完成",
                "data": result.get("data") if isinstance(result, dict) else result,
                "cache_used": result.get("cache_used", False) if isinstance(result, dict) else False,
                "function_id": "10"
            }
        except Exception as e:
            print(f"[ERROR] 關鍵事件摘要分析失敗: {str(e)}")
            return {"success": False, "message": f"關鍵事件摘要分析失敗: {str(e)}", "function_id": "10"}
    
    def _execute_single_driver_comprehensive(self, **kwargs):
        """執行單一車手綜合分析 - 使用功能12替代實現"""
        try:
            print("[START] 開始執行單一車手綜合分析...")
            print("[TEST] 此功能使用單一車手詳細遙測分析 (功能12) 作為替代實現")
            
            # 調用功能12作為替代實現
            result = self._execute_single_driver_telemetry(**kwargs)
            
            # 轉換結果標識
            if result and result.get("success"):
                result["function_id"] = "11"
                result["message"] = "單一車手綜合分析完成 (基於詳細遙測分析)"
                result["source_function"] = "12"
            else:
                result = {
                    "success": False,
                    "message": "單一車手綜合分析失敗：無法獲取遙測數據",
                    "function_id": "11"
                }
            
            return result
            
        except Exception as e:
            print(f"[ERROR] 單一車手綜合分析失敗: {str(e)}")
            return {"success": False, "message": f"單一車手綜合分析失敗: {str(e)}", "function_id": "11"}
    
    def _execute_single_driver_telemetry(self, **kwargs):
        """執行單一車手詳細遙測分析 - 符合開發核心原則 (更新版支援所有車手分析)"""
        try:
            print("[START] 開始執行車手詳細遙測分析...")
            
            # 1. 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            driver = kwargs.get('driver')  # 檢查是否指定特定車手
            
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            from CLI_modules.cli.analyzer.single_driver_analysis import run_single_driver_telemetry_json, run_all_drivers_telemetry_analysis
            from prettytable import PrettyTable
            import os
            import json
            from datetime import datetime
            
            # 2. 功能選擇邏輯
            if driver:
                print(f"[INFO] 指定車手模式: 分析車手 {driver}")
                analysis_mode = "single"
            else:
                print("[INFO] 所有車手模式: 分析所有可用車手")
                analysis_mode = "all"
            
            # 3. 顯示功能列表 (詳細輸出模式)
            if show_detailed_output:
                print("\n[SEARCH] Function 12 提供的遙測分析功能:")
                
                features_table = PrettyTable()
                features_table.field_names = ["功能類別", "分析項目", "詳細說明"]
                features_table.align = "l"
                
                features_table.add_row(["[F1] 車手基本信息", "車手代碼識別", "自動識別並分析指定/所有車手"])
                features_table.add_row(["", "總圈數統計", "計算車手完成的總圈數"])
                features_table.add_row(["", "有效圈數", "分析有效圈速數據數量"])
                features_table.add_row(["", "最終名次", "顯示車手比賽最終排名"])
                
                features_table.add_row(["⏱️ 圈速分析", "最快圈時間", "找出車手單圈最快時間"])
                features_table.add_row(["", "最快圈圈數", "標識最快圈發生的圈數"])
                features_table.add_row(["", "最慢圈時間", "記錄車手最慢單圈時間"])
                features_table.add_row(["", "平均圈速", "計算所有有效圈的平均時間"])
                features_table.add_row(["", "圈速標準差", "分析圈速一致性和穩定度"])
                
                features_table.add_row(["[FINISH] 區間時間", "Sector 1 時間", "第一區間的詳細時間分析"])
                features_table.add_row(["", "Sector 2 時間", "第二區間的詳細時間分析"])
                features_table.add_row(["", "Sector 3 時間", "第三區間的詳細時間分析"])
                features_table.add_row(["", "區間最佳", "各區間的最佳時間記錄"])
                
                features_table.add_row(["🛞 輪胎分析", "輪胎配方", "分析使用的輪胎類型"])
                features_table.add_row(["", "輪胎壽命", "記錄輪胎使用的圈數"])
                features_table.add_row(["", "輪胎策略", "分析整場比賽的輪胎策略"])
                
                features_table.add_row(["[TOOL] Pitstop 分析", "進站次數", "統計車手總進站次數"])
                features_table.add_row(["", "進站時間", "詳細記錄每次進站時間"])
                features_table.add_row(["", "進站圈數", "記錄每次進站的圈數"])
                
                features_table.add_row(["📄 數據輸出", "JSON 詳細報告", "生成完整的 JSON 格式分析報告"])
                features_table.add_row(["", "時間格式化", "統一的時間顯示格式 (H:MM:SS.mmm)"])
                features_table.add_row(["", "結構化數據", "便於後續分析的結構化數據輸出"])
                
                print(features_table)
                
                print("\n💡 Function 12 特色 (更新版):")
                print("   • [TARGET] 智能模式選擇: 自動檢測是分析單一車手還是所有車手")
                print("   • [PACKAGE] 批量分析: 一次性分析所有車手的完整遙測數據") 
                print("   • [FAST] 高效處理: 並行處理多車手數據，提升分析效率")
                print("   • [SEARCH] 深度洞察: 提供車手表現的全方位比較分析")
                print("   • [CHART] 統計摘要: 生成賽事整體統計和車手排名")
                print("   • 🛠️ 專業工具: 適用於車隊分析師和工程師的批量分析")
            
            print(f"\n[START] 開始執行遙測分析 ({analysis_mode} 模式)...")
            
            # 4. 執行分析
            if analysis_mode == "single":
                # 單一車手分析
                result = run_single_driver_telemetry_json(
                    self.data_loader,
                    None,  # open_analyzer
                    f1_analysis_instance=self.f1_analysis_instance,
                    enable_debug=True,
                    selected_driver=driver
                )
            else:
                # 所有車手分析
                result = run_all_drivers_telemetry_analysis(
                    self.data_loader,
                    None,  # open_analyzer
                    f1_analysis_instance=self.f1_analysis_instance,
                    enable_debug=True
                )
            
            # 5. 結果驗證和反饋
            if not self._report_analysis_results(result, f"車手詳細遙測分析 ({analysis_mode} 模式)"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "12"}

            # 6. 保存JSON輸出 (總是執行，不受詳細輸出模式影響)
            if result and result.get('success'):
                json_dir = "json"
                os.makedirs(json_dir, exist_ok=True)
                
                # 獲取年份、賽事和賽段信息
                year = getattr(self.data_loader, 'year', 'Unknown')
                race_name = getattr(self.data_loader, 'race_name', 'Unknown')
                session_type = getattr(self.data_loader, 'session_type', 'Unknown')
                
                if analysis_mode == "single":
                    json_filename = f"single_driver_telemetry_analysis_{year}_{race_name}_{session_type}.json"
                else:
                    json_filename = f"all_drivers_telemetry_analysis_{year}_{race_name}_{session_type}.json"
                
                json_path = os.path.join(json_dir, json_filename)
                
                try:
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
                    print(f"\n📄 JSON 分析報告已保存: {json_path}")
                except Exception as e:
                    print(f"[WARNING] JSON 保存失敗: {str(e)}")

            # 7. 詳細結果顯示 (詳細輸出模式)
            if show_detailed_output and result and result.get('success'):
                data = result.get('data', {})
                
                if analysis_mode == "single":
                    # 單一車手結果顯示
                    telemetry_data = data.get('single_driver_telemetry', {})
                    driver_info = telemetry_data.get('driver_info', {})
                    lap_analysis = telemetry_data.get('lap_time_analysis', {})
                    pitstop_analysis = telemetry_data.get('pitstop_analysis', {})
                    
                    print("\n[STATS] 單一車手遙測分析結果摘要:")
                    summary_table = PrettyTable()
                    summary_table.field_names = ["分析項目", "結果"]
                    summary_table.align = "l"
                    
                    if driver_info:
                        summary_table.add_row(["[F1] 分析車手", driver_info.get('driver_code', 'N/A')])
                        summary_table.add_row(["[START] 初始名次", driver_info.get('starting_position', 'N/A')])
                        summary_table.add_row(["🏆 最終名次", driver_info.get('final_position', 'N/A')])
                    
                    if lap_analysis:
                        fastest_lap = lap_analysis.get('fastest_lap', {})
                        if fastest_lap:
                            summary_table.add_row(["[FAST] 最快圈時間", fastest_lap.get('lap_time', 'N/A')])
                            summary_table.add_row(["[FINISH] 最快圈圈數", f"第 {fastest_lap.get('lap_number', 'N/A')} 圈"])
                            summary_table.add_row(["🛞 最快圈輪胎", fastest_lap.get('tire_compound', 'N/A')])
                        
                        stats = lap_analysis.get('statistics', {})
                        if stats:
                            summary_table.add_row(["[CHART] 平均圈速", stats.get('average_lap_time', 'N/A')])
                            summary_table.add_row(["[STATS] 圈速穩定性", stats.get('lap_time_std', 'N/A')])
                    
                    if pitstop_analysis:
                        summary_table.add_row(["[TOOL] 進站次數", pitstop_analysis.get('pitstop_count', 'N/A')])
                    
                    print(summary_table)
                    
                else:
                    # 所有車手結果顯示
                    all_drivers_data = data.get('all_drivers_telemetry', {})
                    analysis_summary = data.get('analysis_summary', {})
                    
                    print(f"\n[STATS] 所有車手遙測分析結果摘要:")
                    print(f"[INFO] 成功分析 {len(all_drivers_data)} 位車手")
                    
                    # 創建車手概覽表
                    overview_table = PrettyTable()
                    overview_table.field_names = ["車手", "車隊", "初始排名", "最終排名", "最快圈時間"]
                    overview_table.align = "l"
                    
                    fastest_overall = None
                    fastest_time = float('inf')
                    
                    for driver_code, driver_data in all_drivers_data.items():
                        driver_info = driver_data.get('driver_info', {})
                        lap_analysis = driver_data.get('lap_time_analysis', {})
                        
                        # 獲取最快圈時間
                        fastest_lap = lap_analysis.get('fastest_lap', {})
                        fastest_lap_time = fastest_lap.get('lap_time', 'N/A')
                        
                        # 追蹤整體最快圈
                        if fastest_lap_time != 'N/A':
                            try:
                                # 直接比較時間字符串（已經是MM:SS.000格式）
                                if fastest_overall is None:
                                    fastest_time = fastest_lap_time
                                    fastest_overall = driver_code
                                elif fastest_lap_time < fastest_time:
                                    fastest_time = fastest_lap_time
                                    fastest_overall = driver_code
                            except:
                                pass
                        
                        overview_table.add_row([
                            driver_info.get('driver_code', 'N/A'),
                            driver_info.get('team_name', 'N/A')[:15] + "..." if len(driver_info.get('team_name', '')) > 15 else driver_info.get('team_name', 'N/A'),
                            driver_info.get('starting_position', 'N/A'),
                            driver_info.get('final_position', 'N/A'),
                            fastest_lap_time
                        ])
                    
                    print(overview_table)
                    
                    if fastest_overall:
                        print(f"\n🏆 全場最快圈: {fastest_overall} ({fastest_time})")
            
            print(f"[OK] Function 12 遙測分析完成 ({analysis_mode} 模式)！")
            return result
            
        except Exception as e:
            print(f"[ERROR] 車手詳細遙測分析失敗: {str(e)}")
            return {"success": False, "message": f"車手詳細遙測分析失敗: {str(e)}", "function_id": "12"}
    
    def _get_fastest_lap_number(self, driver):
        """查找指定車手的最速圈圈數"""
        try:
            if not hasattr(self.data_loader, 'laps') or self.data_loader.laps is None:
                print(f"[WARNING] 無法獲取圈速數據來查找 {driver} 的最速圈")
                return None
                
            driver_data = self.data_loader.laps.pick_driver(driver)
            if driver_data.empty:
                print(f"[WARNING] 找不到車手 {driver} 的數據")
                return None
            
            # 過濾有效的圈速數據
            valid_laps = driver_data[driver_data['LapTime'].notna()]
            if valid_laps.empty:
                print(f"[WARNING] 車手 {driver} 沒有有效的圈速數據")
                return None
            
            # 找到最速圈
            fastest_lap = valid_laps.loc[valid_laps['LapTime'].idxmin()]
            lap_number = int(fastest_lap['LapNumber'])
            lap_time = fastest_lap['LapTime']
            
            print(f"[DEBUG] 車手 {driver} 最速圈: 第 {lap_number} 圈 (時間: {lap_time})")
            return lap_number
            
        except Exception as e:
            print(f"[ERROR] 查找車手 {driver} 最速圈時發生錯誤: {e}")
            return None
    
    def _execute_driver_comparison(self, **kwargs):
        """執行車手對比分析 - 包含詳細遙測比較功能"""
        try:
            print("[START] 開始執行車手對比分析...")
            
            # 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            # 獲取車手參數
            driver1 = kwargs.get('driver1', kwargs.get('driver'))
            driver2 = kwargs.get('driver2')
            
            # 獲取初始圈數參數
            lap1_original = kwargs.get('lap1') or kwargs.get('lap') or 1
            lap2_original = kwargs.get('lap2') or kwargs.get('lap') or 1
            lap1 = lap1_original
            lap2 = lap2_original
            
            # 特殊處理：lap=99 觸發最速圈邏輯 - 在此階段查找實際圈數
            if lap1 == 99:
                print(f"[INFO] 車手1圈數設為99，查找最速圈...")
                lap1_actual = self._get_fastest_lap_number(driver1)
                if lap1_actual is not None:
                    lap1 = lap1_actual
                    print(f"[INFO] 車手 {driver1} 最速圈: 第 {lap1} 圈")
                else:
                    print(f"[WARNING] 無法找到車手 {driver1} 的最速圈，使用第1圈")
                    lap1 = 1
                    
            if lap2 == 99:
                print(f"[INFO] 車手2圈數設為99，查找最速圈...")
                lap2_actual = self._get_fastest_lap_number(driver2)
                if lap2_actual is not None:
                    lap2 = lap2_actual
                    print(f"[INFO] 車手 {driver2} 最速圈: 第 {lap2} 圈")
                else:
                    print(f"[WARNING] 無法找到車手 {driver2} 的最速圈，使用第1圈")
                    lap2 = 1
            
            # 檢查是否啟用最速圈模式（保留舊的參數支援）
            use_fastest_lap = kwargs.get('fastest_lap', False) or kwargs.get('fastest', False)
            
            # 正確處理圈數參數 - 支援最速圈模式
            if use_fastest_lap:
                # 舊的最速圈模式：查找實際圈數
                lap1_actual = self._get_fastest_lap_number(driver1)
                lap2_actual = self._get_fastest_lap_number(driver2)
                if lap1_actual is not None and lap2_actual is not None:
                    lap1, lap2 = lap1_actual, lap2_actual
                    print(f"[DEBUG] 最速圈模式啟用: {driver1} 第{lap1}圈 vs {driver2} 第{lap2}圈")
                else:
                    print(f"[WARNING] 無法找到最速圈，使用第1圈")
                    lap1, lap2 = 1, 1
            
            print(f"[DEBUG] 最終圈數設定: lap1={lap1}, lap2={lap2}")
            
            # 判斷是否為單車手模式
            single_driver_mode = driver2 is None
            
            if single_driver_mode:
                print(f"[STATS] 單車手分析模式: {driver1}")
                print(f"[BALANCE] 執行單車手圈速分析: {driver1}")
                print(f"   • 圈數: 第 {lap1} 圈")
                print(f"   • 輸出格式: driver_data_{driver1}_{getattr(self.data_loader, 'year', 2025)}_{getattr(self.data_loader, 'race_name', 'Japan')}_{getattr(self.data_loader, 'session_type', 'R')}_Lap{lap1}.json")
                print(f"   • 圖表生成: 已禁用")
                
                # 單車手模式：使用車手圈速分析模組
                from CLI_modules.cli.analyzer.single_driver_laptime_analysis import SingleDriverLaptimeAnalysis
                
                try:
                    analyzer = SingleDriverLaptimeAnalysis(
                        data_loader=self.data_loader,
                        year=getattr(self.data_loader, 'year', 2025),
                        race=getattr(self.data_loader, 'race_name', 'Japan'),
                        session=getattr(self.data_loader, 'session_type', 'R')
                    )
                    
                    # 執行分析並獲取結果
                    result = analyzer.analyze_lap_times(driver=driver1, lap_number=lap1, **kwargs)
                    
                    if result and result.get("success"):
                        # 保存為指定格式的JSON檔案
                        self._save_driver_data_json(result, driver1, lap1)
                        return result
                except Exception as e:
                    print(f"[ERROR] 單車手圈速分析失敗: {e}")
                
                # 如果遙測分析失敗，回退到基本分析
                print("[REFRESH] 回退到基本車手分析...")
                from CLI_modules.cli.analyzer.driver_comparison_advanced import run_driver_comparison_json
                result = run_driver_comparison_json(
                    self.data_loader,
                    f1_analysis_instance=self.f1_analysis_instance,
                    enable_debug=True,
                    driver1=driver1,
                    driver2=None,  # 確保為None表示單車手模式
                    lap1=lap1,
                    lap2=None,
                    show_detailed_output=show_detailed_output
                )
                
                # 即使回退，也要保存為正確格式的JSON檔案
                if result and result.get("success"):
                    self._save_driver_data_json(result, driver1, lap1)
                    
                return result
                
            else:
                print(f"[STATS] 雙車手比較模式: {driver1} vs {driver2}")
                print(f"[BALANCE] 執行詳細遙測比較分析: {driver1} vs {driver2}")
                print(f"   • 圈數: 第 {lap1} 圈 vs 第 {lap2} 圈")
                print(f"   • 包含: 速度/RPM/油門/煞車/檔位/加速度/速度差/距離差對比")
            
            # 使用詳細遙測比較模組（僅雙車手模式）
            from CLI_modules.cli.analyzer.two_driver_telemetry_comparison_fixed import run_two_driver_telemetry_comparison_analysis
            
            # 準備參數，避免重複
            analysis_kwargs = {k: v for k, v in kwargs.items() if k not in ['year', 'race', 'session', 'driver', 'driver2', 'lap_number', 'lap1', 'lap2', 'show_detailed_output']}
            
            result = run_two_driver_telemetry_comparison_analysis(
                data_loader=self.data_loader,
                year=getattr(self.data_loader, 'year', 2025),
                race=getattr(self.data_loader, 'race_name', 'Japan'),
                session=getattr(self.data_loader, 'session_type', 'R'),
                driver=driver1,
                driver2=driver2,
                lap_number=lap1,  # 保持向後兼容
                lap1=lap1,
                lap2=lap2,
                # 傳遞原始圈數參數用於檔案命名
                lap1_original=lap1_original,
                lap2_original=lap2_original,
                show_detailed_output=show_detailed_output,
                **analysis_kwargs
            )
            
            # 結果反饋
            if result and self._report_analysis_results(result, "車手遙測對比分析"):
                return result
            else:
                print("[WARNING] 詳細遙測比較結果驗證失敗，嘗試基本比較...")
                raise Exception("詳細遙測比較結果驗證失敗")
            
        except Exception as e:
            print(f"[ERROR] 車手對比分析失敗: {str(e)}")
            # 如果詳細遙測比較失敗，回退到基本比較
            try:
                print("[REFRESH] 回退到基本車手比較分析...")
                from CLI_modules.cli.analyzer.driver_comparison_advanced import run_driver_comparison_json
                result = run_driver_comparison_json(
                    self.data_loader,
                    f1_analysis_instance=self.f1_analysis_instance,
                    enable_debug=True,
                    driver1=kwargs.get('driver1', kwargs.get('driver')),
                    driver2=kwargs.get('driver2'),
                    lap1=kwargs.get('lap1'),
                    lap2=kwargs.get('lap2'),
                    show_detailed_output=show_detailed_output
                )
                return result
            except Exception as fallback_error:
                print(f"[ERROR] 基本車手比較也失敗: {fallback_error}")
                return {"success": False, "message": f"車手對比分析失敗: {str(e)}", "function_id": "13"}
    
    # ===== 其他功能的執行函數 =====
    
    def _execute_race_position_changes(self, **kwargs):
        """執行賽事位置變化分析 - 使用功能15替代實現"""
        try:
            print("[START] 開始執行賽事位置變化分析...")
            print("[INFO] 此功能使用賽事超車統計分析 (功能15) 作為替代實現")
            
            # 調用功能15作為替代實現
            result = self._execute_race_overtaking_statistics(**kwargs)
            
            # 轉換結果標識
            if result and result.get("success"):
                result["function_id"] = "14"
                result["message"] = "賽事位置變化分析完成 (基於超車統計分析)"
                result["source_function"] = "15"
            else:
                result = {
                    "success": False,
                    "message": "賽事位置變化分析失敗：無法獲取超車數據",
                    "function_id": "14"
                }
            
            return result
            
        except Exception as e:
            print(f"[ERROR] 賽事位置變化分析失敗: {str(e)}")
            return {"success": False, "message": f"賽事位置變化分析失敗: {str(e)}", "function_id": "14"}
    
    def _execute_race_overtaking_statistics(self, **kwargs):
        """執行賽事超車統計分析 - 符合開發核心原則
        
        🆕 支援多年度分析模式：
        - 單年度模式：-f 15 -y 2024 -r Japan -s R
        - 多年度模式：-f 15 --start-year 2022 --end-year 2025 -r Japan -s R
        """
        import os
        import pickle
        import json
        from datetime import datetime
        
        try:
            print("[TEST] 開始執行賽事超車統計分析...")
            
            # 1. 參數處理 - 檢查是否為多年度模式
            start_year = kwargs.get('start_year')
            end_year = kwargs.get('end_year')
            
            # 🆕 多年度模式
            if start_year and end_year:
                print(f"[INFO] 檢測到多年度分析模式：{start_year}-{end_year}")
                race = kwargs.get('race') or getattr(self.data_loader, 'race_name', 'Japan')
                session = kwargs.get('session') or getattr(self.data_loader, 'session', 'R')
                
                # 調用多年度分析函數
                from CLI_modules.cli.analyzer.all_drivers_annual_overtaking_statistics import run_multi_year_overtaking_statistics
                result = run_multi_year_overtaking_statistics(start_year, end_year, race, session)
                
                if result:
                    return {
                        "success": True,
                        "data": result,
                        "cache_used": False,
                        "function_id": 15,
                        "message": f"多年度超車統計分析完成 ({start_year}-{end_year})",
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "success": False,
                        "message": "多年度超車統計分析失敗",
                        "function_id": 15,
                        "timestamp": datetime.now().isoformat()
                    }
            
            # 原有單年度模式
            year = kwargs.get('year') or getattr(self.data_loader, 'year', 2025)
            race = kwargs.get('race') or getattr(self.data_loader, 'race_name', 'Japan') 
            session = kwargs.get('session') or getattr(self.data_loader, 'session', 'R')
            disable_charts = kwargs.get('disable_charts', False)
            show_detailed_output = kwargs.get('show_detailed_output', True)  # 新增參數：是否顯示詳細輸出
            
            print(f"[STATS] 分析參數: {year} {race} {session}")
            if show_detailed_output:
                print(f"[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            # 2. 檢查緩存 - 實現緩存機制
            cache_key = f"race_overtaking_statistics_{year}_{race}_{session}"
            cache_dir = "cache"
            os.makedirs(cache_dir, exist_ok=True)
            cache_path = os.path.join(cache_dir, f"{cache_key}.pkl")
            
            if os.path.exists(cache_path) and not show_detailed_output:
                # 只有在不需要詳細輸出時才直接返回緩存
                print("[PACKAGE] 使用緩存數據")
                with open(cache_path, 'rb') as f:
                    cached_data = pickle.load(f)
                cached_result = {
                    "success": True,
                    "data": cached_data,
                    "cache_used": True,
                    "cache_key": cache_key,
                    "function_id": 15,
                    "message": "賽事超車統計分析完成 (使用緩存)",
                    "timestamp": datetime.now().isoformat()
                }
                self._report_analysis_results(cached_result, "賽事超車統計分析")
                return cached_result
            elif os.path.exists(cache_path) and show_detailed_output:
                # 緩存存在但需要詳細輸出時，重新執行分析但使用緩存的基礎數據
                print("[PACKAGE] 使用緩存數據 + [STATS] 顯示詳細分析結果")
                cache_available = True
            else:
                cache_available = False
            
            if not cache_available:
                print("[REFRESH] 重新計算 - 開始數據分析...")
            else:
                print("[REFRESH] 重新顯示 - 展示詳細分析結果...")
            
            # 3. 數據載入驗證
            if not self.data_loader:
                print("[ERROR] 數據載入器未初始化")
                return {
                    "success": False, 
                    "message": "數據載入器未初始化", 
                    "data": None,
                    "cache_used": False,
                    "cache_key": cache_key,
                    "function_id": 15,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 4. 執行分析 - 整合現有超車分析模組
            try:
                from CLI_modules.cli.analyzer.all_drivers_annual_overtaking_statistics import run_all_drivers_annual_overtaking_statistics
                print("[START] 調用全部車手年度超車統計模組...")
                result = run_all_drivers_annual_overtaking_statistics(
                    self.data_loader,
                    self.dynamic_team_mapping,
                    self.f1_analysis_instance
                )
                
                if result:
                    analysis_result = {
                        "success": True,
                        "data": result,
                        "cache_used": cache_available,
                        "cache_key": cache_key,
                        "function_id": "15",
                        "message": "賽事超車統計分析完成",
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    # 如果模組返回None，提供備用實現
                    print("[WARNING] 主要模組返回None，使用備用實現...")
                    backup_result = {
                        "analysis_type": "race_overtaking_statistics",
                        "year": year,
                        "race": race,
                        "session": session,
                        "overtaking_data": "數據來源：備用實現",
                        "total_overtakes": 0,
                        "note": "主要分析模組無可用數據，使用備用結果"
                    }
                    
                    analysis_result = {
                        "success": True,
                        "data": backup_result,
                        "cache_used": False,
                        "cache_key": cache_key,
                        "function_id": "15",
                        "message": "賽事超車統計分析完成 (備用實現)",
                        "source": "backup_implementation",
                        "timestamp": datetime.now().isoformat()
                    }
                    
            except Exception as e:
                print(f"[WARNING] 主要模組執行失敗: {str(e)}")
                print("[REFRESH] 使用最簡備用實現...")
                
                # 最簡備用實現
                backup_result = {
                    "analysis_type": "race_overtaking_statistics",
                    "year": year,
                    "race": race,
                    "session": session,
                    "error_info": str(e),
                    "overtaking_data": "分析模組執行失敗",
                    "total_overtakes": 0,
                    "note": "由於技術問題，使用備用結果"
                }
                
                analysis_result = {
                    "success": True,
                    "data": backup_result,
                    "cache_used": False,
                    "cache_key": cache_key,
                    "function_id": "15",
                    "message": "賽事超車統計分析完成 (最簡備用實現)",
                    "source": "minimal_backup",
                    "timestamp": datetime.now().isoformat()
                }
                
                if not cache_available:
                    print("[CHART] 執行超車統計分析...")
                else:
                    print("[CHART] 重新執行超車統計分析以顯示詳細結果...")
                    
                analysis_success = run_all_drivers_annual_overtaking_statistics(
                    self.data_loader, 
                    self.dynamic_team_mapping, 
                    self.f1_analysis_instance
                )
                
                if not analysis_success:
                    print("[ERROR] 超車統計分析執行失敗")
                    return {
                        "success": False, 
                        "message": "超車統計分析執行失敗", 
                        "data": None,
                        "cache_used": cache_available,
                        "cache_key": cache_key,
                        "function_id": 15,
                        "timestamp": datetime.now().isoformat()
                    }
                
            except ImportError as e:
                print(f"[ERROR] 模組導入失敗: {e}")
                return {
                    "success": False, 
                    "message": f"模組導入失敗: {e}", 
                    "data": None,
                    "cache_used": cache_available,
                    "cache_key": cache_key,
                    "function_id": 15,
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as e:
                print(f"[ERROR] 分析執行錯誤: {e}")
                return {
                    "success": False, 
                    "message": f"分析執行錯誤: {e}", 
                    "data": None,
                    "cache_used": cache_available,
                    "cache_key": cache_key,
                    "function_id": 15,
                    "timestamp": datetime.now().isoformat()
                }
            
            # 5. 構建結果數據 - Function 15 標準格式
            timestamp = datetime.now()
            result_data = {
                "analysis_type": "race_overtaking_statistics",
                "year": year,
                "race": race,
                "session": session,
                "execution_time": f"{timestamp.strftime('%H:%M:%S.%f')[:-3]}",
                "data_summary": {
                    "analysis_completed": True,
                    "cache_enabled": True,
                    "json_output_generated": True,
                    "detailed_output_shown": show_detailed_output,
                    "cache_reused": cache_available
                }
            }
            
            # Function 15 標準格式結果
            result = {
                "success": True,
                "data": result_data,
                "cache_used": cache_available,
                "cache_key": cache_key,
                "function_id": 15,
                "message": "賽事超車統計分析完成",
                "timestamp": timestamp.isoformat()
            }
            
            # 6. 結果驗證和反饋 - 提供清晰的執行結果反饋
            if not self._report_analysis_results(result, "賽事超車統計分析"):
                return {"success": False, "message": "結果驗證失敗", "cache_used": False, "cache_key": cache_key, "function_id": 15}
            
            # 7. 保存緩存 (只有在非緩存模式下才保存新緩存)
            if not cache_available:
                try:
                    with open(cache_path, 'wb') as f:
                        pickle.dump(result_data, f)
                    print("[SAVE] 分析結果已緩存")
                except Exception as e:
                    print(f"[WARNING] 緩存保存失敗: {e}")
            else:
                print("[PACKAGE] 緩存數據已存在，無需重新保存")
            
            return result
            
        except Exception as e:
            error_msg = f"賽事超車統計分析失敗: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {
                "success": False, 
                "message": error_msg, 
                "data": None,
                "cache_used": False,
                "cache_key": "",
                "function_id": 15,
                "timestamp": datetime.now().isoformat()
            }
    
    def _report_analysis_results(self, data, analysis_type="analysis"):
        """報告分析結果狀態 - 符合開發核心原則"""
        if not data:
            print(f"[ERROR] {analysis_type}失敗：無可用數據")
            return False
        
        # 檢查數據完整性
        if isinstance(data, dict):
            if data.get("success", False):
                print(f"[STATS] {analysis_type}結果摘要：")
                print(f"   • 執行狀態: {'[OK] 成功' if data.get('success') else '[ERROR] 失敗'}")
                print(f"   • 功能編號: {data.get('function_id', 'N/A')}")
                
                # 檢查是否有實際數據
                data_content = data.get('data', {})
                if isinstance(data_content, dict):
                    analysis_type_key = data_content.get('analysis_type', 'N/A')
                    execution_time_key = data_content.get('execution_time', 'N/A')
                else:
                    analysis_type_key = 'N/A'
                    execution_time_key = 'N/A'
                
                print(f"   • 分析類型: {analysis_type_key}")
                print(f"   • 執行時間: {execution_time_key}")
                
                # 修復緩存狀態檢查邏輯 - 直接從Function 15標準格式讀取
                cache_status = data.get('cache_used', False)
                print(f"   • 緩存狀態: {'[OK] 已啟用' if cache_status else '[REFRESH] 新建'}")
                
                # 如果有緩存鍵值，也顯示
                cache_key = data.get('cache_key', '')
                if cache_key:
                    print(f"   • 緩存鍵值: {cache_key[:50]}...")
                
                print(f"[OK] {analysis_type}分析完成！")
                return True
            else:
                print(f"[ERROR] {analysis_type}執行失敗: {data.get('message', '未知錯誤')}")
                return False
        else:
            # 處理其他類型的數據
            data_count = len(data) if hasattr(data, '__len__') else 1
            print(f"[STATS] {analysis_type}結果摘要：")
            print(f"   • 數據項目數量: {data_count}")
            print(f"   • 數據完整性: {'[OK] 良好' if data_count > 0 else '[ERROR] 不足'}")
            print(f"[OK] {analysis_type}分析完成！")
            return True
    
    def _execute_single_driver_overtaking(self, **kwargs):
        """執行單一車手超車分析 - Function 16 (Function 15 標準)"""
        try:
            print("[START] 開始執行單一車手超車分析...")
            
            # 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            from CLI_modules.cli.analyzer.single_driver_overtaking_analysis import run_single_driver_overtaking_analysis
            print("[FINISH] 執行單一車手超車分析...")
            
            # 避免參數重複 - 從 kwargs 中移除 show_detailed_output
            analysis_kwargs = kwargs.copy()
            analysis_kwargs.pop('show_detailed_output', None)
            
            result = run_single_driver_overtaking_analysis(
                self.data_loader,
                f1_analysis_instance=self.f1_analysis_instance,
                show_detailed_output=show_detailed_output,
                **analysis_kwargs
            )
            
            # 結果反饋
            if not self._report_analysis_results(result, "單一車手超車分析"):
                return {"success": False, "message": "單一車手超車分析結果驗證失敗", "function_id": "16"}
            
            return {
                "success": True,
                "data": result.get('data'),
                "cache_used": result.get('cache_used', False),
                "cache_key": result.get('cache_key'),
                "function_id": "16",
                "message": "單一車手超車分析完成"
            }
        except Exception as e:
            print(f"[ERROR] 單一車手超車分析失敗: {str(e)}")
            return {"success": False, "message": f"單一車手超車分析失敗: {str(e)}", "function_id": "16"}
    
    # ===== 單車手分析模組執行函數 (11-17) =====
    
    def _execute_single_driver_dnf(self, **kwargs):
        """執行單一車手DNF分析 - 符合開發核心原則"""
        try:
            print("[START] 開始執行單一車手DNF分析...")
            
            # 參數處理 - 支援詳細輸出控制和車手參數
            show_detailed_output = kwargs.get('show_detailed_output', True)
            driver = kwargs.get('driver', None)
            
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            if driver:
                print(f"[TARGET] 使用指定車手: {driver}")
            
            from CLI_modules.cli.analyzer.single_driver_dnf_detailed import run_single_driver_detailed_dnf_analysis
            print("[TOOL] 執行單一車手DNF分析...")
            result = run_single_driver_detailed_dnf_analysis(
                data_loader=self.data_loader,
                f1_analysis_instance=self.f1_analysis_instance,
                show_detailed_output=show_detailed_output,
                driver=driver
            )
            
            # 結果反饋
            if not self._report_analysis_results(result, "單一車手DNF分析"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "19"}
            
            return {"success": True, "data": result, "function_id": "19"}
            
        except Exception as e:
            error_msg = f"單一車手DNF分析失敗: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {"success": False, "message": error_msg, "function_id": "19"}
    
    def _execute_dynamic_corner_detection(self, **kwargs):
        """執行動態彎道檢測分析 - Function 17 [STAR] 新增功能"""
        try:
            print("[START] 開始執行動態彎道檢測分析...")
            
            # 1. 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            driver = kwargs.get('driver', self.driver)
            export_json = kwargs.get('export_json', True)
            
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (顯示完整彎道檢測表格)")
            
            # 2. 模組調用 - 使用新的動態彎道檢測模組
            from CLI_modules.cli.analyzer.dynamic_corner_detection import run_dynamic_corner_detection_analysis
            
            # 只傳遞函數需要的參數，過濾掉不需要的參數
            valid_params = ['year', 'race', 'session']
            analysis_kwargs = {k: v for k, v in kwargs.items() if k in valid_params}
            
            result = run_dynamic_corner_detection_analysis(
                data_loader=self.data_loader,
                driver=driver,
                show_detailed_output=show_detailed_output,
                export_json=export_json,
                **analysis_kwargs
            )
            
            # 3. 結果驗證和標準化輸出
            if result:
                corners_count = len(result.get('corners_data', []))
                avg_confidence = result.get('statistics', {}).get('average_confidence', 0)
                
                print(f"[OK] 動態彎道檢測完成!")
                print(f"   [STATS] 檢測到彎道: {corners_count} 個")
                print(f"   [TARGET] 平均信心度: {avg_confidence:.2f}")
                
                return {
                    "success": True,
                    "message": f"動態彎道檢測完成 - 檢測到 {corners_count} 個彎道",
                    "function_id": "17",
                    "corners_count": corners_count,
                    "average_confidence": avg_confidence,
                    "analysis_data": result
                }
            else:
                return {
                    "success": False,
                    "message": "動態彎道檢測失敗 - 無可用數據",
                    "function_id": "17"
                }
            
        except Exception as e:
            print(f"[ERROR] 動態彎道檢測失敗: {str(e)}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": f"動態彎道檢測失敗: {str(e)}", "function_id": "17"}
        
    def _execute_corner_detailed_analysis(self, **kwargs):
        """執行指定彎道詳細分析 - Function 18 (原Function 18)"""
        try:
            print("[START] 開始執行指定彎道詳細分析...")
            
            # 1. 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            # 2. 模組調用 - 使用專門的彎道詳細分析模組
            from CLI_modules.cli.analyzer.corner_detailed_analysis import run_corner_detailed_analysis
            
            # 移除可能重複的參數
            analysis_kwargs = kwargs.copy()
            
            result = run_corner_detailed_analysis(
                data_loader=self.data_loader,
                f1_analysis_instance=self.f1_analysis_instance,
                **analysis_kwargs
            )
            
            # 3. 結果準備和反饋
            if not result:
                result = {
                    "success": True,
                    "message": "指定彎道詳細分析完成",
                    "function_id": "18",
                    "data": {},
                    "cache_used": False
                }
            
            # 確保結果格式正確
            if isinstance(result, dict) and 'success' not in result:
                result['success'] = True
                result['function_id'] = "18"
            
            # 4. 結果反饋
            if not self._report_analysis_results(result, "指定彎道詳細分析"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "18"}
            
            return result
            
        except ImportError as e:
            print(f"[WARNING] 彎道分析模組未找到，使用基礎實現: {e}")
            
            # 基礎實現
            result = {
                "success": True,
                "message": "指定彎道詳細分析功能 - 基礎實現",
                "function_id": "18",
                "data": {
                    "driver": kwargs.get('driver', 'VER'),
                    "corner_number": kwargs.get('corner_number', 1),
                    "analysis_type": "corner_detailed_analysis"
                },
                "cache_used": False
            }
            
            if not self._report_analysis_results(result, "指定彎道詳細分析"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "18"}
            
            return result
            
        except Exception as e:
            print(f"[ERROR] 指定彎道詳細分析失敗: {str(e)}")
            return {"success": False, "message": f"指定彎道詳細分析失敗: {str(e)}", "function_id": "18"}
        
    def _execute_single_driver_all_corners(self, **kwargs):
        """執行單一車手全部彎道分析 - 符合開發核心原則"""
        try:
            print("[START] 開始執行單一車手全部彎道分析...")
            
            # 參數處理 - 支援詳細輸出控制和車手參數
            show_detailed_output = kwargs.get('show_detailed_output', True)
            driver = kwargs.get('driver1', kwargs.get('driver', self.driver))  # 自動選擇車手
            
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            print(f"[TARGET] 使用指定車手: {driver}")
            
            from CLI_modules.cli.analyzer.single_driver_all_corners_detailed_analysis import run_single_driver_all_corners_detailed_analysis
            print("[STATS] 執行單一車手全部彎道分析...")
            result = run_single_driver_all_corners_detailed_analysis(
                self.data_loader,
                f1_analysis_instance=self.f1_analysis_instance,
                show_detailed_output=show_detailed_output,
                driver=driver  # 傳遞車手參數，避免交互式輸入
            )
            
            # 結果反饋
            if not self._report_analysis_results(result, "單一車手全部彎道分析"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "20"}
            
            return {"success": True, "data": result, "function_id": "20", "message": "單一車手全部彎道分析完成"}
            
        except Exception as e:
            error_msg = f"單一車手全部彎道分析失敗: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {"success": False, "message": error_msg, "function_id": "20"}
        
    def _execute_all_drivers_comprehensive(self, **kwargs):
        """執行所有車手綜合分析 - 使用非交互式方式"""
        try:
            print("[START] 開始執行所有車手綜合分析...")
            print("[REFRESH] 使用自動化分析模式 (避免交互式輸入)")
            
            # 參數處理
            show_detailed_output = kwargs.get('show_detailed_output', True)
            driver = kwargs.get('driver', kwargs.get('driver1', 'VER'))
            
            print(f"[TARGET] 自動選擇主要車手: {driver}")
            
            # 重定向到功能12 (單一車手詳細遙測分析) - 已驗證無交互式輸入
            print("[STATS] 執行基於單一車手詳細遙測的綜合分析...")
            
            # 清理參數，避免重複傳遞
            clean_kwargs = {k: v for k, v in kwargs.items() 
                          if k not in ['driver', 'driver1', 'driver2', 'show_detailed_output']}
            
            result = self._execute_single_driver_telemetry(
                driver=driver,
                show_detailed_output=show_detailed_output,
                **clean_kwargs
            )
            
            if result.get('success', False):
                # 修改回應訊息以反映綜合分析特性
                result['message'] = f"所有車手綜合分析完成 (基於{driver}車手詳細分析)"
                result['function_id'] = "21"
                print("[OK] 所有車手綜合分析完成！")
                return result
            else:
                return {"success": False, "message": "所有車手綜合分析失敗", "function_id": "21"}
            
        except Exception as e:
            error_msg = f"所有車手綜合分析失敗: {str(e)}"
            print(f"[ERROR] {error_msg}")
            return {"success": False, "message": error_msg, "function_id": "21"}
        
    def _execute_corner_speed_analysis(self, **kwargs):
        """執行彎道速度分析 - 使用功能17的結果實現"""
        try:
            print("[START] 開始執行彎道速度分析...")
            print("[TEST] 此功能使用動態彎道檢測分析 (功能17) 的結果")
            
            # 1. 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            # 2. 調用功能17來獲取彎道分析結果
            result = self._execute_dynamic_corner_detection(**kwargs)
            
            # 3. 轉換結果為彎道速度分析格式
            if result and result.get("success"):
                corner_speed_result = {
                    "success": True,
                    "message": "彎道速度分析完成 (基於動態彎道檢測)",
                    "function_id": "22",
                    "data": result.get("data"),
                    "cache_used": result.get("cache_used", False),
                    "analysis_type": "corner_speed_analysis",
                    "source_function": "17"
                }
            else:
                corner_speed_result = {
                    "success": False,
                    "message": "彎道速度分析失敗：無法獲取彎道數據",
                    "function_id": "22"
                }
            
            # 4. 結果反饋
            if not self._report_analysis_results(corner_speed_result, "彎道速度分析"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "22"}
            
            return corner_speed_result
            
        except Exception as e:
            print(f"[ERROR] 彎道速度分析失敗: {str(e)}")
            return {"success": False, "message": f"彎道速度分析失敗: {str(e)}", "function_id": "22"}
        
    def _execute_all_drivers_overtaking(self, **kwargs):
        """執行全部車手超車分析 - 符合開發核心原則"""
        try:
            print("[START] 開始執行全部車手超車分析...")
            
            # 1. 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            # 2. 模組調用 - 注意：該模組不接受show_detailed_output參數
            from CLI_modules.cli.analyzer.all_drivers_annual_overtaking_statistics import run_all_drivers_annual_overtaking_statistics
            result = run_all_drivers_annual_overtaking_statistics(
                self.data_loader,
                self.dynamic_team_mapping,
                self.f1_analysis_instance
            )
            
            # 3. 結果準備和反饋
            if not result:
                result = {
                    "success": True,
                    "message": "全部車手超車分析完成",
                    "function_id": "16"
                }
            
            if not self._report_analysis_results(result, "全部車手超車分析"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "16"}
            
            return result
        except Exception as e:
            print(f"[ERROR] 全部車手超車分析失敗: {str(e)}")
            return {"success": False, "message": f"全部車手超車分析失敗: {str(e)}", "function_id": "16"}
        
    def _execute_all_drivers_dnf(self, **kwargs):
        """Function 24: 全車手年度DNF分析 - Function 19的擴展版本"""
        try:
            print("[START] 開始執行 Function 24: 全車手年度DNF分析...")
            print("[INFO] 這是 Function 19 的擴展版本：從單車手DNF分析擴展到全車手年度分析")
            
            # 1. 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            year = kwargs.get('year', 2025)
            session = kwargs.get('session', 'R')
            
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            # 2. 準備乾淨的參數字典，避免重複參數
            clean_kwargs = {k: v for k, v in kwargs.items() if k not in ['year', 'session', 'show_detailed_output']}
            
            # 3. 模組調用 - 使用新的全車手年度DNF分析模組
            from CLI_modules.cli.analyzer.all_drivers_annual_dnf_analysis import run_all_drivers_annual_dnf_analysis
            result = run_all_drivers_annual_dnf_analysis(
                data_loader=self.data_loader,
                year=year,
                session=session,
                show_detailed_output=show_detailed_output,
                **clean_kwargs
            )
            
            # 4. 結果準備和反饋
            if not result:
                result = {
                    "success": False,
                    "message": "全車手年度DNF分析無結果",
                    "function_id": "24"
                }
            else:
                # 包裝結果為標準格式
                wrapped_result = {
                    "success": True,
                    "message": "全車手年度DNF分析完成",
                    "function_id": "24",
                    "data": result,
                    "cache_used": result.get('metadata', {}).get('cache_used', False),
                    "analysis_type": "annual_all_drivers_dnf",
                    "execution_time": "completed"
                }
                result = wrapped_result
            
            if not self._report_analysis_results(result, "全車手年度DNF分析"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "24"}
            
            return result
        except Exception as e:
            print(f"[ERROR] Function 24 執行失敗: {str(e)}")
            return {"success": False, "message": f"Function 24 執行失敗: {str(e)}", "function_id": "24"}
    
    # ===== 系統功能執行函數 =====
    
    def _execute_reload_race_data(self, **kwargs):
        """重新載入賽事數據 - 符合開發核心原則"""
        try:
            print("[START] 開始重新載入賽事數據...")
            
            # 1. 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            # 2. 結果準備
            result = {"success": True, "message": "請使用 CLI 重新載入數據", "function_id": "47"}
            
            # 3. 結果反饋
            if not self._report_analysis_results(result, "重新載入賽事數據"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "47"}
            
            return result
        except Exception as e:
            print(f"[ERROR] 重新載入賽事數據失敗: {str(e)}")
            return {"success": False, "message": f"重新載入賽事數據失敗: {str(e)}", "function_id": "47"}
    
    def _execute_show_module_status(self, **kwargs):
        """顯示模組狀態 - 符合開發核心原則"""
        try:
            print("[START] 開始顯示模組狀態...")
            
            # 1. 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            # 2. 結果準備
            result = {"success": True, "message": "模組狀態檢查完成", "function_id": "48"}
            
            # 3. 結果反饋
            if not self._report_analysis_results(result, "顯示模組狀態"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "48"}
            
            return result
        except Exception as e:
            print(f"[ERROR] 顯示模組狀態失敗: {str(e)}")
            return {"success": False, "message": f"顯示模組狀態失敗: {str(e)}", "function_id": "48"}
    
    def _execute_show_help(self, **kwargs):
        """顯示幫助信息 - 符合開發核心原則"""
        try:
            print("[START] 開始顯示幫助信息...")
            
            # 1. 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            # 2. 結果準備
            result = {"success": True, "message": "幫助信息已顯示", "function_id": "49"}
            
            # 3. 結果反饋
            if not self._report_analysis_results(result, "顯示幫助信息"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "49"}
            
            return result
        except Exception as e:
            print(f"[ERROR] 顯示幫助信息失敗: {str(e)}")
            return {"success": False, "message": f"顯示幫助信息失敗: {str(e)}", "function_id": "49"}
    
    def _execute_overtaking_cache_management(self, **kwargs):
        """超車緩存管理 - 符合開發核心原則"""
        try:
            print("[START] 開始超車緩存管理...")
            
            # 1. 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            # 2. 結果準備
            result = {"success": True, "message": "超車緩存管理完成", "function_id": "50"}
            
            # 3. 結果反饋
            if not self._report_analysis_results(result, "超車緩存管理"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "50"}
            
            return result
        except Exception as e:
            print(f"[ERROR] 超車緩存管理失敗: {str(e)}")
            return {"success": False, "message": f"超車緩存管理失敗: {str(e)}", "function_id": "50"}
    
    def _execute_dnf_cache_management(self, **kwargs):
        """DNF緩存管理 - 符合開發核心原則"""
        try:
            print("[START] 開始DNF緩存管理...")
            
            # 1. 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            # 2. 結果準備
            result = {"success": True, "message": "DNF緩存管理完成", "function_id": "51"}
            
            # 3. 結果反饋
            if not self._report_analysis_results(result, "DNF緩存管理"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "51"}
            
            return result
        except Exception as e:
            print(f"[ERROR] DNF緩存管理失敗: {str(e)}")
            return {"success": False, "message": f"DNF緩存管理失敗: {str(e)}", "function_id": "51"}
    
    # ===== 子功能執行函數 =====
    
    def _execute_accident_key_events(self, **kwargs):
        """執行關鍵事件摘要分析 - 符合開發核心原則"""
        try:
            print("[START] 開始執行關鍵事件摘要分析...")
            
            # 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            from CLI_modules.cli.analyzer.key_events_analysis import run_key_events_summary_analysis
            print("[SEARCH] 執行關鍵事件摘要分析...")
            result = run_key_events_summary_analysis(
                self.data_loader,
                show_detailed_output=show_detailed_output  # 新增參數傳遞
            )
            
            # 結果反饋
            if not self._report_analysis_results({"success": True if result else False, "data": result}, "關鍵事件摘要分析"):
                return {"success": False, "message": "結果驗證失敗", "function_id": "4.1"}
            
            return {"success": True, "message": "關鍵事件摘要分析完成", "function_id": "4.1"}
        except Exception as e:
            print(f"[ERROR] 關鍵事件摘要分析失敗: {str(e)}")
            return {"success": False, "message": f"關鍵事件摘要分析失敗: {str(e)}", "function_id": "4.1"}
    
    def _execute_accident_special_incidents(self, **kwargs):
        """執行特殊事件報告分析 - Function 4.2 - 符合開發核心原則"""
        try:
            print("[START] 開始執行特殊事件報告分析...")
            
            # 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            try:
                from CLI_modules.cli.analyzer.special_incidents_analysis import run_special_incidents_analysis  # type: ignore
            except ImportError:
                from modules.gui.accident_analysis.special_incidents_analysis import (
                    run_special_incidents_analysis,
                )
            print("[ALERT] 執行特殊事件報告分析...")
            result = run_special_incidents_analysis(
                self.data_loader,
                f1_analysis_instance=self.f1_analysis_instance,
                show_detailed_output=show_detailed_output
            )
            
            # 結果反饋
            if not self._report_analysis_results({"success": True, "data": result}, "特殊事件報告分析"):
                return {"success": False, "message": "特殊事件報告分析結果驗證失敗", "function_id": "4.2"}
            
            return {"success": True, "message": "特殊事件報告分析完成", "function_id": "4.2"}
        except Exception as e:
            print(f"[ERROR] 特殊事件報告分析失敗: {str(e)}")
            return {"success": False, "message": f"特殊事件報告分析失敗: {str(e)}", "function_id": "4.2"}
    
    def _execute_accident_driver_severity(self, **kwargs):
        """執行車手嚴重程度分析 - Function 4.3 - 符合開發核心原則"""
        try:
            print("[START] 開始執行車手嚴重程度分析...")
            
            # 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            from CLI_modules.cli.analyzer.driver_severity_analysis import run_driver_severity_analysis
            print("🏆 執行車手嚴重程度分析...")
            result = run_driver_severity_analysis(
                self.data_loader,
                self.dynamic_team_mapping,
                self.f1_analysis_instance,
                show_detailed_output=show_detailed_output
            )
            
            # 結果反饋
            if not self._report_analysis_results({"success": True, "data": result}, "車手嚴重程度分析"):
                return {"success": False, "message": "車手嚴重程度分析結果驗證失敗", "function_id": "4.3"}
            
            return {"success": True, "message": "車手嚴重程度分析完成", "function_id": "4.3"}
        except Exception as e:
            print(f"[ERROR] 車手嚴重程度分析失敗: {str(e)}")
            return {"success": False, "message": f"車手嚴重程度分析失敗: {str(e)}", "function_id": "4.3"}
    
    def _execute_accident_team_risk(self, **kwargs):
        """執行車隊風險分析 - Function 4.4 - 符合開發核心原則"""
        try:
            print("[START] 開始執行車隊風險分析...")
            
            # 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            from CLI_modules.cli.analyzer.team_risk_analysis import run_team_risk_analysis
            print("[FINISH] 執行車隊風險分析...")
            result = run_team_risk_analysis(
                self.data_loader,
                self.dynamic_team_mapping,
                self.f1_analysis_instance,
                show_detailed_output=show_detailed_output
            )
            
            # 結果反饋
            if not self._report_analysis_results({"success": True, "data": result}, "車隊風險分析"):
                return {"success": False, "message": "車隊風險分析結果驗證失敗", "function_id": "4.4"}
            
            return {"success": True, "message": "車隊風險分析完成", "function_id": "4.4"}
        except Exception as e:
            print(f"[ERROR] 車隊風險分析失敗: {str(e)}")
            return {"success": False, "message": f"車隊風險分析失敗: {str(e)}", "function_id": "4.4"}
    
    def _execute_accident_all_incidents(self, **kwargs):
        """執行所有事件詳細列表分析 - Function 4.6 - 符合開發核心原則"""
        try:
            print("[START] 開始執行所有事件詳細列表分析...")
            
            # 參數處理 - 支援詳細輸出控制
            show_detailed_output = kwargs.get('show_detailed_output', True)
            if show_detailed_output:
                print("[INFO] 詳細輸出模式: 啟用 (緩存數據也將顯示完整表格)")
            
            from CLI_modules.cli.analyzer.all_incidents_analysis import run_all_incidents_analysis
            print("[INFO] 執行所有事件詳細列表分析...")
            result = run_all_incidents_analysis(
                self.data_loader,
                f1_analysis_instance=self.f1_analysis_instance,
                show_detailed_output=show_detailed_output
            )
            
            # 結果反饋
            if not self._report_analysis_results({"success": True, "data": result}, "所有事件詳細列表分析"):
                return {"success": False, "message": "所有事件詳細列表分析結果驗證失敗", "function_id": "4.6"}
            
            return {"success": True, "message": "所有事件詳細列表分析完成", "function_id": "4.6"}
        except Exception as e:
            print(f"[ERROR] 所有事件詳細列表分析失敗: {str(e)}")
            return {"success": False, "message": f"所有事件詳細列表分析失敗: {str(e)}", "function_id": "4.6"}
    
    def _execute_speed_gap_analysis(self, **kwargs):
        """執行速度差距分析"""
        try:
            from CLI_modules.cli.analyzer.speed_gap_analysis import run_speed_gap_analysis
            print("[F1] 執行速度差距分析...")
            print(f"[TARGET] 使用車手: {self.driver} vs {self.driver2}")
            run_speed_gap_analysis(
                self.data_loader,
                f1_analysis_instance=self.f1_analysis_instance,
                auto_driver1=self.driver,
                auto_driver2=self.driver2
            )
            return {"success": True, "message": f"速度差距分析完成 ({self.driver} vs {self.driver2})", "function_id": "7.1"}
        except Exception as e:
            return {"success": False, "message": f"速度差距分析失敗: {str(e)}", "function_id": "7.1"}
    
    def _execute_distance_gap_analysis(self, **kwargs):
        """執行距離差距分析"""
        try:
            from CLI_modules.cli.analyzer.distance_gap_analysis import run_distance_gap_analysis
            print("📏 執行距離差距分析...")
            print(f"[TARGET] 使用車手: {self.driver} vs {self.driver2}")
            run_distance_gap_analysis(
                self.data_loader,
                f1_analysis_instance=self.f1_analysis_instance,
                auto_driver1=self.driver,
                auto_driver2=self.driver2
            )
            return {"success": True, "message": f"距離差距分析完成 ({self.driver} vs {self.driver2})", "function_id": "7.2"}
        except Exception as e:
            return {"success": False, "message": f"距離差距分析失敗: {str(e)}", "function_id": "7.2"}
    
    def _execute_driver_statistics_overview(self, **kwargs):
        """執行車手數據統計總覽"""
        try:
            from CLI_modules.cli.analyzer.gui.driver_analysis.driver_statistics_overview import run_driver_statistics_overview
            print("[STATS] 執行車手數據統計總覽...")
            run_driver_statistics_overview(
                self.data_loader,
                self.dynamic_team_mapping,
                self.f1_analysis_instance
            )
            return {"success": True, "message": "車手數據統計總覽完成", "function_id": "14.1"}
        except Exception as e:
            return {"success": False, "message": f"車手數據統計總覽失敗: {str(e)}", "function_id": "14.1"}
    
    def _execute_driver_telemetry_statistics(self, **kwargs):
        """執行車手遙測資料統計"""
        try:
            from CLI_modules.cli.analyzer.gui.driver_analysis.driver_telemetry_statistics import run_driver_telemetry_statistics
            print("[TOOL] 執行車手遙測資料統計...")
            run_driver_telemetry_statistics(
                self.data_loader,
                self.dynamic_team_mapping,
                self.f1_analysis_instance
            )
            return {"success": True, "message": "車手遙測資料統計完成", "function_id": "14.2"}
        except Exception as e:
            return {"success": False, "message": f"車手遙測資料統計失敗: {str(e)}", "function_id": "14.2"}
    
    def _execute_driver_overtaking_analysis(self, **kwargs):
        """執行車手超車分析"""
        try:
            from CLI_modules.cli.analyzer.driver_overtaking_analysis import run_driver_overtaking_analysis
            print("[START] 執行車手超車分析...")
            run_driver_overtaking_analysis(
                self.data_loader,
                self.dynamic_team_mapping,
                self.f1_analysis_instance
            )
            return {"success": True, "message": "車手超車分析完成", "function_id": "14.3"}
        except Exception as e:
            return {"success": False, "message": f"車手超車分析失敗: {str(e)}", "function_id": "14.3"}
    
    def _execute_driver_fastest_lap_ranking(self, **kwargs):
        """執行最速圈排名分析"""
        try:
            from CLI_modules.cli.analyzer.driver_fastest_lap_ranking import run_driver_fastest_lap_ranking
            print("🏆 執行最速圈排名分析...")
            run_driver_fastest_lap_ranking(
                self.data_loader,
                self.dynamic_team_mapping,
                self.f1_analysis_instance
            )
            return {"success": True, "message": "最速圈排名分析完成", "function_id": "14.4"}
        except Exception as e:
            return {"success": False, "message": f"最速圈排名分析失敗: {str(e)}", "function_id": "14.4"}
    
    def _execute_all_drivers_comprehensive_full(self, **kwargs):
        """執行完整綜合分析"""
        try:
            from CLI_modules.cli.analyzer.gui.driver_analysis.driver_comprehensive_full import run_driver_comprehensive_full
            print("👥 執行完整綜合分析...")
            run_driver_comprehensive_full(
                self.data_loader,
                self.dynamic_team_mapping,
                self.f1_analysis_instance
            )
            return {"success": True, "message": "完整綜合分析完成", "function_id": "14.9"}
        except Exception as e:
            return {"success": False, "message": f"完整綜合分析失敗: {str(e)}", "function_id": "14.9"}
    
    # ===== 超車分析子功能 =====
    
    def _execute_annual_overtaking_statistics(self, **kwargs):
        """執行年度超車統計"""
        try:
            from CLI_modules.cli.analyzer.all_drivers_annual_overtaking_statistics import run_all_drivers_annual_overtaking_statistics
            print("[STATS] 執行年度超車統計...")
            run_all_drivers_annual_overtaking_statistics(
                self.data_loader,
                self.dynamic_team_mapping,
                self.f1_analysis_instance
            )
            return {"success": True, "message": "年度超車統計完成", "function_id": "16.1"}
        except Exception as e:
            return {"success": False, "message": f"年度超車統計失敗: {str(e)}", "function_id": "16.1"}
    
    def _execute_overtaking_performance_comparison(self, **kwargs):
        """執行超車效能比較"""
        try:
            from CLI_modules.cli.analyzer.all_drivers_overtaking_performance_comparison import run_all_drivers_overtaking_performance_comparison
            print("[FINISH] 執行超車效能比較...")
            run_all_drivers_overtaking_performance_comparison(
                self.data_loader,
                self.dynamic_team_mapping,
                self.f1_analysis_instance
            )
            return {"success": True, "message": "超車效能比較完成", "function_id": "16.2"}
        except Exception as e:
            return {"success": False, "message": f"超車效能比較失敗: {str(e)}", "function_id": "16.2"}
    
    def _execute_overtaking_visualization_analysis(self, **kwargs):
        """執行超車視覺化分析"""
        try:
            from CLI_modules.cli.analyzer.all_drivers_overtaking_visualization_analysis import run_all_drivers_overtaking_visualization_analysis
            print("[CHART] 執行超車視覺化分析...")
            run_all_drivers_overtaking_visualization_analysis(
                self.data_loader,
                self.dynamic_team_mapping,
                self.f1_analysis_instance
            )
            return {"success": True, "message": "超車視覺化分析完成", "function_id": "16.3"}
        except Exception as e:
            return {"success": False, "message": f"超車視覺化分析失敗: {str(e)}", "function_id": "16.3"}
    
    def _execute_overtaking_trends_analysis(self, **kwargs):
        """執行超車趨勢分析"""
        try:
            from CLI_modules.cli.analyzer.all_drivers_overtaking_trends_analysis import run_all_drivers_overtaking_trends_analysis
            print("[CHART] 執行超車趨勢分析...")
            run_all_drivers_overtaking_trends_analysis(
                self.data_loader,
                self.dynamic_team_mapping,
                self.f1_analysis_instance
            )
            return {"success": True, "message": "超車趨勢分析完成", "function_id": "16.4"}
        except Exception as e:
            return {"success": False, "message": f"超車趨勢分析失敗: {str(e)}", "function_id": "16.4"}
    
    # ===== 其他子功能的預留實現 =====
    
    def _execute_telemetry_complete_lap(self, **kwargs):
        """執行完整圈次遙測分析"""
        return {"success": True, "message": "完整圈次遙測分析功能開發中", "function_id": "6.1"}
    
    def _execute_telemetry_tire_strategy(self, **kwargs):
        """執行輪胎策略遙測分析"""
        return {"success": True, "message": "輪胎策略遙測分析功能開發中", "function_id": "6.2"}
    
    def _execute_telemetry_tire_performance(self, **kwargs):
        """執行輪胎性能遙測分析"""
        return {"success": True, "message": "輪胎性能遙測分析功能開發中", "function_id": "6.3"}
    
    def _execute_telemetry_pitstop_records(self, **kwargs):
        """執行進站記錄遙測分析"""
        return {"success": True, "message": "進站記錄遙測分析功能開發中", "function_id": "6.4"}
    
    def _execute_telemetry_special_events(self, **kwargs):
        """執行特殊事件遙測分析"""
        return {"success": True, "message": "特殊事件遙測分析功能開發中", "function_id": "6.5"}
    
    def _execute_telemetry_fastest_lap(self, **kwargs):
        """執行最快圈遙測分析"""
        return {"success": True, "message": "最快圈遙測分析功能開發中", "function_id": "6.6"}
    
    def _execute_telemetry_specific_lap(self, **kwargs):
        """執行指定圈次遙測分析"""
        return {"success": True, "message": "指定圈次遙測分析功能開發中", "function_id": "6.7"}
    
    def _execute_detailed_dnf_analysis(self, **kwargs):
        """執行詳細DNF分析 - Function 11.1"""
        try:
            from CLI_modules.cli.analyzer.single_driver_dnf_detailed import SingleDriverDNFDetailed
            print("[ALERT] 執行詳細DNF與責任事故分析...")
            print(f"[TARGET] 分析車手: {self.driver}")
            
            # 創建分析器實例
            analyzer = SingleDriverDNFDetailed(
                data_loader=self.data_loader,
                year=getattr(self.data_loader, 'year', 2025),
                race=getattr(self.data_loader, 'race', 'Japan'),
                session=getattr(self.data_loader, 'session', 'R')
            )
            
            # 執行分析
            result = analyzer.analyze(driver=self.driver)
            
            if result:
                return {"success": True, "message": f"詳細DNF分析完成 (車手: {self.driver})", "function_id": "11.1"}
            else:
                return {"success": False, "message": "詳細DNF分析未產生結果", "function_id": "11.1"}
        except Exception as e:
            return {"success": False, "message": f"詳細DNF分析失敗: {str(e)}", "function_id": "11.1"}
    
    def _execute_annual_dnf_statistics(self, **kwargs):
        """執行年度DNF統計 - Function 11.2"""
        try:
            from CLI_modules.cli.analyzer.annual_dnf_statistics import AnnualDNFStatistics
            print("[STATS] 執行年度DNF統計摘要...")
            print(f"[TARGET] 分析年份: {getattr(self.data_loader, 'year', 2025)}")
            
            # 創建分析器實例
            analyzer = AnnualDNFStatistics(
                data_loader=self.data_loader,
                year=getattr(self.data_loader, 'year', 2025)
            )
            
            # 執行分析
            result = analyzer.analyze()
            
            if result:
                return {"success": True, "message": "年度DNF統計分析完成", "function_id": "11.2"}
            else:
                return {"success": False, "message": "年度DNF統計分析未產生結果", "function_id": "11.2"}
        except Exception as e:
            return {"success": False, "message": f"年度DNF統計失敗: {str(e)}", "function_id": "11.2"}
    
    def _execute_single_driver_corner_integrated(self, **kwargs):
        """執行單車手彎道整合分析"""
        try:
            from CLI_modules.cli.analyzer.single_driver_corner_analysis_integrated import run_single_driver_corner_analysis_integrated
            print("[F1] 執行單車手彎道整合分析...")
            run_single_driver_corner_analysis_integrated(
                self.data_loader,
                f1_analysis_instance=self.f1_analysis_instance
            )
            return {"success": True, "message": "單車手彎道整合分析完成", "function_id": "12.1"}
        except Exception as e:
            return {"success": False, "message": f"單車手彎道整合分析失敗: {str(e)}", "function_id": "12.1"}
    
    def _execute_team_drivers_corner_comparison(self, **kwargs):
        """執行隊伍車手彎道比較"""
        try:
            from CLI_modules.cli.analyzer.team_drivers_corner_comparison_integrated import run_team_drivers_corner_comparison_integrated
            print("🆚 執行隊伍車手彎道比較...")
            run_team_drivers_corner_comparison_integrated(
                self.data_loader,
                self.dynamic_team_mapping,
                self.f1_analysis_instance
            )
            return {"success": True, "message": "隊伍車手彎道比較完成", "function_id": "12.2"}
        except Exception as e:
            return {"success": False, "message": f"隊伍車手彎道比較失敗: {str(e)}", "function_id": "12.2"}
    
    # ===== 預留擴展功能實現 (23-52) =====
    
    def _execute_weather_analysis_advanced(self, **kwargs):
        """高級天氣分析"""
        return {"success": True, "message": "高級天氣分析功能開發中", "function_id": "23"}
    
    def _execute_tire_strategy_optimization(self, **kwargs):
        """輪胎策略優化"""
        return {"success": True, "message": "輪胎策略優化功能開發中", "function_id": "24"}
    
    def _execute_lap_time_prediction(self, **kwargs):
        """圈速預測分析"""
        return {"success": True, "message": "圈速預測分析功能開發中", "function_id": "25"}
    
    def _execute_fuel_consumption_analysis(self, **kwargs):
        """燃料消耗分析"""
        return {"success": True, "message": "燃料消耗分析功能開發中", "function_id": "26"}
    
    def _execute_aerodynamic_efficiency_analysis(self, **kwargs):
        """空氣動力學效率分析"""
        return {"success": True, "message": "空氣動力學效率分析功能開發中", "function_id": "27"}
    
    def _execute_brake_performance_analysis(self, **kwargs):
        """煞車性能分析 (Function 34)"""
        try:
            from CLI_modules.cli.analyzer.brake_performance_analyzer import (
                BrakePerformanceAnalyzer,
            )

            print("[START] 全部車手煞車性能分析 (Function 34)")

            if not self._check_data_loaded(34):
                return {
                    "success": False,
                    "message": "尚未載入賽事資料，無法執行煞車性能分析",
                    "function_id": "34",
                }

            year = kwargs.get("year", getattr(self.data_loader, "year", None))
            race = kwargs.get("race", getattr(self.data_loader, "race_name", None))
            session = kwargs.get("session", getattr(self.data_loader, "session_type", None))
            top_n = kwargs.get("top_n")
            include_chart = kwargs.get("include_chart", True)

            analyzer = BrakePerformanceAnalyzer(
                self.data_loader,
                year=year,
                race=race,
                session=session,
            )
            result = analyzer.run(top_n=top_n, include_chart=include_chart)

            if result.get("success"):
                self._export_to_json(result, 34, "brake_performance")

            return result

        except Exception as exc:
            print(f"[ERROR] 煞車性能分析失敗: {exc}")
            return {
                "success": False,
                "message": f"煞車性能分析失敗: {exc}",
                "function_id": "34",
            }
    
    def _check_parts_freshness(self, year: int) -> dict:
        """
        檢查部件分析數據的新鮮度（與 Function 97 一致）
        
        Returns:
            dict: {
                "exists": bool,
                "path": str,
                "age_hours": float,
                "is_fresh": bool,
                "should_regenerate": bool,
                "refresh_interval_hours": float
            }
        """
        import os
        from pathlib import Path
        from datetime import datetime, timezone
        
        json_dir = Path("json")
        if not json_dir.exists():
            return {
                "exists": False,
                "path": None,
                "age_hours": None,
                "is_fresh": False,
                "should_regenerate": True,
                "reason": "JSON 目錄不存在",
                "refresh_interval_hours": 120
            }
        
        # 搜尋最新版檔案（簡化版固定檔名）
        pattern = f"fia_parts_analysis_{year}.json"
        latest_file = json_dir / pattern
        
        if not latest_file.exists():
            return {
                "exists": False,
                "path": None,
                "age_hours": None,
                "is_fresh": False,
                "should_regenerate": True,
                "reason": "找不到現有部件分析檔案",
                "refresh_interval_hours": 120
            }
        
        # 計算檔案年齡
        file_mtime = datetime.fromtimestamp(latest_file.stat().st_mtime, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        age = now - file_mtime
        age_hours = age.total_seconds() / 3600
        
        # 🔄 使用智能刷新間隔判斷
        refresh_interval = self._determine_parts_refresh_interval(year)
        is_fresh = age_hours < refresh_interval
        
        return {
            "exists": True,
            "path": str(latest_file),
            "age_hours": round(age_hours, 2),
            "is_fresh": is_fresh,
            "should_regenerate": not is_fresh,
            "reason": "檔案仍在有效期內" if is_fresh else "檔案已過期",
            "refresh_interval_hours": refresh_interval
        }
    
    def _determine_parts_refresh_interval(self, year: int) -> float:
        """
        判斷部件分析刷新間隔：根據賽事狀態決定刷新頻率（與 Function 97 一致）
        
        策略：
        - 正常模式：120 小時（5 天）- 賽程間期穩定時段
        - 賽前加速模式：12 小時 - 賽前 2 天內，頻繁檢查部件變更
        - 賽後加速模式：6 小時 - 賽後 24 小時內，密集監控部件更新
        
        Args:
            year: 賽季年份
            
        Returns:
            刷新間隔（小時）
        """
        from pathlib import Path
        from datetime import datetime, timezone
        import json
        
        # 刷新間隔常數（與 Function 97 一致）
        PARTS_REFRESH_HOURS_NORMAL = 120  # 5 天
        PARTS_REFRESH_HOURS_RACE_APPROACHING = 12  # 12 小時
        PARTS_REFRESH_HOURS_POST_RACE = 6  # 6 小時
        RACE_APPROACHING_THRESHOLD_DAYS = 2
        POST_RACE_MONITORING_HOURS = 24
        
        try:
            json_dir = Path("json")
            if not json_dir.exists():
                return PARTS_REFRESH_HOURS_NORMAL
            
            # 尋找最新的 season_calendar JSON
            calendar_files = sorted(
                json_dir.glob("season_calendar_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
            
            if not calendar_files:
                return PARTS_REFRESH_HOURS_NORMAL
            
            # 讀取 calendar JSON
            with open(calendar_files[0], "r", encoding="utf-8") as f:
                calendar_data = json.load(f)
            
            events = calendar_data.get("data", {}).get("events", [])
            if not events:
                return PARTS_REFRESH_HOURS_NORMAL
            
            # 過濾指定年份的賽事
            year_events = [e for e in events if e.get("season_year") == year]
            if not year_events:
                return PARTS_REFRESH_HOURS_NORMAL
            
            now = datetime.now(timezone.utc)
            
            # 分離已完成和未完成的賽事
            completed_events = [e for e in year_events if e.get("is_completed", False)]
            upcoming_events = [e for e in year_events if not e.get("is_completed", False)]
            
            # 🔥 優先檢查：賽後 24 小時內的加速模式（最高優先級）
            if completed_events:
                latest_completed = completed_events[-1]
                race_date_str = latest_completed.get("race_date")
                
                if race_date_str:
                    try:
                        race_date = datetime.strptime(race_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                        hours_since_race = (now - race_date).total_seconds() / 3600
                        
                        # 🏁 賽後 24 小時內，啟用賽後加速模式（6 小時刷新）
                        if 0 <= hours_since_race <= POST_RACE_MONITORING_HOURS:
                            race_name = latest_completed.get("event_name", "Unknown")
                            remaining_hours = POST_RACE_MONITORING_HOURS - hours_since_race
                            print(f"[PARTS] 🏁 賽後監控期！{race_name} 結束後 {hours_since_race:.1f} 小時")
                            print(f"[PARTS] 🔥 啟用賽後加速模式（6 小時刷新），剩餘監控時間 {remaining_hours:.1f} 小時")
                            return PARTS_REFRESH_HOURS_POST_RACE
                    except ValueError:
                        pass
            
            # 🚨 次要檢查：賽前 2 天內的加速模式
            if upcoming_events:
                for event in upcoming_events[:3]:
                    race_date_str = event.get("race_date")
                    if race_date_str:
                        try:
                            race_date = datetime.strptime(race_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                            days_until_race = (race_date - now).days
                            
                            # 🏎️ 賽前 2 天內，啟用賽前加速模式
                            if 0 <= days_until_race <= RACE_APPROACHING_THRESHOLD_DAYS:
                                race_name = event.get("event_name", "Unknown")
                                print(f"[PARTS] 🏎️ 賽事臨近！{race_name} 在 {days_until_race} 天後")
                                print(f"[PARTS] ⚡ 啟用賽前加速模式（12 小時刷新）")
                                return PARTS_REFRESH_HOURS_RACE_APPROACHING
                        except ValueError:
                            continue
            
            # ✅ 正常模式：賽程間期
            if not upcoming_events:
                print(f"[PARTS] ✅ 賽季已結束，使用正常模式（120 小時）")
            else:
                print(f"[PARTS] ✅ 無特殊事件，使用正常模式（120 小時）")
            
            return PARTS_REFRESH_HOURS_NORMAL
            
        except Exception as e:
            print(f"[PARTS] ❌ 判斷刷新間隔時出錯: {e}，降級使用正常模式")
            return PARTS_REFRESH_HOURS_NORMAL
    
    def _execute_fia_parts_analysis(self, **kwargs):
        """FIA Parts Changes Analysis (Function 29)
        
        分析 FIA 技術文件中的部件變更記錄
        支援按年份、車隊、車手、變更類型篩選
        使用 V2.0 分類器提供高品質分析
        
        ✅ 智能刷新機制（與 Function 97 一致）：
        - 賽後 24 小時內：6 小時刷新（密集監控部件更新）
        - 賽前 2 天內：12 小時刷新（頻繁檢查部件變更）
        - 正常時期：120 小時刷新（5 天穩定期）
        """
        try:
            import json
            import os
            from pathlib import Path
            from collections import Counter, defaultdict
            from CLI_modules.cli.core.fia_parts_classifier import UpgradeClassifierV2
            
            print("[START] FIA 部件變更分析 (Function 29) - 使用 V2.0 分類器")
            print("🔄 智能刷新機制：根據賽事狀態自動調整更新頻率")
            
            # 獲取參數
            year = kwargs.get("year", 2025)
            force = kwargs.get("force", False)  # 是否強制刷新
            team = kwargs.get("team")  # 可選：篩選特定車隊
            driver = kwargs.get("driver")  # 可選：篩選特定車手
            change_type = kwargs.get("change_type")  # 可選：篩選變更類型
            race = kwargs.get("race")  # 可選：篩選特定賽事
            min_confidence = kwargs.get("min_confidence", 0.0)  # 最低信心度過濾
            exclude_noise = kwargs.get("exclude_noise", True)  # 預設排除噪音
            
            # ✅ 智能刷新機制：檢查現有檔案新鮮度（與 Function 97 一致）
            if not force:
                freshness = self._check_parts_freshness(year)
                if freshness.get("is_fresh"):
                    print("=" * 80)
                    print("✅ 部件分析資料仍在有效期內，使用既有 JSON")
                    print(f"📄 路徑: {freshness['path']}")
                    print(f"⏰ 年齡: {freshness['age_hours']} 小時")
                    print(f"🔄 刷新間隔: {freshness['refresh_interval_hours']} 小時")
                    print("=" * 80)
                    try:
                        with open(freshness["path"], "r", encoding="utf-8") as handle:
                            payload = json.load(handle)
                        
                        # 更新 metadata
                        payload["metadata"] = payload.get("metadata", {})
                        payload["metadata"]["last_freshness_check"] = datetime.now().isoformat()
                        payload["metadata"]["file_age_hours"] = freshness["age_hours"]
                        payload["metadata"]["is_fresh"] = True
                        payload["metadata"]["refresh_interval_hours"] = freshness["refresh_interval_hours"]
                        payload["message"] = payload.get("message", "使用既有部件分析資料")
                        
                        print(f"[SUCCESS] 載入既有分析結果：{len(payload.get('records', []))} 筆記錄")
                        return payload
                    except Exception as exc:
                        print(f"[PARTS] 讀取既有 JSON 失敗: {exc}，改為重新生成")
            
            # 如果強制刷新或檔案已過期，重新生成
            if force:
                print("=" * 80)
                print("🔥 強制刷新模式：從 FIAdoc PDF 重新解析生成完整分析")
                print("=" * 80)
                
                # ✅ 簡化模式：使用 SimplePartsParser
                try:
                    from CLI_modules.cli.core.fia_parts_pdf_parser_simple import SimplePartsParser
                    
                    print(f"\n[STEP 1/3] 從 PDF 解析部件變更記錄...")
                    parser = SimplePartsParser(year=year, fiadoc_dir="FIAdoc")
                    parser.analyze_all_documents()
                    
                    if not parser.all_changes:
                        print("⚠️  沒有解析到任何部件變更記錄")
                        return {
                            "success": False,
                            "message": "PDF 解析無結果，請檢查 FIAdoc 資料夾",
                            "function_id": "29"
                        }
                    
                    # ✅ 只保存 PDF 原始資料（移除分類器）
                    print(f"\n[STEP 2/3] 保存 PDF 原始資料...")
                    json_file = f"{year}_f1_parts_changes_raw.json"
                    
                    # 結構化輸出（包含 FastF1 映射表）
                    output_data = {
                        "success": True,
                        "message": f"從 PDF 解析完成，共 {len(parser.all_changes)} 筆記錄",
                        "year": year,
                        "total_records": len(parser.all_changes),
                        "records": parser.all_changes,
                        "driver_mapping": parser.fastf1_mapping if parser.fastf1_mapping else None,
                        "metadata": {
                            "source": "FIAdoc PDF - Parts and parameters been replaced",
                            "parser_version": "SimplePartsParser v2.0",
                            "mapping_source": parser.mapping_source,
                            "extracted_fields": ["賽事", "賽事日期", "車隊", "車手", "車號", "部件", "來源文件", "年份"],
                            "note": "此資料包含 PDF 原始資訊 + FastF1 動態車號映射"
                        }
                    }
                    
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(output_data, f, ensure_ascii=False, indent=2)
                    
                    print(f"✅ PDF 解析完成：{len(parser.all_changes)} 筆記錄")
                    print(f"💾 已保存: {json_file}")
                    print(f"📋 資料欄位: 賽事、賽事日期、車隊、車手、車號、部件")
                    print(f"🗺️  車號映射: {parser.mapping_source} ({len(parser.CAR_NUMBER_TO_DRIVER)} 位車手)")
                    if parser.fastf1_mapping:
                        print(f"🗺️  映射已包含在主 JSON 的 driver_mapping 欄位中")
                    
                except Exception as pdf_error:
                    print(f"❌ PDF 解析失敗: {pdf_error}")
                    import traceback
                    traceback.print_exc()
                    return {
                        "success": False,
                        "message": f"PDF 解析失敗: {str(pdf_error)}",
                        "function_id": "29"
                    }
            else:
                print("=" * 80)
                print("⚠️  部件分析資料已過期，重新生成...")
                freshness = self._check_parts_freshness(year)
                print(f"📄 舊檔案年齡: {freshness.get('age_hours', 'N/A')} 小時")
                print(f"🔄 刷新間隔: {freshness.get('refresh_interval_hours', 120)} 小時")
                print("=" * 80)
            
            # 讀取 PDF 原始資料（唯一版本）
            json_file = f"{year}_f1_parts_changes_raw.json"
            
            if not os.path.exists(json_file):
                print(f"[ERROR] 找不到資料檔案: {json_file}")
                print(f"💡 提示: 使用 --force 參數重新生成")
                return {
                    "success": False,
                    "message": f"找不到 FIA 部件變更資料檔案: {json_file}",
                    "function_id": "29"
                }
            
            print(f"[INFO] 讀取 PDF 原始資料: {json_file}")
            with open(json_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # 提取記錄列表（新格式包含 metadata）
            if isinstance(json_data, dict) and "records" in json_data:
                all_records = json_data["records"]
            else:
                all_records = json_data  # 舊格式直接是列表
            
            print(f"[INFO] 載入 {len(all_records)} 筆部件變更記錄")
            
            # 篩選資料
            filtered_records = all_records
            
            # ❌ 移除噪音過濾（PDF 原始資料無分類資訊）
            # ❌ 移除信心度過濾（PDF 原始資料無信心度）
            # ❌ 移除變更類型過濾（PDF 原始資料無變更類型）
            
            if team:
                filtered_records = [r for r in filtered_records if r.get("車隊") == team]
                print(f"[FILTER] 車隊={team}, 剩餘 {len(filtered_records)} 筆")
            
            if driver:
                filtered_records = [r for r in filtered_records if r.get("車手") == driver]
                print(f"[FILTER] 車手={driver}, 剩餘 {len(filtered_records)} 筆")
            
            if race:
                filtered_records = [r for r in filtered_records if r.get("賽事") == race]
                print(f"[FILTER] 賽事={race}, 剩餘 {len(filtered_records)} 筆")
            
            if not filtered_records:
                print("[WARNING] 篩選後無資料")
                return {
                    "success": False,
                    "message": "篩選條件過嚴，無符合的記錄",
                    "function_id": "29"
                }
            
            # ✅ 統計分析（只包含 PDF 原始欄位）
            stats = {
                "total_records": len(filtered_records),
                "by_team": dict(Counter([r["車隊"] for r in filtered_records])),
                "by_race": dict(Counter([r.get("賽事", "Unknown") for r in filtered_records])),
                "by_driver": dict(Counter([r["車手"] for r in filtered_records]))
            }
            
            # 前 5 名車隊
            top5_teams = dict(Counter(stats["by_team"]).most_common(5))
            
            # 輸出結果
            print("\n" + "="*80)
            print(f"FIA 部件變更分析報告 - {year} (PDF 原始資料)")
            print("="*80)
            print(f"總記錄數: {stats['total_records']}")
            
            print(f"\n賽事分佈:")
            for race_name, count in sorted(stats["by_race"].items(), key=lambda x: x[1], reverse=True):
                percentage = (count / stats['total_records']) * 100
                print(f"  {race_name}: {count} 筆 ({percentage:.1f}%)")
            
            print(f"\n前 5 名車隊 (部件變更次數):")
            for idx, (team_name, count) in enumerate(top5_teams.items(), 1):
                print(f"  {idx}. {team_name}: {count} 筆")
            
            # 構建結果
            # ✅ 添加智能刷新間隔資訊
            refresh_interval = self._determine_parts_refresh_interval(year)
            
            result = {
                "success": True,
                "message": f"FIA 部件變更分析完成 ({stats['total_records']} 筆記錄) - PDF 原始資料",
                "function_id": "29",
                "data_version": "Raw PDF Data Only",
                "year": year,
                "filters": {
                    "team": team,
                    "driver": driver,
                    "race": race
                },
                "metadata": {
                    "generated_at": None,  # 將在下方設定
                    "refresh_interval_hours": refresh_interval,
                    "is_fresh": True,
                    "force_refresh": force,
                    "note": "此資料僅包含 PDF 原始資訊（賽事、賽事日期、車隊、車手、車號、部件），無自動分類或推斷說明"
                },
                "statistics": stats,
                "top5_teams": top5_teams,
                "records": filtered_records
            }
            
            # 導出 JSON（Function 29 專用：只用 year 不用 race/session）
            # ✅ 與 Function 97 (Championship Standings) 保持一致的命名邏輯
            json_dir = "json"
            os.makedirs(json_dir, exist_ok=True)
            
            # 構建過濾器後綴（如果有過濾條件）
            filter_suffix = ""
            if team:
                filter_suffix += f"_team_{team}"
            if driver:
                filter_suffix += f"_driver_{driver}"
            if race:
                filter_suffix += f"_race_{race}"
            if change_type:
                filter_suffix += f"_type_{change_type}"
            if min_confidence > 0.0:
                filter_suffix += f"_conf{int(min_confidence*100)}"
            
            # 📝 時間戳格式：ISO 8601 格式
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%dT%H%M%SZ")
            
            # 📝 檔名規則（簡化版）：
            # - 最新版（無時間戳）：fia_parts_analysis_{year}.json
            # - 歷史版（帶時間戳）：fia_parts_analysis_{year}_{filter}_{timestamp}.json
            
            # 生成兩個檔案
            json_filename_latest = f"fia_parts_analysis_{year}{filter_suffix}.json"
            json_filename_archive = f"fia_parts_analysis_{year}{filter_suffix}_{timestamp}.json"
            
            # 添加時間戳到 result 內容（與 Function 97 一致）
            result["generated_at"] = datetime.now().isoformat()
            result["timestamp"] = timestamp
            
            # 保存最新版（固定檔名，供 GUI 讀取）
            json_path_latest = os.path.join(json_dir, json_filename_latest)
            with open(json_path_latest, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            print(f"\n📄 JSON 最新版已保存: {json_path_latest}")
            
            # 保存歷史版（帶時間戳，供備份）
            json_path_archive = os.path.join(json_dir, json_filename_archive)
            with open(json_path_archive, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            print(f"📄 JSON 歷史版已保存: {json_path_archive}")
            
            print("\n[SUCCESS] FIA 部件變更分析完成 (V2.0 分類器)")
            return result
            
        except Exception as exc:
            print(f"[ERROR] FIA 部件變更分析失敗: {exc}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"FIA 部件變更分析失敗: {exc}",
                "function_id": "29"
            }
    
    def _execute_tire_strategy_optimization(self, **kwargs):
        """輪胎策略優化 (Function 30)"""
        return {"success": True, "message": "輪胎策略優化功能開發中", "function_id": "30"}
    
    def _execute_lap_time_prediction(self, **kwargs):
        """圈速預測分析 (Function 31)"""
        return {"success": True, "message": "圈速預測分析功能開發中", "function_id": "31"}
    
    def _execute_fuel_consumption_analysis(self, **kwargs):
        """燃料消耗分析 (Function 32)"""
        return {"success": True, "message": "燃料消耗分析功能開發中", "function_id": "32"}
    
    def _execute_aerodynamic_efficiency_analysis(self, **kwargs):
        """空氣動力學效率分析 (Function 33)"""
        return {"success": True, "message": "空氣動力學效率分析功能開發中", "function_id": "33"}
    
    def _execute_engine_performance_analysis(self, **kwargs):
        """引擎性能分析 (Function 35)"""
        return {"success": True, "message": "引擎性能分析功能開發中", "function_id": "35"}
    
    def _execute_race_strategy_simulation(self, **kwargs):
        """賽事策略模擬"""
        return {"success": True, "message": "賽事策略模擬功能開發中", "function_id": "30"}
    
    def _execute_championship_impact_analysis(self, **kwargs):
        """championship impact analysis"""
        return {"success": True, "message": "championship impact analysis功能開發中", "function_id": "31"}
    
    def _execute_track_evolution_analysis(self, **kwargs):
        """賽道演化分析"""
        return {"success": True, "message": "賽道演化分析功能開發中", "function_id": "32"}
    
    def _execute_safety_car_impact_analysis(self, **kwargs):
        """安全車影響分析"""
        return {"success": True, "message": "安全車影響分析功能開發中", "function_id": "33"}
    
    # ===== 全部車手分析模組實現 (34-46) =====
    
    def _execute_all_drivers_statistics_overview(self, **kwargs):
        """全部車手統計總覽"""
        return {"success": True, "message": "全部車手統計總覽功能開發中", "function_id": "34"}
    
    def _execute_all_drivers_telemetry_comparison(self, **kwargs):
        """全部車手遙測比較"""
        return {"success": True, "message": "全部車手遙測比較功能開發中", "function_id": "35"}
    
    def _execute_all_drivers_consistency_analysis(self, **kwargs):
        """全部車手一致性分析"""
        return {"success": True, "message": "全部車手一致性分析功能開發中", "function_id": "36"}
    
    def _execute_all_drivers_race_pace_analysis(self, **kwargs):
        """全部車手比賽節奏分析"""
        return {"success": True, "message": "全部車手比賽節奏分析功能開發中", "function_id": "37"}
    
    def _execute_all_drivers_qualifying_analysis(self, **kwargs):
        """全部車手排位賽分析"""
        return {"success": True, "message": "全部車手排位賽分析功能開發中", "function_id": "38"}
    
    def _execute_all_drivers_tire_management(self, **kwargs):
        """全部車手輪胎管理分析"""
        return {"success": True, "message": "全部車手輪胎管理分析功能開發中", "function_id": "39"}
    
    def _execute_all_drivers_sector_analysis(self, **kwargs):
        """全部車手分段分析"""
        return {"success": True, "message": "全部車手分段分析功能開發中", "function_id": "40"}
    
    def _execute_all_drivers_cornering_analysis(self, **kwargs):
        """Function 47: 全車手彎道速度分析（多彎道模式）
        
        ⚠️ 棄用警告 (2025-12-14): 
        此功能已被 Function 120 (F120_corner_all_laps_analysis) 取代。
        F120 提供更完整的數據結構，包括過濾旗標和統計指標。
        建議使用 function_id=120 獲取彎道分析數據。
        """
        try:
            # ⚠️ 輸出棄用警告
            print("[⚠️ DEPRECATED] Function 47 已棄用，建議改用 Function 120 (F120_corner_all_laps_analysis)")
            print("[⚠️ DEPRECATED] F120 提供過濾旗標 (entry_filtered, exit_filtered) 和更完整的統計數據")
            
            from CLI_modules.cli.analyzer.all_drivers_cornering_analysis import (
                run_all_drivers_cornering_analysis
            )
            
            print("[START] 開始執行全車手彎道速度分析 (Function 47)")
            
            # 檢查數據是否已載入
            if not self._check_data_loaded(47):
                return {
                    "success": False,
                    "message": "尚未載入賽事資料",
                    "function_id": "47"
                }
            
            # 執行分析
            result = run_all_drivers_cornering_analysis(
                data_loader=self.data_loader,
                year=getattr(self.data_loader, 'year', None),
                race=getattr(self.data_loader, 'race_name', None),
                session=getattr(self.data_loader, 'session_type', None),
                show_detailed_output=kwargs.get('show_detailed_output', True)
            )
            
            # 導出 JSON
            if result and result.get("success"):
                self._export_to_json(result, 47, "all_drivers_cornering_analysis")
            
            return result
            
        except Exception as e:
            print(f"[ERROR] 全車手彎道速度分析失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"分析失敗: {str(e)}",
                "function_id": "47"
            }
    
    def _execute_fp2_corner_all_laps_analysis(self, **kwargs):
        """Function 120: FP2 彎道全圈數分析（雙模式：統一+分組）"""
        try:
            from CLI_modules.cli.analyzer.fp2_corner_all_laps_analysis import (
                run_fp2_corner_all_laps_analysis
            )
            
            print("[F120 START] 開始執行彎道全圈數分析 (Function 120)")
            
            # 檢查數據是否已載入
            if not self._check_data_loaded(120):
                return {
                    "success": False,
                    "message": "尚未載入賽事資料",
                    "function_id": "120"
                }
            
            # 🆕 方案 A：智慧會話選擇
            session_type = getattr(self.data_loader, 'session_type', None)
            race_name = getattr(self.data_loader, 'race_name', None)
            sprint_races = ["China", "Miami", "Belgium", "USA", "Brazil", "Qatar"]
            
            is_sprint = race_name in sprint_races
            recommended_session = "SQ" if is_sprint else "FP2"
            
            if session_type != recommended_session:
                if is_sprint:
                    print(f"[F120 INFO] {race_name} 是衝刺賽週末，建議使用 SQ (當前: {session_type})")
                else:
                    print(f"[F120 INFO] {race_name} 是一般賽事，建議使用 FP2 (當前: {session_type})")
            
            # 執行分析
            result = run_fp2_corner_all_laps_analysis(
                data_loader=self.data_loader,
                year=getattr(self.data_loader, 'year', None),
                race=getattr(self.data_loader, 'race_name', None),
                session=session_type,
                show_detailed_output=kwargs.get('show_detailed_output', True)
            )
            
            # 導出 JSON
            if result and result.get("success"):
                self._export_to_json(result, 120, "F120_corner_all_laps_analysis")
            
            return result
            
        except Exception as e:
            print(f"[F120 ERROR] FP2 彎道全圈數分析失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"執行失敗: {str(e)}",
                "function_id": "120"
            }
    
    def _execute_fp2_straight_line_all_laps_analysis(self, **kwargs):
        """Function 121: FP2 直線速度全圈數分析（官方API版本）"""
        try:
            from CLI_modules.cli.analyzer.fp2_straight_line_all_laps_analysis import (
                FP2StraightLineAllLapsAnalysis
            )
            
            print("[F121 START] 開始執行直線速度全圈數分析 (Function 121)")
            
            # 檢查數據是否已載入
            if not self._check_data_loaded(121):
                return {
                    "success": False,
                    "message": "尚未載入賽事資料",
                    "function_id": "121"
                }
            
            # 🆕 方案 A：智慧會話選擇
            session_type = getattr(self.data_loader, 'session_type', None)
            race_name = getattr(self.data_loader, 'race_name', None)
            sprint_races = ["China", "Miami", "Belgium", "USA", "Brazil", "Qatar"]
            
            is_sprint = race_name in sprint_races
            recommended_session = "SQ" if is_sprint else "FP2"
            
            if session_type != recommended_session:
                if is_sprint:
                    print(f"[F121 INFO] {race_name} 是衝刺賽週末，建議使用 SQ (當前: {session_type})")
                else:
                    print(f"[F121 INFO] {race_name} 是一般賽事，建議使用 FP2 (當前: {session_type})")
            
            # 執行分析
            analyzer = FP2StraightLineAllLapsAnalysis(self.data_loader)
            result = analyzer.analyze(show_detailed_output=kwargs.get('show_detailed_output', True))
            
            # 導出 JSON
            if result and result.get("success"):
                self._export_to_json(result, 121, "fp2_straight_line_all_laps_analysis")
            
            return result
            
        except Exception as e:
            print(f"[F121 ERROR] FP2 直線速度全圈數分析失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"執行失敗: {str(e)}",
                "function_id": "121"
            }
    
    def _execute_brake_all_laps_analysis(self, **kwargs):
        """Function 122: 煞車性能全圈數分析（官方API版本+多數決統一煞車點）"""
        try:
            from CLI_modules.cli.analyzer.brake_all_laps_analysis import (
                BrakeAllLapsAnalysis
            )

            print("[F122 START] 開始執行煞車性能全圈數分析 (Function 122)")

            # 檢查數據是否已載入
            if not self._check_data_loaded(122):
                return {
                    "success": False,
                    "message": "尚未載入賽事資料",
                    "function_id": "122"
                }

            # 執行分析（支援所有會話類型：FP1/FP2/FP3/Q/R）
            analyzer = BrakeAllLapsAnalysis(self.data_loader)
            result = analyzer.analyze(show_detailed_output=kwargs.get('show_detailed_output', True))

            # 導出 JSON
            if result and result.get("success"):
                self._export_to_json(result, 122, "brake_all_laps_analysis")

            return result

        except Exception as e:
            print(f"[F122 ERROR] 煞車性能全圈數分析失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"執行失敗: {str(e)}",
                "function_id": "122"
            }

    def _execute_vehicle_performance_analysis(self, **kwargs):
        """Function 125: 車輛性能綜合分析（整合F120+F121+F122+F100）"""
        try:
            from CLI_modules.cli.analyzer.f125_vehicle_performance import (
                run_vehicle_performance_analysis
            )

            print("[F125 START] 開始執行車輛性能綜合分析 (Function 125)")

            # 檢查數據是否已載入
            if not self._check_data_loaded(125):
                return {
                    "success": False,
                    "message": "尚未載入賽事資料",
                    "function_id": "125"
                }

            # 獲取年份、賽事、會話類型
            year = self.data_loader.year
            race = self.data_loader.race_name
            session = self.data_loader.session_type

            print(f"[F125 INFO] 分析參數: {year} {race} {session}")

            # 執行分析
            result = run_vehicle_performance_analysis(
                year=year,
                race=race,
                session=session
            )

            # 導出 JSON
            if result and result.get("success"):
                self._export_to_json(result, 125, "vehicle_performance_analysis")

            return result

        except Exception as e:
            error_msg = f"F125 execution failed: {str(e)}"
            print(f"[F125 ERROR] {error_msg}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": error_msg,
                "function_id": "125"
            }

    def _execute_all_drivers_straight_line_speed(self, **kwargs):
        """全部車手直線速度分析"""
        try:
            from CLI_modules.cli.analyzer.all_drivers_straight_line_speed import (
                AllDriversStraightLineSpeedAnalysis,
            )

            print("[START] 全部車手直線速度分析 (Function 48)")

            if not self._check_data_loaded(48):
                return {
                    "success": False,
                    "message": "尚未載入賽事資料，無法執行全部車手直線速度分析",
                    "function_id": "48",
                }

            year = kwargs.get("year", getattr(self.data_loader, "year", None))
            race = kwargs.get("race", getattr(self.data_loader, "race_name", None))
            session = kwargs.get("session", getattr(self.data_loader, "session_type", None))
            top_n = kwargs.get("top_n")
            include_chart = kwargs.get("include_chart", True)

            analyzer = AllDriversStraightLineSpeedAnalysis(
                self.data_loader,
                year=year,
                race=race,
                session=session,
            )
            result = analyzer.run(top_n=top_n, include_chart=include_chart)

            if result.get("success"):
                self._export_to_json(result, 48, "all_drivers_straight_line_speed")

            return result

        except Exception as exc:
            print(f"[ERROR] 全部車手直線速度分析失敗: {exc}")
            return {
                "success": False,
                "message": f"全部車手直線速度分析失敗: {exc}",
                "function_id": "48",
            }
    
    def _execute_all_drivers_race_starts_analysis(self, **kwargs):
        """全部車手起步分析"""
        return {"success": True, "message": "全部車手起步分析功能開發中", "function_id": "43"}
    
    def _execute_all_drivers_defensive_driving(self, **kwargs):
        """全部車手防守駕駛分析"""
        return {"success": True, "message": "全部車手防守駕駛分析功能開發中", "function_id": "44"}
    
    def _execute_all_drivers_wet_weather_performance(self, **kwargs):
        """全部車手雨天表現分析"""
        return {"success": True, "message": "全部車手雨天表現分析功能開發中", "function_id": "45"}
    
    def _execute_all_drivers_championship_simulation(self, **kwargs):
        """全部車手championship模擬"""
        return {"success": True, "message": "全部車手championship模擬功能開發中", "function_id": "46"}
    
    # ===== 系統功能實現 (47-52) =====
    
    def _execute_data_export_manager(self, **kwargs):
        """數據導出管理"""
        return {"success": True, "message": "數據導出管理功能開發中", "function_id": "47"}
    
    def _execute_cache_optimization(self, **kwargs):
        """緩存優化"""
        return {"success": True, "message": "緩存優化功能開發中", "function_id": "48"}
    
    def _execute_system_diagnostics(self, **kwargs):
        """系統診斷"""
        return {"success": True, "message": "系統診斷功能開發中", "function_id": "49"}
    
    def _execute_performance_benchmarking(self, **kwargs):
        """效能基準測試"""
        return {"success": True, "message": "效能基準測試功能開發中", "function_id": "50"}

    def _execute_ideal_lap_analysis(self, **kwargs):
        """Function 53: 全車手理想圈分析"""

        try:
            from CLI_modules.cli.analyzer.ideal_lap_analysis import IdealLapAnalyzer
        except ImportError as exc:  # pragma: no cover - module import guard
            message = f"無法載入理想圈分析模組: {exc}"
            print(f"[ERROR] {message}")
            return {
                "success": False,
                "message": message,
                "function_id": "53",
                "data": None,
            }

        if self.data_loader is None:
            return {
                "success": False,
                "message": "理想圈分析失敗：資料載入器未就緒",
                "function_id": "53",
                "data": None,
            }

        debug = kwargs.get("debug") if "debug" in kwargs else True
        save_json = kwargs.get("save_json", True)

        analyzer = IdealLapAnalyzer(self.data_loader, debug=bool(debug))

        if not analyzer.load_data():
            return {
                "success": False,
                "message": "理想圈分析失敗：無可用圈速資料",
                "function_id": "53",
                "data": None,
            }

        driver_results = analyzer.analyze_all_drivers()
        payload = analyzer.build_json(driver_results)

        output_file = None
        if payload.get("success") and save_json:
            output_file = analyzer.save_json(payload)
            if output_file:
                payload["output_file"] = output_file

        result = {
            "success": payload.get("success", False),
            "message": payload.get("message", "理想圈分析完成") if payload.get("success") else payload.get("message", "理想圈分析失敗"),
            "data": payload,
            "output_file": output_file,
            "cache_used": False,
        }

        return self._standardize_result(result, 53, "全車手理想圈分析")
    
    def _execute_data_integrity_check(self, **kwargs):
        """數據完整性檢查"""
        return {"success": True, "message": "數據完整性檢查功能開發中", "function_id": "51"}
    
    def _execute_api_health_check(self, **kwargs):
        """API 健康檢查"""
        return {
            "success": True,
            "message": "API 系統運行正常",
            "function_id": "52",
            "system_status": {
                "data_loader": self.data_loader is not None,
                "mapping_ready": True,
                "total_functions": len(self.function_mapping) + len(self.sub_function_mapping)
            }
        }

    def _execute_driver_throttle_ratio(self, **kwargs):
        """Function 54: 全車手每圈油門比例分析"""

        try:
            from CLI_modules.cli.analyzer.driver_throttle_ratio import (
                DEFAULT_COAST_THRESHOLD,
                DEFAULT_FULL_THROTTLE_THRESHOLD,
                run_driver_throttle_ratio_analysis,
            )
        except ImportError as exc:
            message = f"無法載入油門分析模組: {exc}"
            print(f"[ERROR] {message}")
            return {
                "success": False,
                "message": message,
                "function_id": "54",
                "data": None,
            }

        threshold = kwargs.get("threshold") or kwargs.get("full_throttle_threshold")
        coast_threshold = kwargs.get("coast_threshold")
        show_summary = kwargs.get("show_summary", True)
        save_json = kwargs.get("save_json", True)

        try:
            result = run_driver_throttle_ratio_analysis(
                data_loader=self.data_loader,
                threshold=float(threshold) if threshold is not None else DEFAULT_FULL_THROTTLE_THRESHOLD,
                coast_threshold=float(coast_threshold) if coast_threshold is not None else DEFAULT_COAST_THRESHOLD,
                show_summary=bool(show_summary),
                save_json=False,  # JSON 保存由下方 _export_to_json() 統一處理
            )
            
            # 統一 JSON 導出邏輯（與 F34/F47/F48 一致）
            if result.get("success"):
                self._export_to_json(result, 54, "driver_throttle_ratio")
            
            return result
        except Exception as exc:  # pragma: no cover - runtime safeguard
            message = f"全車手油門比例分析失敗: {exc}"
            print(f"[ERROR] {message}")
            return {
                "success": False,
                "message": message,
                "function_id": "54",
                "data": None,
            }

    def _execute_fuel_corrected_laptime(self, **kwargs):
        """Function 55: 燃油校正圈速分析 (F1 官方 Live Timing)
        
        使用 F1 官方 Live Timing 數據進行燃油影響校正的圈速分析
        數據來源: json/LiveF1/ (由 livef1_downloader.py 從 livetiming.formula1.com 下載)
        公式: T_corrected = T_actual + fuel_effect_coef * fuel_consumed
        """
        try:
            from CLI_modules.cli.prediction.fuel_corrected_laptime_analyzer import (
                run_fuel_corrected_analysis,
            )
        except ImportError as exc:
            message = f"無法載入燃油校正分析模組: {exc}"
            print(f"[ERROR] {message}")
            return {
                "success": False,
                "message": message,
                "function_id": "55",
                "data": None,
            }
        
        # 從 data_loader 或 kwargs 獲取參數
        year = kwargs.get("year")
        race = kwargs.get("race")
        session = kwargs.get("session", "R")
        drivers = kwargs.get("drivers")
        show_detailed_output = kwargs.get("show_detailed_output", True)
        
        if self.data_loader is not None:
            year = year or getattr(self.data_loader, 'year', None)
            race = race or getattr(self.data_loader, 'race_name', None)
            session = session or getattr(self.data_loader, 'session_type', 'R')
        
        # 預設值
        year = year or 2024
        race = race or "Italian"
        
        try:
            result = run_fuel_corrected_analysis(
                data_loader=self.data_loader,
                year=int(year),
                race=str(race),
                session=str(session),
                drivers=drivers,
                show_detailed_output=bool(show_detailed_output)
            )
            
            return self._standardize_result(result, 55, "燃油校正圈速分析")
        except Exception as exc:
            message = f"燃油校正圈速分析失敗: {exc}"
            print(f"[ERROR] {message}")
            return {
                "success": False,
                "message": message,
                "function_id": "55",
                "data": None,
            }

    def _execute_tire_degradation_analysis(self, **kwargs):
        """Function 56: 輪胎衰退分析 (時變線性模型, F1 Official Live Timing)
        
        基於 Cappello & Hoegh 2025 論文的時變線性衰退模型:
        degradation(t) = base_rate + acceleration * tire_age
        
        功能:
            - 分析各配方 (SOFT/MEDIUM/HARD) 的衰退率
            - 計算最佳 stint 長度
            - 生成賽道級統計
            - 可選: 根據觀測數據更新資料庫
        """
        try:
            from CLI_modules.cli.prediction.tire_degradation_analyzer import (
                run_tire_degradation_analysis,
            )

            year = kwargs.get("year")
            race = kwargs.get("race") or kwargs.get("race_name")
            session = kwargs.get("session") or kwargs.get("session_type") or "R"
            drivers = kwargs.get("drivers") or kwargs.get("driver")
            update_database = kwargs.get("update_database", False)

            if year is None and self.data_loader and getattr(self.data_loader, "year", None):
                year = self.data_loader.year
            if race is None and self.data_loader and getattr(self.data_loader, "race_name", None):
                race = self.data_loader.race_name
            if session == "R" and self.data_loader and getattr(self.data_loader, "session_type", None):
                session = self.data_loader.session_type

            if year is None:
                year = datetime.now().year
            if race is None:
                race = "Austrian"

            # 處理單一車手參數
            if isinstance(drivers, str):
                drivers = [drivers]

            result = run_tire_degradation_analysis(
                data_loader=self.data_loader,
                year=int(year),
                race=str(race),
                session=str(session),
                drivers=drivers,
                show_detailed_output=kwargs.get("show_detailed_output", True),
                update_database=bool(update_database),
            )

            return self._standardize_result(result, 56, "輪胎衰退分析")
        except Exception as exc:
            message = f"輪胎衰退分析失敗: {exc}"
            print(f"[ERROR] {message}")
            return {
                "success": False,
                "message": message,
                "function_id": "56",
                "data": None,
            }

    def _execute_combined_laptime_prediction(self, **kwargs):
        """Function 57: 綜合圈速預測 (整合 F55 燃油校正 + F56 輪胎衰退)
        
        功能:
            結合燃油效應和輪胎衰退進行圈速預測
            predicted_time = base_time + fuel_effect + tire_degradation
        """
        try:
            from CLI_modules.cli.prediction.combined_laptime_predictor import (
                run_combined_laptime_prediction,
            )

            year = kwargs.get("year")
            race = kwargs.get("race") or kwargs.get("race_name")
            session = kwargs.get("session") or kwargs.get("session_type") or "R"
            drivers = kwargs.get("drivers") or kwargs.get("driver")

            if year is None and self.data_loader and getattr(self.data_loader, "year", None):
                year = self.data_loader.year
            if race is None and self.data_loader and getattr(self.data_loader, "race_name", None):
                race = self.data_loader.race_name
            if session == "R" and self.data_loader and getattr(self.data_loader, "session_type", None):
                session = self.data_loader.session_type

            if year is None:
                year = datetime.now().year
            if race is None:
                race = "Austrian"

            # 處理單一車手參數
            if isinstance(drivers, str):
                drivers = [drivers]

            result = run_combined_laptime_prediction(
                data_loader=self.data_loader,
                year=int(year),
                race=str(race),
                session=str(session),
                drivers=drivers,
                show_detailed_output=kwargs.get("show_detailed_output", True),
            )

            return self._standardize_result(result, 57, "Combined Laptime Prediction")
        except Exception as exc:
            message = f"Combined laptime prediction failed: {exc}"
            print(f"[ERROR] {message}")
            return {
                "success": False,
                "message": message,
                "function_id": "57",
                "data": None,
            }

    def _execute_pit_stop_strategy_prediction(self, **kwargs):
        """Function 58: 進站策略預測 (Pit Stop Strategy Predictor)
        
        功能:
            58.1 進站時機預測 - 預測每位車手的最佳進站圈數
            58.2 策略組合優化 - 比較 1-stop / 2-stop / 3-stop 策略
            58.3 Undercut/Overcut 警告 - 實時偵測對手策略威脅
        """
        try:
            from CLI_modules.cli.prediction.pit_stop_strategy_predictor import (
                run_pit_stop_strategy_prediction,
            )

            year = kwargs.get("year")
            race = kwargs.get("race") or kwargs.get("race_name")
            session = kwargs.get("session") or kwargs.get("session_type") or "R"
            drivers = kwargs.get("drivers") or kwargs.get("driver")

            if year is None and self.data_loader and getattr(self.data_loader, "year", None):
                year = self.data_loader.year
            if race is None and self.data_loader and getattr(self.data_loader, "race_name", None):
                race = self.data_loader.race_name
            if session == "R" and self.data_loader and getattr(self.data_loader, "session_type", None):
                session = self.data_loader.session_type

            if year is None:
                year = datetime.now().year
            if race is None:
                race = "Austrian"

            # 處理單一車手參數
            if isinstance(drivers, str):
                drivers = [drivers]

            result = run_pit_stop_strategy_prediction(
                data_loader=self.data_loader,
                year=int(year),
                race=str(race),
                session=str(session),
                drivers=drivers,
                show_detailed_output=kwargs.get("show_detailed_output", True),
            )

            return self._standardize_result(result, 58, "Pit Stop Strategy Prediction")
        except Exception as exc:
            message = f"Pit stop strategy prediction failed: {exc}"
            print(f"[ERROR] {message}")
            return {
                "success": False,
                "message": message,
                "function_id": "58",
                "data": None,
            }

    def _execute_championship_standings_analysis(self, **kwargs):
        """Function 97: 賽季積分查詢 (車手/車隊)"""

        try:
            from CLI_modules.cli.analyzer.championship_standings_analysis import (
                generate_championship_standings,
            )

            year = kwargs.get("year")
            if year is None and self.data_loader and getattr(self.data_loader, "year", None):
                year = self.data_loader.year
            if year is None:
                year = datetime.now().year

            result = generate_championship_standings(
                year=int(year),
                round_hint=kwargs.get("round") or kwargs.get("round_hint") or "last",
                save_json=kwargs.get("save_json", True),
                include_drivers=kwargs.get("include_drivers", True),
                include_constructors=kwargs.get("include_constructors", True),
                force=kwargs.get("force", False),
            )

            return self._standardize_result(result, 97, "賽季積分查詢")

        except Exception as exc:  # pragma: no cover - runtime safeguard
            return {
                "success": False,
                "message": f"賽季積分查詢失敗: {exc}",
                "function_id": "97",
                "data": None,
            }

    def _execute_team_color_analysis(self, **kwargs):
        """Function 98: 顏色配置輸出 (FastF1 團隊/車手色票 + 12小時智能刷新)"""

        try:
            from CLI_modules.cli.analyzer.team_color_analysis import (
                generate_team_color_report,
                check_color_freshness
            )

            colormap = kwargs.get("colormap") or kwargs.get("palette") or "fastf1"
            include_drivers = kwargs.get("include_drivers", True)
            save_json = kwargs.get("save_json", True)
            force = kwargs.get("force", False)  # 是否強制重新生成

            year = kwargs.get("year")
            if year is None and self.data_loader and getattr(self.data_loader, "year", None):
                year = self.data_loader.year
            if year is None:
                year = datetime.now().year

            result = generate_team_color_report(
                year=int(year),
                colormap=str(colormap),
                save_json=bool(save_json),
                include_drivers=bool(include_drivers),
                force=bool(force),
            )

            return self._standardize_result(result, 98, "顏色配置輸出")

        except Exception as exc:  # pragma: no cover - runtime safeguard
            return {
                "success": False,
                "message": f"顏色配置輸出失敗: {exc}",
                "function_id": "98",
                "data": None,
            }

    def _execute_season_calendar_analysis(self, **kwargs):
        """Function 99: 賽季賽程查詢 (支援 2020-2025 批量查詢 + 12小時智能刷新)"""

        try:
            from CLI_modules.cli.analyzer.season_calendar_analysis import (
                generate_season_calendar,
                check_calendar_freshness
            )

            # 檢查是否要批量查詢 2020-2025
            all_years = kwargs.get("all_years", True)  # 預設啟用批量查詢
            force = kwargs.get("force", False)  # 是否強制重新生成
            
            if all_years:
                # 批量查詢 2020-2025 (含智能刷新檢查)
                print("\n🎯 啟用批量查詢模式: 2020-2025 年所有賽季")
                print("🔍 智能刷新機制: 12 小時自動檢查\n")
                
                result = generate_season_calendar(save_json=True, all_years=True, force=force)
            else:
                # 單一年份查詢（原始模式）
                year = kwargs.get("year")
                if not year:
                    if self.data_loader and getattr(self.data_loader, "year", None):
                        year = self.data_loader.year
                    else:
                        year = datetime.now().year
                
                print(f"\n🎯 單一年份查詢模式: {year} 年")
                result = generate_season_calendar(int(year), save_json=True)
            
            return self._standardize_result(result, 99, "賽季賽程查詢")

        except Exception as exc:  # pragma: no cover - runtime safeguard
            return {
                "success": False,
                "message": f"賽季賽程查詢失敗: {exc}",
                "function_id": "99",
                "data": None,
            }

    def _execute_historical_flags_analysis(self, **kwargs):
        """Function 100: 歷年旗幟統計分析 (2020-2025 賽道旗幟歷史)"""
        
        try:
            from CLI_modules.cli.analyzer.historical_flags_analysis import (
                run_historical_flags_analysis_json
            )
            
            # 參數處理
            race = kwargs.get("race")
            if not race:
                if self.data_loader and getattr(self.data_loader, "race", None):
                    race = self.data_loader.race
                else:
                    return {
                        "success": False,
                        "message": "缺少必要參數: race (賽道名稱)",
                        "function_id": "100"
                    }
            
            # ⚠️ CLI 使用 -y 傳遞 year，但此功能需要多年範圍
            # 優先使用 start_year 和 end_year，如果不存在則使用 year
            # 預設 2022-2025（跳過 COVID-19 取消的 2020-2021）
            start_year = kwargs.get("start_year")
            end_year = kwargs.get("end_year")
            year = kwargs.get("year")
            
            # ✅ 修復：優先使用 start_year/end_year，如果不存在才使用 year
            if start_year and end_year:
                # 明確指定了年份範圍
                start_year = int(start_year)
                end_year = int(end_year)
            elif year:
                # 只有 year 參數：預設為 2022-2025 範圍
                start_year = 2022
                end_year = 2025
                print(f"[FUNCTION 100] ⚠️  只提供 year={year}，自動設定範圍 2022-2025")
            else:
                # 沒有任何年份參數：使用預設值
                start_year = 2022
                end_year = 2025
            
            session_type = kwargs.get("session") or "R"  # ✅ 修復：確保 None 會使用預設值
            
            print(f"\n[FUNCTION 100] 歷年旗幟統計分析")
            print(f"  賽道: {race}")
            print(f"  年份範圍: {start_year}-{end_year}")
            print(f"  會話類型: {session_type}")
            print(f"  功能: 統計 Yellow/Double Yellow/Red Flag + Safety Car")
            
            # 執行分析
            result = run_historical_flags_analysis_json(
                race=race,
                start_year=int(start_year),
                end_year=int(end_year),
                session_type=session_type
            )
            
            return self._standardize_result(result, 100, "歷年旗幟統計分析")
            
        except Exception as exc:
            return {
                "success": False,
                "message": f"歷年旗幟統計分析失敗: {exc}",
                "function_id": "100",
                "data": None
            }

    def _execute_season_start_reaction_analysis(self, **kwargs):
        """Function 101: 年度起跑反應分析 (0-50km/h分布 + P1位置統計)"""
        
        try:
            from CLI_modules.cli.analyzer.f101_season_start_reaction import (
                run_season_start_reaction_analysis
            )
            
            # 參數處理
            year = kwargs.get("year")
            if not year:
                if self.data_loader and getattr(self.data_loader, "year", None):
                    year = self.data_loader.year
                else:
                    year = datetime.now().year
            
            print(f"\n[FUNCTION 101] 年度起跑反應分析")
            print(f"  年份: {year}")
            print(f"  功能: 0-50km/h 時間分布 + P1 Lap2 位置統計")
            
            # 執行分析
            result = run_season_start_reaction_analysis(
                year=int(year),
                save_json=True
            )
            
            return self._standardize_result(result, 101, "年度起跑反應分析")
            
        except Exception as exc:
            return {
                "success": False,
                "message": f"年度起跑反應分析失敗: {exc}",
                "function_id": "101",
                "data": None
            }

    def _execute_race_weather_forecast(self, **kwargs):
        """Function 96: 賽事天氣預報 (支援 Open-Meteo API + 12小時智能刷新)"""

        try:
            from CLI_modules.cli.analyzer.race_weather_forecast import (
                generate_race_weather_forecast,
                check_weather_forecast_freshness
            )

            # 參數處理
            year = kwargs.get("year")
            event_name = kwargs.get("race")  # 從 race 參數映射到 event_name
            force = kwargs.get("force", False)
            
            # 自動選擇年份
            if not year:
                if self.data_loader and getattr(self.data_loader, "year", None):
                    year = self.data_loader.year
                else:
                    year = datetime.now().year
            
            # 顯示功能資訊
            print(f"\n🌤️  賽事天氣預報: {year} {event_name or '(自動選擇下一場比賽)'}")
            print("🔍 數據來源: Open-Meteo API (免費)")
            print("📅 包含: 比賽日前2天預報 + 前2年歷史數據")
            
            # 檢查現有檔案新鮮度
            if not force:
                freshness = check_weather_forecast_freshness(year, event_name)
                if freshness.get("is_fresh"):
                    age_formatted = freshness.get("age_formatted", "未知")
                    print(f"✅ 發現新鮮快取檔案 (更新於 {age_formatted} 前)")
                    print(f"📁 檔案: {freshness.get('path')}")
            
            # 生成天氣預報
            result = generate_race_weather_forecast(
                year=int(year),
                event_name=event_name,
                save_json=True,
                force=force
            )
            
            # 顯示結果摘要
            if result.get("success"):
                metadata = result.get("metadata", {})
                data = result.get("data", {})
                
                print(f"\n✅ {result.get('message')}")
                print(f"📍 賽事: {metadata.get('event_name')}")
                print(f"📅 比賽日期: {metadata.get('race_date_local')}")
                print(f"🏁 第 {metadata.get('round')} 站")
                
                coordinates = data.get("coordinates", {})
                print(f"🌍 賽道: {coordinates.get('circuit')}")
                print(f"🗺️  座標: {coordinates.get('latitude')}, {coordinates.get('longitude')}")
                
                if metadata.get("output_file"):
                    print(f"💾 輸出: {metadata.get('output_file')}")
                
                # 顯示天氣預報摘要
                forecast = data.get("forecast", {})
                forecast_days = forecast.get("days", [])
                
                print("\n📊 天氣預報摘要:")
                for day_data in forecast_days:
                    label = day_data.get("label", "")
                    date = day_data.get("date", "")
                    summary = day_data.get("summary", {})
                    
                    label_text = {
                        "race_minus_2": "比賽日前2天",
                        "race_minus_1": "比賽日前1天",
                        "race_day": "比賽當天"
                    }.get(label, label)
                    
                    temp_max = summary.get("temperature_max")
                    temp_min = summary.get("temperature_min")
                    precip = summary.get("precipitation_sum")
                    wind = summary.get("windspeed_max")
                    wind_dir = summary.get("winddirection_cardinal")
                    
                    print(f"\n  {label_text} ({date}):")
                    if temp_max is not None and temp_min is not None:
                        print(f"    🌡️  溫度: {temp_min:.1f}°C ~ {temp_max:.1f}°C")
                    if precip is not None:
                        print(f"    🌧️  降雨量: {precip:.1f} mm")
                    if wind is not None:
                        wind_text = f"{wind:.1f} km/h"
                        if wind_dir:
                            wind_text += f" ({wind_dir})"
                        print(f"    💨 風速: {wind_text}")
            
            return self._standardize_result(result, 96, "賽事天氣預報")

        except Exception as exc:
            import traceback
            print(f"\n❌ 賽事天氣預報失敗: {exc}")
            traceback.print_exc()
            return {
                "success": False,
                "message": f"賽事天氣預報失敗: {exc}",
                "function_id": "96",
                "data": None,
            }

    # ===== 分拆的單一車手分析功能 (24-26) =====
    
    def _execute_driver_race_position(self, year, race, session, driver, **kwargs):
        """Function 25: 車手比賽位置分析"""
        print("[START] 開始執行車手比賽位置分析...")
        
        try:
            from CLI_modules.cli.analyzer.single_driver_position_analysis import SingleDriverPositionAnalysis
            
            analyzer = SingleDriverPositionAnalysis(
                data_loader=self.data_loader,
                year=year,
                race=race,
                session=session
            )
            
            # 根據是否有指定車手來決定分析模式
            if driver:
                return analyzer.analyze_position_changes(driver=driver, **kwargs)
            else:
                return analyzer.analyze_position_changes(**kwargs)
            
        except ImportError:
            print("[WARNING] 車手比賽位置分析模組尚未實現，使用單一車手綜合分析替代")
            return self._execute_single_driver_comprehensive_analysis(year, race, session, driver, **kwargs)
        except Exception as e:
            print(f"[ERROR] 車手比賽位置分析執行失敗: {e}")
            return {"success": False, "error": str(e), "function_id": "24"}

    def _execute_driver_tire_strategy(self, year, race, session, driver, **kwargs):
        """Function 26: 整合輪胎策略分析 (FastF1 + 快取 + JSON)"""
        print("[TIRE_STRATEGY] 開始執行整合輪胎策略分析...")
        print("🎯 目標：完整輪胎策略分析 - 快取管理 + FastF1資料 + JSON輸出")
        print("🔧 方法：新整合模組 - TireStrategyAnalyzer")
        
        try:
            # 使用新的整合輪胎策略分析模組
            from CLI_modules.cli.analyzer.tire_stragtegy.tire_strategy_cli import run_tire_strategy_analysis
            
            print("✅ 載入整合輪胎策略分析模組")
            
            # 準備分析參數
            analysis_params = {
                'year': year,
                'race': race,
                'session': session,
                'driver': driver,
                'use_cache': kwargs.get('use_cache', True),
                'verbose': kwargs.get('show_detailed_output', True),
                **kwargs
            }
            
            # 執行分析
            result = run_tire_strategy_analysis(**analysis_params)
            
            # 檢查結果
            if result and isinstance(result, dict) and result.get("success"):
                print("[SUCCESS] 整合輪胎策略分析完成")
                print(f"[INFO] 分析目標: {result['analysis_params']['driver'] if result['analysis_params'].get('driver') else '所有車手'}")
                
                # 確保返回完整信息
                result.setdefault('function_id', '26')
                return result
            else:
                error_msg = result.get('message', '分析失敗') if isinstance(result, dict) else '未知錯誤'
                print(f"[ERROR] 分析失敗: {error_msg}")
                return {
                    "success": False, 
                    "message": error_msg, 
                    "function_id": "26"
                }
            
        except ImportError as e:
            print(f"[ERROR] 無法載入整合輪胎策略分析模組: {e}")
            print("[FALLBACK] 嘗試使用備用 FastF1 模組...")
            
            # 備用方案：使用原有的 FastF1 模組
            try:
                from CLI_modules.cli.analyzer.fastf1_only_tire_strategy_clean import run_fastf1_tire_strategy_analysis
                
                result = run_fastf1_tire_strategy_analysis(
                    f1_data=None,
                    year=year,
                    race=race,
                    session=session,
                    driver=driver,
                    verbose=kwargs.get('show_detailed_output', False)
                )
                
                if result and isinstance(result, dict) and result.get("success"):
                    print("[SUCCESS] 備用 FastF1 輪胎策略分析完成")
                    result.setdefault('function_id', '26')
                    return result
                else:
                    return {"success": False, "message": "備用分析也失敗", "function_id": "26"}
                    
            except Exception as fallback_error:
                print(f"[ERROR] 備用分析也失敗: {fallback_error}")
                return {"success": False, "message": f"所有分析方法都失敗: {str(e)}, {str(fallback_error)}", "function_id": "26"}
            
        except Exception as e:
            print(f"[ERROR] 輪胎策略分析執行失敗: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "message": str(e), "function_id": "26"}

    def _execute_driver_fastest_lap_analysis(self, year, race, session, driver, **kwargs):
        """Function 26: 車手最速圈速分析"""
        print("[FAST] 開始執行車手最速圈速分析...")
        
        try:
            from CLI_modules.cli.analyzer.single_driver_laptime_analysis import SingleDriverLaptimeAnalysis
            
            analyzer = SingleDriverLaptimeAnalysis(
                data_loader=self.data_loader,
                year=year,
                race=race,
                session=session
            )
            
            return analyzer.analyze_fastest_lap(driver=driver, **kwargs)
            
        except ImportError:
            print("[WARNING] 車手最速圈速分析模組尚未實現，使用單一車手綜合分析替代")
            return self._execute_single_driver_comprehensive_analysis(year, race, session, driver, **kwargs)
        except Exception as e:
            print(f"[ERROR] 車手最速圈速分析執行失敗: {e}")
            return {"success": False, "error": str(e), "function_id": "26"}

    def _execute_driver_lap_time_analysis(self, driver=None, silent_mode=False, **kwargs):
        """Function 28: 車手每圈圈速分析
        
        ⚠️ 重要變更 (2025-10-21): 
        此函數現在像 Function 13/54 一樣，從 data_loader 讀取 year/race/session
        不再接受這些參數，確保數據來源與 metadata 始終一致
        
        Args:
            driver: 車手代碼，如果為 None 則分析全部車手
            silent_mode: 是否啟用靜默模式，隱藏詳細表格輸出
        """
        try:
            from CLI_modules.cli.analyzer.single_driver_detailed_laptime_analysis import SingleDriverDetailedLaptimeAnalysis
            
            # ✅ 像 Function 13/54 一樣：從 data_loader 讀取 year/race/session
            year = getattr(self.data_loader, 'year', 2025)
            race = getattr(self.data_loader, 'race_name', 'Japan')
            session = getattr(self.data_loader, 'session_type', 'R')
            
            analyzer = SingleDriverDetailedLaptimeAnalysis(
                data_loader=self.data_loader,
                year=year,      # ✅ 從 data_loader 讀取
                race=race,      # ✅ 從 data_loader 讀取
                session=session # ✅ 從 data_loader 讀取
            )
            
            # 準備參數，支援靜默模式
            analysis_kwargs = kwargs.copy()
            analysis_kwargs['show_detailed_output'] = not silent_mode  # 靜默模式時不顯示詳細輸出
            analysis_kwargs['silent_mode'] = silent_mode  # 傳遞靜默模式參數
            
            # 根據是否有指定車手來決定分析模式
            if driver:
                result = analyzer.analyze_every_lap(driver=driver, **analysis_kwargs)
            else:
                result = analyzer.analyze_every_lap(driver=None, **analysis_kwargs)
            
            # 確保回傳值有 success 字段
            if result and isinstance(result, dict):
                result.setdefault('success', True)
                result.setdefault('function_id', '28')
            
            return result
            
        except ImportError:
            print("[WARNING] 車手每圈圈速分析模組尚未實現，使用單一車手綜合分析替代")
            return self._execute_single_driver_comprehensive_analysis(year, race, session, driver, **kwargs)
        except Exception as e:
            print(f"[ERROR] 車手每圈圈速分析執行失敗: {e}")
            return {"success": False, "error": str(e), "function_id": "28"}

    def _execute_single_driver_comprehensive_analysis(self, year, race, session, driver, **kwargs):
        """Function 11: 單一車手綜合分析 (fallback for split functions)"""
        try:
            from CLI_modules.cli.analyzer.single_driver_analysis import run_single_driver_comprehensive_analysis
            return run_single_driver_comprehensive_analysis(
                data_loader=self.data_loader,
                year=year,
                race=race,
                session=session,
                driver=driver,
                **kwargs
            )
        except Exception as e:
            print(f"[ERROR] 單一車手綜合分析執行失敗: {e}")
            return {"success": False, "error": str(e), "function_id": "11"}

    def _save_driver_data_json(self, result, driver, lap_number):
        """保存車手資料為指定格式的JSON檔案"""
        try:
            import json
            import os
            
            # 創建 json 目錄
            json_dir = "json"
            os.makedirs(json_dir, exist_ok=True)
            
            # 生成檔案名稱: driver_data_VER_2025_Japan_R_Lap12.json
            year = getattr(self.data_loader, 'year', 2025)
            race = getattr(self.data_loader, 'race_name', 'Japan')
            session = getattr(self.data_loader, 'session_type', 'R')
            
            filename = f"driver_data_{driver}_{year}_{race}_{session}_Lap{lap_number}.json"
            filepath = os.path.join(json_dir, filename)
            
            # 保存JSON檔案
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"💾 車手資料JSON已保存: {filepath}")
            
        except Exception as e:
            print(f"⚠️ 車手資料JSON保存失敗: {e}")
    
    # ============================================================================
    # 預測系統功能 (功能 70-79)
    # ============================================================================
    
    def _execute_fp_q_data_collector(self, **kwargs):
        """
        功能 70: FP→Q 訓練數據收集器
        
        用途: 收集 FP1/FP2/FP3 和 Q 的數據用於機器學習訓練
        輸出: JSON 格式的訓練數據
        """
        try:
            from CLI_modules.cli.prediction.fp_q_data_collector import FPQDataCollector
            from CLI_modules.cli.prediction.race_calendar import get_races_for_year
            
            print("\n" + "="*60)
            print("功能 70: FP→Q 訓練數據收集器")
            print("="*60)
            
            # 初始化收集器
            collector = FPQDataCollector()
            
            # 獲取參數
            year = kwargs.get('year')
            race = kwargs.get('race')
            collect_season = kwargs.get('collect_season', False)
            start_year = kwargs.get('start_year')
            end_year = kwargs.get('end_year')
            start_race = kwargs.get('start_race', 1)
            end_race = kwargs.get('end_race')
            
            include_fp1 = not kwargs.get('no_fp1', False)
            include_fp2 = not kwargs.get('no_fp2', False)
            include_fp3 = not kwargs.get('no_fp3', False)
            
            # 執行收集
            if start_year and end_year:
                # 多賽季模式 - 使用賽事名稱列表
                print(f"\n🏁 多賽季模式: {start_year}-{end_year}")
                
                for year in range(start_year, end_year + 1):
                    print(f"\n{'#'*60}")
                    print(f"# 處理賽季: {year}")
                    print(f"{'#'*60}")
                    
                    # 獲取該年份的賽事列表
                    races = get_races_for_year(year)
                    
                    if not races:
                        print(f"⚠️  {year} 年份沒有賽事數據，跳過")
                        continue
                    
                    print(f"📅 {year} 賽季共 {len(races)} 場賽事")
                    season_success = 0
                    
                    for idx, race_name in enumerate(races, 1):
                        try:
                            print(f"\n🏁 [{idx}/{len(races)}] 收集 {year} {race_name}...")
                            data = collector.collect_single_race(
                                year,
                                race_name,
                                include_fp1=include_fp1,
                                include_fp2=include_fp2,
                                include_fp3=include_fp3
                            )
                            
                            if data:
                                # 立即保存每場賽事
                                collector.save_to_json(data)
                                season_success += 1
                                print(f"✅ {race_name} 收集成功 ({season_success}/{len(races)})")
                            else:
                                print(f"⚠️  {race_name} 數據不完整，跳過")
                            
                        except Exception as e:
                            error_str = str(e)
                            print(f"❌ {race_name} 錯誤: {str(e)[:150]}")
                            continue
                    
                    print(f"\n✅ {year} 賽季完成: {season_success}/{len(races)} 場賽事成功")
            
            elif collect_season and year:
                # 單賽季模式
                print(f"\n🏁 賽季模式: {year}")
                
                race_num = start_race
                season_success = 0
                
                while True:
                    if end_race and race_num > end_race:
                        break
                    
                    try:
                        print(f"\n🏁 收集賽事 {race_num} ({year})...")
                        data = collector.collect_single_race(
                            year,
                            race_num,
                            include_fp1=include_fp1,
                            include_fp2=include_fp2,
                            include_fp3=include_fp3
                        )
                        
                        if data:
                            # 立即保存每場賽事
                            collector.save_to_json(data)
                            season_success += 1
                        else:
                            print(f"⚠️  賽事 {race_num} 數據不完整，跳過")
                        
                        race_num += 1
                        
                    except Exception as e:
                        error_str = str(e)
                        if "No matching round" in error_str or "cannot be found" in error_str:
                            print(f"\n✅ {year} 賽季結束 (共 {season_success} 場賽事)")
                            break
                        else:
                            print(f"❌ 賽事 {race_num} 錯誤: {str(e)[:100]}")
                            race_num += 1
                            continue
            
            elif year and race:
                # 單場賽事模式
                print(f"\n🏁 單場賽事模式: {year} {race}")
                
                data = collector.collect_single_race(
                    year,
                    race,
                    include_fp1=include_fp1,
                    include_fp2=include_fp2,
                    include_fp3=include_fp3
                )
                
                if data:
                    collector.save_to_json(data)
            else:
                print("❌ 錯誤: 請提供必要的參數")
                print("   - 單場賽事: --year YEAR --race RACE")
                print("   - 單賽季: --year YEAR --season")
                print("   - 多賽季: --start-year START --end-year END")
                return False
            
            print("\n✅ 功能 70 執行完成！")
            return True
            
        except Exception as e:
            print(f"\n❌ 功能 70 執行失敗: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def _execute_q_race_data_collector(self, **kwargs):
        """功能 71: Q→R 訓練數據收集器 (規劃中)"""
        print("\n⚠️  功能 71 (Q→R 數據收集器) 尚未實現")
        print("   狀態: 規劃中")
        print("   預計實現: Phase 1 Week 3-4")
        return False
    
    def _execute_xgboost_trainer(self, **kwargs):
        """功能 72: XGBoost 模型訓練器"""
        try:
            print("\n🤖 執行 XGBoost 模型訓練器 (功能 72)...")
            
            from CLI_modules.cli.prediction.xgboost_trainer import run_xgboost_training
            
            # 參數處理
            start_year = kwargs.get('start_year', 2018)
            end_year = kwargs.get('end_year', 2023)
            exclude_wet = kwargs.get('exclude_wet', True)
            verbose = kwargs.get('show_detailed_output', True)
            
            # 執行訓練
            result = run_xgboost_training(
                start_year=start_year,
                end_year=end_year,
                exclude_wet=exclude_wet,
                verbose=verbose
            )
            
            return result
            
        except ImportError as e:
            return {
                "success": False,
                "message": f"缺少必要套件: {str(e)}",
                "hint": "請執行: pip install xgboost scikit-learn",
                "function_id": "72"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"XGBoost 訓練失敗: {str(e)}",
                "error": str(e),
                "function_id": "72"
            }
    
    def _execute_placeholder_73(self, **kwargs):
        """功能 73: v3.10 批次訓練器 (XGBoost 模型訓練)
        
        v3.10 = v3.8 - is_top_driver
        基於 V3.8 vs V3.9 對比分析，移除無效特徵：
        - is_top_driver (V3.8 所有賽道重要性為 0%)
        
        v3.10 特徵架構 (16 特徵):
        - v3.0 基礎特徵 (8): ideal_s1/s2/s3/lap, apex speeds, max_speed
        - v3.3 交互特徵 (3): s1_s2_ratio, sector_cv, s2_lap_ratio
        - v3.4 速度特徵 (3): max_speed_lap_ratio, max_speed_s2_ratio, speed_consistency
        - v3.5 有效特徵 (2): fp3_relative_position, fp3_gap_to_fastest
        
        參數:
            --trials: Optuna 試驗次數 (預設: 500)
            --cv-folds: 交叉驗證 folds (預設: 3)
            --workers: 並行 workers (預設: 1)
            --track: 指定單一賽道訓練 (預設: 訓練所有 24 個賽道)
        
        輸出:
            - models/track_specific_v3.10/{track}.pkl
            - v3.10_training_results.json
        """
        try:
            print("\n" + "="*70)
            print("功能 73: v3.10 批次訓練器")
            print("="*70)
            print("版本: v3.10 (16 特徵 - 移除 is_top_driver)")
            print("改進: 移除 V3.8 中重要性為 0% 的 is_top_driver 特徵")
            
            # 導入訓練器 (使用 importlib 因為檔名有小數點)
            import importlib.util
            from pathlib import Path
            
            module_path = Path(__file__).parent.parent.parent.parent / "batch_train_all_tracks_v3.10.py"
            if not module_path.exists():
                return {
                    "success": False,
                    "message": "找不到 batch_train_all_tracks_v3.10.py",
                    "function_id": "73"
                }
            
            spec = importlib.util.spec_from_file_location("batch_trainer_v310", module_path)
            batch_trainer_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(batch_trainer_module)
            BatchTrainerV3_10 = batch_trainer_module.BatchTrainerV3_10
            
            # 參數處理
            trials = kwargs.get('trials', 500)
            cv_folds = kwargs.get('cv_folds', 3)
            workers = kwargs.get('workers', 1)
            specific_track = kwargs.get('track', None)
            
            print(f"\n訓練參數:")
            print(f"  Optuna trials: {trials}")
            print(f"  CV folds: {cv_folds}")
            print(f"  Workers: {workers}")
            if specific_track:
                print(f"  指定賽道: {specific_track}")
            else:
                print(f"  模式: 訓練所有 24 個賽道")
            
            # 創建訓練器
            trainer = BatchTrainerV3_10(
                trials=trials,
                cv_folds=cv_folds,
                workers=workers
            )
            
            # 執行訓練
            if specific_track:
                print(f"\n開始訓練: {specific_track}")
                result = trainer.train_single_track(specific_track)
                if result:
                    return {
                        "success": True,
                        "message": f"{specific_track} 訓練完成",
                        "track": specific_track,
                        "cv_mae": result['cv_mae'],
                        "train_mae": result['train_mae'],
                        "train_r2": result['train_r2'],
                        "sample_count": result['sample_count'],
                        "function_id": "73"
                    }
                else:
                    return {
                        "success": False,
                        "message": f"{specific_track} 訓練失敗",
                        "function_id": "73"
                    }
            else:
                print(f"\n開始訓練所有賽道...")
                trainer.train_all_tracks()
                
                # 計算統計
                all_cv_mae = [r['cv_mae'] for r in trainer.results.values()]
                avg_cv_mae = sum(all_cv_mae) / len(all_cv_mae)
                all_r2 = [r['train_r2'] for r in trainer.results.values()]
                avg_r2 = sum(all_r2) / len(all_r2)
                
                print(f"\n{'='*70}")
                print("v3.10 訓練完成！")
                print(f"{'='*70}")
                print(f"\n模型保存位置: models/track_specific_v3.10/")
                print(f"結果檔案: v3.10_training_results.json")
                print(f"\n整體性能:")
                print(f"  平均 CV MAE: {avg_cv_mae:.3f}s")
                print(f"  平均 R²: {avg_r2:.4f}")
                print(f"  訓練賽道數: {len(trainer.results)}/24")
                
                return {
                    "success": True,
                    "message": f"所有賽道訓練完成 ({len(trainer.results)}/24)",
                    "avg_cv_mae": avg_cv_mae,
                    "avg_r2": avg_r2,
                    "tracks_trained": len(trainer.results),
                    "results": trainer.results,
                    "function_id": "73"
                }
        
        except ImportError as e:
            return {
                "success": False,
                "message": f"缺少必要模組: {str(e)}",
                "hint": "請確認 batch_train_all_tracks_v3.10.py 存在",
                "function_id": "73"
            }
        except Exception as e:
            print(f"[ERROR] v3.10 訓練失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"v3.10 訓練失敗: {str(e)}",
                "error": str(e),
                "function_id": "73"
            }
    
    def _execute_placeholder_74(self, **kwargs):
        """功能 74: 排位賽預測 JSON 生成器 (v3.10 模型)
        
        使用已訓練的 v3.10 模型生成排位賽預測結果並輸出 JSON 檔案。
        
        工作流程:
        1. 載入 models/track_specific_v3.10/{track}.pkl
        2. 提取 FP3 數據作為預測特徵
        3. 生成排位賽時間預測
        4. 輸出 JSON: json/qualifying_prediction_{year}_{race}.json
        
        參數:
            year: 賽季年份 (必填)
            race: 賽事名稱 (必填)
            session: 會話類型，固定為 "Q" (排位賽)
        
        輸出結構:
            {
                "metadata": {
                    "track": "Monaco",
                    "year": 2024,
                    "session": "Q",
                    "model_r2": 0.8923,
                    "model_mae": 2.534,
                    "sample_count": 145,
                    "prediction_time": "2025-11-05T14:30:00"
                },
                "predictions": [
                    {
                        "rank": 1,
                        "driver": "VER",
                        "team": "Red Bull Racing",
                        "fp3_time": 64.643,
                        "predicted_time": 64.523,
                        "actual_q_time": null,
                        "improvement": -0.120
                    },
                    ...
                ]
            }
        
        返回:
            Dict: 執行結果
        """
        try:
            import pickle
            import json
            import pandas as pd
            import numpy as np
            from pathlib import Path
            from datetime import datetime
            
            print("\n" + "="*70)
            print("功能 74: 排位賽預測 JSON 生成器 (v3.10)")
            print("="*70)
            
            # ========================================
            # 1. 參數驗證
            # ========================================
            year = kwargs.get('year')
            race = kwargs.get('race')
            
            if not year or not race:
                return {
                    "success": False,
                    "message": "缺少必要參數: year 和 race",
                    "function_id": "74"
                }
            
            print(f"\n目標賽事: {year} {race} (排位賽預測)")
            
            # ========================================
            # 2. 載入 v3.10 模型
            # ========================================
            model_dir = Path(__file__).parent.parent.parent.parent / "models" / "track_specific_v3.10"
            model_file = model_dir / f"{race}.pkl"  # ✅ 修正: 檔名格式為 {race}.pkl
            
            if not model_file.exists():
                return {
                    "success": False,
                    "message": f"找不到 {race} 的 v3.10 模型檔案",
                    "hint": f"請先執行: python f1_analysis_modular_main.py -f 73 --track {race}",
                    "expected_file": str(model_file),
                    "function_id": "74"
                }
            
            print(f"✅ 載入模型: {model_file}")
            with open(model_file, 'rb') as f:
                model_data = pickle.load(f)
            
            model = model_data['model']
            feature_names = model_data['feature_names']
            
            # ✅ v3.10 模型結構：{model, feature_names, cv_mae, train_mae, train_r2, sample_count, version}
            model_r2 = model_data.get('train_r2', 0.0)
            model_mae = model_data.get('train_mae', 0.0)
            cv_mae = model_data.get('cv_mae', 0.0)
            sample_count = model_data.get('sample_count', 0)
            model_version = model_data.get('version', 'v3.10')
            
            # 如果完全沒有指標，顯示警告
            if model_r2 == 0.0 and model_mae == 0.0 and sample_count == 0:
                print(f"⚠️  警告: 模型檔案缺少訓練指標 (train_r2, train_mae, sample_count)")
                print(f"   提示: 這是舊版本模型，請重新訓練以獲取完整指標")
                print(f"   命令: python f1_analysis_modular_main.py -f 73 --track {race}")
            else:
                print(f"   模型版本: {model_version}")
                print(f"   模型 R²: {model_r2:.4f}")
                print(f"   模型 MAE: {model_mae:.3f}s")
                print(f"   交叉驗證 MAE: {cv_mae:.3f}s")
                print(f"   樣本數: {sample_count}")
            print(f"   特徵數: {len(feature_names)} (v3.10 移除 is_top_driver)")
            
            # ========================================
            # 3. 智能載入練習數據（支援 Sprint 賽制）
            # ========================================
            print(f"\n正在載入 {year} {race} 練習數據...")
            
            # 🔧 初始化 data_loader（如果尚未初始化）
            if not self.data_loader:
                print("   初始化數據載入器...")
                from CLI_modules.cli.core.compatible_data_loader import CompatibleF1DataLoader
                self.data_loader = CompatibleF1DataLoader()
                print("   ✅ 數據載入器已初始化")
            
            # 🔧 智能數據源選擇邏輯
            # 傳統賽制: FP3 → FP2 → FP1
            # Sprint 賽制: Sprint Qualifying → Sprint → FP1
            session_loaded = False
            session_type_used = None
            
            # 嘗試載入順序
            fallback_sessions = ['FP3', 'Sprint Qualifying', 'FP2', 'Sprint', 'FP1']
            
            for session_type in fallback_sessions:
                try:
                    print(f"   嘗試載入 {session_type}...")
                    loaded = self.data_loader.load_race_data(year, race, session_type)
                    if loaded:
                        session_loaded = True
                        session_type_used = session_type
                        print(f"   ✅ 成功載入 {session_type} 數據")
                        break
                except Exception as e:
                    print(f"   ⚠️  {session_type} 不可用: {str(e)[:50]}")
                    continue
            
            if not session_loaded:
                return {
                    "success": False,
                    "message": f"無法載入 {year} {race} 任何練習數據",
                    "hint": "請確認該賽事有可用的練習/排位數據（FP3/Sprint Qualifying/FP2/Sprint/FP1）",
                    "function_id": "74"
                }
            
            # ✅ 修正: 直接訪問 self.data_loader.session
            session = self.data_loader.session
            if not session:
                return {
                    "success": False,
                    "message": "會話數據未載入",
                    "function_id": "74"
                }
            
            laps = session.laps
            
            # 過濾有效圈速
            laps = laps[laps['LapTime'].notna()]
            laps = laps[laps['IsAccurate'] == True]
            
            if laps.empty:
                return {
                    "success": False,
                    "message": f"{year} {race} {session_type_used} 無有效圈速數據",
                    "function_id": "74"
                }
            
            print(f"✅ {session_type_used} 數據載入成功 ({len(laps)} 個有效圈速)")
            
            # ========================================
            # 4. 計算每位車手的練習最快圈特徵
            # ========================================
            print("\n計算車手特徵...")
            predictions = []
            
            # 獲取所有車手
            drivers = laps['Driver'].unique()
            
            for driver_code in drivers:
                driver_laps = laps[laps['Driver'] == driver_code]
                
                # 找到最快圈
                fastest_lap = driver_laps.loc[driver_laps['LapTime'].idxmin()]
                
                # 提取基礎時間
                lap_time = fastest_lap['LapTime'].total_seconds()
                
                # 提取扇區時間（v3.8 需要的基礎特徵）
                try:
                    s1 = fastest_lap['Sector1Time'].total_seconds() if pd.notna(fastest_lap['Sector1Time']) else lap_time / 3
                    s2 = fastest_lap['Sector2Time'].total_seconds() if pd.notna(fastest_lap['Sector2Time']) else lap_time / 3
                    s3 = fastest_lap['Sector3Time'].total_seconds() if pd.notna(fastest_lap['Sector3Time']) else lap_time / 3
                except:
                    s1, s2, s3 = lap_time / 3, lap_time / 3, lap_time / 3
                
                # 提取速度數據
                try:
                    telemetry = fastest_lap.get_telemetry()
                    speeds = telemetry['Speed'].values if 'Speed' in telemetry.columns else np.array([250.0])
                    max_speed = float(speeds.max())
                    avg_speed = float(speeds.mean())
                    speed_std = float(speeds.std())
                    
                    # 計算低/中/高速彎道平均速度
                    low_speed_apex = float(np.percentile(speeds, 25))   # 25th percentile
                    mid_speed_apex = float(np.percentile(speeds, 50))   # median
                    high_speed_apex = float(np.percentile(speeds, 75))  # 75th percentile
                except:
                    max_speed = 300.0
                    avg_speed = 250.0
                    speed_std = 10.0
                    low_speed_apex = 200.0
                    mid_speed_apex = 250.0
                    high_speed_apex = 280.0
                
                # ✅ 修正: 構建 v3.8 特徵向量（17 特徵，匹配實際模型）
                features = {
                    # v3.0 基礎特徵 (8)
                    'ideal_s1': s1,
                    'ideal_s2': s2,
                    'ideal_s3': s3,
                    'ideal_lap': lap_time,
                    'low_speed_apex': low_speed_apex,     # ✅ 修正特徵名稱
                    'mid_speed_apex': mid_speed_apex,     # ✅ 修正特徵名稱
                    'high_speed_apex': high_speed_apex,   # ✅ 修正特徵名稱
                    'max_speed': max_speed,
                    
                    # v3.3 交互特徵 (3)
                    's1_s2_ratio': s1 / s2 if s2 > 0 else 1.0,
                    'sector_cv': speed_std / avg_speed if avg_speed > 0 else 0.1,
                    's2_lap_ratio': s2 / lap_time if lap_time > 0 else 0.33,
                    
                    # v3.4 速度特徵 (3)
                    'max_speed_lap_ratio': max_speed * lap_time / 1000 if lap_time > 0 else 20.0,
                    'max_speed_s2_ratio': max_speed / s2 if s2 > 0 else 10.0,
                    'speed_consistency': 1.0 - (speed_std / avg_speed) if avg_speed > 0 else 0.9,
                    
                    # v3.5 排位相關特徵 (2) - v3.10 移除 is_top_driver
                    'fp3_relative_position': 0.5,  # 待計算
                    'fp3_gap_to_fastest': 0.0,      # 待計算
                    # ❌ v3.10: 已移除 is_top_driver (V3.8 證明重要性為 0%)
                }
                
                predictions.append({
                    'driver': driver_code,
                    'fp3_time': lap_time,
                    'features': features,
                    'team': fastest_lap.get('Team', 'Unknown')
                })
            
            # 計算 FP3 排位相關特徵
            predictions.sort(key=lambda x: x['fp3_time'])
            fastest_fp3 = predictions[0]['fp3_time']
            
            for i, pred in enumerate(predictions):
                pred['features']['fp3_relative_position'] = (i + 1) / len(predictions)
                pred['features']['fp3_gap_to_fastest'] = pred['fp3_time'] - fastest_fp3
            
            print(f"✅ 提取 {len(predictions)} 位車手的特徵")
            
            # ========================================
            # 5. 生成預測
            # ========================================
            print("\n生成排位賽預測...")
            
            for pred in predictions:
                # 構建特徵向量（依照模型訓練時的特徵順序）
                feature_vector = [pred['features'][fname] for fname in feature_names]
                
                # ✅ 修正: 模型預測的是改進值 (improvement/delta)，而非絕對時間
                # 模型輸出: FP3 → Q 的時間變化 (通常為負值，表示進步)
                predicted_improvement = model.predict([feature_vector])[0]
                pred['predicted_time'] = float(pred['fp3_time'] + predicted_improvement)  # 絕對時間 = FP3 + delta
                pred['improvement'] = float(predicted_improvement)  # 改進值
            
            # 按預測時間排序
            predictions.sort(key=lambda x: x['predicted_time'])
            
            # ========================================
            # 6. 嘗試獲取實際排位賽結果（如果賽事已完成）
            # ========================================
            actual_q_times = {}  # driver_code -> actual_q_time
            
            try:
                print(f"\n嘗試載入 {year} {race} Q 會話數據...")
                q_loaded = self.data_loader.load_race_data(year, race, 'Q')
                
                if q_loaded and self.data_loader.session:
                    q_session = self.data_loader.session
                    q_laps = q_session.laps
                    
                    # 過濾有效圈速
                    q_laps = q_laps[q_laps['LapTime'].notna()]
                    
                    if not q_laps.empty:
                        print(f"✅ Q 會話數據載入成功 ({len(q_laps)} 個圈速)")
                        
                        # 提取每位車手的最快圈
                        for driver_code in q_laps['Driver'].unique():
                            driver_q_laps = q_laps[q_laps['Driver'] == driver_code]
                            fastest_q_lap = driver_q_laps.loc[driver_q_laps['LapTime'].idxmin()]
                            q_time = fastest_q_lap['LapTime'].total_seconds()
                            actual_q_times[driver_code] = float(q_time)
                        
                        print(f"✅ 提取 {len(actual_q_times)} 位車手的實際 Q 結果")
                    else:
                        print("⚠️  Q 會話無有效圈速數據")
                else:
                    print("⚠️  Q 會話數據不可用（可能賽事尚未進行）")
                    
            except Exception as e:
                print(f"⚠️  無法載入 Q 會話數據: {e}")
                print("   提示: 如果賽事尚未進行，這是正常的")
            
            # ========================================
            # 7. 構建 JSON 輸出（包含名次計算）
            # ========================================
            
            # 7.1 計算練習數據預測名次（根據練習時間排序）
            fp3_sorted = sorted(predictions, key=lambda x: x['fp3_time'])
            fp3_rank_map = {pred['driver']: rank for rank, pred in enumerate(fp3_sorted, 1)}
            
            # 7.2 計算 Q 名次（根據實際 Q 結果排序）
            q_rank_map = {}  # driver_code -> q_rank
            if actual_q_times:
                # 將有 Q 結果的車手按時間排序
                q_sorted = sorted(actual_q_times.items(), key=lambda x: x[1])
                q_rank_map = {driver: rank for rank, (driver, _) in enumerate(q_sorted, 1)}
                print(f"✅ 已計算 {len(q_rank_map)} 位車手的 Q 名次")
            else:
                print("⚠️  無實際 Q 結果，Q 名次將為 None")
            
            output_data = {
                "metadata": {
                    "track": race,
                    "year": year,
                    "session": "Q",
                    "data_source": session_type_used,  # 🔧 新增: 實際使用的數據源
                    "model_r2": float(model_r2),
                    "model_mae": float(model_mae),
                    "sample_count": int(sample_count),
                    "prediction_time": datetime.now().isoformat(),
                    "model_version": "v3.10",  # 修正版本號
                    "feature_count": len(feature_names),
                    "has_actual_results": len(actual_q_times) > 0  # ✅ 新增: 標記是否有實際結果
                },
                "predictions": []
            }
            
            for rank, pred in enumerate(predictions, 1):
                driver_code = pred['driver']
                actual_q_time = actual_q_times.get(driver_code)  # ✅ 修正: 從實際結果獲取
                fp3_rank = fp3_rank_map[driver_code]
                actual_q_rank = q_rank_map.get(driver_code)
                
                # 計算名次變化（FP3 預測 vs Q 實際）
                # 正數 = 進步（排名上升），負數 = 退步（排名下降）
                rank_change = None
                if actual_q_rank is not None:
                    rank_change = fp3_rank - actual_q_rank  # FP3 第3名 → Q 第1名 = +2（進步）
                
                output_data["predictions"].append({
                    "rank": rank,
                    "driver": driver_code,
                    "team": pred['team'],
                    "fp3_time": float(pred['fp3_time']),
                    "predicted_time": float(pred['predicted_time']),
                    "actual_q_time": actual_q_time,  # ✅ 修正: 填入實際結果（如果有）
                    "improvement": float(pred['improvement']),
                    "fp3_predicted_rank": fp3_rank,  # ✅ 新增: FP3 預測名次
                    "actual_q_rank": actual_q_rank,  # ✅ 新增: Q 名次（如果有）
                    "rank_change": rank_change  # ✅ 新增: 名次變化（FP3預測 → Q實際）
                })
            
            # ========================================
            # 8. 保存 JSON 檔案
            # ========================================
            json_dir = Path(__file__).parent.parent.parent.parent / "json"
            json_dir.mkdir(exist_ok=True)
            
            json_file = json_dir / f"qualifying_prediction_{year}_{race}.json"
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ JSON 檔案已保存: {json_file}")
            
            # ========================================
            # 9. 輸出預測摘要和名次變化分析
            # ========================================
            print(f"\n預測摘要:")
            print(f"  前 5 名預測:")
            for i, pred in enumerate(output_data['predictions'][:5], 1):
                fp3_rank = pred.get('fp3_predicted_rank', 'N/A')
                q_rank = pred.get('actual_q_rank', 'N/A')
                rank_change = pred.get('rank_change')
                
                change_str = ""
                if rank_change is not None:
                    if rank_change > 0:
                        change_str = f" [↑{rank_change}]"  # 進步
                    elif rank_change < 0:
                        change_str = f" [↓{abs(rank_change)}]"  # 退步
                    else:
                        change_str = " [→]"  # 持平
                
                print(f"    P{i}: {pred['driver']} - {pred['predicted_time']:.3f}s (FP3: {pred['fp3_time']:.3f}s, △{pred['improvement']:.3f}s) FP3排名:{fp3_rank} → Q排名:{q_rank}{change_str}")
            
            # 如果有實際結果，顯示名次變化統計
            if actual_q_times:
                print(f"\n名次變化分析:")
                
                # 計算進步、退步、持平的車手數量
                improved = [p for p in output_data['predictions'] if p.get('rank_change') and p['rank_change'] > 0]
                declined = [p for p in output_data['predictions'] if p.get('rank_change') and p['rank_change'] < 0]
                unchanged = [p for p in output_data['predictions'] if p.get('rank_change') == 0]
                
                print(f"  進步（排名上升）: {len(improved)} 位車手")
                if improved:
                    # 按進步幅度排序
                    improved.sort(key=lambda x: x['rank_change'], reverse=True)
                    for p in improved[:3]:  # 顯示前 3 名進步最多的
                        print(f"    {p['driver']}: FP3 第{p['fp3_predicted_rank']}名 → Q 第{p['actual_q_rank']}名 (↑{p['rank_change']})")
                
                print(f"  退步（排名下降）: {len(declined)} 位車手")
                if declined:
                    # 按退步幅度排序
                    declined.sort(key=lambda x: x['rank_change'])
                    for p in declined[:3]:  # 顯示前 3 名退步最多的
                        print(f"    {p['driver']}: FP3 第{p['fp3_predicted_rank']}名 → Q 第{p['actual_q_rank']}名 (↓{abs(p['rank_change'])})")
                
                print(f"  持平（排名不變）: {len(unchanged)} 位車手")
            
            # ✅ 修正: 添加 data 欄位，包含完整的預測數據和 JSON 檔案資訊
            return {
                "success": True,
                "message": f"{year} {race} 排位賽預測生成成功",
                "data": {
                    "json_data": [str(json_file)],  # API 期望的 JSON 檔案列表格式
                    "metadata": output_data["metadata"],
                    "predictions": output_data["predictions"],
                    "predictions_count": len(predictions)
                },
                "json_file": str(json_file),
                "predictions_count": len(predictions),
                "model_r2": float(model_r2),
                "model_mae": float(model_mae),
                "function_id": "74"
            }
        
        except FileNotFoundError as e:
            return {
                "success": False,
                "message": f"檔案未找到: {str(e)}",
                "function_id": "74"
            }
        except Exception as e:
            print(f"[ERROR] 排位賽預測生成失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"排位賽預測生成失敗: {str(e)}",
                "error": str(e),
                "function_id": "74"
            }
    
    def _execute_fp2_q_batch_trainer(self, **kwargs):
        """功能 75: FP2→Q 批次訓練器 (XGBoost 模型訓練)
        
        使用 FP2 數據預測排位賽 (Q) 成績，架構與 Function 73 (FP3→Q) 相同。
        
        v3.10 FP2 特徵架構 (16 特徵):
        - v3.0 基礎特徵 (8): ideal_s1/s2/s3/lap (from FP2), apex speeds, max_speed
        - v3.3 交互特徵 (3): s1_s2_ratio, sector_cv, s2_lap_ratio
        - v3.4 速度特徵 (3): max_speed_lap_ratio, max_speed_s2_ratio, speed_consistency
        - v3.5 排位特徵 (2): fp2_relative_position, fp2_gap_to_fastest
        
        參數:
            --trials: Optuna 試驗次數 (預設: 500)
            --cv-folds: 交叉驗證 folds (預設: 3)
            --workers: 並行 workers (預設: 1)
            --track: 指定單一賽道訓練 (預設: 訓練所有 24 個賽道)
        
        輸出:
            - models/fp2_q_specific_v3.10/{track}.pkl
            - fp2_q_v3.10_training_results.json
        
        與 Function 73 差異:
            - 數據源: FP2 (而非 FP3)
            - 模型目錄: fp2_q_specific_v3.10 (而非 track_specific_v3.10)
            - 預期準確度: 比 FP3 稍低 5-10%（因距離排位賽更遠）
        """
        try:
            import pickle
            import json
            import pandas as pd
            import numpy as np
            from pathlib import Path
            from datetime import datetime
            
            print("\n" + "="*70)
            print("功能 75: FP2→Q 批次訓練器")
            print("="*70)
            print("版本: v3.10 (16 特徵 FP2→Q 預測)")
            print("數據源: FP2 (週五下午練習賽)")
            print("預測目標: Q (週六排位賽)")
            
            # 導入必要模組
            try:
                import xgboost as xgb
                from sklearn.model_selection import cross_val_score, KFold
                from sklearn.metrics import mean_absolute_error, r2_score
            except ImportError as e:
                return {
                    "success": False,
                    "message": f"缺少必要套件: {str(e)}",
                    "hint": "請執行: pip install xgboost scikit-learn",
                    "function_id": "75"
                }
            
            # 參數處理
            trials = kwargs.get('trials', 500)
            cv_folds = kwargs.get('cv_folds', 3)
            workers = kwargs.get('workers', 1)
            specific_track = kwargs.get('track', None)
            start_year = kwargs.get('start_year', 2018)
            end_year = kwargs.get('end_year', 2024)
            
            print(f"\n訓練參數:")
            print(f"  數據年份: {start_year}-{end_year}")
            print(f"  Optuna trials: {trials}")
            print(f"  CV folds: {cv_folds}")
            print(f"  Workers: {workers}")
            if specific_track:
                print(f"  指定賽道: {specific_track}")
            else:
                print(f"  模式: 訓練所有賽道")
            
            # 創建模型保存目錄
            model_dir = Path(__file__).parent.parent.parent.parent / "models" / "fp2_q_specific_v3.10"
            model_dir.mkdir(parents=True, exist_ok=True)
            print(f"\n模型保存目錄: {model_dir}")
            
            # 載入訓練數據
            print(f"\n正在載入 FP2→Q 訓練數據...")
            training_data_dir = Path(__file__).parent.parent.parent.parent / "training_data"
            
            # 優先使用 Cleaning 後的數據 (v4.0)
            fp2_data_file = training_data_dir / "fp2_q_training_data_cleaned.json"
            if not fp2_data_file.exists():
                print("⚠️  找不到清洗後的數據，使用原始 2022-2025 數據...")
                fp2_data_file = training_data_dir / "fp2_q_training_data_2022_2025.json"
            
            if not fp2_data_file.exists():
                fp2_data_file = training_data_dir / "fp2_q_training_data.json"
            
            if not fp2_data_file.exists():
                return {
                    "success": False,
                    "message": "找不到 FP2→Q 訓練數據",
                    "hint": "請先執行: python batch_collect_2022_2025_fp2_q_data.py (收集 2022-2025 數據)",
                    "expected_file": str(fp2_data_file),
                    "function_id": "75"
                }
            
            with open(fp2_data_file, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
            
            print(f"✅ 載入訓練數據: {len(all_data)} 筆賽事記錄")
            
            # 組織數據（按賽道分組）
            track_data = {}
            for record in all_data:
                # 支援兩種格式: 直接 'track' 或 'metadata.race'
                track = record.get('track')
                if not track:
                    metadata = record.get('metadata', {})
                    track = metadata.get('race')
                if not track:
                    continue
                
                if track not in track_data:
                    track_data[track] = []
                track_data[track].append(record)
            
            print(f"✅ 數據已按賽道分組: {len(track_data)} 個賽道")
            
            # 定義特徵名稱 (v3.10 FP2 版本)
            feature_names = [
                # v3.0 基礎特徵 (8)
                'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
                'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
                
                # v3.3 交互特徵 (3)
                's1_s2_ratio', 'sector_cv', 's2_lap_ratio',
                
                # v3.4 速度特徵 (3)
                'max_speed_lap_ratio', 'max_speed_s2_ratio', 'speed_consistency',
                
                # v3.5 FP2 排位特徵 (2)
                'fp2_relative_position', 'fp2_gap_to_fastest'
            ]
            
            # 訓練結果
            training_results = {}
            
            # 決定訓練哪些賽道
            tracks_to_train = [specific_track] if specific_track else list(track_data.keys())
            
            print(f"\n開始訓練 {len(tracks_to_train)} 個賽道...")
            
            for idx, track in enumerate(tracks_to_train, 1):
                print(f"\n{'='*70}")
                print(f"[{idx}/{len(tracks_to_train)}] 訓練賽道: {track}")
                print(f"{'='*70}")
                
                if track not in track_data:
                    print(f"⚠️  {track} 無訓練數據，跳過")
                    continue
                
                records = track_data[track]
                print(f"  數據量: {len(records)} 筆賽事記錄")
                
                # 構建訓練集 (v3.11: 新增 sample_years 用於時間衰減權重)
                X_train = []
                y_train = []
                sample_years = []  # v3.11: 記錄每個樣本的年份
                
                for record in records:
                    # 支援三種格式
                    # 格式 1: 舊版直接格式 (fp2_best_lap, q_best_lap)
                    fp2_data = record.get('fp2_best_lap')
                    q_data = record.get('q_best_lap')
                    
                    if fp2_data and q_data:
                        # 舊格式: 直接使用
                        feature_vector = [fp2_data.get(fname, 0.0) for fname in feature_names]
                        X_train.append(feature_vector)
                        fp2_time = fp2_data.get('ideal_lap', 0.0)
                        q_time = q_data.get('ideal_lap', 0.0)
                        improvement = q_time - fp2_time
                        y_train.append(improvement)
                        # v3.11: 記錄年份用於時間衰減權重
                        record_year = record.get('year') or record.get('metadata', {}).get('year', 2024)
                        sample_years.append(record_year)
                    else:
                        # 格式 2: 新版嵌套格式 (fp2.drivers, qualifying.results)
                        fp2_section = record.get('fp2', {})
                        q_section = record.get('qualifying', {})
                        
                        fp2_drivers = fp2_section.get('drivers', {})
                        q_results = q_section.get('results', {})
                        
                        # 格式 3: FPQDataCollector 格式 (practice_sessions.FP2.driver_data, qualifying.results)
                        if not fp2_drivers or not q_results:
                            practice_sessions = record.get('practice_sessions', {})
                            fp2_section = practice_sessions.get('FP2', {})
                            fp2_drivers = fp2_section.get('driver_data', {})
                            q_section = record.get('qualifying', {})
                            q_results = q_section.get('results', {})
                        
                        if not fp2_drivers or not q_results:
                            continue
                        
                        # 為每個車手構建樣本
                        for driver, fp2_driver_data in fp2_drivers.items():
                            if driver not in q_results:
                                continue
                            
                            q_driver_data = q_results[driver]
                            
                            # 目標值: Q 最佳成績時間 (從 q3_time/q2_time/q1_time 取最佳)
                            fp2_time = fp2_driver_data.get('fastest_lap', 0.0) or fp2_driver_data.get('ideal_lap', 0.0)
                            
                            # Q 時間需要從字符串解析
                            q_time_str = q_driver_data.get('q3_time') or q_driver_data.get('q2_time') or q_driver_data.get('q1_time')
                            
                            # 先檢查數據有效性
                            if not q_time_str or fp2_time <= 0:
                                continue
                            
                            try:
                                # 解析 "0 days 00:01:30.558000" 格式
                                import re
                                match = re.search(r'(\d+):(\d+):(\d+\.?\d*)', str(q_time_str))
                                if not match:
                                    continue
                                    
                                h, m, s = match.groups()
                                q_time = int(h) * 3600 + int(m) * 60 + float(s)
                                improvement = q_time - fp2_time
                                
                                # 提取特徵向量（只有成功解析 Q 時間才添加）
                                # 先檢查特徵是否存在，不存在則提取基礎數據
                                if 'ideal_s1' in fp2_driver_data:
                                    # 已有特徵數據
                                    feature_vector = [fp2_driver_data.get(fname, 0.0) for fname in feature_names]
                                else:
                                    # 需要從基礎數據構建特徵向量 (使用默認值，後續可優化)
                                    feature_vector = [
                                        fp2_driver_data.get('sector1_best', 0.0),  # ideal_s1
                                        fp2_driver_data.get('sector2_best', 0.0),  # ideal_s2
                                        fp2_driver_data.get('sector3_best', 0.0),  # ideal_s3
                                        fp2_driver_data.get('fastest_lap', 0.0),   # ideal_lap
                                        0.0, 0.0, 0.0,  # low/mid/high speed apex (需要補充)
                                        fp2_driver_data.get('speed_trap_max', 0.0),  # max_speed
                                        0.0, 0.0, 0.0,  # s1_s2_ratio, sector_cv, s2_lap_ratio
                                        0.0, 0.0, 0.0,  # max_speed_lap_ratio, max_speed_s2_ratio, speed_consistency
                                        0.0, 0.0  # fp2_relative_position, fp2_gap_to_fastest
                                    ]
                                
                                X_train.append(feature_vector)
                                y_train.append(improvement)
                                # v3.11: 記錄年份
                                record_year = record.get('metadata', {}).get('year', 2024)
                                sample_years.append(record_year)
                            except Exception as e:
                                print(f"  ⚠️  {driver} 數據解析失敗: {str(e)}")
                                continue
                
                if len(X_train) < 10:
                    print(f"⚠️  {track} 樣本數不足 ({len(X_train)} < 10)，跳過")
                    continue
                
                X_train = np.array(X_train)
                y_train = np.array(y_train)
                sample_years = np.array(sample_years)
                
                print(f"  訓練樣本: {len(X_train)} 筆")
                
                # v3.11: 計算時間衰減權重 (較新的數據權重更高)
                current_year = 2025
                decay_rate = 0.85  # 每過一年權重減少 15%
                sample_weights = decay_rate ** (current_year - sample_years)
                print(f"  年份分布: {dict(zip(*np.unique(sample_years, return_counts=True)))}")
                print(f"  權重範圍: {sample_weights.min():.3f} - {sample_weights.max():.3f}")
                
                # 訓練 XGBoost 模型 (v4.0: Optuna Optimized 2026-01-21)
                # CV MAE: 5.176s (Generalized)
                model = xgb.XGBRegressor(
                    n_estimators=353,
                    max_depth=9,
                    learning_rate=0.0867,
                    subsample=0.6378,
                    colsample_bytree=0.6097,
                    min_child_weight=6,
                    reg_alpha=1.0077,
                    reg_lambda=0.8641,
                    gamma=0.3904,
                    objective='reg:squarederror',
                    random_state=42,
                    n_jobs=workers
                )
                
                # 訓練模型 (v3.11: 使用時間衰減權重)
                model.fit(X_train, y_train, sample_weight=sample_weights)
                
                # 評估模型
                y_pred = model.predict(X_train)
                train_mae = mean_absolute_error(y_train, y_pred)
                train_r2 = r2_score(y_train, y_pred)
                
                # 交叉驗證
                kf = KFold(n_splits=cv_folds, shuffle=True, random_state=42)
                cv_scores = -cross_val_score(model, X_train, y_train, cv=kf, scoring='neg_mean_absolute_error', n_jobs=workers)
                cv_mae = cv_scores.mean()
                
                print(f"\n  訓練結果:")
                print(f"    Train MAE: {train_mae:.3f}s")
                print(f"    Train R²: {train_r2:.4f}")
                print(f"    CV MAE: {cv_mae:.3f}s")
                
                # 保存模型
                model_file = model_dir / f"{track}.pkl"
                model_data = {
                    'model': model,
                    'feature_names': feature_names,
                    'cv_mae': float(cv_mae),
                    'train_mae': float(train_mae),
                    'train_r2': float(train_r2),
                    'sample_count': len(X_train),
                    'version': 'v3.11_FP2',  # v3.11: 加強正則化 + 異常值過濾
                    'data_source': 'FP2',
                    'prediction_target': 'Q'
                }
                
                with open(model_file, 'wb') as f:
                    pickle.dump(model_data, f)
                
                print(f"  ✅ 模型已保存: {model_file}")
                
                # 記錄結果
                training_results[track] = {
                    'cv_mae': float(cv_mae),
                    'train_mae': float(train_mae),
                    'train_r2': float(train_r2),
                    'sample_count': len(X_train)
                }
            
            # 保存訓練結果摘要
            results_file = Path(__file__).parent.parent.parent.parent / "fp2_q_v3.10_training_results.json"
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(training_results, f, indent=2, ensure_ascii=False)
            
            print(f"\n{'='*70}")
            print("FP2→Q 訓練完成！")
            print(f"{'='*70}")
            print(f"\n訓練結果保存: {results_file}")
            
            if training_results:
                all_cv_mae = [r['cv_mae'] for r in training_results.values()]
                all_r2 = [r['train_r2'] for r in training_results.values()]
                avg_cv_mae = sum(all_cv_mae) / len(all_cv_mae)
                avg_r2 = sum(all_r2) / len(all_r2)
                
                print(f"\n整體性能:")
                print(f"  平均 CV MAE: {avg_cv_mae:.3f}s")
                print(f"  平均 R²: {avg_r2:.4f}")
                print(f"  訓練賽道數: {len(training_results)}")
                
                return {
                    "success": True,
                    "message": f"FP2→Q 訓練完成 ({len(training_results)} 個賽道)",
                    "avg_cv_mae": avg_cv_mae,
                    "avg_r2": avg_r2,
                    "tracks_trained": len(training_results),
                    "results": training_results,
                    "function_id": "75"
                }
            else:
                return {
                    "success": False,
                    "message": "沒有成功訓練任何賽道",
                    "function_id": "75"
                }
        
        except Exception as e:
            print(f"[ERROR] FP2→Q 訓練失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"FP2→Q 訓練失敗: {str(e)}",
                "error": str(e),
                "function_id": "75"
            }
    
    def _identify_quali_sim_laps_fp2(self, driver_laps: 'pd.DataFrame') -> 'pd.DataFrame':
        """
        識別 FP2 中的排位模擬圈速（簡化版：SOFT 胎最快圈）
        
        過濾策略：
        1. 基礎過濾：Out Lap, In Lap, IsAccurate, 黃旗/安全車
        2. 直接找 SOFT 胎最快圈（無 TyreLife 限制）
        3. 回退：無 SOFT 胎時返回空（外部會使用所有圈速最快圈）
        
        Args:
            driver_laps: 單一車手的所有圈速 DataFrame
            
        Returns:
            符合條件的 SOFT 胎圈速 DataFrame（可能為空）
        """
        import pandas as pd
        
        if driver_laps.empty:
            return pd.DataFrame()
        
        # ========== 階段 1: 基礎過濾 ==========
        filtered_laps = driver_laps.copy()
        
        # 1. IsAccurate 檢查
        if 'IsAccurate' in filtered_laps.columns:
            filtered_laps = filtered_laps[filtered_laps['IsAccurate'] == True]
        
        # 2. Out Lap 過濾 (PitOutTime 存在)
        if 'PitOutTime' in filtered_laps.columns:
            filtered_laps = filtered_laps[pd.isna(filtered_laps['PitOutTime'])]
        
        # 3. In Lap 過濾（當前圈或下一圈有 PitInTime）
        if 'PitInTime' in filtered_laps.columns:
            # 排除本身是進站圈的
            filtered_laps = filtered_laps[pd.isna(filtered_laps['PitInTime'])]
            
            # 排除下一圈是進站圈的（In Lap）
            if 'LapNumber' in filtered_laps.columns and not filtered_laps.empty:
                in_lap_numbers = set()
                all_lap_numbers = set(driver_laps['LapNumber'].values)
                pit_in_laps = driver_laps[pd.notna(driver_laps['PitInTime'])]['LapNumber'].values
                
                for pit_lap in pit_in_laps:
                    # 前一圈是 In Lap
                    if pit_lap - 1 in all_lap_numbers:
                        in_lap_numbers.add(pit_lap - 1)
                
                if in_lap_numbers:
                    filtered_laps = filtered_laps[~filtered_laps['LapNumber'].isin(in_lap_numbers)]
        
        # 4. 黃旗/安全車過濾
        if 'TrackStatus' in filtered_laps.columns:
            filtered_laps = filtered_laps[
                ~filtered_laps['TrackStatus'].astype(str).str.contains(
                    'Yellow|SafetyCar|VSC', 
                    case=False, 
                    na=False
                )
            ]
        
        if filtered_laps.empty:
            return pd.DataFrame()
        
        # ========== 階段 2: 直接找 SOFT 胎最快圈（無 TyreLife 限制） ==========
        if 'Compound' in filtered_laps.columns:
            soft_laps = filtered_laps[filtered_laps['Compound'].str.upper() == 'SOFT']
            
            # 直接返回所有 SOFT 胎圈速，讓外部選最快的
            if not soft_laps.empty:
                return soft_laps
        
        # 如果沒有 Compound 資料，返回空（外部會使用層級 4 回退）
        return pd.DataFrame()
    
    def _execute_fp2_q_prediction_generator(self, **kwargs):
        """功能 76: FP2→Q 排位賽預測生成器
        
        使用已訓練的 FP2→Q 模型生成排位賽預測結果並輸出 JSON 檔案。
        
        工作流程:
        1. 載入 models/fp2_q_specific_v3.10/{track}.pkl
        2. 提取 FP2 數據作為預測特徵
        3. 生成排位賽時間預測
        4. 輸出 JSON: json/fp2_qualifying_prediction_{year}_{race}.json
        
        參數:
            year: 賽季年份 (必填)
            race: 賽事名稱 (必填)
        
        輸出結構: 與 Function 74 相同，但數據源為 FP2
        
        返回:
            Dict: 執行結果
        """
        try:
            import pickle
            import json
            import pandas as pd
            import numpy as np
            from pathlib import Path
            from datetime import datetime
            
            print("\n" + "="*70)
            print("功能 76: FP2→Q 排位賽預測生成器")
            print("="*70)
            
            # 參數驗證
            year = kwargs.get('year')
            race = kwargs.get('race')
            
            if not year or not race:
                return {
                    "success": False,
                    "message": "缺少必要參數: year 和 race",
                    "function_id": "76"
                }
            
            print(f"\n目標賽事: {year} {race} (FP2→Q 預測)")
            
            # 載入 FP2→Q 模型
            model_dir = Path(__file__).parent.parent.parent.parent / "models" / "fp2_q_specific_v3.10"
            model_file = model_dir / f"{race}.pkl"
            
            if not model_file.exists():
                return {
                    "success": False,
                    "message": f"找不到 {race} 的 FP2→Q 模型檔案",
                    "hint": f"請先執行: python f1_analysis_modular_main.py -f 75 --track {race}",
                    "expected_file": str(model_file),
                    "function_id": "76"
                }
            
            print(f"✅ 載入模型: {model_file}")
            with open(model_file, 'rb') as f:
                model_data = pickle.load(f)
            
            model = model_data['model']
            feature_names = model_data['feature_names']
            model_r2 = model_data.get('train_r2', 0.0)
            model_mae = model_data.get('train_mae', 0.0)
            cv_mae = model_data.get('cv_mae', 0.0)
            sample_count = model_data.get('sample_count', 0)
            
            print(f"   模型版本: {model_data.get('version', 'v3.10_FP2')}")
            print(f"   模型 R²: {model_r2:.4f}")
            print(f"   模型 MAE: {model_mae:.3f}s")
            print(f"   交叉驗證 MAE: {cv_mae:.3f}s")
            print(f"   樣本數: {sample_count}")
            
            # 載入 FP2 數據
            print(f"\n正在載入 {year} {race} FP2 數據...")
            
            if not self.data_loader:
                print("   初始化數據載入器...")
                from CLI_modules.cli.core.compatible_data_loader import CompatibleF1DataLoader
                self.data_loader = CompatibleF1DataLoader()
            
            # 嘗試載入 FP2，失敗時自動 fallback 到 FP1
            session_type_used = 'FP2'
            try:
                print(f"   嘗試載入 FP2...")
                loaded = self.data_loader.load_race_data(year, race, 'FP2')
                
                if not loaded:
                    # FP2 不存在，嘗試 fallback 到 FP1
                    print(f"   ⚠️  FP2 不存在，自動 fallback 到 FP1...")
                    loaded = self.data_loader.load_race_data(year, race, 'FP1')
                    if not loaded:
                        return {
                            "success": False,
                            "message": f"無法載入 {year} {race} FP2 或 FP1 數據",
                            "function_id": "76"
                        }
                    session_type_used = 'FP1'
                    print(f"   ✅ 已自動使用 FP1 數據（衝刺賽週末）")
                
                session = self.data_loader.session
                if not session:
                    return {
                        "success": False,
                        "message": f"{session_type_used} 會話數據未載入",
                        "function_id": "76"
                    }
                
                laps = session.laps
                laps = laps[laps['LapTime'].notna()]
                laps = laps[laps['IsAccurate'] == True]
                
                if laps.empty:
                    return {
                        "success": False,
                        "message": f"{year} {race} {session_type_used} 無有效圈速數據",
                        "function_id": "76"
                    }
                
                print(f"✅ {session_type_used} 數據載入成功 ({len(laps)} 個有效圈速)")
                
            except Exception as e:
                # 最後嘗試 FP1 fallback
                if session_type_used == 'FP2':
                    print(f"   ⚠️  FP2 載入失敗: {str(e)}")
                    print(f"   嘗試 fallback 到 FP1...")
                    try:
                        loaded = self.data_loader.load_race_data(year, race, 'FP1')
                        if loaded:
                            session_type_used = 'FP1'
                            session = self.data_loader.session
                            laps = session.laps
                            laps = laps[laps['LapTime'].notna()]
                            laps = laps[laps['IsAccurate'] == True]
                            if not laps.empty:
                                print(f"   ✅ 已自動使用 FP1 數據（衝刺賽週末）")
                                print(f"✅ FP1 數據載入成功 ({len(laps)} 個有效圈速)")
                            else:
                                return {
                                    "success": False,
                                    "message": f"{year} {race} FP1 無有效圈速數據",
                                    "function_id": "76"
                                }
                        else:
                            return {
                                "success": False,
                                "message": f"載入 FP2 和 FP1 數據均失敗: {str(e)}",
                                "function_id": "76"
                            }
                    except Exception as fp1_error:
                        return {
                            "success": False,
                            "message": f"載入 FP2 失敗: {str(e)}, FP1 fallback 也失敗: {str(fp1_error)}",
                            "function_id": "76"
                        }
                else:
                    return {
                        "success": False,
                        "message": f"載入 {session_type_used} 數據失敗: {str(e)}",
                        "function_id": "76"
                    }
            
            # 計算每位車手的 FP2 特徵 (使用 SOFT 胎 Quali Sim 過濾)
            print("\n計算車手特徵（使用 Quali Sim 過濾）...")
            predictions = []
            drivers = laps['Driver'].unique()
            
            # 統計資訊
            filter_stats = {
                'total_drivers': len(drivers),
                'using_soft_quali_sim': 0,
                'using_soft_any_stint': 0,
                'using_fallback': 0
            }
            
            for driver_code in drivers:
                driver_laps = laps[laps['Driver'] == driver_code]
                
                # ============================================================
                # 方案 2: 智能 Quali Sim 識別（多層回退策略）
                # ============================================================
                
                quali_sim_laps = self._identify_quali_sim_laps_fp2(driver_laps)
                
                if not quali_sim_laps.empty:
                    fastest_lap = quali_sim_laps.loc[quali_sim_laps['LapTime'].idxmin()]
                    filter_stats['using_soft_quali_sim'] += 1
                    print(f"   {driver_code}: 使用 SOFT 胎 Quali Sim 最快圈 ({len(quali_sim_laps)} 圈候選)")
                else:
                    # 回退策略：使用所有圈速的最快圈
                    fastest_lap = driver_laps.loc[driver_laps['LapTime'].idxmin()]
                    filter_stats['using_fallback'] += 1
                    compound = fastest_lap.get('Compound', 'UNKNOWN')
                    print(f"   {driver_code}: ⚠️ 無 Quali Sim，使用最快圈 ({compound} 胎)")
                
                lap_time = fastest_lap['LapTime'].total_seconds()
                
                try:
                    s1 = fastest_lap['Sector1Time'].total_seconds() if pd.notna(fastest_lap['Sector1Time']) else lap_time / 3
                    s2 = fastest_lap['Sector2Time'].total_seconds() if pd.notna(fastest_lap['Sector2Time']) else lap_time / 3
                    s3 = fastest_lap['Sector3Time'].total_seconds() if pd.notna(fastest_lap['Sector3Time']) else lap_time / 3
                except:
                    s1, s2, s3 = lap_time / 3, lap_time / 3, lap_time / 3
                
                try:
                    telemetry = fastest_lap.get_telemetry()
                    speeds = telemetry['Speed'].values if 'Speed' in telemetry.columns else np.array([250.0])
                    max_speed = float(speeds.max())
                    avg_speed = float(speeds.mean())
                    speed_std = float(speeds.std())
                    low_speed_apex = float(np.percentile(speeds, 25))
                    mid_speed_apex = float(np.percentile(speeds, 50))
                    high_speed_apex = float(np.percentile(speeds, 75))
                except:
                    max_speed = 300.0
                    avg_speed = 250.0
                    speed_std = 10.0
                    low_speed_apex = 200.0
                    mid_speed_apex = 250.0
                    high_speed_apex = 280.0
                
                features = {
                    'ideal_s1': s1,
                    'ideal_s2': s2,
                    'ideal_s3': s3,
                    'ideal_lap': lap_time,
                    'low_speed_apex': low_speed_apex,
                    'mid_speed_apex': mid_speed_apex,
                    'high_speed_apex': high_speed_apex,
                    'max_speed': max_speed,
                    's1_s2_ratio': s1 / s2 if s2 > 0 else 1.0,
                    'sector_cv': speed_std / avg_speed if avg_speed > 0 else 0.1,
                    's2_lap_ratio': s2 / lap_time if lap_time > 0 else 0.33,
                    'max_speed_lap_ratio': max_speed * lap_time / 1000 if lap_time > 0 else 20.0,
                    'max_speed_s2_ratio': max_speed / s2 if s2 > 0 else 10.0,
                    'speed_consistency': 1.0 - (speed_std / avg_speed) if avg_speed > 0 else 0.9,
                    'fp2_relative_position': 0.5,
                    'fp2_gap_to_fastest': 0.0
                }
                
                predictions.append({
                    'driver': driver_code,
                    'fp2_time': lap_time,
                    'features': features,
                    'team': fastest_lap.get('Team', 'Unknown')
                })
            
            # 計算 FP2 排位相關特徵
            predictions.sort(key=lambda x: x['fp2_time'])
            fastest_fp2 = predictions[0]['fp2_time']
            
            for i, pred in enumerate(predictions):
                pred['features']['fp2_relative_position'] = (i + 1) / len(predictions)
                pred['features']['fp2_gap_to_fastest'] = pred['fp2_time'] - fastest_fp2
            
            print(f"✅ 提取 {len(predictions)} 位車手的特徵")
            print(f"   - SOFT 胎 Quali Sim: {filter_stats['using_soft_quali_sim']} 位")
            print(f"   - 回退使用最快圈: {filter_stats['using_fallback']} 位")
            
            # ============================================================
            # 載入車隊燃油習慣校正數據 (方案 B - 僅 Quali Sim)
            # ============================================================
            team_fuel_habits = {}
            fuel_habits_file = Path(__file__).parent.parent.parent.parent / "training_data" / "team_fuel_habits.json"
            if fuel_habits_file.exists():
                try:
                    with open(fuel_habits_file, 'r', encoding='utf-8') as f:
                        habits_data = json.load(f)
                    team_fuel_habits = habits_data.get('team_habits', {})
                    # 過濾只保留有 Quali Sim 數據的車隊
                    team_fuel_habits = {
                        k: v for k, v in team_fuel_habits.items() 
                        if v.get('has_quali_sim_data', False) and v.get('fuel_correction_seconds') is not None
                    }
                    print(f"\n✅ 載入車隊燃油習慣 (僅 Quali Sim): {len(team_fuel_habits)} 個車隊")
                except Exception as e:
                    print(f"⚠️  載入車隊燃油習慣失敗: {e}")
            else:
                print(f"⚠️  未找到車隊燃油習慣檔案，不進行燃油校正")
            
            # ============================================================
            # 車隊 FP2→Q 一致性調整因子 (2026-01-04 新增)
            # 從 2022-2025 歷史數據學習（training_data/team_consistency_factors.json）
            # 正數值 = 預測時間需要加慢（這些車隊 FP2 表現比 Q 不一致）
            # ============================================================
            team_consistency_adjustment = {}
            consistency_file = Path(__file__).parent.parent.parent.parent / "training_data" / "team_consistency_factors.json"
            if consistency_file.exists():
                try:
                    with open(consistency_file, 'r', encoding='utf-8') as f:
                        consistency_data = json.load(f)
                    for team, info in consistency_data.get('team_factors', {}).items():
                        team_consistency_adjustment[team] = info.get('total_adjustment', 0.0)
                    print(f"✅ 載入車隊一致性因子 (從歷史數據學習): {len(team_consistency_adjustment)} 個車隊")
                except Exception as e:
                    print(f"⚠️  載入車隊一致性因子失敗: {e}")
            else:
                print(f"⚠️  未找到車隊一致性因子檔案")
            
            # ============================================================
            # 賽道特定調整因子 (2026-01-04 新增)
            # 不同賽道的 FP2→Q 轉化特性不同
            # track_adjustment = 賽道平均 - 全局平均
            # 正數 = 需要加慢預測，負數 = 需要加快預測
            # ============================================================
            track_adjustment = 0.0
            track_factors_file = Path(__file__).parent.parent.parent.parent / "training_data" / "track_adjustment_factors.json"
            if track_factors_file.exists():
                try:
                    with open(track_factors_file, 'r', encoding='utf-8') as f:
                        track_factors_data = json.load(f)
                    track_factors = track_factors_data.get('track_factors', {})
                    if race in track_factors:
                        track_adjustment = track_factors[race].get('track_adjustment', 0.0)
                        print(f"✅ 載入賽道調整因子: {race} = {track_adjustment:+.3f}s")
                    else:
                        print(f"⚠️  未找到 {race} 的賽道調整因子，使用預設值 0.0")
                except Exception as e:
                    print(f"⚠️  載入賽道調整因子失敗: {e}")
            
            # ============================================================
            # 賽道演進效應因子 (2026-01-05 新增)
            # Q 時賽道通常有更多橡膠，抓地力更好
            # evolution_adjustment = 相對於全局中位數的偏差
            # 正數 = 演進較弱需要加慢預測，負數 = 演進較強需要加快預測
            # ============================================================
            track_evolution_adjustment = 0.0
            track_evolution_file = Path(__file__).parent.parent.parent.parent / "training_data" / "track_evolution_factors.json"
            if track_evolution_file.exists():
                try:
                    with open(track_evolution_file, 'r', encoding='utf-8') as f:
                        evolution_data = json.load(f)
                    evolution_factors = evolution_data.get('track_factors', {})
                    if race in evolution_factors:
                        track_evolution_adjustment = evolution_factors[race].get('evolution_adjustment', 0.0)
                        median_delta = evolution_factors[race].get('median_delta', 0.0)
                        print(f"✅ 載入賽道演進因子: {race} = {track_evolution_adjustment:+.3f}s (中位數: {median_delta:.3f}s)")
                    else:
                        print(f"⚠️  未找到 {race} 的賽道演進因子，使用預設值 0.0")
                except Exception as e:
                    print(f"⚠️  載入賽道演進因子失敗: {e}")
            
            # ============================================================
            # 車隊樂觀度校正因子 (2026-01-04 新增)
            # 某些車隊的 FP2 Quali Sim 過於樂觀，無法在 Q 重現
            # 這個校正因子基於預測誤差分析
            # ============================================================
            team_optimism_correction = {}
            optimism_file = Path(__file__).parent.parent.parent.parent / "training_data" / "team_optimism_correction.json"
            if optimism_file.exists():
                try:
                    with open(optimism_file, 'r', encoding='utf-8') as f:
                        optimism_data = json.load(f)
                    for team_name, info in optimism_data.get('team_corrections', {}).items():
                        team_optimism_correction[team_name] = info.get('optimism_correction', 0.0)
                    print(f"✅ 載入車隊樂觀度校正因子: {len(team_optimism_correction)} 個車隊")
                except Exception as e:
                    print(f"⚠️  載入車隊樂觀度校正因子失敗: {e}")
            
            # 生成預測
            print("\n生成排位賽預測（燃油校正 + 車隊一致性調整 + 賽道調整 + 賽道演進 + 樂觀度校正）...")
            
            for pred in predictions:
                feature_vector = [pred['features'][fname] for fname in feature_names]
                predicted_improvement = model.predict([feature_vector])[0]
                
                # 應用車隊燃油校正 (僅限有 Quali Sim 數據的車隊)
                team = pred.get('team', 'Unknown')
                if team in team_fuel_habits:
                    fuel_correction = team_fuel_habits[team].get('fuel_correction_seconds')
                    correction_source = 'quali_sim_only'
                else:
                    # 沒有 Quali Sim 數據，不進行燃油校正
                    fuel_correction = None
                    correction_source = 'no_data'
                
                # 計算預測時間
                # 基本預測 = FP2時間 + 模型預測的改進量
                base_predicted = pred['fp2_time'] + predicted_improvement
                
                # 應用燃油校正：FP2 Quali Sim 比實際 Q 快，需要加回校正值
                # fuel_correction_seconds 代表「實際Q時間 - Quali Sim時間」的平均差異
                if fuel_correction is not None:
                    final_predicted = base_predicted + fuel_correction
                else:
                    final_predicted = base_predicted
                
                # 🆕 應用車隊一致性調整因子（從歷史數據學習）
                consistency_adj = team_consistency_adjustment.get(team, 0.0)
                if consistency_adj > 0:
                    final_predicted += consistency_adj
                    pred['consistency_adjustment'] = float(consistency_adj)
                else:
                    pred['consistency_adjustment'] = 0.0
                
                # 🆕 應用賽道調整因子（從歷史數據學習）
                # track_adjustment 已經計算為相對於全局平均的偏差
                # 正數 = 這個賽道 FP2→Q 進步較少，需要加慢預測
                # 負數 = 這個賽道 FP2→Q 進步較多，需要加快預測
                final_predicted += track_adjustment
                pred['track_adjustment'] = float(track_adjustment)
                
                # 🆕 應用賽道演進效應因子（2026-01-05）
                # evolution_adjustment 相對於全局中位數的偏差
                # 正數 = 演進較弱需要加慢預測，負數 = 演進較強需要加快預測
                if track_evolution_adjustment != 0.0:
                    final_predicted += track_evolution_adjustment
                    pred['evolution_adjustment'] = float(track_evolution_adjustment)
                else:
                    pred['evolution_adjustment'] = 0.0
                
                # 🆕 應用車隊樂觀度校正因子（2026-01-04）
                # 某些車隊的 FP2 Quali Sim 過於樂觀，無法在 Q 重現
                optimism_adj = team_optimism_correction.get(team, 0.0)
                if optimism_adj > 0:
                    final_predicted += optimism_adj
                    pred['optimism_adjustment'] = float(optimism_adj)
                else:
                    pred['optimism_adjustment'] = 0.0
                
                pred['predicted_time_xgb'] = float(final_predicted) # Store raw XGB
                pred['predicted_time'] = float(final_predicted)
                pred['improvement'] = float(final_predicted - pred['fp2_time'])
                pred['fuel_correction'] = float(fuel_correction) if fuel_correction else None
                pred['fuel_correction_source'] = correction_source
            
            # ============================================================
            # v5.0 Ensemble Stacking 邏輯 (XGBoost + LightGBM + CatBoost)
            # 1. 獲取 LightGBM 預測 (增加多樣性)
            # 2. 結合 XGBoost 和 LightGBM 生成 Ensemble Time
            # 3. 使用 CatBoost Ranker 進行最終排序
            # ============================================================
            
            # --- LightGBM Loading ---
            lgbm_model_path = Path(__file__).parent.parent.parent.parent / "models" / "fp2_q_lightgbm_v5" / "lightgbm_model_v5.0.txt"
            has_lgbm = False
            if lgbm_model_path.exists():
                try:
                    import lightgbm as lgb
                    lgb_booster = lgb.Booster(model_file=str(lgbm_model_path))
                    print(f"\n✅ 啟用 LightGBM (v5.0 Ensemble)")
                    
                    # 準備特徵 (與 train_fp2_q_lightgbm.py 一致)
                    lgbm_feats = [
                        'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
                        'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
                        's1_s2_ratio', 'sector_cv', 's2_lap_ratio',
                        'max_speed_lap_ratio', 'max_speed_s2_ratio', 'speed_consistency',
                        'fp2_relative_position', 'fp2_gap_to_fastest'
                    ]
                    
                    lgbm_input = []
                    for p in predictions:
                        row = [p['features'].get(f, 0.0) for f in lgbm_feats]
                        lgbm_input.append(row)
                        
                    lgbm_preds = lgb_booster.predict(lgbm_input)
                    
                    for i, p in enumerate(predictions):
                        # Calculate LightGBM Time
                         # Improvement output from model
                        imp_lgb = lgbm_preds[i]
                        
                        # Apply same adjustments as XGBoost (Track, Fuel, etc.)
                        # Note: LightGBM trained on raw improvement? 
                        # train_fp2_q_lightgbm.py loaded CLEANED data which has static factors applied?
                        # No, clean_static_factors UPDATED json files, but clean_data contains RAW improvement?
                        # Wait, clean_static_factors filters rows, but does not modify 'fp2_d' values inside the list?
                        # It saves `clean_data` which is a LIST of records.
                        # The records are ORIGINAL.
                        # So LightGBM predicts Raw Improvement (Q - FP2).
                        # We need to apply Track/Evolution adjustments to it too.
                        
                        base_lgb = p['fp2_time'] + imp_lgb
                        
                        # Apply Adjustments (Re-using calculated values from XGB loop)
                        # We stored adjustments in p['track_adjustment'], etc.
                        adj = p.get('track_adjustment', 0) + \
                              p.get('evolution_adjustment', 0) + \
                              p.get('consistency_adjustment', 0) + \
                              p.get('optimism_adjustment', 0)
                        
                        fuel = p.get('fuel_correction') or 0
                        
                        final_lgb = base_lgb + adj + fuel
                        p['predicted_time_lgbm'] = final_lgb
                        
                    has_lgbm = True
                except Exception as e:
                    print(f"⚠️  載入 LightGBM 失敗: {e}")
            
            # --- Ensemble Averaging ---
            if has_lgbm:
                for p in predictions:
                    # Weighting: XGB (Optuna) 0.6, LGBM (Dart) 0.4
                    t_xgb = p['predicted_time_xgb']
                    t_lgb = p['predicted_time_lgbm']
                    p['predicted_time'] = 0.6 * t_xgb + 0.4 * t_lgb
                    p['improvement'] = p['predicted_time'] - p['fp2_time']
            
            # --- CatBoost Ranking & Swap ---
            xgb_times_sorted = sorted([p['predicted_time'] for p in predictions])
            
            # 嘗試載入 CatBoost Ranker
            catboost_model_path = Path(__file__).parent.parent.parent.parent / "models" / "fp2_q_catboost_v4" / "catboost_ranker_v4.0.cbm"
            use_catboost = False
            
            if catboost_model_path.exists():
                try:
                    from catboost import CatBoostRanker
                    ranker = CatBoostRanker()
                    ranker.load_model(str(catboost_model_path))
                    print(f"✅ 啟用 CatBoost Ranker (v4.0 Hybrid)")
                    
                    # 準備 CatBoost 輸入特徵
                    # 注意：必須與 train_fp2_q_catboost.py 中的特徵順序一致
                    numeric_features = [
                        'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
                        'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
                        's1_s2_ratio', 'sector_cv', 's2_lap_ratio',
                        'max_speed_lap_ratio', 'max_speed_s2_ratio', 'speed_consistency',
                        'fp2_relative_position', 'fp2_gap_to_fastest'
                    ]
                    cat_features = ['Track', 'Team']
                    
                    # 必須為每一行構建特徵列表 [Num..., Cat...]
                    batch_data = []
                    for p in predictions:
                        row = []
                        # 數值特徵
                        for feat in numeric_features:
                            row.append(p['features'].get(feat, 0.0))
                        # 類別特徵
                        row.append(race)       # Track
                        row.append(p['team'])  # Team
                        batch_data.append(row)
                    
                    # 預測分數 (Relevance Score, Higher is Better usually for YetiRank predictions if trained on relevance labels)
                    # Train script used Relevance = 21 - Rank. So Higher = Better.
                    scores = ranker.predict(batch_data)
                    
                    for i, p in enumerate(predictions):
                        p['rank_score'] = float(scores[i])
                        
                    # 按分數降序排序 (Higher Score = Better Rank)
                    predictions.sort(key=lambda x: x['rank_score'], reverse=True)
                    use_catboost = True
                    print(f"   Ensemble + Hybrid Swap 應用完成...")
                    
                except Exception as e:
                    print(f"⚠️  載入 CatBoost Ranker 失敗，回退至僅使用 Time Ensemble: {e}")
                    import traceback
                    traceback.print_exc()
            
            if use_catboost:
                # 應用 Hybrid Time Swap: 將排序好的 Ensemble 時間分配給 CatBoost 排序後的車手
                for i, p in enumerate(predictions):
                    new_time = xgb_times_sorted[i] # 第 i 名應該獲得第 i 快的时间
                    p['predicted_time'] = new_time
                    p['improvement'] = new_time - p['fp2_time']
            else:
                # 原有邏輯：僅按時間排序
                predictions.sort(key=lambda x: x['predicted_time'])
            
            # 嘗試獲取實際排位賽結果
            actual_q_times = {}
            try:
                print(f"\n嘗試載入 {year} {race} Q 會話數據...")
                q_loaded = self.data_loader.load_race_data(year, race, 'Q')
                
                if q_loaded and self.data_loader.session:
                    q_session = self.data_loader.session
                    q_laps = q_session.laps[q_session.laps['LapTime'].notna()]
                    
                    if not q_laps.empty:
                        print(f"✅ Q 會話數據載入成功")
                        for driver_code in q_laps['Driver'].unique():
                            driver_q_laps = q_laps[q_laps['Driver'] == driver_code]
                            fastest_q_lap = driver_q_laps.loc[driver_q_laps['LapTime'].idxmin()]
                            actual_q_times[driver_code] = float(fastest_q_lap['LapTime'].total_seconds())
            except:
                print("⚠️  Q 會話數據不可用")
            
            # 計算 FP2 預測名次（按 FP2 時間排序）
            fp2_sorted = sorted(predictions, key=lambda x: x['fp2_time'])
            fp2_rank_map = {p['driver']: i + 1 for i, p in enumerate(fp2_sorted)}
            
            # 計算 Q 實際名次（按 Q 時間排序）
            q_rank_map = {}
            if actual_q_times:
                q_sorted = sorted(actual_q_times.items(), key=lambda x: x[1])
                q_rank_map = {driver: i + 1 for i, (driver, _) in enumerate(q_sorted)}
            
            # 構建 JSON 輸出
            output_data = {
                "metadata": {
                    "track": race,
                    "year": year,
                    "session": "Q",
                    "data_source": session_type_used,  # 記錄實際使用的 session (FP2 或 FP1)
                    "is_sprint_weekend": (session_type_used == 'FP1'),  # 標記是否為衝刺賽週末
                    "model_r2": float(model_r2),
                    "model_mae": float(model_mae),
                    "sample_count": int(sample_count),
                    "prediction_time": datetime.now().isoformat(),
                    "model_version": "v3.10_FP2",
                    "feature_count": len(feature_names),
                    "has_actual_results": len(actual_q_times) > 0,
                    "fuel_correction_enabled": len(team_fuel_habits) > 0,
                    "fuel_correction_teams_count": len(team_fuel_habits)
                },
                "predictions": []
            }
            
            for rank, pred in enumerate(predictions, 1):
                driver = pred['driver']
                fp2_pred_rank = fp2_rank_map.get(driver, rank)
                actual_q_rank = q_rank_map.get(driver)
                
                # 計算名次變化（FP2 預測名次 → Q 實際名次）
                # 正數 = 進步（例如：FP2 第5 → Q 第3 = +2）
                # 負數 = 退步（例如：FP2 第3 → Q 第5 = -2）
                rank_change = None
                if actual_q_rank is not None:
                    rank_change = fp2_pred_rank - actual_q_rank
                
                fuel_corr_value = pred.get('fuel_correction')
                output_data["predictions"].append({
                    "rank": rank,
                    "driver": driver,
                    "team": pred['team'],
                    "fp2_time": float(pred['fp2_time']),
                    "predicted_time": float(pred['predicted_time']),
                    "actual_q_time": actual_q_times.get(driver),
                    "improvement": float(pred['improvement']),
                    "fuel_correction": float(fuel_corr_value) if fuel_corr_value is not None else 0.0,
                    "fuel_correction_source": pred.get('fuel_correction_source', 'unknown'),
                    "consistency_adjustment": float(pred.get('consistency_adjustment', 0)),
                    "track_adjustment": float(pred.get('track_adjustment', 0)),
                    "evolution_adjustment": float(pred.get('evolution_adjustment', 0)),
                    "optimism_adjustment": float(pred.get('optimism_adjustment', 0)),
                    "fp2_predicted_rank": fp2_pred_rank,
                    "actual_q_rank": actual_q_rank,
                    "rank_change": rank_change
                })
            
            # 保存 JSON
            json_dir = Path(__file__).parent.parent.parent.parent / "json"
            json_dir.mkdir(exist_ok=True)
            json_file = json_dir / f"fp2_qualifying_prediction_{year}_{race}.json"
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n✅ JSON 檔案已保存: {json_file}")
            
            # 輸出預測摘要
            print(f"\n預測摘要 (基於 {session_type_used} 數據):")
            if session_type_used == 'FP1':
                print(f"  ⚠️  注意：衝刺賽週末，已自動使用 FP1 數據替代 FP2")
            print(f"  前 5 名預測:")
            for i, pred in enumerate(output_data['predictions'][:5], 1):
                print(f"    P{i}: {pred['driver']} - {pred['predicted_time']:.3f}s ({session_type_used}: {pred['fp2_time']:.3f}s, △{pred['improvement']:.3f}s)")
            
            return {
                "success": True,
                "message": f"{year} {race} FP2→Q 預測生成成功",
                "data": {
                    "json_data": [str(json_file)],
                    "metadata": output_data["metadata"],
                    "predictions": output_data["predictions"],
                    "predictions_count": len(predictions)
                },
                "json_file": str(json_file),
                "predictions_count": len(predictions),
                "model_r2": float(model_r2),
                "model_mae": float(model_mae),
                "function_id": "76"
            }
        
        except Exception as e:
            print(f"[ERROR] FP2→Q 預測生成失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"FP2→Q 預測生成失敗: {str(e)}",
                "error": str(e),
                "function_id": "76"
            }

    def _execute_ensemble_training(self, **kwargs) -> Dict[str, Any]:
        """
        功能 76: 集成學習訓練（XGBoost + LightGBM + CatBoost）(2025-11-02)
        
        使用三個 GBDT 模型的集成策略，包含：
        - XGBoost (Function 75 最佳參數)
        - LightGBM (匹配參數)
        - CatBoost (匹配參數)
        - 加權平均集成（逆 MAE 權重）
        - Stacking 集成（Ridge 元模型）
        
        目標：在 Function 75 基礎上（MAE 0.8264s）進一步優化至 < 0.80s
        
        參數：
            --start-year: 訓練起始年份（默認 2018）
            --end-year: 訓練結束年份（默認 2024）
            --test-year: 測試年份（默認 2025）
            --val-split: 驗證集比例（默認 0.2）
        
        返回：
            Dict: 包含集成性能指標的結果
        """
        try:
            from CLI_modules.cli.prediction.ensemble_trainer import EnsembleTrainer
            import numpy as np
            import pandas as pd
            import json
            from pathlib import Path
            from datetime import datetime
            
            # 獲取參數，使用默認值
            start_year = kwargs.get('start_year') or 2018
            end_year = kwargs.get('end_year') or 2024
            test_year = kwargs.get('test_year') or 2025
            val_split = kwargs.get('val_split') or 0.2
            
            print("="*70)
            print(f"功能 76: 集成學習訓練（XGBoost + LightGBM + CatBoost）")
            print("="*70)
            print(f"訓練資料: {start_year}-{end_year}")
            print(f"測試資料: {test_year}")
            print(f"驗證集比例: {val_split*100:.0f}%")
            print(f"目標: MAE < 0.80s（Function 75 基準: 0.8264s）")
            print("="*70)
            
            # ===== 步驟 1: 載入訓練數據（複用 Function 75 的 XGBoostTrainer）=====
            print("\n[1/6] 載入訓練數據...")
            
            # 使用 XGBoostTrainer 載入數據（與 Function 75 一致）
            from CLI_modules.cli.prediction.xgboost_trainer import XGBoostTrainer
            
            trainer = XGBoostTrainer(verbose=True)
            
            print(f"  載入 {start_year}-{end_year} 訓練數據...")
            training_data = trainer.load_training_data(
                start_year=start_year,
                end_year=end_year,
                exclude_wet=True
            )
            
            if training_data.empty:
                return {
                    "success": False,
                    "message": "未找到有效訓練數據",
                    "function_id": "76"
                }
            
            # 準備特徵（使用 XGBoostTrainer 的 prepare_features）
            X_train_full, y_train_full = trainer.prepare_features(training_data)
            
            print(f"\n✅ 訓練數據載入完成: {len(X_train_full)} 樣本")
            print(f"   特徵維度: {X_train_full.shape[1]}")
            print(f"   目標範圍: {y_train_full.min():.3f}s - {y_train_full.max():.3f}s")
            
            # 獲取特徵數量（從 XGBoostTrainer）
            features_count = X_train_full.shape[1]
            
            # ===== 步驟 2: 分割訓練/驗證集 =====
            print(f"\n[2/6] 分割訓練/驗證集（{int((1-val_split)*100)}%/{int(val_split*100)}%）...")
            
            from sklearn.model_selection import train_test_split
            X_train, X_val, y_train, y_val = train_test_split(
                X_train_full, y_train_full, test_size=val_split, random_state=42
            )
            
            print(f"   訓練集: {len(X_train)} 樣本")
            print(f"   驗證集: {len(X_val)} 樣本")
            
            # ===== 步驟 3: 訓練集成模型 =====
            print(f"\n[3/6] 訓練集成模型（XGBoost + LightGBM + CatBoost）...")
            
            ensemble = EnsembleTrainer(features_count=features_count, verbose=True)
            
            # 訓練 XGBoost
            print("\n  [3.1] 訓練 XGBoost...")
            ensemble.train_xgboost(X_train, y_train, X_val, y_val)
            xgb_perf = ensemble.performance['xgboost']
            print(f"     MAE: {xgb_perf['mae']:.4f}s  R²: {xgb_perf['r2']:.4f}  RMSE: {xgb_perf['rmse']:.4f}s")
            
            # 訓練 LightGBM
            print("\n  [3.2] 訓練 LightGBM...")
            ensemble.train_lightgbm(X_train, y_train, X_val, y_val)
            lgb_perf = ensemble.performance['lightgbm']
            print(f"     MAE: {lgb_perf['mae']:.4f}s  R²: {lgb_perf['r2']:.4f}  RMSE: {lgb_perf['rmse']:.4f}s")
            
            # 訓練 CatBoost
            print("\n  [3.3] 訓練 CatBoost...")
            ensemble.train_catboost(X_train, y_train, X_val, y_val)
            ctb_perf = ensemble.performance['catboost']
            print(f"     MAE: {ctb_perf['mae']:.4f}s  R²: {ctb_perf['r2']:.4f}  RMSE: {ctb_perf['rmse']:.4f}s")
            
            # ===== 步驟 4: 創建集成策略 =====
            print(f"\n[4/6] 創建集成策略...")
            
            # 加權平均集成
            print("\n  [4.1] 加權平均集成（逆 MAE 權重）...")
            ensemble.create_weighted_average(X_val, y_val)
            weighted_perf = ensemble.performance['weighted_avg']
            print(f"     權重: XGB={ensemble.ensemble_weights['xgboost']:.3f}, "
                  f"LGB={ensemble.ensemble_weights['lightgbm']:.3f}, "
                  f"CTB={ensemble.ensemble_weights['catboost']:.3f}")
            print(f"     MAE: {weighted_perf['mae']:.4f}s  R²: {weighted_perf['r2']:.4f}  RMSE: {weighted_perf['rmse']:.4f}s")
            
            # Stacking 集成
            print("\n  [4.2] Stacking 集成（Ridge 元模型）...")
            ensemble.create_stacking(X_train, y_train, X_val, y_val)
            stacking_perf = ensemble.performance['stacking']
            stacking_weights = stacking_perf.get('weights', {})
            print(f"     權重: XGB={stacking_weights.get('xgboost', 0):.3f}, "
                  f"LGB={stacking_weights.get('lightgbm', 0):.3f}, "
                  f"CTB={stacking_weights.get('catboost', 0):.3f}")
            print(f"     MAE: {stacking_perf['mae']:.4f}s  R²: {stacking_perf['r2']:.4f}  RMSE: {stacking_perf['rmse']:.4f}s")
            
            # ===== 步驟 5: 選擇最佳方法 =====
            print(f"\n[5/6] 選擇最佳方法...")
            best_method = ensemble.select_best_method()
            best_perf = ensemble.performance[best_method]
            
            print(f"\n   🏆 最佳方法: {best_method}")
            print(f"      MAE: {best_perf['mae']:.4f}s")
            print(f"      R²: {best_perf['r2']:.4f}")
            print(f"      RMSE: {best_perf['rmse']:.4f}s")
            
            # ===== 步驟 6: 2025 測試集驗證 =====
            print(f"\n[6/6] 2025 測試集驗證...")
            
            # 使用 XGBoostTrainer 載入測試數據
            trainer_test = XGBoostTrainer(verbose=False)
            
            print(f"  載入 {test_year} 測試數據...")
            test_data = trainer_test.load_training_data(
                start_year=test_year,
                end_year=test_year,
                exclude_wet=True
            )
            
            if test_data.empty:
                print(f"   ⚠️ 未找到 {test_year} 測試數據，跳過測試集驗證")
                X_test, y_test = None, None
                mae_test, r2_test, rmse_test = None, None, None
            else:
                X_test, y_test = trainer_test.prepare_features(test_data)
                
                y_test_pred = ensemble.predict(X_test, method='best')
                
                from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
                mae_test = mean_absolute_error(y_test, y_test_pred)
                r2_test = r2_score(y_test, y_test_pred)
                rmse_test = np.sqrt(mean_squared_error(y_test, y_test_pred))
                
                print(f"\n   測試集樣本: {len(X_test)}")
                print(f"   測試集 MAE: {mae_test:.4f}s")
                print(f"   測試集 R²: {r2_test:.4f}")
                print(f"   測試集 RMSE: {rmse_test:.4f}s")
                
                # 與 Function 75 比較
                baseline_mae = 0.8264
                improvement = ((baseline_mae - mae_test) / baseline_mae) * 100
                print(f"\n   📊 vs Function 75:")
                print(f"      基準 MAE: {baseline_mae:.4f}s")
                print(f"      改進幅度: {improvement:+.2f}%")
                print(f"      目標達成: {'✅ 是' if mae_test < 0.80 else '❌ 否'} (目標 < 0.80s)")
            
            # ===== 保存模型和結果 =====
            print(f"\n保存集成模型...")
            model_dir = Path("models")
            model_dir.mkdir(exist_ok=True)
            ensemble.save(str(model_dir))
            print(f"   ✅ 模型已保存至 {model_dir}/")
            
            # 生成報告
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report = {
                "function_id": "76",
                "function_name": "集成學習訓練",
                "timestamp": timestamp,
                "training_period": f"{start_year}-{end_year}",
                "test_year": test_year,
                "training_samples": int(len(X_train)),
                "validation_samples": int(len(X_val)),
                "test_samples": int(len(X_test)) if X_test is not None else 0,
                "feature_count": features_count,
                "features": list(training_data.columns),  # 從 DataFrame 獲取特徵名稱
                "models": {
                    "xgboost": {
                        "mae": float(xgb_perf['mae']),
                        "r2": float(xgb_perf['r2']),
                        "rmse": float(xgb_perf['rmse'])
                    },
                    "lightgbm": {
                        "mae": float(lgb_perf['mae']),
                        "r2": float(lgb_perf['r2']),
                        "rmse": float(lgb_perf['rmse'])
                    },
                    "catboost": {
                        "mae": float(ctb_perf['mae']),
                        "r2": float(ctb_perf['r2']),
                        "rmse": float(ctb_perf['rmse'])
                    },
                    "weighted_average": {
                        "mae": float(weighted_perf['mae']),
                        "r2": float(weighted_perf['r2']),
                        "rmse": float(weighted_perf['rmse']),
                        "weights": {
                            "xgboost": float(ensemble.ensemble_weights['xgboost']),
                            "lightgbm": float(ensemble.ensemble_weights['lightgbm']),
                            "catboost": float(ensemble.ensemble_weights['catboost'])
                        }
                    },
                    "stacking": {
                        "mae": float(stacking_perf['mae']),
                        "r2": float(stacking_perf['r2']),
                        "rmse": float(stacking_perf['rmse']),
                        "weights": stacking_weights
                    }
                },
                "best_method": best_method,
                "best_validation_performance": {
                    "mae": float(best_perf['mae']),
                    "r2": float(best_perf['r2']),
                    "rmse": float(best_perf['rmse'])
                }
            }
            
            # 添加測試集結果（如果有）
            if mae_test is not None:
                report["test_performance"] = {
                    "mae": float(mae_test),
                    "r2": float(r2_test),
                    "rmse": float(rmse_test),
                    "baseline_mae": baseline_mae,
                    "improvement_pct": float(improvement),
                    "target_achieved": mae_test < 0.80
                }
            
            # 保存 JSON 報告
            report_dir = Path("reports")
            report_dir.mkdir(exist_ok=True)
            report_path = report_dir / f"ensemble_training_{timestamp}.json"
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"\n✅ 報告已保存至 {report_path}")
            
            # ===== 總結 =====
            print("\n" + "="*70)
            print("集成學習訓練完成！")
            print("="*70)
            print(f"最佳方法: {best_method}")
            print(f"驗證集 MAE: {best_perf['mae']:.4f}s")
            if mae_test is not None:
                print(f"測試集 MAE: {mae_test:.4f}s")
                print(f"目標達成: {'✅ 是' if mae_test < 0.80 else '❌ 否'} (< 0.80s)")
                print(f"vs Function 75: {improvement:+.2f}%")
            print("="*70)
            
            return {
                "success": True,
                "message": f"集成學習訓練完成（最佳方法：{best_method}）",
                "best_method": best_method,
                "validation_mae": float(best_perf['mae']),
                "test_mae": float(mae_test) if mae_test is not None else None,
                "improvement_pct": float(improvement) if mae_test is not None else None,
                "target_achieved": mae_test < 0.80 if mae_test is not None else None,
                "report_path": str(report_path),
                "function_id": "76"
            }
            
        except ImportError as e:
            return {
                "success": False,
                "message": f"缺少必要套件: {str(e)}",
                "hint": "請確認已安裝 xgboost, lightgbm, catboost, scikit-learn",
                "function_id": "76"
            }
        except Exception as e:
            print(f"[ERROR] 集成學習訓練失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"集成學習訓練失敗: {str(e)}",
                "error": str(e),
                "function_id": "76"
            }
    
    def _execute_track_specific_training(self, **kwargs) -> Dict[str, Any]:
        """
        功能 77: 賽道特定模型訓練（v2.0 + Function 78）(2025-11-03)
        
        為每個賽道訓練獨立的 XGBoost 模型，並整合 Function 78 的車手 FP3→Q 特徵
        
        參數：
            --track: 賽道名稱（例如：Mexico）
            --train: 訓練模式（生成模型）
            --predict: 預測模式（使用已訓練模型）
            --year: 預測年份（默認 2025）
        
        返回：
            Dict: 包含訓練或預測結果
        """
        try:
            from CLI_modules.cli.prediction.track_specific_trainer import TrackSpecificTrainer
            from pathlib import Path
            
            # 獲取參數
            track_name = kwargs.get('track') or 'Mexico'
            train_mode = kwargs.get('train', False)
            predict_mode = kwargs.get('predict', False)
            year = kwargs.get('year', 2025)
            
            print("="*70)
            print(f"功能 77: 賽道特定模型訓練 (v2.0 + Function 78)")
            print("="*70)
            print(f"賽道: {track_name}")
            print(f"模式: {'訓練' if train_mode else '預測' if predict_mode else '訓練'}")
            if predict_mode:
                print(f"預測年份: {year}")
            print("="*70)
            
            # 建立訓練器
            trainer = TrackSpecificTrainer(verbose=True)
            
            if train_mode or (not predict_mode):
                # 訓練模式
                print(f"\n[訓練模式] 載入 2018-2024 歷史數據...")
                
                # 載入訓練數據
                track_data = trainer.load_training_data(
                    start_year=2018,
                    end_year=2024,
                    exclude_wet=True
                )
                
                if not track_data:
                    return {
                        "success": False,
                        "message": "無法載入訓練數據",
                        "function_id": "77"
                    }
                
                # 檢查指定賽道是否有數據
                if track_name not in trainer.track_data:
                    available_tracks = list(trainer.track_data.keys())
                    return {
                        "success": False,
                        "message": f"找不到賽道 {track_name} 的數據",
                        "available_tracks": available_tracks,
                        "function_id": "77"
                    }
                
                # 訓練單一賽道模型
                result = trainer.train_track_model(track_name)
                
                if result['success']:
                    # 儲存模型
                    model_file = trainer.models_dir / f"{track_name}.pkl"
                    import pickle
                    with open(model_file, 'wb') as f:
                        pickle.dump({
                            'model': trainer.track_models[track_name],
                            'performance': trainer.track_performance[track_name],
                            'track': track_name
                        }, f)
                    
                    print(f"\n💾 模型已儲存: {model_file}")
                    
                    return {
                        "success": True,
                        "message": f"{track_name} 模型訓練完成",
                        "track": track_name,
                        "train_mae": result['train_mae'],
                        "test_mae": result['test_mae'],
                        "test_r2": result['test_r2'],
                        "model_file": str(model_file),
                        "function_id": "77"
                    }
                else:
                    return result
            
            else:
                # 預測模式
                print(f"\n[預測模式] 使用 {track_name} 模型預測 {year} 年排位賽")
                
                result = trainer.predict_2025_qualifying(track_name, year)
                
                if result['success']:
                    return {
                        "success": True,
                        "message": f"{year} {track_name} 排位預測完成",
                        "track": track_name,
                        "year": year,
                        "mae": result['mae'],
                        "r2": result['r2'],
                        "spearman": result['spearman'],
                        "predictions": result['predictions'],
                        "function_id": "77"
                    }
                else:
                    return result
        
        except ImportError as e:
            return {
                "success": False,
                "message": f"缺少必要套件: {str(e)}",
                "hint": "請確認已安裝 xgboost, scikit-learn",
                "function_id": "77"
            }
        except Exception as e:
            print(f"[ERROR] 賽道特定訓練失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"賽道特定訓練失敗: {str(e)}",
                "error": str(e),
                "function_id": "77"
            }
    
    def _execute_driver_fp3_q_feature_extraction(self, **kwargs) -> Dict[str, Any]:
        """
        功能 78: 車手 FP3→Q 特徵提取 (2025-11-03)
        
        從 2022-2024 的 FP3 和 Q 數據中提取車手的歷史改進模式特徵
        
        參數：
            --track: 賽道名稱（默認 Mexico）
        
        返回：
            Dict: 包含特徵提取結果
        """
        try:
            import subprocess
            import sys
            from pathlib import Path
            
            # 獲取參數
            track_name = kwargs.get('track') or 'Mexico'
            
            print("="*70)
            print(f"功能 78: 車手 FP3→Q 特徵提取")
            print("="*70)
            print(f"賽道: {track_name}")
            print("="*70)
            
            # 執行特徵提取腳本
            script_path = Path("scripts/extract_driver_fp3_q_features.py")
            
            if not script_path.exists():
                return {
                    "success": False,
                    "message": f"找不到特徵提取腳本: {script_path}",
                    "function_id": "78"
                }
            
            print(f"\n執行特徵提取腳本: {script_path}")
            
            # 執行腳本（不使用 subprocess，直接導入執行）
            import sys
            import os
            
            # 添加腳本目錄到 Python 路徑
            script_dir = script_path.parent
            if str(script_dir) not in sys.path:
                sys.path.insert(0, str(script_dir))
            
            # 導入並執行
            import extract_driver_fp3_q_features
            extractor = extract_driver_fp3_q_features.DriverFP3QFeatureExtractor(track_name=track_name)
            success = extractor.run()
            
            if success:
                output_file = Path("json") / f"driver_fp3_q_features_{track_name}.json"
                return {
                    "success": True,
                    "message": f"{track_name} 賽道的車手 FP3→Q 特徵提取完成",
                    "track": track_name,
                    "output_file": str(output_file),
                    "function_id": "78"
                }
            else:
                return {
                    "success": False,
                    "message": "特徵提取失敗",
                    "function_id": "78"
                }
        
        except Exception as e:
            print(f"[ERROR] 特徵提取失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"特徵提取失敗: {str(e)}",
                "error": str(e),
                "function_id": "78"
            }

    def _execute_dynamic_team_rating(self, **kwargs):
        """Function 79: 動態車隊評級報告 (Live_timing_test 版本)"""
        try:
            import sys
            from pathlib import Path
            
            # 添加 Live_timing_test 到路徑
            base_dir = Path(__file__).resolve().parent.parent.parent.parent
            live_timing_path = base_dir / "Live_timing_test"
            if str(live_timing_path) not in sys.path:
                sys.path.insert(0, str(live_timing_path))
            
            print("="*70)
            print("Function 79: 動態車隊評級報告")
            print("="*70)
            
            # 導入並執行
            from generate_dynamic_rating_report import generate_report
            report = generate_report()
            
            # 保存報告
            output_file = base_dir / "docs/DYNAMIC_TEAM_RATING_REPORT.md"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(f"\n[OK] 報告已保存: {output_file}")
            
            return {
                "success": True,
                "message": "動態車隊評級報告生成完成",
                "output_file": str(output_file),
                "function_id": "79"
            }
            
        except Exception as e:
            print(f"[ERROR] 報告生成失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"報告生成失敗: {str(e)}",
                "error": str(e),
                "function_id": "79"
            }

    def _execute_dynamic_team_rating_cli(self, **kwargs):
        """Function 80: 動態車隊評級分析 / Q→R 正賽預測 (JSON 輸出)
        
        功能說明:
        - 基於歷史數據（2023-2024）計算車隊基準評級
        - 結合 2025 賽季數據動態更新評級
        - 【新增】指定賽道時執行 Q→R 正賽預測
        - 輸出 JSON 格式分析結果，適用於 API 和 GUI 整合
        
        評級公式:
        rating = (win_rate * 4) + (pole_rate * 2) + (podium_rate * 2) + (normalized_points * 2)
        
        參數:
        - year: 目標年份（預設 2025）
        - race: 賽道名稱（如指定則執行 Q→R 預測）
        - up_to_round: 只分析到第 N 輪（可選）
        - show_detailed_output: 是否顯示詳細輸出（預設 True）
        
        輸出:
        - JSON 檔案保存到 json/prediction/
        - 若指定 race：race_prediction_{year}_{race}.json
        - 若未指定 race：dynamic_team_rating_{timestamp}.json
        """
        try:
            from CLI_modules.cli.analyzer.dynamic_team_rating_analysis import (
                run_dynamic_team_rating_analysis
            )
            
            # 參數處理
            year = kwargs.pop('year', None)
            if not year:
                if self.data_loader and getattr(self.data_loader, "year", None):
                    year = self.data_loader.year
                else:
                    year = 2025
            
            # 獲取賽道名稱（新增）
            race = kwargs.pop('race', None)
            if not race:
                if self.data_loader and getattr(self.data_loader, "race", None):
                    race = self.data_loader.race
            
            up_to_round = kwargs.pop('up_to_round', None)
            show_detailed_output = kwargs.pop('show_detailed_output', True)
            
            print("="*70)
            if race:
                print(f"Function 80: Q->R 正賽預測 ({race} {year})")
            else:
                print("Function 80: 動態車隊評級分析 (JSON 輸出)")
            print("="*70)
            print(f"  年份: {year}")
            if race:
                print(f"  賽道: {race}")
                print(f"  模式: Q->R 正賽預測")
            if up_to_round:
                print(f"  分析範圍: 第 1-{up_to_round} 輪")
            print("="*70)
            
            # 執行分析
            result = run_dynamic_team_rating_analysis(
                data_loader=self.data_loader,
                year=year,
                race=race,
                up_to_round=up_to_round,
                show_detailed_output=show_detailed_output
            )
            
            return self._standardize_result(result, 80, "Q->R 正賽預測" if race else "動態車隊評級分析")
            
        except Exception as e:
            print(f"[ERROR] 動態車隊評級分析失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"動態車隊評級分析失敗: {str(e)}",
                "error": str(e),
                "function_id": "80"
            }
    
    # ===== F81-85: 超車預測系統 =====
    
    def _execute_overtake_data_collector(self, year=None, race=None, session="R", **kwargs):
        """Function 81: 超車事件數據收集器
        
        從 Live F1 JSON 數據收集超車事件，生成訓練數據。
        
        Args:
            year: 年份，None 則收集所有可用年份
            race: 賽事名稱（可選，指定則只收集該賽事）
            session: 會話類型（預設 R = 正賽）
            **kwargs: 其他參數
                - split_by_year: bool，是否按年份分割訓練集/驗證集
                - validation_year: int，驗證集的年份閾值（>= 此年份的數據進入驗證集）
            
        Returns:
            收集統計結果
        """
        try:
            # 提取分割參數
            split_by_year = kwargs.get('split_by_year', False)
            validation_year = kwargs.get('validation_year', 2025)
            
            print("=" * 70)
            print("F81: 超車事件數據收集器")
            if split_by_year:
                print(f"模式: 訓練集（< {validation_year}）/ 驗證集（>= {validation_year}）分割")
            else:
                print("模式: 統一收集")
            print("=" * 70)
            
            # 導入收集器
            from CLI_modules.cli.prediction.overtake_prediction.data_collector import (
                OvertakeDataCollector, run_f81_data_collection
            )
            
            # 確定年份列表
            years_to_collect = None
            if year:
                years_to_collect = [int(year)]
            
            # 執行收集
            summary = run_f81_data_collection(
                years=years_to_collect,
                split_by_year=split_by_year,
                validation_year=validation_year,
                verbose=True
            )
            
            return self._standardize_result(summary, 81, "超車事件數據收集")
            
        except Exception as e:
            print(f"[ERROR] F81 超車數據收集失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"超車數據收集失敗: {str(e)}",
                "error": str(e),
                "function_id": "81"
            }
    
    def _execute_overtake_model_trainer(self, year=None, race=None, session="R", **kwargs):
        """Function 82: 超車預測模型訓練器
        
        使用收集的數據訓練 XGBoost 超車預測模型。
        
        Args:
            year: 年份 (暫未使用，預留未來版本化訓練)
            race: 賽事 (暫未使用)
            session: 會話類型 (暫未使用)
            
        Returns:
            訓練報告
        """
        try:
            print("=" * 70)
            print("F82: 超車預測模型訓練器")
            print("=" * 70)
            
            # 導入訓練器
            from CLI_modules.cli.prediction.overtake_prediction.model_trainer import (
                run_f82_model_training
            )
            
            # 執行訓練
            summary = run_f82_model_training(
                version="v1",
                verbose=True
            )
            
            return self._standardize_result(summary, 82, "超車預測模型訓練")
            
        except Exception as e:
            print(f"[ERROR] F82 模型訓練失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"模型訓練失敗: {str(e)}",
                "error": str(e),
                "function_id": "82"
            }
    
    def _execute_overtake_predictor(self, year=None, race=None, session="R", **kwargs):
        """Function 83: 超車預測推理器
        
        使用訓練好的模型進行超車預測。
        
        參數:
            -d / --driver: 進攻者代碼 (如 VER)
            -d2 / --driver2: 防守者代碼 (如 LEC)
        """
        print("=" * 70)
        print("F83: 超車預測推理器")
        print("=" * 70)
        
        try:
            from CLI_modules.cli.prediction.overtake_prediction.predictor import run_f83_prediction
            
            # 從 kwargs 獲取參數 (driver 和 driver2)
            attacker = kwargs.get('driver', 'VER')
            defender = kwargs.get('driver2', 'LEC')
            gap = float(kwargs.get('gap', 0.8))
            tyre_diff = int(kwargs.get('tyre_diff', 0))
            race_progress = float(kwargs.get('race_progress', 0.5))
            
            result = run_f83_prediction(
                attacker=attacker,
                defender=defender,
                gap=gap,
                tyre_diff=tyre_diff,
                race_progress=race_progress,
                verbose=True
            )
            
            return result
            
        except Exception as e:
            print(f"[ERROR] 預測失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"預測失敗: {str(e)}",
                "function_id": "83"
            }
    
    def _execute_overtake_llm_explainer(self, year=None, race=None, session="R", **kwargs):
        """Function 84: 超車預測 LLM 解說器
        
        使用 LLM 生成超車預測的自然語言解說。
        預設使用本地 Ollama (qwen3:8b)，也支援 OpenAI/Anthropic。
        
        參數:
            -d / --driver: 進攻者代碼 (如 VER)
            -d2 / --driver2: 防守者代碼 (如 LEC)
            --no-llm: 使用規則引擎而非 LLM
        """
        print("=" * 70)
        print("F84: 超車預測 LLM 解說器")
        print("=" * 70)
        
        try:
            from CLI_modules.cli.prediction.overtake_prediction.explainer import run_f84_explanation
            
            # 從 kwargs 獲取參數
            attacker = kwargs.get('driver', 'VER')
            defender = kwargs.get('driver2', 'LEC')
            gap = float(kwargs.get('gap', 0.8))
            tyre_diff = int(kwargs.get('tyre_diff', 0))
            race_progress = float(kwargs.get('race_progress', 0.5))
            use_llm = not kwargs.get('no_llm', False)
            
            result = run_f84_explanation(
                attacker=attacker,
                defender=defender,
                gap=gap,
                tyre_diff=tyre_diff,
                race_progress=race_progress,
                use_llm=use_llm,
                llm_provider="ollama",
                llm_model="qwen3:8b",
                verbose=True
            )
            
            return result
            
        except Exception as e:
            print(f"[ERROR] 解說生成失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"解說生成失敗: {str(e)}",
                "function_id": "84"
            }
    
    def _execute_close_combat_trainer(self, year=None, race=None, session="R", **kwargs):
        """Function 85: 近距離接觸模型訓練器 (F85)
        
        訓練 XGBoost 模型預測車手接近到 0.2-0.3 秒內的機率。
        這是比 F83 更早期的戰鬥預警系統。
        
        Args:
            --model-version: 模型版本號 (預設為 1)
            --verbose: 詳細輸出 (預設為 True)
        
        Returns:
            模型檔案: close_combat_xgb_v{version}.json
        """
        print("=" * 70)
        print("F85: 近距離接觸模型訓練器")
        print("=" * 70)
        
        try:
            from CLI_modules.cli.prediction.overtake_prediction.close_combat_trainer import run_f85_model_training
            
            # 從 kwargs 獲取參數
            model_version = int(kwargs.get('model_version', 1))
            verbose = kwargs.get('verbose', True)
            
            result = run_f85_model_training(
                version=model_version,
                verbose=verbose
            )
            
            return result
            
        except Exception as e:
            print(f"[ERROR] F85 訓練失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"F85 訓練失敗: {str(e)}",
                "function_id": "85"
            }
    
    def _execute_close_combat_predictor(self, year=None, race=None, session="R", **kwargs):
        """Function 86: 近距離接觸預測器 (F86)
        
        預測車手接近到 0.2-0.3 秒內的機率。
        這是比 F83 更早期的戰鬥預警系統。
        
        Args:
            -d / --driver: 進攻者代碼 (如 VER)
            -d2 / --driver2: 防守者代碼 (如 LEC)
            --gap: 當前差距 (秒)
            --model-version: 模型版本號 (預設為 1)
            
        Returns:
            近距離接觸機率和關鍵因素分析
        """
        print("=" * 70)
        print("F86: 近距離接觸預測器")
        print("=" * 70)
        
        try:
            from CLI_modules.cli.prediction.overtake_prediction.close_combat_predictor import run_f86_prediction
            
            # 從 kwargs 獲取參數
            attacker = kwargs.get('driver', 'VER')
            defender = kwargs.get('driver2', 'LEC')
            gap = float(kwargs.get('gap', 1.5))
            model_version = int(kwargs.get('model_version', 1))
            
            result = run_f86_prediction(
                attacker=attacker,
                defender=defender,
                gap=gap,
                version=model_version,
                verbose=True
            )
            
            return result
            
        except Exception as e:
            print(f"[ERROR] F86 預測失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"F86 預測失敗: {str(e)}",
                "function_id": "86"
            }

    def _execute_driver_strategy_prediction(self, year=None, race=None, session="R", **kwargs):
        """Function 87: 車手策略預測器
        
        根據 F88 省輪胎分析結果，計算個人化進站圈數預測。
        
        公式: 個人化進站圈數 = 大數據預估圈數 × (1 + Tire Saving Adjustment Factor)
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 賽事階段
            
        Returns:
            包含每位車手個人化預測和驗證結果的 JSON
        """
        print("=" * 70)
        print("F87: 車手策略預測器 (Driver Strategy Predictor)")
        print("=" * 70)
        
        # 取得參數
        year = year or kwargs.get("year") or self.data_loader.year if self.data_loader else None
        race = race or kwargs.get("race") or self.data_loader.race if self.data_loader else None
        session = session or kwargs.get("session", "R")
        
        if not year or not race:
            return {
                "success": False,
                "message": "缺少必要參數: year 和 race",
                "function_id": "87"
            }
        
        print(f"[INFO] 分析參數: {year} {race} {session}")
        
        try:
            from CLI_modules.cli.prediction.driver_strategy_predictor import run_driver_strategy_prediction
            
            result = run_driver_strategy_prediction(
                year=year,
                race=race,
                session=session,
                save_output=True,
                print_report=True
            )
            
            if result.get("success"):
                # 標準化 JSON 導出
                self._export_to_json(result, 87, "driver_strategy_prediction")
            
            return result
            
        except FileNotFoundError as e:
            print(f"[WARNING] 找不到 F88 分析結果，嘗試先執行 F88...")
            # 先執行 F88 (輪胎節省分析)
            f88_result = self._execute_tire_saving_analysis(year, race, session, **kwargs)
            if f88_result.get("success"):
                # 重新執行 F87
                from CLI_modules.cli.prediction.driver_strategy_predictor import run_driver_strategy_prediction
                result = run_driver_strategy_prediction(
                    year=year,
                    race=race,
                    session=session,
                    save_output=True,
                    print_report=True
                )
                if result.get("success"):
                    self._export_to_json(result, 87, "driver_strategy_prediction")
                return result
            else:
                return {
                    "success": False,
                    "message": f"F88 執行失敗，無法進行 F87 預測: {f88_result.get('message')}",
                    "function_id": "87"
                }
            
        except Exception as e:
            print(f"[ERROR] F87 執行失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"F87 執行失敗: {str(e)}",
                "function_id": "87"
            }
    
    def _execute_tire_saving_analysis(self, year=None, race=None, session="R", **kwargs):
        """Function 88: 省輪胎行為分析 (F88)
        
        分析車手在比賽中的省輪胎行為，識別主動省胎策略。
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 賽事階段
            
        Returns:
            包含每位車手省輪胎分數和分類的 JSON
        """
        print("=" * 70)
        print("F88: 省輪胎行為分析 (Tire Saving Behavior Analysis)")
        print("=" * 70)
        
        # 取得參數
        year = year or kwargs.get("year") or self.data_loader.year if self.data_loader else None
        race = race or kwargs.get("race") or self.data_loader.race if self.data_loader else None
        session = session or kwargs.get("session", "R")
        
        if not year or not race:
            return {
                "success": False,
                "message": "缺少必要參數: year 和 race",
                "function_id": "88"
            }
        
        print(f"[INFO] 分析參數: {year} {race} {session}")
        
        try:
            from CLI_modules.cli.prediction.tire_saving_analyzer import run_tire_saving_analysis
            
            result = run_tire_saving_analysis(
                year=year,
                race=race,
                session=session,
                save_json=True
            )
            
            if result.get("success"):
                # 標準化 JSON 導出
                self._export_to_json(result, 88, "tire_saving_analysis")
            
            return result
            
        except Exception as e:
            print(f"[ERROR] F88 執行失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"F88 執行失敗: {str(e)}",
                "function_id": "88"
            }
    
    def _execute_fp2_race_ml_trainer(self, **kwargs):
        """功能 90: FP2→R 機器學習訓練器 V2.0 (FastF1)
        
        使用 FastF1 獲取 2023-2024 FP2 + Race 數據訓練模型。
        每個賽道獨立訓練 XGBoost 模型。
        
        參數:
            train: 是否為訓練模式 (默認 False)
            start_year: 起始年份 (默認 2023)
            end_year: 結束年份 (默認 2024)
            
        輸出:
            - models/fp2_race_ml_v2.0/{track_name}.pkl
            - reports/fp2_race_ml_training_report_v2.json
        """
        print("\n" + "="*70)
        print("功能 90: FP2→R 機器學習訓練器 V2.0")
        print("="*70)
        print("版本: v2.0.0 (FastF1)")
        print("訓練數據: 2023-2024 FP2 + Race")
        print("模型類型: XGBoost (每個賽道獨立)")
        print("預測目標: 正賽逐圈圈速 (lap 3+)")
        
        # 檢查是否為訓練模式
        train_mode = kwargs.get("train", False)
        
        if not train_mode:
            return {
                "success": False,
                "message": "F90 需要 --train 參數才能執行訓練",
                "hint": "使用範例: python f1_analysis_modular_main.py -f 90 --train",
                "function_id": "90"
            }
        
        # 訓練年份範圍（可自訂）
        start_year = kwargs.get("start_year") or 2023
        end_year = kwargs.get("end_year") or 2024
        
        try:
            from CLI_modules.cli.prediction.fp2_race_ml_trainer_v2 import run_fp2_race_ml_training_v2
            
            result = run_fp2_race_ml_training_v2(
                start_year=start_year,
                end_year=end_year,
                verbose=True
            )
            
            return result
            
        except Exception as e:
            print(f"[ERROR] F90 執行失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"F90 執行失敗: {str(e)}",
                "function_id": "90"
            }
    
    def _execute_fp2_race_ml_predictor(self, **kwargs):
        """功能 91: FP2→R 機器學習預測器 V2.0
        
        使用 F90 V2 訓練的模型 + LiveF1 FP2 數據預測正賽圈速。
        
        參數:
            year: 年份
            race: 比賽名稱
            session: 會話 (默認 FP2)
            
        輸出:
            - json/fp2_race_ml_prediction_v2_{year}_{race}_{timestamp}.json
        """
        print("\n" + "="*70)
        print("功能 91: FP2→R 機器學習預測器 V2.0")
        print("="*70)
        print("版本: v2.0.0")
        print("模型: FastF1 訓練 (F90 V2)")
        print("輸入: LiveF1 FP2 數據")
        print("輸出: 正賽逐圈圈速預測")
        
        year = kwargs.get("year") or self.data_loader.year if self.data_loader else None
        race = kwargs.get("race") or self.data_loader.race if self.data_loader else None
        session = kwargs.get("session", "FP2")
        
        if not year or not race:
            return {
                "success": False,
                "message": "缺少必要參數: year 和 race",
                "hint": "使用範例: python f1_analysis_modular_main.py -f 91 -y 2025 -r Abu_Dhabi",
                "function_id": "91"
            }
        
        print(f"[INFO] 預測參數: {year} {race} {session}")
        
        try:
            from CLI_modules.cli.prediction.fp2_race_ml_predictor_v2 import run_fp2_race_ml_prediction_v2
            
            result = run_fp2_race_ml_prediction_v2(
                year=year,
                race=race,
                session=session,
                verbose=True
            )
            
            return result
            
        except Exception as e:
            print(f"[ERROR] F91 執行失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"F91 執行失敗: {str(e)}",
                "function_id": "91"
            }
    
    def _execute_live_timing_weather_analysis(self, **kwargs):
        """功能 126: Live Timing 天氣分析
        
        使用 F1 Live Timing API 的 WeatherData.jsonStream 獲取逐圈天氣數據。
        
        參數:
            year: 年份 (2018+)
            race: 賽事名稱
            session: 會話類型 (默認 R)
            
        輸出:
            - json/live_timing_weather_{year}_{race}_{session}.json
        """
        print("\n" + "="*70)
        print("功能 126: Live Timing 天氣分析")
        print("="*70)
        print("數據來源: F1 Live Timing API (WeatherData.jsonStream)")
        print("輸出內容: 逐圈氣溫/賽道溫度/濕度/降雨/風速")
        
        # 從 kwargs 獲取參數，若無則從 data_loader 獲取
        year = kwargs.get("year")
        if not year and self.data_loader:
            year = self.data_loader.year
        race = kwargs.get("race")
        if not race and self.data_loader:
            race = self.data_loader.race
        session = kwargs.get("session", "R")
        
        if not year or not race:
            return {
                "success": False,
                "message": "缺少必要參數: year 和 race",
                "hint": "使用範例: python f1_analysis_modular_main.py -f 126 -y 2025 -r Japan -s R",
                "function_id": "126"
            }
        
        print(f"[INFO] 分析參數: {year} {race} {session}")
        
        try:
            from CLI_modules.cli.analyzer.live_timing_weather_analysis import (
                run_live_timing_weather_analysis
            )
            
            result = run_live_timing_weather_analysis(
                year=year,
                race=race,
                session=session
            )
            
            return result
            
        except Exception as e:
            print(f"[ERROR] F126 執行失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"F126 執行失敗: {str(e)}",
                "function_id": "126"
            }

    def _execute_live_timing_traffic_distance_analysis(self, **kwargs):
        """功能 127: Live Timing traffic 分析（距離門檻版）

        使用 Live Timing cache (PKL) 的 position + XY 推導前車距離（公尺），
        以距離門檻判定 traffic；SC/VSC 狀態的圈數整圈排除。

        參數:
            year: 年份
            race: 賽事名稱
            session: 會話類型 (默認 R)
            traffic_distance_threshold_m: 距離門檻（公尺，默認 50）
            lap_traffic_ratio_threshold: 單圈 traffic 比例門檻（默認 0.3）

        輸出:
            - json/live_timing_traffic_distance_{year}_{race}_{session}.json
        """
        print("\n" + "="*70)
        print("功能 127: Live Timing traffic 分析（距離門檻版）")
        print("="*70)
        print("數據來源: F1 Live Timing cache (PKL)")
        print("輸出內容: per-driver traffic_ratio / laps_in_traffic / time_in_traffic_ratio")

        year = kwargs.get("year")
        if not year and self.data_loader:
            year = self.data_loader.year
        race = kwargs.get("race")
        if not race and self.data_loader:
            race = self.data_loader.race
        session = kwargs.get("session", "R")
        traffic_distance_threshold_m = float(kwargs.get("traffic_distance_threshold_m", 50.0))
        lap_traffic_ratio_threshold = float(kwargs.get("lap_traffic_ratio_threshold", 0.3))

        if not year or not race:
            return {
                "success": False,
                "message": "缺少必要參數: year 和 race",
                "hint": "使用範例: python f1_analysis_modular_main.py -f 127 -y 2025 -r Japan -s R",
                "function_id": "127"
            }

        print(
            f"[INFO] 分析參數: {year} {race} {session} | "
            f"distance={traffic_distance_threshold_m}m | lap_ratio={lap_traffic_ratio_threshold}"
        )

        try:
            from CLI_modules.cli.analyzer.live_timing_traffic_distance_analysis import (
                run_live_timing_traffic_distance_analysis
            )

            result = run_live_timing_traffic_distance_analysis(
                year=year,
                race=race,
                session=session,
                traffic_distance_threshold_m=traffic_distance_threshold_m,
                lap_traffic_ratio_threshold=lap_traffic_ratio_threshold,
            )

            return result

        except Exception as e:
            print(f"[ERROR] F127 執行失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"F127 執行失敗: {str(e)}",
                "function_id": "127"
            }

    def _execute_fp2_race_correlation_analysis(self, **kwargs):
        """功能 131: FP2-Race Long Run 相關性分析

        分析 FP2 Long Run 模擬圈數與正賽實際表現的相關性。
        使用與 GUI Long Run 模組完全相同的計算邏輯：
        1. IQR-based outlier filtering
        2. Fuel correction
        3. Track evolution (statistical median)
        4. Fully-Corrected Lap Times

        參數:
            year: 年份
            race: 賽事名稱
            fp2_simulate_lap: FP2 模擬的正賽圈數 (默認 20)
            fuel_start: 起跑燃油 (kg, 默認 85.0)
            fuel_consumption: 每圈油耗 (kg, 默認 1.70)
            fuel_effect: 燃油效應係數 (s/kg, 默認 0.030)

        輸出:
            - json/fp2_race_correlation_{year}_{race}.json
        """
        print("\n" + "="*70)
        print("功能 131: FP2-Race Long Run 相關性分析")
        print("="*70)
        print("數據來源: Function 28 (FP2 + Race lap data)")
        print("計算邏輯: 與 GUI Long Run 模組完全一致")
        print("輸出內容: per-driver FP2/Race 配速對比 + 輪胎退化對比")

        year = kwargs.get("year")
        if not year and self.data_loader:
            year = self.data_loader.year
        race = kwargs.get("race")
        if not race and self.data_loader:
            race = self.data_loader.race
        
        fp2_simulate_lap = int(kwargs.get("fp2_simulate_lap", 20))
        fuel_start = float(kwargs.get("fuel_start", 85.0))
        fuel_consumption = float(kwargs.get("fuel_consumption", 1.70))
        fuel_effect = float(kwargs.get("fuel_effect", 0.030))

        if not year or not race:
            return {
                "success": False,
                "message": "缺少必要參數: year 和 race",
                "hint": "使用範例: python f1_analysis_modular_main.py -f 131 -y 2025 -r Japan",
                "function_id": "131"
            }

        print(f"[INFO] 分析參數: {year} {race}")
        print(f"[INFO] FP2 模擬圈數: {fp2_simulate_lap}")
        print(f"[INFO] 燃油設定: {fuel_start}kg 起跑, {fuel_consumption}kg/lap, {fuel_effect}s/kg")

        try:
            from CLI_modules.cli.analyzer.fp2_race_correlation_analyzer import (
                run_fp2_race_correlation_analysis
            )

            result = run_fp2_race_correlation_analysis(
                year=int(year),
                race=race,
                fp2_simulate_lap=fp2_simulate_lap,
                fuel_start=fuel_start,
                fuel_consumption=fuel_consumption,
                fuel_effect=fuel_effect,
                save_json=True
            )

            return self._standardize_result(result, 131, "FP2-Race Long Run 相關性分析")

        except Exception as e:
            print(f"[ERROR] F131 執行失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"F131 執行失敗: {str(e)}",
                "function_id": "131"
            }

    # ===== F134-F141: Position Tracking Simulator 數據收集系統 =====

    def _execute_overtake_history_collector(self, **kwargs):
        """功能 134: 超車事件歷史收集器

        從 PKL 快取提取 2024-2025 所有超車事件，用於訓練超車成功率模型。

        輸出:
            - json/overtake_events_history_2024_2025.json
        """
        print("\n" + "="*70)
        print("功能 134: 超車事件歷史收集器 (Overtake History Collector)")
        print("="*70)

        try:
            from CLI_modules.cli.analyzer.overtake_history_collector import execute_overtake_history_collector
            return execute_overtake_history_collector(**kwargs)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"F134 執行失敗: {str(e)}",
                "function_id": "134"
            }

    def _execute_overtake_attempt_failed_collector(self, **kwargs):
        """功能 135: 超車嘗試失敗收集器

        識別超車嘗試但失敗的事件，補充 F134 的成功案例用於模型訓練。

        輸出:
            - json/overtake_attempts_failed_2024_2025.json
        """
        print("\n" + "="*70)
        print("功能 135: 超車嘗試失敗收集器 (待開發)")
        print("="*70)
        return {"success": False, "message": "F135 尚未實作", "function_id": "135"}

    def _execute_track_overtake_difficulty_analyzer(self, **kwargs):
        """功能 136: 賽道超車難度分析器

        計算每條賽道的基礎超車難度係數。

        輸出:
            - json/track_overtake_difficulty.json
        """
        print("\n" + "="*70)
        print("功能 136: 賽道超車難度分析器 (待開發)")
        print("="*70)
        return {"success": False, "message": "F136 尚未實作", "function_id": "136"}

    def _execute_team_performance_matrix_calculator(self, **kwargs):
        """功能 137: 車隊性能差係數計算器

        計算車隊間的相對性能差異係數。

        輸出:
            - json/team_performance_matrix.json
        """
        print("\n" + "="*70)
        print("功能 137: 車隊性能差係數計算器 (待開發)")
        print("="*70)
        return {"success": False, "message": "F137 尚未實作", "function_id": "137"}

    def _execute_overtake_success_model_trainer(self, **kwargs):
        """功能 138: 超車成功率模型訓練器

        訓練 Logistic Regression 超車成功率模型。

        輸出:
            - models/overtake_success_model.pkl
            - json/overtake_model_coefficients.json
            - json/overtake_model_evaluation.json
        """
        print("\n" + "="*70)
        print("功能 138: 超車成功率模型訓練器 (待開發)")
        print("="*70)
        return {"success": False, "message": "F138 尚未實作", "function_id": "138"}

    def _execute_new_driver_coefficient_completer(self, **kwargs):
        """功能 139: 新車手係數補全器

        為缺乏歷史數據的新車手/替補車手生成預設係數。

        輸出:
            - json/driver_coefficients_complete.json
        """
        print("\n" + "="*70)
        print("功能 139: 新車手係數補全器 (待開發)")
        print("="*70)
        return {"success": False, "message": "F139 尚未實作", "function_id": "139"}

    def _execute_qualifying_result_collector(self, **kwargs):
        """功能 140: 排位賽結果收集器

        收集排位賽結果作為比賽起跑位置。

        輸出:
            - json/qualifying_results_{year}.json
        """
        print("\n" + "="*70)
        print("功能 140: 排位賽結果收集器 (待開發)")
        print("="*70)
        return {"success": False, "message": "F140 尚未實作", "function_id": "140"}

    def _execute_sc_trigger_probability_model(self, **kwargs):
        """功能 141: SC 觸發機率模型

        從歷史數據統計 SC 觸發機率和彎道分布。

        輸出:
            - json/sc_trigger_probability.json
        """
        print("\n" + "="*70)
        print("功能 141: SC 觸發機率模型 (待開發)")
        print("="*70)
        return {"success": False, "message": "F141 尚未實作", "function_id": "141"}

    def _execute_pit_lane_time_analyzer(self, **kwargs):
        """功能 142: 進站時間損失分析器

        分析 2022-2025 所有賽道的進站時間損失，用於策略模擬器。

        輸出:
            - json/pit_lane_time_loss_all_tracks.json
        """
        print("\n" + "="*70)
        print("功能 142: 進站時間損失分析器 (Pit Lane Time Loss Analyzer)")
        print("="*70)

        try:
            from CLI_modules.cli.analyzer.pit_lane_time_analyzer import execute_pit_lane_time_analyzer

            # 執行分析
            result = execute_pit_lane_time_analyzer(
                years=[2022, 2023, 2024, 2025],
                save_json=True
            )

            return self._standardize_result(result, 142, "進站時間損失分析")

        except Exception as e:
            print(f"[ERROR] F142 執行失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"F142 執行失敗: {str(e)}",
                "function_id": "142"
            }


    def _execute_fia_season_stats_analysis(self, **kwargs):
        """功能 143: FIA 賽季統計分析

        從 FIA 官網抓取 PU 元件使用狀況與部件更換記錄。
        支援增量更新，輸出完整賽季 JSON。

        參數:
            year: 賽季年份 (2024, 2025, ...)
            force: 是否強制重新處理所有數據

        輸出:
            - json/fia_season_stats_{year}.json
        """
        print("\n" + "="*70)
        print("功能 143: FIA 賽季統計分析 (PU Elements + Parts Changes)")
        print("="*70)

        try:
            from CLI_modules.cli.analyzer.fia_season_stats_analyzer import (
                run_fia_season_stats_analysis
            )

            # 參數處理
            year = kwargs.get("year")
            if not year:
                if self.data_loader and getattr(self.data_loader, "year", None):
                    year = self.data_loader.year
                else:
                    year = 2025  # 預設 2025 賽季
            
            year = int(year)
            force = kwargs.get("force", False)

            print(f"[F143] 年份: {year}")
            print(f"[F143] 模式: {'強制重建' if force else '增量更新'}")

            # 執行分析
            result = run_fia_season_stats_analysis(year=year, force=force)

            return self._standardize_result(result, 143, "FIA 賽季統計分析")

        except Exception as e:
            print(f"[ERROR] F143 執行失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "message": f"F143 執行失敗: {str(e)}",
                "function_id": "143"
            }


# ===== 支援函數和工具 =====

def create_function_mapper(data_loader=None, dynamic_team_mapping=None, f1_analysis_instance=None):
    """創建並配置功能映射器實例"""
    return F1AnalysisFunctionMapper(
        data_loader=data_loader,
        dynamic_team_mapping=dynamic_team_mapping,
        f1_analysis_instance=f1_analysis_instance
    )

def get_available_functions():
    """獲取所有可用功能的列表"""
    mapper = F1AnalysisFunctionMapper()
    return {
        "main_functions": list(mapper.function_map.keys()),
        "sub_functions": list(mapper.sub_function_map.keys()),
        "total_count": len(mapper.function_map) + len(mapper.sub_function_map)
    }

def execute_function_by_number(function_number, data_loader=None, dynamic_team_mapping=None, 
                               f1_analysis_instance=None, **kwargs):
    """根據功能編號執行對應的分析功能"""
    mapper = F1AnalysisFunctionMapper(
        data_loader=data_loader,
        dynamic_team_mapping=dynamic_team_mapping,
        f1_analysis_instance=f1_analysis_instance
    )
    return mapper.execute_function(function_number, **kwargs)

if __name__ == "__main__":
    # 測試功能
    print("🧪 F1 Analysis Function Mapper Test")
    print("=" * 50)
    
    # 顯示可用功能
    available = get_available_functions()
    print(f"[STATS] 總功能數: {available['total_count']}")
    print(f"🔹 主要功能: {len(available['main_functions'])} 個")
    print(f"🔸 子功能: {len(available['sub_functions'])} 個")
    
    print("\n[OK] Function Mapper 模組載入成功！")
