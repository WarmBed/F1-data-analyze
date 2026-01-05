#!/usr/bin/env python3
"""
TrafficDataLoader - F1T 流量分析專用數據載入器
==============================================

基於通用數據載入器架構實現的流量分析數據載入器，負責：
- 從 f100 historical_flags JSON 讀取 position_changes 數據
- 計算賽道超車難度係數
- 分析歷年超車趨勢
- 提供 DRS Train 和 Track Position Loss 評估數據

數據來源：CLI -f100 生成的 historical_flags_{race}_{years}.json
輸出格式：標準化的流量分析數據結構

Author: F1T Team
Date: 2025-01-05
Version: 1.0.0
"""

import os
import json
import glob
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from PyQt5.QtCore import pyqtSignal

from core.logger import get_logger
from core.gui_i18n import tr

# 導入通用基礎類別
try:
    from modules.gui.base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig
except ImportError:
    from ...base.universal_data_loader_base import UniversalDataLoader, AnalysisConfig


logger = get_logger("traffic_data_loader", component="gui")


class TrafficDataLoader(UniversalDataLoader):
    """
    流量分析通用數據載入器
    
    基於 UniversalDataLoader 實現的流量分析專門載入器，
    從 f100 historical_flags JSON 讀取 position_changes 數據。
    """
    
    # 自定義信號
    overtaking_data_loaded = pyqtSignal(dict)  # 超車數據載入完成
    difficulty_calculated = pyqtSignal(float, str)  # 超車難度計算完成 (難度值, 難度等級)
    
    # 超車難度基準值（基於歷史數據統計）
    MIN_OVERTAKES_PER_RACE = 5    # Monaco 級別（極難超車）
    MAX_OVERTAKES_PER_RACE = 50   # Bahrain/Brazil 級別（容易超車）
    
    # 難度等級定義
    DIFFICULTY_LEVELS = {
        (0.0, 0.2): ("VERY_EASY", tr("非常容易超車")),
        (0.2, 0.4): ("EASY", tr("容易超車")),
        (0.4, 0.6): ("MODERATE", tr("中等難度")),
        (0.6, 0.8): ("HARD", tr("較難超車")),
        (0.8, 1.0): ("VERY_HARD", tr("極難超車")),
    }
    
    def __init__(self, parent=None):
        """初始化流量分析數據載入器"""
        # 配置流量分析參數
        config = AnalysisConfig(
            display_name=tr("流量分析"),
            debug_prefix="TRAFFIC_ANALYSIS",
            data_source="json",
            cli_function="100",  # CLI -f100 歷史旗幟分析（包含 position_changes）
            file_patterns=[
                "historical_flags_{race}_*.json",
                "historical_flags_{race}_{years}.json"
            ],
            cache_pattern="traffic_analysis_{race}.pkl",
            description=tr("賽道超車難度和流量分析"),
            search_directories=["json", "json_exports"]
        )
        
        # 註冊流量分析類型
        analysis_type = "traffic_analysis"
        if analysis_type not in self.ANALYSIS_TYPES:
            self.register_analysis_type(analysis_type, config)
        
        super().__init__(analysis_type, parent)
        
        # 快取已計算的難度數據
        self._difficulty_cache: Dict[str, Dict] = {}
        
        logger.info("[TRAFFIC_ANALYSIS] %s", tr("初始化完成"))
    
    def load_historical_flags_data(self, race: str) -> Optional[Dict[str, Any]]:
        """
        載入指定賽道的歷史旗幟數據
        
        Args:
            race: 賽事名稱 (例如: "Japan", "Monaco", "Brazil")
            
        Returns:
            歷史旗幟數據字典，包含 yearly_summary 和 position_changes
        """
        logger.info("[TRAFFIC_ANALYSIS] %s: %s", tr("載入歷史旗幟數據"), race)
        
        # 搜尋匹配的 JSON 檔案
        json_dir = Path("json")
        if not json_dir.exists():
            logger.error("[TRAFFIC_ANALYSIS] %s", tr("json 目錄不存在"))
            return None
        
        # 搜尋模式：historical_flags_{race}_*.json
        patterns = [
            f"historical_flags_{race}_*.json",
            f"historical_flags_{race.replace(' ', '_')}_*.json",
            f"historical_flags_{self._normalize_race_name(race)}_*.json"
        ]
        
        found_files = []
        for pattern in patterns:
            matches = list(json_dir.glob(pattern))
            found_files.extend(matches)
        
        if not found_files:
            logger.warning("[TRAFFIC_ANALYSIS] %s: %s", tr("找不到歷史旗幟數據"), race)
            return None
        
        # 選擇最新的檔案（優先選擇包含 2025 的檔案）
        found_files.sort(key=lambda f: ("2025" in f.name, f.stat().st_mtime), reverse=True)
        selected_file = found_files[0]
        
        logger.info("[TRAFFIC_ANALYSIS] %s: %s", tr("使用檔案"), selected_file.name)
        
        try:
            with open(selected_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data
        except Exception as e:
            logger.error("[TRAFFIC_ANALYSIS] %s: %s", tr("讀取 JSON 失敗"), e)
            return None
    
    def calculate_overtaking_difficulty(self, race: str, 
                                        use_cache: bool = True) -> Dict[str, Any]:
        """
        計算指定賽道的超車難度
        
        Args:
            race: 賽事名稱
            use_cache: 是否使用快取
            
        Returns:
            包含超車難度分析結果的字典：
            {
                "difficulty_score": 0.0-1.0,
                "difficulty_level": "MODERATE",
                "difficulty_label": "中等難度",
                "avg_overtakes_per_race": 25.5,
                "yearly_overtakes": {"2023": 30, "2024": 21, ...},
                "trend": "decreasing",
                "confidence": 0.85
            }
        """
        # 檢查快取
        if use_cache and race in self._difficulty_cache:
            logger.debug("[TRAFFIC_ANALYSIS] %s: %s", tr("使用快取數據"), race)
            return self._difficulty_cache[race]
        
        # 載入歷史數據
        data = self.load_historical_flags_data(race)
        if not data:
            return self._create_default_difficulty_result(race)
        
        # 提取 yearly_summary
        yearly_summary = self._extract_yearly_summary(data)
        if not yearly_summary:
            return self._create_default_difficulty_result(race)
        
        # 計算各年度超車數據
        yearly_overtakes = {}
        for year, year_data in yearly_summary.items():
            if isinstance(year_data, dict):
                # position_changes 是純賽道超車數
                overtakes = year_data.get('position_changes', 0)
                # 如果有詳細數據，優先使用 on_track_overtakes
                detail = year_data.get('position_changes_detail', {})
                if detail and 'on_track_overtakes' in detail:
                    overtakes = detail.get('on_track_overtakes', overtakes)
                yearly_overtakes[year] = overtakes
        
        # 計算平均超車數
        valid_overtakes = [v for v in yearly_overtakes.values() if v > 0]
        if not valid_overtakes:
            return self._create_default_difficulty_result(race)
        
        avg_overtakes = sum(valid_overtakes) / len(valid_overtakes)
        
        # 計算難度分數 (0.0 = 極易超車, 1.0 = 極難超車)
        difficulty_score = self._calculate_difficulty_score(avg_overtakes)
        
        # 確定難度等級
        difficulty_level, difficulty_label = self._get_difficulty_level(difficulty_score)
        
        # 分析趨勢
        trend = self._analyze_trend(yearly_overtakes)
        
        # 計算信心度（基於可用年份數量）
        confidence = min(1.0, len(valid_overtakes) / 4.0)  # 4年數據 = 100% 信心
        
        result = {
            "race": race,
            "difficulty_score": round(difficulty_score, 3),
            "difficulty_level": difficulty_level,
            "difficulty_label": difficulty_label,
            "avg_overtakes_per_race": round(avg_overtakes, 1),
            "yearly_overtakes": yearly_overtakes,
            "trend": trend,
            "confidence": round(confidence, 2),
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        # 快取結果
        self._difficulty_cache[race] = result
        
        # 發送信號
        self.difficulty_calculated.emit(difficulty_score, difficulty_level)
        
        logger.info("[TRAFFIC_ANALYSIS] %s: %s (%.1f/race, score=%.2f)", 
                   race, difficulty_label, avg_overtakes, difficulty_score)
        
        return result
    
    def get_drs_train_risk(self, race: str, 
                           our_position: int,
                           opponent_pace_delta: float = 0.0) -> Dict[str, Any]:
        """
        評估 DRS Train 風險
        
        Args:
            race: 賽事名稱
            our_position: 我方車手位置
            opponent_pace_delta: 與前車的速度差 (秒/圈)
            
        Returns:
            DRS Train 風險評估結果
        """
        difficulty = self.calculate_overtaking_difficulty(race)
        difficulty_score = difficulty.get("difficulty_score", 0.5)
        
        # DRS Train 風險公式:
        # - 難超車的賽道 = 更高風險
        # - 速度差越小 = 更高風險
        # - 中場位置 = 更高風險 (車多)
        
        # 位置因素 (P6-P15 風險最高)
        position_factor = 1.0
        if 6 <= our_position <= 15:
            position_factor = 1.3  # 中場擁擠
        elif our_position <= 5:
            position_factor = 0.7  # 前方車少
        else:
            position_factor = 0.9  # 後方車散開
        
        # 速度差因素 (0.3秒內難以超車)
        pace_factor = 1.0
        if abs(opponent_pace_delta) < 0.3:
            pace_factor = 1.5  # 速度接近，難以超車
        elif abs(opponent_pace_delta) < 0.5:
            pace_factor = 1.2
        elif abs(opponent_pace_delta) > 1.0:
            pace_factor = 0.6  # 速度差大，較易超車
        
        # 基礎 DRS Train 風險
        base_risk = difficulty_score * 0.6 + 0.2  # 20% 基礎風險
        
        # 總風險
        total_risk = min(1.0, base_risk * position_factor * pace_factor)
        
        # 估算卡在車陣中的時間損失 (秒)
        # 難超車賽道每圈損失更多
        time_loss_per_lap = difficulty_score * 0.5 * pace_factor  # 0-0.5 秒/圈
        
        return {
            "drs_train_risk": round(total_risk, 2),
            "risk_level": self._get_risk_level(total_risk),
            "estimated_time_loss_per_lap": round(time_loss_per_lap, 2),
            "factors": {
                "difficulty_factor": round(difficulty_score, 2),
                "position_factor": round(position_factor, 2),
                "pace_factor": round(pace_factor, 2)
            },
            "recommendation": self._get_drs_train_recommendation(total_risk, difficulty_score)
        }
    
    def get_track_position_loss(self, race: str,
                                 pit_lap: int,
                                 our_position_before_pit: int,
                                 pit_stop_time: float = 22.0,
                                 traffic_density: float = 0.5) -> Dict[str, Any]:
        """
        評估進站後的 Track Position 損失
        
        Args:
            race: 賽事名稱
            pit_lap: 進站圈數
            our_position_before_pit: 進站前位置
            pit_stop_time: 進站時間 (秒)
            traffic_density: 賽道擁擠程度 (0-1)
            
        Returns:
            Track Position 損失評估結果
        """
        difficulty = self.calculate_overtaking_difficulty(race)
        difficulty_score = difficulty.get("difficulty_score", 0.5)
        
        # 估算進站損失位置數
        # 基礎損失: ~3-4 位 (假設 22 秒進站 + 出站)
        base_positions_lost = pit_stop_time / 6.0  # 約每 6 秒損失 1 位
        
        # 交通密度影響
        traffic_penalty = traffic_density * 2  # 最多額外損失 2 位
        
        # 難超車賽道 = 回補更困難
        recovery_difficulty = difficulty_score
        
        estimated_loss = base_positions_lost + traffic_penalty
        
        # 回補時間估算 (圈數)
        # 假設每圈可追回 0.3 秒差距，每個位置約需 1-2 秒差距
        time_per_position = 1.5  # 秒
        recovery_pace_advantage = 0.3  # 假設有 0.3 秒/圈的優勢
        
        # 難超車賽道需要更長時間
        laps_to_recover_one = time_per_position / recovery_pace_advantage
        laps_to_recover_one *= (1 + recovery_difficulty * 0.5)  # 難超車增加 50%
        
        total_laps_to_recover = laps_to_recover_one * estimated_loss
        
        return {
            "estimated_positions_lost": round(estimated_loss, 1),
            "recovery_difficulty": round(recovery_difficulty, 2),
            "laps_to_recover": round(total_laps_to_recover, 1),
            "undercut_potential": self._calculate_undercut_potential(difficulty_score),
            "overcut_potential": self._calculate_overcut_potential(difficulty_score),
            "recommendation": self._get_pit_timing_recommendation(
                difficulty_score, our_position_before_pit, traffic_density
            )
        }
    
    def get_all_circuits_difficulty(self) -> List[Dict[str, Any]]:
        """
        獲取所有賽道的超車難度排名
        
        Returns:
            按超車難度排序的賽道列表
        """
        # 2025 賽曆中的所有賽道
        circuits = [
            "Abu Dhabi", "Australia", "Austria", "Azerbaijan", "Bahrain",
            "Belgium", "Brazil", "Canada", "China", "Emilia Romagna",
            "Great Britain", "Hungary", "Italy", "Japan", "Las Vegas",
            "Mexico", "Miami", "Monaco", "Netherlands", "Qatar",
            "Saudi Arabia", "Singapore", "Spain", "United States"
        ]
        
        results = []
        for circuit in circuits:
            difficulty = self.calculate_overtaking_difficulty(circuit, use_cache=True)
            results.append(difficulty)
        
        # 按難度分數排序 (最難的在前)
        results.sort(key=lambda x: x.get("difficulty_score", 0.5), reverse=True)
        
        return results
    
    # ========== 私有輔助方法 ==========
    
    def _normalize_race_name(self, race: str) -> str:
        """正規化賽事名稱"""
        # 處理常見的別名
        aliases = {
            "Australian": "Australia",
            "British": "Great_Britain",
            "Dutch": "Netherlands",
            "Japanese": "Japan",
            "Saudi_Arabian": "Saudi_Arabia",
            "Mexican": "Mexico",
            "Spanish": "Spain",
            "Belgian": "Belgium",
            "Sao Paulo": "Brazil",
            "São Paulo": "Brazil",
        }
        
        normalized = race.replace(" ", "_")
        return aliases.get(normalized, normalized)
    
    def _extract_yearly_summary(self, data: Dict) -> Optional[Dict]:
        """從數據中提取 yearly_summary"""
        # 嘗試多種可能的路徑
        if "data" in data and "yearly_summary" in data["data"]:
            return data["data"]["yearly_summary"]
        if "yearly_summary" in data:
            return data["yearly_summary"]
        if "summary" in data:
            return data["summary"]
        return None
    
    def _calculate_difficulty_score(self, avg_overtakes: float) -> float:
        """
        計算超車難度分數
        
        公式: difficulty = 1.0 - (avg_overtakes - MIN) / (MAX - MIN)
        
        Returns:
            0.0-1.0 的難度分數 (1.0 = 最難)
        """
        if avg_overtakes <= self.MIN_OVERTAKES_PER_RACE:
            return 1.0
        if avg_overtakes >= self.MAX_OVERTAKES_PER_RACE:
            return 0.0
        
        normalized = (avg_overtakes - self.MIN_OVERTAKES_PER_RACE) / \
                     (self.MAX_OVERTAKES_PER_RACE - self.MIN_OVERTAKES_PER_RACE)
        
        return 1.0 - normalized
    
    def _get_difficulty_level(self, score: float) -> Tuple[str, str]:
        """根據分數獲取難度等級"""
        for (low, high), (level, label) in self.DIFFICULTY_LEVELS.items():
            if low <= score < high:
                return level, label
        return "VERY_HARD", tr("極難超車")
    
    def _analyze_trend(self, yearly_overtakes: Dict[str, int]) -> str:
        """分析超車趨勢"""
        if len(yearly_overtakes) < 2:
            return "unknown"
        
        years = sorted(yearly_overtakes.keys())
        values = [yearly_overtakes[y] for y in years]
        
        # 簡單線性趨勢
        if len(values) >= 2:
            first_half = sum(values[:len(values)//2]) / max(1, len(values)//2)
            second_half = sum(values[len(values)//2:]) / max(1, len(values) - len(values)//2)
            
            if second_half > first_half * 1.1:
                return "increasing"
            elif second_half < first_half * 0.9:
                return "decreasing"
        
        return "stable"
    
    def _get_risk_level(self, risk: float) -> str:
        """獲取風險等級描述"""
        if risk < 0.3:
            return tr("低風險")
        elif risk < 0.6:
            return tr("中等風險")
        elif risk < 0.8:
            return tr("高風險")
        else:
            return tr("極高風險")
    
    def _get_drs_train_recommendation(self, risk: float, difficulty: float) -> str:
        """獲取 DRS Train 策略建議"""
        if risk > 0.7 and difficulty > 0.6:
            return tr("建議採用 undercut 策略，避免被卡在車陣中")
        elif risk > 0.5:
            return tr("注意進站時機，盡量避開車陣")
        else:
            return tr("DRS Train 風險可控，可正常執行策略")
    
    def _calculate_undercut_potential(self, difficulty: float) -> str:
        """計算 undercut 潛力"""
        if difficulty > 0.7:
            return tr("非常有效 - 難超車賽道 undercut 價值高")
        elif difficulty > 0.5:
            return tr("有效 - 建議考慮 undercut")
        else:
            return tr("一般 - 賽道超車容易，undercut 優勢有限")
    
    def _calculate_overcut_potential(self, difficulty: float) -> str:
        """計算 overcut 潛力"""
        if difficulty > 0.7:
            return tr("較低 - 出站後難以回補位置")
        elif difficulty > 0.5:
            return tr("中等 - 取決於輪胎優勢")
        else:
            return tr("較高 - 賽道超車容易，可考慮 overcut")
    
    def _get_pit_timing_recommendation(self, difficulty: float, 
                                       position: int, 
                                       traffic: float) -> str:
        """獲取進站時機建議"""
        if difficulty > 0.7 and position <= 10:
            return tr("強烈建議提前進站 (undercut)，保護賽道位置")
        elif difficulty > 0.5 and traffic > 0.6:
            return tr("建議避開車陣進站窗口，或採用反向策略")
        else:
            return tr("可根據輪胎狀況正常進站")
    
    def _create_default_difficulty_result(self, race: str) -> Dict[str, Any]:
        """創建預設難度結果（當數據不可用時）"""
        return {
            "race": race,
            "difficulty_score": 0.5,
            "difficulty_level": "MODERATE",
            "difficulty_label": tr("中等難度"),
            "avg_overtakes_per_race": 0,
            "yearly_overtakes": {},
            "trend": "unknown",
            "confidence": 0.0,
            "error": tr("無法載入歷史數據")
        }
    
    # ========== 必須實現的抽象方法 ==========
    
    def _validate_load_parameters(self, params: Dict[str, Any]) -> bool:
        """驗證載入參數"""
        if "race" not in params:
            logger.error("[TRAFFIC_ANALYSIS] %s", tr("缺少必要參數: race"))
            return False
        return True
    
    def _build_filename_patterns(self, **kwargs) -> List[str]:
        """構建檔案名稱搜尋模式"""
        race = kwargs.get("race", "*")
        return [
            f"historical_flags_{race}_*.json",
            f"historical_flags_{self._normalize_race_name(race)}_*.json"
        ]
    
    def _generate_data_via_cli(self, **kwargs) -> bool:
        """
        [已禁用] 透過 CLI 工具生成數據
        
        API-ONLY 模式: 此方法已禁用
        """
        logger.warning("[TRAFFIC_ANALYSIS] %s", tr("[API-ONLY] CLI 調用已禁用"))
        return False
    
    def _validate_data_format(self, raw_data: Any) -> bool:
        """驗證數據格式"""
        if not isinstance(raw_data, dict):
            return False
        
        # 檢查是否有 yearly_summary
        yearly_summary = self._extract_yearly_summary(raw_data)
        return yearly_summary is not None
    
    def _process_data(self, raw_data: Any) -> Dict[str, Any]:
        """處理數據為標準格式"""
        return raw_data  # 歷史旗幟數據已經是標準格式
