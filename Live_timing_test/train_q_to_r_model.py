#!/usr/bin/env python3
"""
Phase 1: 真正的 Q→R 預測模型訓練

使用實際的排位賽數據 (Q) 預測比賽結果 (R)
這才是真正的預測系統！

數據來源: q_to_r_training_data.json (由 extract_q_to_r_data.py 生成)
"""

import json
import os
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

# 專案根目錄
PROJECT_ROOT = Path(__file__).parent.parent
JSON_DIR = PROJECT_ROOT / "json"
MODELS_DIR = PROJECT_ROOT / "models"
MODELS_DIR.mkdir(exist_ok=True)


def load_training_data():
    """
    載入訓練數據
    """
    data_file = JSON_DIR / "q_to_r_training_data.json"
    
    if not data_file.exists():
        raise FileNotFoundError(f"找不到訓練數據: {data_file}")
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data


def prepare_features(samples: list) -> tuple:
    """
    準備特徵和標籤
    """
    df = pd.DataFrame(samples)
    
    # 特徵列
    feature_cols = [
        'grid_position',
        'team_rating',
        'is_pole',
        'is_front_row',
        'grid_advantage',
        'driver_win_rate',
        'driver_podium_rate',
        'driver_avg_finish',
    ]
    
    X = df[feature_cols].values
    y = df['is_winner'].values
    
    return X, y, feature_cols, df


def evaluate_predictions(model, X_test, y_test, test_df, feature_cols):
    """
    評估預測結果
    """
    # 取得勝率預測
    proba = model.predict_proba(X_test)[:, 1]
    test_df = test_df.copy()
    test_df['win_probability'] = proba
    
    # 按賽事分組，評估 Top-1, Top-3 準確率
    races = test_df.groupby(['year', 'race'])
    
    top1_correct = 0
    top3_correct = 0
    total_races = 0
    
    results = []
    
    for (year, race), group in races:
        # 按勝率排序
        sorted_group = group.sort_values('win_probability', ascending=False)
        
        predicted_winner = sorted_group.iloc[0]['driver']
        predicted_top3 = sorted_group.head(3)['driver'].tolist()
        
        # 找出實際冠軍
        actual_winner = group[group['is_winner'] == 1]
        if len(actual_winner) == 0:
            continue
        
        actual_winner_driver = actual_winner.iloc[0]['driver']
        
        # 檢查準確性
        is_top1_correct = predicted_winner == actual_winner_driver
        is_top3_correct = actual_winner_driver in predicted_top3
        
        if is_top1_correct:
            top1_correct += 1
        if is_top3_correct:
            top3_correct += 1
        total_races += 1
        
        results.append({
            'year': year,
            'race': race,
            'predicted_winner': predicted_winner,
            'predicted_win_prob': sorted_group.iloc[0]['win_probability'],
            'actual_winner': actual_winner_driver,
            'top1_correct': is_top1_correct,
            'top3_correct': is_top3_correct,
            'predicted_top3': predicted_top3,
        })
    
    if total_races == 0:
        return 0, 0, []
    
    top1_accuracy = top1_correct / total_races
    top3_accuracy = top3_correct / total_races
    
    return top1_accuracy, top3_accuracy, results


def train_model():
    """
    訓練 Q→R 預測模型
    """
    print("=" * 60)
    print("🏎️ Phase 1: 真正的 Q→R 預測模型訓練")
    print("=" * 60)
    
    # 載入數據
    print("\n📂 載入訓練數據...")
    data = load_training_data()
    samples = data['samples']
    
    print(f"   總樣本數: {len(samples)}")
    print(f"   勝利樣本: {sum(1 for s in samples if s['is_winner'])}")
    
    # 準備特徵
    print("\n🔧 準備特徵...")
    X, y, feature_cols, df = prepare_features(samples)
    
    print(f"   特徵數: {len(feature_cols)}")
    for i, col in enumerate(feature_cols):
        print(f"      {i+1}. {col}")
    
    # 分割訓練/測試集 (按賽事分割，確保同一場賽事不會被分到兩邊)
    races = df.groupby(['year', 'race']).ngroups
    print(f"\n📊 總賽事數: {races}")
    
    # 獲取所有賽事
    race_keys = df.groupby(['year', 'race']).groups.keys()
    race_list = list(race_keys)
    
    # 隨機分割賽事 (80% 訓練, 20% 測試)
    np.random.seed(42)
    np.random.shuffle(race_list)
    
    split_idx = int(len(race_list) * 0.8)
    train_races = race_list[:split_idx]
    test_races = race_list[split_idx:]
    
    print(f"   訓練賽事: {len(train_races)}")
    print(f"   測試賽事: {len(test_races)}")
    
    # 分割數據
    train_mask = df.apply(lambda row: (row['year'], row['race']) in train_races, axis=1)
    test_mask = ~train_mask
    
    X_train, X_test = X[train_mask], X[test_mask]
    y_train, y_test = y[train_mask], y[test_mask]
    train_df, test_df = df[train_mask], df[test_mask].copy()
    
    print(f"   訓練樣本: {len(X_train)}")
    print(f"   測試樣本: {len(X_test)}")
    
    # 訓練 XGBoost 模型
    print("\n🎯 訓練 XGBoost 模型...")
    
    # 計算正負樣本比例
    pos_ratio = sum(y_train) / len(y_train)
    scale_pos_weight = (1 - pos_ratio) / pos_ratio
    
    model = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        eval_metric='logloss',
    )
    
    model.fit(X_train, y_train)
    
    # 特徵重要性
    print("\n📈 特徵重要性:")
    feature_importance = dict(zip(feature_cols, model.feature_importances_))
    sorted_importance = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    
    for feat, imp in sorted_importance:
        bar = "█" * int(imp * 50)
        print(f"   {feat:25s} {imp:.4f} {bar}")
    
    # 評估測試集
    print("\n📊 測試集評估:")
    top1_acc, top3_acc, results = evaluate_predictions(model, X_test, y_test, test_df, feature_cols)
    
    print(f"   Top-1 準確率: {top1_acc*100:.1f}%")
    print(f"   Top-3 準確率: {top3_acc*100:.1f}%")
    
    # 顯示測試結果
    print("\n🏁 測試結果詳情:")
    for r in results:
        status = "✅" if r['top1_correct'] else ("⚠️" if r['top3_correct'] else "❌")
        print(f"   {status} {r['year']} {r['race']}: "
              f"預測 {r['predicted_winner']} ({r['predicted_win_prob']*100:.1f}%), "
              f"實際 {r['actual_winner']}")
    
    # 儲存模型
    model_file = MODELS_DIR / "win_probability_q_to_r.pkl"
    model_data = {
        'model': model,
        'feature_cols': feature_cols,
        'metadata': {
            'description': '真正的 Q→R 預測模型',
            'created': datetime.now().isoformat(),
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'top1_accuracy': top1_acc,
            'top3_accuracy': top3_acc,
            'feature_importance': feature_importance,
        }
    }
    
    joblib.dump(model_data, model_file)
    print(f"\n✅ 模型已儲存: {model_file}")
    
    # 返回評估結果
    return {
        'top1_accuracy': top1_acc,
        'top3_accuracy': top3_acc,
        'test_results': results,
        'feature_importance': feature_importance,
    }


def predict_race(year: int, race: str, q_results: dict):
    """
    使用模型預測比賽結果
    
    Args:
        year: 年份
        race: 賽道名稱
        q_results: {driver: {'q_rank': int, 'team': str}}
    
    Returns:
        預測結果列表 [(driver, win_probability), ...]
    """
    # 載入模型
    model_file = MODELS_DIR / "win_probability_q_to_r.pkl"
    model_data = joblib.load(model_file)
    model = model_data['model']
    feature_cols = model_data['feature_cols']
    
    # 載入車手統計數據
    data_file = JSON_DIR / "q_to_r_training_data.json"
    with open(data_file, 'r', encoding='utf-8') as f:
        training_data = json.load(f)
    driver_stats = training_data.get('driver_stats', {})
    
    # 車隊評分
    team_ratings = {
        "Red Bull Racing": 0.95,
        "McLaren": 0.94,
        "Ferrari": 0.92,
        "Mercedes": 0.88,
        "Aston Martin": 0.80,
        "Alpine": 0.75,
        "Williams": 0.72,
        "RB": 0.70,
        "Haas": 0.68,
        "Sauber": 0.65,
        "Kick Sauber": 0.65,
    }
    
    predictions = []
    
    for driver, info in q_results.items():
        grid_position = info['q_rank']
        team = info.get('team', 'Unknown')
        
        # 取得車手統計
        stats = driver_stats.get(driver, {})
        
        # 準備特徵
        features = {
            'grid_position': grid_position,
            'team_rating': team_ratings.get(team, 0.7),
            'is_pole': 1 if grid_position == 1 else 0,
            'is_front_row': 1 if grid_position <= 2 else 0,
            'grid_advantage': (20 - grid_position) / 19,
            'driver_win_rate': stats.get('win_rate', 0),
            'driver_podium_rate': stats.get('podium_rate', 0),
            'driver_avg_finish': stats.get('avg_finish', 10),
        }
        
        X = np.array([[features[col] for col in feature_cols]])
        proba = model.predict_proba(X)[0][1]
        
        predictions.append((driver, proba, grid_position, team))
    
    # 按勝率排序
    predictions.sort(key=lambda x: x[1], reverse=True)
    
    return predictions


def demo_prediction():
    """
    示範預測功能
    """
    print("\n" + "=" * 60)
    print("🔮 預測示範: 2025 日本 GP")
    print("=" * 60)
    
    # 載入日本站 Q 數據
    q_file = JSON_DIR / "qualifying_prediction_2025_Japan.json"
    with open(q_file, 'r', encoding='utf-8') as f:
        q_data = json.load(f)
    
    # 建立 Q 結果
    q_results = {}
    for pred in q_data.get("predictions", []):
        driver = pred.get("driver")
        q_rank = pred.get("actual_q_rank")
        team = pred.get("team")
        if driver and q_rank:
            q_results[driver] = {'q_rank': q_rank, 'team': team}
    
    # 預測
    predictions = predict_race(2025, "Japan", q_results)
    
    print("\n📊 預測結果 (基於排位賽數據):")
    print("-" * 50)
    
    for i, (driver, proba, grid, team) in enumerate(predictions[:10]):
        bar = "█" * int(proba * 30)
        print(f"   {i+1:2d}. {driver:4s} (G{grid:2d}, {team:15s}) "
              f"{proba*100:5.1f}% {bar}")
    
    # 顯示實際結果 (從 LapSeries)
    print("\n📋 實際比賽結果:")
    lap_series_file = JSON_DIR / "LiveF1" / "2025" / "Japanese_Race" / "LapSeries.json"
    if lap_series_file.exists():
        with open(lap_series_file, 'r', encoding='utf-8') as f:
            race_data = json.load(f)
        
        # 找最後一圈的位置
        final_positions = {}
        driver_map = {
            "1": "VER", "4": "NOR", "81": "PIA", "16": "LEC", "63": "SAI",
            "12": "ANT", "6": "LAW", "44": "HAM", "23": "ALB", "87": "BOR",
            "10": "GAS", "14": "ALO", "30": "DOO", "22": "TSU",
            "27": "HUL", "5": "HAD", "31": "OCO", "7": "BEA", "18": "STR"
        }
        
        for record in race_data.get("records", []):
            for driver_num, driver_data in record.get("data", {}).items():
                lap_pos = driver_data.get("LapPosition", {})
                if isinstance(lap_pos, dict):
                    for lap_str, pos_str in lap_pos.items():
                        lap = int(lap_str)
                        pos = int(pos_str)
                        driver_code = driver_map.get(driver_num, f"#{driver_num}")
                        final_positions[driver_code] = (pos, lap)
        
        # 排序
        sorted_results = sorted(final_positions.items(), key=lambda x: (-x[1][1], x[1][0]))
        
        print("-" * 50)
        for i, (driver, (pos, lap)) in enumerate(sorted_results[:10]):
            # 找到預測排名
            pred_rank = next((j+1 for j, p in enumerate(predictions) if p[0] == driver), "?")
            pred_proba = next((p[1] for p in predictions if p[0] == driver), 0)
            
            status = "🏆" if pos == 1 else ("🥈" if pos == 2 else ("🥉" if pos == 3 else "  "))
            print(f"   {status} P{pos:2d}: {driver:4s} "
                  f"(預測排名: {pred_rank}, 勝率: {pred_proba*100:.1f}%)")


if __name__ == "__main__":
    # 訓練模型
    results = train_model()
    
    # 示範預測
    demo_prediction()
