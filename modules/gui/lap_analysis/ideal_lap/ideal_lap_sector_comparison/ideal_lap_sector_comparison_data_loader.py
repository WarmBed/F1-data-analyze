#!/usr/bin/env python3
"""
理想圈分段對比資料載入器
Ideal Lap Sector Comparison Data Loader

負責載入和轉換 CLI Function 53 輸出的理想圈分析資料，專注於分段對比
遵循 API-ONLY 模式，優先使用 API，備援使用本地 JSON

作者: F1T Team
日期: 2025-10-09
版本: 1.0.0
"""

from modules.gui.base.universal_data_loader_base import UniversalDataLoader
from typing import Dict, Any, Optional, List


class IdealLapSectorComparisonDataLoader(UniversalDataLoader):
    """
    理想圈分段對比資料載入器
    
    繼承自 UniversalDataLoader，實作理想圈與最快圈分段對比資料的載入、驗證和轉換
    
    資料來源：
    - API: refactored_api.py (function_id=53)
    - 本地 JSON: json/ideal_lap_ranking_{year}_{race}_{session}.json
    
    轉換後的資料結構：
    {
        "comparison_data": [
            {
                "driver": "SAI",
                "team": "Ferrari",
                "ideal_sectors": [s1, s2, s3],
                "fastest_sectors": [s1, s2, s3],
                "sector_sources": {"s1": {"lap": 42, "time": 31.320}, ...},
                "is_optimal": [True, False, False],
                "delta": [0.0, +0.168, +0.252]
            }
        ],
        "statistics": {
            "sector_1": {"avg_loss": 0.142, "max_loss": 0.325, "perfect_count": 2},
            "sector_2": {...},
            "sector_3": {...}
        }
    }
    """
    
    # CLI 功能編號（複用 Function 53）
    CLI_FUNCTION = 53
    
    # JSON 檔案命名模式
    JSON_PATTERN = "ideal_lap_ranking_{year}_{race}_{session}.json"
    
    # 分析類型標識
    ANALYSIS_TYPE = "ideal_lap_sector_comparison"
    
    def __init__(self, year: str, race: str, session: str, parent=None):
        """
        初始化資料載入器
        
        Args:
            year: 賽季年份 (例如: "2025")
            race: 賽事名稱 (例如: "Japan")
            session: 賽段類型 (例如: "R", "Q", "FP1")
            parent: 父元件 (用於信號連接)
        """
        super().__init__(analysis_type=self.ANALYSIS_TYPE, parent=parent)
        
        self.year = str(year)
        self.race = race
        self.session = session
        
        self._debug(f"[SECTOR_COMPARISON_LOADER] 初始化完成: {year} {race} {session}")
    
    def _validate_data_format(self, data: Any) -> bool:
        """
        驗證資料格式是否符合預期
        
        檢查項目：
        1. 資料必須是字典
        2. 必須包含 "analysis_result" 鍵
        3. 必須包含 ranking 和 sector_comparison
        
        Args:
            data: 待驗證的資料
            
        Returns:
            bool: 資料格式是否正確
        """
        try:
            if not isinstance(data, dict):
                self._debug("[VALIDATE] ❌ 資料不是字典類型")
                return False
            
            if "analysis_result" not in data:
                self._debug("[VALIDATE] ❌ 缺少 'analysis_result' 鍵")
                return False
            
            analysis_result = data["analysis_result"]
            
            # 檢查必要的子鍵
            if "ranking" not in analysis_result:
                self._debug("[VALIDATE] ❌ 缺少 'ranking' 鍵")
                return False
            
            ranking = analysis_result["ranking"]
            if not isinstance(ranking, list) or len(ranking) == 0:
                self._debug("[VALIDATE] ❌ 'ranking' 必須是非空列表")
                return False
            
            # 檢查第一個車手資料是否包含分段資訊
            first_driver = ranking[0]
            required_fields = ["driver", "sector_breakdown", "ideal_lap_detail", "laps"]
            missing_fields = [field for field in required_fields if field not in first_driver]
            
            if missing_fields:
                self._debug(f"[VALIDATE] ❌ 車手資料缺少欄位: {missing_fields}")
                return False
            
            # 檢查 sector_breakdown 結構
            sector_breakdown = first_driver["sector_breakdown"]
            if not all(f"sector_{i}" in sector_breakdown for i in [1, 2, 3]):
                self._debug("[VALIDATE] ❌ sector_breakdown 缺少必要分段")
                return False
            
            # 檢查 ideal_lap_detail 結構
            ideal_lap_detail = first_driver["ideal_lap_detail"]
            if "sector_sources" not in ideal_lap_detail:
                self._debug("[VALIDATE] ❌ ideal_lap_detail 缺少 sector_sources")
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
        轉換資料為分段對比顯示格式
        
        主要工作：
        1. 為每位車手提取理想圈分段時間
        2. 找到最快圈並提取其分段時間
        3. 計算時間差
        4. 判斷每個分段是否在最快圈中為最佳
        5. 計算統計數據（平均損失、最大損失、完美分段車手數）
        
        Args:
            data: 原始資料
            
        Returns:
            Dict: 轉換後的資料，包含 comparison_data 和 statistics
        """
        try:
            self._debug("[TRANSFORM] 開始轉換分段對比資料...")
            
            ranking = data["analysis_result"]["ranking"]
            comparison_data = []
            
            # 統計資料初始化
            sector_stats = {
                "sector_1": {"losses": [], "perfect_count": 0},
                "sector_2": {"losses": [], "perfect_count": 0},
                "sector_3": {"losses": [], "perfect_count": 0}
            }
            
            # ========== 1. 為每位車手處理分段資料 ==========
            for driver_data in ranking:
                try:
                    # 提取理想圈分段
                    sector_sources = driver_data["ideal_lap_detail"]["sector_sources"]
                    ideal_sectors = [
                        sector_sources["s1"]["time"],
                        sector_sources["s2"]["time"],
                        sector_sources["s3"]["time"]
                    ]
                    
                    # 找到最快圈並提取分段
                    fastest_lap = self._find_fastest_lap(driver_data.get("laps", []))
                    if fastest_lap:
                        fastest_sectors = fastest_lap["sector_times"]
                    else:
                        # 如果找不到最快圈，使用 sector_breakdown 中的時間
                        self._debug(f"[TRANSFORM] ⚠️ {driver_data['driver']} 找不到最快圈，使用 sector_breakdown")
                        sector_breakdown = driver_data["sector_breakdown"]
                        fastest_sectors = [
                            sector_breakdown["sector_1"]["time"],
                            sector_breakdown["sector_2"]["time"],
                            sector_breakdown["sector_3"]["time"]
                        ]
                    
                    # 判斷每個分段是否最佳
                    sector_breakdown = driver_data["sector_breakdown"]
                    is_optimal = [
                        sector_breakdown["sector_1"].get("is_optimal_in_fastest", False),
                        sector_breakdown["sector_2"].get("is_optimal_in_fastest", False),
                        sector_breakdown["sector_3"].get("is_optimal_in_fastest", False)
                    ]
                    
                    # 計算時間差
                    delta = [fastest - ideal for ideal, fastest in zip(ideal_sectors, fastest_sectors)]
                    
                    # 更新統計資料
                    for i, (sector_key, is_opt, d) in enumerate(zip(
                        ["sector_1", "sector_2", "sector_3"], is_optimal, delta
                    )):
                        sector_stats[sector_key]["losses"].append(d)
                        if is_opt:
                            sector_stats[sector_key]["perfect_count"] += 1
                    
                    # 組裝單一車手的對比資料
                    comparison_data.append({
                        "driver": driver_data["driver"],
                        "team": driver_data.get("team", "Unknown"),
                        "position": driver_data.get("position", 0),
                        "ideal_sectors": ideal_sectors,
                        "fastest_sectors": fastest_sectors,
                        "sector_sources": sector_sources,
                        "is_optimal": is_optimal,
                        "delta": delta,
                        "ideal_lap_time": sum(ideal_sectors),
                        "fastest_lap_time": sum(fastest_sectors)
                    })
                    
                except Exception as e:
                    self._debug(f"[TRANSFORM] ⚠️ 處理車手 {driver_data.get('driver', 'Unknown')} 失敗: {e}")
                    continue
            
            # ========== 2. 計算統計摘要 ==========
            statistics = {}
            total_drivers = len(comparison_data)
            
            for sector_key, stats in sector_stats.items():
                losses = stats["losses"]
                if losses:
                    avg_loss = sum(losses) / len(losses)
                    max_loss = max(losses)
                    min_loss = min(losses)
                    perfect_count = stats["perfect_count"]
                    perfect_percentage = (perfect_count / total_drivers * 100) if total_drivers > 0 else 0
                    
                    # 找到最大損失的車手
                    max_loss_driver = None
                    min_loss_driver = None
                    for comp in comparison_data:
                        sector_idx = int(sector_key.split("_")[1]) - 1
                        if comp["delta"][sector_idx] == max_loss:
                            max_loss_driver = comp["driver"]
                        if comp["delta"][sector_idx] == min_loss:
                            min_loss_driver = comp["driver"]
                    
                    statistics[sector_key] = {
                        "avg_loss": avg_loss,
                        "max_loss": max_loss,
                        "max_loss_driver": max_loss_driver,
                        "min_loss": min_loss,
                        "min_loss_driver": min_loss_driver,
                        "perfect_count": perfect_count,
                        "perfect_percentage": perfect_percentage
                    }
                else:
                    statistics[sector_key] = {
                        "avg_loss": 0.0,
                        "max_loss": 0.0,
                        "max_loss_driver": "N/A",
                        "min_loss": 0.0,
                        "min_loss_driver": "N/A",
                        "perfect_count": 0,
                        "perfect_percentage": 0.0
                    }
            
            self._debug(f"[TRANSFORM] ✅ 轉換完成，共處理 {len(comparison_data)} 位車手")
            
            return {
                "success": True,
                "comparison_data": comparison_data,
                "statistics": statistics,
                "total_drivers": total_drivers,
                "original_data": data  # 保留原始資料以備後用
            }
            
        except Exception as e:
            self._debug(f"[TRANSFORM] ❌ 轉換失敗: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "comparison_data": [],
                "statistics": {}
            }
    
    def _find_fastest_lap(self, laps: List[Dict]) -> Optional[Dict]:
        """
        從 laps 陣列中找到最快圈
        
        Args:
            laps: 圈速列表
            
        Returns:
            Optional[Dict]: 最快圈資料，包含 sector_times 等，若無則返回 None
        """
        if not laps:
            return None
        
        try:
            # 過濾掉無效圈（時間為 None 或 0）
            valid_laps = [
                lap for lap in laps 
                if lap.get("lap_time_seconds") is not None and lap.get("lap_time_seconds") > 0
            ]
            
            if not valid_laps:
                return None
            
            # 找到最快圈
            fastest = min(valid_laps, key=lambda x: x["lap_time_seconds"])
            
            # 檢查是否有分段時間
            if "sector_times" not in fastest or not fastest["sector_times"]:
                self._debug(f"[FIND_FASTEST] ⚠️ 最快圈缺少 sector_times")
                return None
            
            return fastest
            
        except Exception as e:
            self._debug(f"[FIND_FASTEST] ❌ 查找失敗: {e}")
            return None
    
    def _generate_data_via_cli(self, **kwargs) -> bool:
        """
        [已禁用] 通過 CLI 生成數據
        
        ⚠️ API-ONLY 模式: 此方法已禁用，系統只允許通過 API 獲取數據
        """
        self._debug("⚠️  [API-ONLY] CLI 調用已禁用")
        self._debug("💡 提示: 請使用 API 獲取數據或手動執行 CLI 命令")
        self._debug(f"   CLI 命令: python f1_analysis_modular_main.py -f {self.CLI_FUNCTION} -y {self.year} -r {self.race} -s {self.session}")
        return False
