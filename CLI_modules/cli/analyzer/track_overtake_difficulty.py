"""
F136: 賽道超車難度分析器

計算每條賽道的基礎超車難度係數，用於位置追蹤模擬器的超車成功率模型。

處理邏輯:
  1. 讀取 F134 (成功超車) 和 F135 (失敗嘗試) 的數據
  2. 統計每賽道的超車成功率
  3. 計算超車難度係數 (0=容易, 1=困難)
  
輸出: track_overtake_difficulty.json
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict
from datetime import datetime


class TrackOvertakeDifficultyAnalyzer:
    """賽道超車難度分析器"""
    
    # 每條賽道的標準比賽圈數 (用於計算每圈超車率)
    TRACK_LAPS = {
        'Abu_Dhabi': 58,
        'Australian': 58,
        'Austrian': 71,
        'Azerbaijan': 51,
        'Bahrain': 57,
        'Belgian': 44,
        'British': 52,
        'Canadian': 70,
        'Chinese': 56,
        'Dutch': 72,
        'Emilia_Romagna': 63,
        'Hungarian': 70,
        'Italian': 53,
        'Japanese': 53,
        'Las_Vegas': 50,
        'Mexico_City': 71,
        'Miami': 57,
        'Monaco': 78,
        'Qatar': 57,
        'Saudi_Arabian': 50,
        'Singapore': 62,
        'Spanish': 66,
        'United_States': 56,
        'São_Paulo': 71,
    }
    
    def __init__(self):
        self.json_dir = Path("json")
        self.output_path = self.json_dir / "track_overtake_difficulty.json"
        
    def analyze(self) -> Dict[str, Any]:
        """執行賽道超車難度分析"""
        print("\n" + "="*60)
        print("F136: Track Overtake Difficulty Analyzer")
        print("="*60)
        
        # 讀取成功超車數據 (F134)
        success_data = self._load_json("overtake_events_history_2024_2025.json")
        if not success_data:
            print("[F136] Error: Cannot load F134 data")
            return {}
            
        # 讀取失敗嘗試數據 (F135)
        failed_data = self._load_json("overtake_attempts_failed_2024_2025.json")
        if not failed_data:
            print("[F136] Error: Cannot load F135 data")
            return {}
            
        # 統計每賽道的成功和失敗次數
        track_stats = self._collect_track_stats(success_data, failed_data)
        
        # 計算難度係數
        result = self._calculate_difficulty(track_stats)
        
        # 保存結果
        self._save_result(result)
        
        return result
        
    def _load_json(self, filename: str) -> Dict:
        """讀取 JSON 檔案"""
        filepath = self.json_dir / filename
        if not filepath.exists():
            print(f"[F136] File not found: {filepath}")
            return {}
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[F136] Error loading {filename}: {e}")
            return {}
            
    def _collect_track_stats(
        self, 
        success_data: Dict, 
        failed_data: Dict
    ) -> Dict[str, Dict]:
        """收集每賽道的統計數據"""
        track_stats = defaultdict(lambda: {
            'success_count': 0,
            'failed_count': 0,
            'on_track_success': 0,  # 僅計算賽道上的超車 (排除進站)
            'races': set(),
            'success_events': [],
            'failed_events': []
        })
        
        # 處理成功超車事件
        for event in success_data.get('events', []):
            track = event.get('track', '')
            if not track:
                continue
                
            track_stats[track]['success_count'] += 1
            track_stats[track]['races'].add(event.get('race', ''))
            
            # 統計賽道上超車 (非進站相關)
            if event.get('overtake_type') == 'on_track':
                track_stats[track]['on_track_success'] += 1
                
            track_stats[track]['success_events'].append(event)
            
        # 處理失敗嘗試事件
        for event in failed_data.get('events', []):
            track = event.get('track', '')
            if not track:
                continue
                
            track_stats[track]['failed_count'] += 1
            track_stats[track]['races'].add(event.get('race', ''))
            track_stats[track]['failed_events'].append(event)
            
        # 轉換 set 為 list
        for track in track_stats:
            track_stats[track]['races'] = list(track_stats[track]['races'])
            
        return dict(track_stats)
        
    def _calculate_difficulty(self, track_stats: Dict) -> Dict[str, Any]:
        """計算每賽道的超車難度係數"""
        tracks = {}
        
        for track_name, stats in track_stats.items():
            total_attempts = stats['success_count'] + stats['failed_count']
            num_races = len(stats['races'])
            
            if total_attempts == 0 or num_races == 0:
                continue
                
            # 計算成功率
            success_rate = stats['success_count'] / total_attempts
            
            # 計算每場比賽的平均超車次數
            avg_overtakes = stats['success_count'] / num_races
            
            # 計算每圈超車率
            laps_per_race = self.TRACK_LAPS.get(track_name, 60)
            total_laps = laps_per_race * num_races
            overtake_rate_per_lap = stats['success_count'] / total_laps
            
            # 計算難度係數 (基於成功率的倒數，正規化到 0-1)
            # 低成功率 = 高難度
            difficulty_coefficient = 1 - success_rate
            
            # 計算每場比賽的嘗試次數
            avg_attempts_per_race = total_attempts / num_races
            
            tracks[track_name] = {
                'success_count': stats['success_count'],
                'failed_count': stats['failed_count'],
                'total_attempts': total_attempts,
                'success_rate': round(success_rate, 4),
                'overtake_rate_per_lap': round(overtake_rate_per_lap, 4),
                'difficulty_coefficient': round(difficulty_coefficient, 4),
                'avg_overtakes_per_race': round(avg_overtakes, 1),
                'avg_attempts_per_race': round(avg_attempts_per_race, 1),
                'sample_races': num_races,
                'on_track_success': stats['on_track_success']
            }
            
        # 排序 (按難度係數降序)
        sorted_tracks = dict(
            sorted(tracks.items(), key=lambda x: x[1]['difficulty_coefficient'], reverse=True)
        )
        
        return {
            'metadata': {
                'analysis_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'data_source': {
                    'success_events': 'overtake_events_history_2024_2025.json (F134)',
                    'failed_events': 'overtake_attempts_failed_2024_2025.json (F135)'
                },
                'total_tracks': len(sorted_tracks),
                'difficulty_scale': '0=easy, 1=difficult'
            },
            'tracks': sorted_tracks
        }
        
    def _save_result(self, result: Dict):
        """保存結果到 JSON"""
        self.json_dir.mkdir(exist_ok=True)
        
        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
        print(f"\n[F136] Results saved to: {self.output_path}")
        print(f"  - Total tracks analyzed: {len(result.get('tracks', {}))}")
        
        # 顯示摘要
        print("\n[F136] Track Difficulty Summary (sorted by difficulty):")
        print("-" * 70)
        print(f"{'Track':<20} {'Success%':>10} {'Difficulty':>12} {'Avg/Race':>10}")
        print("-" * 70)
        
        for track, data in list(result.get('tracks', {}).items())[:10]:
            print(f"{track:<20} {data['success_rate']*100:>9.1f}% {data['difficulty_coefficient']:>11.3f} {data['avg_overtakes_per_race']:>10.1f}")
            

def execute_track_overtake_difficulty(
    year: int = None,
    race: str = None,
    session: str = None,
    **kwargs
) -> Dict[str, Any]:
    """
    執行賽道超車難度分析器
    
    這是 CLI 模組的入口點
    """
    analyzer = TrackOvertakeDifficultyAnalyzer()
    return analyzer.analyze()


# 直接執行測試
if __name__ == "__main__":
    result = execute_track_overtake_difficulty()
    print(f"\nAnalysis complete. Tracks analyzed: {len(result.get('tracks', {}))}")
