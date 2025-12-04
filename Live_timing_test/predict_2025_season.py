"""
使用 2023-2024 訓練的模型預測 2025 賽季

⚠️ 更新 2025-11-26:
- 移除硬編碼的車隊評級
- 改用動態評級系統 (DynamicTeamRating)
- 評級基於 2023-2024 歷史數據 + 2025 當前賽季結果
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import joblib
import sys

# 路徑設定
BASE_DIR = Path("c:/Users/mike2/OneDrive/Code/F1-data-analyze")
MODEL_PATH = BASE_DIR / "models/win_probability_2023_2024_trained.pkl"
JSON_DIR = BASE_DIR / "json"
OUTPUT_DIR = BASE_DIR / "docs"

# 確保可以導入動態評級模組
sys.path.insert(0, str(BASE_DIR / "Live_timing_test"))

# 導入動態評級系統
from dynamic_team_rating import DynamicTeamRating, get_rating_system

# 初始化動態評級系統
_rating_system: DynamicTeamRating = None

def get_team_rating_dynamic(team: str) -> float:
    """獲取動態車隊評級"""
    global _rating_system
    if _rating_system is None:
        _rating_system = DynamicTeamRating()
        _rating_system.load_historical_data()
        _rating_system.load_2025_results()
    return _rating_system.get_team_rating(team)

def get_driver_team_dynamic(driver_code: str) -> tuple:
    """獲取車手的車隊和評級"""
    global _rating_system
    if _rating_system is None:
        _rating_system = DynamicTeamRating()
        _rating_system.load_historical_data()
        _rating_system.load_2025_results()
    return _rating_system.get_driver_team_rating(driver_code)

# 車手到車隊映射 (作為後備)
DRIVER_TEAMS_2025 = {
    "VER": "Red Bull Racing",
    "TSU": "Red Bull Racing",
    "HAD": "Racing Bulls",  # Hadjar
    "LEC": "Ferrari",
    "HAM": "Ferrari",
    "NOR": "McLaren",
    "PIA": "McLaren",
    "RUS": "Mercedes",
    "ANT": "Mercedes",  # Antonelli
    "ALO": "Aston Martin",
    "STR": "Aston Martin",
    "GAS": "Alpine",
    "DOO": "Alpine",  # Doohan
    "ALB": "Williams",
    "SAI": "Williams",
    "LAW": "Racing Bulls",
    "BOT": "Kick Sauber",
    "BOR": "Kick Sauber",  # Bortoleto
    "OCO": "Haas F1 Team",
    "BEA": "Haas F1 Team",
    "HUL": "Haas F1 Team",
}

def load_qualifying_data():
    """載入 2025 排位賽數據"""
    qualifying_files = list(JSON_DIR.glob("qualifying_prediction_2025_*.json"))
    races = []
    
    for f in qualifying_files:
        race_name = f.stem.replace("qualifying_prediction_2025_", "")
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # 提取排位賽結果
        q_results = []
        for driver_data in data.get("predictions", []):
            q_rank = driver_data.get("actual_q_rank")
            if q_rank and q_rank <= 10:  # 只取前 10
                q_results.append({
                    "driver": driver_data.get("driver"),  # 修正: driver_code -> driver
                    "q_position": q_rank,
                    "team": driver_data.get("team", "Unknown")
                })
        
        if q_results:
            races.append({
                "race": race_name,
                "qualifying": sorted(q_results, key=lambda x: x["q_position"])
            })
    
    return races

def load_race_results():
    """載入 2025 正賽結果"""
    results = {}
    
    # 首先嘗試從手動整理的結果檔案載入
    manual_results_file = BASE_DIR / "json/historical_data/f1_2025_results.json"
    if manual_results_file.exists():
        with open(manual_results_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for race in data.get("races", []):
            race_name = race.get("race", "")
            winner = race.get("winner", "")
            r_top5 = race.get("r_top5", [])
            
            if race_name and r_top5:
                final_positions = {driver: i+1 for i, driver in enumerate(r_top5)}
                results[race_name] = final_positions
        
        print(f"  (從手動整理檔案載入 {len(results)} 場結果)")
        return results
    
    # 方法 1: 從 driver_race_position 檔案讀取
    race_position_files = list(JSON_DIR.glob("driver_race_position_2025_*_R.json"))
    for f in race_position_files:
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        race_name = data.get("race", "")
        if not race_name:
            continue
        
        # 提取完賽位置
        final_positions = {}
        all_drivers = data.get("all_drivers_position_analysis", {})
        for driver, info in all_drivers.items():
            finish_pos = info.get("finishing_position")
            if finish_pos and str(finish_pos).isdigit():
                final_positions[driver] = int(finish_pos)
        
        if final_positions:
            results[race_name] = final_positions
    
    # 方法 2: 從 ideal_lap_ranking 檔案讀取 (補充)
    ideal_lap_files = list(JSON_DIR.glob("ideal_lap_ranking_2025_*_R.json"))
    for f in ideal_lap_files:
        race_name = f.stem.replace("ideal_lap_ranking_2025_", "").replace("_R", "")
        if race_name in results:
            continue  # 已有數據
            
        with open(f, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # 從 ranking 提取
        ranking = data.get("data", {}).get("ranking", [])
        if not ranking:
            ranking = data.get("ranking", [])
        
        if ranking:
            final_positions = {}
            for i, entry in enumerate(ranking, 1):
                driver = entry.get("driver", entry.get("Driver", ""))
                if driver:
                    final_positions[driver] = i
            
            if final_positions:
                results[race_name] = final_positions
    
    return results

def predict_race(model, qualifying: list) -> list:
    """預測單場比賽的勝率"""
    predictions = []
    
    for driver in qualifying[:5]:  # 只預測前 5
        driver_code = driver["driver"]
        q_pos = driver["q_position"]
        
        # 使用動態評級系統
        team, team_rating = get_driver_team_dynamic(driver_code)
        
        # 如果動態系統找不到，使用後備映射
        if team == "Unknown":
            team = DRIVER_TEAMS_2025.get(driver_code, driver.get("team", "Unknown"))
            team_rating = get_team_rating_dynamic(team)
        
        # 準備特徵
        features = np.array([[
            q_pos,
            team_rating,
            1 if q_pos == 1 else 0,
            1 if q_pos <= 3 else 0,
            10 - q_pos
        ]])
        
        # 預測
        prob = model.predict_proba(features)[0][1]
        
        predictions.append({
            "driver": driver_code,
            "team": team,
            "q_position": q_pos,
            "win_probability": prob
        })
    
    # 按勝率排序
    predictions.sort(key=lambda x: x["win_probability"], reverse=True)
    return predictions

def generate_report(races: list, race_results: dict, model):
    """生成 2025 預測報告"""
    report = []
    report.append("# F1 2025 賽季勝率預測報告")
    report.append(f"\n**生成時間**: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"\n**模型訓練數據**: 2023-2024 賽季 (46 場比賽)")
    report.append("\n---\n")
    
    # 統計
    total_predictions = 0
    top1_correct = 0
    top3_correct = 0
    completed_races = 0
    
    report.append("## 各場比賽預測與結果\n")
    
    for race in sorted(races, key=lambda x: x["race"]):
        race_name = race["race"]
        qualifying = race["qualifying"]
        
        if not qualifying:
            continue
        
        # 預測
        predictions = predict_race(model, qualifying)
        
        # 查找實際結果
        actual_result = race_results.get(race_name, {})
        actual_winner = None
        for driver, pos in actual_result.items():
            if pos == 1:
                actual_winner = driver
                break
        
        # 計算準確率
        is_completed = actual_winner is not None
        if is_completed:
            completed_races += 1
            total_predictions += 1
            
            pred_winner = predictions[0]["driver"]
            if pred_winner == actual_winner:
                top1_correct += 1
            
            top3_predicted = [p["driver"] for p in predictions[:3]]
            if actual_winner in top3_predicted:
                top3_correct += 1
        
        # 輸出
        report.append(f"### {race_name}")
        report.append(f"\n**排位賽桿位**: {qualifying[0]['driver']}")
        
        if is_completed:
            report.append(f"\n**實際冠軍**: {actual_winner}")
            status = "✓" if predictions[0]["driver"] == actual_winner else "✗"
            report.append(f"\n**預測狀態**: {status}")
        else:
            report.append(f"\n**實際冠軍**: *未完賽*")
        
        report.append("\n| 預測排名 | 車手 | 車隊 | 排位 | 勝率 |")
        report.append("|---------|------|------|------|------|")
        
        for i, pred in enumerate(predictions, 1):
            driver = pred["driver"]
            marker = "**" if is_completed and driver == actual_winner else ""
            report.append(f"| {i} | {marker}{driver}{marker} | {pred['team']} | Q{pred['q_position']} | {pred['win_probability']:.1%} |")
        
        report.append("\n")
    
    # 總結
    report.append("---\n")
    report.append("## 模型準確率統計\n")
    
    if completed_races > 0:
        report.append(f"- **已完賽**: {completed_races} 場")
        report.append(f"- **Top-1 準確率**: {top1_correct}/{completed_races} = **{top1_correct/completed_races*100:.1f}%**")
        report.append(f"- **Top-3 準確率**: {top3_correct}/{completed_races} = **{top3_correct/completed_races*100:.1f}%**")
    else:
        report.append("*無已完賽數據*")
    
    report.append("\n---\n")
    report.append("## 模型說明\n")
    report.append("""
本模型使用 XGBoost 機器學習算法，基於以下特徵預測勝率：

1. **排位賽位置** (q_position) - 最重要特徵
2. **車隊評級** (team_rating) - 動態計算（見下方說明）
3. **是否桿位** (is_pole)
4. **是否前三** (is_top3)
5. **位置優勢** (position_advantage)

### 訓練數據
- 2023 賽季: 22 場比賽
- 2024 賽季: 24 場比賽
- 總計: 230 個訓練樣本

### 車隊評級計算方法 (動態評級系統)

**不再使用硬編碼評級！**

評級公式:
```
rating = (win_rate × 4) + (pole_rate × 2) + (podium_rate × 2) + (normalized_points × 2)
```

評級來源:
- **基準評級**: 2023-2024 歷史統計（46 場比賽）
- **當前評級**: 2025 賽季累積結果
- **加權方式**: 隨賽季進行，當前賽季權重逐漸提高

### 歷史統計
- 桿位奪冠率: 56.5% (26/46)
- VER 統治力: 25 勝 (2023-2024)
""")
    
    return "\n".join(report)

def main():
    print("="*60)
    print("F1 2025 賽季勝率預測")
    print("使用 2023-2024 訓練模型")
    print("="*60)
    
    # 載入模型
    model = joblib.load(MODEL_PATH)
    print(f"✓ 模型已載入: {MODEL_PATH}")
    
    # 載入 2025 排位賽數據
    races = load_qualifying_data()
    print(f"✓ 載入 {len(races)} 場 2025 排位賽數據")
    
    # 載入正賽結果
    race_results = load_race_results()
    print(f"✓ 載入 {len(race_results)} 場正賽結果")
    
    # 生成報告
    report = generate_report(races, race_results, model)
    
    # 保存報告
    OUTPUT_DIR.mkdir(exist_ok=True)
    output_file = OUTPUT_DIR / "2025_WIN_PROBABILITY_REPORT.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✓ 報告已保存: {output_file}")
    
    # 顯示摘要
    print("\n" + "="*60)
    print("預測摘要")
    print("="*60)
    
    for race in sorted(races, key=lambda x: x["race"]):
        race_name = race["race"]
        qualifying = race["qualifying"]
        if qualifying:
            predictions = predict_race(model, qualifying)
            actual_result = race_results.get(race_name, {})
            actual_winner = next((d for d, p in actual_result.items() if p == 1), "?")
            pred_winner = predictions[0]["driver"]
            status = "✓" if pred_winner == actual_winner else ("?" if actual_winner == "?" else "✗")
            print(f"{race_name:20} | 預測: {pred_winner} ({predictions[0]['win_probability']:.0%}) | 實際: {actual_winner} {status}")

if __name__ == "__main__":
    main()
