"""
F137 Track Corner Analyzer - 賽道彎道分析器
F138 DRS Zone Analyzer - DRS 區域分析器

從 FastF1 取得真實的賽道彎道和 DRS 區域數據，
用於策略模擬器的精確位置追蹤。
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import pandas as pd


@dataclass
class CornerInfo:
    """彎道資訊"""
    number: int
    letter: str
    distance_m: float
    angle: float
    
    # 速度分類 (從遙測數據分析)
    speed_category: str = "unknown"  # low/mid/high
    min_speed_kmh: float = 0.0
    avg_speed_kmh: float = 0.0
    max_speed_kmh: float = 0.0


@dataclass
class DRSZoneInfo:
    """DRS 區域資訊"""
    zone_id: int
    detection_distance_m: float  # 偵測點距離
    activation_distance_m: float  # 啟動點距離
    end_distance_m: float  # 結束點距離
    length_m: float = 0.0
    
    def __post_init__(self):
        if self.end_distance_m > self.activation_distance_m:
            self.length_m = self.end_distance_m - self.activation_distance_m
        else:
            # 跨越起終點
            self.length_m = -1  # 需要賽道長度來計算


@dataclass
class TrackCircuitData:
    """賽道完整數據"""
    track_name: str
    track_length_m: float
    corners: List[CornerInfo]
    drs_zones: List[DRSZoneInfo]
    corners_count: int = 0
    drs_zones_count: int = 0
    
    def __post_init__(self):
        self.corners_count = len(self.corners)
        self.drs_zones_count = len(self.drs_zones)


class TrackCircuitAnalyzer:
    """
    賽道分析器
    
    從 FastF1 取得彎道和 DRS 區域的真實數據
    """
    
    def __init__(self, cache_dir: str = "f1_analysis_cache"):
        self.cache_dir = cache_dir
        self.json_dir = Path(__file__).parent.parent.parent / "json"
        
    def analyze_track(
        self,
        year: int,
        race: str,
        session_type: str = "R"
    ) -> Optional[TrackCircuitData]:
        """
        分析賽道的彎道和 DRS 區域
        
        Args:
            year: 年份
            race: 賽事名稱
            session_type: 場次類型 (R/Q/FP1/FP2/FP3)
            
        Returns:
            TrackCircuitData 或 None
        """
        try:
            import fastf1
            fastf1.Cache.enable_cache(self.cache_dir)
            
            print(f"[TrackCircuitAnalyzer] 載入 {year} {race} {session_type}...")
            session = fastf1.get_session(year, race, session_type)
            session.load()
            
            # 取得賽道資訊
            circuit_info = session.get_circuit_info()
            
            # 取得賽道長度
            track_length = self._get_track_length(session)
            
            # 分析彎道
            corners = self._analyze_corners(circuit_info, session)
            
            # 分析 DRS 區域
            drs_zones = self._analyze_drs_zones(session, track_length)
            
            return TrackCircuitData(
                track_name=race,
                track_length_m=track_length,
                corners=corners,
                drs_zones=drs_zones
            )
            
        except Exception as e:
            print(f"[TrackCircuitAnalyzer] 分析失敗: {e}")
            return None
    
    def _get_track_length(self, session) -> float:
        """取得賽道長度"""
        try:
            # 從最快圈的遙測數據取得
            fastest = session.laps.pick_fastest()
            tel = fastest.get_telemetry()
            return tel['Distance'].max()
        except:
            # 預設值
            return 5000.0
    
    def _analyze_corners(
        self,
        circuit_info,
        session
    ) -> List[CornerInfo]:
        """
        分析彎道資訊
        
        從 FastF1 的 circuit_info.corners 取得彎道位置，
        並從遙測數據分析每個彎道的速度。
        """
        corners = []
        
        # 取得彎道基本資訊
        corners_df = circuit_info.corners
        
        # 取得速度數據 (從最快圈)
        try:
            fastest = session.laps.pick_fastest()
            tel = fastest.get_telemetry()
        except:
            tel = None
        
        for _, row in corners_df.iterrows():
            corner_num = int(row['Number'])
            corner_letter = str(row.get('Letter', ''))
            distance = float(row['Distance']) if pd.notna(row['Distance']) else 0.0
            angle = float(row['Angle']) if pd.notna(row['Angle']) else 0.0
            
            # 分析該彎道的速度
            speed_info = self._get_corner_speed(tel, distance, angle)
            
            corners.append(CornerInfo(
                number=corner_num,
                letter=corner_letter,
                distance_m=distance,
                angle=abs(angle),  # 使用絕對值
                speed_category=speed_info['category'],
                min_speed_kmh=speed_info['min'],
                avg_speed_kmh=speed_info['avg'],
                max_speed_kmh=speed_info['max']
            ))
        
        return corners
    
    def _get_corner_speed(
        self,
        telemetry,
        corner_distance: float,
        angle: float
    ) -> Dict[str, float]:
        """
        分析彎道的速度
        
        根據彎道位置前後 100m 的遙測數據計算速度
        """
        default = {'category': 'unknown', 'min': 0, 'avg': 0, 'max': 0}
        
        if telemetry is None or corner_distance <= 0:
            return default
        
        try:
            # 取彎道前後 100m 的數據
            window = 100
            mask = (
                (telemetry['Distance'] >= corner_distance - window) &
                (telemetry['Distance'] <= corner_distance + window)
            )
            corner_data = telemetry[mask]
            
            if len(corner_data) == 0:
                return default
            
            min_speed = corner_data['Speed'].min()
            avg_speed = corner_data['Speed'].mean()
            max_speed = corner_data['Speed'].max()
            
            # 速度分類
            if min_speed < 100:
                category = "low"
            elif min_speed < 180:
                category = "mid"
            else:
                category = "high"
            
            return {
                'category': category,
                'min': float(min_speed),
                'avg': float(avg_speed),
                'max': float(max_speed)
            }
            
        except Exception as e:
            return default
    
    def _analyze_drs_zones(
        self,
        session,
        track_length: float
    ) -> List[DRSZoneInfo]:
        """
        分析 DRS 區域
        
        從多個車手的遙測數據中分析 DRS 開啟位置
        """
        drs_zones = []
        
        try:
            # 收集多個車手的 DRS 數據
            all_drs_activations = []
            
            for driver in session.drivers[:10]:  # 前 10 個車手
                driver_laps = session.laps.pick_drivers(driver)
                if len(driver_laps) == 0:
                    continue
                
                # 取中間幾圈 (避免開始和結束的異常)
                mid_laps = driver_laps[
                    (driver_laps['LapNumber'] >= 10) &
                    (driver_laps['LapNumber'] <= 40)
                ]
                
                if len(mid_laps) == 0:
                    continue
                
                for _, lap in mid_laps.iterrows():
                    try:
                        tel = lap.get_telemetry()
                        if 'DRS' not in tel.columns:
                            continue
                        
                        # 找出 DRS 開啟的區域
                        zones = self._find_drs_zones_in_lap(tel, track_length)
                        all_drs_activations.extend(zones)
                        
                    except:
                        continue
            
            # 聚合 DRS 區域
            if all_drs_activations:
                drs_zones = self._aggregate_drs_zones(all_drs_activations, track_length)
            
        except Exception as e:
            print(f"[TrackCircuitAnalyzer] DRS 分析錯誤: {e}")
        
        return drs_zones
    
    def _find_drs_zones_in_lap(
        self,
        telemetry,
        track_length: float
    ) -> List[Tuple[float, float]]:
        """
        找出單圈中的 DRS 開啟區域
        
        Returns:
            List of (start_distance, end_distance)
        """
        zones = []
        
        try:
            # DRS >= 10 表示 DRS 開啟
            tel = telemetry.copy()
            tel['DRS_on'] = tel['DRS'] >= 10
            
            # 找出變化點
            tel['DRS_change'] = tel['DRS_on'].diff()
            
            # 開始點 (False -> True)
            starts = tel[(tel['DRS_change'] == True) & (tel['DRS_on'] == True)]['Distance'].tolist()
            # 結束點 (True -> False)
            ends = tel[(tel['DRS_change'] == True) & (tel['DRS_on'] == False)]['Distance'].tolist()
            
            # 配對
            for start in starts:
                # 找最近的結束點
                valid_ends = [e for e in ends if e > start]
                if valid_ends:
                    end = min(valid_ends)
                    zones.append((start, end))
                else:
                    # 可能跨越起終點
                    if ends:
                        zones.append((start, ends[0] + track_length))
            
        except:
            pass
        
        return zones
    
    def _aggregate_drs_zones(
        self,
        all_activations: List[Tuple[float, float]],
        track_length: float
    ) -> List[DRSZoneInfo]:
        """
        聚合所有 DRS 開啟數據，找出穩定的 DRS 區域
        """
        if not all_activations:
            return []
        
        # 將所有開始點分組 (每 100m 一組)
        start_groups = {}
        for start, end in all_activations:
            group_key = int(start / 100) * 100
            if group_key not in start_groups:
                start_groups[group_key] = []
            start_groups[group_key].append((start, end))
        
        # 找出穩定的區域 (至少有 5 個樣本)
        drs_zones = []
        zone_id = 1
        
        for group_key in sorted(start_groups.keys()):
            samples = start_groups[group_key]
            if len(samples) >= 5:
                # 計算平均值
                avg_start = sum(s for s, e in samples) / len(samples)
                avg_end = sum(e for s, e in samples) / len(samples)
                
                # 處理跨越起終點的情況
                if avg_end > track_length:
                    avg_end = avg_end - track_length
                
                # 估算偵測點 (啟動點前約 70m)
                detection = avg_start - 70
                if detection < 0:
                    detection += track_length
                
                drs_zones.append(DRSZoneInfo(
                    zone_id=zone_id,
                    detection_distance_m=detection,
                    activation_distance_m=avg_start,
                    end_distance_m=avg_end
                ))
                zone_id += 1
        
        return drs_zones
    
    def save_to_json(
        self,
        data: TrackCircuitData,
        output_dir: Optional[Path] = None
    ) -> str:
        """保存數據到 JSON"""
        if output_dir is None:
            output_dir = self.json_dir
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 轉換為可序列化的格式
        output = {
            'track_name': data.track_name,
            'track_length_m': data.track_length_m,
            'corners_count': data.corners_count,
            'drs_zones_count': data.drs_zones_count,
            'corners': [asdict(c) for c in data.corners],
            'drs_zones': [asdict(z) for z in data.drs_zones]
        }
        
        filename = f"track_circuit_data_{data.track_name.replace(' ', '_')}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print(f"[TrackCircuitAnalyzer] 已保存到 {filepath}")
        return str(filepath)


def analyze_track_circuit(
    year: int,
    race: str,
    session_type: str = "R",
    save_json: bool = True
) -> Optional[Dict]:
    """
    分析賽道的彎道和 DRS 區域
    
    這是 F137/F138 的統一入口點
    """
    analyzer = TrackCircuitAnalyzer()
    data = analyzer.analyze_track(year, race, session_type)
    
    if data is None:
        return None
    
    if save_json:
        analyzer.save_to_json(data)
    
    # 返回摘要
    return {
        'track_name': data.track_name,
        'track_length_m': data.track_length_m,
        'corners_count': data.corners_count,
        'drs_zones_count': data.drs_zones_count,
        'corners': [
            {
                'number': c.number,
                'distance_m': c.distance_m,
                'speed_category': c.speed_category,
                'min_speed_kmh': c.min_speed_kmh
            }
            for c in data.corners
        ],
        'drs_zones': [
            {
                'zone_id': z.zone_id,
                'activation_m': z.activation_distance_m,
                'end_m': z.end_distance_m,
                'length_m': z.length_m
            }
            for z in data.drs_zones
        ]
    }


if __name__ == "__main__":
    # 測試
    result = analyze_track_circuit(2025, "Japan", "R")
    
    if result:
        print("\n=== 分析結果 ===")
        print(f"賽道: {result['track_name']}")
        print(f"長度: {result['track_length_m']:.0f}m")
        print(f"彎道數: {result['corners_count']}")
        print(f"DRS 區數: {result['drs_zones_count']}")
        
        print("\n彎道列表:")
        for c in result['corners'][:5]:
            print(f"  T{c['number']}: {c['distance_m']:.0f}m, "
                  f"{c['speed_category']}, min={c['min_speed_kmh']:.0f}km/h")
        
        print("\nDRS 區域:")
        for z in result['drs_zones']:
            print(f"  Zone {z['zone_id']}: {z['activation_m']:.0f}m - {z['end_m']:.0f}m")
