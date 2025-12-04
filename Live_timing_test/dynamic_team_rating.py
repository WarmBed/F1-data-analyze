"""
動態車隊評級系統

方案 A: 基於歷史數據（2023-2024）計算車隊基準評級
方案 B: 每場 2025 比賽後動態更新評級

特點:
1. 不使用硬編碼評級
2. 基於實際比賽結果計算
3. 支持滾動更新（最近 N 場比賽權重更高）
4. 可選 LLM 輔助調整（未來擴展）
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import math

BASE_DIR = Path("c:/Users/mike2/OneDrive/Code/F1-data-analyze")


@dataclass
class TeamPerformance:
    """車隊表現統計"""
    wins: int = 0
    poles: int = 0
    podiums: int = 0  # 前三名
    top5_finishes: int = 0
    total_races: int = 0
    total_points: float = 0  # 積分 (P1=25, P2=18, ...)
    
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
    def avg_points_per_race(self) -> float:
        return self.total_points / self.total_races if self.total_races > 0 else 0


# F1 積分系統
POINTS_SYSTEM = {
    1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
    6: 8, 7: 6, 8: 4, 9: 2, 10: 1
}


class DynamicTeamRating:
    """
    動態車隊評級計算器
    
    評級計算公式:
    rating = (win_rate × 4) + (pole_rate × 2) + (podium_rate × 2) + (normalized_points × 2)
    
    範圍: 1-10
    """
    
    def __init__(self, 
                 base_years: List[int] = [2023, 2024],
                 rolling_weight: float = 0.7,
                 min_rating: float = 1.0,
                 max_rating: float = 10.0):
        """
        初始化
        
        Args:
            base_years: 基準年份列表（用於計算初始評級）
            rolling_weight: 滾動更新時新數據的權重 (0-1)
            min_rating: 最低評級
            max_rating: 最高評級
        """
        self.base_years = base_years
        self.rolling_weight = rolling_weight
        self.min_rating = min_rating
        self.max_rating = max_rating
        
        # 車隊表現數據
        self.base_performance: Dict[str, TeamPerformance] = {}  # 基準年份
        self.current_performance: Dict[str, TeamPerformance] = {}  # 當前賽季
        
        # 車隊評級
        self.base_ratings: Dict[str, float] = {}
        self.current_ratings: Dict[str, float] = {}
        
        # 車手到車隊映射
        self.driver_teams: Dict[str, str] = {}
        
        # 車隊名稱標準化
        self.team_aliases = {
            "Red Bull": "Red Bull Racing",
            "RB": "Racing Bulls",
            "AlphaTauri": "Racing Bulls",
            "Sauber": "Kick Sauber",
            "Alfa Romeo": "Kick Sauber",
            "Haas": "Haas F1 Team",
        }
    
    def _normalize_team_name(self, team: str) -> str:
        """標準化車隊名稱"""
        return self.team_aliases.get(team, team)
    
    def load_historical_data(self):
        """載入 2023-2024 歷史數據"""
        # 從 f1_historical_data.py 導入
        try:
            from f1_historical_data import F1_2023_RESULTS, F1_2024_RESULTS, DRIVER_TEAMS
        except ImportError:
            # 直接讀取 JSON
            json_file = BASE_DIR / "json/historical_data/f1_2023_2024_training_data.json"
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._process_training_json(data)
                return
            else:
                print("警告: 找不到歷史數據檔案")
                return
        
        # 處理 2023 數據
        self._process_season_results(F1_2023_RESULTS, DRIVER_TEAMS, "base")
        
        # 處理 2024 數據
        self._process_season_results(F1_2024_RESULTS, DRIVER_TEAMS, "base")
        
        # 計算基準評級
        self._calculate_ratings("base")
        
        print(f"已載入 {2023}-{2024} 基準數據")
        self._print_ratings("base")
    
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
            
            # 每場比賽只計算一次車隊參賽
            team_race_key = f"{race_key}_{team}"
            if team_race_key not in races_processed:
                performance[team].total_races += 1
                races_processed.add(team_race_key)
            
            # 統計表現
            if is_winner:
                performance[team].wins += 1
            if q_pos == 1:
                performance[team].poles += 1
            if q_pos <= 3:
                performance[team].podiums += 1
            if q_pos <= 5:
                performance[team].top5_finishes += 1
            
            # 積分（使用排位賽位置作為近似）
            points = POINTS_SYSTEM.get(q_pos, 0)
            performance[team].total_points += points
        
        self.base_performance = dict(performance)
        self._calculate_ratings("base")
        
        print(f"已從 JSON 載入基準數據")
        self._print_ratings("base")
    
    def _process_season_results(self, results: list, driver_teams: dict, mode: str):
        """處理單賽季結果"""
        perf_dict = self.base_performance if mode == "base" else self.current_performance
        
        for race in results:
            pole = race.get("pole")
            winner = race.get("winner")
            r_top5 = race.get("r_top5", [])
            
            # 記錄車隊表現
            teams_in_race = set()
            
            for pos, driver in enumerate(r_top5, 1):
                team = self._normalize_team_name(driver_teams.get(driver, "Unknown"))
                self.driver_teams[driver] = team
                
                if team not in perf_dict:
                    perf_dict[team] = TeamPerformance()
                
                # 每場比賽每車隊只計算一次參賽
                if team not in teams_in_race:
                    perf_dict[team].total_races += 1
                    teams_in_race.add(team)
                
                # 統計
                if driver == winner:
                    perf_dict[team].wins += 1
                if driver == pole:
                    perf_dict[team].poles += 1
                if pos <= 3:
                    perf_dict[team].podiums += 1
                if pos <= 5:
                    perf_dict[team].top5_finishes += 1
                
                points = POINTS_SYSTEM.get(pos, 0)
                perf_dict[team].total_points += points
    
    def load_2025_results(self, up_to_round: Optional[int] = None):
        """
        載入 2025 賽季結果
        
        Args:
            up_to_round: 只載入到第 N 輪（用於模擬漸進更新）
        """
        try:
            from f1_2025_results import F1_2025_RESULTS, DRIVER_TEAMS_2025
        except ImportError:
            json_file = BASE_DIR / "json/historical_data/f1_2025_results.json"
            if json_file.exists():
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                F1_2025_RESULTS = data.get("races", [])
                DRIVER_TEAMS_2025 = data.get("driver_teams", {})
            else:
                print("警告: 找不到 2025 結果檔案")
                return
        
        # 重置當前表現
        self.current_performance = {}
        
        # 過濾到指定輪次
        results = F1_2025_RESULTS
        if up_to_round is not None:
            results = [r for r in results if r.get("round", 0) <= up_to_round]
        
        # 處理結果
        self._process_season_results(results, DRIVER_TEAMS_2025, "current")
        
        # 更新車手車隊映射
        self.driver_teams.update(DRIVER_TEAMS_2025)
        
        # 計算當前評級（結合基準 + 當前）
        self._calculate_combined_ratings()
        
        print(f"已載入 2025 賽季 {len(results)} 場比賽結果")
        self._print_ratings("current")
    
    def _calculate_ratings(self, mode: str):
        """計算評級"""
        perf_dict = self.base_performance if mode == "base" else self.current_performance
        rating_dict = self.base_ratings if mode == "base" else self.current_ratings
        
        if not perf_dict:
            return
        
        # 找出最大積分（用於標準化）
        max_points = max(p.avg_points_per_race for p in perf_dict.values()) or 1
        
        for team, perf in perf_dict.items():
            # 評級公式
            # win_rate (0-1) × 4 = 0-4 分
            # pole_rate (0-1) × 2 = 0-2 分
            # podium_rate (0-1) × 2 = 0-2 分
            # normalized_points (0-1) × 2 = 0-2 分
            # 總計: 0-10 分
            
            normalized_points = perf.avg_points_per_race / max_points if max_points > 0 else 0
            
            raw_rating = (
                perf.win_rate * 4 +
                perf.pole_rate * 2 +
                perf.podium_rate * 2 +
                normalized_points * 2
            )
            
            # 限制範圍
            rating = max(self.min_rating, min(self.max_rating, raw_rating))
            rating_dict[team] = round(rating, 2)
    
    def _calculate_combined_ratings(self):
        """計算結合評級（基準 + 當前賽季）"""
        # 首先確保基準評級存在
        if not self.base_ratings:
            self._calculate_ratings("base")
        
        # 計算當前賽季的純評級
        self._calculate_ratings("current")
        
        # 合併所有車隊
        all_teams = set(self.base_ratings.keys()) | set(self.current_ratings.keys())
        
        for team in all_teams:
            base_rating = self.base_ratings.get(team, 5.0)  # 默認 5
            current_rating = self.current_ratings.get(team, base_rating)
            
            # 加權平均
            # rolling_weight 用於當前賽季，(1 - rolling_weight) 用於基準
            if team in self.current_performance and self.current_performance[team].total_races > 0:
                # 根據當前賽季比賽數調整權重
                races = self.current_performance[team].total_races
                # 比賽越多，當前賽季權重越高（最高 rolling_weight）
                adjusted_weight = min(self.rolling_weight, races / 10)
                combined = base_rating * (1 - adjusted_weight) + current_rating * adjusted_weight
            else:
                combined = base_rating
            
            self.current_ratings[team] = round(combined, 2)
    
    def _print_ratings(self, mode: str):
        """打印評級"""
        rating_dict = self.base_ratings if mode == "base" else self.current_ratings
        perf_dict = self.base_performance if mode == "base" else self.current_performance
        
        print(f"\n{'='*50}")
        print(f"車隊評級 ({'基準' if mode == 'base' else '當前'})")
        print(f"{'='*50}")
        
        sorted_teams = sorted(rating_dict.items(), key=lambda x: x[1], reverse=True)
        for team, rating in sorted_teams:
            perf = perf_dict.get(team, TeamPerformance())
            print(f"  {team:20} | 評級: {rating:5.2f} | "
                  f"勝: {perf.wins:2d} | 桿: {perf.poles:2d} | "
                  f"勝率: {perf.win_rate*100:5.1f}%")
    
    def get_team_rating(self, team: str) -> float:
        """獲取車隊評級"""
        team = self._normalize_team_name(team)
        
        # 優先使用當前評級
        if team in self.current_ratings:
            return self.current_ratings[team]
        
        # 其次使用基準評級
        if team in self.base_ratings:
            return self.base_ratings[team]
        
        # 默認評級
        return 5.0
    
    def get_driver_team_rating(self, driver_code: str) -> Tuple[str, float]:
        """獲取車手的車隊和評級"""
        team = self.driver_teams.get(driver_code, "Unknown")
        rating = self.get_team_rating(team)
        return team, rating
    
    def get_all_ratings(self) -> Dict[str, float]:
        """獲取所有車隊評級"""
        # 合併基準和當前
        all_ratings = dict(self.base_ratings)
        all_ratings.update(self.current_ratings)
        return all_ratings
    
    def update_with_race_result(self, 
                                 race_name: str,
                                 pole: str,
                                 winner: str,
                                 top5: List[str],
                                 driver_teams: Dict[str, str]):
        """
        單場比賽後更新評級
        
        Args:
            race_name: 比賽名稱
            pole: 桿位車手
            winner: 冠軍車手
            top5: 前五名車手
            driver_teams: 車手到車隊映射
        """
        # 更新車手車隊映射
        self.driver_teams.update(driver_teams)
        
        # 記錄車隊表現
        teams_in_race = set()
        
        for pos, driver in enumerate(top5, 1):
            team = self._normalize_team_name(driver_teams.get(driver, "Unknown"))
            
            if team not in self.current_performance:
                self.current_performance[team] = TeamPerformance()
            
            perf = self.current_performance[team]
            
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
            
            points = POINTS_SYSTEM.get(pos, 0)
            perf.total_points += points
        
        # 重新計算評級
        self._calculate_combined_ratings()
        
        print(f"\n已更新: {race_name} | 冠軍: {winner}")
        self._print_ratings("current")
    
    def export_ratings(self, output_path: Optional[Path] = None) -> dict:
        """導出評級到 JSON"""
        data = {
            "base_ratings": self.base_ratings,
            "current_ratings": self.current_ratings,
            "base_performance": {
                team: {
                    "wins": p.wins,
                    "poles": p.poles,
                    "podiums": p.podiums,
                    "total_races": p.total_races,
                    "win_rate": p.win_rate,
                    "pole_rate": p.pole_rate
                }
                for team, p in self.base_performance.items()
            },
            "current_performance": {
                team: {
                    "wins": p.wins,
                    "poles": p.poles,
                    "podiums": p.podiums,
                    "total_races": p.total_races,
                    "win_rate": p.win_rate,
                    "pole_rate": p.pole_rate
                }
                for team, p in self.current_performance.items()
            },
            "driver_teams": self.driver_teams
        }
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"已導出: {output_path}")
        
        return data


# 全局實例
_rating_system: Optional[DynamicTeamRating] = None


def get_rating_system() -> DynamicTeamRating:
    """獲取評級系統單例"""
    global _rating_system
    if _rating_system is None:
        _rating_system = DynamicTeamRating()
        _rating_system.load_historical_data()
    return _rating_system


def get_team_rating(team: str) -> float:
    """便捷函數：獲取車隊評級"""
    return get_rating_system().get_team_rating(team)


def get_driver_rating(driver_code: str) -> Tuple[str, float]:
    """便捷函數：獲取車手的車隊和評級"""
    return get_rating_system().get_driver_team_rating(driver_code)


if __name__ == "__main__":
    print("="*60)
    print("動態車隊評級系統測試")
    print("="*60)
    
    # 建立評級系統
    rating_system = DynamicTeamRating()
    
    # 載入 2023-2024 基準數據
    rating_system.load_historical_data()
    
    # 載入 2025 當前數據
    print("\n" + "="*60)
    print("載入 2025 賽季數據...")
    print("="*60)
    rating_system.load_2025_results()
    
    # 導出
    output_file = BASE_DIR / "json/historical_data/dynamic_team_ratings.json"
    rating_system.export_ratings(output_file)
    
    # 測試查詢
    print("\n" + "="*60)
    print("車手評級查詢測試")
    print("="*60)
    
    test_drivers = ["VER", "NOR", "LEC", "HAM", "PIA", "RUS"]
    for driver in test_drivers:
        team, rating = rating_system.get_driver_team_rating(driver)
        print(f"  {driver}: {team} = {rating:.2f}")
