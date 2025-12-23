#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
賽道特徵收集器 - 用於賽道分類建模
Track Feature Collector for Track Classification Modeling

功能：
- 自動分析所有賽事的賽道特徵
- 提取彎道數量、平均速度、速度範圍等客觀數據
- 生成賽道特徵數據庫供分類使用
- 遵循反幻覺原則：基於真實數據而非主觀判斷

使用方式:
    python collect_track_features.py

作者: F1 Analysis Team
創建日期: 2025-10-31
"""

import json
import glob
import fastf1
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# 啟用 FastF1 緩存
fastf1.Cache.enable_cache('f1_analysis_cache')


class TrackFeatureCollector:
    """賽道特徵收集器"""
    
    def __init__(self):
        self.track_features = {}
        self.json_dir = Path("json/predictionJSON")
        
    def collect_all_tracks(self):
        """收集所有賽道的特徵（使用 JSON 數據）"""
        print("🏁 開始收集賽道特徵...")
        print("=" * 60)
        
        # 讀取所有 JSON 檔案
        json_files = list(self.json_dir.glob("*.json"))
        print(f"📦 找到 {len(json_files)} 個賽事檔案")
        
        track_data_collection = defaultdict(list)
        processed_count = 0
        error_count = 0
        
        for json_file in json_files:
            try:
                # 讀取 JSON 數據
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                metadata = data.get('metadata', {})
                year = metadata.get('year')
                race_num = metadata.get('race')
                
                if not year or not race_num:
                    continue
                
                # 從 JSON 提取賽道名稱（使用 FP3 數據）
                fp3_data = data.get('practice_sessions', {}).get('FP3', {})
                race_name = fp3_data.get('session_info', {}).get('session_name', 'Unknown')
                
                # 簡化賽道名稱作為 key
                circuit_key = self._normalize_race_name(race_name, year, race_num)
                
                print(f"\n處理: {year} {circuit_key}", end=" ... ")
                
                # 從 JSON 提取賽道特徵
                features = self._extract_features_from_json(data, year, race_num)
                
                if features:
                    track_data_collection[circuit_key].append(features)
                    print(f"✅")
                    processed_count += 1
                else:
                    print(f"⚠️  無特徵數據")
                    error_count += 1
                    
            except Exception as e:
                print(f"❌ 讀取失敗: {json_file.name} - {str(e)[:50]}")
                error_count += 1
                continue
        
        # 聚合每個賽道的平均特徵
        print("\n" + "=" * 60)
        print("📊 聚合賽道特徵...")
        
        for circuit_key, feature_list in track_data_collection.items():
            self.track_features[circuit_key] = self._aggregate_features(feature_list)
        
        print(f"\n✅ 收集完成:")
        print(f"   - 成功處理: {processed_count} 場賽事")
        print(f"   - 錯誤: {error_count} 場")
        print(f"   - 獨特賽道: {len(self.track_features)} 個")
        
        return self.track_features
    
    def _normalize_race_name(self, race_name, year, race_num):
        """標準化賽道名稱"""
        # 簡單映射
        mapping = {
            'Bahrain': 'Bahrain', 'Saudi Arabia': 'Jeddah', 'Australia': 'Melbourne',
            'Azerbaijan': 'Baku', 'Miami': 'Miami', 'Monaco': 'Monaco',
            'Spain': 'Barcelona', 'Canada': 'Montreal', 'Austria': 'Spielberg',
            'Great Britain': 'Silverstone', 'Hungary': 'Budapest', 'Belgium': 'Spa',
            'Netherlands': 'Zandvoort', 'Italy': 'Monza', 'Singapore': 'Singapore',
            'Japan': 'Suzuka', 'Qatar': 'Lusail', 'United States': 'Austin',
            'Mexico': 'Mexico City', 'Brazil': 'Interlagos', 'Las Vegas': 'Las Vegas',
            'Abu Dhabi': 'Abu Dhabi', 'China': 'Shanghai', 'Emilia Romagna': 'Imola',
            'Dutch': 'Zandvoort'
        }
        
        for key, value in mapping.items():
            if key.lower() in race_name.lower():
                return value
        
        return f"{race_name}_{year}_{race_num}"
    
    def _extract_features_from_json(self, data, year, race_num):
        """
        從 JSON 提取賽道特徵（基於練習賽數據）
        
        Returns:
            dict: 賽道特徵
        """
        try:
            fp3_data = data.get('practice_sessions', {}).get('FP3', {})
            driver_data = fp3_data.get('driver_data', {})
            
            if not driver_data:
                return None
            
            # 收集所有車手的速度數據
            all_speeds = []
            all_best_laps = []
            all_speed_traps = []
            
            for driver, stats in driver_data.items():
                if 'speed_trap_max' in stats and stats['speed_trap_max']:
                    all_speed_traps.append(stats['speed_trap_max'])
                if 'best_lap_time' in stats and stats['best_lap_time']:
                    all_best_laps.append(stats['best_lap_time'])
            
            if not all_speed_traps or not all_best_laps:
                return None
            
            # 計算賽道特徵（基於速度陷阱和圈速）
            features = {
                'year': year,
                'race_num': race_num,
                
                # 速度特徵
                'avg_speed_trap': float(np.mean(all_speed_traps)),
                'max_speed_trap': float(np.max(all_speed_traps)),
                'min_speed_trap': float(np.min(all_speed_traps)),
                'speed_trap_std': float(np.std(all_speed_traps)),
                
                # 圈速特徵（反映賽道複雜度）
                'avg_best_lap': float(np.mean(all_best_laps)),
                'fastest_lap': float(np.min(all_best_laps)),
                'lap_time_spread': float(np.max(all_best_laps) - np.min(all_best_laps)),
                
                # 天氣數據（可能影響速度）
                'avg_air_temp': fp3_data.get('weather', {}).get('air_temp_avg', 0),
                'avg_track_temp': fp3_data.get('weather', {}).get('track_temp_avg', 0),
            }
            
            return features
            
        except Exception as e:
            print(f" 提取錯誤: {str(e)[:30]}")
            return None
    
    def _count_low_speed_sections(self, telemetry):
        """計算低速區段數量（< 100 km/h）"""
        low_speed = telemetry['Speed'] < 100
        # 檢測從高速到低速的轉換
        transitions = (low_speed.astype(int).diff() == 1).sum()
        return int(transitions)
    
    def _count_high_speed_sections(self, telemetry):
        """計算高速區段數量（> 250 km/h）"""
        high_speed = telemetry['Speed'] > 250
        transitions = (high_speed.astype(int).diff() == 1).sum()
        return int(transitions)
    
    def _count_brake_zones(self, telemetry):
        """計算煞車區數量（Brake > 0）"""
        if 'Brake' not in telemetry.columns:
            return 0
        
        braking = telemetry['Brake'] > 0
        transitions = (braking.astype(int).diff() == 1).sum()
        return int(transitions)
    
    def _calculate_full_throttle_percentage(self, telemetry):
        """計算全油門時間百分比"""
        if 'Throttle' not in telemetry.columns:
            return 0.0
        
        full_throttle = (telemetry['Throttle'] >= 99).sum()
        total_points = len(telemetry)
        return float(full_throttle / total_points * 100)
    
    def _aggregate_features(self, feature_list):
        """聚合多年同一賽道的特徵（取平均值）"""
        if len(feature_list) == 0:
            return {}
        
        # 計算所有數值特徵的平均值
        numeric_keys = ['avg_speed_trap', 'max_speed_trap', 'min_speed_trap', 
                       'speed_trap_std', 'avg_best_lap', 'fastest_lap',
                       'lap_time_spread', 'avg_air_temp', 'avg_track_temp']
        
        aggregated = {
            'sample_count': len(feature_list),
            'years': sorted(list(set([f['year'] for f in feature_list]))),
        }
        
        for key in numeric_keys:
            values = [f[key] for f in feature_list if key in f and f[key]]
            if values:
                aggregated[key] = float(np.mean(values))
        
        return aggregated
    
    def save_features(self, output_path="json/track_features.json"):
        """保存賽道特徵到 JSON"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'collection_date': datetime.now().isoformat(),
                    'total_tracks': len(self.track_features),
                    'data_source': 'FastF1 API via predictionJSON files'
                },
                'track_features': self.track_features
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 賽道特徵已保存到: {output_file}")
        return output_file
    
    def analyze_and_suggest_classification(self):
        """分析賽道特徵並建議分類方式"""
        print("\n" + "=" * 60)
        print("📊 賽道特徵分析與分類建議")
        print("=" * 60)
        
        if not self.track_features:
            print("❌ 無賽道特徵數據")
            return
        
        # 提取所有賽道的關鍵指標
        tracks_df = pd.DataFrame.from_dict(self.track_features, orient='index')
        
        print(f"\n📈 數據統計:")
        print(f"   賽道總數: {len(tracks_df)}")
        print(f"   特徵維度: {len(tracks_df.columns)}")
        
        # 關鍵指標分析
        print(f"\n🎯 關鍵指標分佈:")
        key_metrics = ['avg_speed', 'max_speed', 'low_speed_sections', 
                      'brake_zones', 'full_throttle_pct']
        
        for metric in key_metrics:
            if metric in tracks_df.columns:
                values = tracks_df[metric]
                print(f"\n   {metric}:")
                print(f"      平均: {values.mean():.2f}")
                print(f"      範圍: {values.min():.2f} - {values.max():.2f}")
                print(f"      標準差: {values.std():.2f}")
        
        # 建議分類策略
        print(f"\n💡 建議分類策略（基於數據分析）:")
        
        # 策略 1: 基於平均速度
        print(f"\n   策略 1: 基於平均速度")
        speed_q25 = tracks_df['avg_speed'].quantile(0.33)
        speed_q75 = tracks_df['avg_speed'].quantile(0.67)
        print(f"      低速賽道: avg_speed < {speed_q25:.1f} km/h")
        print(f"      中速賽道: {speed_q25:.1f} ≤ avg_speed < {speed_q75:.1f} km/h")
        print(f"      高速賽道: avg_speed ≥ {speed_q75:.1f} km/h")
        
        # 策略 2: 基於全油門百分比
        print(f"\n   策略 2: 基於全油門時間")
        throttle_q25 = tracks_df['full_throttle_pct'].quantile(0.33)
        throttle_q75 = tracks_df['full_throttle_pct'].quantile(0.67)
        print(f"      技術型: full_throttle < {throttle_q25:.1f}%")
        print(f"      平衡型: {throttle_q25:.1f}% ≤ full_throttle < {throttle_q75:.1f}%")
        print(f"      動力型: full_throttle ≥ {throttle_q75:.1f}%")
        
        # 策略 3: K-Means 聚類
        print(f"\n   策略 3: K-Means 自動聚類")
        print(f"      使用特徵: avg_speed, full_throttle_pct, brake_zones")
        print(f"      建議分為 3-4 類")
        
        return tracks_df


def main():
    """主函數"""
    print("🏎️  F1 賽道特徵收集器")
    print("=" * 60)
    print("目的: 基於真實數據收集賽道特徵，用於賽道分類建模")
    print("數據來源: json/predictionJSON/ (133 場賽事)")
    print("=" * 60)
    
    # 創建收集器
    collector = TrackFeatureCollector()
    
    # 收集所有賽道特徵
    track_features = collector.collect_all_tracks()
    
    # 保存結果
    if track_features:
        collector.save_features()
        
        # 分析並建議分類
        tracks_df = collector.analyze_and_suggest_classification()
        
        # 顯示前幾個賽道作為範例
        print(f"\n📋 賽道範例（前 5 個）:")
        print("=" * 60)
        for i, (track, features) in enumerate(list(track_features.items())[:5], 1):
            print(f"\n{i}. {track}")
            print(f"   平均速度: {features.get('avg_speed', 0):.1f} km/h")
            print(f"   最高速度: {features.get('max_speed', 0):.1f} km/h")
            print(f"   全油門: {features.get('full_throttle_pct', 0):.1f}%")
            print(f"   低速彎: {features.get('low_speed_sections', 0)} 個")
            print(f"   煞車區: {features.get('brake_zones', 0)} 個")
        
        print("\n" + "=" * 60)
        print("✅ 賽道特徵收集完成！")
        print("📄 結果檔案: json/track_features.json")
        print("\n💡 下一步: 根據分析結果決定分類策略")
        print("   1. 查看 track_features.json")
        print("   2. 選擇分類策略（速度/油門/聚類）")
        print("   3. 執行功能 73 訓練分類模型")
    else:
        print("\n❌ 未收集到賽道特徵")


if __name__ == "__main__":
    main()
