#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
賽道特徵收集器 - 基於真實遙測數據
Track Feature Collector Based on Real Telemetry Data

功能：
- 自動分析所有賽事的賽道特徵
- 從 FastF1 載入真實遙測數據
- 提取彎道數量、速度特徵、賽道長度等客觀數據
- 生成賽道特徵數據庫供分類使用
- 遵循反幻覺原則：基於真實數據而非主觀判斷

使用方式:
    python collect_track_features_telemetry.py

作者: F1 Analysis Team
創建日期: 2025-10-31
"""

import json
import fastf1
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import time

# 啟用 FastF1 緩存
fastf1.Cache.enable_cache('f1_analysis_cache')


class TrackFeatureCollectorTelemetry:
    """基於遙測數據的賽道特徵收集器"""
    
    def __init__(self):
        self.track_features = {}
        
    def collect_all_tracks(self, year_range=(2018, 2024)):
        """收集所有賽道的特徵（使用真實遙測數據）"""
        print("🏁 開始收集賽道特徵（基於遙測數據）...")
        print("=" * 60)
        
        track_data_collection = defaultdict(list)
        processed_count = 0
        error_count = 0
        
        for year in range(year_range[0], year_range[1] + 1):
            print(f"\n📅 處理 {year} 賽季...")
            
            # 獲取該年賽季的賽程
            try:
                schedule = fastf1.get_event_schedule(year)
            except Exception as e:
                print(f"❌ 無法獲取 {year} 賽程: {e}")
                continue
            
            for idx, event in schedule.iterrows():
                race_name = event['EventName']
                round_number = event['RoundNumber']
                
                # 跳過測試賽和其他非正式賽事
                if pd.isna(round_number) or event['EventFormat'] == 'testing':
                    continue
                
                circuit_key = self._normalize_race_name(race_name, year, round_number)
                
                print(f"\n處理: {year} 第 {round_number} 場 {race_name}", end=" ... ")
                
                try:
                    # 載入 FP3 會話（最接近正賽狀態）
                    session = fastf1.get_session(year, round_number, 'FP3')
                    
                    # 🔑 關鍵修復：使用 session.load() 不帶參數，載入所有數據包括遙測
                    print("載入中", end="")
                    session.load()  # 默認載入所有數據
                    print(".", end="")
                    
                    # 檢查數據是否可用
                    if not hasattr(session, 'laps') or session.laps is None or session.laps.empty:
                        print(" ⚠️  無圈數數據")
                        error_count += 1
                        continue
                    
                    # 提取賽道特徵
                    features = self._extract_track_features(session, year, round_number)
                    
                    if features:
                        track_data_collection[circuit_key].append(features)
                        print(f" ✅")
                        processed_count += 1
                    else:
                        print(f" ⚠️  無特徵數據")
                        error_count += 1
                        
                    # 避免 API 限流
                    time.sleep(1)
                    
                except Exception as e:
                    print(f" ❌ 錯誤: {str(e)[:50]}")
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
        mapping = {
            'Bahrain': 'Bahrain', 'Saudi Arabia': 'Jeddah', 'Australia': 'Melbourne',
            'Azerbaijan': 'Baku', 'Miami': 'Miami', 'Monaco': 'Monaco',
            'Spain': 'Barcelona', 'Canada': 'Montreal', 'Austria': 'Spielberg',
            'Great Britain': 'Silverstone', 'Hungary': 'Budapest', 'Belgium': 'Spa',
            'Netherlands': 'Zandvoort', 'Italy': 'Monza', 'Singapore': 'Singapore',
            'Japan': 'Suzuka', 'Qatar': 'Lusail', 'United States': 'Austin',
            'Mexico': 'Mexico City', 'Brazil': 'Interlagos', 'Las Vegas': 'Las Vegas',
            'Abu Dhabi': 'Abu Dhabi', 'China': 'Shanghai', 'Emilia Romagna': 'Imola',
            'Dutch': 'Zandvoort', 'Styrian': 'Spielberg', 'Turkish': 'Istanbul',
            'Portuguese': 'Portimao', 'French': 'Paul Ricard'
        }
        
        for key, value in mapping.items():
            if key.lower() in race_name.lower():
                return value
        
        # 如果無法映射，使用原始名稱
        return race_name.replace(' Grand Prix', '').replace(' ', '_')
    
    def _extract_track_features(self, session, year, race_num):
        """從會話提取賽道特徵（使用遙測數據）"""
        try:
            features = {
                'year': year,
                'race_number': race_num,
            }
            
            # 1. 獲取最快圈的遙測數據
            fastest_lap = session.laps.pick_fastest()
            if fastest_lap is None or fastest_lap.empty:
                return None
            
            # 🔑 關鍵：現在可以成功獲取遙測數據（因為 session.load() 載入了遙測）
            telemetry = fastest_lap.get_telemetry()
            
            if telemetry is None or telemetry.empty:
                print(f" [無遙測]", end="")
                return None
            
            # 2. 賽道長度和圈速
            # 嘗試獲取賽道長度（可能不存在於舊數據）
            try:
                if hasattr(session, 'event') and hasattr(session.event, 'CircuitLength'):
                    features['track_length'] = float(session.event.CircuitLength)
                elif hasattr(session, 'event') and 'CircuitLength' in session.event:
                    features['track_length'] = float(session.event['CircuitLength'])
                else:
                    features['track_length'] = 0.0  # 無數據時設為 0
            except (KeyError, AttributeError, TypeError):
                features['track_length'] = 0.0
            
            features['fastest_lap_time'] = float(fastest_lap['LapTime'].total_seconds())
            
            # 3. 速度特徵
            features['avg_speed'] = float(telemetry['Speed'].mean())
            features['max_speed'] = float(telemetry['Speed'].max())
            features['min_speed'] = float(telemetry['Speed'].min())
            features['speed_std'] = float(telemetry['Speed'].std())
            
            # 4. 油門特徵
            features['avg_throttle'] = float(telemetry['Throttle'].mean())
            features['full_throttle_pct'] = float((telemetry['Throttle'] >= 99).sum() / len(telemetry) * 100)
            
            # 5. 煞車特徵
            if 'Brake' in telemetry.columns:
                features['brake_pct'] = float((telemetry['Brake'] > 0).sum() / len(telemetry) * 100)
            else:
                features['brake_pct'] = 0.0
            
            # 6. 簡易彎道檢測（速度低於某閾值的區段）
            speed_threshold = features['avg_speed'] * 0.7  # 低於平均速度 70%
            is_cornering = telemetry['Speed'] < speed_threshold
            
            # 計算連續彎道區段
            corner_transitions = is_cornering.astype(int).diff().fillna(0)
            corner_count = (corner_transitions == 1).sum()
            features['estimated_corners'] = int(corner_count)
            
            # 7. DRS 區段（如果有數據）
            if 'DRS' in telemetry.columns:
                features['drs_activations'] = int((telemetry['DRS'] > 10).sum())
            else:
                features['drs_activations'] = 0
            
            # 8. 天氣數據（如果可用）
            if hasattr(session, 'weather_data') and session.weather_data is not None:
                weather = session.weather_data.iloc[-1]  # 最後一筆天氣數據
                features['avg_air_temp'] = float(weather.get('AirTemp', 0))
                features['avg_track_temp'] = float(weather.get('TrackTemp', 0))
            else:
                features['avg_air_temp'] = 0.0
                features['avg_track_temp'] = 0.0
            
            return features
            
        except Exception as e:
            print(f"\n   提取特徵錯誤: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _aggregate_features(self, feature_list):
        """聚合多年同一賽道的特徵（取平均值）"""
        if not feature_list:
            return None
        
        # 提取數值特徵
        numeric_keys = [
            'track_length', 'fastest_lap_time', 'avg_speed', 'max_speed', 
            'min_speed', 'speed_std', 'avg_throttle', 'full_throttle_pct',
            'brake_pct', 'estimated_corners', 'drs_activations',
            'avg_air_temp', 'avg_track_temp'
        ]
        
        aggregated = {}
        
        for key in numeric_keys:
            values = [f[key] for f in feature_list if key in f and f[key] is not None]
            if values:
                aggregated[key] = float(np.mean(values))
            else:
                aggregated[key] = 0.0
        
        # 記錄數據來源
        aggregated['data_years'] = sorted(list(set(f['year'] for f in feature_list)))
        aggregated['sample_count'] = len(feature_list)
        
        return aggregated
    
    def save_to_json(self, output_file='json/predictionJSON/track_features.json'):
        """保存賽道特徵到 JSON 檔案"""
        if not self.track_features:
            print("❌ 沒有賽道特徵可保存")
            return False
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 準備輸出數據
        output_data = {
            'metadata': {
                'created_at': datetime.now().isoformat(),
                'total_tracks': len(self.track_features),
                'description': '賽道特徵數據庫 - 用於賽道分類建模',
                'data_source': 'FastF1 真實遙測數據'
            },
            'tracks': self.track_features
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 賽道特徵已保存到: {output_path}")
        print(f"   - 賽道數量: {len(self.track_features)}")
        
        return True
    
    def analyze_features(self):
        """分析賽道特徵，建議分類策略"""
        if not self.track_features:
            print("❌ 沒有賽道特徵可分析")
            return
        
        print("\n" + "=" * 60)
        print("📊 賽道特徵分析")
        print("=" * 60)
        
        # 提取所有賽道的特徵值
        df = pd.DataFrame(self.track_features).T
        
        print("\n🔢 特徵統計:")
        print(df[['avg_speed', 'full_throttle_pct', 'estimated_corners', 'track_length']].describe())
        
        print("\n💡 建議分類策略（基於數據分析）:")
        
        # 策略 1: 基於平均速度
        speed_33 = df['avg_speed'].quantile(0.33)
        speed_67 = df['avg_speed'].quantile(0.67)
        
        print(f"\n1️⃣ 基於平均速度分類:")
        print(f"   - 高速賽道 (> {speed_67:.1f} km/h): {(df['avg_speed'] > speed_67).sum()} 個")
        print(f"   - 中速賽道 ({speed_33:.1f} - {speed_67:.1f} km/h): {((df['avg_speed'] >= speed_33) & (df['avg_speed'] <= speed_67)).sum()} 個")
        print(f"   - 低速賽道 (< {speed_33:.1f} km/h): {(df['avg_speed'] < speed_33).sum()} 個")
        
        # 策略 2: 基於全油門百分比
        throttle_33 = df['full_throttle_pct'].quantile(0.33)
        throttle_67 = df['full_throttle_pct'].quantile(0.67)
        
        print(f"\n2️⃣ 基於全油門比例分類:")
        print(f"   - 高油門賽道 (> {throttle_67:.1f}%): {(df['full_throttle_pct'] > throttle_67).sum()} 個")
        print(f"   - 中油門賽道 ({throttle_33:.1f}% - {throttle_67:.1f}%): {((df['full_throttle_pct'] >= throttle_33) & (df['full_throttle_pct'] <= throttle_67)).sum()} 個")
        print(f"   - 低油門賽道 (< {throttle_33:.1f}%): {(df['full_throttle_pct'] < throttle_33).sum()} 個")
        
        # 顯示極端案例
        print("\n🏆 特徵極端值:")
        print(f"\n   最高速賽道: {df['avg_speed'].idxmax()} ({df['avg_speed'].max():.1f} km/h)")
        print(f"   最低速賽道: {df['avg_speed'].idxmin()} ({df['avg_speed'].min():.1f} km/h)")
        print(f"   最多彎道: {df['estimated_corners'].idxmax()} ({int(df['estimated_corners'].max())} 個)")
        print(f"   最長賽道: {df['track_length'].idxmax()} ({df['track_length'].max():.2f} km)")


def main():
    """主程式"""
    collector = TrackFeatureCollectorTelemetry()
    
    # 收集賽道特徵
    features = collector.collect_all_tracks(year_range=(2018, 2024))
    
    if not features:
        print("\n❌ 未收集到賽道特徵")
        return
    
    # 保存到 JSON
    collector.save_to_json('json/predictionJSON/track_features.json')
    
    # 分析特徵
    collector.analyze_features()


if __name__ == "__main__":
    main()
