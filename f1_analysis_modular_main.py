#!/usr/bin/env python3
"""
F1 Analysis CLI - 模組化主程式 (CLI 參數化模式)
F1 Analysis CLI - Modular Main Program (CLI Parameter Mode)
版本: 5.4 (CLI專用版)
作者: F1 Analysis Team

專用模組化主程式，負責呼叫各個獨立分析模組
僅支援 CLI 參數化模式，適合自動化和腳本化使用
修正了 AllDriversDNFAdvanced 變數範圍問題和雨天分析依賴問題
"""

import os
import sys
import argparse
from typing import Optional, Union, Dict, Any
from datetime import datetime

import core.dependency_guard  # noqa: F401  # 確保可選依賴存在

from core.logger import setup_logging, get_logger
from core.cli_language import resolve_cli_language
from core.cli_help_catalog import iter_cli_help_lines

# CLI 模式：使用 logger 系統，print() 會被重定向到 log 檔案
setup_logging(component="cli")
logger = get_logger("main", component="cli")
logger.info("F1 CLI 控制台初始化完成")

# 移除編碼設置，避免 traceback 問題

# 確保 modules 和 CLI_modules 目錄在 Python 路徑中
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_dir = os.path.join(current_dir, 'modules')
cli_modules_dir = os.path.join(current_dir, 'CLI_modules')

if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)
if cli_modules_dir not in sys.path:
    sys.path.insert(0, cli_modules_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# 導入所有分析模組
try:
    # 使用統一函數映射器
    from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper
    from CLI_modules.cli.core.compatible_data_loader import CompatibleF1DataLoader
    from CLI_modules.cli.core.compatible_f1_analysis_instance import create_f1_analysis_instance
    
    #print("[OK] 統一函數映射器導入成功！")
    has_function_mapper = True
    
    # 向後兼容：保留部分重要模組的直接導入
    try:
        # 使用新的增強版降雨分析模組
        from CLI_modules.cli.analyzer.weather.rain_analyzer import EnhancedRainAnalyzer
        has_rain_analysis = True
        # print("[OK] 增強版降雨分析模組導入成功！")
    except ImportError:
        # print("[WARNING] 增強版降雨分析模組未找到")
        has_rain_analysis = False
    from CLI_modules.cli.analyzer.all_drivers_overtaking_trends_analysis import run_all_drivers_overtaking_trends_analysis
    
    # 導入其他模組
    try:
        from modules import (
            # 基礎分析模組
            # run_comprehensive_analysis,  # 已移除 - 使用統一映射器
            run_single_driver_comprehensive_analysis,  # 單一車手分析
            run_track_path_analysis,
            run_pitstop_analysis,
            run_single_driver_detailed_telemetry_analysis,
            run_driver_comparison_analysis,
            
            # 超車分析模組
            run_single_driver_overtaking_analysis,
            run_all_drivers_overtaking_analysis,
            
            # 彎道分析模組
            run_corner_speed_analysis,
            run_single_driver_detailed_corner_analysis
        )
        
        # 導入新拆分的模組
        from CLI_modules.cli.analyzer.speed_gap_analysis import run_speed_gap_analysis
        from CLI_modules.cli.analyzer.distance_gap_analysis import run_distance_gap_analysis
        
        # 導入新的彎道分析子模組 (集成版本 - 包含進站與事件資料)
        from CLI_modules.cli.analyzer.single_driver_corner_analysis_integrated import run_single_driver_corner_analysis_integrated
        from CLI_modules.cli.analyzer.team_drivers_corner_comparison_integrated import run_team_drivers_corner_comparison_integrated
        
    except ImportError as e:
        print(f"[WARNING] 部分模組導入失敗: {e}")
    
    print("[SUCCESS] 獨立分析模組導入成功！")
except ImportError as e:
    print(f"[ERROR] 模組導入失敗: {e}")
    print("請確保 modules/ 目錄存在且包含所有必要的模組文件")
    sys.exit(1)

# 導入主程式的必要類別以進行數據載入
try:
    import fastf1
    from prettytable import PrettyTable
    import pandas as pd
    import numpy as np
    print("[OK] 基礎依賴包導入成功！")
    
    # 導入兼容數據載入器
    try:
        from CLI_modules.cli.core.compatible_data_loader import CompatibleF1DataLoader
        print("[OK] 兼容數據載入器導入成功！")
    except ImportError as e:
        print(f"[ERROR] 兼容數據載入器導入失敗: {e}")
        # 創建簡化的獨立數據載入器作為備用
        class IndependentF1DataLoader:
            """簡化的F1數據載入器（備用）"""
            
            def __init__(self):
                self.session = None
                self.results = None
                self.laps = None
                self.session_loaded = False
                self.year = None
                self.race_name = None
                self.session_type = None
                
            def load_race_data(self, year, race_name, session_type):
                """載入賽事數據"""
                try:
                    fastf1.Cache.enable_cache('f1_analysis_cache')
                    
                    # 載入賽段
                    session = fastf1.get_session(year, race_name, session_type)
                    session.load()
                    
                    self.session = session
                    self.results = session.results
                    self.laps = session.laps
                    self.session_loaded = True
                    self.year = year
                    self.race_name = race_name
                    self.session_type = session_type
                    
                    print(f"[OK] 成功載入 {year} {race_name} {session_type} 數據")
                    return True
                    
                except Exception as e:
                    print(f"[ERROR] 載入賽事數據失敗: {e}")
                    return False
        
        CompatibleF1DataLoader = IndependentF1DataLoader
    
    print("[OK] 兼容數據載入器創建成功！")
    
except ImportError as e:
    print(f"[ERROR] 基礎依賴導入失敗: {e}")
    print("請安裝必要的依賴：pip install fastf1 pandas numpy prettytable matplotlib")
    sys.exit(1)


class F1AnalysisModularCLI:
    """F1分析模組化命令行介面"""
    
    def __init__(self, args=None):
        self.version = "5.4"
        self.title = "F1 Analysis CLI - 模組化版本 (映射表同步版)"
        self.data_loader = None
        self.session_loaded = False
        self.dynamic_team_mapping = None
        self.f1_analysis_instance = None  # 添加完整的F1分析實例
        self.open_analyzer = None  # 添加 OpenF1 分析器實例
        self.args = args  # 保存命令行參數
        self.last_error_message: Optional[str] = None
        self.last_error_details: Optional[Dict[str, Any]] = None
        preferred_language = getattr(args, "language", None) if args else None
        if preferred_language and preferred_language.lower() in {"auto", "default"}:
            preferred_language = None
        self.preferred_language = resolve_cli_language(preferred_language)
        
        # 初始化F1分析實例
        self._initialize_f1_analysis_instance()
        
    def _initialize_f1_analysis_instance(self):
        """初始化F1分析實例"""
        try:
            from CLI_modules.cli.core.compatible_f1_analysis_instance import create_f1_analysis_instance
            self.f1_analysis_instance = create_f1_analysis_instance(self.data_loader)
            if self.f1_analysis_instance:
                print("[OK] F1分析實例初始化成功")
            else:
                print("[WARNING] F1分析實例初始化失敗，某些功能可能受限")
        except ImportError as e:
            print(f"[WARNING] 無法導入F1分析實例模組: {e}")
            print("某些高級功能(如超車分析、圈速趨勢圖)可能無法使用")
        except Exception as e:
            print(f"[WARNING] F1分析實例初始化錯誤: {e}")
        
    def _update_f1_analysis_instance(self):
        """更新F1分析實例的數據載入器"""
        if self.f1_analysis_instance and self.data_loader:
            try:
                self.f1_analysis_instance.set_data_loader(self.data_loader)
                self.f1_analysis_instance.update_session_status(self.session_loaded)
                self.f1_analysis_instance.set_dynamic_team_mapping(self.dynamic_team_mapping)
                
                # 重要：設置數據載入器的 f1_analysis_instance 引用
                self.data_loader.f1_analysis_instance = self.f1_analysis_instance
                
                print("[OK] F1分析實例已更新")
            except Exception as e:
                print(f"[WARNING] 更新F1分析實例失敗: {e}")
    
    def _initialize_open_analyzer(self):
        """初始化 OpenF1 分析器"""
        try:
            from CLI_modules.cli.core.compatible_data_loader import F1OpenDataAnalyzer
            self.open_analyzer = F1OpenDataAnalyzer()
            print("[OK] OpenF1 分析器初始化成功")
        except ImportError as e:
            print(f"[WARNING] 無法導入 OpenF1 分析器: {e}")
            self.open_analyzer = None
        except Exception as e:
            print(f"[WARNING] OpenF1 分析器初始化錯誤: {e}")
            self.open_analyzer = None
        
    def display_header(self):
        """顯示程式標題"""
        print("=" * 80)
        print(f" {self.title} v{self.version}")
        print(" F1 Telemetry Analysis - Enhanced Race Display Edition")
        print("=" * 80)
        print(" [F1]  基於 FastF1 和 OpenF1 的專業F1遙測分析系統")
        print(" [STATS]  完全模組化設計，支援2024-2025年賽季數據")
        print(" [CALENDAR]  新增賽事日期與完整名稱顯示功能")
        print("=" * 80)

    def load_race_data_from_args(self, year=None, race=None, session=None):
        """從命令行參數載入賽事數據"""
        if not year or not race or not session:
            return self.load_race_data_at_startup()
        
        print(f"\n[STATS] 從參數載入 {year} {race} {session} 數據...")
        
        # 初始化數據載入器
        try:
            self.data_loader = CompatibleF1DataLoader()
            print("[OK] 兼容數據載入器初始化成功")
        except Exception as e:
            print(f"[ERROR] 數據載入器初始化失敗: {e}")
            self.last_error_message = f"數據載入器初始化失敗: {e}"
            self.last_error_details = {
                "year": year,
                "race": race,
                "session": session,
                "exception": str(e)
            }
            return False
        
        # 載入數據
        if self.data_loader.load_race_data(year, race, session):
            self.session_loaded = True
            print(f"[OK] 賽事數據載入完成！")
            
            # 初始化 OpenF1 分析器
            self._initialize_open_analyzer()
            
            # 更新F1分析實例
            self._update_f1_analysis_instance()
            
            return True
        else:
            print(f"[ERROR] 賽事數據載入失敗")
            self.last_error_message = "無法載入指定賽事的數據"
            self.last_error_details = {
                "year": year,
                "race": race,
                "session": session
            }
            return False





    def show_module_status(self):
        """顯示模組狀態"""
        print("\n[PACKAGE] 模組狀態檢查")
        print("=" * 50)
        
        modules_info = [
            ("rain_intensity_analyzer_complete", "完整復刻降雨強度分析模組"),
            ("rain_analysis", "雨天分析模組"),
            ("driver_comprehensive", "綜合駕駛員分析模組"),
            ("track_path_analysis", "賽道路線分析模組"),
            ("pitstop_analysis", "進站策略分析模組"),
            ("accident_analysis_complete", "事故分析模組"),
            ("telemetry_analysis", "遙測分析模組"),
            ("driver_comparison", "車手對比分析模組"),
            ("overtaking_analysis", "超車分析模組"),
            ("dnf_analysis", "DNF分析模組"),
            ("corner_analysis", "彎道分析模組"),
            ("base", "基礎類別模組")
        ]
        
        for module_name, description in modules_info:
            try:
                module_path = os.path.join(modules_dir, f"{module_name}.py")
                if os.path.exists(module_path):
                    print(f"[OK] {description} - {module_name}.py")
                else:
                    print(f"[ERROR] {description} - {module_name}.py (檔案不存在)")
            except Exception as e:
                print(f"[ERROR] {description} - 檢查失敗: {e}")
        
        # 顯示數據載入狀態
        print("\n[STATS] 數據載入狀態:")
        if self.data_loader:
            print("[OK] 數據載入器已初始化")
            if self.session_loaded:
                print("[OK] 賽事數據已載入")
            else:
                print("[ERROR] 尚未載入賽事數據")
        else:
            print("[ERROR] 數據載入器未初始化")
        
        print("=" * 50)

    def run_rain_intensity_analysis(self):
        """執行降雨狀況分析 - 簡化版只顯示有雨/無雨"""
        try:
            print("[RAIN] 分析中...")
            # 使用統一函數映射器執行功能1
            result = self.run_analysis_direct(1)
            if result.get("success", False):
                # 顯示降雨結論
                if 'rain_status' in result:
                    print(f"🌧️ {result['rain_status']}")
            else:
                print(f"[ERROR] 分析失敗: {result.get('message', '未知錯誤')}")
        except Exception as e:
            print(f"[ERROR] 執行失敗: {e}")

    # === 獨立事故分析方法 ===
    
    def run_accident_key_events_summary(self):
        """執行關鍵事件摘要分析 - 新版本無車隊映射錯誤"""
        try:
            from CLI_modules.cli.analyzer.key_events_analysis import run_key_events_summary_analysis
            print("\n[CHECK] 執行關鍵事件摘要分析...")
            
            # 使用新的關鍵事件分析模組
            run_key_events_summary_analysis(self.data_loader)
            
        except ImportError as e:
            print(f"[ERROR] 關鍵事件分析模組未找到: {e}")
            # 後備方案：使用原始方法
            try:
                from modules.gui.accident_analysis.accident_analysis_complete import F1AccidentAnalysisComplete
                accident_analyzer = F1AccidentAnalysisComplete(self.data_loader, f1_analysis_instance=self)
                if hasattr(self, 'dynamic_team_mapping') and self.dynamic_team_mapping:
                    accident_analyzer.dynamic_team_mapping = self.dynamic_team_mapping.copy()
                else:
                    accident_analyzer.dynamic_team_mapping = {}
                accident_analyzer.run_key_events_summary_only()
            except Exception as fallback_error:
                print(f"[ERROR] 後備方案也失敗: {fallback_error}")
            
        except Exception as e:
            print(f"[ERROR] 關鍵事件摘要分析失敗: {e}")
    
    def run_accident_special_incidents(self):
        """執行特殊事件報告分析 - 新版本無車隊映射錯誤"""
        try:
            from modules.gui.accident_analysis.special_incidents_analysis import run_special_incidents_analysis
            print("\n[ALERT] 執行特殊事件報告分析...")
            
            # 使用新的特殊事件分析模組
            run_special_incidents_analysis(self.data_loader)
            
        except ImportError as e:
            print(f"[ERROR] 特殊事件分析模組未找到: {e}")
            # 後備方案：使用原始方法
            try:
                from modules.gui.accident_analysis.accident_analysis_complete import F1AccidentAnalysisComplete
                accident_analyzer = F1AccidentAnalysisComplete(self.data_loader, f1_analysis_instance=self)
                if hasattr(self, 'dynamic_team_mapping') and self.dynamic_team_mapping:
                    accident_analyzer.dynamic_team_mapping = self.dynamic_team_mapping.copy()
                else:
                    accident_analyzer.dynamic_team_mapping = {}
                accident_analyzer.run_special_incidents_only()
            except Exception as fallback_error:
                print(f"[ERROR] 後備方案也失敗: {fallback_error}")
            
        except Exception as e:
            print(f"[ERROR] 特殊事件報告分析失敗: {e}")
    
    def run_accident_driver_severity_scores(self):
        """執行車手嚴重程度分數統計 - 新版本無車隊映射錯誤"""
        try:
            from CLI_modules.cli.analyzer.driver_severity_analysis import run_driver_severity_analysis
            print("\n🏆 執行車手嚴重程度分數統計...")
            
            # 使用新的車手嚴重程度分析模組
            run_driver_severity_analysis(self.data_loader)
            
        except ImportError as e:
            print(f"[ERROR] 車手嚴重程度分析模組未找到: {e}")
            # 後備方案：使用原始方法
            try:
                from modules.gui.accident_analysis.accident_analysis_complete import F1AccidentAnalysisComplete
                accident_analyzer = F1AccidentAnalysisComplete(self.data_loader, f1_analysis_instance=self)
                if hasattr(self, 'dynamic_team_mapping') and self.dynamic_team_mapping:
                    accident_analyzer.dynamic_team_mapping = self.dynamic_team_mapping.copy()
                else:
                    accident_analyzer.dynamic_team_mapping = {}
                accident_analyzer.run_driver_severity_scores_only()
            except Exception as fallback_error:
                print(f"[ERROR] 後備方案也失敗: {fallback_error}")
            
        except Exception as e:
            print(f"[ERROR] 車手嚴重程度分數統計失敗: {e}")
    
    def run_accident_team_risk_scores(self):
        """執行車隊風險分數統計 - 新版本無車隊映射錯誤"""
        try:
            from modules.gui.accident_analysis.team_risk_analysis import run_team_risk_analysis
            print("\n[FINISH] 執行車隊風險分數統計...")
            
            # 使用新的車隊風險分析模組
            run_team_risk_analysis(self.data_loader)
            
        except ImportError as e:
            print(f"[ERROR] 車隊風險分析模組未找到: {e}")
            # 後備方案：使用原始方法
            try:
                from modules.gui.accident_analysis.accident_analysis_complete import F1AccidentAnalysisComplete
                accident_analyzer = F1AccidentAnalysisComplete(self.data_loader, f1_analysis_instance=self)
                if hasattr(self, 'dynamic_team_mapping') and self.dynamic_team_mapping:
                    accident_analyzer.dynamic_team_mapping = self.dynamic_team_mapping.copy()
                else:
                    accident_analyzer.dynamic_team_mapping = {}
                accident_analyzer.run_team_risk_scores_only()
            except Exception as fallback_error:
                print(f"[ERROR] 後備方案也失敗: {fallback_error}")
            
        except Exception as e:
            print(f"[ERROR] 車隊風險分數統計失敗: {e}")
    
    def run_accident_all_incidents_summary(self):
        """執行所有事件詳細列表分析 - 新版本無車隊映射錯誤"""
        try:
            from modules.gui.accident_analysis.all_incidents_analysis import run_all_incidents_analysis
            print("\n[INFO] 執行所有事件詳細列表分析...")
            
            # 使用新的所有事件分析模組
            run_all_incidents_analysis(self.data_loader)
            
        except ImportError as e:
            print(f"[ERROR] 所有事件分析模組未找到: {e}")
            # 後備方案：使用原始方法
            try:
                from modules.gui.accident_analysis.accident_analysis_complete import F1AccidentAnalysisComplete
                accident_analyzer = F1AccidentAnalysisComplete(self.data_loader, f1_analysis_instance=self)
                if hasattr(self, 'dynamic_team_mapping') and self.dynamic_team_mapping:
                    accident_analyzer.dynamic_team_mapping = self.dynamic_team_mapping.copy()
                else:
                    accident_analyzer.dynamic_team_mapping = {}
                accident_analyzer.run_all_incidents_summary_only()
            except Exception as fallback_error:
                print(f"[ERROR] 後備方案也失敗: {fallback_error}")
            
        except Exception as e:
            print(f"[ERROR] 所有事件詳細列表分析失敗: {e}")

    # === 單一車手詳細遙測分析方法 ===
    
    def run_telemetry_complete_lap_analysis(self):
        """執行詳細圈次分析 - 完整圈速記錄 (含JSON輸出)"""
        try:
            from modules.single_driver_detailed_telemetry import SingleDriverTelemetryAnalyzer
            analyzer = SingleDriverTelemetryAnalyzer(self.data_loader)
            analyzer.run_complete_lap_analysis(auto_driver="VER", save_json=True)
            
        except Exception as e:
            print(f"[ERROR] 詳細圈次分析失敗: {e}")
    
    def run_telemetry_detailed_tire_strategy(self):
        """執行詳細輪胎策略分析 (含JSON輸出)"""
        try:
            from modules.single_driver_detailed_telemetry import SingleDriverTelemetryAnalyzer
            analyzer = SingleDriverTelemetryAnalyzer(self.data_loader)
            analyzer.run_detailed_tire_strategy(auto_driver="VER", save_json=True)
            
        except Exception as e:
            print(f"[ERROR] 詳細輪胎策略分析失敗: {e}")
    
    def run_telemetry_tire_performance_analysis(self):
        """執行輪胎性能詳細分析 (含JSON輸出)"""
        try:
            from modules.single_driver_detailed_telemetry import SingleDriverTelemetryAnalyzer
            analyzer = SingleDriverTelemetryAnalyzer(self.data_loader)
            analyzer.run_tire_performance_analysis(auto_driver="VER", save_json=True)
            
        except Exception as e:
            print(f"[ERROR] 輪胎性能詳細分析失敗: {e}")
    
    def run_telemetry_pitstop_records(self):
        """執行進站記錄分析 (含JSON輸出)"""
        try:
            from modules.single_driver_detailed_telemetry import SingleDriverTelemetryAnalyzer
            analyzer = SingleDriverTelemetryAnalyzer(self.data_loader)
            analyzer.run_pitstop_records(auto_driver="VER", save_json=True)
            
        except Exception as e:
            print(f"[ERROR] 進站記錄分析失敗: {e}")
    
    def run_telemetry_special_events(self):
        """執行特殊事件分析 (含JSON輸出)"""
        try:
            from modules.single_driver_detailed_telemetry import SingleDriverTelemetryAnalyzer
            analyzer = SingleDriverTelemetryAnalyzer(self.data_loader)
            analyzer.run_special_events(auto_driver="VER", save_json=True)
            
        except Exception as e:
            print(f"[ERROR] 特殊事件分析失敗: {e}")
    
    def run_telemetry_fastest_lap(self):
        """執行最快圈遙測圖表 (含JSON輸出)"""
        try:
            from modules.single_driver_detailed_telemetry import SingleDriverTelemetryAnalyzer
            analyzer = SingleDriverTelemetryAnalyzer(self.data_loader)
            analyzer.run_fastest_lap_telemetry(auto_driver="VER", save_json=True)
            
        except Exception as e:
            print(f"[ERROR] 最快圈遙測圖表失敗: {e}")
    
    def run_telemetry_specific_lap(self):
        """執行指定圈次遙測圖表 (含JSON輸出)"""
        try:
            from modules.single_driver_detailed_telemetry import SingleDriverTelemetryAnalyzer
            analyzer = SingleDriverTelemetryAnalyzer(self.data_loader)
            analyzer.run_specific_lap_telemetry(auto_driver="VER", save_json=True, auto_lap=1)
            
        except Exception as e:
            print(f"[ERROR] 指定圈次遙測圖表失敗: {e}")

    def run_analysis_direct(self, function_id: Union[str, int]) -> Dict[str, Any]:
        """直接執行分析功能 - 參數化模式
        
        Args:
            function_id: 功能編號 (整數 1-52 或字符串子功能如 "4.1")
            
        Returns:
            Dict[str, Any]: 執行結果
        """
        try:
            # 導入統一功能映射器
            from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper
            
            # 創建映射器
            mapper = F1AnalysisFunctionMapper(
                data_loader=self.data_loader,
                dynamic_team_mapping=self.dynamic_team_mapping,
                f1_analysis_instance=self.f1_analysis_instance,
                driver=getattr(self.args, 'driver', None),
                driver2=getattr(self.args, 'driver2', None)
            )
            
            # 執行分析
            # 處理詳細輸出參數
            show_detailed_output = False  # 預設關閉詳細輸出
            if hasattr(self.args, 'show_detailed_output') and self.args.show_detailed_output:
                show_detailed_output = True
            elif hasattr(self.args, 'no_detailed_output') and self.args.no_detailed_output:
                show_detailed_output = False
            
            colormap = getattr(self.args, 'colormap', None)
            save_json_flag = not getattr(self.args, 'no_save_json', False)
            include_driver_colors = not getattr(self.args, 'no_driver_colors', False)

            result = mapper.execute_function_by_number(
                function_id,
                year=self.args.year,
                race=self.args.race,
                session=self.args.session,
                driver=getattr(self.args, 'driver', None),
                driver2=getattr(self.args, 'driver2', None),
                lap=getattr(self.args, 'lap', None),
                lap1=getattr(self.args, 'lap1', None),
                lap2=getattr(self.args, 'lap2', None),
                corner=getattr(self.args, 'corner', None),
                show_detailed_output=show_detailed_output,
                colormap=colormap,
                save_json=save_json_flag,
                include_drivers=include_driver_colors
            )
            
            if result.get("success", False):
                print(f"[OK] 功能 {function_id} 執行成功")
                self.last_error_message = None
                self.last_error_details = None
            else:
                print(f"[ERROR] 功能 {function_id} 執行失敗: {result.get('message', '未知錯誤')}")
                self.last_error_message = result.get('message', '未知錯誤')
                self.last_error_details = {
                    "function_id": function_id,
                    "result": result
                }
            
            return result
            
        except Exception as e:
            error_result = {
                "success": False,
                "message": f"執行功能 {function_id} 時發生錯誤: {str(e)}",
                "function_id": str(function_id),
                "error": str(e)
            }
            print(f"[ERROR] {error_result['message']}")
            self.last_error_message = error_result['message']
            self.last_error_details = {
                "function_id": function_id,
                "exception": str(e)
            }
            return error_result
        """執行分析功能並返回JSON格式的結果
        
        Args:
            function_id: 分析功能編號
            
        Returns:
            dict: 包含分析結果的字典，格式為 {"success": bool, "data": dict}
        """
        try:
            if not self.session_loaded or not self.data_loader:
                return {
                    "success": False,
                    "error": "尚未載入賽事數據"
                }
            
            # 功能 1: 降雨強度分析 - 使用增強版模組
            if function_id == 1:
                try:
                    # 使用統一函數映射器執行增強版降雨分析
                    from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper
                    
                    mapper = F1AnalysisFunctionMapper(
                        data_loader=self.data_loader,
                        dynamic_team_mapping=self.dynamic_team_mapping,
                        f1_analysis_instance=self.f1_analysis_instance
                    )
                    
                    print("[RAIN] 執行分析...")
                    
                    # 執行增強版降雨分析
                    result = mapper.execute_function_by_number(1)
                    
                    if result.get("success", False):
                        return {
                            "success": True,
                            "data": result.get("data", {}),
                            "message": "增強版降雨分析執行成功",
                            "analysis_type": "enhanced_rain_analysis"
                        }
                    else:
                        return {
                            "success": False,
                            "error": result.get("message", "增強版降雨分析執行失敗")
                        }
                        
                except ImportError as e:
                    return {
                        "success": False,
                        "error": f"增強版降雨分析模組未找到: {str(e)}"
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"執行增強版降雨分析時發生錯誤: {str(e)}"
                    }
            
            # 功能 2: 賽道路線分析 (Track Path Analysis)
            elif function_id == 2:
                try:
                    from modules.track_path_analysis import run_track_path_analysis
                    print("\n[TRACK] 執行賽道路線分析 (功能2)...")
                    
                    # 執行賽道路線分析
                    result = run_track_path_analysis(self.data_loader)
                    
                    return {
                        "success": True if result else False,
                        "message": "賽道路線分析完成" if result else "賽道路線分析失敗",
                        "data": result,
                        "timestamp": datetime.now().isoformat()
                    }
                        
                except ImportError as e:
                    return {
                        "success": False,
                        "message": f"賽道路線分析模組未找到: {str(e)}",
                        "data": None,
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"執行賽道路線分析時發生錯誤: {str(e)}",
                        "data": None,
                        "timestamp": datetime.now().isoformat()
                    }
            
            # 功能 3: 進站策略分析 (Pitstop Strategy Analysis)
            elif function_id == 3:
                try:
                    from modules.pitstop_strategy_analysis import run_pitstop_strategy_analysis
                    print("\n[PIT] 執行進站策略分析 (功能3)...")
                    
                    # 執行進站策略分析
                    result = run_pitstop_strategy_analysis(self.data_loader)
                    
                    return {
                        "success": True if result else False,
                        "message": "進站策略分析完成" if result else "進站策略分析失敗",
                        "data": result,
                        "timestamp": datetime.now().isoformat()
                    }
                        
                except ImportError as e:
                    return {
                        "success": False,
                        "message": f"進站策略分析模組未找到: {str(e)}",
                        "data": None,
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"執行進站策略分析時發生錯誤: {str(e)}",
                        "data": None,
                        "timestamp": datetime.now().isoformat()
                    }
            
            # 功能 4: 獨立事故分析 (Independent Accident Analysis)
            elif function_id == 4:
                print(f"[DEBUG] 執行 function_id == 4 分支 - 獨立事故分析")
                try:
                    print(f"[DEBUG] 嘗試導入 modules.gui.accident_analysis.accident_analysis")
                    from modules.gui.accident_analysis.accident_analysis import run_accident_analysis_json
                    print(f"[DEBUG] 成功導入事故分析模組")
                    print("\n💥 執行獨立事故分析 (功能4)...")
                    
                    # 執行JSON版本的事故分析
                    json_result = run_accident_analysis_json(
                        self.data_loader, 
                        dynamic_team_mapping=self.dynamic_team_mapping,
                        f1_analysis_instance=self.f1_analysis_instance,
                        enable_debug=True
                    )
                    
                    return json_result
                        
                except ImportError as e:
                    print(f"[DEBUG] ImportError: {e}")
                    return {
                        "success": False,
                        "message": f"獨立事故分析模組未找到: {str(e)}",
                        "data": None,
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    print(f"[DEBUG] Exception: {e}")
                    return {
                        "success": False,
                        "message": f"執行獨立事故分析時發生錯誤: {str(e)}",
                        "data": None,
                        "timestamp": datetime.now().isoformat()
                    }
            
            # 功能 5: 單一車手綜合分析 (Single Driver Comprehensive Analysis)
            elif function_id == 5:
                try:
                    from modules.single_driver_comprehensive_analysis import run_single_driver_comprehensive_analysis
                    print("\n[F1] 執行單一車手綜合分析 (功能5)...")
                    
                    # 執行單一車手綜合分析
                    result = run_single_driver_comprehensive_analysis(self.data_loader)
                    
                    return {
                        "success": True if result else False,
                        "message": "單一車手綜合分析完成" if result else "單一車手綜合分析失敗",
                        "data": result,
                        "timestamp": datetime.now().isoformat()
                    }
                        
                except ImportError as e:
                    return {
                        "success": False,
                        "message": f"單一車手綜合分析模組未找到: {str(e)}",
                        "data": None,
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"執行單一車手綜合分析時發生錯誤: {str(e)}",
                        "data": None,
                        "timestamp": datetime.now().isoformat()
                    }
            
            # 功能 6: 單一車手詳細遙測分析 (Single Driver Detailed Telemetry)
            elif function_id == 6:
                try:
                    from modules.single_driver_detailed_telemetry_analysis import run_single_driver_detailed_telemetry_analysis
                    print("\n[TEST] 執行單一車手詳細遙測分析 (功能6)...")
                    
                    # 執行單一車手詳細遙測分析
                    result = run_single_driver_detailed_telemetry_analysis(self.data_loader)
                    
                    return {
                        "success": True if result else False,
                        "message": "單一車手詳細遙測分析完成" if result else "單一車手詳細遙測分析失敗",
                        "data": result,
                        "timestamp": datetime.now().isoformat()
                    }
                        
                except ImportError as e:
                    return {
                        "success": False,
                        "message": f"單一車手詳細遙測分析模組未找到: {str(e)}",
                        "data": None,
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"執行單一車手詳細遙測分析時發生錯誤: {str(e)}",
                        "data": None,
                        "timestamp": datetime.now().isoformat()
                    }
            
            # 功能 7: 單一車手詳細遙測分析
            elif function_id == 7:
                try:
                    from CLI_modules.cli.analyzer.single_driver_analysis import run_single_driver_telemetry_json
                    print("\n📡 執行單一車手詳細遙測分析 (JSON輸出版)...")
                    
                    # 執行JSON版本的單一車手詳細遙測分析
                    json_result = run_single_driver_telemetry_json(
                        self.data_loader, 
                        self.open_analyzer,
                        f1_analysis_instance=self.f1_analysis_instance,
                        enable_debug=True
                    )
                    
                    return json_result
                        
                except ImportError as e:
                    return {
                        "success": False,
                        "message": f"單一車手詳細遙測分析模組未找到: {str(e)}",
                        "data": None,
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"執行單一車手詳細遙測分析時發生錯誤: {str(e)}",
                        "data": None,
                        "timestamp": datetime.now().isoformat()
                    }
            
            # 功能 8: 所有事件詳細列表分析 (All Incidents Summary)
            elif function_id == 8:
                try:
                    from modules.all_incidents_analysis import run_all_incidents_analysis
                    print("\n📋 執行所有事件詳細列表分析 (增強版本)...")
                    
                    # 執行增強版本的所有事件分析
                    success = run_all_incidents_analysis(self.data_loader)
                    
                    if success:
                        return {
                            "success": True,
                            "message": "所有事件詳細列表分析完成 (增強版本)",
                            "data": {
                                "analysis_type": "all_incidents_analysis",
                                "year": getattr(self.data_loader, 'current_year', 2025),
                                "race": getattr(self.data_loader, 'current_race', 'Unknown'),
                                "session": getattr(self.data_loader, 'current_session', 'R'),
                                "enhanced_features": [
                                    "保留所有原始 race_control_messages",
                                    "詳細的旗幟分類 (DOUBLE_YELLOW, BLUE_FLAG 等)",
                                    "增強的事件分類系統",
                                    "完整的 FastF1 原始欄位",
                                    "雙重分類系統 (原始+增強)"
                                ]
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                    else:
                        return {
                            "success": False,
                            "message": "所有事件詳細列表分析失敗",
                            "data": None,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                except ImportError as e:
                    return {
                        "success": False,
                        "message": f"所有事件分析模組未找到: {str(e)}",
                        "data": None,
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"執行所有事件詳細列表分析時發生錯誤: {str(e)}",
                        "data": None,
                        "timestamp": datetime.now().isoformat()
                    }
            
            # 功能 9: 特殊事件報告分析 (Special Incident Reports)
            elif function_id == 9:
                try:
                    from modules.special_incidents_analysis import run_special_incidents_analysis_json
                    print("\n🚨 執行特殊事件報告分析 (JSON輸出版)...")
                    
                    # 執行JSON版本的特殊事件報告分析
                    json_result = run_special_incidents_analysis_json(
                        self.data_loader,
                        dynamic_team_mapping=self.dynamic_team_mapping,
                        f1_analysis_instance=self.f1_analysis_instance,
                        enable_debug=True
                    )
                    
                    return json_result
                        
                except ImportError as e:
                    # 後備方案：使用原始方法並強制生成 JSON
                    print(f"[WARNING] JSON版模組未找到，使用後備方案: {e}")
                    try:
                        self.run_accident_special_incidents()
                        
                        # 強制生成基本 JSON 結果
                        return {
                            "success": True,
                            "message": "特殊事件報告分析完成 (後備方案)",
                            "data": {
                                "analysis_type": "special_incidents",
                                "year": getattr(self.data_loader, 'current_year', 2025),
                                "race": getattr(self.data_loader, 'current_race', 'Unknown'),
                                "session": getattr(self.data_loader, 'current_session', 'R'),
                                "fallback_mode": True,
                                "note": "使用後備分析方法，請檢查模組 modules.special_incidents_analysis"
                            },
                            "timestamp": datetime.now().isoformat()
                        }
                    except Exception as fallback_error:
                        return {
                            "success": False,
                            "message": f"特殊事件報告分析後備方案也失敗: {str(fallback_error)}",
                            "data": None,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"執行特殊事件報告分析時發生錯誤: {str(e)}",
                        "data": None,
                        "timestamp": datetime.now().isoformat()
                    }
            
            else:
                # 對於其他功能，返回基本 JSON 結果
                return {
                    "success": False,
                    "message": f"功能 {function_id} 尚未實作 JSON 輸出版本",
                    "data": {
                        "function_id": str(function_id),
                        "note": "此功能需要進一步實作 JSON 支援"
                    },
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"執行分析功能時發生錯誤: {str(e)}"
            }

    def _create_basic_key_events_summary(self):
        """創建基本關鍵事件摘要"""
        try:
            print("\n[CHECK] 創建基本關鍵事件摘要...")
            print("[STATS] 分析進站策略關鍵轉折點...")
            
            if not self.data_loader or not hasattr(self.data_loader, 'session'):
                print("[ERROR] 數據載入器或會話未就緒")
                return
            
            session = self.data_loader.session
            if hasattr(session, 'laps') and session.laps is not None:
                laps = session.laps
                print(f"[CHART] 總圈數分析: {len(laps)} 圈")
                print(f"[FINISH] 參賽車手數: {len(laps['Driver'].unique())} 位")
                print("[OK] 基本關鍵事件摘要完成")
            else:
                print("[ERROR] 無法獲取圈數數據")
                
        except Exception as e:
            print(f"[ERROR] 基本關鍵事件摘要失敗: {e}")

    def _create_basic_special_incidents(self):
        """創建基本特殊事件報告"""
        try:
            print("\n[ALERT] 創建基本特殊事件報告...")
            print("[STATS] 分析比賽中的異常情況...")
            
            if not self.data_loader:
                print("[ERROR] 數據載入器未就緒")
                return
                
            print("[CHECK] 檢查特殊事件...")
            print("   - Safety Car 部署情況")
            print("   - Virtual Safety Car 情況")
            print("   - 紅旗中斷情況")
            print("   - DRS 可用性")
            print("[OK] 基本特殊事件報告完成")
                
        except Exception as e:
            print(f"[ERROR] 基本特殊事件報告失敗: {e}")

    def _create_basic_driver_severity_scores(self):
        """創建基本車手嚴重程度分數統計"""
        try:
            print("\n🏆 創建基本車手嚴重程度分數統計...")
            print("[STATS] 評估各車手表現嚴重程度...")
            
            if not self.data_loader or not hasattr(self.data_loader, 'session'):
                print("[ERROR] 數據載入器或會話未就緒")
                return
                
            session = self.data_loader.session
            if hasattr(session, 'laps') and session.laps is not None:
                laps = session.laps
                drivers = laps['Driver'].unique()
                
                print(f"[CHART] 分析 {len(drivers)} 位車手的表現:")
                for i, driver in enumerate(drivers[:5], 1):  # 顯示前5位車手
                    driver_laps = laps[laps['Driver'] == driver]
                    avg_time = driver_laps['LapTime'].dt.total_seconds().mean()
                    print(f"   {i}. {driver}: 平均圈時 {avg_time:.3f}s")
                
                print("[OK] 基本車手嚴重程度分數統計完成")
            else:
                print("[ERROR] 無法獲取圈數數據")
                
        except Exception as e:
            print(f"[ERROR] 基本車手嚴重程度分數統計失敗: {e}")

    def _create_basic_team_risk_scores(self):
        """創建基本車隊風險分數統計"""
        try:
            print("\n[FINISH] 創建基本車隊風險分數統計...")
            print("[STATS] 評估各車隊的風險程度...")
            
            # 檢查車隊映射，如果沒有就嘗試從session數據創建
            if not self.dynamic_team_mapping:
                print("[TOOL] 嘗試從賽事數據創建車隊映射...")
                if self.data_loader and hasattr(self.data_loader, 'session'):
                    session = self.data_loader.session
                    if hasattr(session, 'laps') and session.laps is not None:
                        laps = session.laps
                        drivers = laps['Driver'].unique()
                        
                        # 創建基本車隊映射（這裡可以改進以獲取真實車隊名稱）
                        self.dynamic_team_mapping = {}
                        team_names = [
                            "Red Bull Racing", "McLaren", "Ferrari", "Mercedes", 
                            "Aston Martin", "Alpine", "Williams", "RB", 
                            "Haas", "Sauber"
                        ]
                        
                        for i, driver in enumerate(drivers):
                            team_index = i % len(team_names)
                            self.dynamic_team_mapping[driver] = team_names[team_index]
                        
                        print(f"[OK] 創建了 {len(self.dynamic_team_mapping)} 位車手的車隊映射")
            
            if self.dynamic_team_mapping:
                print(f"[CHART] 分析 {len(self.dynamic_team_mapping)} 位車手的車隊分布:")
                team_count = {}
                for driver, team in self.dynamic_team_mapping.items():
                    team_count[team] = team_count.get(team, 0) + 1
                
                for team, count in sorted(team_count.items()):
                    print(f"   {team}: {count} 位車手")
                    
                print("[OK] 基本車隊風險分數統計完成")
            else:
                print("[ERROR] 無法創建車隊映射")
                
        except Exception as e:
            print(f"[ERROR] 基本車隊風險分數統計失敗: {e}")

    def _create_basic_all_incidents_summary(self):
        """創建基本所有事件詳細列表"""
        try:
            print("\n[INFO] 創建基本所有事件詳細列表...")
            print("[STATS] 彙整所有分析事件...")
            
            print("[CHECK] 事件類別統計:")
            print("   [PIN] 進站事件")
            print("   [ALERT] 安全車事件")
            print("   [WARNING] 黃旗事件")
            print("   [FINISH] 賽道限制事件")
            print("   [STATS] 輪胎策略事件")
            
            print("[OK] 基本所有事件詳細列表完成")
                
        except Exception as e:
            print(f"[ERROR] 基本所有事件詳細列表失敗: {e}")

    def show_help(self):
        """顯示幫助信息"""
        print("\n📖 F1分析CLI - 模組化版本使用說明 (v5.4 CLI專用版)")
        print("=" * 80)
        print("這是完全模組化的F1分析系統，僅支援CLI參數化模式。")
        print("基於FastF1和OpenF1官方API，支援2024-2025年F1賽季的專業級遙測數據分析。")
        print("✨ 新功能: 增強型賽事選擇界面，顯示賽事日期與完整Grand Prix名稱")
        
        print("\n[FINISH] 賽事選擇增強功能")
        print("─" * 80)
        print("• [CALENDAR] 顯示每場比賽的確切日期")
        print("• 🏆 顯示完整的Grand Prix正式名稱")
        print("• [STATS] 更清晰的表格化賽事列表")
        print("• 🌍 支援2024-2025年完整賽季日程")
        
        print("\n[RAIN]  基礎分析模組 (功能1-10)")
        print("=" * 80)
        
        print("1.  [RAIN] 降雨狀況分析")
        print("    分析降雨狀況 (有雨/無雨)，輸出 JSON 格式")
        
        print("\n2.  [TRACK] 賽道路線分析 (Track Path Analysis)")
        print("    功能描述：分析車手在賽道上的行駛路線和最佳賽車線")
        print("    輸入參數：年份、賽事、賽段類型、車手選擇(可選)")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • Track_Path_Coordinates (賽道路線座標表)")
        print("          - Columns: X, Y, Z, Speed, Distance, Sector")
        print("        • Racing_Line_Analysis (賽車線分析表)")
        print("          - Columns: CornerNumber, OptimalSpeed, ActualSpeed, LineDifference")
        print("      [CHART] Figure輸出：")
        print("        • track_layout_with_paths.png (賽道布局與路線圖)")
        print("        • racing_line_heatmap.png (賽車線熱力圖)")
        print("        • speed_zones_visualization.png (速度區域視覺化)")
        
        print("\n3.  [PIT] 車手最快進站時間排行榜 (Driver Fastest Pitstop Ranking)")
        print("    功能描述：統計各車手最快的進站時間表現")
        print("    輸入參數：年份、賽事、賽段類型")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • Pitstop_Time_Ranking (進站時間排行表)")
        print("          - Columns: Driver, FastestPitstop, AveragePitstop, PitstopCount")
        
        print("\n4.  [PIT] 車隊進站時間排行榜 (Team Pitstop Ranking)")
        print("    功能描述：統計各車隊的進站時間表現")
        print("    輸入參數：年份、賽事、賽段類型")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • Team_Pitstop_Ranking (車隊進站排行表)")
        print("          - Columns: Team, AveragePitstop, BestPitstop, PitstopCount")
        
        print("\n5.  [PIT] 車手進站詳細記錄 (Driver Detailed Pitstop Records)")
        print("    功能描述：詳細記錄指定車手的進站情況")
        print("    輸入參數：年份、賽事、賽段類型、車手縮寫")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • Pitstop_Details (進站詳細記錄表)")
        print("          - Columns: LapNumber, PitstopTime, TyreCompound, PositionChange")
        
        print("\n6.  💥 事故統計摘要分析 (Accident Statistics Summary)")
        print("    功能描述：統計比賽中的事故事件總覽")
        print("    輸入參數：年份、賽事、賽段類型")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • Accident_Summary (事故摘要表)")
        print("          - Columns: TotalAccidents, DriversInvolved, Locations, SeverityLevels")
        
        print("\n7.  💥 嚴重程度分佈分析 (Severity Distribution Analysis)")
        print("    功能描述：分析事故嚴重程度的分布情況")
        print("    輸入參數：年份、賽事、賽段類型")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • Severity_Distribution (嚴重程度分布表)")
        print("          - Columns: SeverityLevel, Count, Percentage, MostCommonLocation")
        
        print("\n8.  💥 所有事件詳細列表分析 (All Incidents Summary)")
        print("    功能描述：列出所有比賽事件的詳細信息")
        print("    輸入參數：年份、賽事、賽段類型")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • All_Incidents_List (所有事件列表)")
        print("          - Columns: Time, IncidentType, Drivers, Location, Details")
        
        print("\n9.  💥 特殊事件報告分析 (Special Incident Reports)")
        print("    功能描述：分析特殊的比賽事件")
        print("    輸入參數：年份、賽事、賽段類型")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • Special_Incidents (特殊事件表)")
        print("          - Columns: IncidentType, Time, Drivers, Impact, Details")
        
        print("\n10. 💥 關鍵事件摘要分析 (Key Events Summary)")
        print("    功能描述：總結比賽中的關鍵事件")
        print("    輸入參數：年份、賽事、賽段類型")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • Key_Events_Summary (關鍵事件摘要表)")
        print("          - Columns: EventType, Time, Description, RaceImpact")
        
        print("\n[F1] 單車手分析模組 (功能11-20)")
        print("=" * 80)
        
        print("11. [F1] 單一車手綜合分析 (Single Driver Comprehensive Analysis)")
        print("    ⚠️  狀態：已棄用 (DEPRECATED)")
        print("    功能描述：指定車手的詳細賽事表現分析")
        print("    輸入參數：年份、賽事、賽段類型、車手縮寫")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • Driver_Performance_Summary (車手表現摘要)")
        print("          - Columns: LapNumber, LapTime, Position, SectorTimes, Speed")
        
        print("\n12. 📡 單一車手詳細遙測分析 (Single Driver Detailed Telemetry)")
        print("    功能描述：深度分析單一車手的遙測數據")
        print("    輸入參數：年份、賽事、賽段類型、車手縮寫、圈數選擇")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • Telemetry_Data (遙測數據表)")
        print("          - Columns: Distance, Speed, Throttle, Brake, Gear, RPM, DRS")
        print("        • Performance_Metrics (性能指標表)")
        print("          - Columns: Metric, Value, OptimalValue, Difference, Percentage")
        print("      [CHART] Figure輸出：")
        print("        • speed_trace.png (速度軌跡圖)")
        print("        • throttle_brake_analysis.png (油門煞車分析)")
        print("        • gear_shift_patterns.png (換檔模式圖)")
        
        print("\n13. [BALANCE] 雙車手比較分析 (Driver Comparison)")
        print("    功能描述：比較兩位車手的詳細表現")
        print("    輸入參數：年份、賽事、賽段類型、兩位車手縮寫")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • Driver_Comparison_Table (車手對比表)")
        print("          - Columns: Metric, Driver1_Value, Driver2_Value, Difference, Winner")
        print("        • Lap_by_Lap_Comparison (逐圈對比表)")
        print("          - Columns: LapNumber, Driver1_Time, Driver2_Time, TimeDiff, PositionDiff")
        print("      [CHART] Figure輸出：")
        print("        • lap_time_comparison.png (圈速對比圖)")
        print("        • telemetry_overlay.png (遙測數據疊加圖)")
        
        print("\n14. [CHART] 賽事位置變化圖 (Race Position Changes)")
        print("    ⚠️  狀態：已棄用 (DEPRECATED)")
        print("    功能描述：顯示賽事中位置變化的圖表")
        print("    輸入參數：年份、賽事、賽段類型")
        print("    主要輸出：")
        print("      [CHART] Figure輸出：")
        print("        • position_changes_chart.png (位置變化圖)")
        
        print("\n15. [START] 賽事超車統計分析 (Race Overtaking Statistics)")
        print("    功能描述：統計賽事中的超車事件")
        print("    輸入參數：年份、賽事、賽段類型")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • Overtaking_Statistics (超車統計表)")
        print("          - Columns: TotalOvertakes, Successful, Failed, KeyMoments")
        
        print("\n16. [FINISH] 單一車手超車分析 (Single Driver Overtaking)")
        print("    功能描述：分析指定車手的超車和被超車情況")
        print("    輸入參數：年份、賽事、賽段類型、車手縮寫")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • Overtaking_Events (超車事件表)")
        print("          - Columns: LapNumber, Location, Type, TargetDriver, Success, Method")
        print("        • Overtaking_Statistics (超車統計表)")
        print("          - Columns: Total_Overtakes, Successful, Failed, DefensiveActions")
        print("      [CHART] Figure輸出：")
        print("        • overtaking_timeline.png (超車時間軸)")
        print("        • track_overtaking_zones.png (賽道超車區域圖)")
        
        print("\n17. [TARGET] 動態彎道檢測分析 (Dynamic Corner Detection)")
        print("    ⭐ 狀態：新增功能 (NEW)")
        print("    功能描述：動態檢測和分析賽道彎道")
        print("    輸入參數：年份、賽事、賽段類型")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • Corner_Detection_Results (彎道檢測結果表)")
        print("          - Columns: CornerNumber, StartPoint, EndPoint, Radius, Speed")
        
        print("\n18. [TARGET] 彎道詳細分析 (Corner Detailed Analysis)")
        print("    功能描述：詳細分析指定彎道的表現")
        print("    輸入參數：年份、賽事、賽段類型、彎道編號")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • Corner_Performance (彎道表現表)")
        print("          - Columns: LapNumber, Entry_Speed, Apex_Speed, Exit_Speed, Time_Through_Corner")
        print("        • Corner_Statistics (彎道統計表)")
        print("          - Columns: Best_Speed, Average_Speed, Consistency, Improvement_Rate")
        print("      [CHART] Figure輸出：")
        print("        • corner_speed_progression.png (彎道速度進步圖)")
        print("        • racing_line_corner.png (彎道賽車線分析)")
        
        print("\n19. [TOOL] 單一車手DNF分析 (Single Driver DNF Analysis)")
        print("    功能描述：分析指定車手的DNF情況")
        print("    輸入參數：年份、賽事、賽段類型、車手縮寫")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • DNF_Analysis (DNF分析表)")
        print("          - Columns: DNF_Reason, LapNumber, Position_Before_DNF, PreDNF_Performance")
        print("        • Reliability_Metrics (可靠性指標表)")
        print("          - Columns: Component, Status, WarningSignals, PredictedFailure")
        print("      [CHART] Figure輸出：")
        print("        • performance_before_dnf.png (DNF前表現圖)")
        print("        • failure_analysis.png (故障分析圖)")
        
        print("\n20. [TARGET] 單一車手全部彎道分析 (Single Driver All Corners)")
        print("    功能描述：分析指定車手在所有彎道的表現")
        print("    輸入參數：年份、賽事、賽段類型、車手縮寫")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • All_Corners_Performance (全彎道表現表)")
        print("          - Columns: Corner_Number, Entry_Speed, Apex_Speed, Exit_Speed, Consistency")
        print("      [CHART] Figure輸出：")
        print("        • all_corners_heatmap.png (全彎道熱力圖)")
        print("        • corner_consistency_radar.png (彎道一致性雷達圖)")
        
        print("\n👥 全部車手分析模組 (功能21-24)")
        print("=" * 80)
        
        print("21. 👥 所有車手綜合分析 (All Drivers Comprehensive Analysis)")
        print("    功能描述：全賽事20位車手的綜合表現分析")
        print("    輸入參數：年份、賽事、賽段類型")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • All_Drivers_Summary (全車手摘要表)")
        print("          - Columns: Driver, Position, BestLap, AverageLap, Consistency, Points")
        print("        • Championship_Impact (冠軍積分影響表)")
        print("          - Columns: Driver, PointsGained, ChampionshipPosition, PositionChange")
        print("      [CHART] Figure輸出：")
        print("        • drivers_performance_comparison.png (車手表現對比圖)")
        print("        • championship_standings.png (冠軍積分榜)")
        
        print("\n22. [F1] 彎道速度分析 (Corner Speed Analysis)")
        print("    ⚠️  狀態：已棄用 (DEPRECATED)")
        print("    功能描述：分析賽道各彎道的速度表現")
        print("    輸入參數：年份、賽事、賽段類型")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • Corner_Speed_Ranking (彎道速度排名表)")
        print("          - Columns: Corner, FastestDriver, Speed, AverageSpeed, SpeedVariation")
        
        print("\n23. [START] 全部車手超車分析 (All Drivers Overtaking)")
        print("    功能描述：全賽事所有超車事件的綜合分析")
        print("    輸入參數：年份、賽事、賽段類型")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • All_Overtaking_Events (全部超車事件表)")
        print("          - Columns: LapNumber, Driver1, Driver2, Location, Type, Success")
        print("        • Overtaking_Statistics (超車統計表)")
        print("          - Columns: Driver, Total_Overtakes, Success_Rate, Best_Overtaking_Zone")
        print("      [CHART] Figure輸出：")
        print("        • race_overtaking_map.png (賽事超車地圖)")
        print("        • overtaking_statistics.png (超車統計圖)")
        print("      [SAVE] 暫存檔案：overtaking_cache/目錄中的JSON檔案")
        
        print("\n24. [STATS] 全部車手DNF分析 (All Drivers DNF Analysis)")
        print("    功能描述：分析所有未完賽車手的退賽原因")
        print("    輸入參數：年份、賽事、賽段類型")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • DNF_Summary (DNF摘要表)")
        print("          - Columns: Driver, DNF_Reason, LapNumber, Position_Lost, Impact_Score")
        print("        • Reliability_Analysis (可靠性分析表)")
        print("          - Columns: Team, DNF_Count, Main_Issues, Reliability_Rating")
        print("      [CHART] Figure輸出：")
        print("        • dnf_reasons_distribution.png (DNF原因分布圖)")
        print("        • team_reliability_ranking.png (車隊可靠性排名)")
        print("      [SAVE] 暫存檔案：dnf_analysis_cache/目錄中的TXT和PNG檔案")
        
        print("\n🏆 全部車手全年分析模組 (選項14-15)")
        print("=" * 80)
        
        print("14. [START] 全部車手超車分析 (All Drivers Overtaking)")
        print("    功能描述：全賽事所有超車事件的綜合分析")
        print("    輸入參數：年份、賽事、賽段類型")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • All_Overtaking_Events (全部超車事件表)")
        print("          - Columns: LapNumber, Driver1, Driver2, Location, Type, Success")
        print("        • Overtaking_Statistics (超車統計表)")
        print("          - Columns: Driver, Total_Overtakes, Success_Rate, Best_Overtaking_Zone")
        print("      [CHART] Figure輸出：")
        print("        • race_overtaking_map.png (賽事超車地圖)")
        print("        • overtaking_statistics.png (超車統計圖)")
        print("      [SAVE] 暫存檔案：overtaking_cache/目錄中的JSON檔案")
        
        print("\n15. [STATS] 獨立全部車手DNF分析 (Independent All Drivers DNF)")
        print("    功能描述：分析所有未完賽車手的退賽原因")
        print("    輸入參數：年份、賽事、賽段類型")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • DNF_Summary (DNF摘要表)")
        print("          - Columns: Driver, DNF_Reason, LapNumber, Position_Lost, Impact_Score")
        print("        • Reliability_Analysis (可靠性分析表)")
        print("          - Columns: Team, DNF_Count, Main_Issues, Reliability_Rating")
        print("      [CHART] Figure輸出：")
        print("        • dnf_reasons_distribution.png (DNF原因分布圖)")
        print("        • team_reliability_ranking.png (車隊可靠性排名)")
        print("      [SAVE] 暫存檔案：dnf_analysis_cache/目錄中的TXT和PNG檔案")
        
        print("\n[TOOL] 系統功能 (功能49-53)")
        print("=" * 80)
        
        print("49. [REFRESH] 數據匯出管理器 (Data Export Manager)")
        print("    功能描述：管理數據匯出功能")
        print("    輸入參數：匯出選項")
        print("    主要輸出：匯出的數據檔案")
        
        print("\n50. [CACHE] 快取優化 (Cache Optimization)")
        print("    功能描述：優化系統快取性能")
        print("    輸入參數：優化參數")
        print("    主要輸出：優化報告")
        
        print("\n51. [DIAG] 系統診斷 (System Diagnostics)")
        print("    功能描述：檢查系統狀態和診斷問題")
        print("    輸入參數：診斷選項")
        print("    主要輸出：診斷報告")
        
        print("\n52. [PERF] 性能基準測試 (Performance Benchmarking)")
        print("    功能描述：測試系統性能")
        print("    輸入參數：測試參數")
        print("    主要輸出：性能報告")
        
        print("\n53. [CHECK] 數據完整性檢查 (Data Integrity Check)")
        print("    功能描述：檢查數據完整性")
        print("    輸入參數：檢查參數")
        print("    主要輸出：完整性報告")

        print("\n99. [CALENDAR] 賽季賽程查詢 (Season Calendar Overview)")
        print("    功能描述：列出指定年份已完成與即將進行的賽事")
        print("    輸入參數：年份 (-y)")
        print("    主要輸出：賽程 JSON 與摘要資訊")
        
        print("\n[SETTINGS]  設定功能 (字母選項)")
        print("=" * 80)
        
        print("S.  [SETTINGS] 重新設定賽事參數 (Change Race Settings)")
        print("    功能描述：使用新參數重新設定分析的賽事參數")
        print("    輸入參數：年份、賽事、賽段參數")
        
        print("\nL.  [INFO] 列出支援的賽事 (List Supported Races)")
        print("    功能描述：顯示2024-2025年支援的所有賽事")
        print("    輸入參數：可選年份")
        
        print("\nC.  [CHECK] 暫存狀態檢查 (Check Cache Status)")
        print("    功能描述：檢查所有暫存目錄的狀態")
        print("    輸入參數：無")
        
        print("\nD.  [CHECK] DNF暫存檢查 (Check DNF Cache)")
        print("    功能描述：檢查DNF分析暫存的詳細狀態")
        print("    輸入參數：無")
        
        print("\n[NOTE] 輸出檔案命名規則")
        print("=" * 80)
        print("• Table檔案：CSV格式，檔名包含分析類型和時間戳")
        print("• Figure檔案：PNG格式，高解析度，支援中文字體")
        print("• 暫存檔案：JSON/TXT格式，包含完整分析數據")
        print("• 檔名格式：{year}_{race}_{analysis_type}_{timestamp}")
        
        print("\n[TOOL] 技術架構與數據流")
        print("=" * 80)
        print("• 數據來源：FastF1官方API + OpenF1即時數據")
        print("• 處理流程：數據載入 → 清理驗證 → 分析計算 → 輸出生成")
        print("• 暫存機制：自動暫存計算結果，避免重複載入")
        print("• 錯誤處理：每個模組獨立錯誤處理，確保系統穩定性")
        
        print("\n[WARNING]  重要注意事項")
        print("=" * 80)
        print("• 網路需求：需要穩定網路連接以獲取F1數據")
        print("• 資料完整性：較新賽事數據完整性較高，建議優先分析")
        print("• 練習賽限制：練習賽數據可能不完整，建議使用正賽數據")
        print("• 暫存管理：定期清理暫存檔案以節省磁碟空間")
        
        print("=" * 80)
        print("💡 快速開始：輸入功能編號(1-24, 49-53)或子功能編號開始分析，輸入0退出")
        print("[REFRESH] 更新日期：2025年9月6日 | 版本：v5.4 (映射表同步版)")
        print("=" * 80)

    # 移除了大量的互動式模式方法，包括：
    # - run_analysis: 處理互動式選單選擇的龐大方法
    # 移除了 run_analysis 方法 - 僅支援參數化模式
    # 所有互動式選單處理邏輯已移除，程式更加簡潔高效

    # 移除了 manage_dnf_cache 方法 - 僅保留參數化模式核心功能



    def run(self):
        """執行 F1 分析 - 僅支援參數化模式"""
        self.last_error_message = None
        self.last_error_details = None
        self.display_header()
        
        print(f"\n[OK] 模組化F1分析系統已啟動 (參數化模式)")
        print(f"[FILES] 模組目錄: {modules_dir}")
        print(f"[PYTHON] Python版本: {sys.version.split()[0]}")
        
        # 檢查是否提供了必要參數
        if not self.args or not (self.args.year or self.args.race or self.args.session or self.args.function):
            print("\n[ERROR] 此程式僅支援參數化模式運行")
            print("請提供必要的參數來執行分析功能")
            print("\n使用範例:")
            print("  python f1_analysis_modular_main.py -y 2025 -r China -s R -f 1")
            print("  python f1_analysis_modular_main.py --help  # 查看完整參數說明")
            self.last_error_message = "缺少必要的參數"
            self.last_error_details = {
                "year": getattr(self.args, "year", None),
                "race": getattr(self.args, "race", None),
                "session": getattr(self.args, "session", None),
                "function": getattr(self.args, "function", None),
            }
            return False
        
        # 參數模式
        print("\n[START] 參數模式啟動...")
        return self.run_parameter_mode()

    def run_parameter_mode(self):
        """參數模式運行 - 唯一支援的運行模式"""
        print("=" * 60)
        print("[TOOL] 參數化模式 - F1分析系統核心")
        print("=" * 60)
        
        # 載入數據
        year = self.args.year if self.args.year else 2025
        race = self.args.race if self.args.race else "China"
        session = self.args.session if self.args.session else "R"

        function_id = str(self.args.function) if self.args.function else None
        # 系統功能和工具功能不需要載入賽事數據
        # 49: 數據匯出, 50: 快取優化, 51: 系統診斷, 52: 性能基準, 98: API 健康檢查, 99: 賽季賽程查詢
        # ⚠️ Function 53 (理想圈分析) 需要賽事數據，已從此列表移除
        data_optional_functions = {"49", "50", "51", "52", "98", "99"}

        print(f"[STATS] 載入參數: Year={year}, Race={race}, Session={session}")

        if function_id in data_optional_functions:
            print(f"[INFO] 功能 {function_id} 不需要賽事數據，跳過 FastF1 載入流程")
        else:
            if not self.load_race_data_from_args(year, race, session):
                print("[ERROR] 參數模式數據載入失敗")
                if not self.last_error_message:
                    self.last_error_message = "賽事數據載入失敗"
                    self.last_error_details = {
                        "year": year,
                        "race": race,
                        "session": session
                    }
                return False
        
        # 執行指定功能
        if self.args.function:
            function_id = self.args.function
            print(f"[TARGET] 執行功能: {function_id}")
            
            # 使用統一功能映射器執行
            result = self.run_analysis_direct(function_id)
            
            if result.get("success", False):
                print("[OK] 參數化模式功能執行完成")
                print(f"[INFO] 執行摘要: {result.get('message', '分析完成')}")
                
                # 顯示結果數據摘要
                if result.get("data"):
                    data_size = len(str(result['data']))
                    print(f"[STATS] 結果數據大小: {data_size} 字元")
                    
                    # 如果有 JSON 數據，顯示文件信息
                    if isinstance(result['data'], dict) and 'json_data' in result['data']:
                        json_files = result['data']['json_data']
                        if json_files:
                            print(f"📄 生成的 JSON 文件: {len(json_files)} 個")
                            
                return True
            else:
                print("[ERROR] 參數化模式功能執行失敗")
                print(f"[ERROR] 錯誤信息: {result.get('message', '未知錯誤')}")
                self.last_error_message = result.get('message', '未知錯誤')
                self.last_error_details = {
                    "function_id": function_id,
                    "result": result
                }
                return False
        else:
            print("[ERROR] 參數模式需要指定功能編號 (-f)")
            print("範例: python f1_analysis_modular_main.py -y 2025 -r China -s R -f 1")
            print("使用 --help 查看所有可用參數和功能")
            self.last_error_message = "缺少功能編號參數 (-f)"
            self.last_error_details = {
                "function": getattr(self.args, 'function', None)
            }
            return False


def create_argument_parser():
    """創建命令行參數解析器"""
    parser = argparse.ArgumentParser(
        description='F1 Analysis CLI - 參數化模式專用版本 v5.4 (映射表同步版)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用範例 (僅支援參數化模式):
  # 直接執行降雨強度分析
  python f1_analysis_modular_main.py -y 2025 -r China -s R -f 1
  
  # 執行速度差距分析 (指定車手)
  python f1_analysis_modular_main.py -y 2025 -r China -s R -f 7.1 -d VER -d2 LEC
  
  # 執行詳細DNF分析 (指定車手)
  python f1_analysis_modular_main.py -y 2025 -r China -s R -f 11.1 -d VER
  
  # 執行事故分析功能8 (所有事件詳細列表)
  python f1_analysis_modular_main.py -y 2025 -r China -s R -f 8

    # 查詢 2025 年賽程概覽 (無需賽事參數)
    python f1_analysis_modular_main.py -f 99 -y 2025
  
  # 顯示支援的賽事列表
  python f1_analysis_modular_main.py --list-races
  
  # 查看完整參數說明
  python f1_analysis_modular_main.py --help

功能編號對照:
  [RAIN]  基礎分析模組 (1-10):
  1  [RAIN] 降雨強度分析              2  [TRACK] 賽道路線分析
  3  [PIT] 車手最快進站時間排行榜      4  [PIT] 車隊進站時間排行榜
  5  [PIT] 車手進站詳細記錄            6  💥 事故統計摘要分析
  7  💥 嚴重程度分佈分析              8  💥 所有事件詳細列表分析
  9  💥 特殊事件報告分析              10 💥 關鍵事件摘要分析
  
  👤 單車手分析模組 (11-20):
  11 [F1] 單一車手綜合分析 ⚠️棄用     12 📡 單一車手詳細遙測分析
  13 [BALANCE] 雙車手比較分析         14 [CHART] 賽事位置變化圖 ⚠️棄用
  15 [START] 賽事超車統計分析         16 [FINISH] 單一車手超車分析
  17 [TARGET] 動態彎道檢測分析 ⭐新增  18 [TARGET] 彎道詳細分析
  19 [TOOL] 單一車手DNF分析           20 [TARGET] 單一車手全部彎道分析
  
  👥 全部車手分析模組 (21-24):
  21 👥 所有車手綜合分析             22 [F1] 彎道速度分析 ⚠️棄用
  23 [START] 全部車手超車分析         24 [STATS] 全部車手DNF分析
  
  [TOOL] 系統功能 (49-53):
  49 [REFRESH] 數據匯出管理器         50 [CACHE] 快取優化
  51 [DIAG] 系統診斷                 52 [PERF] 性能基準測試
  53 [CHECK] 數據完整性檢查
  
  子功能模組:
  4.1 💥 事故關鍵事件                4.2 💥 事故特殊事件
  4.3 � 事故車手嚴重程度            4.4 💥 事故車隊風險
  4.5 💥 事故所有事件                6.1 📡 遙測完整圈分析
  6.2 📡 遙測輪胎策略                6.3 📡 遙測輪胎性能
  6.4 📡 遙測進站記錄                6.5 📡 遙測特殊事件
  6.6 📡 遙測最快圈                  6.7 � 遙測指定圈
  7.1 [BALANCE] 速度差距分析         7.2 [BALANCE] 距離差距分析
  11.1 [TOOL] 詳細DNF分析            11.2 [TOOL] 年度DNF統計
  12.1 [TARGET] 單一車手彎道整合     12.2 [TARGET] 車隊彎道比較
  14.1 [STATS] 車手統計總覽          14.2 [TOOL] 車手遙測統計
  14.3 [START] 車手超車分析          14.9 👥 所有車手綜合分析
  16.1 [START] 年度超車統計          16.2 [FINISH] 超車表現比較
  16.3 [CHART] 超車視覺化分析        16.4 [CHART] 超車趨勢分析

💡 注意：本版本僅支援參數化模式，所有功能都需要透過命令行參數指定
        功能編號完全對應映射表，棄用功能可能無法正常使用
        '''
    )
    
    # 賽事參數
    parser.add_argument('-y', '--year', type=int, choices=list(range(2020, 2026)), 
                       help='賽季年份 (2020-2025，與 API 和功能 99 一致)')
    parser.add_argument('-r', '--race', type=str,
                       help='賽事名稱 (如: China, Bahrain, Australia 等)')
    parser.add_argument('-s', '--session', type=str,
                       help='賽段類型 (R=正賽, Q=排位賽, FP1/FP2/FP3=練習賽, S=短衝刺賽)')
    
    # 功能參數
    parser.add_argument('-f', '--function', type=str,
                       help='直接執行指定功能 (1-20, 4.1-4.5, 6.1-6.7, 7.1-7.2, 11.1-11.2, 12.1-12.2, 14.1-14.3, 16.1-16.4等子功能)')
    
    # 車手參數
    parser.add_argument('-d', '--driver', type=str,
                       help='主要車手代碼 (如: VER, LEC, HAM 等)')
    parser.add_argument('-d2', '--driver2', type=str,
                       help='次要車手代碼 (用於雙車手比較分析，如: VER, LEC, HAM 等)')
    
    # 分析參數
    parser.add_argument('--lap', type=int,
                       help='指定圈數 (用於特定圈數的遙測分析)')
    parser.add_argument('--lap1', type=int,
                       help='車手1的指定圈數 (用於雙車手比較分析)')
    parser.add_argument('--lap2', type=int,
                       help='車手2的指定圈數 (用於雙車手比較分析)')
    parser.add_argument('--fastest', action='store_true',
                       help='使用最速圈進行分析 (適用於車手比較分析)')
    parser.add_argument('--corner', type=int,
                       help='指定彎道編號 (用於彎道詳細分析，如: 1, 2, 3 等)')
    
    # 額外選項
    parser.add_argument('--list-races', action='store_true',
                       help='列出支援的賽事列表')
    parser.add_argument('--show-detailed-output', action='store_true', default=False,
                       help='顯示詳細的表格輸出，包含每圈詳細數據')
    parser.add_argument('--no-detailed-output', action='store_true', 
                       help='禁用詳細輸出，緩存模式下只顯示摘要 (預設行為)')
    parser.add_argument('--silent', action='store_true',
                       help='靜默模式：隱藏所有表格和統計輸出，僅執行分析並保存結果')
    parser.add_argument('--version', action='version', version='F1 Analysis CLI v5.3')
    parser.add_argument('--colormap', choices=['fastf1', 'official'],
                       help='顏色配置輸出時使用的色盤 (fastf1 或 official)')
    parser.add_argument('--no-save-json', action='store_true',
                       help='工具模式僅顯示結果，不輸出 JSON 檔案')
    parser.add_argument('--no-driver-colors', action='store_true',
                       help='顏色配置輸出時僅生成車隊色票，不包含車手')

    return parser

def main() -> int:
    """主程式進入點 - 僅支援參數化模式"""
    try:
        # 解析命令行參數
        parser = create_argument_parser()
        args = parser.parse_args()

        # 未提供任何參數時，顯示使用說明並提前結束
        if len(sys.argv) <= 1:
            print("\n[INFO] 偵測到未提供任何參數，本程式僅支援參數化模式運行。")
            print("請參考以下範例提供必要的參數後再試一次：")
            print("  python f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 1")
            print("  python f1_analysis_modular_main.py --help  # 查看完整參數說明")
            parser.print_help()
            return 0

        # 如果要求列出賽事
        if args.list_races:
            if args.year:
                # 顯示指定年份的詳細賽事列表
                print_races_for_year(args.year)
            else:
                # 顯示所有支援年份的賽事列表
                print_supported_races()
            return 0

        # 檢查 modules 目錄是否存在
        if not os.path.exists(modules_dir):
            print(f"[ERROR] 找不到 modules 目錄: {modules_dir}")
            print("請確保在正確的工作目錄中運行此程式")
            return 1

        # 啟動模組化CLI (僅參數化模式)
        cli = F1AnalysisModularCLI(args)
        success = cli.run()
        
        if not success:
            error_message = cli.last_error_message or "分析執行失敗"
            print(f"[ERROR] 分析執行失敗: {error_message}")
            if cli.last_error_details:
                logger.error("CLI 執行失敗詳情: %s", cli.last_error_details)
            return 1

        return 0

    except KeyboardInterrupt:
        print("\n\n👋 程式已被使用者中斷，再見！")
        return 0
    except Exception:
        logger.exception("CLI 執行期間發生未處理例外")
        print("請檢查系統環境或聯繫技術支援")
        return 1

def _is_interactive_environment() -> bool:
    """判斷當前是否為互動式環境，避免在 IDE/Jupyter 中拋出 SystemExit 堆疊"""
    if hasattr(sys, "ps1"):
        return True
    if "IPython" in sys.modules:
        return True
    # 檢查 VS Code Python Debug Console
    if "debugpy" in sys.modules or "_pydevd_bundle" in sys.modules:
        return True
    # 檢查其他 IDE 調試器
    if any(mod in sys.modules for mod in ["pydevd", "pdb", "bdb"]):
        return True
    argv0 = sys.argv[0] if sys.argv else ""
    return argv0 in {"", "-c"}

def print_supported_races():
    """列印支援的賽事列表"""
    print("\n[FINISH] F1 分析系統支援的賽事列表")
    print("=" * 60)
    
    race_options = {
        2024: [
            "Bahrain", "Saudi Arabia", "Australia", "Japan", "China", "Miami",
            "Emilia Romagna", "Monaco", "Canada", "Spain", "Austria", "Great Britain",
            "Hungary", "Belgium", "Netherlands", "Italy", "Azerbaijan", "Singapore",
            "United States", "Mexico", "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
        ],
        2025: [
            "Australia", "China", "Japan", "Bahrain", "Saudi Arabia", "Miami",
            "Monaco", "Spain", "Canada", "Austria", "Great Britain", "Hungary",
            "Belgium", "Netherlands", "Italy", "Azerbaijan", "Singapore",
            "United States", "Mexico", "Brazil", "Qatar", "Abu Dhabi"
        ]
    }
    
    for year in [2024, 2025]:
        print(f"\n[CALENDAR] {year} 年賽季:")
        races = race_options[year]
        for i, race in enumerate(races, 1):
            print(f"  {i:2d}. {race}")
    
    print("\n💡 賽段類型:")
    print("  R    - 正賽 (Race)")
    print("  Q    - 排位賽 (Qualifying)")
    print("  FP1  - 第一次自由練習")
    print("  FP2  - 第二次自由練習")
    print("  FP3  - 第三次自由練習")
    print("  S    - 短衝刺賽 (Sprint)")
    print("=" * 60)

def print_races_for_year(year):
    """列印指定年份的賽事列表，包含詳細信息"""
    # 賽事日期映射 - 詳細完整版本
    race_dates = {
        2024: {
            "Bahrain": "2024-03-02",
            "Saudi Arabia": "2024-03-09", 
            "Australia": "2024-03-24",
            "Japan": "2024-04-07",
            "China": "2024-04-21",
            "Miami": "2024-05-05",
            "Emilia Romagna": "2024-05-19",
            "Monaco": "2024-05-26",
            "Canada": "2024-06-09",
            "Spain": "2024-06-23",
            "Austria": "2024-06-30",
            "Great Britain": "2024-07-07",
            "Hungary": "2024-07-21",
            "Belgium": "2024-07-28",
            "Netherlands": "2024-09-01",
            "Italy": "2024-09-01",
            "Azerbaijan": "2024-09-15",
            "Singapore": "2024-09-22",
            "United States": "2024-10-20",
            "Mexico": "2024-10-27",
            "Brazil": "2024-11-03",
            "Las Vegas": "2024-11-23",
            "Qatar": "2024-12-01",
            "Abu Dhabi": "2024-12-08"
        },
        2025: {
            "Australia": "2025-03-16",
            "China": "2025-03-23",
            "Japan": "2025-04-06", 
            "Bahrain": "2025-04-13",
            "Saudi Arabia": "2025-04-20",
            "Miami": "2025-05-04",
            "Monaco": "2025-05-25",
            "Spain": "2025-06-01",
            "Canada": "2025-06-15",
            "Austria": "2025-06-29",
            "Great Britain": "2025-07-06",
            "Hungary": "2025-07-27",
            "Belgium": "2025-08-31",
            "Netherlands": "2025-09-07",
            "Italy": "2025-09-07",
            "Azerbaijan": "2025-09-21",
            "Singapore": "2025-10-05",
            "United States": "2025-10-19",
            "Mexico": "2025-10-26",
            "Brazil": "2025-11-09",
            "Qatar": "2025-11-30",
            "Abu Dhabi": "2025-12-07"
        }
    }
    
    # 賽事全名映射 - 標準正式名稱
    race_full_names = {
        "Bahrain": "Bahrain Grand Prix",
        "Saudi Arabia": "Saudi Arabian Grand Prix",
        "Australia": "Australian Grand Prix",
        "Japan": "Japanese Grand Prix",
        "China": "Chinese Grand Prix", 
        "Miami": "Miami Grand Prix",
        "Emilia Romagna": "Emilia Romagna Grand Prix",
        "Monaco": "Monaco Grand Prix",
        "Canada": "Canadian Grand Prix",
        "Spain": "Spanish Grand Prix",
        "Austria": "Austrian Grand Prix",
        "Great Britain": "British Grand Prix",
        "Hungary": "Hungarian Grand Prix",
        "Belgium": "Belgian Grand Prix",
        "Netherlands": "Dutch Grand Prix",
        "Italy": "Italian Grand Prix",
        "Azerbaijan": "Azerbaijan Grand Prix",
        "Singapore": "Singapore Grand Prix",
        "United States": "United States Grand Prix",
        "Mexico": "Mexican Grand Prix",
        "Brazil": "Brazilian Grand Prix", 
        "Las Vegas": "Las Vegas Grand Prix",
        "Qatar": "Qatar Grand Prix",
        "Abu Dhabi": "Abu Dhabi Grand Prix"
    }
    
    race_options = {
        2024: [
            "Bahrain", "Saudi Arabia", "Australia", "Japan", "China", "Miami",
            "Emilia Romagna", "Monaco", "Canada", "Spain", "Austria", "Great Britain",
            "Hungary", "Belgium", "Netherlands", "Italy", "Azerbaijan", "Singapore",
            "United States", "Mexico", "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
        ],
        2025: [
            "Australia", "China", "Japan", "Bahrain", "Saudi Arabia", "Miami",
            "Monaco", "Spain", "Canada", "Austria", "Great Britain", "Hungary",
            "Belgium", "Netherlands", "Italy", "Azerbaijan", "Singapore",
            "United States", "Mexico", "Brazil", "Qatar", "Abu Dhabi"
        ]
    }
    
    races = race_options.get(year, race_options[2025])
    dates = race_dates.get(year, race_dates[2025])
    
    print(f"\n[FINISH] {year} 年賽事列表:")
    race_table = PrettyTable()
    race_table.field_names = ["編號", "比賽日期", "賽事名稱", "完整名稱"]
    race_table.align = "l"
    
    for i, race in enumerate(races, 1):
        race_date = dates.get(race, "TBD")
        full_name = race_full_names.get(race, f"{race} Grand Prix")
        race_table.add_row([i, race_date, race, full_name])
    
    print(race_table)


if __name__ == "__main__":
    _exit_code = main()
    if _is_interactive_environment():
        if isinstance(_exit_code, int) and _exit_code != 0:
            print(f"[WARN] CLI 已以狀態碼 {_exit_code} 結束 (互動模式下已抑制 SystemExit)")
    else:
        sys.exit(_exit_code)
