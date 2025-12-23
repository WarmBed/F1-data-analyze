#!/usr/bin/env python3
"""
Function 78 特徵提取器 - 車手 FP3→Q 歷史關係特徵
根據 2022-2024 年 Mexico 賽道的 FP3 和 Q 數據，計算每個車手的歷史改進模式

輸出: json/driver_fp3_q_features_Mexico.json

特徵說明:
1. driver_avg_fp3_to_q_delta: 平均 FP3→Q 時間差（秒）
2. driver_fp3_to_q_std: FP3→Q 改進的一致性（標準差）
3. driver_track_appearances: 該車手在 Mexico 的出賽次數
4. driver_best_delta: 該車手在 Mexico 的最佳改進幅度（秒）

作者: F1 Analysis Team
日期: 2025-11-03
版本: 1.0
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict
import statistics


class DriverFP3QFeatureExtractor:
    """車手 FP3→Q 特徵提取器"""
    
    def __init__(self, track_name: str = "Mexico"):
        self.track_name = track_name
        self.json_dir = Path("json")
        self.years = [2022, 2023, 2024]
        
        # 儲存每個車手的歷史資料
        self.driver_history = defaultdict(lambda: {
            'fp3_times': [],
            'q_times': [],
            'deltas': [],
            'appearances': 0
        })
    
    def load_session_data(self, year: int, session: str) -> Dict[str, Any]:
        """載入指定年份和賽段的 JSON 數據"""
        filename = f"all_drivers_cornering_analysis_{year}_{self.track_name}_{session}.json"
        filepath = self.json_dir / filename
        
        if not filepath.exists():
            print(f"⚠️  警告: 找不到檔案 {filename}")
            return None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"✅ 載入成功: {filename}")
        return data
    
    def extract_lap_times(self, data: Dict[str, Any]) -> Dict[str, float]:
        """從 JSON 數據中提取每個車手的 lap_time"""
        if not data or not data.get('success'):
            return {}
        
        lap_times = {}
        drivers_data = data.get('fastest_lap_analysis', {}).get('drivers', [])
        
        for driver_info in drivers_data:
            driver_code = driver_info.get('driver')
            lap_time = driver_info.get('lap_time')
            
            if driver_code and lap_time:
                lap_times[driver_code] = lap_time
        
        return lap_times
    
    def collect_historical_data(self):
        """收集 2022-2024 年的歷史數據"""
        print(f"\n🔍 開始收集 {self.track_name} 賽道 FP3→Q 歷史數據...")
        print(f"📅 年份範圍: {self.years[0]}-{self.years[-1]}")
        print("-" * 60)
        
        for year in self.years:
            print(f"\n📊 處理 {year} 年數據:")
            
            # 載入 FP3 和 Q 數據
            fp3_data = self.load_session_data(year, "FP3")
            q_data = self.load_session_data(year, "Q")
            
            if not fp3_data or not q_data:
                print(f"❌ {year} 年數據不完整，跳過")
                continue
            
            # 提取圈速
            fp3_times = self.extract_lap_times(fp3_data)
            q_times = self.extract_lap_times(q_data)
            
            print(f"   FP3 車手數: {len(fp3_times)}, Q 車手數: {len(q_times)}")
            
            # 計算每個車手的 delta
            matched_drivers = 0
            for driver in fp3_times:
                if driver in q_times:
                    fp3_time = fp3_times[driver]
                    q_time = q_times[driver]
                    delta = fp3_time - q_time  # 正值表示 Q 比 FP3 快
                    
                    self.driver_history[driver]['fp3_times'].append(fp3_time)
                    self.driver_history[driver]['q_times'].append(q_time)
                    self.driver_history[driver]['deltas'].append(delta)
                    self.driver_history[driver]['appearances'] += 1
                    
                    matched_drivers += 1
            
            print(f"   ✅ 成功匹配 {matched_drivers} 名車手的 FP3→Q 數據")
        
        print("\n" + "=" * 60)
        print(f"📈 總計收集到 {len(self.driver_history)} 名車手的歷史數據")
        return len(self.driver_history)
    
    def calculate_features(self) -> Dict[str, Dict[str, float]]:
        """計算每個車手的 4 個特徵"""
        print("\n🧮 開始計算車手特徵...")
        print("-" * 60)
        
        features = {}
        
        for driver, history in self.driver_history.items():
            deltas = history['deltas']
            appearances = history['appearances']
            
            if appearances == 0:
                continue
            
            # 特徵 1: 平均 FP3→Q 時間差
            avg_delta = statistics.mean(deltas)
            
            # 特徵 2: FP3→Q 改進的標準差（一致性）
            std_delta = statistics.stdev(deltas) if len(deltas) > 1 else 0.0
            
            # 特徵 3: 出賽次數
            track_appearances = appearances
            
            # 特徵 4: 最佳改進幅度
            best_delta = max(deltas)
            
            features[driver] = {
                'driver_avg_fp3_to_q_delta': round(avg_delta, 3),
                'driver_fp3_to_q_std': round(std_delta, 3),
                'driver_track_appearances': track_appearances,
                'driver_best_delta': round(best_delta, 3)
            }
            
            print(f"   {driver}: Δ={avg_delta:.3f}s, σ={std_delta:.3f}s, "
                  f"出賽={track_appearances}次, 最佳Δ={best_delta:.3f}s")
        
        print("-" * 60)
        print(f"✅ 成功計算 {len(features)} 名車手的特徵")
        return features
    
    def save_features(self, features: Dict[str, Dict[str, float]]):
        """將特徵儲存為 JSON 格式"""
        output_file = self.json_dir / f"driver_fp3_q_features_{self.track_name}.json"
        
        output_data = {
            "success": True,
            "function_id": "78",
            "track": self.track_name,
            "training_years": self.years,
            "feature_count": 4,
            "driver_count": len(features),
            "generated_at": "2025-11-03",
            "features": features,
            "feature_descriptions": {
                "driver_avg_fp3_to_q_delta": "平均 FP3→Q 時間差（秒），正值表示 Q 比 FP3 快",
                "driver_fp3_to_q_std": "FP3→Q 改進的標準差（秒），值越小表示越穩定",
                "driver_track_appearances": "該車手在此賽道的出賽次數",
                "driver_best_delta": "該車手在此賽道的最佳改進幅度（秒）"
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 特徵已儲存至: {output_file}")
        print(f"📄 檔案大小: {output_file.stat().st_size / 1024:.2f} KB")
    
    def run(self):
        """執行完整的特徵提取流程"""
        print("=" * 60)
        print("🏎️  Function 78: 車手 FP3→Q 特徵提取器")
        print("=" * 60)
        
        # 步驟 1: 收集歷史數據
        driver_count = self.collect_historical_data()
        
        if driver_count == 0:
            print("\n❌ 錯誤: 沒有收集到任何車手數據")
            return False
        
        # 步驟 2: 計算特徵
        features = self.calculate_features()
        
        if not features:
            print("\n❌ 錯誤: 無法計算特徵")
            return False
        
        # 步驟 3: 儲存特徵
        self.save_features(features)
        
        print("\n" + "=" * 60)
        print("✅ Function 78 執行完成！")
        print("=" * 60)
        return True


def main():
    """主函數"""
    extractor = DriverFP3QFeatureExtractor(track_name="Mexico")
    success = extractor.run()
    
    if success:
        print("\n🎉 特徵提取成功！現在可以使用這些特徵訓練模型。")
        print("💡 下一步: 執行 python f1_analysis_modular_main.py -f 77 --track Mexico --train")
    else:
        print("\n❌ 特徵提取失敗，請檢查錯誤訊息。")


if __name__ == "__main__":
    main()
