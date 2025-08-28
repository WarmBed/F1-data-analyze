#!/usr/bin/env python3
"""
F1 Analysis CLI - 模組化主程式
F1 Analysis CLI - Modular Main Program
版本: 5.3 (增強賽事顯示版)
作者: F1 Analysis Team

專用模組化主程式，負責呼叫各個獨立分析模組
修正了 AllDriversDNFAdvanced 變數範圍問題和雨天分析依賴問題
新增: 賽事日期顯示、完整賽事名稱、增強型賽事選擇界面
"""

import os
import sys
import argparse
from typing import Optional, Union, Dict, Any
from datetime import datetime

# 設置標準輸出編碼為 UTF-8，避免 Windows 編碼問題
if sys.platform.startswith('win'):
    import locale
    try:
        # 嘗試設置控制台編碼為 UTF-8
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())
    except:
        # 如果失敗，使用預設編碼
        pass

# 確保 modules 目錄在 Python 路徑中
current_dir = os.path.dirname(os.path.abspath(__file__))
modules_dir = os.path.join(current_dir, 'modules')
if modules_dir not in sys.path:
    sys.path.insert(0, modules_dir)

# 導入所有分析模組
try:
    # 使用統一函數映射器
    from modules.function_mapper import F1AnalysisFunctionMapper
    from modules.compatible_data_loader import CompatibleF1DataLoader
    from modules.compatible_f1_analysis_instance import create_f1_analysis_instance
    
    print("[OK] 統一函數映射器導入成功！")
    has_function_mapper = True
    
    # 向後兼容：保留部分重要模組的直接導入
    try:
        from modules.rain_intensity_analyzer_json import run_rain_intensity_analysis_json
        has_rain_analysis = True
    except ImportError:
        print("[WARNING] 降雨分析模組未找到")
        has_rain_analysis = False
    from modules.all_drivers_overtaking_trends_analysis import run_all_drivers_overtaking_trends_analysis
    
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
        from modules.speed_gap_analysis import run_speed_gap_analysis
        from modules.distance_gap_analysis import run_distance_gap_analysis
        
        # 導入新的彎道分析子模組 (集成版本 - 包含進站與事件資料)
        from modules.single_driver_corner_analysis_integrated import run_single_driver_corner_analysis_integrated
        from modules.team_drivers_corner_comparison_integrated import run_team_drivers_corner_comparison_integrated
        
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
        from modules.compatible_data_loader import CompatibleF1DataLoader
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
        self.version = "5.3"
        self.title = "F1 Analysis CLI - 模組化版本 (增強賽事顯示版)"
        self.data_loader = None
        self.session_loaded = False
        self.dynamic_team_mapping = None
        self.f1_analysis_instance = None  # 添加完整的F1分析實例
        self.open_analyzer = None  # 添加 OpenF1 分析器實例
        self.args = args  # 保存命令行參數
        
        # 初始化F1分析實例
        self._initialize_f1_analysis_instance()
        
    def _initialize_f1_analysis_instance(self):
        """初始化F1分析實例"""
        try:
            from modules.compatible_f1_analysis_instance import create_f1_analysis_instance
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
            from modules.compatible_data_loader import F1OpenDataAnalyzer
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
            return False

    def load_race_data_at_startup(self):
        """程序啟動時載入賽事數據"""
        print("\n[TOOL] 初始化系統 - 請選擇要分析的賽事")
        print("=" * 60)
        
        # 初始化數據載入器
        try:
            self.data_loader = CompatibleF1DataLoader()
            print("[OK] 兼容數據載入器初始化成功")
        except Exception as e:
            print(f"[ERROR] 數據載入器初始化失敗: {e}")
            return False
        
        # 獲取賽季
        while True:
            try:
                year_input = input("請輸入賽季年份 (2024/2025，直接按 Enter 使用 2025): ").strip()
                if not year_input:
                    year = 2025
                    print(f"[OK] 使用預設年份: {year}")
                else:
                    year = int(year_input)
                    if year not in [2024, 2025]:
                        print("[ERROR] 請輸入 2024 或 2025")
                        continue
                    print(f"[OK] 使用年份: {year}")
                break
            except ValueError:
                print("[ERROR] 請輸入有效的年份")
            except EOFError:
                # 處理管道輸入或測試環境
                year = 2025
                print(f"[OK] 自動使用預設年份: {year}")
                break
        
        # 賽事列表與日期 - 完整更新版本
        race_options = {
            2024: [
                "Bahrain", "Saudi Arabia", "Australia", "Japan", "China", "Miami",
                "Emilia Romagna", "Monaco", "Canada", "Spain", "Austria", "Great Britain",
                "Hungary", "Belgium", "Netherlands", "Italy", "Azerbaijan", "Singapore",
                "United States", "Mexico", "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
            ],
            2025: [
                "Australia", "China", "Japan", "Bahrain", "Saudi Arabia", "Miami",
                "Emilia Romagna", "Monaco", "Spain", "Canada", "Austria", "Great Britain",
                "Belgium", "Hungary", "Netherlands", "Italy", "Azerbaijan", "Singapore",
                "United States", "Mexico", "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
            ]
        }
        
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
                "Emilia Romagna": "2025-05-18",
                "Monaco": "2025-05-25",
                "Spain": "2025-06-01",
                "Canada": "2025-06-15",
                "Austria": "2025-06-29",
                "Great Britain": "2025-07-06",
                "Hungary": "2025-08-03",  # 修正：匈牙利大獎賽
                "Belgium": "2025-07-27",  # 修正：比利時大獎賽（根據FastF1）
                "Netherlands": "2025-08-31",  # 修正：荷蘭大獎賽
                "Italy": "2025-09-07",  # 恢復：義大利大獎賽正確日期
                "Azerbaijan": "2025-09-21",
                "Singapore": "2025-10-05",
                "United States": "2025-10-19",
                "Mexico": "2025-10-26",
                "Brazil": "2025-11-09",
                "Las Vegas": "2025-11-22",
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
        
        # 讓使用者選擇賽事
        while True:
            try:
                choice_input = input(f"\n請選擇賽事編號 (1-{len(races)}，或直接按 Enter 使用 Japan): ").strip()
                if not choice_input:
                    race_name = "Japan"
                    print(f"[OK] 使用預設賽事: {race_name}")
                else:
                    choice = int(choice_input)
                    if choice < 1 or choice > len(races):
                        print(f"[ERROR] 請輸入 1 到 {len(races)} 之間的數字")
                        continue
                    race_name = races[choice - 1]
                    print(f"[OK] 已選擇: {race_name}")
                break
            except ValueError:
                print("[ERROR] 請輸入有效的數字")
            except EOFError:
                race_name = "Japan"
                print(f"[OK] 自動選擇: {race_name}")
                break
        
        # 獲取賽段類型
        print(f"\n[F1]  賽段類型選項:")
        print("   R  - 正賽 (Race)")
        print("   Q  - 排位賽 (Qualifying)")
        print("   FP1, FP2, FP3 - 自由練習")
        print("   S  - 短衝刺賽 (Sprint)")
        
        session_type = input("請輸入賽段類型 (直接按 Enter 使用 R): ").strip().upper()
        if not session_type:
            session_type = "R"
            print(f"[OK] 使用預設賽段類型: {session_type}")
        
        # 載入數據
        print(f"\n[STATS] 載入 {year} {race_name} {session_type} 數據...")
        if self.data_loader.load_race_data(year, race_name, session_type):
            self.session_loaded = True
            print(f"[OK] 賽事數據載入完成！")
            
            # 初始化 OpenF1 分析器
            self._initialize_open_analyzer()
            
            # 更新F1分析實例
            self._update_f1_analysis_instance()
            
            return True
        else:
            print(f"[ERROR] 賽事數據載入失敗")
            return False

    def display_menu(self):
        """顯示主選單"""
        print("\n" + "="*80)
        print("[F1]  F1 賽事分析 CLI 模組化版本 v2.0")
        print("="*80)
        
        if self.session_loaded:
            print("[STATS] 數據狀態: [OK] 已載入賽事數據")
        else:
            print("[STATS] 數據狀態: [ERROR] 尚未載入賽事數據")
        print("─" * 80)
        
        print("\n基礎分析模組")
        print("1.  [RAIN] 降雨強度分析                 (Rain Intensity Analysis)")
        print("2.  [TRACK] 賽道路線分析                 (Track Path Analysis)")
        print("3.  🏆 車手最快進站時間排行榜        (Driver Fastest Pitstop Ranking)")
        print("4.  [FINISH] 車隊進站時間排行榜            (Team Pitstop Ranking)")  
        print("5.  [INFO] 車手進站詳細記錄              (Driver Detailed Pitstop Records)")
        print("6.  💥 獨立事故分析                 (Independent Accident Analysis)")
        
        print("\n事故分析子模組")
        print("6.1 [CHECK] 關鍵事件摘要                 (Key Events Summary)")
        print("6.2 [ALERT] 特殊事件報告                 (Special Incident Reports)")
        print("6.3 🏆 車手嚴重程度分數統計         (Driver Severity Scores)")
        print("6.4 [FINISH] 車隊風險分數統計             (Team Risk Scores)")
        print("6.5 [INFO] 所有事件詳細列表             (All Incidents Summary)")
        
        print("\n單車手單圈分析模組")
        print("7.  [F1] 單一車手綜合分析             (Single Driver Comprehensive Analysis)")
        print("8.  📡 單一車手詳細遙測分析         (Single Driver Detailed Telemetry)")
        
        print("\n遙測分析子模組")
        print("6.1 [CHART] 詳細圈次分析                 (Complete Lap Analysis)")
        print("6.2 [FINISH] 詳細輪胎策略分析             (Detailed Tire Strategy)")
        print("6.3 [STATS] 輪胎性能詳細分析             (Tire Performance Analysis)")
        print("6.4 [PIT] 進站記錄                     (Pitstop Records)")
        print("6.5 [ALERT] 特殊事件分析                 (Special Events)")
        print("6.6 [F1] 最快圈速度遙測數據           (Fastest Lap Speed Data)")
        print("6.7 [STATS] 指定圈次完整遙測數據         (Specific Lap Full Telemetry)")
        
        print("\n比較分析模組")
        print("7.  🆚 雙車手比較分析               (Two Driver Comparison)")
        print("7.1 [F1] 速度差距分析                 (Speed Gap Analysis)")
        print("7.2 📏 距離差距分析                 (Distance Gap Analysis)")
        print("10. [FINISH] 單一車手超車分析             (Single Driver Overtaking)")
        print("11. [TOOL] 獨立單一車手DNF分析          (Independent Single Driver DNF)")
        print("12. [TARGET] 單賽事指定彎道詳細分析       (Single Race Specific Corner Detailed Analysis)")
        print("13. [STATS] 單一車手指定賽事全部彎道詳細分析 (Single Driver All Corners Detailed Analysis)")
        
        print("\n全部車手單圈分析模組")
        print("14.1 [STATS] 車手數據統計總覽           (Driver Statistics Overview)")
        print("14.2 [TOOL] 車手遙測資料統計           (Driver Telemetry Statistics)")
        print("14.3 [START] 車手超車分析               (Driver Overtaking Analysis)")
        print("14.9 👥 所有車手綜合分析           (All Drivers Comprehensive Analysis)")
        print("15. [F1] 彎道速度分析                 (Corner Speed Analysis)")
        
        print("\n全部車手全年分析模組")
        print("16. [START] 全部車手超車分析             (All Drivers Overtaking) [新版子模組]")
        print("    • 16.1 年度超車統計 • 16.2 表現比較 • 16.3 視覺化分析 • 16.4 趨勢分析")
        print("17. [STATS] 獨立全部車手DNF分析          (Independent All Drivers DNF)")
        
        print("\n系統功能")
        print("18. [REFRESH] 重新載入賽事數據             (Reload Race Data)")
        print("19. [PACKAGE] 顯示模組狀態                 (Show Module Status)")
        print("20. 📖 顯示幫助信息                 (Show Help)")
        print("21. [SAVE] 超車暫存管理                 (Overtaking Cache Management)")
        print("22. [ARCHIVE] DNF暫存管理                 (DNF Cache Management)")
        
        print("\n設定功能")
        print("S.  [SETTINGS] 重新設定賽事參數             (Change Race Settings)")
        print("L.  [INFO] 列出支援的賽事               (List Supported Races)")
        print("C.  [CHECK] 暫存狀態檢查                 (Check Cache Status)")
        print("D.  [CHECK] DNF暫存檢查                  (Check DNF Cache)")
        
        print("\n0.  退出程式 (Exit)")
        print("─" * 80)

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
        """執行降雨強度分析 - 專門的天氣數據分析"""
        try:
            print("\n[RAIN] 執行降雨強度分析...")
            from modules.rain_intensity_analysis import run_rain_intensity_analysis
            run_rain_intensity_analysis(self.data_loader)
        except ImportError as e:
            print(f"[ERROR] 降雨分析模組導入失敗: {e}")
            print("正在創建基礎降雨分析...")
            self._create_basic_rain_analysis()
        except Exception as e:
            print(f"[ERROR] 降雨分析執行失敗: {e}")
            self._create_basic_rain_analysis()

    # === 獨立事故分析方法 ===
    
    def run_accident_key_events_summary(self):
        """執行關鍵事件摘要分析 - 新版本無車隊映射錯誤"""
        try:
            from modules.key_events_analysis import run_key_events_summary_analysis
            print("\n[CHECK] 執行關鍵事件摘要分析...")
            
            # 使用新的關鍵事件分析模組
            run_key_events_summary_analysis(self.data_loader)
            
        except ImportError as e:
            print(f"[ERROR] 關鍵事件分析模組未找到: {e}")
            # 後備方案：使用原始方法
            try:
                from modules.accident_analysis_complete import F1AccidentAnalysisComplete
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
            from modules.special_incidents_analysis import run_special_incidents_analysis
            print("\n[ALERT] 執行特殊事件報告分析...")
            
            # 使用新的特殊事件分析模組
            run_special_incidents_analysis(self.data_loader)
            
        except ImportError as e:
            print(f"[ERROR] 特殊事件分析模組未找到: {e}")
            # 後備方案：使用原始方法
            try:
                from modules.accident_analysis_complete import F1AccidentAnalysisComplete
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
            from modules.driver_severity_analysis import run_driver_severity_analysis
            print("\n🏆 執行車手嚴重程度分數統計...")
            
            # 使用新的車手嚴重程度分析模組
            run_driver_severity_analysis(self.data_loader)
            
        except ImportError as e:
            print(f"[ERROR] 車手嚴重程度分析模組未找到: {e}")
            # 後備方案：使用原始方法
            try:
                from modules.accident_analysis_complete import F1AccidentAnalysisComplete
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
            from modules.team_risk_analysis import run_team_risk_analysis
            print("\n[FINISH] 執行車隊風險分數統計...")
            
            # 使用新的車隊風險分析模組
            run_team_risk_analysis(self.data_loader)
            
        except ImportError as e:
            print(f"[ERROR] 車隊風險分析模組未找到: {e}")
            # 後備方案：使用原始方法
            try:
                from modules.accident_analysis_complete import F1AccidentAnalysisComplete
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
            from modules.all_incidents_analysis import run_all_incidents_analysis
            print("\n[INFO] 執行所有事件詳細列表分析...")
            
            # 使用新的所有事件分析模組
            run_all_incidents_analysis(self.data_loader)
            
        except ImportError as e:
            print(f"[ERROR] 所有事件分析模組未找到: {e}")
            # 後備方案：使用原始方法
            try:
                from modules.accident_analysis_complete import F1AccidentAnalysisComplete
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
            from modules.function_mapper import F1AnalysisFunctionMapper
            
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
            show_detailed_output = True  # 預設啟用
            if hasattr(self.args, 'no_detailed_output') and self.args.no_detailed_output:
                show_detailed_output = False
            elif hasattr(self.args, 'show_detailed_output'):
                show_detailed_output = self.args.show_detailed_output
            
            result = mapper.execute_function_by_number(
                function_id,
                year=self.args.year,
                race=self.args.race,
                session=self.args.session,
                driver=getattr(self.args, 'driver', None),
                driver2=getattr(self.args, 'driver2', None),
                lap=getattr(self.args, 'lap', None),
                corner=getattr(self.args, 'corner', None),
                show_detailed_output=show_detailed_output
            )
            
            if result.get("success", False):
                print(f"[OK] 功能 {function_id} 執行成功")
            else:
                print(f"[ERROR] 功能 {function_id} 執行失敗: {result.get('message', '未知錯誤')}")
            
            return result
            
        except Exception as e:
            error_result = {
                "success": False,
                "message": f"執行功能 {function_id} 時發生錯誤: {str(e)}",
                "function_id": str(function_id),
                "error": str(e)
            }
            print(f"[ERROR] {error_result['message']}")
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
            
            # 功能 1: 降雨強度分析
            if function_id == 1:
                try:
                    from modules.rain_intensity_analyzer_json import run_rain_intensity_analysis_json
                    print("\n[RAIN]  執行降雨強度分析 (JSON輸出版)...")
                    
                    # 執行JSON版本的降雨分析
                    json_result = run_rain_intensity_analysis_json(
                        self.data_loader, 
                        year=self.year,
                        race_name=self.race,
                        session=self.session,
                        enable_debug=True
                    )
                    
                    if "error" in json_result:
                        return {
                            "success": False,
                            "error": json_result["error"]
                        }
                    else:
                        return {
                            "success": True,
                            "data": json_result
                        }
                        
                except ImportError as e:
                    return {
                        "success": False,
                        "error": f"JSON降雨分析模組未找到: {str(e)}"
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "error": f"執行降雨分析時發生錯誤: {str(e)}"
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
                    print(f"[DEBUG] 嘗試導入 modules.accident_analysis")
                    from modules.accident_analysis import run_accident_analysis_json
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
                    from modules.single_driver_analysis import run_single_driver_telemetry_json
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
            
            # 功能 8: 車手對比分析
            elif function_id == 8:
                try:
                    from modules.driver_comparison_advanced import run_driver_comparison_json
                    print("\n[BALANCE] 執行車手對比分析 (JSON輸出版)...")
                    
                    # 執行JSON版本的車手對比分析
                    json_result = run_driver_comparison_json(
                        self.data_loader, 
                        f1_analysis_instance=self.f1_analysis_instance,
                        enable_debug=True
                    )
                    
                    return json_result
                        
                except ImportError as e:
                    return {
                        "success": False,
                        "message": f"車手對比分析模組未找到: {str(e)}",
                        "data": None,
                        "timestamp": datetime.now().isoformat()
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"執行車手對比分析時發生錯誤: {str(e)}",
                        "data": None,
                        "timestamp": datetime.now().isoformat()
                    }
            
            else:
                # 對於其他功能，返回標準執行結果
                result = self.run_analysis(function_id)
                return {
                    "success": result if isinstance(result, bool) else True,
                    "data": {"message": "功能執行完成", "supports_json": False}
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"執行分析功能時發生錯誤: {str(e)}"
            }

    def _create_basic_rain_analysis(self):
        """創建基礎降雨分析"""
        try:
            if not self.data_loader or not hasattr(self.data_loader, 'session'):
                print("[ERROR] 數據載入器或會話未就緒")
                return
            
            session = self.data_loader.session
            print("\n[RAIN]  執行基礎降雨分析...")
            
            if hasattr(session, 'weather_data') and session.weather_data is not None:
                weather = session.weather_data
                
                print(f"[STATS] 天氣數據概覽:")
                if 'Rainfall' in weather.columns:
                    total_rainfall = weather['Rainfall'].sum()
                    print(f"   [RAIN]  總降雨量: {total_rainfall:.2f} mm")
                    
                    if total_rainfall > 0:
                        print(f"   ☔ 本場比賽有降雨記錄")
                        rain_laps = weather[weather['Rainfall'] > 0]
                        print(f"   🕒 降雨持續時間: {len(rain_laps)} 個記錄點")
                    else:
                        print(f"   [SUN]  本場比賽無降雨記錄")
                else:
                    print("   ❓ 降雨數據不可用")
                
                if 'AirTemp' in weather.columns:
                    avg_temp = weather['AirTemp'].mean()
                    print(f"   [TEMP]  平均氣溫: {avg_temp:.1f}°C")
                
                if 'TrackTemp' in weather.columns:
                    avg_track_temp = weather['TrackTemp'].mean()
                    print(f"   [FINISH] 平均賽道溫度: {avg_track_temp:.1f}°C")
                    
                print("[OK] 基礎降雨分析完成")
            else:
                print("[ERROR] 無法獲取天氣數據")
                
        except Exception as e:
            print(f"[ERROR] 基礎降雨分析失敗: {e}")

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

    def _show_function_16_submenu(self):
        """顯示 Function 16 子選單"""
        print("\n" + "=" * 60)
        print("[START] 全部車手超車分析模組 (Function 16)")
        print("=" * 60)
        print("請選擇分析類型:")
        print("16.1 [STATS] 年度超車統計               (Annual Overtaking Statistics)")
        print("16.2 [FINISH] 表現比較分析               (Performance Comparison)")
        print("16.3 [CHART] 視覺化分析                 (Visualization Analysis)")
        print("16.4 [CHART] 趨勢分析                   (Trends Analysis)")
        print("0.   ↩️ 返回主選單                 (Back to Main Menu)")
        print("=" * 60)
        
        try:
            choice = input("\n請輸入選項 (16.1, 16.2, 16.3, 16.4, 0): ").strip()
            
            if choice == "0":
                return
            elif choice == "16.1":
                print("\n[STATS] 執行年度超車統計分析...")
                success = run_all_drivers_annual_overtaking_statistics(
                    self.data_loader, 
                    self.dynamic_team_mapping, 
                    self.f1_analysis_instance
                )
                if success:
                    print("[OK] 年度超車統計分析完成")
                else:
                    print("[ERROR] 年度超車統計分析失敗")
                    
            elif choice == "16.2":
                print("\n[FINISH] 執行表現比較分析...")
                success = run_all_drivers_overtaking_performance_comparison(
                    self.data_loader, 
                    self.dynamic_team_mapping, 
                    self.f1_analysis_instance
                )
                if success:
                    print("[OK] 表現比較分析完成")
                else:
                    print("[ERROR] 表現比較分析失敗")
                    
            elif choice == "16.3":
                print("\n[CHART] 執行視覺化分析...")
                success = run_all_drivers_overtaking_visualization_analysis(
                    self.data_loader, 
                    self.dynamic_team_mapping, 
                    self.f1_analysis_instance
                )
                if success:
                    print("[OK] 視覺化分析完成")
                else:
                    print("[ERROR] 視覺化分析失敗")
                    
            elif choice == "16.4":
                print("\n[CHART] 執行趨勢分析...")
                success = run_all_drivers_overtaking_trends_analysis(
                    self.data_loader, 
                    self.dynamic_team_mapping, 
                    self.f1_analysis_instance
                )
                if success:
                    print("[OK] 趨勢分析完成")
                else:
                    print("[ERROR] 趨勢分析失敗")
                    
            else:
                print(f"[ERROR] 無效選項: {choice}")
                print("請輸入有效的選項 (16.1, 16.2, 16.3, 16.4, 0)")
                
        except KeyboardInterrupt:
            print("\n[WARNING] 操作已取消")
        except Exception as e:
            print(f"[ERROR] 子選單執行失敗: {e}")

    def show_help(self):
        """顯示幫助信息"""
        print("\n📖 F1分析CLI - 模組化版本使用說明 (v5.3)")
        print("=" * 80)
        print("這是完全模組化的F1分析系統，每個功能都是獨立的模組。")
        print("基於FastF1和OpenF1官方API，支援2024-2025年F1賽季的專業級遙測數據分析。")
        print("✨ 新功能: 增強型賽事選擇界面，顯示賽事日期與完整Grand Prix名稱")
        
        print("\n[FINISH] 賽事選擇增強功能")
        print("─" * 80)
        print("• [CALENDAR] 顯示每場比賽的確切日期")
        print("• 🏆 顯示完整的Grand Prix正式名稱")
        print("• [STATS] 更清晰的表格化賽事列表")
        print("• 🌍 支援2024-2025年完整賽季日程")
        
        print("\n[RAIN]  基礎分析模組 (選項1-4)")
        print("=" * 80)
        
        print("1.  [RAIN] 降雨強度分析 (Rain Intensity Analysis)")
        print("    功能描述：完全復刻原版降雨強度分析功能")
        print("    輸入參數：年份、賽事、賽段類型")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • Weather_Data_Summary (天氣數據摘要表)")
        print("          - Columns: Time, Rainfall(mm), AirTemp(°C), TrackTemp(°C), Humidity(%)")
        print("        • Rain_Impact_Analysis (降雨影響分析表)")
        print("          - Columns: LapNumber, TotalRainfall, WetTyreUsage, LapTimeImpact")
        print("      [CHART] Figure輸出：")
        print("        • rainfall_timeline_chart.png (降雨時間線圖)")
        print("        • weather_conditions_heatmap.png (天氣條件熱力圖)")
        print("        • tire_strategy_rain_analysis.png (輪胎策略雨天分析)")
        print("      [NOTE] 文字輸出：降雨強度統計報告")
        
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
        
        print("\n3.  [PIT] 進站策略分析 (Pitstop Strategy Analysis)")
        print("    ├── 3.1 [CHECK] 關鍵事件摘要           (Key Events Summary)")
        print("    ├── 3.2 [ALERT] 特殊事件報告           (Special Incident Reports)")
        print("    ├── 3.3 🏆 車手嚴重程度分數統計   (Driver Severity Scores)")
        print("    ├── 3.4 [FINISH] 車隊風險分數統計       (Team Risk Scores)")
        print("    └── 3.5 [INFO] 所有事件詳細列表       (All Incidents Summary)")
        print("    功能描述：詳細分析各車手的進站策略和效果")
        print("    輸入參數：年份、賽事、賽段類型")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • Pitstop_Summary (進站摘要表)")
        print("          - Columns: Driver, PitstopNumber, LapNumber, Duration, TyreCompound")
        print("        • Strategy_Effectiveness (策略效果分析表)")
        print("          - Columns: Driver, Strategy, PositionGain/Loss, TimeGain/Loss")
        print("      [CHART] Figure輸出：")
        print("        • pitstop_timeline.png (進站時間軸)")
        print("        • strategy_comparison.png (策略對比圖)")
        print("        • tire_degradation_analysis.png (輪胎衰退分析)")
        
        print("\n4.  💥 獨立事故分析 (Independent Accident Analysis)")
        print("    功能描述：檢測和分析比賽中的事故事件")
        print("    輸入參數：年份、賽事、賽段類型")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • Incident_Log (事故記錄表)")
        print("          - Columns: LapNumber, Time, IncidentType, DriversInvolved, Location")
        print("        • Safety_Car_Analysis (安全車分析表)")
        print("          - Columns: Period, Duration, Reason, ImpactOnRace")
        print("      [CHART] Figure輸出：")
        print("        • incident_timeline.png (事故時間軸)")
        print("        • accident_location_map.png (事故位置圖)")
        
        print("\n[F1] 單車手單圈分析模組 (選項5-10)")
        print("=" * 80)
        
        print("5.  [F1] 單一車手綜合分析 (Single Driver Comprehensive Analysis)")
        print("    功能描述：指定車手的詳細賽事表現分析")
        print("    輸入參數：年份、賽事、賽段類型、車手縮寫(如:VER)")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • Driver_Performance_Summary (車手表現摘要)")
        print("          - Columns: LapNumber, LapTime, Position, Sector1/2/3Times, Speed")
        print("        • Session_Statistics (賽段統計表)")
        print("          - Columns: Metric, Value, Rank, BestLap, AverageLap")
        print("      [CHART] Figure輸出：")
        print("        • lap_time_progression.png (圈速進步圖)")
        print("        • position_changes.png (位置變化圖)")
        print("        • sector_time_analysis.png (分段時間分析)")
        
        print("\n6.  📡 單一車手詳細遙測分析 (Single Driver Detailed Telemetry)")
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
        
        print("\n7.  [BALANCE] 車手對比分析 (Driver Comparison)")
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
        
        print("\n8.  [FINISH] 單一車手超車分析 (Single Driver Overtaking)")
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
        
        print("\n9.  [TOOL] 獨立單一車手DNF分析 (Independent Single Driver DNF)")
        print("    功能描述：深度分析特定車手的DNF情況")
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
        
        print("\n10. [TARGET] 單賽事指定彎道詳細分析 (Single Race Specific Corner Detailed Analysis)")
        print("    功能描述：單一車手詳細彎道分析，指定車手在特定彎道的每圈表現")
        print("    輸入參數：年份、賽事、賽段類型、車手縮寫、彎道編號")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • Corner_Performance (彎道表現表)")
        print("          - Columns: LapNumber, Entry_Speed, Apex_Speed, Exit_Speed, Time_Through_Corner")
        print("        • Corner_Statistics (彎道統計表)")
        print("          - Columns: Best_Speed, Average_Speed, Consistency, Improvement_Rate")
        print("      [CHART] Figure輸出：")
        print("        • corner_speed_progression.png (彎道速度進步圖)")
        print("        • racing_line_corner.png (彎道賽車線分析)")
        print("      [WARNING]  注意：自動排除LAP1 T1數據，避免起跑線影響")
        
        print("\n11. [STATS] 單一車手指定賽事全部彎道詳細分析 (Single Driver All Corners Detailed Analysis)")
        print("    功能描述：綜合分析指定車手在整場賽事中所有彎道的表現與穩定性")
        print("    輸入參數：年份、賽事、賽段類型、車手縮寫")
        print("    分析項目：")
        print("      [TARGET] 所有彎道的速度表現分布 (>= 50 km/h)")
        print("      [CHART] 入彎/出彎表現穩定性")
        print("      [FINISH] 與理想賽車線對比分析")
        print("      [STATS] 跨圈數的彎道表現一致性")
        print("      [STAR] 彎道表現評分與排名")
        print("      [STATS] Box-and-Whisker Plot 速度分布分析")
        print("      [TARGET] 雷達圖顯示所有彎道編號")
        print("      [CHART] 速度分布與穩定度複合圖")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • All_Corners_Performance_Summary (全彎道表現摘要表)")
        print("          - Columns: Corner_Number, Avg_Entry_Speed, Avg_Apex_Speed, Avg_Exit_Speed, Consistency_Score")
        print("        • Corner_Stability_Analysis (彎道穩定性分析表)")
        print("          - Columns: Corner_Number, Speed_Variance, Time_Variance, Performance_Rating, Improvement_Trend")
        print("        • Racing_Line_Comparison (賽車線對比表)")
        print("          - Columns: Corner_Number, Optimal_Line_Deviation, Speed_Loss, Performance_Gap")
        print("      [STATS] Figure輸出：")
        print("        • all_corners_heatmap.png (全彎道表現熱力圖)")
        print("        • corner_consistency_radar.png (彎道一致性雷達圖)")
        print("        • racing_line_deviation_map.png (賽車線偏差地圖)")
        print("        • corner_performance_trends.png (彎道表現趨勢圖)")
        print("      [NOTE] 分析報告：完整的彎道表現評估報告")
        
        print("\n👥 全部車手單圈分析模組 (選項12-13)")
        print("=" * 80)
        
        print("12. 👥 所有車手綜合分析 (All Drivers Comprehensive Analysis)")
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
        
        print("\n13. [F1] 彎道速度分析 (Corner Speed Analysis)")
        print("    功能描述：分析賽道各彎道的速度表現")
        print("    輸入參數：年份、賽事、賽段類型")
        print("    主要輸出：")
        print("      [STATS] Table格式：")
        print("        • Corner_Speed_Ranking (彎道速度排名表)")
        print("          - Columns: Corner, FastestDriver, Speed, AverageSpeed, SpeedVariation")
        print("        • Track_Sector_Analysis (賽道分段分析表)")
        print("          - Columns: Sector, BestTime, Driver, AverageTime, Difficulty_Rating")
        print("      [CHART] Figure輸出：")
        print("        • corner_speed_heatmap.png (彎道速度熱力圖)")
        print("        • track_difficulty_analysis.png (賽道難度分析)")
        
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
        
        print("\n[TOOL] 系統功能 (選項16-20)")
        print("=" * 80)
        
        print("16. [REFRESH] 重新載入賽事數據 (Reload Race Data)")
        print("    功能描述：重新選擇年份、賽事和賽段")
        print("    輸入參數：互動式選擇新的賽事參數")
        print("    主要輸出：資料載入狀態確認訊息")
        
        print("\n17. [PACKAGE] 顯示模組狀態 (Show Module Status)")
        print("    功能描述：檢查所有分析模組的載入狀態")
        print("    輸入參數：無")
        print("    主要輸出：各模組載入狀態列表和系統診斷資訊")
        
        print("\n18. 📖 顯示幫助信息 (Show Help)")
        print("    功能描述：顯示所有功能的詳細說明")
        print("    輸入參數：無")
        print("    主要輸出：完整的功能說明文件（即本文件）")
        
        print("\n19. [SAVE] 超車暫存管理 (Overtaking Cache Management)")
        print("    功能描述：管理超車分析的暫存檔案")
        print("    輸入參數：管理選項（列出、清除等）")
        print("    主要輸出：暫存檔案狀態和管理操作結果")
        
        print("\n20. [ARCHIVE] DNF暫存管理 (DNF Cache Management)")
        print("    功能描述：管理DNF分析的暫存檔案")
        print("    輸入參數：管理選項（列出、清除等）")
        print("    主要輸出：DNF暫存檔案狀態和管理操作結果")
        
        print("\n[SETTINGS]  設定功能 (字母選項)")
        print("=" * 80)
        
        print("S.  [SETTINGS] 重新設定賽事參數 (Change Race Settings)")
        print("    功能描述：重新設定分析的賽事參數")
        print("    輸入參數：互動式重新選擇年份、賽事、賽段")
        
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
        print("💡 快速開始：輸入功能編號(1-19)、字母選項(S/L/C/D)開始分析，輸入0退出")
        print("[REFRESH] 更新日期：2025年8月1日 | 版本：v5.3 (增強賽事顯示版)")
        print("=" * 80)

    def run_analysis(self, choice) -> bool:
        """執行選定的分析功能
        
        Args:
            choice: 使用者選擇的功能編號或字母
            
        Returns:
            bool: 是否繼續運行程式
        """
        try:
            # 調試輸出 - 幫助追蹤問題
            print(f"[CHECK] DEBUG: run_analysis 接收到參數: {repr(choice)} (類型: {type(choice)})")
            
            # 處理字母選項
            if choice == 'S':
                print("\n[SETTINGS] 重新設定賽事參數...")
                self.load_race_data_at_startup()
                return True
                
            elif choice == 'L':
                print("\n[INFO] 列出支援的賽事...")
                print_supported_races()
                return True
                
            elif choice == 'C':
                print("\n[CHECK] 暫存狀態檢查...")
                self.check_cache_status()
                return True
                
            elif choice == 'D':
                print("\n[CHECK] DNF暫存檢查...")
                self.check_dnf_cache()
                return True
            
            # 處理事故分析子模組選項 (4.1-4.5)
            elif choice == "4.1":  # 關鍵事件摘要
                if not self.session_loaded or not self.data_loader:
                    print("\n[ERROR] 尚未載入賽事數據！請先選擇選項18載入賽事數據")
                    return True
                print("\n[CHECK] 執行關鍵事件摘要分析...")
                self.run_accident_key_events_summary()
                return True
                
            elif choice == "4.2":  # 特殊事件報告
                if not self.session_loaded or not self.data_loader:
                    print("\n[ERROR] 尚未載入賽事數據！請先選擇選項18載入賽事數據")
                    return True
                print("\n[ALERT] 執行特殊事件報告分析...")
                self.run_accident_special_incidents()
                return True
                
            elif choice == "4.3":  # 車手嚴重程度分數統計
                if not self.session_loaded or not self.data_loader:
                    print("\n[ERROR] 尚未載入賽事數據！請先選擇選項18載入賽事數據")
                    return True
                print("\n🏆 執行車手嚴重程度分數統計...")
                self.run_accident_driver_severity_scores()
                return True
                
            elif choice == "4.4":  # 車隊風險分數統計
                if not self.session_loaded or not self.data_loader:
                    print("\n[ERROR] 尚未載入賽事數據！請先選擇選項18載入賽事數據")
                    return True
                print("\n[FINISH] 執行車隊風險分數統計...")
                self.run_accident_team_risk_scores()
                return True
                
            elif choice == "4.5":  # 所有事件詳細列表
                if not self.session_loaded or not self.data_loader:
                    print("\n[ERROR] 尚未載入賽事數據！請先選擇選項18載入賽事數據")
                    return True
                print("\n[INFO] 執行所有事件詳細列表...")
                self.run_accident_all_incidents_summary()
                return True
            
            # 處理遙測分析子模組選項 (6.1-6.7)
            elif choice == "6.1":  # 詳細圈次分析
                if not self.session_loaded or not self.data_loader:
                    print("\n[ERROR] 尚未載入賽事數據！請先選擇選項18載入賽事數據")
                    return True
                print("\n[CHART] 執行詳細圈次分析...")
                self.run_telemetry_complete_lap_analysis()
                return True
                
            elif choice == "6.2":  # 詳細輪胎策略分析
                if not self.session_loaded or not self.data_loader:
                    print("\n[ERROR] 尚未載入賽事數據！請先選擇選項18載入賽事數據")
                    return True
                print("\n[FINISH] 執行詳細輪胎策略分析...")
                self.run_telemetry_detailed_tire_strategy()
                return True
                
            elif choice == "6.3":  # 輪胎性能詳細分析
                if not self.session_loaded or not self.data_loader:
                    print("\n[ERROR] 尚未載入賽事數據！請先選擇選項18載入賽事數據")
                    return True
                print("\n[STATS] 執行輪胎性能詳細分析...")
                self.run_telemetry_tire_performance_analysis()
                return True
                
            elif choice == "6.4":  # 進站記錄
                if not self.session_loaded or not self.data_loader:
                    print("\n[ERROR] 尚未載入賽事數據！請先選擇選項18載入賽事數據")
                    return True
                print("\n[PIT] 執行進站記錄分析...")
                self.run_telemetry_pitstop_records()
                return True
                
            elif choice == "6.5":  # 特殊事件分析
                if not self.session_loaded or not self.data_loader:
                    print("\n[ERROR] 尚未載入賽事數據！請先選擇選項18載入賽事數據")
                    return True
                print("\n[ALERT] 執行特殊事件分析...")
                self.run_telemetry_special_events()
                return True
                
            elif choice == "6.6":  # 最快圈速度遙測數據
                if not self.session_loaded or not self.data_loader:
                    print("\n[ERROR] 尚未載入賽事數據！請先選擇選項18載入賽事數據")
                    return True
                print("\n[F1] 執行最快圈速度遙測數據...")
                self.run_telemetry_fastest_lap()
                return True
                
            elif choice == "6.7":  # 指定圈次完整遙測數據
                if not self.session_loaded or not self.data_loader:
                    print("\n[ERROR] 尚未載入賽事數據！請先選擇選項18載入賽事數據")
                    return True
                print("\n[STATS] 執行指定圈次完整遙測數據...")
                self.run_telemetry_specific_lap()
                return True
            
            # 處理子模組選項
            elif choice == "7.1":  # 速度差距分析
                if not self.session_loaded or not self.data_loader:
                    print("\n[ERROR] 尚未載入賽事數據！請先選擇選項18載入賽事數據")
                    return True
                print("\n[F1] 執行速度差距分析模組 (含原始數據輸出)...")
                try:
                    # 優先使用增強版分析，並自動選擇車手
                    from enhanced_gap_analysis_with_raw_data import enhance_gap_analysis_with_raw_data
                    enhance_gap_analysis_with_raw_data(self.data_loader, analysis_type="speed", auto_driver1="VER", auto_driver2="NOR")
                except ImportError:
                    # 後備使用原版分析
                    try:
                        from modules.speed_gap_analysis import run_speed_gap_analysis
                        run_speed_gap_analysis(self.data_loader, f1_analysis_instance=self.f1_analysis_instance)
                    except ImportError:
                        print("[ERROR] 速度差距分析模組未找到")
                return True
                
            elif choice == "7.2":  # 距離差距分析
                if not self.session_loaded or not self.data_loader:
                    print("\n[ERROR] 尚未載入賽事數據！請先選擇選項18載入賽事數據")
                    return True
                print("\n📏 執行距離差距分析模組 (含原始數據輸出)...")
                try:
                    # 優先使用增強版分析，並自動選擇車手
                    from enhanced_gap_analysis_with_raw_data import enhance_gap_analysis_with_raw_data
                    enhance_gap_analysis_with_raw_data(self.data_loader, analysis_type="distance", auto_driver1="VER", auto_driver2="NOR")
                except ImportError:
                    # 後備使用原版分析
                    try:
                        from modules.distance_gap_analysis import run_distance_gap_analysis
                        run_distance_gap_analysis(self.data_loader, f1_analysis_instance=self.f1_analysis_instance)
                    except ImportError:
                        print("[ERROR] 距離差距分析模組未找到")
                return True
            
            elif choice == "11.1":  # 詳細DNF與責任事故分析
                print("\n[ALERT] 執行詳細DNF與責任事故分析模組...")
                try:
                    from modules.single_driver_dnf_detailed import run_single_driver_detailed_dnf_analysis
                    result = run_single_driver_detailed_dnf_analysis(self.data_loader)
                    
                    if result:
                        print("[OK] 詳細DNF與責任事故分析完成")
                    else:
                        print("[ERROR] 詳細DNF與責任事故分析失敗")
                        
                except Exception as e:
                    print(f"[ERROR] 執行詳細DNF與責任事故分析時發生錯誤: {e}")
                    import traceback
                    traceback.print_exc()
                return True
            
            elif choice == "11.2":  # 年度DNF統計摘要
                print("\n[STATS] 執行年度DNF統計摘要分析模組...")
                try:
                    from modules.annual_dnf_statistics import run_annual_dnf_statistics_analysis
                    result = run_annual_dnf_statistics_analysis(2024)
                    
                    if result:
                        print("[OK] 年度DNF統計摘要分析完成")
                    else:
                        print("[ERROR] 年度DNF統計摘要分析失敗")
                        
                except Exception as e:
                    print(f"[ERROR] 執行年度DNF統計摘要分析時發生錯誤: {e}")
                    import traceback
                    traceback.print_exc()
                return True
            
            elif choice == "14.1":  # 車手數據統計總覽
                if not self.session_loaded or not self.data_loader:
                    print("\n[ERROR] 尚未載入賽事數據！請先選擇選項18載入賽事數據")
                    return True
                print("\n[STATS] 執行車手數據統計總覽...")
                try:
                    from modules.driver_statistics_overview import run_driver_statistics_overview
                    run_driver_statistics_overview(self.data_loader, self.dynamic_team_mapping, self.f1_analysis_instance)
                    print("[OK] 車手數據統計總覽完成")
                except ImportError as e:
                    print(f"[ERROR] 模組導入失敗: {e}")
                    print("請確認 modules/driver_statistics_overview.py 檔案存在")
                except Exception as e:
                    print(f"[ERROR] 執行車手數據統計總覽時發生錯誤: {e}")
                    import traceback
                    traceback.print_exc()
                return True
                    
            elif choice == "14.2":  # 車手遙測資料統計
                if not self.session_loaded or not self.data_loader:
                    print("\n[ERROR] 尚未載入賽事數據！請先選擇選項18載入賽事數據")
                    return True
                print("\n[TOOL] 執行車手遙測資料統計...")
                try:
                    from modules.driver_telemetry_statistics import run_driver_telemetry_statistics
                    run_driver_telemetry_statistics(self.data_loader, self.dynamic_team_mapping, self.f1_analysis_instance)
                    print("[OK] 車手遙測資料統計完成")
                except ImportError as e:
                    print(f"[ERROR] 模組導入失敗: {e}")
                    print("請確認 modules/driver_telemetry_statistics.py 檔案存在")
                except Exception as e:
                    print(f"[ERROR] 執行車手遙測資料統計時發生錯誤: {e}")
                    import traceback
                    traceback.print_exc()
                return True
                    
            elif choice == "14.3":  # 車手超車分析
                if not self.session_loaded or not self.data_loader:
                    print("\n[ERROR] 尚未載入賽事數據！請先選擇選項18載入賽事數據")
                    return True
                print("\n[START] 執行車手超車分析...")
                try:
                    from modules.driver_overtaking_analysis import run_driver_overtaking_analysis
                    run_driver_overtaking_analysis(self.data_loader, self.dynamic_team_mapping, self.f1_analysis_instance)
                    print("[OK] 車手超車分析完成")
                except ImportError as e:
                    print(f"[ERROR] 模組導入失敗: {e}")
                    print("請確認 modules/driver_overtaking_analysis.py 檔案存在")
                except Exception as e:
                    print(f"[ERROR] 執行車手超車分析時發生錯誤: {e}")
                    import traceback
                    traceback.print_exc()
                return True
                
            elif choice.lower().strip() == '14.4':
                # Function 14.4: 🏆 最速圈排名分析 - 含區間時間
                if not self.session_loaded:
                    print("\n[ERROR] 尚未載入賽事數據！請先選擇選項18載入賽事數據")
                    return True
                print("\n[START] 執行最速圈排名分析...")
                try:
                    from modules.driver_fastest_lap_ranking import run_driver_fastest_lap_ranking
                    run_driver_fastest_lap_ranking(self.data_loader, self.dynamic_team_mapping, self.f1_analysis_instance)
                    print("[OK] 最速圈排名分析完成")
                except ImportError as e:
                    print(f"[ERROR] 模組導入失敗: {e}")
                    print("請確認 modules/driver_fastest_lap_ranking.py 檔案存在")
                except Exception as e:
                    print(f"[ERROR] 執行最速圈排名分析時發生錯誤: {e}")
                    import traceback
                    traceback.print_exc()
                return True
            
            # 處理數字選項
            if choice == 0:
                print("\n👋 感謝使用F1分析CLI模組化版本！")
                return False
                
            elif choice == 18:  # 重新載入賽事數據
                print("\n[REFRESH] 重新載入賽事數據...")
                self.load_race_data_at_startup()
                
            elif choice == 19:  # 顯示模組狀態
                self.show_module_status()
                
            elif choice == 20:  # 顯示幫助信息
                self.show_help()
                
            elif choice == 21:  # 超車暫存管理
                print("\n[SAVE] 超車暫存管理...")
                self.manage_overtaking_cache()
                
            elif choice == 22:  # DNF暫存管理
                print("\n[ARCHIVE] DNF暫存管理...")
                self.manage_dnf_cache()
            
            # 處理字符串格式的子功能選項
            elif choice == "12.1":  # 單一車手詳細彎道分析 (增強版)
                print("\n[F1] 執行單一車手詳細彎道分析 (增強版)...")
                try:
                    print("[CHECK] 自動選擇車手: LEC")
                    print("[TARGET] 自動選擇彎道: 第 1 彎")
                    print("[STATS] 含 JSON 原始數據輸出 + 進站與事件資料")
                    
                    result = run_single_driver_corner_analysis_integrated(self.data_loader, f1_analysis_instance=self.f1_analysis_instance)
                    
                    if result:
                        print("[OK] 單一車手詳細彎道分析完成")
                    else:
                        print("[ERROR] 單一車手詳細彎道分析失敗")
                        
                except Exception as e:
                    print(f"[ERROR] 執行單一車手詳細彎道分析時發生錯誤: {e}")
                    import traceback
                    traceback.print_exc()
            
            elif choice == "12.2":  # 團隊車手對比彎道分析
                print("\n🆚 執行團隊車手對比彎道分析...")
                try:
                    print("[CHECK] 自動選擇車手: VER vs NOR")
                    print("[TARGET] 自動選擇彎道: 第 1 彎")
                    print("[STATS] 含 JSON 原始數據輸出 + 進站與事件資料")
                    
                    result = run_team_drivers_corner_comparison_integrated(self.data_loader, f1_analysis_instance=self.f1_analysis_instance)
                    
                    if result:
                        print("[OK] 團隊車手對比彎道分析完成")
                    else:
                        print("[ERROR] 團隊車手對比彎道分析失敗")
                        
                except Exception as e:
                    print(f"[ERROR] 執行團隊車手對比彎道分析時發生錯誤: {e}")
                    import traceback
                    traceback.print_exc()
                
            # Function 16 子選項處理 - 全部車手超車分析
            elif choice == "16.1":  # 年度超車統計
                if not self.session_loaded or not self.data_loader:
                    print("\n[ERROR] 尚未載入賽事數據！請先選擇選項18載入賽事數據")
                    return True
                print("\n[STATS] 執行年度超車統計分析...")
                try:
                    success = run_all_drivers_annual_overtaking_statistics(
                        self.data_loader, 
                        self.dynamic_team_mapping, 
                        self.f1_analysis_instance
                    )
                    if success:
                        print("[OK] 年度超車統計分析完成")
                    else:
                        print("[ERROR] 年度超車統計分析失敗")
                except Exception as e:
                    print(f"[ERROR] 執行年度超車統計分析時發生錯誤: {e}")
                    import traceback
                    traceback.print_exc()
                    
            elif choice == "16.2":  # 表現比較分析
                if not self.session_loaded or not self.data_loader:
                    print("\n[ERROR] 尚未載入賽事數據！請先選擇選項18載入賽事數據")
                    return True
                print("\n[FINISH] 執行表現比較分析...")
                try:
                    success = run_all_drivers_overtaking_performance_comparison(
                        self.data_loader, 
                        self.dynamic_team_mapping, 
                        self.f1_analysis_instance
                    )
                    if success:
                        print("[OK] 表現比較分析完成")
                    else:
                        print("[ERROR] 表現比較分析失敗")
                except Exception as e:
                    print(f"[ERROR] 執行表現比較分析時發生錯誤: {e}")
                    import traceback
                    traceback.print_exc()
                    
            elif choice == "16.3":  # 視覺化分析
                if not self.session_loaded or not self.data_loader:
                    print("\n[ERROR] 尚未載入賽事數據！請先選擇選項18載入賽事數據")
                    return True
                print("\n[CHART] 執行視覺化分析...")
                try:
                    success = run_all_drivers_overtaking_visualization_analysis(
                        self.data_loader, 
                        self.dynamic_team_mapping, 
                        self.f1_analysis_instance
                    )
                    if success:
                        print("[OK] 視覺化分析完成")
                    else:
                        print("[ERROR] 視覺化分析失敗")
                except Exception as e:
                    print(f"[ERROR] 執行視覺化分析時發生錯誤: {e}")
                    import traceback
                    traceback.print_exc()
                    
            elif choice == "16.4":  # 趨勢分析
                if not self.session_loaded or not self.data_loader:
                    print("\n[ERROR] 尚未載入賽事數據！請先選擇選項18載入賽事數據")
                    return True
                print("\n[CHART] 執行趨勢分析...")
                try:
                    success = run_all_drivers_overtaking_trends_analysis(
                        self.data_loader, 
                        self.dynamic_team_mapping, 
                        self.f1_analysis_instance
                    )
                    if success:
                        print("[OK] 趨勢分析完成")
                    else:
                        print("[ERROR] 趨勢分析失敗")
                except Exception as e:
                    print(f"[ERROR] 執行趨勢分析時發生錯誤: {e}")
                    import traceback
                    traceback.print_exc()
                
            elif choice in range(1, 23) or (isinstance(choice, str) and choice.isdigit() and int(choice) in range(1, 23)):
                # 轉換字符串為整數
                if isinstance(choice, str) and choice.isdigit():
                    choice = int(choice)
                    
                # 檢查是否已載入數據
                if not self.session_loaded or not self.data_loader:
                    print("\n[ERROR] 尚未載入賽事數據！")
                    print("請先選擇選項18載入賽事數據，或重新啟動程式")
                    return True
                
                # 執行分析功能 - 重新排列後的順序
                if choice == 1:  # 降雨強度分析
                    self.run_rain_intensity_analysis()
                    
                elif choice == 2:  # 賽道位置分析 (Raw Data版本)
                    print("\n[TRACK] 執行賽道位置分析模組 (Raw Data表格版本)...")
                    try:
                        from modules.track_position_analysis import run_track_position_analysis
                        run_track_position_analysis(self.data_loader)
                    except ImportError:
                        print("[ERROR] 賽道位置分析模組未找到")
                        # 後備方案：使用舊版分析
                        run_track_path_analysis(self.data_loader, self.dynamic_team_mapping, self.f1_analysis_instance)
                    
                elif choice == 3:  # 進站策略分析
                    print("\n[PIT] 執行進站策略分析模組...")
                    
                    # 也可以執行完整的進站策略分析
                    try:
                        from modules.pitstop_analysis_complete import run_pitstop_analysis
                        run_pitstop_analysis(self.data_loader, self.dynamic_team_mapping, f1_analysis_instance=self.f1_analysis_instance)
                    except ImportError:
                        try:
                            from modules.pitstop_analysis import run_pitstop_analysis
                            run_pitstop_analysis(self.data_loader, f1_analysis_instance=self.f1_analysis_instance)
                        except ImportError:
                            print("[ERROR] 進站策略分析模組未找到")
                    
                elif choice == 4:  # 獨立事故分析 (一般模式)
                    print("\n 執行事故分析模組...")
                    try:
                        from modules.accident_analysis_complete import run_accident_analysis
                        run_accident_analysis(self.data_loader, self.dynamic_team_mapping, f1_analysis_instance=self.f1_analysis_instance)
                    except ImportError:
                        try:
                            from modules.accident_analysis import run_accident_analysis
                            run_accident_analysis(self.data_loader, self.dynamic_team_mapping, f1_analysis_instance=self.f1_analysis_instance)
                        except ImportError:
                            print("[ERROR] 事故分析模組未找到")
                    
                elif choice == 5:  # 單一車手綜合分析
                    print("\n[F1]  執行單一車手綜合分析模組...")
                    run_single_driver_comprehensive_analysis(self.data_loader, self.dynamic_team_mapping)
                    
                elif choice == 6:  # 單一車手詳細遙測分析 (一般模式) - 安全檢查
                    print(f"[CHECK] DEBUG: 觸發功能 6，choice={repr(choice)}")
                    print("📡 執行單一車手詳細遙測分析模組...")
                    try:
                        from modules.single_driver_detailed_telemetry import run_single_driver_detailed_telemetry_analysis
                        run_single_driver_detailed_telemetry_analysis(self.data_loader, f1_analysis_instance=self.f1_analysis_instance)
                    except ImportError:
                        print("[ERROR] 單一車手詳細遙測分析模組未找到")
                    
                elif choice == 7:  # 雙車手比較分析
                    print("\n🆚 執行雙車手比較分析模組...")
                    run_driver_comparison_analysis(self.data_loader)
                    
                elif choice == 8:  # 賽事位置變化圖 (僅數據，不生成圖片)
                    print("\n[STATS] 執行賽事位置變化圖分析...")
                    try:
                        # 使用專門的位置變化圖工具
                        from race_position_chart import RacePositionChartGenerator
                        
                        generator = RacePositionChartGenerator()
                        generator.data_loader = self.data_loader
                        
                        # 自動選擇車手
                        driver_input = "VER"  # 預設車手
                        print(f"[CHECK] 自動選擇車手: {driver_input}")
                        
                        # 使用當前載入的賽事數據
                        year = self.data_loader.current_year if hasattr(self.data_loader, 'current_year') else 2025
                        race = self.data_loader.current_race if hasattr(self.data_loader, 'current_race') else "Japan"
                        
                        # 僅生成數據，不生成圖片
                        success = generator.generate_position_changes_chart(driver_input, year, race, generate_chart=False)
                        
                        if success:
                            print("[OK] 位置變化圖分析完成")
                        else:
                            print("[ERROR] 位置變化圖分析失敗")
                            
                    except Exception as e:
                        print(f"[ERROR] 位置變化圖生成失敗: {e}")
                        import traceback
                        traceback.print_exc()
                    
                elif choice == 9:  # 賽事超車統計分析 (Raw Data輸出版)
                    print("\n[CHART] 執行賽事超車統計分析...")
                    try:
                        # 使用完整的超車分析功能，但專注於Raw Data輸出
                        print("[FINISH] 啟動超車統計分析模組...")
                        
                        # 自動選擇車手
                        driver_input = "VER"  # 預設車手
                        print(f"[CHECK] 自動選擇車手: {driver_input}")
                        
                        # 使用當前載入的賽事數據
                        year = self.data_loader.current_year if hasattr(self.data_loader, 'current_year') else 2025
                        
                        print(f"[STATS] 分析 {driver_input} 在 {year} 年的超車統計...")
                        print("[REFRESH] 載入超車分析模組...")
                        
                        # 使用完整的超車分析功能
                        from modules.single_driver_overtaking_advanced import SingleDriverOvertakingAdvanced
                        analyzer = SingleDriverOvertakingAdvanced(self.data_loader)
                        
                        # 執行分析並顯示Raw Data
                        result = analyzer.analyze_single_driver_overtaking(driver_input, [year])
                        
                        if result:
                            print("[OK] 超車統計分析完成")
                            print("\n[INFO] Raw Data 超車統計摘要:")
                            print(f"車手: {driver_input}")
                            print(f"分析年份: {year}")
                            print(f"分析結果已保存到相應檔案")
                        else:
                            print("[ERROR] 超車統計分析失敗")
                            
                    except Exception as e:
                        print(f"[ERROR] 超車統計分析失敗: {e}")
                        import traceback
                        traceback.print_exc()
                    
                elif choice == 10:  # 單一車手超車分析 (完整統計分析)
                    print("\n[FINISH] 執行單一車手超車分析模組...")
                    run_single_driver_overtaking_analysis(self.data_loader, f1_analysis_instance=self.f1_analysis_instance)
                    
                elif choice == 11:  # 獨立單一車手DNF分析
                    print("\n[TOOL] 執行獨立單一車手DNF分析模組...")
                    try:
                        from modules.all_drivers_dnf_advanced import AllDriversDNFAdvanced
                        from modules.data_loader import F1DataLoader
                        
                        # 初始化資料載入器和DNF分析器
                        data_loader = F1DataLoader()
                        dnf_analyzer = AllDriversDNFAdvanced(data_loader)
                        
                        # 執行單一車手詳細DNF分析
                        result = dnf_analyzer.run_single_driver_detailed_dnf_analysis()
                        
                        if result:
                            print("[OK] 獨立單一車手DNF分析完成")
                        else:
                            print("[ERROR] 獨立單一車手DNF分析失敗")
                            
                    except ImportError as e:
                        print(f"[ERROR] 模組導入失敗: {e}")
                    except Exception as e:
                        print(f"[ERROR] 執行獨立單一車手DNF分析時發生錯誤: {e}")
                        import traceback
                        traceback.print_exc()
                
                elif choice == 11.1:  # 詳細DNF與責任事故分析
                    print("\n[ALERT] 執行詳細DNF與責任事故分析模組...")
                    try:
                        from modules.single_driver_dnf_detailed import run_single_driver_detailed_dnf_analysis
                        result = run_single_driver_detailed_dnf_analysis(self.data_loader)
                        
                        if result:
                            print("[OK] 詳細DNF與責任事故分析完成")
                        else:
                            print("[ERROR] 詳細DNF與責任事故分析失敗")
                            
                    except Exception as e:
                        print(f"[ERROR] 執行詳細DNF與責任事故分析時發生錯誤: {e}")
                        import traceback
                        traceback.print_exc()
                
                elif choice == 11.2:  # 年度DNF統計摘要
                    print("\n[STATS] 執行年度DNF統計摘要分析模組...")
                    try:
                        from modules.annual_dnf_statistics import run_annual_dnf_statistics_analysis
                        result = run_annual_dnf_statistics_analysis(2024)
                        
                        if result:
                            print("[OK] 年度DNF統計摘要分析完成")
                        else:
                            print("[ERROR] 年度DNF統計摘要分析失敗")
                            
                    except Exception as e:
                        print(f"[ERROR] 執行年度DNF統計摘要分析時發生錯誤: {e}")
                        import traceback
                        traceback.print_exc()
                    
                elif choice == 12:  # 單賽事指定彎道詳細分析
                    print("\n[TARGET] 執行單一車手詳細彎道分析模組...")
                    run_single_driver_detailed_corner_analysis(self.data_loader, f1_analysis_instance=self.f1_analysis_instance)
                    
                elif choice == 13:  # 單一車手指定賽事全部彎道詳細分析
                    print("\n[STATS] 執行單一車手指定賽事全部彎道詳細分析模組...")
                    print("[TARGET] 包含Box-and-Whisker速度分析、雷達圖彎道編號顯示、速度與穩定度複合圖")
                    try:
                        from modules.single_driver_all_corners_detailed_analysis import run_single_driver_all_corners_detailed_analysis
                        run_single_driver_all_corners_detailed_analysis(self.data_loader, f1_analysis_instance=self.f1_analysis_instance)
                        print("[OK] 單一車手指定賽事全部彎道詳細分析完成")
                    except ImportError as e:
                        print(f"[ERROR] 模組導入失敗: {e}")
                        print("請確認 modules/single_driver_all_corners_detailed_analysis.py 檔案存在")
                    except Exception as e:
                        print(f"[ERROR] 執行單一車手指定賽事全部彎道詳細分析時發生錯誤: {e}")
                        import traceback
                        traceback.print_exc()
                    
                elif choice == 14:  # 保留原有功能作為14.9 (所有車手綜合分析) - 使用統一映射器
                    print("\n👥 執行所有車手綜合分析模組...")
                    result = self.function_mapper.execute_function(21)  # Function 21: 所有車手綜合分析
                    if result:
                        print("[OK] 所有車手綜合分析完成！")
                    else:
                        print("[ERROR] 所有車手綜合分析執行失敗")
                    
                elif choice == 15:  # 彎道速度分析
                    print("\n[F1]  執行彎道速度分析模組...")
                    run_corner_speed_analysis(self.data_loader, self.f1_analysis_instance)
                    
                elif choice == 16:  # 全部車手超車分析子選單
                    self._show_function_16_submenu()
                    
                elif choice == 17:  # 獨立全部車手DNF分析
                    print("\n[STATS] 執行全部車手DNF與責任分析模組...")
                    try:
                        from modules.all_drivers_dnf_advanced import AllDriversDNFAdvanced
                        
                        # 使用完全復刻 f1_analysis_cli_new.py 選項 10 的功能
                        dnf_analyzer = AllDriversDNFAdvanced(self.data_loader)
                        dnf_analyzer.run_analysis()
                        print("[OK] 全部車手DNF與責任分析完成")
                        
                    except ImportError as e:
                        print(f"[ERROR] 模組導入失敗: {e}")
                        print("請確認 modules/all_drivers_dnf_advanced.py 檔案存在")
                    except Exception as e:
                        print(f"[ERROR] 執行全部車手DNF與責任分析時發生錯誤: {e}")
                        import traceback
                        traceback.print_exc()
                
                # 新增的彎道分析子功能
                elif choice == "12.1":  # 單一車手詳細彎道分析 (增強版)
                    print("\n[F1] 執行單一車手詳細彎道分析 (增強版)...")
                    try:
                        print("[CHECK] 自動選擇車手: LEC")
                        print("[TARGET] 自動選擇彎道: 第 1 彎")
                        print("[STATS] 含 JSON 原始數據輸出 + 進站與事件資料")
                        
                        result = run_single_driver_corner_analysis_integrated(self.data_loader, f1_analysis_instance=self.f1_analysis_instance)
                        
                        if result:
                            print("[OK] 單一車手詳細彎道分析完成")
                        else:
                            print("[ERROR] 單一車手詳細彎道分析失敗")
                            
                    except Exception as e:
                        print(f"[ERROR] 執行單一車手詳細彎道分析時發生錯誤: {e}")
                        import traceback
                        traceback.print_exc()
                
                elif choice == "12.2":  # 團隊車手對比彎道分析
                    print("\n🆚 執行團隊車手對比彎道分析...")
                    try:
                        print("[CHECK] 自動選擇車手: VER vs NOR")
                        print("[TARGET] 自動選擇彎道: 第 1 彎")
                        print("[STATS] 含 JSON 原始數據輸出 + 進站與事件資料")
                        
                        result = run_team_drivers_corner_comparison_integrated(self.data_loader, f1_analysis_instance=self.f1_analysis_instance)
                        
                        if result:
                            print("[OK] 團隊車手對比彎道分析完成")
                        else:
                            print("[ERROR] 團隊車手對比彎道分析失敗")
                            
                    except Exception as e:
                        print(f"[ERROR] 執行團隊車手對比彎道分析時發生錯誤: {e}")
                        import traceback
                        traceback.print_exc()
                
            else:
                print("[ERROR] 無效的選項，請選擇 0-22、字母選項 S, L, C, D 或子模組選項 14.1-14.3, 16.1-16.4, 7.1, 7.2, 12.1, 12.2")
                
        except KeyboardInterrupt:
            print("\n\n[WARNING]  使用者中斷操作")
            return False
        except Exception as e:
            print(f"\n[ERROR] 執行分析時發生錯誤: {e}")
            print("請檢查模組是否正確安裝，或聯繫技術支援")
            
        return True

    def check_cache_status(self):
        """檢查暫存狀態"""
        print("\n[CHECK] 暫存狀態檢查")
        print("=" * 50)
        
        cache_dirs = [
            ("cache", "基礎暫存目錄"),
            ("f1_cache", "F1數據暫存"),
            ("f1_analysis_cache", "F1分析暫存"),
            ("overtaking_cache", "超車分析暫存"),
            ("corner_analysis_cache", "彎道分析暫存"),
            ("dnf_analysis_cache", "DNF分析暫存")
        ]
        
        for cache_dir, description in cache_dirs:
            cache_path = os.path.join(os.getcwd(), cache_dir)
            if os.path.exists(cache_path):
                file_count = len([f for f in os.listdir(cache_path) if os.path.isfile(os.path.join(cache_path, f))])
                print(f"[OK] {description}: {file_count} 個檔案")
            else:
                print(f"[ERROR] {description}: 目錄不存在")
        
        print("=" * 50)

    def check_dnf_cache(self):
        """檢查DNF暫存狀態"""
        print("\n[CHECK] DNF暫存檢查")
        print("=" * 50)
        
        dnf_cache_dir = os.path.join(os.getcwd(), "dnf_analysis_cache")
        if os.path.exists(dnf_cache_dir):
            files = os.listdir(dnf_cache_dir)
            txt_files = [f for f in files if f.endswith('.txt')]
            png_files = [f for f in files if f.endswith('.png')]
            
            print(f"[STATS] DNF分析文字檔案: {len(txt_files)} 個")
            print(f"[CHART] DNF分析圖表檔案: {len(png_files)} 個")
            
            if txt_files:
                print("\n📄 最近的DNF分析文字檔案:")
                for txt_file in sorted(txt_files)[-5:]:  # 顯示最新的5個檔案
                    print(f"   • {txt_file}")
        else:
            print("[ERROR] DNF暫存目錄不存在")
        
        print("=" * 50)

    def manage_overtaking_cache(self):
        """管理超車暫存檔案"""
        print("\n[SAVE] 超車暫存管理")
        print("=" * 50)
        
        overtaking_cache_dir = os.path.join(os.getcwd(), "overtaking_cache")
        if not os.path.exists(overtaking_cache_dir):
            print("[ERROR] 超車暫存目錄不存在")
            return
        
        files = os.listdir(overtaking_cache_dir)
        if not files:
            print("[FOLDER] 超車暫存目錄為空")
            return
        
        print(f"[STATS] 找到 {len(files)} 個超車暫存檔案")
        print("\n選項:")
        print("1. 列出所有檔案")
        print("2. 清除所有暫存檔案")
        print("3. 返回主選單")
        
        try:
            choice = input("\n請選擇 (1-3): ").strip()
            
            if choice == '1':
                print("\n[INFO] 超車暫存檔案列表:")
                for i, file in enumerate(sorted(files), 1):
                    file_path = os.path.join(overtaking_cache_dir, file)
                    file_size = os.path.getsize(file_path)
                    print(f"   {i:2d}. {file} ({file_size} bytes)")
                    
            elif choice == '2':
                confirm = input("[WARNING] 確定要清除所有超車暫存檔案嗎? (y/N): ").strip().lower()
                if confirm == 'y':
                    for file in files:
                        os.remove(os.path.join(overtaking_cache_dir, file))
                    print("[OK] 所有超車暫存檔案已清除")
                else:
                    print("[ERROR] 取消清除操作")
                    
        except Exception as e:
            print(f"[ERROR] 管理超車暫存時發生錯誤: {e}")
        
        print("=" * 50)

    def manage_dnf_cache(self):
        """管理DNF暫存檔案"""
        print("\n[ARCHIVE] DNF暫存管理")
        print("=" * 50)
        
        dnf_cache_dir = os.path.join(os.getcwd(), "dnf_analysis_cache")
        if not os.path.exists(dnf_cache_dir):
            print("[ERROR] DNF暫存目錄不存在")
            return
        
        files = os.listdir(dnf_cache_dir)
        if not files:
            print("[FOLDER] DNF暫存目錄為空")
            return
        
        txt_files = [f for f in files if f.endswith('.txt')]
        png_files = [f for f in files if f.endswith('.png')]
        
        print(f"[STATS] 找到 {len(txt_files)} 個DNF分析文字檔案")
        print(f"[CHART] 找到 {len(png_files)} 個DNF分析圖表檔案")
        
        print("\n選項:")
        print("1. 列出文字檔案")
        print("2. 列出圖表檔案")
        print("3. 清除所有DNF暫存檔案")
        print("4. 返回主選單")
        
        try:
            choice = input("\n請選擇 (1-4): ").strip()
            
            if choice == '1':
                print("\n📄 DNF分析文字檔案:")
                for i, file in enumerate(sorted(txt_files), 1):
                    print(f"   {i:2d}. {file}")
                    
            elif choice == '2':
                print("\n[CHART] DNF分析圖表檔案:")
                for i, file in enumerate(sorted(png_files), 1):
                    print(f"   {i:2d}. {file}")
                    
            elif choice == '3':
                confirm = input("[WARNING] 確定要清除所有DNF暫存檔案嗎? (y/N): ").strip().lower()
                if confirm == 'y':
                    for file in files:
                        os.remove(os.path.join(dnf_cache_dir, file))
                    print("[OK] 所有DNF暫存檔案已清除")
                else:
                    print("[ERROR] 取消清除操作")
                    
        except Exception as e:
            print(f"[ERROR] 管理DNF暫存時發生錯誤: {e}")
        
        print("=" * 50)

    def get_user_choice(self) -> Optional[str]:
        """獲取使用者選擇"""
        try:
            choice_str = input("\n請選擇功能 (0-22, 4.1-4.5, 6.1-6.7, 7.1, 7.2, 14.1-14.3, 16.1-16.4, S, L, C, D): ").strip().upper()
            if not choice_str:
                return None
            
            # 處理字母選項
            if choice_str in ['S', 'L', 'C', 'D']:
                return choice_str
            
            # 處理子模組選項
            if choice_str in ['4.1', '4.2', '4.3', '4.4', '4.5', '6.1', '6.2', '6.3', '6.4', '6.5', '6.6', '6.7', '7.1', '7.2', '14.1', '14.2', '14.3']:
                return choice_str
            
            # 處理數字選項
            return int(choice_str)
        except ValueError:
            if choice_str in ['S', 'L', 'C', 'D', '4.1', '4.2', '4.3', '4.4', '4.5', '6.1', '6.2', '6.3', '6.4', '6.5', '6.6', '6.7', '7.1', '7.2', '14.1', '14.2', '14.3']:
                return choice_str
            print("[ERROR] 請輸入有效的數字或選項 (S, L, C, D, 4.1-4.5, 6.1-6.7, 7.1, 7.2, 14.1-14.3, 16.1-16.4)")
            return None
        except KeyboardInterrupt:
            print("\n\n👋 程式已被使用者中斷")
            return 0

    def run(self):
        """主運行迴圈"""
        self.display_header()
        
        print(f"\n[OK] 模組化F1分析系統已啟動")
        print(f"[FILES] 模組目錄: {modules_dir}")
        print(f"[PYTHON] Python版本: {sys.version.split()[0]}")
        
        # 檢查是否為參數模式
        if self.args and (self.args.year or self.args.race or self.args.session or self.args.function):
            print("\n[START] 參數模式啟動...")
            return self.run_parameter_mode()
        
        # 互動模式
        print("\n[START] 系統初始化中...")
        if not self.load_race_data_at_startup():
            print("\n[WARNING] 數據載入失敗，但您仍可使用系統功能 (選項18-22)")
            print("若要執行分析功能，請使用選項18重新載入數據")
        
        while True:
            self.display_menu()
            choice = self.get_user_choice()
            
            if choice is None:
                continue
                
            if not self.run_analysis(choice):
                break
                
            input("\n按 Enter 鍵繼續...")

    def run_parameter_mode(self):
        """參數模式運行 - 使用統一功能映射器"""
        print("=" * 60)
        print("[TOOL] 參數化模式 - 符合核心開發原則")
        print("=" * 60)
        
        # 載入數據
        year = self.args.year if self.args.year else 2025
        race = self.args.race if self.args.race else "Japan"
        session = self.args.session if self.args.session else "R"
        
        print(f"[STATS] 載入參數: Year={year}, Race={race}, Session={session}")
        
        if not self.load_race_data_from_args(year, race, session):
            print("[ERROR] 參數模式數據載入失敗")
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
                return False
        else:
            print("[ERROR] 參數模式需要指定功能編號 (-f)")
            print("範例: python f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 1")
            return False


def create_argument_parser():
    """創建命令行參數解析器"""
    parser = argparse.ArgumentParser(
        description='F1 Analysis CLI - 模組化主程式 v5.3',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用範例:
  # 互動模式 (預設)
  python f1_analysis_modular_main.py
  
  # 載入特定賽事後進入互動模式
  python f1_analysis_modular_main.py -y 2025 -r Japan -s R
  
  # 直接執行降雨強度分析
  python f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 1
  
  # 執行速度差距分析 (指定車手)
  python f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 7.1 -d VER -d2 LEC
  
  # 執行詳細DNF分析 (指定車手)
  python f1_analysis_modular_main.py -y 2025 -r Japan -s R -f 11.1 -d VER
  
  # 顯示模組狀態
  python f1_analysis_modular_main.py -f 19
  
  # 顯示幫助
  python f1_analysis_modular_main.py -f 20

功能編號對照:
  [RAIN]  基礎分析模組:
  1  [RAIN] 降雨強度分析              3  [PIT] 進站策略分析
  2  [TRACK] 賽道路線分析                 ├── 3.1 [CHECK] 關鍵事件摘要
                                    ├── 3.2 [ALERT] 特殊事件報告
                                    ├── 3.3 🏆 車手嚴重程度分數統計
                                    ├── 3.4 [FINISH] 車隊風險分數統計
                                    └── 3.5 [INFO] 所有事件詳細列表
  4  💥 獨立事故分析
  
  👤 單車手單圈分析模組:
  5  [F1] 單一車手綜合分析          8  [FINISH] 單一車手超車分析
  6  📡 單一車手詳細遙測分析      9  [TOOL] 獨立單一車手DNF分析
  7  [BALANCE] 車手對比分析            10 [TARGET] 單賽事指定彎道詳細分析
                                 11 [STATS] 單一車手指定賽事全部彎道詳細分析
  
  👥 全部車手單圈分析模組:
  12 👥 所有車手綜合分析         15 [F1] 彎道速度分析
  14.1 [STATS] 車手數據統計總覽       14.2 [TOOL] 車手遙測資料統計
  14.3 [START] 車手超車分析          14.9 👥 所有車手綜合分析
  
  🏆 全部車手全年分析模組:
  16 [START] 全部車手超車分析         17 [STATS] 獨立全部車手DNF分析
      ├── 16.1 [STATS] 年度超車統計
      ├── 16.2 [FINISH] 表現比較分析
      ├── 16.3 [CHART] 視覺化分析
      └── 16.4 [CHART] 趨勢分析
  
  [TOOL] 系統功能:
  18 [REFRESH] 重新載入賽事數據         21 [SAVE] 超車暫存管理
  19 [PACKAGE] 顯示模組狀態            22 [ARCHIVE] DNF暫存管理
  20 📖 顯示幫助信息
  
  [SETTINGS]  設定功能:
  S  [SETTINGS] 重新設定賽事參數          C  [CHECK] 暫存狀態檢查
  L  [INFO] 列出支援的賽事            D  [CHECK] DNF暫存檢查
        '''
    )
    
    # 賽事參數
    parser.add_argument('-y', '--year', type=int, choices=[2024, 2025], 
                       help='賽季年份 (2024 或 2025)')
    parser.add_argument('-r', '--race', type=str,
                       help='賽事名稱 (如: Japan, Bahrain, Australia 等)')
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
    parser.add_argument('--corner', type=int,
                       help='指定彎道編號 (用於彎道詳細分析，如: 1, 2, 3 等)')
    
    # 額外選項
    parser.add_argument('--list-races', action='store_true',
                       help='列出支援的賽事列表')
    parser.add_argument('--show-detailed-output', action='store_true', default=True,
                       help='即使使用緩存數據也顯示詳細的表格輸出 (預設啟用)')
    parser.add_argument('--no-detailed-output', action='store_true', 
                       help='禁用詳細輸出，緩存模式下只顯示摘要')
    parser.add_argument('--version', action='version', version='F1 Analysis CLI v5.3')
    
    return parser

def main():
    """主程式進入點"""
    try:
        # 解析命令行參數
        parser = create_argument_parser()
        args = parser.parse_args()
        
        # 如果要求列出賽事
        if args.list_races:
            if args.year:
                # 顯示指定年份的詳細賽事列表
                print_races_for_year(args.year)
            else:
                # 顯示所有支援年份的賽事列表
                print_supported_races()
            return
        
        # 檢查 modules 目錄是否存在
        if not os.path.exists(modules_dir):
            print(f"[ERROR] 找不到 modules 目錄: {modules_dir}")
            print("請確保在正確的工作目錄中運行此程式")
            sys.exit(1)
            
        # 啟動模組化CLI
        cli = F1AnalysisModularCLI(args)
        cli.run()
        
    except KeyboardInterrupt:
        print("\n\n👋 程式已被使用者中斷，再見！")
    except Exception as e:
        print(f"\n[ERROR] 程式執行錯誤: {e}")
        print("請檢查系統環境或聯繫技術支援")
        sys.exit(1)

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
    main()
