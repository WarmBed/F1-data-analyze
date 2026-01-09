"""
Track Configuration - 賽道配置管理

管理賽道的基本資訊，包含：
- 賽道長度
- DRS 區域位置
- 速度曲線
- 超車難度係數
"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any


@dataclass
class DRSZone:
    """DRS 區域配置"""
    zone_id: int
    detection_point_m: float  # 偵測點位置 (距離起跑線)
    activation_point_m: float  # 啟動點位置
    end_point_m: float  # 結束點位置
    length_m: float = 0.0  # 區域長度 (自動計算)
    
    def __post_init__(self):
        self.length_m = self.end_point_m - self.activation_point_m
        if self.length_m < 0:  # 跨越起終點
            pass  # 需要額外處理


@dataclass
class SpeedCurvePoint:
    """速度曲線上的一個點"""
    distance_m: float
    avg_speed_kmh: float
    min_speed_kmh: float = 0.0
    max_speed_kmh: float = 0.0


@dataclass
class TrackConfig:
    """
    賽道完整配置
    
    包含賽道的所有模擬所需參數
    """
    track_name: str
    track_length_m: float
    difficulty_coefficient: float = 0.5  # 0=容易超車, 1=困難超車
    
    # DRS 區域 (大多數賽道有 2-3 個)
    drs_zones: List[DRSZone] = field(default_factory=list)
    
    # 速度曲線 (每 50m 一個點)
    speed_curve: List[SpeedCurvePoint] = field(default_factory=list)
    
    # 統計資料 (來自 F136)
    overtake_rate_per_lap: float = 0.0
    avg_overtakes_per_race: float = 0.0
    sample_races: int = 0
    
    # Pit Lane 資訊 (來自 F142)
    pit_entry_m: float = 0.0
    pit_exit_m: float = 0.0
    pit_lane_time_loss_s: float = 20.0  # 預設進站損失時間
    
    # SC/VSC 機率 (來自 sc_probability_by_track.json)
    sc_probability_per_lap_pct: float = 2.5  # SC 每圈機率 (%)
    vsc_probability_per_lap_pct: float = 2.0  # VSC 每圈機率 (%)
    avg_sc_per_race: float = 1.0  # 平均每場比賽 SC 次數
    
    # 額外參數
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_speed_at_position(self, position_m: float) -> float:
        """
        獲取指定位置的平均速度
        
        使用線性插值在速度曲線點之間計算
        """
        if not self.speed_curve:
            return 250.0  # 預設速度
            
        # 確保位置在賽道範圍內
        position_m = position_m % self.track_length_m
        
        # 找到最近的兩個點
        prev_point = self.speed_curve[-1]
        for point in self.speed_curve:
            if point.distance_m >= position_m:
                # 線性插值
                if point.distance_m == prev_point.distance_m:
                    return point.avg_speed_kmh
                ratio = (position_m - prev_point.distance_m) / (point.distance_m - prev_point.distance_m)
                return prev_point.avg_speed_kmh + ratio * (point.avg_speed_kmh - prev_point.avg_speed_kmh)
            prev_point = point
            
        return self.speed_curve[-1].avg_speed_kmh
        
    def is_in_drs_zone(self, position_m: float) -> bool:
        """檢查指定位置是否在 DRS 區域內"""
        for zone in self.drs_zones:
            if zone.activation_point_m <= position_m <= zone.end_point_m:
                return True
            # 處理跨越起終點的情況
            if zone.end_point_m < zone.activation_point_m:
                if position_m >= zone.activation_point_m or position_m <= zone.end_point_m:
                    return True
        return False
    
    def is_in_corner(self, position_m: float, speed_threshold_kmh: float = 200.0) -> bool:
        """
        檢查指定位置是否在彎道區域
        
        使用速度曲線判斷：低於閾值速度的區域視為彎道
        
        Args:
            position_m: 賽道位置 (公尺)
            speed_threshold_kmh: 速度閾值 (km/h)，低於此速度視為彎道
            
        Returns:
            True 如果位置在彎道，False 如果在直線
        """
        if not self.speed_curve:
            return False  # 無速度曲線，預設為直線
            
        speed = self.get_speed_at_position(position_m)
        return speed < speed_threshold_kmh
    
    def get_corner_type(self, position_m: float) -> str:
        """
        判斷當前位置的彎道類型
        
        基於速度曲線區分：
        - "straight": 速度 >= 250 km/h (直線)
        - "high": 200-250 km/h (高速彎)
        - "mid": 150-200 km/h (中速彎)  
        - "low": < 150 km/h (低速彎)
        
        Args:
            position_m: 賽道位置 (公尺)
            
        Returns:
            彎道類型字串: "straight", "high", "mid", "low"
        """
        if not self.speed_curve:
            return "straight"  # 無速度曲線，預設為直線
            
        speed = self.get_speed_at_position(position_m)
        
        if speed >= 250:
            return "straight"
        elif speed >= 200:
            return "high"
        elif speed >= 150:
            return "mid"
        else:
            return "low"
        
    def get_drs_detection_distance(self, position_m: float) -> Optional[float]:
        """
        如果在 DRS 區域內，返回距離 detection point 的距離
        返回 None 如果不在任何 DRS 區域
        """
        for zone in self.drs_zones:
            if zone.activation_point_m <= position_m <= zone.end_point_m:
                return position_m - zone.detection_point_m
        return None


class TrackConfigManager:
    """
    賽道配置管理器
    
    負責載入和管理所有賽道的配置
    """
    
    # 名稱映射 (用於處理不同格式的賽道名稱)
    TRACK_NAME_ALIASES = {
        "Japan": "Japanese",
        "Japanese": "Japanese",
        "Saudi Arabia": "Saudi Arabian",
        "Saudi Arabian": "Saudi Arabian",
        "Great Britain": "British",
        "British": "British",
        "United States": "United States",
        "USA": "United States",
        "Abu Dhabi": "Abu Dhabi",
        "Netherlands": "Dutch",
        "Dutch": "Dutch",
        "Mexico": "Mexico City",
        "Mexico City": "Mexico City",
        "Las Vegas": "Las Vegas",
        "Australia": "Australian",
        "Australian": "Australian",
        "China": "Chinese",
        "Chinese": "Chinese",
        "Spain": "Spanish",
        "Spanish": "Spanish",
        "Canada": "Canadian",
        "Canadian": "Canadian",
        "Austria": "Austrian",
        "Austrian": "Austrian",
        "Hungary": "Hungarian",
        "Hungarian": "Hungarian",
        "Belgium": "Belgian",
        "Belgian": "Belgian",
        "Italy": "Italian",
        "Italian": "Italian",
        "Brazil": "São Paulo",
        "São Paulo": "São Paulo",
        "Sao Paulo": "São Paulo",
        "Qatar": "Qatar",
        "Monaco": "Monaco",
        "Miami": "Miami",
        "Singapore": "Singapore",
        "Azerbaijan": "Azerbaijan",
        "Bahrain": "Bahrain",
        "Emilia Romagna": "Emilia Romagna",
        "Imola": "Emilia Romagna",
    }
    
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent
        self.json_dir = self.base_dir / "json"
        
        # 緩存
        self._tracks: Dict[str, TrackConfig] = {}
        self._track_difficulty: Dict[str, float] = {}
        self._pit_team_stats: Dict[str, Dict[str, Dict[str, Any]]] = {}  # {track: {team: stats}}
        self._pit_lane_time_loss: Dict[str, float] = {}
        self._sc_probability: Dict[str, Dict[str, float]] = {}
        
        # 載入各類數據
        self._load_track_difficulty()
        self._load_pit_lane_time_loss()
        self._load_sc_probability()
        
    def _normalize_track_name(self, track_name: str) -> str:
        """正規化賽道名稱"""
        return self.TRACK_NAME_ALIASES.get(track_name, track_name)
        
    def _load_track_difficulty(self) -> None:
        """從 F136 輸出載入賽道難度係數"""
        difficulty_file = self.json_dir / "track_overtake_difficulty.json"
        if difficulty_file.exists():
            try:
                with open(difficulty_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                tracks = data.get("tracks", {})
                for track_name, info in tracks.items():
                    self._track_difficulty[track_name] = info.get("difficulty_coefficient", 0.5)
                    
                print(f"[TrackConfigManager] 載入 {len(self._track_difficulty)} 個賽道難度係數")
            except Exception as e:
                print(f"[TrackConfigManager] 載入賽道難度失敗: {e}")
    
    def _load_pit_lane_time_loss(self) -> None:
        """從 F142 輸出載入 pit lane 時間損失（包含車隊細分統計）"""
        pit_file = self.json_dir / "pit_lane_time_loss_all_tracks.json"
        if pit_file.exists():
            try:
                with open(pit_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                tracks = data.get("tracks", {})
                team_stats_count = 0
                for track_name, info in tracks.items():
                    # 使用 avg_pit_loss_s 或 median_pit_loss_s
                    avg_loss = info.get("avg_pit_loss_s", 22.0)
                    self._pit_lane_time_loss[track_name] = avg_loss
                    
                    # 載入車隊細分統計
                    by_team = info.get("by_team")
                    if by_team:
                        self._pit_team_stats[track_name] = by_team
                        team_stats_count += 1
                
                print(f"[TrackConfigManager] 載入 {len(self._pit_lane_time_loss)} 個賽道 pit 損失時間 ({team_stats_count} 含車隊統計)")
            except Exception as e:
                print(f"[TrackConfigManager] 載入 pit 損失時間失敗: {e}")
    
    def _load_sc_probability(self) -> None:
        """從 sc_probability_by_track.json 載入 SC/VSC 機率"""
        sc_file = self.json_dir / "sc_probability_by_track.json"
        if sc_file.exists():
            try:
                with open(sc_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                tracks = data.get("tracks", {})
                for track_name, info in tracks.items():
                    self._sc_probability[track_name] = {
                        "sc_per_lap_pct": info.get("sc_probability_per_lap_pct", 2.5),
                        "vsc_per_lap_pct": info.get("vsc_probability_per_lap_pct", 2.0),
                        "avg_sc_per_race": info.get("avg_sc_per_race", 1.0),
                        "avg_vsc_per_race": info.get("avg_vsc_per_race", 1.0)
                    }
                
                print(f"[TrackConfigManager] 載入 {len(self._sc_probability)} 個賽道 SC/VSC 機率")
            except Exception as e:
                print(f"[TrackConfigManager] 載入 SC 機率失敗: {e}")
                
    def get_track(self, track_name: str) -> TrackConfig:
        """
        獲取賽道配置
        
        如果未緩存，會創建一個預設配置
        """
        # 使用原始名稱作為 key，但查找時使用正規化名稱
        if track_name in self._tracks:
            return self._tracks[track_name]
            
        # 創建新配置
        config = self._create_default_config(track_name)
        self._tracks[track_name] = config
        return config
        
    def _load_track_circuit_data(self, track_name: str) -> Optional[Dict]:
        """
        載入 track_circuit_data JSON 檔案
        
        這個檔案包含真實的彎道速度、DRS 區域等數據
        
        Args:
            track_name: 賽道名稱
            
        Returns:
            JSON 數據字典，如果檔案不存在則返回 None
        """
        # 嘗試多種命名格式
        name_variants = [
            track_name.replace(" ", "_"),
            track_name,
            self._normalize_track_name(track_name).replace(" ", "_"),
        ]
        
        for name in name_variants:
            filepath = self.json_dir / f"track_circuit_data_{name}.json"
            if filepath.exists():
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        print(f"[TrackConfigManager] 載入真實賽道數據: {filepath.name}")
                        return data
                except Exception as e:
                    print(f"[TrackConfigManager] 載入 {filepath.name} 失敗: {e}")
                    
        return None
    
    def _build_speed_curve_from_circuit_data(
        self, 
        circuit_data: Dict, 
        track_length: float
    ) -> List[SpeedCurvePoint]:
        """
        從 track_circuit_data 的彎道速度建立真實速度曲線
        
        Args:
            circuit_data: track_circuit_data JSON 數據
            track_length: 賽道長度 (m)
            
        Returns:
            速度曲線點列表
        """
        corners = circuit_data.get("corners", [])
        if not corners:
            return []
            
        # 建立彎道位置 → 速度的映射
        corner_speeds: Dict[float, Dict[str, float]] = {}
        for corner in corners:
            distance = corner.get("distance_m", 0)
            corner_speeds[distance] = {
                "min": corner.get("min_speed_kmh", 100),
                "avg": corner.get("avg_speed_kmh", 150),
                "max": corner.get("max_speed_kmh", 200)
            }
        
        # 建立每 50m 一個點的速度曲線
        speed_curve = []
        sorted_corners = sorted(corner_speeds.keys())
        
        for d in range(0, int(track_length), 50):
            distance = float(d)
            
            # 查找最近的彎道
            nearest_corner = None
            min_distance = float('inf')
            
            for corner_dist in sorted_corners:
                diff = abs(corner_dist - distance)
                if diff < min_distance:
                    min_distance = diff
                    nearest_corner = corner_dist
            
            if nearest_corner is not None and min_distance < 200:
                # 在彎道附近，使用彎道速度
                corner_data = corner_speeds[nearest_corner]
                avg_speed = corner_data["avg"]
                min_speed = corner_data["min"]
                max_speed = corner_data["max"]
            else:
                # 在直道區域，使用高速度
                # 從彎道數據推算直道速度
                if corners:
                    max_corner_speed = max(c.get("max_speed_kmh", 250) for c in corners)
                    avg_speed = min(max_corner_speed + 30, 320)  # 直道速度更高
                    min_speed = max_corner_speed
                    max_speed = avg_speed + 10
                else:
                    avg_speed = 280  # 預設直道速度
                    min_speed = 250
                    max_speed = 310
            
            speed_curve.append(SpeedCurvePoint(
                distance_m=distance,
                avg_speed_kmh=avg_speed,
                min_speed_kmh=min_speed,
                max_speed_kmh=max_speed
            ))
        
        print(f"[TrackConfigManager] 從彎道數據建立 {len(speed_curve)} 點速度曲線")
        return speed_curve
    
    def _build_drs_zones_from_circuit_data(self, circuit_data: Dict) -> List[DRSZone]:
        """
        從 track_circuit_data 載入真實 DRS 區域
        
        Args:
            circuit_data: track_circuit_data JSON 數據
            
        Returns:
            DRS 區域列表
        """
        drs_data = circuit_data.get("drs_zones", [])
        if not drs_data:
            return []
            
        drs_zones = []
        for zone in drs_data:
            drs_zones.append(DRSZone(
                zone_id=zone.get("zone_id", len(drs_zones) + 1),
                detection_point_m=zone.get("detection_distance_m", 0),
                activation_point_m=zone.get("activation_distance_m", 0),
                end_point_m=zone.get("end_distance_m", 0)
            ))
            
        print(f"[TrackConfigManager] 載入 {len(drs_zones)} 個真實 DRS 區域")
        return drs_zones
    
    def _build_default_speed_curve(self, length: float) -> List[SpeedCurvePoint]:
        """
        建立預設速度曲線 (當沒有真實數據時使用)
        
        注意：這是備用方案，應優先使用 track_circuit_data 的真實數據
        
        Args:
            length: 賽道長度 (m)
            
        Returns:
            速度曲線點列表
        """
        avg_speed = 230.0  # km/h 平均
        speed_curve = []
        for d in range(0, int(length), 100):
            # 添加一些速度變化 (模擬直道和彎道)
            variation = (d % 500) / 500 * 50 - 25  # -25 到 +25 km/h
            speed = avg_speed + variation
            speed_curve.append(SpeedCurvePoint(
                distance_m=d,
                avg_speed_kmh=speed,
                min_speed_kmh=speed - 20,
                max_speed_kmh=speed + 20
            ))
        print(f"[TrackConfigManager] 警告：使用預設速度曲線 (無真實數據)")
        return speed_curve
    
    def _build_default_drs_zones(self, length: float) -> List[DRSZone]:
        """
        建立預設 DRS 區域 (當沒有真實數據時使用)
        
        注意：這是備用方案，應優先使用 track_circuit_data 的真實數據
        
        Args:
            length: 賽道長度 (m)
            
        Returns:
            DRS 區域列表
        """
        print(f"[TrackConfigManager] 警告：使用預設 DRS 區域 (無真實數據)")
        return [
            DRSZone(
                zone_id=1,
                detection_point_m=length * 0.1,
                activation_point_m=length * 0.15,
                end_point_m=length * 0.35
            ),
            DRSZone(
                zone_id=2,
                detection_point_m=length * 0.6,
                activation_point_m=length * 0.65,
                end_point_m=length * 0.85
            )
        ]
        
    def _create_default_config(self, track_name: str) -> TrackConfig:
        """
        創建賽道的配置
        
        優先使用 track_circuit_data 中的真實數據，
        如果不可用則使用預設值
        """
        # 正規化名稱用於查找難度係數
        normalized_name = self._normalize_track_name(track_name)
        
        # 嘗試載入真實賽道數據
        circuit_data = self._load_track_circuit_data(track_name)
        
        # 賽道長度預設值 (常見賽道)
        TRACK_LENGTHS = {
            "Bahrain": 5412,
            "Saudi Arabia": 6174,
            "Australia": 5278,
            "Japan": 5807,
            "China": 5451,
            "Miami": 5412,
            "Monaco": 3337,
            "Canada": 4361,
            "Spain": 4657,
            "Austria": 4318,
            "Great Britain": 5891,
            "Hungary": 4381,
            "Belgium": 7004,
            "Netherlands": 4259,
            "Italy": 5793,
            "Azerbaijan": 6003,
            "Singapore": 5063,
            "United States": 5513,
            "Mexico": 4304,
            "Brazil": 4309,
            "Las Vegas": 6201,
            "Qatar": 5380,
            "Abu Dhabi": 5281,
        }
        
        # 如果有真實賽道數據，使用 JSON 中的賽道長度
        if circuit_data:
            length = circuit_data.get("track_length_m", TRACK_LENGTHS.get(track_name, 5000))
        else:
            length = TRACK_LENGTHS.get(track_name, 5000)
            
        # 使用正規化名稱查找難度係數
        difficulty = self._track_difficulty.get(normalized_name, 0.5)
        
        # 查找 pit lane 時間損失 (嘗試多種名稱格式)
        pit_loss = self._pit_lane_time_loss.get(track_name)
        if pit_loss is None:
            pit_loss = self._pit_lane_time_loss.get(normalized_name)
        if pit_loss is None:
            # 嘗試下劃線格式
            underscore_name = track_name.replace(" ", "_")
            pit_loss = self._pit_lane_time_loss.get(underscore_name)
        if pit_loss is None:
            pit_loss = 22.0  # 預設值
        
        # 查找 SC/VSC 機率 (嘗試多種名稱格式)
        sc_data = self._sc_probability.get(track_name)
        if sc_data is None:
            sc_data = self._sc_probability.get(normalized_name)
        if sc_data is None:
            underscore_name = track_name.replace(" ", "_")
            sc_data = self._sc_probability.get(underscore_name)
        if sc_data is None:
            sc_data = {
                "sc_per_lap_pct": 2.47,  # 全局平均
                "vsc_per_lap_pct": 1.98,
                "avg_sc_per_race": 1.31
            }
        
        # 建立速度曲線：優先使用真實數據
        if circuit_data:
            # 從 track_circuit_data 的彎道速度建立真實速度曲線
            speed_curve = self._build_speed_curve_from_circuit_data(circuit_data, length)
            if not speed_curve:
                # 如果建立失敗，使用預設邏輯
                speed_curve = self._build_default_speed_curve(length)
        else:
            # 沒有真實數據，使用預設速度曲線
            speed_curve = self._build_default_speed_curve(length)
            
        # 建立 DRS 區域：優先使用真實數據
        if circuit_data:
            drs_zones = self._build_drs_zones_from_circuit_data(circuit_data)
            if not drs_zones:
                # 如果沒有 DRS 數據，使用預設
                drs_zones = self._build_default_drs_zones(length)
        else:
            drs_zones = self._build_default_drs_zones(length)
        
        return TrackConfig(
            track_name=track_name,
            track_length_m=length,
            difficulty_coefficient=difficulty,
            drs_zones=drs_zones,
            speed_curve=speed_curve,
            pit_lane_time_loss_s=pit_loss,
            sc_probability_per_lap_pct=sc_data["sc_per_lap_pct"],
            vsc_probability_per_lap_pct=sc_data["vsc_per_lap_pct"],
            avg_sc_per_race=sc_data["avg_sc_per_race"]
        )
    
    def get_team_pit_loss(self, track_name: str, team_name: str) -> Optional[float]:
        """
        獲取特定車隊在特定賽道的進站時間損失
        
        Args:
            track_name: 賽道名稱
            team_name: 車隊名稱
            
        Returns:
            車隊的平均進站時間損失，如果沒有數據則返回 None
        """
        # 嘗試多種賽道名稱格式
        track_variants = [
            track_name,
            self._normalize_track_name(track_name),
            track_name.replace(" ", "_"),
            track_name.replace("_", " ")
        ]
        
        for variant in track_variants:
            if variant in self._pit_team_stats:
                team_stats = self._pit_team_stats[variant].get(team_name)
                if team_stats:
                    return team_stats.get("avg_pit_loss_s")
        
        return None
    
    def get_all_team_pit_stats(self, track_name: str) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        獲取特定賽道所有車隊的進站統計
        
        Args:
            track_name: 賽道名稱
            
        Returns:
            {team_name: {avg_pit_loss_s, min_pit_loss_s, max_pit_loss_s, ...}}
        """
        track_variants = [
            track_name,
            self._normalize_track_name(track_name),
            track_name.replace(" ", "_"),
            track_name.replace("_", " ")
        ]
        
        for variant in track_variants:
            if variant in self._pit_team_stats:
                return self._pit_team_stats[variant]
        
        return None
        
    def get_all_tracks(self) -> List[str]:
        """獲取所有已知賽道名稱"""
        return list(self._track_difficulty.keys()) if self._track_difficulty else [
            "Bahrain", "Saudi Arabia", "Australia", "Japan", "China",
            "Miami", "Monaco", "Canada", "Spain", "Austria",
            "Great Britain", "Hungary", "Belgium", "Netherlands", "Italy",
            "Azerbaijan", "Singapore", "United States", "Mexico", "Brazil",
            "Las Vegas", "Qatar", "Abu Dhabi"
        ]


# 全局實例
_manager: Optional[TrackConfigManager] = None

def get_track_config_manager() -> TrackConfigManager:
    """獲取全局 TrackConfigManager 實例"""
    global _manager
    if _manager is None:
        _manager = TrackConfigManager()
    return _manager


def get_track_config(track_name: str) -> TrackConfig:
    """便捷函數：獲取賽道配置"""
    return get_track_config_manager().get_track(track_name)
