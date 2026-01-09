# -*- coding: utf-8 -*-
"""
F142 Pit Lane Time Loss Analyzer - 進站時間損失分析器

分析 2022-2025 所有賽道的進站時間損失，用於策略模擬器。

數據來源:
1. FastF1: session.laps 的 PitInTime / PitOutTime
2. LiveF1: PitLaneTimeCollection.json

輸出:
- json/pit_lane_time_loss_all_tracks.json
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import statistics


@dataclass
class PitStopRecord:
    """單次進站記錄"""
    year: int
    race: str
    driver: str
    lap: int
    pit_duration_s: float  # 進站時間 (秒)
    team: str = ""  # 車隊名稱
    stationary_time_s: Optional[float] = None  # 靜止時間


@dataclass
class TeamPitStats:
    """車隊進站統計"""
    team_name: str
    avg_pit_loss_s: float
    min_pit_loss_s: float
    max_pit_loss_s: float
    std_pit_loss_s: float
    sample_count: int
    seasons: List[int]


@dataclass
class TrackPitLossData:
    """賽道進站損失數據"""
    track_name: str
    avg_pit_loss_s: float
    min_pit_loss_s: float
    max_pit_loss_s: float
    std_pit_loss_s: float
    sample_count: int
    seasons: List[int]
    
    # 細分統計
    avg_stationary_s: Optional[float] = None  # 平均靜止時間
    pit_lane_time_s: Optional[float] = None  # pit lane 通過時間 (= total - stationary)
    
    # 車隊細分統計
    by_team: Optional[Dict[str, Dict[str, Any]]] = None  # 每車隊的統計


class PitLaneTimeAnalyzer:
    """
    進站時間損失分析器
    
    分析所有賽道的歷史進站數據，計算平均損失時間。
    """
    
    def __init__(self, cache_dir: str = "f1_analysis_cache"):
        self.cache_dir = cache_dir
        self.json_dir = Path(__file__).parent.parent.parent.parent / "json"
        self.livef1_dir = self.json_dir / "LiveF1"
        
        # 2022-2025 賽道列表
        self.tracks_2025 = [
            "Bahrain", "Saudi_Arabia", "Australia", "Japan", "China",
            "Miami", "Emilia_Romagna", "Monaco", "Canada", "Spain",
            "Austria", "Great_Britain", "Hungary", "Belgium", "Netherlands",
            "Italy", "Azerbaijan", "Singapore", "United_States", "Mexico",
            "Brazil", "Las_Vegas", "Qatar", "Abu_Dhabi"
        ]
        
    def analyze_all_tracks(self, years: List[int] = None) -> Dict[str, TrackPitLossData]:
        """
        分析所有賽道的進站時間損失
        
        Args:
            years: 要分析的年份列表，預設 [2022, 2023, 2024, 2025]
            
        Returns:
            Dict[track_name, TrackPitLossData]
        """
        if years is None:
            years = [2022, 2023, 2024, 2025]
            
        print(f"[PitLaneTimeAnalyzer] 開始分析 {len(years)} 個賽季的進站數據...")
        
        # 收集所有進站記錄
        all_records: Dict[str, List[PitStopRecord]] = {}
        
        for year in years:
            year_records = self._collect_year_data(year)
            for track, records in year_records.items():
                if track not in all_records:
                    all_records[track] = []
                all_records[track].extend(records)
                
        # 計算每條賽道的統計數據
        results = {}
        for track, records in all_records.items():
            if len(records) >= 3:  # 至少 3 個樣本
                pit_times = [r.pit_duration_s for r in records]
                stationary_times = [r.stationary_time_s for r in records if r.stationary_time_s]
                
                # 計算車隊細分統計
                by_team = self._calculate_team_stats(records)
                
                results[track] = TrackPitLossData(
                    track_name=track,
                    avg_pit_loss_s=statistics.mean(pit_times),
                    min_pit_loss_s=min(pit_times),
                    max_pit_loss_s=max(pit_times),
                    std_pit_loss_s=statistics.stdev(pit_times) if len(pit_times) > 1 else 0.0,
                    sample_count=len(records),
                    seasons=sorted(set(r.year for r in records)),
                    avg_stationary_s=statistics.mean(stationary_times) if stationary_times else None,
                    pit_lane_time_s=None,  # 可從 avg - stationary 計算
                    by_team=by_team
                )
                
                team_count = len(by_team) if by_team else 0
                print(f"  {track}: {results[track].avg_pit_loss_s:.2f}s "
                      f"(n={results[track].sample_count}, teams={team_count}, "
                      f"range={results[track].min_pit_loss_s:.1f}-{results[track].max_pit_loss_s:.1f})")
            else:
                print(f"  {track}: 樣本不足 ({len(records)} 個)")
                
        return results
    
    def _collect_year_data(self, year: int) -> Dict[str, List[PitStopRecord]]:
        """
        收集某一年的進站數據
        
        優先使用 FastF1，備用 LiveF1
        """
        print(f"\n[PitLaneTimeAnalyzer] 收集 {year} 賽季數據...")
        
        records = {}
        
        # 嘗試 FastF1
        fastf1_records = self._collect_from_fastf1(year)
        if fastf1_records:
            records.update(fastf1_records)
            
        # 補充 LiveF1 數據
        livef1_records = self._collect_from_livef1(year)
        for track, track_records in livef1_records.items():
            if track not in records:
                records[track] = track_records
            else:
                # 合併不重複的記錄
                existing_keys = {(r.driver, r.lap) for r in records[track]}
                for r in track_records:
                    if (r.driver, r.lap) not in existing_keys:
                        records[track].append(r)
                        
        return records
    
    def _calculate_team_stats(self, records: List[PitStopRecord]) -> Dict[str, Dict[str, Any]]:
        """
        計算車隊細分統計
        
        Args:
            records: 進站記錄列表
            
        Returns:
            Dict[team_name, {avg, min, max, std, count, seasons}]
        """
        # 按車隊分組
        team_records: Dict[str, List[PitStopRecord]] = {}
        for r in records:
            if r.team:
                if r.team not in team_records:
                    team_records[r.team] = []
                team_records[r.team].append(r)
        
        # 計算每車隊統計
        result = {}
        for team, team_recs in team_records.items():
            if len(team_recs) >= 2:  # 至少 2 個樣本
                pit_times = [r.pit_duration_s for r in team_recs]
                result[team] = {
                    "avg_pit_loss_s": round(statistics.mean(pit_times), 2),
                    "min_pit_loss_s": round(min(pit_times), 2),
                    "max_pit_loss_s": round(max(pit_times), 2),
                    "std_pit_loss_s": round(statistics.stdev(pit_times), 2) if len(pit_times) > 1 else 0.0,
                    "sample_count": len(team_recs),
                    "seasons": sorted(set(r.year for r in team_recs))
                }
        
        return result if result else None
    
    def _collect_from_fastf1(self, year: int) -> Dict[str, List[PitStopRecord]]:
        """從 FastF1 收集進站數據"""
        records = {}
        
        try:
            import fastf1
            fastf1.Cache.enable_cache(self.cache_dir)
            
            # 獲取賽季賽程
            try:
                schedule = fastf1.get_event_schedule(year)
                races = schedule[schedule['EventFormat'] != 'testing']
            except Exception as e:
                print(f"    [FastF1] 無法獲取 {year} 賽程: {e}")
                return records
                
            for _, race_info in races.iterrows():
                race_name = race_info.get('EventName', '')
                country = race_info.get('Country', '')
                
                # 標準化賽道名稱
                track_key = self._normalize_track_name(race_name, country)
                if not track_key:
                    continue
                    
                try:
                    session = fastf1.get_session(year, race_name, 'R')
                    session.load(telemetry=False, weather=False, messages=False)
                    
                    laps = session.laps
                    if laps is None or laps.empty:
                        continue
                        
                    # 篩選有進站的圈
                    pit_laps = laps[laps['PitInTime'].notna()]
                    
                    if pit_laps.empty:
                        continue
                        
                    track_records = []
                    for _, lap in pit_laps.iterrows():
                        driver = str(lap.get('Driver', ''))
                        lap_num = int(lap.get('LapNumber', 0))
                        
                        # 計算進站時間損失
                        # PitOutTime - PitInTime = 總進站時間
                        pit_in = lap.get('PitInTime')
                        pit_out = lap.get('PitOutTime')
                        
                        if pit_in is not None and pit_out is not None:
                            try:
                                # timedelta 轉秒
                                pit_duration = (pit_out - pit_in).total_seconds()
                                if 15 < pit_duration < 60:  # 合理範圍
                                    track_records.append(PitStopRecord(
                                        year=year,
                                        race=race_name,
                                        driver=driver,
                                        lap=lap_num,
                                        pit_duration_s=pit_duration
                                    ))
                            except:
                                pass
                                
                    if track_records:
                        records[track_key] = track_records
                        print(f"    [FastF1] {track_key} {year}: {len(track_records)} 進站記錄")
                        
                except Exception as e:
                    # 跳過無法載入的場次
                    pass
                    
        except ImportError:
            print("    [FastF1] 未安裝 fastf1，跳過")
            
        return records
    
    def _load_driver_team_map(self, race_dir: Path) -> Dict[str, str]:
        """
        從 DriverList.json 載入車號到車隊名稱的映射
        
        Args:
            race_dir: 賽事目錄路徑，包含 DriverList.json
            
        Returns:
            Dict[racing_number, team_name]
        """
        driver_file = race_dir / "DriverList.json"
        team_map = {}
        
        if not driver_file.exists():
            return team_map
            
        try:
            with open(driver_file, 'r', encoding='utf-8') as f:
                driver_data = json.load(f)
                
            # LiveF1 DriverList.json 格式: 
            # {"metadata": {...}, "records": [{"timestamp": "...", "data": {...}}, ...]}
            # 第一個 record 的 data 包含完整的車隊資訊
            if 'records' in driver_data and len(driver_data['records']) > 0:
                first_record = driver_data['records'][0]
                if 'data' in first_record:
                    data = first_record['data']
                    for driver_num, info in data.items():
                        if isinstance(info, dict):
                            team_name = info.get('TeamName', '')
                            if team_name:
                                team_map[driver_num] = team_name
                        
        except Exception as e:
            print(f"    [警告] 載入 DriverList.json 失敗: {e}")
            
        return team_map
    
    def _collect_from_livef1(self, year: int) -> Dict[str, List[PitStopRecord]]:
        """從 LiveF1 JSON 收集進站數據，包含車隊資訊"""
        records = {}
        
        year_dir = self.livef1_dir / str(year)
        if not year_dir.exists():
            return records
            
        # 遍歷所有賽事目錄
        for race_dir in year_dir.iterdir():
            if not race_dir.is_dir():
                continue
                
            race_name = race_dir.name
            track_key = self._normalize_track_name(race_name, "")
            if not track_key:
                continue
                
            pit_file = race_dir / "PitLaneTimeCollection.json"
            if not pit_file.exists():
                continue
            
            # 載入車手-車隊映射
            driver_team_map = self._load_driver_team_map(race_dir)
                
            try:
                with open(pit_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                pit_records = data.get('records', data)
                if not isinstance(pit_records, list):
                    pit_records = [data]
                    
                track_records = []
                seen = set()
                
                for record in pit_records:
                    pit_times = record.get('data', {}).get('PitTimes', {})
                    if not pit_times:
                        continue
                        
                    for driver_num, info in pit_times.items():
                        if not isinstance(info, dict):
                            continue
                            
                        lap = info.get('Lap', 0)
                        duration_str = info.get('Duration', '')
                        
                        if not lap or not duration_str:
                            continue
                            
                        # 解析時間字串 (格式: "22.456" 或 "0:22.456")
                        try:
                            if ':' in str(duration_str):
                                parts = str(duration_str).split(':')
                                duration = float(parts[0]) * 60 + float(parts[1])
                            else:
                                duration = float(duration_str)
                        except:
                            continue
                            
                        # 去重
                        key = (driver_num, lap)
                        if key in seen:
                            continue
                        seen.add(key)
                        
                        # 獲取車隊資訊
                        team = driver_team_map.get(driver_num, "")
                        
                        if 15 < duration < 60:  # 合理範圍
                            track_records.append(PitStopRecord(
                                year=year,
                                race=race_name,
                                driver=driver_num,
                                lap=lap,
                                pit_duration_s=duration,
                                team=team
                            ))
                            
                if track_records:
                    records[track_key] = track_records
                    teams_found = len(set(r.team for r in track_records if r.team))
                    print(f"    [LiveF1] {track_key} {year}: {len(track_records)} 進站記錄, {teams_found} 車隊")
                    
            except Exception as e:
                print(f"    [LiveF1] {race_name} 解析失敗: {e}")
                
        return records
    
    def _normalize_track_name(self, race_name: str, country: str) -> Optional[str]:
        """標準化賽道名稱"""
        # 清理名稱
        name = race_name.replace("Grand Prix", "").replace("_Race", "").strip()
        name = name.replace(" ", "_")
        
        # 映射表
        track_mapping = {
            "Bahrain": "Bahrain",
            "Saudi_Arabia": "Saudi_Arabia", "Saudi_Arabian": "Saudi_Arabia", "Jeddah": "Saudi_Arabia",
            "Australia": "Australia", "Australian": "Australia", "Melbourne": "Australia",
            "Japan": "Japan", "Japanese": "Japan", "Suzuka": "Japan",
            "China": "China", "Chinese": "China", "Shanghai": "China",
            "Miami": "Miami",
            "Emilia_Romagna": "Emilia_Romagna", "Imola": "Emilia_Romagna",
            "Monaco": "Monaco",
            "Canada": "Canada", "Canadian": "Canada", "Montreal": "Canada",
            "Spain": "Spain", "Spanish": "Spain", "Barcelona": "Spain",
            "Austria": "Austria", "Austrian": "Austria", "Spielberg": "Austria",
            "Great_Britain": "Great_Britain", "British": "Great_Britain", "Silverstone": "Great_Britain",
            "Hungary": "Hungary", "Hungarian": "Hungary", "Budapest": "Hungary",
            "Belgium": "Belgium", "Belgian": "Belgium", "Spa": "Belgium",
            "Netherlands": "Netherlands", "Dutch": "Netherlands", "Zandvoort": "Netherlands",
            "Italy": "Italy", "Italian": "Italy", "Monza": "Italy",
            "Azerbaijan": "Azerbaijan", "Baku": "Azerbaijan",
            "Singapore": "Singapore",
            "United_States": "United_States", "USA": "United_States", "Austin": "United_States", "COTA": "United_States",
            "Mexico": "Mexico", "Mexican": "Mexico", "Mexico_City": "Mexico",
            "Brazil": "Brazil", "Brazilian": "Brazil", "Sao_Paulo": "Brazil", "Interlagos": "Brazil",
            "Las_Vegas": "Las_Vegas",
            "Qatar": "Qatar", "Lusail": "Qatar",
            "Abu_Dhabi": "Abu_Dhabi", "Yas_Marina": "Abu_Dhabi",
        }
        
        # 嘗試匹配
        for key, value in track_mapping.items():
            if key.lower() in name.lower() or key.lower() in country.lower():
                return value
                
        return None
    
    def save_to_json(self, results: Dict[str, TrackPitLossData]) -> str:
        """保存結果到 JSON"""
        output = {
            "metadata": {
                "analysis_type": "pit_lane_time_loss",
                "generated_at": datetime.now().isoformat(),
                "tracks_count": len(results),
                "description": "每條賽道的平均進站時間損失統計 (2022-2025)"
            },
            "tracks": {
                track: asdict(data)
                for track, data in results.items()
            },
            "summary": {
                "overall_avg_pit_loss_s": statistics.mean([d.avg_pit_loss_s for d in results.values()]),
                "fastest_pit_track": min(results.items(), key=lambda x: x[1].avg_pit_loss_s)[0],
                "slowest_pit_track": max(results.items(), key=lambda x: x[1].avg_pit_loss_s)[0],
                "total_samples": sum(d.sample_count for d in results.values())
            }
        }
        
        output_path = self.json_dir / "pit_lane_time_loss_all_tracks.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
            
        print(f"\n[PitLaneTimeAnalyzer] 結果已保存到: {output_path}")
        return str(output_path)


def execute_pit_lane_time_analyzer(years: List[int] = None, save_json: bool = True) -> Dict[str, Any]:
    """
    執行進站時間損失分析
    
    Args:
        years: 要分析的年份列表
        save_json: 是否保存 JSON
        
    Returns:
        分析結果
    """
    analyzer = PitLaneTimeAnalyzer()
    results = analyzer.analyze_all_tracks(years)
    
    if save_json and results:
        analyzer.save_to_json(results)
        
    return {
        "success": True,
        "tracks_analyzed": len(results),
        "data": {track: asdict(data) for track, data in results.items()}
    }


if __name__ == "__main__":
    result = execute_pit_lane_time_analyzer()
    print(f"\n分析完成: {result['tracks_analyzed']} 條賽道")
