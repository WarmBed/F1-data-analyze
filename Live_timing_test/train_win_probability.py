#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
F1 勝率預測模型 - Phase 1 訓練器
================================

使用提取的訓練數據訓練 XGBoost 模型。

訓練集: 2023 + 2024 (37 場比賽)
測試集: 2025 (22 場比賽)

作者: F1 Telemetry Station Pro
日期: 2025-11-26
"""

import json
import os
import pickle
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

import numpy as np

# XGBoost
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("[WARN] XGBoost 未安裝")

# sklearn
try:
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, log_loss
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("[WARN] sklearn 未安裝")


class WinProbabilityTrainer:
    """勝率預測模型訓練器"""
    
    # 車隊評分 (2024 基準)
    TEAM_RATINGS = {
        "Red Bull Racing": 0.95,
        "Ferrari": 0.88,
        "McLaren": 0.90,
        "Mercedes": 0.85,
        "Aston Martin": 0.70,
        "Alpine": 0.55,
        "Williams": 0.45,
        "RB": 0.50,
        "Racing Bulls": 0.50,
        "Kick Sauber": 0.35,
        "Haas F1 Team": 0.40,
        "Alfa Romeo": 0.35,
        "AlphaTauri": 0.50,
    }
    
    def __init__(self, base_path: str = "."):
        self.base_path = base_path
        self.model = None
        self.training_data = None
        self.overtaking_difficulty = {}
        self.driver_stats = {}
        self.feature_names = []
        self.simple_weights = {}
        
    def load_data(self):
        """載入訓練數據"""
        
        # 載入訓練數據
        data_path = os.path.join(self.base_path, "json", "race_results_training.json")
        
        with open(data_path, 'r', encoding='utf-8') as f:
            self.training_data = json.load(f)
        
        print(f"[INFO] 載入 {len(self.training_data['races'])} 場比賽")
        
        # 載入車手統計
        self.driver_stats = self.training_data.get('driver_stats', {})
        print(f"[INFO] 載入 {len(self.driver_stats)} 位車手統計")
        
        # 載入超車難度
        diff_path = os.path.join(self.base_path, "json", "track_overtaking_difficulty.json")
        
        if os.path.exists(diff_path):
            with open(diff_path, 'r', encoding='utf-8') as f:
                diff_data = json.load(f)
            self.overtaking_difficulty = {
                track: info["difficulty_index"]
                for track, info in diff_data.get("tracks", {}).items()
            }
            print(f"[INFO] 載入 {len(self.overtaking_difficulty)} 個賽道難度")
    
    def prepare_features(self, years: List[int] = None) -> Tuple[np.ndarray, np.ndarray]:
        """準備訓練特徵"""
        
        features = []
        labels = []
        
        for race in self.training_data['races']:
            # 過濾年份
            if years and race['year'] not in years:
                continue
            
            track = race['track']
            
            for result in race['results']:
                # 跳過無效數據
                if result['finish_position'] > 20:
                    continue
                if not result['driver_code']:
                    continue
                
                # 提取特徵
                f = self._extract_features(
                    driver_code=result['driver_code'],
                    team=result['team'],
                    track=track,
                    grid_position=result['grid_position'],
                )
                features.append(f)
                
                # 標籤
                labels.append(1 if result['is_winner'] else 0)
        
        X = np.array(features)
        y = np.array(labels)
        
        print(f"[INFO] 準備 {len(features)} 筆訓練數據，{sum(labels)} 個贏家")
        
        return X, y
    
    def _extract_features(self, driver_code: str, team: str, track: str, grid_position: int) -> List[float]:
        """提取特徵"""
        
        # 1. 起跑位置 (歸一化)
        grid_normalized = min(grid_position, 20) / 20.0
        
        # 2. 車隊評分
        team_rating = self.TEAM_RATINGS.get(team, 0.5)
        
        # 3. 賽道超車難度
        track_normalized = track.replace(" ", "_")
        track_difficulty = self.overtaking_difficulty.get(track_normalized, 0.5)
        
        # 4. 車手統計
        driver_stat = self.driver_stats.get(driver_code, {})
        win_rate = driver_stat.get('win_rate', 0.0)
        podium_rate = driver_stat.get('podium_rate', 0.0)
        avg_finish = driver_stat.get('avg_finish', 10)
        avg_finish_normalized = min(avg_finish, 20) / 20.0
        
        # 5. 車手在該賽道的歷史表現
        track_history = driver_stat.get('track_performances', {}).get(track_normalized, [])
        track_avg = np.mean(track_history) / 20.0 if track_history else 0.5
        
        # 6. 起跑位置優勢 (與超車難度交互)
        grid_advantage = (1 - grid_normalized) * track_difficulty
        
        # 7. 前排起跑
        is_front_row = 1.0 if grid_position <= 3 else 0.0
        
        # 8. 桿位
        is_pole = 1.0 if grid_position == 1 else 0.0
        
        features = [
            grid_normalized,
            team_rating,
            track_difficulty,
            win_rate,
            podium_rate,
            avg_finish_normalized,
            track_avg,
            grid_advantage,
            is_front_row,
            is_pole,
        ]
        
        self.feature_names = [
            'grid_position', 'team_rating', 'track_difficulty',
            'driver_win_rate', 'driver_podium_rate', 'avg_finish',
            'track_history', 'grid_advantage', 'is_front_row', 'is_pole'
        ]
        
        return features
    
    def train(self, X: np.ndarray, y: np.ndarray):
        """訓練模型"""
        
        if not HAS_XGBOOST or not HAS_SKLEARN:
            print("[WARN] 使用簡化模型")
            self._train_simple_model(X, y)
            return
        
        # 分割訓練/驗證集
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # XGBoost 參數
        params = {
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'max_depth': 4,
            'learning_rate': 0.1,
            'n_estimators': 100,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42,
        }
        
        self.model = xgb.XGBClassifier(**params)
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
        
        # 評估
        y_pred = self.model.predict(X_val)
        y_prob = self.model.predict_proba(X_val)[:, 1]
        
        accuracy = accuracy_score(y_val, y_pred)
        logloss = log_loss(y_val, y_prob)
        
        print(f"\n[INFO] 驗證集準確率: {accuracy:.3f}")
        print(f"[INFO] 驗證集 Log Loss: {logloss:.3f}")
        
        # 特徵重要性
        print("\n[INFO] 特徵重要性:")
        importance = self.model.feature_importances_
        for name, imp in sorted(zip(self.feature_names, importance), key=lambda x: -x[1]):
            bar = "=" * int(imp * 30)
            print(f"  {name:20s}: {imp:.3f} {bar}")
    
    def _train_simple_model(self, X: np.ndarray, y: np.ndarray):
        """簡化模型"""
        
        self.simple_weights = {
            'grid_position': -3.0,
            'team_rating': 2.0,
            'track_difficulty': 1.0,
            'driver_win_rate': 4.0,
            'driver_podium_rate': 2.0,
            'avg_finish': -1.5,
            'track_history': -1.0,
            'grid_advantage': 2.5,
            'is_front_row': 1.5,
            'is_pole': 2.0,
        }
        print("[INFO] 簡化模型訓練完成")
    
    def predict_race(self, race_data: List[Dict]) -> List[Dict]:
        """預測單場比賽"""
        
        features = []
        for driver_data in race_data:
            f = self._extract_features(
                driver_code=driver_data.get('driver_code', ''),
                team=driver_data.get('team', ''),
                track=driver_data.get('track', ''),
                grid_position=driver_data.get('grid_position', 10),
            )
            features.append(f)
        
        X = np.array(features)
        
        # 預測
        if self.model is not None and HAS_XGBOOST:
            probabilities = self.model.predict_proba(X)[:, 1]
        else:
            probabilities = self._simple_predict(X)
        
        # 標準化
        prob_sum = np.sum(probabilities)
        if prob_sum > 0:
            probabilities = probabilities / prob_sum
        
        # 組裝結果
        predictions = []
        for i, driver_data in enumerate(race_data):
            predictions.append({
                'driver_code': driver_data.get('driver_code', ''),
                'team': driver_data.get('team', ''),
                'grid_position': driver_data.get('grid_position', 0),
                'win_probability': float(probabilities[i]),
                'win_probability_pct': f"{probabilities[i] * 100:.1f}%"
            })
        
        predictions.sort(key=lambda x: -x['win_probability'])
        return predictions
    
    def _simple_predict(self, X: np.ndarray) -> np.ndarray:
        """簡化預測"""
        
        weights = np.array([
            self.simple_weights.get(name, 0)
            for name in self.feature_names
        ])
        
        scores = np.dot(X, weights)
        exp_scores = np.exp(scores - np.max(scores))
        probabilities = exp_scores / np.sum(exp_scores)
        
        return probabilities
    
    def evaluate_on_year(self, year: int):
        """在指定年份上評估"""
        
        print(f"\n{'=' * 60}")
        print(f"{year} 賽季評估")
        print(f"{'=' * 60}")
        
        correct_top1 = 0
        correct_top3 = 0
        total_races = 0
        
        for race in self.training_data['races']:
            if race['year'] != year:
                continue
            
            track = race['track']
            
            # 找出真正的贏家
            actual_winner = None
            for result in race['results']:
                if result['is_winner']:
                    actual_winner = result['driver_code']
                    break
            
            if not actual_winner:
                continue
            
            # 準備預測數據
            race_data = [
                {
                    'driver_code': r['driver_code'],
                    'team': r['team'],
                    'track': track,
                    'grid_position': r['grid_position'],
                }
                for r in race['results']
                if r['driver_code']
            ]
            
            if not race_data:
                continue
            
            # 預測
            predictions = self.predict_race(race_data)
            
            # 評估
            predicted_top3 = [p['driver_code'] for p in predictions[:3]]
            predicted_winner = predictions[0]['driver_code'] if predictions else None
            
            is_top1_correct = (predicted_winner == actual_winner)
            is_top3_correct = (actual_winner in predicted_top3)
            
            if is_top1_correct:
                correct_top1 += 1
            if is_top3_correct:
                correct_top3 += 1
            total_races += 1
            
            # 輸出詳情
            status = "[O]" if is_top1_correct else ("[~]" if is_top3_correct else "[X]")
            print(f"{status} {track}: 實際={actual_winner}, 預測Top3={predicted_top3}")
        
        # 總結
        if total_races > 0:
            print(f"\n總結: Top-1 {correct_top1}/{total_races} ({correct_top1/total_races*100:.1f}%), "
                  f"Top-3 {correct_top3}/{total_races} ({correct_top3/total_races*100:.1f}%)")
        
        return {
            'year': year,
            'total_races': total_races,
            'top1_accuracy': correct_top1 / total_races if total_races > 0 else 0,
            'top3_accuracy': correct_top3 / total_races if total_races > 0 else 0,
        }
    
    def save_model(self, path: str = "models/win_probability_phase1.pkl"):
        """保存模型"""
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        model_data = {
            'model': self.model,
            'driver_stats': self.driver_stats,
            'overtaking_difficulty': self.overtaking_difficulty,
            'feature_names': self.feature_names,
            'team_ratings': self.TEAM_RATINGS,
            'simple_weights': self.simple_weights,
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"[INFO] 模型已保存: {path}")
    
    def load_model(self, path: str = "models/win_probability_phase1.pkl"):
        """載入模型"""
        
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data.get('model')
        self.driver_stats = model_data.get('driver_stats', {})
        self.overtaking_difficulty = model_data.get('overtaking_difficulty', {})
        self.feature_names = model_data.get('feature_names', [])
        self.simple_weights = model_data.get('simple_weights', {})
        
        print(f"[INFO] 模型已載入: {path}")


def main():
    """主函數"""
    
    print("=" * 60)
    print("F1 勝率預測模型 - Phase 1 訓練")
    print("=" * 60)
    
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 初始化訓練器
    trainer = WinProbabilityTrainer(base_path)
    
    # 載入數據
    print("\n[STEP 1] 載入數據...")
    trainer.load_data()
    
    # 準備特徵 (使用 2023+2024 訓練)
    print("\n[STEP 2] 準備訓練特徵 (2023+2024)...")
    X, y = trainer.prepare_features(years=[2023, 2024])
    
    # 訓練模型
    print("\n[STEP 3] 訓練模型...")
    trainer.train(X, y)
    
    # 保存模型
    print("\n[STEP 4] 保存模型...")
    model_path = os.path.join(base_path, "models", "win_probability_phase1.pkl")
    trainer.save_model(model_path)
    
    # 在 2025 上評估
    print("\n[STEP 5] 評估模型...")
    metrics_2025 = trainer.evaluate_on_year(2025)
    
    # 額外：在 2024 上驗證 (應該較高，因為是訓練數據)
    metrics_2024 = trainer.evaluate_on_year(2024)
    
    # 總結
    print("\n" + "=" * 60)
    print("最終評估結果")
    print("=" * 60)
    print(f"2024 (訓練集): Top-1 {metrics_2024['top1_accuracy']*100:.1f}%, Top-3 {metrics_2024['top3_accuracy']*100:.1f}%")
    print(f"2025 (測試集): Top-1 {metrics_2025['top1_accuracy']*100:.1f}%, Top-3 {metrics_2025['top3_accuracy']*100:.1f}%")
    
    return trainer


if __name__ == "__main__":
    main()
