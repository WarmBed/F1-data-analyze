"""
使用 2023-2024 歷史數據訓練勝率預測模型
然後用於預測 2025 賽季
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report
import xgboost as xgb
import joblib

# 路徑設定
BASE_DIR = Path("c:/Users/mike2/OneDrive/Code/F1-data-analyze")
HISTORICAL_DATA = BASE_DIR / "json/historical_data/f1_2023_2024_training_data.json"
MODEL_OUTPUT = BASE_DIR / "models/win_probability_2023_2024_trained.pkl"

def load_historical_data():
    """載入 2023-2024 歷史數據"""
    with open(HISTORICAL_DATA, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def prepare_features(samples: list) -> tuple:
    """準備特徵和標籤"""
    features = []
    labels = []
    
    for s in samples:
        feature = [
            s["q_position"],  # 排位賽位置 (1-5)
            s["team_rating"],  # 車隊評級 (1-10)
            1 if s["q_position"] == 1 else 0,  # 是否桿位
            1 if s["q_position"] <= 3 else 0,  # 是否前三
            10 - s["q_position"],  # 位置優勢 (越高越好)
        ]
        features.append(feature)
        labels.append(s["is_winner"])
    
    return np.array(features), np.array(labels)

def train_model(X: np.ndarray, y: np.ndarray):
    """訓練 XGBoost 模型"""
    # 分割訓練/測試集
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # 計算正負樣本比例
    scale_pos_weight = len(y[y == 0]) / len(y[y == 1])
    
    # 創建模型
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        scale_pos_weight=scale_pos_weight,
        random_state=42,
        eval_metric='logloss'
    )
    
    # 訓練
    model.fit(X_train, y_train)
    
    # 評估
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    # 交叉驗證
    cv_scores = cross_val_score(model, X, y, cv=5)
    
    return model, accuracy, cv_scores

def analyze_predictions(model, samples: list):
    """分析預測結果"""
    # 按比賽分組
    races = {}
    for s in samples:
        key = f"{s['year']}_{s['race']}"
        if key not in races:
            races[key] = []
        races[key].append(s)
    
    # 統計
    top1_correct = 0
    top3_correct = 0
    total_races = 0
    
    for race_key, drivers in races.items():
        # 預測
        X = []
        for d in drivers:
            X.append([
                d["q_position"],
                d["team_rating"],
                1 if d["q_position"] == 1 else 0,
                1 if d["q_position"] <= 3 else 0,
                10 - d["q_position"],
            ])
        
        probs = model.predict_proba(np.array(X))[:, 1]
        
        # 找出預測冠軍
        pred_winner_idx = np.argmax(probs)
        pred_winner = drivers[pred_winner_idx]["driver"]
        
        # 找出實際冠軍
        actual_winner = next((d["driver"] for d in drivers if d["is_winner"]), None)
        
        if actual_winner:
            total_races += 1
            if pred_winner == actual_winner:
                top1_correct += 1
            
            # Top-3 預測
            top3_indices = np.argsort(probs)[-3:][::-1]
            top3_drivers = [drivers[i]["driver"] for i in top3_indices]
            if actual_winner in top3_drivers:
                top3_correct += 1
    
    return {
        "top1_accuracy": top1_correct / total_races if total_races > 0 else 0,
        "top3_accuracy": top3_correct / total_races if total_races > 0 else 0,
        "total_races": total_races,
        "top1_correct": top1_correct,
        "top3_correct": top3_correct
    }

def main():
    print("="*60)
    print("F1 勝率預測模型訓練")
    print("使用 2023-2024 歷史數據")
    print("="*60)
    
    # 載入數據
    data = load_historical_data()
    samples = data["all"]
    print(f"\n載入樣本數: {len(samples)}")
    
    # 準備特徵
    X, y = prepare_features(samples)
    print(f"特徵維度: {X.shape}")
    print(f"正樣本 (勝利): {sum(y)}, 負樣本: {len(y) - sum(y)}")
    
    # 訓練模型
    print("\n訓練模型...")
    model, accuracy, cv_scores = train_model(X, y)
    
    print(f"\n測試集準確率: {accuracy:.2%}")
    print(f"交叉驗證準確率: {cv_scores.mean():.2%} (+/- {cv_scores.std()*2:.2%})")
    
    # 特徵重要性
    feature_names = ["q_position", "team_rating", "is_pole", "is_top3", "position_advantage"]
    print("\n特徵重要性:")
    for name, imp in zip(feature_names, model.feature_importances_):
        print(f"  {name}: {imp:.3f}")
    
    # 分析預測
    print("\n預測分析:")
    results = analyze_predictions(model, samples)
    print(f"  Top-1 準確率: {results['top1_correct']}/{results['total_races']} = {results['top1_accuracy']:.1%}")
    print(f"  Top-3 準確率: {results['top3_correct']}/{results['total_races']} = {results['top3_accuracy']:.1%}")
    
    # 保存模型
    MODEL_OUTPUT.parent.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_OUTPUT)
    print(f"\n✓ 模型已保存: {MODEL_OUTPUT}")
    
    # 分析桿位奪冠統計
    print("\n" + "="*60)
    print("桿位奪冠統計")
    print("="*60)
    
    poles = [s for s in samples if s["q_position"] == 1]
    pole_wins = sum(1 for s in poles if s["is_winner"])
    print(f"桿位奪冠率: {pole_wins}/{len(poles)} = {pole_wins/len(poles)*100:.1f}%")
    
    # 按車手統計
    driver_stats = {}
    for s in samples:
        driver = s["driver"]
        if driver not in driver_stats:
            driver_stats[driver] = {"poles": 0, "wins": 0, "races": 0}
        if s["q_position"] == 1:
            driver_stats[driver]["poles"] += 1
        if s["is_winner"]:
            driver_stats[driver]["wins"] += 1
        driver_stats[driver]["races"] += 1
    
    print("\n車手統計 (依勝場排序):")
    sorted_drivers = sorted(driver_stats.items(), key=lambda x: x[1]["wins"], reverse=True)
    for driver, stats in sorted_drivers[:10]:
        print(f"  {driver}: {stats['wins']} 勝, {stats['poles']} 桿位")

if __name__ == "__main__":
    main()
