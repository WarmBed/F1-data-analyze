"""
Team Performance Loader - 車隊/車手性能數據載入器

整合 F120 (彎道速度) + F121 (直線速度) + F125 (綜合分析) 的數據，
計算每車隊和每車手的直線/彎道速度係數。

數據來源:
- F120: FP2 彎道全圈分析 (median_speed per corner)
- F121: FP2 直線速度全圈分析 (speed_stats.median)
- F125: 車輛性能綜合分析 (corner_rank_score, straight_rank_score, best_laptime)

更新歷史:
- 2026-01-07: 添加 DriverSpeedProfile，支援車手級別精確模擬
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
import glob


@dataclass
class DriverSpeedProfile:
    """
    車手速度特性 - 用於精確模擬
    
    從 F120/F121/F125 分析獲取每個車手的真實數據：
    - F121: 直線速度 (speed_stats.median)
    - F120: 彎道速度 (各彎道的 median_speed)
    - F125: 綜合性能評分和最佳圈時
    
    更新 (2026-01-07): 添加真實直線/彎道速度 (km/h)
    """
    driver: str
    team: str
    
    # 核心速度係數 (相對於最快車手)
    # 1.0 = 最快車手, <1.0 = 較慢
    speed_factor: float = 1.0
    
    # 分項係數
    straight_speed_factor: float = 1.0  # 直線速度係數
    corner_speed_factor: float = 1.0    # 彎道速度係數
    
    # 原始數據 (從 F125 載入)
    best_laptime: float = 0.0           # FP2 最快圈時 (秒)
    corner_rank_score: float = 10.0     # 彎道排名分 (1-20, 越高越快)
    straight_rank_score: float = 10.0   # 直線排名分 (1-20, 越高越快)
    
    # 真實速度數據 (來自 F120/F121)
    straight_speed_kmh: float = 0.0     # 主直道速度中位數 (km/h) - F121
    low_speed_corner_kmh: float = 0.0   # 低速彎速度 (km/h) - F120
    mid_speed_corner_kmh: float = 0.0   # 中速彎速度 (km/h) - F120
    high_speed_corner_kmh: float = 0.0  # 高速彎速度 (km/h) - F120
    avg_corner_speed_kmh: float = 0.0   # 平均彎道速度 (km/h) - F120
    
    # 圈時差異
    delta_to_fastest: float = 0.0       # 與最快車手的圈時差 (秒)
    
    def __repr__(self):
        return f"DriverSpeedProfile({self.driver}, factor={self.speed_factor:.4f}, lap={self.best_laptime:.3f}s, straight={self.straight_speed_kmh:.0f}km/h)"


@dataclass
class TeamSpeedProfile:
    """車隊速度特性"""
    team: str
    straight_speed_factor: float = 1.0  # 直線速度係數 (相對於平均)
    corner_speed_factor: float = 1.0    # 彎道速度係數 (相對於平均)
    overall_factor: float = 1.0         # 綜合速度係數
    
    # 原始數據
    straight_speed_median: float = 0.0  # 直線速度中位數 (km/h)
    corner_speed_median: float = 0.0    # 彎道速度中位數 (km/h)
    straight_rank: float = 0.0          # F125 直線排名分
    corner_rank: float = 0.0            # F125 彎道排名分
    
    drivers: List[str] = field(default_factory=list)  # 車隊車手


class TeamPerformanceLoader:
    """
    車隊/車手性能數據載入器
    
    從 F120/F121/F125 JSON 文件載入車隊和車手性能數據，
    計算直線/彎道速度係數供 PositionTracker 使用。
    
    更新 (2026-01-07): 支援車手級別的精確速度係數
    """
    
    def __init__(self, json_dir: str = "json"):
        """
        初始化載入器
        
        Args:
            json_dir: JSON 檔案目錄
        """
        self.json_dir = Path(json_dir)
        self.team_profiles: Dict[str, TeamSpeedProfile] = {}
        self.driver_profiles: Dict[str, DriverSpeedProfile] = {}  # 車手級別配置
        
        # 最快圈時 (用於計算相對係數)
        self.fastest_laptime: float = 0.0
        self.fastest_driver: str = ""
        
        # 預設係數 (基於歷史表現，當無數據時使用) - 將被真實數據覆蓋
        self.default_factors = {
            "McLaren": {"straight": 1.010, "corner": 1.012},
            "Ferrari": {"straight": 1.008, "corner": 1.010},
            "Red Bull Racing": {"straight": 1.012, "corner": 1.006},
            "Mercedes": {"straight": 1.006, "corner": 1.008},
            "Aston Martin": {"straight": 1.004, "corner": 1.002},
            "Racing Bulls": {"straight": 1.000, "corner": 1.000},
            "Alpine": {"straight": 0.998, "corner": 0.998},
            "Williams": {"straight": 1.002, "corner": 0.994},
            "Haas F1 Team": {"straight": 0.996, "corner": 0.996},
            "Kick Sauber": {"straight": 0.994, "corner": 0.992},
        }
        
    def load_for_race(self, year: int, race: str, session: str = "FP2") -> Dict[str, TeamSpeedProfile]:
        """
        載入特定賽事的車隊和車手性能數據
        
        數據載入順序:
        1. F125 (車輛性能綜合分析) - 建立 driver_profiles 基礎結構
        2. F121 (直線速度) - 填充 straight_speed_kmh
        3. F120 (彎道速度) - 填充 low/mid/high_speed_corner_kmh
        
        Args:
            year: 年份
            race: 賽事名稱
            session: 時段 (預設 FP2)
            
        Returns:
            車隊性能字典 {team_name: TeamSpeedProfile}
            
        Side effects:
            同時填充 self.driver_profiles (車手級別數據)
        """
        self.team_profiles = {}
        self.driver_profiles = {}
        self.fastest_laptime = 0.0
        self.fastest_driver = ""
        
        # Step 1: 載入 F125 建立基礎 driver_profiles
        f125_loaded = self._load_f125(year, race, session)
        
        if f125_loaded:
            # Step 2: 載入 F121 填充直線速度
            self._load_f121(year, race, session)
            
            # Step 3: 載入 F120 填充彎道速度
            self._load_f120(year, race, session)
        else:
            # 無 F125 時嘗試單獨載入 F120 + F121 (需要其他方式建立 driver_profiles)
            self._load_f120(year, race, session)
            self._load_f121(year, race, session)
            
        # 計算速度係數 (車隊和車手級別)
        self._calculate_speed_factors()
        self._calculate_driver_speed_factors()
        
        # 如果沒有載入任何數據，使用預設值
        if not self.team_profiles:
            print("[TeamPerformanceLoader] 無法載入數據，使用預設係數")
            self._use_default_factors()
            
        # 打印載入摘要
        if self.driver_profiles:
            print(f"[TeamPerformanceLoader] 載入 {len(self.driver_profiles)} 位車手速度配置")
            print(f"[TeamPerformanceLoader] 最快車手: {self.fastest_driver} ({self.fastest_laptime:.3f}s)")
            
        return self.team_profiles
    
    # 賽道名稱到比賽名稱的映射
    TRACK_TO_RACE_MAP = {
        "Yas Marina": "Abu Dhabi",
        "Yas Island": "Abu Dhabi",
        "Bahrain International Circuit": "Bahrain",
        "Jeddah Corniche Circuit": "Saudi Arabia",
        "Albert Park": "Australia",
        "Suzuka": "Japan",
        "Shanghai International Circuit": "China",
        "Miami International Autodrome": "Miami",
        "Circuit de Monaco": "Monaco",
        "Circuit Gilles Villeneuve": "Canada",
        "Circuit de Barcelona-Catalunya": "Spain",
        "Red Bull Ring": "Austria",
        "Silverstone": "Great Britain",
        "Hungaroring": "Hungary",
        "Spa-Francorchamps": "Belgium",
        "Circuit Zandvoort": "Netherlands",
        "Monza": "Italy",
        "Baku City Circuit": "Azerbaijan",
        "Marina Bay Street Circuit": "Singapore",
        "Circuit of the Americas": "United States",
        "Autodromo Hermanos Rodriguez": "Mexico",
        "Interlagos": "Brazil",
        "Las Vegas Street Circuit": "Las Vegas",
        "Lusail International Circuit": "Qatar",
        "Imola": "Emilia Romagna",
    }
    
    def _load_f125(self, year: int, race: str, session: str) -> bool:
        """載入 F125 車輛性能綜合分析 (車隊+車手)"""
        # 嘗試將賽道名稱轉換為比賽名稱
        race_name = self.TRACK_TO_RACE_MAP.get(race, race)
        if race_name != race:
            print(f"[TeamPerformanceLoader] 賽道名稱轉換: {race} -> {race_name}")
        
        pattern = f"vehicle_performance_analysis_{year}_{race_name}*.json"
        files = list(self.json_dir.glob(pattern))
        
        if not files:
            # 嘗試模糊匹配
            pattern = f"vehicle_performance_analysis_{year}_*.json"
            files = [f for f in self.json_dir.glob(pattern) if race_name.lower() in f.name.lower()]
            
        if not files:
            # 嘗試原始 race 名稱
            pattern = f"vehicle_performance_analysis_{year}_{race}*.json"
            files = list(self.json_dir.glob(pattern))
            
        if not files:
            print(f"[TeamPerformanceLoader] 找不到 F125: vehicle_performance_analysis_{year}_{race_name}*.json")
            return False
            
        try:
            with open(files[0], 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            driver_results = data.get('driver_results', [])
            if not driver_results:
                print(f"[TeamPerformanceLoader] F125 無 driver_results")
                return False
            
            # ========== 載入車手級別數據 ==========
            all_laptimes = []
            for dr in driver_results:
                driver = dr.get('driver', '')
                team = dr.get('team', 'Unknown')
                metrics = dr.get('metrics', {})
                
                best_laptime = metrics.get('best_laptime')
                corner_rank = metrics.get('corner_rank_score', 10.0)
                straight_rank = metrics.get('straight_rank_score', 10.0)
                
                if best_laptime and best_laptime > 0:
                    all_laptimes.append((driver, best_laptime))
                    
                    # 創建 DriverSpeedProfile
                    self.driver_profiles[driver] = DriverSpeedProfile(
                        driver=driver,
                        team=team,
                        best_laptime=best_laptime,
                        corner_rank_score=corner_rank,
                        straight_rank_score=straight_rank
                    )
            
            # 找出最快圈時
            if all_laptimes:
                all_laptimes.sort(key=lambda x: x[1])
                self.fastest_driver = all_laptimes[0][0]
                self.fastest_laptime = all_laptimes[0][1]
                
                # 計算每個車手相對於最快車手的圈時差
                for driver, laptime in all_laptimes:
                    if driver in self.driver_profiles:
                        self.driver_profiles[driver].delta_to_fastest = laptime - self.fastest_laptime
                
            # ========== 載入車隊級別數據 ==========
            team_data: Dict[str, Dict] = {}
            for dr in driver_results:
                team = dr.get('team', 'Unknown')
                driver = dr.get('driver', '')
                metrics = dr.get('metrics', {})
                
                if team not in team_data:
                    team_data[team] = {
                        'corner_ranks': [],
                        'straight_ranks': [],
                        'drivers': [],
                        'laptimes': []
                    }
                    
                team_data[team]['drivers'].append(driver)
                if metrics.get('corner_rank_score'):
                    team_data[team]['corner_ranks'].append(metrics['corner_rank_score'])
                if metrics.get('straight_rank_score'):
                    team_data[team]['straight_ranks'].append(metrics['straight_rank_score'])
                if metrics.get('best_laptime'):
                    team_data[team]['laptimes'].append(metrics['best_laptime'])
                    
            # 創建 TeamSpeedProfile
            for team, td in team_data.items():
                profile = TeamSpeedProfile(
                    team=team,
                    drivers=td['drivers']
                )
                
                if td['corner_ranks']:
                    profile.corner_rank = sum(td['corner_ranks']) / len(td['corner_ranks'])
                if td['straight_ranks']:
                    profile.straight_rank = sum(td['straight_ranks']) / len(td['straight_ranks'])
                    
                self.team_profiles[team] = profile
                
            print(f"[TeamPerformanceLoader] 從 F125 載入 {len(self.team_profiles)} 個車隊, {len(self.driver_profiles)} 個車手")
            return True
            
        except Exception as e:
            print(f"[TeamPerformanceLoader] 載入 F125 失敗: {e}")
            return False
            
    def _load_f120(self, year: int, race: str, session: str) -> bool:
        """載入 F120 彎道速度分析 - 提取每位車手的彎道速度"""
        pattern = f"F120_corner_all_laps_analysis_{year}_{race}_{session}*.json"
        files = list(self.json_dir.glob(pattern))
        
        if not files:
            print(f"[TeamPerformanceLoader] 找不到 F120: {pattern}")
            return False
            
        try:
            with open(files[0], 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 獲取選定的彎道類型
            selected_corners = data.get('selected_corners', {})
            low_speed_corner = selected_corners.get('low_speed', {})
            mid_speed_corner = selected_corners.get('mid_speed', {})
            high_speed_corner = selected_corners.get('high_speed', {})
            
            # 獲取彎道編號 (用於匹配車手數據)
            low_corner_key = f"low_speed_corner_{low_speed_corner.get('corner_number', 0)}"
            mid_corner_key = f"mid_speed_corner_{mid_speed_corner.get('corner_number', 0)}"
            high_corner_key = f"high_speed_corner_{high_speed_corner.get('corner_number', 0)}"
            
            drivers = data.get('mode_a_unified', {}).get('drivers', [])
            if not drivers:
                return False
            
            updated_count = 0
            for driver_data in drivers:
                driver_code = driver_data.get('driver', '')
                corners = driver_data.get('corners', {})
                
                # 獲取該車手在各類型彎道的速度
                low_speed = corners.get(low_corner_key, {}).get('median_speed', 0)
                mid_speed = corners.get(mid_corner_key, {}).get('median_speed', 0)
                high_speed = corners.get(high_corner_key, {}).get('median_speed', 0)
                
                # 更新 DriverSpeedProfile
                if driver_code in self.driver_profiles:
                    profile = self.driver_profiles[driver_code]
                    profile.low_speed_corner_kmh = low_speed
                    profile.mid_speed_corner_kmh = mid_speed
                    profile.high_speed_corner_kmh = high_speed
                    # 計算平均彎道速度
                    valid_speeds = [s for s in [low_speed, mid_speed, high_speed] if s > 0]
                    if valid_speeds:
                        profile.avg_corner_speed_kmh = sum(valid_speeds) / len(valid_speeds)
                    updated_count += 1
            
            print(f"[TeamPerformanceLoader] F120 載入 {len(drivers)} 個車手彎道速度 (更新 {updated_count} 個配置)")
            return True
            
        except Exception as e:
            print(f"[TeamPerformanceLoader] 載入 F120 失敗: {e}")
            return False
            
    def _load_f121(self, year: int, race: str, session: str) -> bool:
        """載入 F121 直線速度分析 - 提取每位車手的主直道速度"""
        # 優先使用正賽或指定 session 的數據，如無則嘗試 FP2
        patterns = [
            f"fp2_straight_line_all_laps_analysis_{year}_{race}_{session}*.json",
            f"all_drivers_straight_line_speed_{year}_{race}_{session}.json",
            f"fp2_straight_line_all_laps_analysis_{year}_{race}*.json",  # 回退到 FP2
        ]
        
        files = []
        for pattern in patterns:
            files = list(self.json_dir.glob(pattern))
            if files:
                break
        
        if not files:
            print(f"[TeamPerformanceLoader] 找不到 F121: 嘗試了 {patterns}")
            return False
            
        try:
            with open(files[0], 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # F121 直接使用 drivers 陣列 (不是 mode_a_unified)
            drivers = data.get('drivers', [])
            if not drivers:
                return False
            
            updated_count = 0
            for driver_data in drivers:
                driver_code = driver_data.get('driver', '')
                speed_stats = driver_data.get('speed_stats', {})
                
                # 獲取主直道速度中位數
                straight_speed = speed_stats.get('median', 0)
                
                # 更新 DriverSpeedProfile
                if driver_code in self.driver_profiles:
                    self.driver_profiles[driver_code].straight_speed_kmh = straight_speed
                    updated_count += 1
            
            print(f"[TeamPerformanceLoader] F121 載入 {len(drivers)} 個車手直線速度 (更新 {updated_count} 個配置)")
            return True
            
        except Exception as e:
            print(f"[TeamPerformanceLoader] 載入 F121 失敗: {e}")
            return False
            
    def _calculate_speed_factors(self) -> None:
        """計算速度係數 (將排名分轉換為速度係數)"""
        if not self.team_profiles:
            return
            
        # 計算平均排名分
        all_corner_ranks = [p.corner_rank for p in self.team_profiles.values() if p.corner_rank > 0]
        all_straight_ranks = [p.straight_rank for p in self.team_profiles.values() if p.straight_rank > 0]
        
        avg_corner = sum(all_corner_ranks) / len(all_corner_ranks) if all_corner_ranks else 10.5
        avg_straight = sum(all_straight_ranks) / len(all_straight_ranks) if all_straight_ranks else 10.5
        
        # 將排名分轉換為速度係數
        # 排名分越低越好 (1 = 最快)
        # 係數範圍: 0.99 ~ 1.01 (對應 ±1% 速度差)
        for team, profile in self.team_profiles.items():
            if profile.corner_rank > 0:
                # 排名分 1 → 1.01, 排名分 20 → 0.99
                corner_delta = (avg_corner - profile.corner_rank) / avg_corner * 0.02
                profile.corner_speed_factor = 1.0 + max(-0.02, min(0.02, corner_delta))
            else:
                profile.corner_speed_factor = self.default_factors.get(team, {}).get('corner', 1.0)
                
            if profile.straight_rank > 0:
                straight_delta = (avg_straight - profile.straight_rank) / avg_straight * 0.02
                profile.straight_speed_factor = 1.0 + max(-0.02, min(0.02, straight_delta))
            else:
                profile.straight_speed_factor = self.default_factors.get(team, {}).get('straight', 1.0)
                
            # 綜合係數 (直線和彎道各佔 50%)
            profile.overall_factor = (profile.straight_speed_factor + profile.corner_speed_factor) / 2
    
    def _calculate_driver_speed_factors(self) -> None:
        """
        計算車手級別的速度係數
        
        核心邏輯:
        - 最快車手 speed_factor = 1.0
        - 其他車手根據圈時差計算: factor = fastest_laptime / driver_laptime
        
        分項係數 (直線/彎道) 僅做微調:
        - 排名分用於計算直線vs彎道的相對強弱
        - 微調幅度極小 (±0.2%)，不改變圈時代表的整體速度
        
        這確保更快的車手有更高的速度係數，能準確反映圈時差異
        """
        if not self.driver_profiles or self.fastest_laptime <= 0:
            return
        
        for driver, profile in self.driver_profiles.items():
            if profile.best_laptime > 0:
                # 速度係數 = 最快圈時 / 車手圈時
                # 例如: 83.083 / 84.963 = 0.9779 (慢 2.2%)
                profile.speed_factor = self.fastest_laptime / profile.best_laptime
                
                # 直線/彎道係數: 以 speed_factor 為基準，做極微小調整
                # 排名分差異只影響 ±0.2%，確保不會大幅改變整體速度係數
                avg_rank = 10.5  # 1-20 的中間值
                
                # 計算車手自身的直線vs彎道相對強弱 (正值=該項較強)
                total_rank = profile.corner_rank_score + profile.straight_rank_score
                if total_rank > 0:
                    # 彎道佔比 - 直線佔比，用於微調
                    corner_ratio = profile.corner_rank_score / total_rank
                    straight_ratio = profile.straight_rank_score / total_rank
                    
                    # 微調範圍 ±0.2% (0.002)，根據強項微調
                    corner_adjustment = (corner_ratio - 0.5) * 0.004
                    straight_adjustment = (straight_ratio - 0.5) * 0.004
                    
                    profile.corner_speed_factor = profile.speed_factor * (1.0 + corner_adjustment)
                    profile.straight_speed_factor = profile.speed_factor * (1.0 + straight_adjustment)
                else:
                    # 無排名數據，直接使用 speed_factor
                    profile.corner_speed_factor = profile.speed_factor
                    profile.straight_speed_factor = profile.speed_factor
            else:
                profile.speed_factor = 1.0
                profile.corner_speed_factor = 1.0
                profile.straight_speed_factor = 1.0
            
    def _use_default_factors(self) -> None:
        """使用預設係數"""
        for team, factors in self.default_factors.items():
            profile = TeamSpeedProfile(
                team=team,
                straight_speed_factor=factors['straight'],
                corner_speed_factor=factors['corner'],
                overall_factor=(factors['straight'] + factors['corner']) / 2
            )
            self.team_profiles[team] = profile
            
    def get_speed_factor(self, team: str, is_corner: bool = False) -> float:
        """
        獲取車隊速度係數
        
        Args:
            team: 車隊名稱
            is_corner: 是否為彎道位置
            
        Returns:
            速度係數 (相對於 1.0)
        """
        profile = self.team_profiles.get(team)
        
        if profile:
            return profile.corner_speed_factor if is_corner else profile.straight_speed_factor
        else:
            # 查找預設值
            default = self.default_factors.get(team, {'straight': 1.0, 'corner': 1.0})
            return default['corner'] if is_corner else default['straight']
    
    def get_driver_speed_factor(self, driver: str, is_corner: bool = False) -> float:
        """
        獲取車手速度係數
        
        Args:
            driver: 車手代碼 (如 "VER", "NOR")
            is_corner: 是否為彎道位置
            
        Returns:
            速度係數 (最快車手=1.0, 其他<1.0)
        """
        profile = self.driver_profiles.get(driver)
        
        if profile:
            if is_corner:
                return profile.corner_speed_factor
            else:
                return profile.straight_speed_factor
        
        # 無車手數據時返回 1.0 (中性)
        return 1.0
    
    def get_driver_profile(self, driver: str) -> Optional[DriverSpeedProfile]:
        """獲取車手完整配置"""
        return self.driver_profiles.get(driver)
            
    def get_overall_factor(self, team: str) -> float:
        """獲取車隊綜合速度係數"""
        profile = self.team_profiles.get(team)
        if profile:
            return profile.overall_factor
        else:
            default = self.default_factors.get(team, {'straight': 1.0, 'corner': 1.0})
            return (default['straight'] + default['corner']) / 2
            
    def print_summary(self) -> None:
        """打印車隊性能摘要"""
        print("\n=== 車隊速度係數 ===")
        print(f"{'車隊':<20} {'直線係數':>10} {'彎道係數':>10} {'綜合係數':>10}")
        print("-" * 55)
        
        # 按綜合係數排序
        sorted_teams = sorted(
            self.team_profiles.items(),
            key=lambda x: x[1].overall_factor,
            reverse=True
        )
        
        for team, profile in sorted_teams:
            print(f"{team:<20} {profile.straight_speed_factor:>10.4f} "
                  f"{profile.corner_speed_factor:>10.4f} {profile.overall_factor:>10.4f}")
    
    def print_driver_summary(self) -> None:
        """打印車手性能摘要 (包含真實速度數據)"""
        print("\n=== 車手速度係數 (基於 F125/F120/F121 數據) ===")
        print(f"{'車手':>4} | {'車隊':<15} | {'圈時':>8} | {'直線':>6} | {'彎道':>6} | {'係數':>7}")
        print("-" * 70)
        
        # 按圈時排序
        sorted_drivers = sorted(
            self.driver_profiles.items(),
            key=lambda x: x[1].best_laptime if x[1].best_laptime > 0 else 999
        )
        
        for driver, profile in sorted_drivers:
            straight = f"{profile.straight_speed_kmh:.0f}" if profile.straight_speed_kmh > 0 else "-"
            corner = f"{profile.avg_corner_speed_kmh:.0f}" if profile.avg_corner_speed_kmh > 0 else "-"
            print(f"{driver:>4} | {profile.team:<15} | {profile.best_laptime:>8.3f} | "
                  f"{straight:>6} | {corner:>6} | {profile.speed_factor:>7.4f}")


# 單例實例
_loader_instance: Optional[TeamPerformanceLoader] = None


def get_team_performance_loader(json_dir: str = "json") -> TeamPerformanceLoader:
    """獲取 TeamPerformanceLoader 單例"""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = TeamPerformanceLoader(json_dir)
    return _loader_instance


# 測試代碼
if __name__ == "__main__":
    loader = TeamPerformanceLoader("json")
    
    # 測試載入
    profiles = loader.load_for_race(2025, "Abu Dhabi", "FP2")
    
    # 打印摘要
    loader.print_summary()
    
    # 測試獲取係數
    print("\n=== 測試獲取係數 ===")
    for team in ["McLaren", "Ferrari", "Red Bull Racing", "Mercedes", "Kick Sauber"]:
        straight = loader.get_speed_factor(team, is_corner=False)
        corner = loader.get_speed_factor(team, is_corner=True)
        print(f"{team}: 直線={straight:.4f}, 彎道={corner:.4f}")
