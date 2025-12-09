#!/usr/bin/env python3
"""
F86 - Tire Saving Behavior Analyzer (省輪胎行為分析器)

功能:
    分析車手在比賽中的省輪胎行為模式
    偵測主動省輪胎 vs 輪胎真的衰退完畢
    
核心指標:
    - coasting_trend: Stint 內滑行時間趨勢
    - throttle_trend: Stint 內油門比例趨勢
    - corner_speed_trend: 彎道最低速趨勢
    - sector_time_trend: 各 Sector 時間趨勢
    - pace_vs_expected: 實際圈速 vs 預期衰退
    
驗證方法:
    使用 2023-2024 數據訓練，2025 數據驗證
    成功標準: 省輪胎分數高的車手，實際進站圈數 > 預期進站圈數
    
數據來源:
    - json/driver_throttle_ratio_*.json (F54 油門分析)
    - config/tire_degradation_database.json (輪胎衰退係數)
    
輸出:
    - 每車手每 stint 的省輪胎分數 (0-100)
    - 省輪胎等級: NONE, LIGHT, MODERATE, HEAVY
    - 預測準確度報告

版本: 1.0.0
作者: F1T Team
日期: 2025-12-05
"""

import os
import json
import glob
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, field, asdict
import numpy as np


# ============================================================================
# 數據結構定義
# ============================================================================

@dataclass
class StintPhaseMetrics:
    """Stint 階段指標"""
    phase: str              # "early", "mid", "late"
    laps: str               # "1-7"
    avg_coasting_s: float
    avg_full_throttle_ratio: float
    avg_corner_speed_kmh: float
    avg_lap_time_s: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TireSavingTrends:
    """省輪胎趨勢"""
    coasting_trend: float       # >1.0 = 滑行增加
    throttle_trend: float       # <1.0 = 油門減少
    corner_speed_trend: float   # 負值 = 減速
    sector_time_trends: List[float]  # 各 Sector 每圈慢多少秒
    lap_time_trend: float       # 每圈慢多少秒
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DegradationComparison:
    """衰退比較"""
    actual_deg_per_lap: float       # 實際衰退
    expected_deg_per_lap: float     # 預期衰退
    saving_efficiency: float         # 實際/預期 (<1 = 有效省胎)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StintSavingAnalysis:
    """Stint 省輪胎分析結果"""
    overall_score: float            # 0-100 分
    saving_level: str               # "NONE", "LIGHT", "MODERATE", "HEAVY"
    is_intentional: bool            # 是否主動省輪胎
    confidence: float               # 判斷信心度
    phases: List[StintPhaseMetrics]
    trends: TireSavingTrends
    degradation_comparison: DegradationComparison
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_score": self.overall_score,
            "saving_level": self.saving_level,
            "is_intentional": self.is_intentional,
            "confidence": self.confidence,
            "phases": [p.to_dict() for p in self.phases],
            "trends": self.trends.to_dict(),
            "degradation_comparison": self.degradation_comparison.to_dict()
        }


@dataclass
class StintInfo:
    """Stint 資訊"""
    stint_number: int
    compound: str
    start_lap: int
    end_lap: int
    total_laps: int
    saving_analysis: Optional[StintSavingAnalysis] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "stint_number": self.stint_number,
            "compound": self.compound,
            "start_lap": self.start_lap,
            "end_lap": self.end_lap,
            "total_laps": self.total_laps,
        }
        if self.saving_analysis:
            result["saving_analysis"] = self.saving_analysis.to_dict()
        return result


@dataclass
class DriverSummary:
    """車手省輪胎總結"""
    most_saving_stint: int
    peak_saving_score: float
    avg_saving_score: float
    total_estimated_laps_saved: float
    saving_pattern: str  # "none", "early", "progressive", "aggressive"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============================================================================
# 省輪胎分析器
# ============================================================================

class TireSavingAnalyzer:
    """F86 省輪胎行為分析器"""
    
    def __init__(self, base_path: str = None):
        """
        初始化分析器
        
        Args:
            base_path: 專案根目錄路徑
        """
        if base_path is None:
            current_file = Path(__file__).resolve()
            self.base_path = current_file.parent.parent.parent.parent
        else:
            self.base_path = Path(base_path)
        
        self.json_path = self.base_path / "json"
        self.tire_db_path = self.base_path / "config" / "tire_degradation_database.json"
        
        # 載入輪胎衰退資料庫
        self.tire_database = self._load_tire_database()
        
        # 預設衰退參數 (from predictor.py TYRE_PERFORMANCE)
        self.default_degradation = {
            "SOFT": {"base": 0.065, "cliff_lap": 11, "ideal_laps": 7},
            "MEDIUM": {"base": 0.045, "cliff_lap": 13, "ideal_laps": 9},
            "HARD": {"base": 0.030, "cliff_lap": 17, "ideal_laps": 11}
        }
        
        # 省輪胎分類閾值
        self.saving_thresholds = {
            "NONE": (0, 20),
            "LIGHT": (20, 40),
            "MODERATE": (40, 65),
            "HEAVY": (65, 100)
        }
    
    def _load_tire_database(self) -> Dict[str, Any]:
        """載入輪胎衰退係數資料庫"""
        try:
            if self.tire_db_path.exists():
                with open(self.tire_db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"[WARNING] 找不到輪胎衰退資料庫: {self.tire_db_path}")
                return {"circuits": {}, "default_values": {}}
        except Exception as e:
            print(f"[ERROR] 載入輪胎衰退資料庫失敗: {e}")
            return {"circuits": {}, "default_values": {}}
    
    def _load_throttle_data(self, year: int, race: str, session: str) -> Optional[Dict]:
        """載入 F54 油門分析數據"""
        pattern = f"driver_throttle_ratio_{year}_{race}_{session}*.json"
        files = glob.glob(str(self.json_path / pattern))
        
        if not files:
            # 嘗試不同的賽事名稱格式
            race_variants = [
                race,
                race.replace(" ", "_"),
                race.replace("_", " "),
            ]
            for variant in race_variants:
                pattern = f"driver_throttle_ratio_{year}_{variant}_{session}*.json"
                files = glob.glob(str(self.json_path / pattern))
                if files:
                    break
        
        if not files:
            print(f"[WARNING] 找不到 F54 數據: {year} {race} {session}")
            return None
        
        # 使用最新的檔案
        latest_file = max(files, key=os.path.getmtime)
        print(f"[INFO] 載入 F54 數據: {os.path.basename(latest_file)}")
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[ERROR] 載入 F54 數據失敗: {e}")
            return None
    
    def _get_expected_degradation(self, race: str, compound: str) -> float:
        """獲取預期衰退率"""
        # 嘗試從資料庫獲取
        circuits = self.tire_database.get("circuits", {})
        
        # 賽事名稱映射
        race_to_circuit = {
            "Qatar": "Lusail", "Japan": "Suzuka", "Italy": "Monza",
            "Monaco": "Monaco", "Belgium": "Spa", "Brazil": "Interlagos",
            "Mexico": "Mexico", "Las Vegas": "Las_Vegas", "Abu Dhabi": "Yas_Marina",
            "Bahrain": "Bahrain", "Saudi Arabia": "Jeddah", "Australia": "Melbourne",
            "China": "Shanghai", "Miami": "Miami", "Emilia Romagna": "Imola",
            "Canada": "Montreal", "Spain": "Barcelona", "Austria": "Spielberg",
            "Great Britain": "Silverstone", "Hungary": "Budapest",
            "Netherlands": "Zandvoort", "Singapore": "Singapore", "USA": "Austin",
            "Azerbaijan": "Baku"
        }
        
        circuit_name = race_to_circuit.get(race, race)
        compound_upper = compound.upper() if compound else "MEDIUM"
        
        if circuit_name in circuits:
            circuit_data = circuits[circuit_name]
            base_deg = circuit_data.get("base_degradation", {})
            if compound_upper in base_deg:
                return base_deg[compound_upper]
        
        # 使用預設值
        return self.default_degradation.get(compound_upper, {}).get("base", 0.045)
    
    def _get_expected_stint_length(self, compound: str) -> int:
        """獲取預期 stint 長度"""
        compound_upper = compound.upper() if compound else "MEDIUM"
        return self.default_degradation.get(compound_upper, {}).get("cliff_lap", 13)
    
    def _extract_stints(self, driver_data: Dict) -> List[Dict]:
        """從車手數據中提取 stint 資訊"""
        laps = driver_data.get("laps", [])
        if not laps:
            return []
        
        stints = []
        current_stint = None
        
        for lap in laps:
            stint_num = lap.get("stint", 1)
            compound = lap.get("compound", "MEDIUM")
            lap_number = lap.get("lap_number", 0)
            
            if current_stint is None or current_stint["stint_number"] != stint_num:
                if current_stint:
                    current_stint["end_lap"] = prev_lap_number
                    current_stint["total_laps"] = current_stint["end_lap"] - current_stint["start_lap"] + 1
                    stints.append(current_stint)
                
                current_stint = {
                    "stint_number": stint_num,
                    "compound": compound,
                    "start_lap": lap_number,
                    "laps": []
                }
            
            current_stint["laps"].append(lap)
            prev_lap_number = lap_number
        
        # 最後一個 stint
        if current_stint and current_stint.get("laps"):
            current_stint["end_lap"] = prev_lap_number
            current_stint["total_laps"] = current_stint["end_lap"] - current_stint["start_lap"] + 1
            stints.append(current_stint)
        
        return stints
    
    def _analyze_stint(self, stint_data: Dict, race: str) -> StintSavingAnalysis:
        """分析單一 stint 的省輪胎行為"""
        laps = stint_data.get("laps", [])
        compound = stint_data.get("compound", "MEDIUM")
        
        if len(laps) < 5:
            # stint 太短，無法分析
            return StintSavingAnalysis(
                overall_score=0,
                saving_level="NONE",
                is_intentional=False,
                confidence=0.3,
                phases=[],
                trends=TireSavingTrends(1.0, 1.0, 0, [0, 0, 0], 0),
                degradation_comparison=DegradationComparison(0, 0, 1.0)
            )
        
        # 分割為三個階段: early (前30%), mid (中40%), late (後30%)
        n_laps = len(laps)
        early_end = max(1, int(n_laps * 0.3))
        late_start = n_laps - max(1, int(n_laps * 0.3))
        
        early_laps = laps[:early_end]
        mid_laps = laps[early_end:late_start]
        late_laps = laps[late_start:]
        
        # 計算各階段指標
        phases = []
        for phase_name, phase_laps in [("early", early_laps), ("mid", mid_laps), ("late", late_laps)]:
            if not phase_laps:
                continue
            
            avg_coasting = np.mean([l.get("coasting_duration_s", 0) or 0 for l in phase_laps])
            avg_throttle = np.mean([l.get("full_throttle_ratio", 0.5) or 0.5 for l in phase_laps])
            avg_speed = np.mean([l.get("speed_avg_kmh", 200) or 200 for l in phase_laps])
            avg_lap_time = np.mean([l.get("lap_time_seconds", 0) or 0 for l in phase_laps if l.get("lap_time_seconds")])
            
            lap_range = f"{phase_laps[0].get('lap_number', 0)}-{phase_laps[-1].get('lap_number', 0)}"
            
            phases.append(StintPhaseMetrics(
                phase=phase_name,
                laps=lap_range,
                avg_coasting_s=round(avg_coasting, 2),
                avg_full_throttle_ratio=round(avg_throttle, 3),
                avg_corner_speed_kmh=round(avg_speed, 1),
                avg_lap_time_s=round(avg_lap_time, 3) if avg_lap_time else None
            ))
        
        # 計算趨勢
        early_coasting = np.mean([l.get("coasting_duration_s", 0) or 0 for l in early_laps])
        late_coasting = np.mean([l.get("coasting_duration_s", 0) or 0 for l in late_laps])
        coasting_trend = late_coasting / max(early_coasting, 0.1)
        
        early_throttle = np.mean([l.get("full_throttle_ratio", 0.5) or 0.5 for l in early_laps])
        late_throttle = np.mean([l.get("full_throttle_ratio", 0.5) or 0.5 for l in late_laps])
        throttle_trend = late_throttle / max(early_throttle, 0.01)
        
        early_speed = np.mean([l.get("speed_avg_kmh", 200) or 200 for l in early_laps])
        late_speed = np.mean([l.get("speed_avg_kmh", 200) or 200 for l in late_laps])
        corner_speed_trend = (late_speed - early_speed) / n_laps
        
        # Sector 時間趨勢 (使用現有的 sector 數據)
        sector_trends = [0.0, 0.0, 0.0]
        for i, sector_key in enumerate(["sector1_time", "sector2_time", "sector3_time"]):
            early_sector = [l.get(sector_key) for l in early_laps if l.get(sector_key)]
            late_sector = [l.get(sector_key) for l in late_laps if l.get(sector_key)]
            if early_sector and late_sector:
                sector_trends[i] = (np.mean(late_sector) - np.mean(early_sector)) / n_laps
        
        # 圈速趨勢
        valid_lap_times = [l.get("lap_time_seconds") for l in laps if l.get("lap_time_seconds")]
        if len(valid_lap_times) >= 3:
            lap_time_trend = (valid_lap_times[-1] - valid_lap_times[0]) / len(valid_lap_times)
        else:
            lap_time_trend = 0
        
        trends = TireSavingTrends(
            coasting_trend=round(coasting_trend, 3),
            throttle_trend=round(throttle_trend, 3),
            corner_speed_trend=round(corner_speed_trend, 3),
            sector_time_trends=[round(t, 4) for t in sector_trends],
            lap_time_trend=round(lap_time_trend, 3)
        )
        
        # 衰退比較
        expected_deg = self._get_expected_degradation(race, compound)
        actual_deg = lap_time_trend if lap_time_trend > 0 else 0
        saving_efficiency = actual_deg / max(expected_deg, 0.01)
        
        degradation_comparison = DegradationComparison(
            actual_deg_per_lap=round(actual_deg, 4),
            expected_deg_per_lap=round(expected_deg, 4),
            saving_efficiency=round(saving_efficiency, 3)
        )
        
        # 計算省輪胎評分
        score = self._calculate_saving_score(trends, degradation_comparison)
        level = self._classify_saving_level(score)
        is_intentional, confidence = self._is_intentional_saving(trends, degradation_comparison)
        
        return StintSavingAnalysis(
            overall_score=round(score, 1),
            saving_level=level,
            is_intentional=is_intentional,
            confidence=round(confidence, 2),
            phases=phases,
            trends=trends,
            degradation_comparison=degradation_comparison
        )
    
    def _calculate_saving_score(
        self, 
        trends: TireSavingTrends, 
        degradation: DegradationComparison
    ) -> float:
        """
        計算省輪胎評分 (0-100)
        
        權重設計:
        - coasting: 25% (最直接指標)
        - throttle: 20%
        - corner_speed: 20%
        - sector_time: 15%
        - pace_vs_expected: 20%
        """
        # 滑行增加分數 (ratio > 1.3 = 高分)
        coasting_increase = trends.coasting_trend - 1.0
        coasting_score = min(100, max(0, coasting_increase * 200))
        
        # 油門減少分數 (ratio < 0.9 = 高分)
        throttle_decrease = 1.0 - trends.throttle_trend
        throttle_score = min(100, max(0, throttle_decrease * 200))
        
        # 彎道減速分數 (負值 = 減速)
        corner_score = min(100, max(0, -trends.corner_speed_trend * 50))
        
        # Sector 變慢分數
        avg_sector_slowdown = np.mean([max(0, t) for t in trends.sector_time_trends])
        sector_score = min(100, max(0, avg_sector_slowdown * 500))
        
        # 圈速 vs 預期衰退
        pace_bonus = 0
        if degradation.expected_deg_per_lap > 0.01:
            ratio = degradation.saving_efficiency
            if ratio < 0.8:  # 掉得比預期少 20%+
                pace_bonus = (0.8 - ratio) * 250  # 最高 50 分
        pace_score = min(100, max(0, pace_bonus))
        
        # 加權總分
        weights = {
            'coasting': 0.25,
            'throttle': 0.20,
            'corner_speed': 0.20,
            'sector_time': 0.15,
            'pace_vs_deg': 0.20,
        }
        
        total = (
            weights['coasting'] * coasting_score +
            weights['throttle'] * throttle_score +
            weights['corner_speed'] * corner_score +
            weights['sector_time'] * sector_score +
            weights['pace_vs_deg'] * pace_score
        )
        
        return min(100, max(0, total))
    
    def _classify_saving_level(self, score: float) -> str:
        """分類省輪胎程度"""
        for level, (low, high) in self.saving_thresholds.items():
            if low <= score < high:
                return level
        return "HEAVY" if score >= 65 else "NONE"
    
    def _is_intentional_saving(
        self, 
        trends: TireSavingTrends, 
        degradation: DegradationComparison
    ) -> Tuple[bool, float]:
        """
        判斷是主動省輪胎還是輪胎真的沒了
        
        關鍵區分:
        - 主動省: coasting↑ 但 lap_time 穩定
        - 輪胎沒: coasting↑ 且 lap_time 大幅掉
        """
        coasting_increase = trends.coasting_trend - 1.0
        
        if coasting_increase <= 0:
            return False, 0.9  # 沒有增加滑行，不是省輪胎
        
        # 圈速增加 vs 滑行增加的比例
        lap_time_increase = trends.lap_time_trend
        ratio = lap_time_increase / (coasting_increase + 0.01)
        
        # 與預期衰退比較
        efficiency = degradation.saving_efficiency
        
        # 判斷邏輯:
        if ratio < 0.3 and efficiency < 0.8:
            return True, 0.85  # 高信心主動省
        elif ratio < 0.6 and efficiency < 1.0:
            return True, 0.65  # 中信心主動省
        elif ratio < 1.0 and efficiency < 1.2:
            return True, 0.45  # 低信心可能省
        else:
            return False, 0.70  # 輪胎沒了
    
    def _calculate_driver_summary(self, stints: List[StintInfo]) -> DriverSummary:
        """計算車手省輪胎總結"""
        if not stints:
            return DriverSummary(0, 0, 0, 0, "none")
        
        scores = []
        for stint in stints:
            if stint.saving_analysis:
                scores.append((stint.stint_number, stint.saving_analysis.overall_score))
        
        if not scores:
            return DriverSummary(0, 0, 0, 0, "none")
        
        max_stint, peak_score = max(scores, key=lambda x: x[1])
        avg_score = np.mean([s[1] for s in scores])
        
        # 估計省下的圈數 (基於省輪胎效率)
        total_saved = 0
        for stint in stints:
            if stint.saving_analysis and stint.saving_analysis.saving_level != "NONE":
                efficiency = stint.saving_analysis.degradation_comparison.saving_efficiency
                expected_length = self._get_expected_stint_length(stint.compound)
                if efficiency < 1.0:
                    saved = expected_length * (1.0 - efficiency) * 0.5
                    total_saved += saved
        
        # 判斷省輪胎模式
        if avg_score < 20:
            pattern = "none"
        elif scores[0][1] > avg_score * 1.3:
            pattern = "early"  # 早期就開始省
        elif scores[-1][1] > avg_score * 1.3:
            pattern = "aggressive"  # 末期大幅省
        else:
            pattern = "progressive"  # 漸進式省
        
        return DriverSummary(
            most_saving_stint=max_stint,
            peak_saving_score=round(peak_score, 1),
            avg_saving_score=round(avg_score, 1),
            total_estimated_laps_saved=round(total_saved, 1),
            saving_pattern=pattern
        )
    
    def analyze(
        self, 
        year: int, 
        race: str, 
        session: str = "R",
        save_json: bool = True
    ) -> Dict[str, Any]:
        """
        執行省輪胎行為分析
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 賽事階段 (預設 R = 正賽)
            save_json: 是否儲存 JSON
            
        Returns:
            分析結果字典
        """
        print(f"[INFO] 啟動 F86 - 省輪胎行為分析")
        print(f"  - 賽事: {year} {race} {session}")
        
        # 載入 F54 數據
        throttle_data = self._load_throttle_data(year, race, session)
        if not throttle_data:
            return {
                "success": False,
                "message": f"找不到 F54 數據: {year} {race} {session}",
                "function_id": "86"
            }
        
        # 提取車手數據
        drivers_data = throttle_data.get("data", {}).get("analysis", {}).get("drivers", [])
        if not drivers_data:
            return {
                "success": False,
                "message": "F54 數據中沒有車手資料",
                "function_id": "86"
            }
        
        print(f"[INFO] 找到 {len(drivers_data)} 位車手的數據")
        
        # 分析每位車手
        driver_results = []
        heavy_savers = []
        moderate_savers = []
        no_savers = []
        
        for driver_data in drivers_data:
            driver_code = driver_data.get("driver_code", "UNK")
            team = driver_data.get("team", "Unknown")
            
            print(f"  ↳ 分析車手 {driver_code}...")
            
            # 提取 stint
            stints_raw = self._extract_stints(driver_data)
            
            # 分析每個 stint
            stints = []
            for stint_raw in stints_raw:
                if stint_raw["total_laps"] >= 5:  # 只分析足夠長的 stint
                    analysis = self._analyze_stint(stint_raw, race)
                    stint_info = StintInfo(
                        stint_number=stint_raw["stint_number"],
                        compound=stint_raw["compound"],
                        start_lap=stint_raw["start_lap"],
                        end_lap=stint_raw["end_lap"],
                        total_laps=stint_raw["total_laps"],
                        saving_analysis=analysis
                    )
                    stints.append(stint_info)
            
            # 計算車手總結
            summary = self._calculate_driver_summary(stints)
            
            driver_result = {
                "driver_code": driver_code,
                "team": team,
                "stints": [s.to_dict() for s in stints],
                "summary": summary.to_dict()
            }
            driver_results.append(driver_result)
            
            # 分類車手
            if summary.saving_pattern == "aggressive" or summary.peak_saving_score >= 65:
                heavy_savers.append(driver_code)
            elif summary.saving_pattern != "none" and summary.avg_saving_score >= 20:
                moderate_savers.append(driver_code)
            else:
                no_savers.append(driver_code)
        
        # 建構結果
        result = {
            "success": True,
            "message": f"F86 分析完成，共 {len(driver_results)} 位車手",
            "function_id": "86",
            "data": {
                "metadata": {
                    "year": year,
                    "race": race,
                    "session": session,
                    "analysis_timestamp": datetime.now().isoformat(),
                    "total_drivers": len(driver_results),
                    "analysis_version": "1.0.0"
                },
                "drivers": driver_results,
                "race_overview": {
                    "drivers_with_heavy_saving": heavy_savers,
                    "drivers_with_moderate_saving": moderate_savers,
                    "drivers_with_no_saving": no_savers,
                    "most_aggressive_saver": heavy_savers[0] if heavy_savers else None,
                    "most_aggressive_score": max([d["summary"]["peak_saving_score"] for d in driver_results]) if driver_results else 0
                }
            }
        }
        
        # 儲存 JSON
        if save_json:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tire_saving_analysis_{year}_{race}_{session}_{timestamp}.json"
            output_path = self.json_path / filename
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            print(f"[SUCCESS] 已儲存: {filename}")
        
        return result


# ============================================================================
# CLI 入口函數
# ============================================================================

def run_tire_saving_analysis(
    year: int,
    race: str,
    session: str = "R",
    save_json: bool = True,
    base_path: str = None
) -> Dict[str, Any]:
    """
    F86 入口函數
    
    Args:
        year: 年份
        race: 賽事名稱
        session: 賽事階段
        save_json: 是否儲存 JSON
        base_path: 專案根目錄
        
    Returns:
        分析結果
    """
    analyzer = TireSavingAnalyzer(base_path)
    return analyzer.analyze(year, race, session, save_json)


# ============================================================================
# 直接執行測試
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # 測試用參數
    test_year = 2025
    test_race = "Qatar"
    test_session = "R"
    
    if len(sys.argv) >= 4:
        test_year = int(sys.argv[1])
        test_race = sys.argv[2]
        test_session = sys.argv[3]
    
    result = run_tire_saving_analysis(test_year, test_race, test_session)
    
    if result["success"]:
        print("\n" + "=" * 60)
        print("F86 省輪胎行為分析結果")
        print("=" * 60)
        
        overview = result["data"]["race_overview"]
        print(f"\n大幅省輪胎: {overview['drivers_with_heavy_saving']}")
        print(f"中等省輪胎: {overview['drivers_with_moderate_saving']}")
        print(f"正常駕駛: {overview['drivers_with_no_saving'][:5]}...")
        
        if overview['most_aggressive_saver']:
            print(f"\n最激進省輪胎: {overview['most_aggressive_saver']} (分數: {overview['most_aggressive_score']})")
    else:
        print(f"[ERROR] {result['message']}")
