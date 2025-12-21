#!/usr/bin/env python3
"""
分析 FP3 → Q 的改進率
驗證用戶發現：Q 時間總是優於 FP3 ideal lap

這個分析將揭示：
1. 每個賽道的平均 FP3→Q 改進率
2. 不同車手/車隊的改進幅度差異
3. 改進率與賽道類型的關係
4. 這個特徵對模型的潛在貢獻
"""

import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# 導入 v3.0 trainer 用於數據載入
sys.path.append(str(Path(__file__).parent))
from CLI_modules.cli.prediction.track_specific_trainer_v3 import TrackSpecificTrainerV3


class FP3QImprovementAnalyzer:
    """FP3→Q 改進率分析器"""
    
    def __init__(self):
        self.base_trainer = TrackSpecificTrainerV3(verbose=False)
        self.json_dir = Path("json/predictionJSON")
        
        # 賽道類型分類
        self.track_types = {
            'street': ['Monaco', 'Singapore', 'Baku', 'Azerbaijan', 'Saudi Arabia', 'Las Vegas', 'Miami'],
            'high_speed': ['Italy', 'Great Britain', 'Belgium', 'Austria', 'Mexico'],
            'technical': ['Hungary', 'Netherlands', 'Spain', 'Japan', 'China'],
            'mixed': ['Bahrain', 'Australia', 'Canada', 'Abu Dhabi', 'Brazil', 'United States']
        }
        
        self.results = {
            'by_track': {},
            'by_year': defaultdict(list),
            'by_driver': defaultdict(list),
            'by_track_type': defaultdict(list),
            'overall': []
        }
    
    def get_track_type(self, track_name: str) -> str:
        """取得賽道類型"""
        for track_type, tracks in self.track_types.items():
            if track_name in tracks:
                return track_type
        return 'mixed'
    
    def analyze_single_track(self, track_name: str, start_year: int = 2022, 
                            end_year: int = 2024) -> dict:
        """分析單一賽道的 FP3→Q 改進"""
        print(f"\n{'='*70}")
        print(f"分析賽道: {track_name}")
        print(f"{'='*70}")
        
        track_improvements = []
        
        for year in range(start_year, end_year + 1):
            # 載入 FP3→Q 數據
            fp_q_files = list(self.json_dir.glob(f"fp_q_data_{year}_{track_name}_*.json"))
            if not fp_q_files:
                print(f"  [SKIP] {year} - 找不到數據")
                continue
            
            with open(fp_q_files[0], 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 提取 FP3 和 Q 數據
            fp3_drivers = data.get('practice_sessions', {}).get('FP3', {}).get('driver_data', {})
            q_results = data.get('qualifying', {}).get('results', {})
            
            year_improvements = []
            
            for driver in fp3_drivers.keys():
                if driver not in q_results:
                    continue
                
                fp3_data = fp3_drivers[driver]
                q_data = q_results[driver]
                
                # FP3 ideal lap
                fp3_ideal = fp3_data.get('best_lap_time')
                if fp3_ideal is None or fp3_ideal == 0:
                    continue
                
                # Q 最佳時間
                q_time_str = str(q_data['best_time'])
                if 'days' in q_time_str:
                    time_parts = q_time_str.split(' ')[-1]
                    h, m, s = time_parts.split(':')
                    q_time = int(h) * 3600 + int(m) * 60 + float(s)
                else:
                    continue
                
                # 計算改進
                improvement_seconds = fp3_ideal - q_time
                improvement_rate = improvement_seconds / fp3_ideal
                
                # 驗證：Q 是否真的比 FP3 快
                is_faster = improvement_seconds > 0
                
                improvement_data = {
                    'year': year,
                    'track': track_name,
                    'driver': driver,
                    'fp3_ideal': fp3_ideal,
                    'q_time': q_time,
                    'improvement_seconds': improvement_seconds,
                    'improvement_rate': improvement_rate,
                    'is_q_faster': is_faster
                }
                
                year_improvements.append(improvement_data)
                track_improvements.append(improvement_data)
                
                # 全局統計
                self.results['overall'].append(improvement_data)
                self.results['by_year'][year].append(improvement_data)
                self.results['by_driver'][driver].append(improvement_data)
                
                track_type = self.get_track_type(track_name)
                self.results['by_track_type'][track_type].append(improvement_data)
            
            if year_improvements:
                avg_improvement = np.mean([d['improvement_seconds'] for d in year_improvements])
                avg_rate = np.mean([d['improvement_rate'] for d in year_improvements])
                q_faster_count = sum(1 for d in year_improvements if d['is_q_faster'])
                
                print(f"  [{year}] 樣本數: {len(year_improvements)}")
                print(f"        平均改進: {avg_improvement:.3f}s ({avg_rate*100:.2f}%)")
                print(f"        Q 更快: {q_faster_count}/{len(year_improvements)} ({q_faster_count/len(year_improvements)*100:.1f}%)")
        
        if track_improvements:
            track_result = {
                'track': track_name,
                'track_type': self.get_track_type(track_name),
                'sample_count': len(track_improvements),
                'avg_improvement_seconds': np.mean([d['improvement_seconds'] for d in track_improvements]),
                'std_improvement_seconds': np.std([d['improvement_seconds'] for d in track_improvements]),
                'avg_improvement_rate': np.mean([d['improvement_rate'] for d in track_improvements]),
                'min_improvement': min([d['improvement_seconds'] for d in track_improvements]),
                'max_improvement': max([d['improvement_seconds'] for d in track_improvements]),
                'q_faster_count': sum(1 for d in track_improvements if d['is_q_faster']),
                'q_faster_rate': sum(1 for d in track_improvements if d['is_q_faster']) / len(track_improvements)
            }
            
            self.results['by_track'][track_name] = track_result
            
            print(f"\n  [總結] {track_name}")
            print(f"    總樣本: {track_result['sample_count']}")
            print(f"    平均改進: {track_result['avg_improvement_seconds']:.3f}s ± {track_result['std_improvement_seconds']:.3f}s")
            print(f"    改進率: {track_result['avg_improvement_rate']*100:.2f}%")
            print(f"    Q 更快比例: {track_result['q_faster_rate']*100:.1f}%")
            print(f"    改進範圍: [{track_result['min_improvement']:.3f}s, {track_result['max_improvement']:.3f}s]")
            
            return track_result
        
        return None
    
    def analyze_all_tracks(self):
        """分析所有賽道"""
        # 2025 賽道列表
        tracks = [
            "Australia", "China", "Japan", "Bahrain", "Saudi Arabia",
            "Miami", "Monaco", "Spain", "Canada", "Austria",
            "Great Britain", "Belgium", "Hungary", "Netherlands",
            "Italy", "Azerbaijan", "Singapore", "United States",
            "Mexico", "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
        ]
        
        print("\n" + "="*70)
        print("開始分析所有賽道的 FP3→Q 改進率")
        print("="*70)
        
        for track in tracks:
            self.analyze_single_track(track, 2022, 2024)
        
        self.generate_summary_report()
    
    def generate_summary_report(self):
        """生成總結報告"""
        print("\n" + "="*70)
        print("FP3→Q 改進率分析報告")
        print("="*70)
        
        # 1. 全局統計
        if self.results['overall']:
            all_improvements = [d['improvement_seconds'] for d in self.results['overall']]
            all_rates = [d['improvement_rate'] for d in self.results['overall']]
            q_faster_count = sum(1 for d in self.results['overall'] if d['is_q_faster'])
            
            print(f"\n[全局統計]")
            print(f"  總樣本數: {len(self.results['overall'])}")
            print(f"  平均改進: {np.mean(all_improvements):.3f}s ± {np.std(all_improvements):.3f}s")
            print(f"  平均改進率: {np.mean(all_rates)*100:.2f}%")
            print(f"  Q 更快比例: {q_faster_count}/{len(self.results['overall'])} ({q_faster_count/len(self.results['overall'])*100:.1f}%)")
            print(f"  改進範圍: [{min(all_improvements):.3f}s, {max(all_improvements):.3f}s]")
        
        # 2. 按賽道類型統計
        print(f"\n[按賽道類型統計]")
        for track_type, improvements in self.results['by_track_type'].items():
            if improvements:
                avg_imp = np.mean([d['improvement_seconds'] for d in improvements])
                avg_rate = np.mean([d['improvement_rate'] for d in improvements])
                q_faster = sum(1 for d in improvements if d['is_q_faster'])
                
                print(f"  {track_type:15s}: {avg_imp:6.3f}s ({avg_rate*100:5.2f}%), Q 更快 {q_faster}/{len(improvements)} ({q_faster/len(improvements)*100:.1f}%)")
        
        # 3. Top 5 改進最大的賽道
        print(f"\n[Top 5 改進最大的賽道]")
        sorted_tracks = sorted(
            self.results['by_track'].items(),
            key=lambda x: x[1]['avg_improvement_seconds'],
            reverse=True
        )[:5]
        
        for i, (track, data) in enumerate(sorted_tracks, 1):
            print(f"  {i}. {track:20s}: {data['avg_improvement_seconds']:6.3f}s ({data['avg_improvement_rate']*100:5.2f}%) [{data['track_type']}]")
        
        # 4. Top 5 改進最小的賽道
        print(f"\n[Top 5 改進最小的賽道]")
        sorted_tracks_min = sorted(
            self.results['by_track'].items(),
            key=lambda x: x[1]['avg_improvement_seconds']
        )[:5]
        
        for i, (track, data) in enumerate(sorted_tracks_min, 1):
            print(f"  {i}. {track:20s}: {data['avg_improvement_seconds']:6.3f}s ({data['avg_improvement_rate']*100:5.2f}%) [{data['track_type']}]")
        
        # 5. 年份趨勢
        print(f"\n[年份趨勢]")
        for year in sorted(self.results['by_year'].keys()):
            improvements = self.results['by_year'][year]
            avg_imp = np.mean([d['improvement_seconds'] for d in improvements])
            avg_rate = np.mean([d['improvement_rate'] for d in improvements])
            
            print(f"  {year}: {avg_imp:6.3f}s ({avg_rate*100:5.2f}%), 樣本數: {len(improvements)}")
        
        # 6. 驗證用戶發現
        print(f"\n[驗證用戶發現: Q 是否總是比 FP3 快?]")
        all_data = self.results['overall']
        negative_improvements = [d for d in all_data if not d['is_q_faster']]
        
        print(f"  Q 比 FP3 慢的情況: {len(negative_improvements)}/{len(all_data)} ({len(negative_improvements)/len(all_data)*100:.2f}%)")
        
        if negative_improvements:
            print(f"  [例外情況分析]")
            for d in negative_improvements[:10]:  # 顯示前 10 個例外
                print(f"    {d['year']} {d['track']:15s} {d['driver']:3s}: FP3 {d['fp3_ideal']:.3f}s → Q {d['q_time']:.3f}s (慢 {-d['improvement_seconds']:.3f}s)")
        
        # 7. 保存結果
        self.save_results()
    
    def save_results(self):
        """保存分析結果"""
        output_file = Path("fp3_q_improvement_analysis.json")
        
        # 轉換為可序列化格式
        serializable_results = {
            'by_track': self.results['by_track'],
            'by_year': {str(k): v for k, v in self.results['by_year'].items()},
            'by_track_type': dict(self.results['by_track_type']),
            'summary': {
                'total_samples': len(self.results['overall']),
                'avg_improvement_seconds': np.mean([d['improvement_seconds'] for d in self.results['overall']]),
                'avg_improvement_rate': np.mean([d['improvement_rate'] for d in self.results['overall']]),
                'q_faster_rate': sum(1 for d in self.results['overall'] if d['is_q_faster']) / len(self.results['overall'])
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n[保存結果] {output_file}")


def main():
    analyzer = FP3QImprovementAnalyzer()
    analyzer.analyze_all_tracks()


if __name__ == '__main__':
    main()
