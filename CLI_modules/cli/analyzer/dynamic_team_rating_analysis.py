"""
動態車隊評級分析模組 - CLI Function 80

功能：
1. 基於歷史數據（2023-2024）計算車隊基準評級
2. 結合 2025 賽季數據動態更新評級
3. 使用 Q 排位賽結果預測 R 正賽結果
4. 載入實際正賽結果計算 rank_change
5. 輸出 JSON 格式分析結果（與 FP3→Q 格式兼容）

評級公式：
rating = (win_rate * 4) + (pole_rate * 2) + (podium_rate * 2) + (normalized_points * 2)

輸出格式（與 FP3→Q 相同）：
{
  "metadata": {"track": "...", "year": ..., "has_actual_results": true/false},
  "predictions": [
    {"rank": 1, "driver": "VER", "team": "...", "team_rating": 6.37, 
     "q_position": 1, "predicted_position": 1, "actual_position": 1, "rank_change": 0}
  ],
  "team_ratings": {...}
}
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# F1 積分系統
POINTS_SYSTEM = {
    1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
    6: 8, 7: 6, 8: 4, 9: 2, 10: 1
}

# 2025 車隊標準名稱映射
TEAM_STANDARD_NAMES = {
    "Red Bull Racing": "Red Bull Racing",
    "Red Bull": "Red Bull Racing",
    "McLaren": "McLaren",
    "Ferrari": "Ferrari",
    "Mercedes": "Mercedes",
    "Aston Martin": "Aston Martin",
    "Alpine": "Alpine",
    "Williams": "Williams",
    "Racing Bulls": "Racing Bulls",
    "RB": "Racing Bulls",
    "Kick Sauber": "Kick Sauber",
    "Sauber": "Kick Sauber",
    "Haas": "Haas F1 Team",
    "Haas F1 Team": "Haas F1 Team",
}

# 2025 車手到車隊映射
DRIVER_TEAMS_2025 = {
    "VER": "Red Bull Racing",
    "PER": "Red Bull Racing",
    "TSU": "Red Bull Racing",
    "NOR": "McLaren",
    "PIA": "McLaren",
    "LEC": "Ferrari",
    "HAM": "Ferrari",
    "RUS": "Mercedes",
    "ANT": "Mercedes",
    "ALO": "Aston Martin",
    "STR": "Aston Martin",
    "GAS": "Alpine",
    "DOO": "Alpine",
    "COL": "Alpine",
    "ALB": "Williams",
    "SAI": "Williams",
    "LAW": "Racing Bulls",
    "HAD": "Racing Bulls",
    "BOT": "Kick Sauber",
    "BOR": "Kick Sauber",
    "OCO": "Haas F1 Team",
    "BEA": "Haas F1 Team",
    "HUL": "Haas F1 Team",
}


@dataclass
class TeamPerformance:
    """車隊表現統計"""
    wins: int = 0
    poles: int = 0
    podiums: int = 0
    top5_finishes: int = 0
    total_races: int = 0
    total_points: float = 0
    
    @property
    def win_rate(self) -> float:
        return self.wins / self.total_races if self.total_races > 0 else 0
    
    @property
    def pole_rate(self) -> float:
        return self.poles / self.total_races if self.total_races > 0 else 0
    
    @property
    def podium_rate(self) -> float:
        return self.podiums / self.total_races if self.total_races > 0 else 0
    
    @property
    def avg_points(self) -> float:
        return self.total_points / self.total_races if self.total_races > 0 else 0
    
    def to_dict(self) -> dict:
        """轉換為字典"""
        return {
            "wins": self.wins,
            "poles": self.poles,
            "podiums": self.podiums,
            "top5_finishes": self.top5_finishes,
            "total_races": self.total_races,
            "total_points": self.total_points,
            "win_rate": round(self.win_rate, 4),
            "pole_rate": round(self.pole_rate, 4),
            "podium_rate": round(self.podium_rate, 4),
            "avg_points": round(self.avg_points, 2)
        }


class DynamicTeamRatingAnalyzer:
    """
    動態車隊評級分析器 - CLI 模組
    
    支援兩種模式：
    1. 完整評級分析（原有功能）
    2. Q→R 預測模式（新功能）- 輸出與 FP3→Q 相同格式
    """
    
    # 車隊名稱標準化
    TEAM_ALIASES = {
        "Red Bull": "Red Bull Racing",
        "RB": "Racing Bulls",
        "AlphaTauri": "Racing Bulls",
        "Sauber": "Kick Sauber",
        "Alfa Romeo": "Kick Sauber",
        "Haas": "Haas F1 Team",
    }
    
    def __init__(self, 
                 base_years: List[int] = None,
                 min_rating: float = 1.0,
                 max_rating: float = 10.0):
        """
        初始化分析器
        
        Args:
            base_years: 基準年份列表（預設 2023-2024）
            min_rating: 最低評級
            max_rating: 最高評級
        """
        self.base_years = base_years or [2023, 2024]
        self.min_rating = min_rating
        self.max_rating = max_rating
        
        # 車隊表現數據
        self.base_performance: Dict[str, TeamPerformance] = {}
        self.current_performance: Dict[str, TeamPerformance] = {}
        
        # 車隊評級
        self.base_ratings: Dict[str, float] = {}
        self.current_ratings: Dict[str, float] = {}
        
        # 車手到車隊映射
        self.driver_teams: Dict[str, str] = dict(DRIVER_TEAMS_2025)
        
        # 評級歷史（逐場變化）
        self.rating_history: Dict[str, List[dict]] = defaultdict(list)
        
        # 分析結果
        self._analysis_result: Optional[dict] = None
        
        # Q→R 預測相關
        self._race_name: Optional[str] = None
        self._q_results: Optional[List[dict]] = None
        self._r_results: Optional[List[dict]] = None
    
    def _normalize_team_name(self, team: str) -> str:
        """標準化車隊名稱"""
        if team in TEAM_STANDARD_NAMES:
            return TEAM_STANDARD_NAMES[team]
        return self.TEAM_ALIASES.get(team, team)
    
    def _calculate_rating(self, perf: TeamPerformance, max_points: float) -> float:
        """
        計算評級
        
        公式：rating = (win_rate * 4) + (pole_rate * 2) + (podium_rate * 2) + (normalized_points * 2)
        """
        normalized_points = perf.avg_points / max_points if max_points > 0 else 0
        
        raw_rating = (
            perf.win_rate * 4 +
            perf.pole_rate * 2 +
            perf.podium_rate * 2 +
            normalized_points * 2
        )
        
        return max(self.min_rating, min(self.max_rating, round(raw_rating, 2)))
    
    def _get_dynamic_weight(self, round_num: int) -> float:
        """
        根據比賽場數計算動態權重
        
        Returns:
            當前賽季數據的權重（0-1）
        """
        if round_num <= 5:
            return 0.1  # 基準 90% + 當前 10%
        elif round_num <= 10:
            return 0.3  # 基準 70% + 當前 30%
        elif round_num <= 15:
            return 0.5  # 基準 50% + 當前 50%
        else:
            return 0.7  # 基準 30% + 當前 70%
    
    def load_historical_data(self) -> bool:
        """載入 2023-2024 歷史數據"""
        try:
            # 嘗試導入歷史數據模組
            sys.path.insert(0, str(BASE_DIR / "Live_timing_test"))
            from f1_historical_data import F1_2023_RESULTS, F1_2024_RESULTS, DRIVER_TEAMS
            
            print("[INFO] 載入 2023-2024 歷史數據...")
            
            # 處理 2023 和 2024 數據
            for results in [F1_2023_RESULTS, F1_2024_RESULTS]:
                self._process_season_results(results, DRIVER_TEAMS, "base")
            
            # 計算基準評級
            self._calculate_ratings("base")
            
            print(f"[OK] 已載入 2023-2024 基準數據，共 {sum(p.total_races for p in self.base_performance.values())} 場比賽表現")
            return True
            
        except ImportError as e:
            print(f"[WARN] 無法導入歷史數據模組: {e}")
            
            # 嘗試從 JSON 檔案載入
            json_file = BASE_DIR / "json/historical_data/f1_2023_2024_training_data.json"
            if json_file.exists():
                print(f"[INFO] 從 JSON 載入: {json_file}")
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._process_training_json(data)
                self._calculate_ratings("base")
                return True
            else:
                # 使用硬編碼的預設評級
                print(f"[WARN] 找不到歷史數據，使用預設評級")
                self._use_default_ratings()
                return True
        except Exception as e:
            print(f"[ERROR] 載入歷史數據失敗: {e}")
            self._use_default_ratings()
            return True
    
    def _use_default_ratings(self):
        """使用預設的車隊評級（基於 2023-2024 數據）"""
        self.base_ratings = {
            "Red Bull Racing": 8.05,
            "McLaren": 4.89,
            "Ferrari": 4.18,
            "Mercedes": 3.04,
            "Alpine": 3.33,
            "Aston Martin": 2.22,
            "Williams": 2.20,
            "Racing Bulls": 2.00,
            "Kick Sauber": 1.80,
            "Haas F1 Team": 1.70,
        }
        self.current_ratings = {
            "Red Bull Racing": 6.37,
            "McLaren": 6.30,
            "Ferrari": 4.19,
            "Mercedes": 3.47,
            "Alpine": 3.33,
            "Aston Martin": 2.22,
            "Williams": 2.20,
            "Racing Bulls": 5.00,
            "Kick Sauber": 5.00,
            "Haas F1 Team": 5.00,
        }
        print("[OK] 已載入預設車隊評級")
    
    def _process_season_results(self, results: list, driver_teams: dict, mode: str):
        """處理單賽季結果"""
        perf_dict = self.base_performance if mode == "base" else self.current_performance
        
        for race in results:
            pole = race.get("pole")
            winner = race.get("winner")
            r_top5 = race.get("r_top5", [])
            
            teams_in_race = set()
            
            for pos, driver in enumerate(r_top5, 1):
                team = self._normalize_team_name(driver_teams.get(driver, "Unknown"))
                self.driver_teams[driver] = team
                
                if team not in perf_dict:
                    perf_dict[team] = TeamPerformance()
                
                perf = perf_dict[team]
                
                # 每場比賽每車隊只計算一次參賽
                if team not in teams_in_race:
                    perf.total_races += 1
                    teams_in_race.add(team)
                
                # 統計
                if driver == winner:
                    perf.wins += 1
                if driver == pole:
                    perf.poles += 1
                if pos <= 3:
                    perf.podiums += 1
                if pos <= 5:
                    perf.top5_finishes += 1
                
                perf.total_points += POINTS_SYSTEM.get(pos, 0)
    
    def _process_training_json(self, data: dict):
        """從訓練 JSON 處理數據"""
        performance = defaultdict(TeamPerformance)
        
        # 建立車手到車隊映射
        for sample in data.get("all", []):
            driver = sample["driver"]
            team = self._normalize_team_name(sample.get("team", "Unknown"))
            self.driver_teams[driver] = team
        
        # 計算每場比賽的表現
        races_processed = set()
        for sample in data.get("all", []):
            race_key = f"{sample['year']}_{sample['race']}"
            driver = sample["driver"]
            team = self._normalize_team_name(sample.get("team", "Unknown"))
            q_pos = sample["q_position"]
            is_winner = sample["is_winner"]
            
            team_race_key = f"{race_key}_{team}"
            if team_race_key not in races_processed:
                performance[team].total_races += 1
                races_processed.add(team_race_key)
            
            if is_winner:
                performance[team].wins += 1
            if q_pos == 1:
                performance[team].poles += 1
            if q_pos <= 3:
                performance[team].podiums += 1
            if q_pos <= 5:
                performance[team].top5_finishes += 1
            
            performance[team].total_points += POINTS_SYSTEM.get(q_pos, 0)
        
        self.base_performance = dict(performance)
    
    def _calculate_ratings(self, mode: str):
        """計算評級"""
        perf_dict = self.base_performance if mode == "base" else self.current_performance
        rating_dict = self.base_ratings if mode == "base" else self.current_ratings
        
        if not perf_dict:
            return
        
        max_points = max((p.avg_points for p in perf_dict.values()), default=1)
        
        for team, perf in perf_dict.items():
            rating_dict[team] = self._calculate_rating(perf, max_points)
    
    def load_2025_results(self, up_to_round: Optional[int] = None) -> bool:
        """
        載入 2025 賽季結果
        
        Args:
            up_to_round: 只載入到第 N 輪（用於模擬漸進更新）
        """
        try:
            sys.path.insert(0, str(BASE_DIR / "Live_timing_test"))
            from f1_2025_results import F1_2025_RESULTS, DRIVER_TEAMS_2025 as DT_2025
            
            print("[INFO] 載入 2025 賽季數據...")
            
            results = F1_2025_RESULTS
            if up_to_round is not None:
                results = [r for r in results if r.get("round", 0) <= up_to_round]
            
            # 重置當前表現
            self.current_performance = {}
            self.rating_history = defaultdict(list)
            
            # 逐場計算評級變化
            for race in results:
                self._process_race_and_update_ratings(race, DT_2025)
            
            # 更新車手車隊映射
            self.driver_teams.update(DT_2025)
            
            print(f"[OK] 已載入 2025 賽季 {len(results)} 場比賽結果")
            return True
            
        except ImportError as e:
            print(f"[WARN] 無法導入 2025 結果模組: {e}")
            
            json_file = BASE_DIR / "json/historical_data/f1_2025_results.json"
            if json_file.exists():
                print(f"[INFO] 從 JSON 載入: {json_file}")
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                results = data.get("races", [])
                driver_teams = data.get("driver_teams", {})
                
                if up_to_round is not None:
                    results = [r for r in results if r.get("round", 0) <= up_to_round]
                
                self.current_performance = {}
                self.rating_history = defaultdict(list)
                
                for race in results:
                    self._process_race_and_update_ratings(race, driver_teams)
                
                self.driver_teams.update(driver_teams)
                print(f"[OK] 已載入 2025 賽季 {len(results)} 場比賽結果")
                return True
            else:
                print(f"[WARN] 找不到 2025 結果檔案，使用預設評級")
                return True
        except Exception as e:
            print(f"[ERROR] 載入 2025 數據失敗: {e}")
            return True
    
    def _process_race_and_update_ratings(self, race: dict, driver_teams: dict):
        """處理單場比賽並更新評級"""
        round_num = race.get("round", 0)
        race_name = race.get("race", "Unknown")
        pole = race.get("pole")
        winner = race.get("winner")
        r_top5 = race.get("r_top5", [])
        
        teams_in_race = set()
        
        for pos, driver in enumerate(r_top5, 1):
            team = self._normalize_team_name(driver_teams.get(driver, "Unknown"))
            
            if team not in self.current_performance:
                self.current_performance[team] = TeamPerformance()
            
            perf = self.current_performance[team]
            
            if team not in teams_in_race:
                perf.total_races += 1
                teams_in_race.add(team)
            
            if driver == winner:
                perf.wins += 1
            if driver == pole:
                perf.poles += 1
            if pos <= 3:
                perf.podiums += 1
            if pos <= 5:
                perf.top5_finishes += 1
            
            perf.total_points += POINTS_SYSTEM.get(pos, 0)
        
        # 計算當前評級
        self._calculate_ratings("current")
        
        # 計算加權評級
        weight = self._get_dynamic_weight(round_num)
        
        all_teams = set(self.base_ratings.keys()) | set(self.current_ratings.keys())
        combined_ratings = {}
        
        for team in all_teams:
            base_r = self.base_ratings.get(team, 5.0)
            curr_r = self.current_ratings.get(team, base_r)
            
            if team in self.current_performance:
                combined_ratings[team] = round(base_r * (1 - weight) + curr_r * weight, 2)
            else:
                combined_ratings[team] = base_r
            
            # 記錄歷史
            self.rating_history[team].append({
                "round": round_num,
                "race": race_name,
                "rating": combined_ratings[team],
                "weight": weight
            })
        
        # 更新當前評級為加權後的值
        self.current_ratings = combined_ratings

    # ===== Q→R 預測功能（新增）=====
    
    def load_qualifying_results(self, year: int, race: str) -> bool:
        """
        載入排位賽結果
        
        Args:
            year: 年份
            race: 賽道名稱
            
        Returns:
            bool: 是否成功載入
        """
        self._race_name = race
        self._q_results = []
        
        # 搜索 qualifying_prediction JSON
        json_dir = BASE_DIR / "json"
        patterns = [
            f"qualifying_prediction_{year}_{race}.json",
            f"qualifying_prediction_{year}_{race.replace(' ', '_')}.json",
        ]
        
        for pattern in patterns:
            json_file = json_dir / pattern
            if json_file.exists():
                print(f"[INFO] 載入排位賽結果: {json_file.name}")
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 從 predictions 中提取 actual_q_rank
                for pred in data.get("predictions", []):
                    driver = pred.get("driver")
                    q_rank = pred.get("actual_q_rank")
                    team = pred.get("team", self.driver_teams.get(driver, "Unknown"))
                    
                    if driver and q_rank:
                        self._q_results.append({
                            "driver": driver,
                            "q_position": q_rank,
                            "team": self._normalize_team_name(team)
                        })
                
                # 按 Q 位置排序
                self._q_results.sort(key=lambda x: x["q_position"])
                print(f"[OK] 載入 {len(self._q_results)} 位車手的排位賽結果")
                return True
        
        # 嘗試從 FastF1 獲取
        print(f"[WARN] 找不到排位賽 JSON，嘗試從 FastF1 獲取...")
        return self._load_q_from_fastf1(year, race)
    
    def _load_q_from_fastf1(self, year: int, race: str) -> bool:
        """從 FastF1 載入排位賽結果"""
        try:
            import fastf1
            
            # 啟用緩存
            cache_dir = BASE_DIR / "f1_analysis_cache"
            cache_dir.mkdir(exist_ok=True)
            fastf1.Cache.enable_cache(str(cache_dir))
            
            print(f"[INFO] 從 FastF1 載入 {year} {race} 排位賽...")
            session = fastf1.get_session(year, race, 'Q')
            session.load()
            
            # 獲取排位賽結果
            results = session.results
            self._q_results = []
            
            for _, row in results.iterrows():
                driver = row.get('Abbreviation', '')
                position = row.get('Position', 0)
                team = row.get('TeamName', '')
                
                if driver and position:
                    self._q_results.append({
                        "driver": driver,
                        "q_position": int(position),
                        "team": self._normalize_team_name(team)
                    })
            
            self._q_results.sort(key=lambda x: x["q_position"])
            print(f"[OK] 從 FastF1 載入 {len(self._q_results)} 位車手")
            return len(self._q_results) > 0
            
        except Exception as e:
            print(f"[ERROR] FastF1 載入失敗: {e}")
            return False
    
    def load_race_results(self, year: int, race: str) -> bool:
        """
        載入正賽結果
        
        Args:
            year: 年份
            race: 賽道名稱
            
        Returns:
            bool: 是否成功載入（比賽可能尚未進行）
        """
        self._r_results = []
        
        # 嘗試從 FastF1 獲取正賽結果
        try:
            import fastf1
            
            # 啟用緩存
            cache_dir = BASE_DIR / "f1_analysis_cache"
            cache_dir.mkdir(exist_ok=True)
            fastf1.Cache.enable_cache(str(cache_dir))
            
            print(f"[INFO] 從 FastF1 載入 {year} {race} 正賽結果...")
            session = fastf1.get_session(year, race, 'R')
            session.load()
            
            # 檢查是否有結果
            results = session.results
            if results is None or len(results) == 0:
                print(f"[INFO] 正賽尚未進行或無結果")
                return False
            
            for _, row in results.iterrows():
                driver = row.get('Abbreviation', '')
                position = row.get('Position', 0)
                status = row.get('Status', '')
                
                if driver:
                    self._r_results.append({
                        "driver": driver,
                        "r_position": int(position) if position else 99,
                        "status": status
                    })
            
            self._r_results.sort(key=lambda x: x["r_position"])
            print(f"[OK] 載入 {len(self._r_results)} 位車手的正賽結果")
            return len(self._r_results) > 0
            
        except Exception as e:
            print(f"[INFO] 正賽結果不可用: {e}")
            return False
    
    def predict_race_positions(self) -> List[dict]:
        """
        使用車隊評級和 Q 位置預測正賽位置
        
        預測邏輯：
        - 綜合評分 = Q 位置得分 * 0.6 + 車隊評級得分 * 0.4
        - Q 位置得分 = (20 - Q位置) / 19
        - 車隊評級得分 = 車隊評級 / 10
        
        Returns:
            List[dict]: 預測結果
        """
        if not self._q_results:
            print("[ERROR] 沒有排位賽數據，無法預測")
            return []
        
        predictions = []
        
        for q_data in self._q_results:
            driver = q_data["driver"]
            q_pos = q_data["q_position"]
            team = q_data["team"]
            
            # 獲取車隊評級
            team_rating = self.current_ratings.get(team) or self.base_ratings.get(team, 5.0)
            
            # 計算綜合評分
            q_score = (20 - q_pos) / 19  # Q 位置得分 (0-1)
            rating_score = team_rating / 10  # 評級得分 (0-1)
            
            # 綜合評分 (Q 位置權重 60%, 車隊評級權重 40%)
            combined_score = q_score * 0.6 + rating_score * 0.4
            
            predictions.append({
                "driver": driver,
                "team": team,
                "team_rating": team_rating,
                "q_position": q_pos,
                "combined_score": combined_score
            })
        
        # 按綜合評分排序，生成預測位置
        predictions.sort(key=lambda x: x["combined_score"], reverse=True)
        
        for i, pred in enumerate(predictions, 1):
            pred["predicted_position"] = i
            pred["rank"] = i
        
        return predictions
    
    def build_prediction_result(self, year: int, race: str) -> dict:
        """
        構建與 FP3→Q 格式相同的預測結果
        
        Returns:
            dict: 預測結果 JSON
        """
        predictions = self.predict_race_positions()
        
        if not predictions:
            return {
                "success": False,
                "error": "無法生成預測",
                "function_id": "80"
            }
        
        # 檢查是否有實際正賽結果
        has_actual = self._r_results is not None and len(self._r_results) > 0
        
        # 建立車手到正賽位置的映射
        r_positions = {}
        if has_actual:
            for r_data in self._r_results:
                r_positions[r_data["driver"]] = r_data["r_position"]
        
        # 添加實際位置和排名變化
        for pred in predictions:
            driver = pred["driver"]
            
            if has_actual and driver in r_positions:
                actual_pos = r_positions[driver]
                pred["actual_position"] = actual_pos
                pred["rank_change"] = pred["predicted_position"] - actual_pos
            else:
                pred["actual_position"] = None
                pred["rank_change"] = None
        
        # 按預測位置排序
        predictions.sort(key=lambda x: x["rank"])
        
        # 計算準確率
        top1_correct = False
        top3_correct = 0
        
        if has_actual:
            # 檢查預測冠軍是否正確
            predicted_winner = predictions[0]["driver"]
            actual_winner = next((d for d, p in r_positions.items() if p == 1), None)
            top1_correct = predicted_winner == actual_winner
            
            # 檢查前三名準確率
            predicted_top3 = [p["driver"] for p in predictions[:3]]
            actual_top3 = [d for d, p in sorted(r_positions.items(), key=lambda x: x[1])[:3]]
            top3_correct = len(set(predicted_top3) & set(actual_top3))
        
        # 構建結果
        result = {
            "success": True,
            "message": "Q->R 正賽預測完成",
            "function_id": "80",
            "metadata": {
                "track": race,
                "year": year,
                "session": "R",
                "data_source": "Q",
                "prediction_model": "Dynamic Team Rating + Q Position",
                "prediction_time": datetime.now().isoformat(),
                "model_version": "v1.0",
                "has_actual_results": has_actual,
                "accuracy": {
                    "top1_correct": top1_correct,
                    "top3_correct": top3_correct
                } if has_actual else None
            },
            "predictions": predictions,
            "team_ratings": {
                team: {
                    "current": self.current_ratings.get(team, 5.0),
                    "base": self.base_ratings.get(team, 5.0)
                }
                for team in set(p["team"] for p in predictions)
            }
        }
        
        return result
    
    def analyze_with_prediction(self,
                                year: int = 2025,
                                race: str = None,
                                show_detailed_output: bool = True,
                                **kwargs) -> dict:
        """
        執行 Q→R 預測分析
        
        Args:
            year: 年份
            race: 賽道名稱
            show_detailed_output: 是否顯示詳細輸出
            
        Returns:
            dict: 分析結果
        """
        start_time = datetime.now()
        
        print(f"\n{'='*60}")
        print(f"[START] Q->R 正賽預測分析")
        print(f"  年份: {year}")
        print(f"  賽道: {race or '(未指定)'}")
        print(f"{'='*60}")
        
        # 載入評級數據
        self.load_historical_data()
        self.load_2025_results()
        
        # 如果未指定賽道，使用最新的排位賽數據
        if not race:
            # 搜索最新的 qualifying_prediction JSON
            json_dir = BASE_DIR / "json"
            q_files = sorted(json_dir.glob(f"qualifying_prediction_{year}_*.json"))
            if q_files:
                latest = q_files[-1]
                race = latest.stem.replace(f"qualifying_prediction_{year}_", "")
                print(f"[INFO] 使用最新賽事: {race}")
            else:
                return {
                    "success": False,
                    "error": "找不到排位賽數據",
                    "function_id": "80"
                }
        
        # 載入排位賽結果
        if not self.load_qualifying_results(year, race):
            return {
                "success": False,
                "error": f"無法載入 {race} 排位賽數據",
                "function_id": "80"
            }
        
        # 嘗試載入正賽結果
        self.load_race_results(year, race)
        
        # 構建預測結果
        result = self.build_prediction_result(year, race)
        
        # 計算執行時間
        execution_time = (datetime.now() - start_time).total_seconds()
        result["execution_time"] = f"{execution_time:.2f}s"
        
        # 顯示詳細輸出
        if show_detailed_output:
            self._print_prediction_output(result)
        
        self._analysis_result = result
        return result
    
    def _print_prediction_output(self, result: dict):
        """打印預測結果"""
        predictions = result.get("predictions", [])
        metadata = result.get("metadata", {})
        
        has_actual = metadata.get("has_actual_results", False)
        
        print(f"\n[PREDICTION] Q->R 正賽預測結果 ({metadata.get('track', '')} {metadata.get('year', '')}):")
        print("-" * 70)
        
        if has_actual:
            print(f"{'Rank':>4} | {'Driver':<5} | {'Team':<20} | {'Rating':>6} | {'Q Pos':>5} | {'Pred':>4} | {'Actual':>6} | {'Change':>6}")
        else:
            print(f"{'Rank':>4} | {'Driver':<5} | {'Team':<20} | {'Rating':>6} | {'Q Pos':>5} | {'Pred':>4}")
        
        print("-" * 70)
        
        for pred in predictions[:20]:
            if has_actual:
                actual = pred.get('actual_position', 'TBD')
                change = pred.get('rank_change', '')
                change_str = f"+{change}" if change and change > 0 else str(change) if change else "TBD"
                print(f"{pred['rank']:>4} | {pred['driver']:<5} | {pred['team']:<20} | {pred['team_rating']:>6.2f} | {pred['q_position']:>5} | {pred['predicted_position']:>4} | {actual:>6} | {change_str:>6}")
            else:
                print(f"{pred['rank']:>4} | {pred['driver']:<5} | {pred['team']:<20} | {pred['team_rating']:>6.2f} | {pred['q_position']:>5} | {pred['predicted_position']:>4}")
        
        if has_actual:
            accuracy = metadata.get("accuracy", {})
            print("-" * 70)
            print(f"[ACCURACY] 冠軍預測: {'正確' if accuracy.get('top1_correct') else '錯誤'}")
            print(f"[ACCURACY] 前三名命中: {accuracy.get('top3_correct', 0)}/3")
        
        print(f"\n{'='*60}")
        print(f"[OK] 預測分析完成")
        print(f"{'='*60}")

    # ===== 原有分析功能 =====
    
    def analyze(self, 
                year: int = 2025,
                race: str = None,
                up_to_round: Optional[int] = None,
                show_detailed_output: bool = True,
                **kwargs) -> dict:
        """
        執行分析並返回 JSON 格式結果
        
        如果指定了 race 參數，則執行 Q→R 預測分析
        否則執行完整的車隊評級分析
        
        Args:
            year: 目標年份
            race: 賽道名稱（如指定則執行 Q→R 預測）
            up_to_round: 只分析到第 N 輪
            show_detailed_output: 是否顯示詳細輸出
            
        Returns:
            dict: 分析結果（JSON 格式）
        """
        # 如果指定了 race，執行 Q→R 預測
        if race:
            return self.analyze_with_prediction(
                year=year,
                race=race,
                show_detailed_output=show_detailed_output,
                **kwargs
            )
        
        # 否則執行原有的完整評級分析
        start_time = datetime.now()
        
        print(f"\n{'='*60}")
        print("[START] 動態車隊評級分析")
        print(f"{'='*60}")
        
        # 載入基準數據
        if not self.load_historical_data():
            return {
                "success": False,
                "error": "無法載入歷史數據",
                "function_id": "80"
            }
        
        # 載入 2025 數據
        if year >= 2025:
            if not self.load_2025_results(up_to_round):
                print("[WARN] 無法載入 2025 數據，僅使用基準評級")
        
        # 構建結果
        result = self._build_analysis_result(year, up_to_round)
        
        # 計算執行時間
        execution_time = (datetime.now() - start_time).total_seconds()
        result["execution_time"] = f"{execution_time:.2f}s"
        
        # 顯示詳細輸出
        if show_detailed_output:
            self._print_detailed_output(result)
        
        self._analysis_result = result
        return result
    
    def _build_analysis_result(self, year: int, up_to_round: Optional[int]) -> dict:
        """構建分析結果"""
        # 基準評級排序
        sorted_base = sorted(self.base_ratings.items(), key=lambda x: x[1], reverse=True)
        
        # 當前評級排序
        sorted_current = sorted(self.current_ratings.items(), key=lambda x: x[1], reverse=True)
        
        # 評級變化
        rating_changes = []
        for team, current_rating in sorted_current:
            base_rating = self.base_ratings.get(team, 5.0)
            change = current_rating - base_rating
            rating_changes.append({
                "team": team,
                "base_rating": base_rating,
                "current_rating": current_rating,
                "change": round(change, 2),
                "trend": "up" if change > 0.1 else ("down" if change < -0.1 else "stable")
            })
        
        # 車隊表現詳情
        team_performance = {}
        for team, perf in self.base_performance.items():
            team_performance[team] = {
                "base": perf.to_dict(),
                "current": self.current_performance.get(team, TeamPerformance()).to_dict()
            }
        
        # 逐場評級變化
        race_by_race = []
        all_teams = list(self.base_ratings.keys())
        if self.rating_history:
            # 獲取所有比賽場次
            sample_team = list(self.rating_history.keys())[0] if self.rating_history else None
            if sample_team:
                for race_info in self.rating_history[sample_team]:
                    round_data = {
                        "round": race_info["round"],
                        "race": race_info["race"],
                        "weight": race_info["weight"],
                        "ratings": {}
                    }
                    for team in all_teams:
                        history = self.rating_history.get(team, [])
                        matching = [h for h in history if h["round"] == race_info["round"]]
                        if matching:
                            round_data["ratings"][team] = matching[0]["rating"]
                    race_by_race.append(round_data)
        
        return {
            "success": True,
            "message": "動態車隊評級分析完成",
            "function_id": "80",
            "data": {
                "analysis_type": "dynamic_team_rating",
                "year": year,
                "up_to_round": up_to_round,
                "timestamp": datetime.now().isoformat(),
                
                "formula": {
                    "description": "rating = (win_rate * 4) + (pole_rate * 2) + (podium_rate * 2) + (normalized_points * 2)",
                    "components": [
                        {"name": "win_rate", "weight": 4, "description": "勝率 (0-1)"},
                        {"name": "pole_rate", "weight": 2, "description": "桿位率 (0-1)"},
                        {"name": "podium_rate", "weight": 2, "description": "頒獎台率 (0-1)"},
                        {"name": "normalized_points", "weight": 2, "description": "標準化積分 (0-1)"}
                    ],
                    "range": {"min": 1.0, "max": 10.0}
                },
                
                "dynamic_weighting": {
                    "description": "根據比賽場數調整基準與當前評級的權重",
                    "rules": [
                        {"rounds": "1-5", "base_weight": 0.9, "current_weight": 0.1},
                        {"rounds": "6-10", "base_weight": 0.7, "current_weight": 0.3},
                        {"rounds": "11-15", "base_weight": 0.5, "current_weight": 0.5},
                        {"rounds": "16+", "base_weight": 0.3, "current_weight": 0.7}
                    ]
                },
                
                "base_ratings": {
                    "years": self.base_years,
                    "rankings": [{"rank": i+1, "team": team, "rating": rating} 
                                 for i, (team, rating) in enumerate(sorted_base)]
                },
                
                "current_ratings": {
                    "year": year,
                    "up_to_round": up_to_round,
                    "rankings": [{"rank": i+1, "team": team, "rating": rating} 
                                 for i, (team, rating) in enumerate(sorted_current)]
                },
                
                "rating_changes": rating_changes,
                
                "team_performance": team_performance,
                
                "race_by_race_evolution": race_by_race,
                
                "driver_team_mapping": dict(self.driver_teams)
            }
        }
    
    def _print_detailed_output(self, result: dict):
        """打印詳細輸出"""
        data = result.get("data", {})
        
        print(f"\n[FORMULA] 評級計算公式:")
        print(f"  rating = (win_rate * 4) + (pole_rate * 2) + (podium_rate * 2) + (normalized_points * 2)")
        
        print(f"\n[BASE] 基準評級 (2023-2024):")
        base_rankings = data.get("base_ratings", {}).get("rankings", [])
        for item in base_rankings[:6]:
            print(f"  {item['rank']:2d}. {item['team']:20} | {item['rating']:.2f}")
        
        print(f"\n[CURRENT] 當前評級 ({data.get('year', 2025)}):")
        current_rankings = data.get("current_ratings", {}).get("rankings", [])
        for item in current_rankings[:6]:
            print(f"  {item['rank']:2d}. {item['team']:20} | {item['rating']:.2f}")
        
        print(f"\n[CHANGES] 評級變化:")
        for change in data.get("rating_changes", [])[:6]:
            trend_symbol = "+" if change["trend"] == "up" else ("-" if change["trend"] == "down" else "=")
            print(f"  {change['team']:20} | {change['base_rating']:.2f} -> {change['current_rating']:.2f} ({trend_symbol}{abs(change['change']):.2f})")
        
        print(f"\n{'='*60}")
        print(f"[OK] 分析完成")
        print(f"{'='*60}")
    
    def save_to_json(self, output_dir: Optional[Path] = None, filename: Optional[str] = None) -> str:
        """
        將分析結果保存為 JSON 檔案
        
        Args:
            output_dir: 輸出目錄
            filename: 檔案名稱（不含副檔名）
            
        Returns:
            str: 保存的檔案路徑
        """
        if self._analysis_result is None:
            raise ValueError("請先執行 analyze() 方法")
        
        if output_dir is None:
            output_dir = BASE_DIR / "json/prediction"
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 判斷是否為 Q→R 預測結果
        metadata = self._analysis_result.get("metadata", {})
        if metadata.get("data_source") == "Q":
            # Q→R 預測格式
            race = metadata.get("track", "Unknown")
            year = metadata.get("year", 2025)
            if filename is None:
                filename = f"race_prediction_{year}_{race}"
        else:
            # 原有格式
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"dynamic_team_rating_{timestamp}"
        
        output_path = output_dir / f"{filename}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self._analysis_result, f, indent=2, ensure_ascii=False)
        
        print(f"[SAVE] JSON 已保存: {output_path}")
        return str(output_path)
    
    def get_team_rating(self, team: str) -> float:
        """獲取車隊評級"""
        team = self._normalize_team_name(team)
        if team in self.current_ratings:
            return self.current_ratings[team]
        if team in self.base_ratings:
            return self.base_ratings[team]
        return 5.0
    
    def get_driver_team_rating(self, driver_code: str) -> Tuple[str, float]:
        """獲取車手的車隊和評級"""
        team = self.driver_teams.get(driver_code, "Unknown")
        rating = self.get_team_rating(team)
        return team, rating


def run_dynamic_team_rating_analysis(data_loader=None, 
                                     year: int = 2025,
                                     race: str = None,
                                     up_to_round: int = None,
                                     show_detailed_output: bool = True,
                                     **kwargs) -> dict:
    """
    執行動態車隊評級分析 - CLI 入口函數
    
    Args:
        data_loader: 數據載入器（可選）
        year: 目標年份（預設 2025）
        race: 賽道名稱（如指定則執行 Q→R 預測）
        up_to_round: 只分析到第 N 輪（可選）
        show_detailed_output: 是否顯示詳細輸出
        **kwargs: 額外參數
        
    Returns:
        dict: 分析結果
    """
    analyzer = DynamicTeamRatingAnalyzer()
    
    result = analyzer.analyze(
        year=year,
        race=race,
        up_to_round=up_to_round,
        show_detailed_output=show_detailed_output,
        **kwargs
    )
    
    # 保存 JSON
    if result.get("success"):
        try:
            analyzer.save_to_json()
        except Exception as e:
            print(f"[WARN] JSON 保存失敗: {e}")
    
    return result


if __name__ == "__main__":
    import sys
    
    print("="*60)
    print("動態車隊評級分析模組測試")
    print("="*60)
    
    # 檢查命令行參數
    if len(sys.argv) > 1:
        # 指定賽道，執行 Q→R 預測
        race = " ".join(sys.argv[1:])
        print(f"\n測試 Q->R 預測模式: {race}")
        result = run_dynamic_team_rating_analysis(
            year=2025,
            race=race,
            show_detailed_output=True
        )
    else:
        # 無參數，執行完整評級分析
        print("\n測試完整評級分析模式")
        result = run_dynamic_team_rating_analysis(show_detailed_output=True)
    
    if result.get("success"):
        print("\n[TEST] 測試成功")
        
        if "predictions" in result:
            print(f"  - 預測車手數: {len(result['predictions'])}")
            print(f"  - 有實際結果: {result.get('metadata', {}).get('has_actual_results', False)}")
        else:
            data = result.get("data", {})
            print(f"  - 基準評級數: {len(data.get('base_ratings', {}).get('rankings', []))}")
            print(f"  - 當前評級數: {len(data.get('current_ratings', {}).get('rankings', []))}")
    else:
        print(f"\n[TEST] 測試失敗: {result.get('error')}")
