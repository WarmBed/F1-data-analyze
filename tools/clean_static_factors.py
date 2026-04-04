import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

# 定義已知的濕地場次 (年份-賽道)
# 這些場次的 Q 或 FP2 是濕地，導致時間無法比較
KNOWN_WET_SESSIONS = [
    # 2021 (Spa 是極端例子)
    "2021_Belgium", "2021_Russia", "2021_Turkey",
    # 2022
    "2022_Canada", "2022_Great Britain", "2022_Singapore", "2022_Japan", "2022_Brazil",
    # 2023
    "2023_Canada", "2023_Austria", "2023_Belgium", "2023_Netherlands",
    # 2024
    "2024_Canada", "2024_Great Britain", "2024_Belgium", "2024_Brazil"
]

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(data, path):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"✅ 已保存: {path}")

def clean_static_factors():
    base_dir = Path(__file__).parent.parent
    training_data_dir = base_dir / "training_data"
    
    print("🧹 開始清洗靜態因子數據 (排除濕地場次)...")
    print(f"已知濕地場次 ({len(KNOWN_WET_SESSIONS)}): {KNOWN_WET_SESSIONS}")
    
    # 1. 載入訓練數據以重新計算因子
    train_file = training_data_dir / "fp2_q_training_data_2022_2025.json"
    if not train_file.exists():
        print("❌ 找不到訓練數據文件")
        return
        
    training_data = load_json(train_file)
    print(f"載入 {len(training_data)} 筆原始訓練記錄")
    
    # 過濾濕地數據
    clean_data = []
    skipped_count = 0
    
    for record in training_data:
        # 獲取年份和賽道
        metadata = record.get('metadata', {})
        year = metadata.get('year')
        race = metadata.get('race') or record.get('track')
        
        if not year or not race:
            continue
            
        key = f"{year}_{race}"
        
        # 檢查是否為已知濕地場次
        if key in KNOWN_WET_SESSIONS:
            skipped_count += 1
            continue
            
        # 檢查數據本身是否異常 (Q 比 FP2 慢超過 5%)
        # 這通常意味著 FP2 乾地但 Q 濕地
        try:
            # 嘗試解析數據
            if 'fp2' in record and 'qualifying' in record:
                # 新格式
                fp2_drivers = record['fp2'].get('drivers', {})
                q_results = record['qualifying'].get('results', {})
                
                valid_diffs = []
                for driver, fp2_d in fp2_drivers.items():
                    if driver in q_results:
                        fp2_time = fp2_d.get('fastest_lap', 0)
                        
                        # 解析 Q 時間
                        q_obj = q_results[driver]
                        q_time_str = q_obj.get('q3_time') or q_obj.get('q2_time') or q_obj.get('q1_time')
                        
                        if fp2_time > 0 and q_time_str:
                            # 簡單解析
                            import re
                            match = re.search(r'(\d+):(\d+):(\d+\.?\d*)', str(q_time_str))
                            if match:
                                h, m, s = match.groups()
                                q_time = int(h) * 3600 + int(m) * 60 + float(s)
                                
                                # 如果 Q 比 FP2 慢超過 5s，視為異常 (除非是超長賽道)
                                diff = q_time - fp2_time
                                valid_diffs.append(diff)
                
                if valid_diffs and np.mean(valid_diffs) > 5.0:
                    print(f"⚠️  檢測到異常慢的 Q 場次 (可能濕地): {year} {race}, 平均慢 {np.mean(valid_diffs):.2f}s")
                    skipped_count += 1
                    continue
        except:
            pass
            
        clean_data.append(record)
        
    print(f"已過濾 {skipped_count} 筆濕地/異常場次，剩餘 {len(clean_data)} 筆乾地數據")
    
    # 1.5 保存清洗後的訓練數據 (v4.0 新增)
    cleaned_train_file = training_data_dir / "fp2_q_training_data_cleaned.json"
    save_json(clean_data, cleaned_train_file)
    print(f"✅ 已保存清洗後的訓練數據: {cleaned_train_file}")
    
    # 2. 重新計算 Track Adjustment
    print("\n🔄 重新計算 Track Adjustment Factors...")
    recalculate_track_factors(clean_data, training_data_dir)
    
    # 3. 重新計算 Evolution Factors
    print("\n🔄 重新計算 Evolution Factors...")
    recalculate_evolution_factors(clean_data, training_data_dir)

def recalculate_track_factors(clean_data, output_dir):
    # 計算每個賽場的平均 improvement (FP2 -> Q)
    track_diffs = {}
    all_diffs = []
    
    for record in clean_data:
        metadata = record.get('metadata', {})
        race = metadata.get('race') or record.get('track')
        
        # 提取這場比賽的所有車手 improvement
        race_diffs = []
        
        # 嘗試 Format 1: 舊版直接格式 (fp2_best_lap, q_best_lap)
        if 'fp2_best_lap' in record and 'q_best_lap' in record:
            fp2_data = record['fp2_best_lap']
            q_data = record['q_best_lap']
            
            fp2_time = fp2_data.get('ideal_lap', 0.0)
            q_time = q_data.get('ideal_lap', 0.0)
            
            if fp2_time > 0 and q_time > 0:
                imp = fp2_time - q_time
                race_diffs.append(imp)
                all_diffs.append(imp)
        
        # 嘗試 Format 2 & 3: 嵌套格式
        else:
            fp2_drivers = {}
            q_results = {}
            
            # Format 2: fp2.drivers
            if 'fp2' in record:
                fp2_drivers = record['fp2'].get('drivers', {})
            # Format 3: practice_sessions.FP2.driver_data
            elif 'practice_sessions' in record:
                fp2_drivers = record['practice_sessions'].get('FP2', {}).get('driver_data', {})
                
            if 'qualifying' in record:
                q_results = record['qualifying'].get('results', {})
                
            if fp2_drivers and q_results:
                for driver, fp2_d in fp2_drivers.items():
                    if driver in q_results:
                        # 嘗試獲取 FP2 時間
                        fp2_time = fp2_d.get('fastest_lap', 0)
                        if fp2_time == 0:
                            fp2_time = fp2_d.get('ideal_lap', 0)
                        
                        # 解析 Q 時間
                        q_obj = q_results[driver]
                        q_time = 0
                        q_time_str = q_obj.get('q3_time') or q_obj.get('q2_time') or q_obj.get('q1_time')
                        
                        if fp2_time > 0 and q_time_str:
                            try:
                                # 格式可能是 float (seconds) 或 string "1:30.123"
                                if isinstance(q_time_str, (int, float)):
                                    q_time = float(q_time_str)
                                else:
                                    import re
                                    match = re.search(r'(\d+):(\d+):(\d+\.?\d*)', str(q_time_str))
                                    if match:
                                        h, m, s = match.groups()
                                        q_time = int(h) * 3600 + int(m) * 60 + float(s)
                            except:
                                pass
                                
                            if q_time > 0:
                                imp = fp2_time - q_time
                                race_diffs.append(imp)
                                all_diffs.append(imp)
        
        if race_diffs:
            if race not in track_diffs:
                track_diffs[race] = []
            track_diffs[race].extend(race_diffs)
            
    global_mean_improvement = np.mean(all_diffs)
    print(f"全局平均進步 (Global Mean Improvement): {global_mean_improvement:.3f}s")
    
    output_factors = {}
    for race, diffs in track_diffs.items():
        track_mean = np.mean(diffs)
        # 偏差 = 全局平均 - 賽道平均
        # 如果賽道進步很多 (e.g. 3s)，全局 (2s)
        # 偏差 = 2 - 3 = -1s
        # 預測時間 += (-1) -> 變快 1s。正確。
        adjustment = global_mean_improvement - track_mean
        
        output_factors[race] = {
            "track_adjustment": adjustment,
            "mean_improvement": track_mean,
            "sample_count": len(diffs)
        }
        print(f"  {race}: Avg Imp {track_mean:.3f}s, Adj {adjustment:+.3f}s")
        
    # 保存
    full_output = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "description": "Track-specific adjustment factors calculated from CLEAN dry races only",
            "global_mean_improvement": global_mean_improvement,
            "wet_races_excluded": True
        },
        "track_factors": output_factors
    }
    
    save_json(full_output, output_dir / "track_adjustment_factors.json")

def recalculate_evolution_factors(clean_data, output_dir):
    # 這裡可以實作類似邏輯，計算 Q1 -> Q3 的演進
    # 暫時簡單生成一個空的或基於上面數據的
    # 目前代碼主要依賴 track_adjustment，evolution 是次要
    pass

if __name__ == "__main__":
    clean_static_factors()
