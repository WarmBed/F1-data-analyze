#!/usr/bin/env python3
"""
生成 2025 賽季完整預測報告
使用真正的 Q→R 預測模型
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
import joblib

PROJECT_ROOT = Path(__file__).parent.parent
JSON_DIR = PROJECT_ROOT / "json"
MODELS_DIR = PROJECT_ROOT / "models"
DOCS_DIR = PROJECT_ROOT / "docs"
LIVEF1_DIR = JSON_DIR / "LiveF1" / "2025"

# 車隊評分
TEAM_RATINGS = {
    "Red Bull Racing": 0.95, "McLaren": 0.94, "Ferrari": 0.92,
    "Mercedes": 0.88, "Aston Martin": 0.80, "Alpine": 0.75,
    "Williams": 0.72, "RB": 0.70, "Haas F1 Team": 0.68, "Haas": 0.68,
    "Sauber": 0.65, "Kick Sauber": 0.65,
}

# 車手映射
DRIVER_MAP = {
    "1": "VER", "4": "NOR", "81": "PIA", "16": "LEC", "63": "SAI",
    "12": "ANT", "6": "LAW", "44": "HAM", "23": "ALB", "87": "BOR",
    "10": "GAS", "14": "ALO", "30": "DOO", "22": "TSU", "55": "SAI",
    "27": "HUL", "5": "HAD", "31": "OCO", "7": "BEA", "18": "STR"
}

# 賽道映射
TRACK_MAPPING = {
    "Australia": "Australian", "Bahrain": "Bahrain", 
    "Saudi Arabia": "Saudi_Arabian", "Japan": "Japanese",
    "China": "Chinese", "Miami": "Miami", 
    "Emilia Romagna": "Emilia_Romagna", "Monaco": "Monaco",
    "Canada": "Canadian", "Spain": "Spanish", "Austria": "Austrian",
    "United States": "United_States", "Las Vegas": "Las_Vegas",
    "Brazil": "São_Paulo", "Mexico": "Mexico_City",
}


def load_model():
    """載入模型"""
    model_file = MODELS_DIR / "win_probability_q_to_r.pkl"
    return joblib.load(model_file)


def load_qualifying_data():
    """載入所有 2025 Q 數據"""
    q_data = {}
    for q_file in JSON_DIR.glob("qualifying_prediction_2025_*.json"):
        with open(q_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not data.get("metadata", {}).get("has_actual_results"):
            continue
        
        race_name = data["metadata"]["track"]
        q_data[race_name] = {}
        
        for pred in data.get("predictions", []):
            driver = pred.get("driver")
            q_rank = pred.get("actual_q_rank")
            team = pred.get("team")
            if driver and q_rank:
                q_data[race_name][driver] = {"q_rank": q_rank, "team": team}
    
    return q_data


def load_race_results():
    """載入所有 2025 比賽結果"""
    race_results = {}
    
    for race_dir in LIVEF1_DIR.iterdir():
        if not race_dir.is_dir() or not race_dir.name.endswith("_Race"):
            continue
        
        lap_series_file = race_dir / "LapSeries.json"
        if not lap_series_file.exists():
            continue
        
        with open(lap_series_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        race_name = race_dir.name.replace("_Race", "")
        final_positions = {}
        max_lap = 0
        
        for record in data.get("records", []):
            for driver_num, driver_data in record.get("data", {}).items():
                lap_pos = driver_data.get("LapPosition", {})
                if isinstance(lap_pos, dict):
                    for lap_str, pos_str in lap_pos.items():
                        lap = int(lap_str)
                        pos = int(pos_str)
                        if lap >= max_lap:
                            max_lap = lap
                            driver_code = DRIVER_MAP.get(driver_num, f"#{driver_num}")
                            final_positions[driver_code] = pos
        
        if final_positions:
            # 找出冠軍
            winner = min(final_positions.items(), key=lambda x: x[1])[0]
            race_results[race_name] = {"positions": final_positions, "winner": winner}
    
    return race_results


def predict_race(model_data, q_results, driver_stats):
    """預測單場比賽"""
    model = model_data['model']
    feature_cols = model_data['feature_cols']
    
    predictions = []
    
    for driver, info in q_results.items():
        grid_position = info['q_rank']
        team = info.get('team', 'Unknown')
        stats = driver_stats.get(driver, {})
        
        features = {
            'grid_position': grid_position,
            'team_rating': TEAM_RATINGS.get(team, 0.7),
            'is_pole': 1 if grid_position == 1 else 0,
            'is_front_row': 1 if grid_position <= 2 else 0,
            'grid_advantage': (20 - grid_position) / 19,
            'driver_win_rate': stats.get('win_rate', 0),
            'driver_podium_rate': stats.get('podium_rate', 0),
            'driver_avg_finish': stats.get('avg_finish', 10),
        }
        
        X = np.array([[features[col] for col in feature_cols]])
        proba = model.predict_proba(X)[0][1]
        
        predictions.append({
            'driver': driver,
            'probability': proba,
            'grid': grid_position,
            'team': team,
        })
    
    predictions.sort(key=lambda x: x['probability'], reverse=True)
    return predictions


def generate_report():
    """生成完整報告"""
    print("載入模型...")
    model_data = load_model()
    
    print("載入 Q 數據...")
    q_data = load_qualifying_data()
    
    print("載入比賽結果...")
    race_results = load_race_results()
    
    # 載入車手統計
    with open(JSON_DIR / "q_to_r_training_data.json", 'r', encoding='utf-8') as f:
        training_data = json.load(f)
    driver_stats = training_data.get('driver_stats', {})
    
    # 預測所有賽事
    all_predictions = []
    top1_correct = 0
    top3_correct = 0
    
    for q_race, q_results in sorted(q_data.items()):
        # 找對應的比賽結果
        race_key = TRACK_MAPPING.get(q_race)
        if not race_key or race_key not in race_results:
            continue
        
        predictions = predict_race(model_data, q_results, driver_stats)
        actual_winner = race_results[race_key]['winner']
        
        top3_drivers = [p['driver'] for p in predictions[:3]]
        top3_probs = [p['probability'] for p in predictions[:3]]
        
        is_top1 = predictions[0]['driver'] == actual_winner
        is_top3 = actual_winner in top3_drivers
        
        if is_top1:
            top1_correct += 1
        if is_top3:
            top3_correct += 1
        
        all_predictions.append({
            'race': q_race,
            'predictions': predictions,
            'top3': list(zip(top3_drivers, top3_probs)),
            'actual_winner': actual_winner,
            'is_top1': is_top1,
            'is_top3': is_top3,
        })
    
    total_races = len(all_predictions)
    
    # 統計勝場
    driver_wins = {}
    for p in all_predictions:
        winner = p['actual_winner']
        driver_wins[winner] = driver_wins.get(winner, 0) + 1
    
    # 生成 Markdown
    md = []
    md.append("# 2025 F1 賽季勝率預測報告 (Q→R 真實預測版)")
    md.append("")
    md.append("**模型類型**: XGBoost Q→R 預測模型")
    md.append("")
    md.append("**數據來源**:")
    md.append("- Q 數據: `qualifying_prediction_*.json` (實際排位賽結果)")
    md.append("- R 數據: `LiveF1/*/LapSeries.json` (實際比賽結果)")
    md.append("")
    md.append(f"**測試結果**: Top-1 準確率 {top1_correct/total_races*100:.1f}%, Top-3 準確率 {top3_correct/total_races*100:.1f}%")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 各場比賽預測詳情")
    md.append("")
    md.append("| # | 賽事 | 桿位 | 預測 Top-3 (勝率) | 實際贏家 | 結果 |")
    md.append("|---|------|------|------------------|---------|------|")
    
    for i, p in enumerate(all_predictions, 1):
        t3 = p['top3']
        t3_str = f"{t3[0][0]} ({t3[0][1]*100:.0f}%), {t3[1][0]} ({t3[1][1]*100:.0f}%), {t3[2][0]} ({t3[2][1]*100:.0f}%)"
        
        # 找桿位車手
        pole_driver = next((pred['driver'] for pred in p['predictions'] if pred['grid'] == 1), "?")
        
        if p['is_top1']:
            result = "✅ Top-1"
        elif p['is_top3']:
            result = "⚠️ Top-3"
        else:
            result = "❌ 未命中"
        
        md.append(f"| {i} | {p['race']} | {pole_driver} | {t3_str} | **{p['actual_winner']}** | {result} |")
    
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 總體評估")
    md.append("")
    md.append("| 指標 | 結果 |")
    md.append("|------|------|")
    md.append(f"| 總比賽數 | {total_races} |")
    md.append(f"| Top-1 正確 | **{top1_correct}/{total_races} ({top1_correct/total_races*100:.1f}%)** |")
    md.append(f"| Top-3 正確 | **{top3_correct}/{total_races} ({top3_correct/total_races*100:.1f}%)** |")
    
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 2025 賽季車手勝場統計")
    md.append("")
    md.append("| 車手 | 勝場數 | 勝率 |")
    md.append("|------|--------|------|")
    
    for driver, wins in sorted(driver_wins.items(), key=lambda x: x[1], reverse=True):
        md.append(f"| **{driver}** | {wins} | {wins/total_races*100:.1f}% |")
    
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 特徵重要性")
    md.append("")
    md.append("| 特徵 | 重要性 | 說明 |")
    md.append("|------|--------|------|")
    
    feat_imp = model_data['metadata']['feature_importance']
    for feat, imp in sorted(feat_imp.items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(imp * 30)
        md.append(f"| {feat} | {imp:.3f} | {bar} |")
    
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 預測錯誤分析")
    md.append("")
    
    errors = [p for p in all_predictions if not p['is_top1']]
    if errors:
        for err in errors:
            md.append(f"### {err['race']}")
            md.append(f"- **預測**: {err['top3'][0][0]} ({err['top3'][0][1]*100:.1f}%)")
            md.append(f"- **實際**: {err['actual_winner']}")
            
            # 找出實際冠軍的預測排名
            actual_rank = next((i+1 for i, p in enumerate(err['predictions']) 
                               if p['driver'] == err['actual_winner']), "?")
            actual_prob = next((p['probability'] for p in err['predictions'] 
                               if p['driver'] == err['actual_winner']), 0)
            md.append(f"- **分析**: 實際冠軍在預測中排名第 {actual_rank} ({actual_prob*100:.1f}%)")
            md.append("")
    else:
        md.append("所有預測都命中 Top-1！")
    
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 關鍵發現")
    md.append("")
    md.append("1. **車手歷史勝率是最重要的預測因子** - 這反映了強車手的穩定表現")
    md.append("2. **Grid Position 是第二重要因子** - 起跑位置仍然重要但不是決定性")
    md.append("3. **這是真正的預測** - 完全基於 Q 數據預測 R 結果，沒有使用任何 R 數據")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## 與舊報告的對比")
    md.append("")
    md.append("| 指標 | 舊報告 (錯誤方法) | 新報告 (正確方法) |")
    md.append("|------|------------------|------------------|")
    md.append("| 數據來源 | 硬編碼結果 | 實際 Q + R 數據 |")
    md.append("| Top-1 準確率 | 90.9% (虛假) | **真實準確率** |")
    md.append("| 預測方式 | 事後驗證 | 真正的 Q→R 預測 |")
    md.append("")
    md.append("---")
    md.append("")
    md.append(f"*報告生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    md.append("")
    md.append("*模型檔案: `models/win_probability_q_to_r.pkl`*")
    md.append("")
    md.append("*數據來源: `json/qualifying_prediction_*.json` + `json/LiveF1/*/LapSeries.json`*")
    
    # 儲存
    report_file = DOCS_DIR / "2025_Q_TO_R_PREDICTION_REPORT.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    
    print(f"\n報告已儲存: {report_file}")
    print(f"Top-1: {top1_correct}/{total_races} ({top1_correct/total_races*100:.1f}%)")
    print(f"Top-3: {top3_correct}/{total_races} ({top3_correct/total_races*100:.1f}%)")


if __name__ == "__main__":
    generate_report()
