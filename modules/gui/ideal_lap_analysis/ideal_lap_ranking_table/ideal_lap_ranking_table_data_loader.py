#!/usr/bin/env python3
"""
理想圈排名表格資料載入器
Ideal Lap Ranking Table Data Loader

負責載入和轉換 CLI Function 53 輸出的理想圈分析資料
遵循 API-ONLY 模式，優先使用 API，備援使用本地 JSON

作者: F1T Team
日期: 2025-10-09
版本: 1.0.0
"""

from modules.gui.base.universal_data_loader_base import UniversalDataLoader
from typing import Dict, Any, Optional, List


class IdealLapRankingTableDataLoader(UniversalDataLoader):
    """
    理想圈排名表格資料載入器
    
    繼承自 UniversalDataLoader，實作理想圈分析資料的載入、驗證和轉換
    
    資料來源：
    - API: refactored_api.py (function_id=53)
    - 本地 JSON: json/ideal_lap_ranking_{year}_{race}_{session}.json
    
    資料結構：
    {
        "analysis_result": {
            "ranking": [
                {
                    "position": int,
                    "driver": str,
                    "team": str,
                    "fastest_lap_time": float,
                    "ideal_lap_time": float,
                    "time_gap": float,
                    "ideal_lap_detail": {...},
                    "laps": [...]
                }
            ],
            "summary": {...},
            "team_analysis": {...},
            "sector_comparison": {...}
        }
    }
    """
    
    # CLI 功能編號
    CLI_FUNCTION = 53
    
    # JSON 檔案命名模式
    JSON_PATTERN = "ideal_lap_ranking_{year}_{race}_{session}.json"
    
    # 分析類型標識
    ANALYSIS_TYPE = "ideal_lap_ranking"
    
    def __init__(self, year: str, race: str, session: str, parent=None):
        """
        初始化資料載入器
        
        Args:
            year: 賽季年份 (例如: "2025")
            race: 賽事名稱 (例如: "Japan")
            session: 賽段類型 (例如: "R", "Q", "FP1")
            parent: 父元件 (用於信號連接)
        """
        # 調用基類 __init__ (只需要 analysis_type 和 parent)
        super().__init__(analysis_type=self.ANALYSIS_TYPE, parent=parent)
        
        self.year = str(year)
        self.race = race
        self.session = session

        # API-ONLY 模式：停用本地 JSON 後備
        self._allow_local_fallback = False
        self._debug("[IDEAL_LAP_LOADER] 已停用本地 JSON 後備 (API-ONLY)")
        
        self._debug(f"[IDEAL_LAP_LOADER] 初始化完成: {year} {race} {session}")
    
    def _validate_data_format(self, data: Any) -> bool:
        """
        驗證資料格式是否符合預期
        
        檢查項目：
        1. 資料必須是字典
        2. 必須包含 "analysis_result" 鍵
        3. analysis_result 必須包含必要的子鍵
        
        Args:
            data: 待驗證的資料
            
        Returns:
            bool: 資料格式是否正確
        """
        try:
            # 檢查基本類型
            if not isinstance(data, dict):
                self._debug("[VALIDATE] ❌ 資料不是字典類型")
                return False
            
            # 檢查頂層結構
            if "analysis_result" not in data:
                self._debug("[VALIDATE] ❌ 缺少 'analysis_result' 鍵")
                return False
            
            analysis_result = data["analysis_result"]
            if not isinstance(analysis_result, dict):
                self._debug("[VALIDATE] ❌ 'analysis_result' 不是字典類型")
                return False
            
            # 檢查必要的子鍵
            required_keys = ["ranking", "summary", "team_analysis", "sector_comparison"]
            missing_keys = [key for key in required_keys if key not in analysis_result]
            
            if missing_keys:
                self._debug(f"[VALIDATE] ❌ 缺少必要的鍵: {missing_keys}")
                return False
            
            # 檢查 ranking 是否為列表且不為空
            ranking = analysis_result["ranking"]
            if not isinstance(ranking, list):
                self._debug("[VALIDATE] ❌ 'ranking' 不是列表類型")
                return False
            
            if len(ranking) == 0:
                self._debug("[VALIDATE] ⚠️ 'ranking' 列表為空")
                return False
            
            # 檢查第一個車手資料是否包含必要欄位
            first_driver = ranking[0]
            required_driver_fields = [
                "position", "driver", "team", 
                "fastest_lap_time", "ideal_lap_time", "time_gap"
            ]
            missing_driver_fields = [
                field for field in required_driver_fields 
                if field not in first_driver
            ]
            
            if missing_driver_fields:
                self._debug(f"[VALIDATE] ❌ 車手資料缺少欄位: {missing_driver_fields}")
                return False
            
            self._debug(f"[VALIDATE] ✅ 資料格式驗證通過 (共 {len(ranking)} 位車手)")
            return True
            
        except Exception as e:
            self._debug(f"[VALIDATE] ❌ 驗證過程發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _transform_data_for_display(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        轉換資料為顯示格式
        
        主要工作：
        1. 計算全場最速實際圈（所有車手中的最快圈）
        2. 找出創造最速圈的車手和圈數
        3. 為每位車手計算與全場最速的差距
        4. 增強統計摘要資料
        5. 計算平均差異、最大潛力、最接近完美單圈
        
        Args:
            data: 原始資料
            
        Returns:
            Dict: 轉換後的資料
        """
        try:
            self._debug("[TRANSFORM] 開始轉換資料...")
            
            ranking = data["analysis_result"]["ranking"]
            
            # ========== 1. 計算全場最速實際圈 ==========
            fastest_laps = [
                d["fastest_lap_time"] 
                for d in ranking 
                if d.get("fastest_lap_time") is not None
            ]
            
            if not fastest_laps:
                self._debug("[TRANSFORM] ⚠️ 沒有找到有效的最速圈數據")
                session_fastest = None
            else:
                session_fastest = min(fastest_laps)
                self._debug(f"[TRANSFORM] 全場最速圈: {session_fastest:.3f}s")
            
            # ========== 2. 找出創造最速圈的車手與圈數 ==========
            fastest_driver = None
            fastest_lap_number = None
            fastest_team = None
            
            if session_fastest:
                for driver in ranking:
                    if driver.get("fastest_lap_time") == session_fastest:
                        fastest_driver = driver["driver"]
                        fastest_team = driver.get("team", "Unknown")
                        
                        # 從 laps 陣列中找到最快圈的圈數
                        if "laps" in driver and isinstance(driver["laps"], list):
                            for lap in driver["laps"]:
                                if lap.get("lap_time_seconds") == session_fastest:
                                    fastest_lap_number = lap.get("lap_number")
                                    break
                        
                        self._debug(
                            f"[TRANSFORM] 最速圈創造者: {fastest_driver} "
                            f"({fastest_team}) - Lap {fastest_lap_number}"
                        )
                        break
            
            # ========== 3. 為每位車手注入額外資料 ==========
            for idx, driver in enumerate(ranking):
                # 全場最速圈資訊
                driver["session_fastest_lap"] = session_fastest
                driver["session_fastest_driver"] = fastest_driver
                driver["session_fastest_lap_number"] = fastest_lap_number
                driver["session_fastest_team"] = fastest_team
                
                # 計算該車手與全場最速的差距
                if driver.get("fastest_lap_time") and session_fastest:
                    gap = driver["fastest_lap_time"] - session_fastest
                    driver["gap_to_session_fastest"] = gap
                else:
                    driver["gap_to_session_fastest"] = None
                
                # 確保 sector_breakdown 存在（用於分段標記）
                if "sector_breakdown" not in driver:
                    driver["sector_breakdown"] = {}
            
            self._debug(f"[TRANSFORM] ✅ 已為 {len(ranking)} 位車手注入資料")
            
            # ========== 4. 增強統計摘要 ==========
            summary = data["analysis_result"]["summary"]
            
            # 添加全場最速圈資訊
            summary["session_fastest_lap"] = session_fastest
            summary["session_fastest_driver"] = fastest_driver
            summary["session_fastest_lap_number"] = fastest_lap_number
            summary["session_fastest_team"] = fastest_team
            
            # 計算平均差異 (車手最速圈 - 理想圈)
            gaps = [d["time_gap"] for d in ranking if d.get("time_gap") is not None]
            summary["average_gap"] = sum(gaps) / len(gaps) if gaps else 0
            
            # 找出最大未發揮潛力的車手
            if gaps:
                max_gap_driver = max(ranking, key=lambda x: x.get("time_gap", 0))
                summary["max_potential_driver"] = max_gap_driver["driver"]
                summary["max_potential_gap"] = max_gap_driver["time_gap"]
                
                # 找出最接近完美單圈的車手
                min_gap_driver = min(ranking, key=lambda x: x.get("time_gap", float('inf')))
                summary["closest_perfect_driver"] = min_gap_driver["driver"]
                summary["closest_perfect_gap"] = min_gap_driver["time_gap"]
            
            # 計算完美單圈達成率 (time_gap = 0)
            perfect_laps = sum(1 for d in ranking if d.get("time_gap", 1) == 0)
            summary["perfect_lap_count"] = perfect_laps
            summary["perfect_lap_rate"] = f"{perfect_laps}/{len(ranking)}"
            
            # 與最快理想圈的差距
            if "fastest_ideal_lap" in summary and session_fastest:
                fastest_ideal = summary["fastest_ideal_lap"]
                if isinstance(fastest_ideal, dict) and "time" in fastest_ideal:
                    ideal_time = fastest_ideal["time"]
                    summary["ideal_vs_session_gap"] = session_fastest - ideal_time
                    self._debug(
                        f"[TRANSFORM] 最快理想圈 vs 實際最速: "
                        f"{summary['ideal_vs_session_gap']:.3f}s"
                    )
            
            self._debug("[TRANSFORM] ✅ 統計摘要已增強")
            self._debug(f"[TRANSFORM] 平均差異: {summary['average_gap']:.3f}s")
            self._debug(f"[TRANSFORM] 完美單圈達成率: {summary['perfect_lap_rate']}")
            
            return data
            
        except Exception as e:
            self._debug(f"[TRANSFORM] ❌ 轉換過程發生錯誤: {e}")
            import traceback
            traceback.print_exc()
            # 即使轉換失敗，也返回原始資料
            return data
    
    def _generate_data_via_cli(self, **kwargs) -> bool:
        """
        ⚠️ API-ONLY 模式: 禁止 CLI 調用
        
        根據 API-ONLY 政策，GUI 模組不允許直接調用 CLI 進程
        只能通過以下方式獲取資料：
        1. REST API (refactored_api.py)
        2. 讀取已存在的本地 JSON 檔案
        
        Returns:
            bool: 固定返回 False
        """
        self._debug("⚠️ [API-ONLY] CLI 調用已禁用")
        self._debug("💡 提示: 請使用 API 獲取資料，或手動執行 CLI 生成 JSON")
        return False
    
    def _find_fastest_driver(self, ranking: list, fastest_time: float) -> Optional[str]:
        """
        找出創造最速圈的車手代碼
        
        Args:
            ranking: 車手排名列表
            fastest_time: 最速圈時間
            
        Returns:
            str: 車手代碼，未找到則返回 None
        """
        for driver in ranking:
            if driver.get("fastest_lap_time") == fastest_time:
                return driver.get("driver")
        return None
    
    def _validate_load_parameters(self, params: Dict[str, Any]) -> bool:
        """
        驗證載入參數
        
        Args:
            params: 參數字典
            
        Returns:
            bool: 參數是否有效
        """
        # 基本參數檢查
        required = ["year", "race", "session"]
        for key in required:
            if key not in params:
                self._debug(f"❌ 缺少必要參數: {key}")
                return False
        return True
    
    def _build_filename_patterns(self, **params) -> List[str]:
        """
        建立檔案搜尋模式
        
        Args:
            **params: 載入參數 (year, race, session)
            
        Returns:
            List[str]: 檔案搜尋模式列表
        """
        year = params.get("year", self.year)
        race = params.get("race", self.race)
        session = params.get("session", self.session)
        
        # 理想圈分析的檔案命名模式
        patterns = [
            f"ideal_lap_ranking_{year}_{race}_{session}.json",
            f"ideal_lap_{year}_{race}_{session}.json",
            f"*ideal*lap*{year}*{race}*{session}*.json"
        ]
        
        return patterns


# ========== 測試代碼 ==========
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    print("=" * 60)
    print("理想圈排名表格資料載入器 - 獨立測試")
    print("=" * 60)
    
    # 創建 Qt 應用程式（需要 QTimer）
    app = QApplication(sys.argv)
    
    # 創建測試實例
    loader = IdealLapRankingTableDataLoader(
        year="2025",
        race="Japan",
        session="R"
    )
    
    print(f"\n📋 載入器配置:")
    print(f"  CLI Function: {loader.CLI_FUNCTION}")
    print(f"  JSON Pattern: {loader.JSON_PATTERN}")
    print(f"  參數: {loader.year} {loader.race} {loader.session}")
    
    # 測試檔案搜尋模式
    print(f"\n🔍 檔案搜尋模式:")
    patterns = loader._build_filename_patterns(
        year=loader.year,
        race=loader.race,
        session=loader.session
    )
    for i, pattern in enumerate(patterns, 1):
        print(f"  {i}. {pattern}")
    
    # 設置信號處理
    def on_data_loaded(data):
        print(f"\n✅ 數據載入成功!")
        
        if "analysis_result" in data:
            ranking = data["analysis_result"]["ranking"]
            summary = data["analysis_result"]["summary"]
            
            print(f"\n📊 資料摘要:")
            print(f"  總車手數: {len(ranking)}")
            print(f"  全場最速圈: {summary.get('session_fastest_lap', 'N/A')}")
            print(f"  創造者: {summary.get('session_fastest_driver', 'N/A')}")
            print(f"  平均差異: {summary.get('average_gap', 0):.3f}s")
            print(f"  完美單圈: {summary.get('perfect_lap_rate', 'N/A')}")
            
            # 顯示前 3 名
            print(f"\n🏆 前 3 名:")
            for i, driver in enumerate(ranking[:3]):
                print(
                    f"  {i+1}. {driver['driver']} - "
                    f"理想圈: {driver['ideal_lap_time']:.3f}s "
                    f"(差異: +{driver['time_gap']:.3f}s)"
                )
        
        app.quit()
    
    def on_load_error(error_msg):
        print(f"\n❌ 載入錯誤: {error_msg}")
        app.quit()
    
    loader.data_loaded.connect(on_data_loaded)
    loader.load_error.connect(on_load_error)
    
    # 啟動載入
    print(f"\n🚀 啟動數據載入...")
    success = loader.load_data(
        year=loader.year,
        race=loader.race,
        session=loader.session
    )
    
    if not success:
        print("❌ 載入啟動失敗")
        sys.exit(1)
    
    # 進入事件循環
    sys.exit(app.exec_())
