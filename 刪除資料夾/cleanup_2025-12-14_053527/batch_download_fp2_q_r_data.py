#!/usr/bin/env python3
"""
批量下載 FP2+Q+R 數據 (2022-2024)
用於 FP2+Q→R 混合預測模型訓練

工作流程:
1. 下載 2022-2024 年所有賽事的 FP2 數據
2. 下載對應的 Q (排位賽) 數據
3. 下載對應的 R (正賽) 數據
4. 整合為訓練數據集
"""

import os
import sys
import json
import fastf1
from pathlib import Path
from datetime import datetime

# 添加專案根目錄
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from CLI_modules.cli.prediction.race_calendar import get_races_for_year

# 啟用緩存
cache_dir = project_root / "f1_analysis_cache"
fastf1.Cache.enable_cache(str(cache_dir))

def collect_fp2_q_r_data(year: int, race_name: str):
    """
    收集單場賽事的 FP2+Q+R 數據
    
    Args:
        year: 賽季年份
        race_name: 賽事名稱
        
    Returns:
        包含 FP2, Q, R 數據的字典
    """
    print(f"\n{'='*70}")
    print(f"📊 收集: {year} {race_name}")
    print(f"{'='*70}")
    
    data = {
        "metadata": {
            "year": year,
            "race": race_name,
            "collection_timestamp": datetime.now().isoformat()
        },
        "fp2": None,
        "qualifying": None,
        "race": None
    }
    
    try:
        # 1. 載入 FP2 數據
        print("\n[1/3] 載入 FP2 數據...")
        try:
            fp2_session = fastf1.get_session(year, race_name, 'FP2')
            fp2_session.load()
            
            if fp2_session.laps is not None and len(fp2_session.laps) > 0:
                data["fp2"] = extract_fp2_features(fp2_session)
                print(f"✅ FP2: {len(data['fp2']['drivers'])} 位車手")
            else:
                print("⚠️  FP2 無有效數據")
                return None
        except Exception as e:
            print(f"❌ FP2 載入失敗: {str(e)[:100]}")
            return None
        
        # 2. 載入 Q 數據
        print("\n[2/3] 載入 Q 數據...")
        try:
            q_session = fastf1.get_session(year, race_name, 'Q')
            q_session.load()
            
            if q_session.results is not None and len(q_session.results) > 0:
                data["qualifying"] = extract_qualifying_results(q_session)
                print(f"✅ Q: {len(data['qualifying']['results'])} 位車手")
            else:
                print("⚠️  Q 無有效數據")
                return None
        except Exception as e:
            print(f"❌ Q 載入失敗: {str(e)[:100]}")
            return None
        
        # 3. 載入 R 數據
        print("\n[3/3] 載入 R 數據...")
        try:
            r_session = fastf1.get_session(year, race_name, 'R')
            r_session.load()
            
            if r_session.results is not None and len(r_session.results) > 0:
                data["race"] = extract_race_results(r_session)
                print(f"✅ R: {len(data['race']['results'])} 位車手")
            else:
                print("⚠️  R 無有效數據")
                return None
        except Exception as e:
            print(f"❌ R 載入失敗: {str(e)[:100]}")
            return None
        
        print(f"\n✅ {year} {race_name} 數據收集完成")
        return data
        
    except Exception as e:
        print(f"\n❌ 收集失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def extract_fp2_features(fp2_session):
    """提取 FP2 特徵 (v3.10 架構)"""
    import pandas as pd
    import numpy as np
    
    fp2_data = {
        "session_info": {
            "session_name": fp2_session.name,
            "date": fp2_session.date.isoformat() if hasattr(fp2_session.date, 'isoformat') else str(fp2_session.date)
        },
        "drivers": {}
    }
    
    for driver in fp2_session.laps['Driver'].unique():
        driver_laps = fp2_session.laps.pick_driver(driver)
        
        # 過濾有效圈速
        valid_laps = driver_laps[(driver_laps['LapTime'].notna()) & (driver_laps['IsAccurate'] == True)]
        
        if len(valid_laps) == 0:
            continue
        
        # 找到最快圈
        fastest_lap = valid_laps.loc[valid_laps['LapTime'].idxmin()]
        lap_time = fastest_lap['LapTime'].total_seconds()
        
        # 提取扇區時間
        try:
            s1 = fastest_lap['Sector1Time'].total_seconds() if pd.notna(fastest_lap['Sector1Time']) else lap_time / 3
            s2 = fastest_lap['Sector2Time'].total_seconds() if pd.notna(fastest_lap['Sector2Time']) else lap_time / 3
            s3 = fastest_lap['Sector3Time'].total_seconds() if pd.notna(fastest_lap['Sector3Time']) else lap_time / 3
        except:
            s1, s2, s3 = lap_time / 3, lap_time / 3, lap_time / 3
        
        # 提取速度數據
        try:
            telemetry = fastest_lap.get_telemetry()
            speeds = telemetry['Speed'].values
            max_speed = float(speeds.max())
            avg_speed = float(speeds.mean())
            speed_std = float(speeds.std())
            low_speed_apex = float(np.percentile(speeds, 25))
            mid_speed_apex = float(np.percentile(speeds, 50))
            high_speed_apex = float(np.percentile(speeds, 75))
        except:
            max_speed = 300.0
            avg_speed = 250.0
            speed_std = 10.0
            low_speed_apex = 200.0
            mid_speed_apex = 250.0
            high_speed_apex = 280.0
        
        # v3.10 特徵
        fp2_data["drivers"][driver] = {
            "team": fastest_lap.get('Team', 'Unknown'),
            "ideal_s1": s1,
            "ideal_s2": s2,
            "ideal_s3": s3,
            "ideal_lap": lap_time,
            "low_speed_apex": low_speed_apex,
            "mid_speed_apex": mid_speed_apex,
            "high_speed_apex": high_speed_apex,
            "max_speed": max_speed,
            "s1_s2_ratio": s1 / s2 if s2 > 0 else 1.0,
            "sector_cv": speed_std / avg_speed if avg_speed > 0 else 0.1,
            "s2_lap_ratio": s2 / lap_time if lap_time > 0 else 0.33,
            "max_speed_lap_ratio": max_speed * lap_time / 1000 if lap_time > 0 else 20.0,
            "max_speed_s2_ratio": max_speed / s2 if s2 > 0 else 10.0,
            "speed_consistency": 1.0 - (speed_std / avg_speed) if avg_speed > 0 else 0.9,
        }
    
    # 計算相對排名特徵
    sorted_drivers = sorted(fp2_data["drivers"].items(), key=lambda x: x[1]["ideal_lap"])
    fastest_fp2 = sorted_drivers[0][1]["ideal_lap"]
    
    for i, (driver, data_dict) in enumerate(sorted_drivers):
        fp2_data["drivers"][driver]["fp2_relative_position"] = (i + 1) / len(sorted_drivers)
        fp2_data["drivers"][driver]["fp2_gap_to_fastest"] = data_dict["ideal_lap"] - fastest_fp2
    
    return fp2_data

def extract_qualifying_results(q_session):
    """提取排位賽結果"""
    import pandas as pd
    
    q_data = {
        "session_info": {
            "event_name": q_session.event['EventName'],
            "circuit": q_session.event['Location'],
            "date": q_session.date.isoformat() if hasattr(q_session.date, 'isoformat') else str(q_session.date)
        },
        "results": {}
    }
    
    for idx, row in q_session.results.iterrows():
        driver = row['Abbreviation']
        
        q_data["results"][driver] = {
            "grid_position": int(row['Position']) if pd.notna(row['Position']) else None,
            "q1_time": str(row['Q1']) if pd.notna(row['Q1']) else None,
            "q2_time": str(row['Q2']) if pd.notna(row['Q2']) else None,
            "q3_time": str(row['Q3']) if pd.notna(row['Q3']) else None,
            "team": row['TeamName']
        }
    
    return q_data

def extract_race_results(r_session):
    """提取正賽結果"""
    import pandas as pd
    
    r_data = {
        "session_info": {
            "event_name": r_session.event['EventName'],
            "date": r_session.date.isoformat() if hasattr(r_session.date, 'isoformat') else str(r_session.date)
        },
        "results": {}
    }
    
    for idx, row in r_session.results.iterrows():
        driver = row['Abbreviation']
        
        r_data["results"][driver] = {
            "finish_position": int(row['Position']) if pd.notna(row['Position']) else None,
            "grid_position": int(row['GridPosition']) if pd.notna(row['GridPosition']) else None,
            "points": float(row['Points']) if pd.notna(row['Points']) else 0.0,
            "status": row['Status'],
            "team": row['TeamName']
        }
    
    return r_data

def main():
    """批量下載 2022-2024 年數據"""
    print("🏎️  F1T FP2+Q→R 數據批量下載")
    print("="*70)
    print("目標: 2022-2024 年所有賽事")
    print("數據: FP2 特徵 + Q 排位 + R 正賽")
    print("="*70)
    
    # 輸出目錄
    output_dir = project_root / "training_data" / "fp2_q_r"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_data = []
    total_success = 0
    total_failed = 0
    
    for year in [2022, 2023, 2024]:
        print(f"\n{'#'*70}")
        print(f"# 處理賽季: {year}")
        print(f"{'#'*70}")
        
        # 獲取該年份的賽事列表
        races = get_races_for_year(year)
        
        if not races:
            print(f"⚠️  {year} 年份沒有賽事數據")
            continue
        
        print(f"📅 {year} 賽季共 {len(races)} 場賽事")
        
        for idx, race_name in enumerate(races, 1):
            print(f"\n[{idx}/{len(races)}] 處理: {year} {race_name}")
            
            data = collect_fp2_q_r_data(year, race_name)
            
            if data:
                all_data.append(data)
                total_success += 1
                
                # 立即保存單場數據
                race_file = output_dir / f"fp2_q_r_{year}_{race_name.replace(' ', '_')}.json"
                with open(race_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                print(f"💾 已保存: {race_file.name}")
            else:
                total_failed += 1
                print(f"❌ 跳過: {year} {race_name}")
    
    # 保存整合數據
    if all_data:
        combined_file = output_dir / "fp2_q_r_training_data_2022_2024.json"
        with open(combined_file, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n{'='*70}")
        print("數據下載完成！")
        print(f"{'='*70}")
        print(f"✅ 成功: {total_success} 場賽事")
        print(f"❌ 失敗: {total_failed} 場賽事")
        print(f"📁 輸出目錄: {output_dir}")
        print(f"📦 整合檔案: {combined_file.name}")
        print(f"{'='*70}")
    else:
        print("\n❌ 沒有成功收集任何數據")

if __name__ == "__main__":
    main()
