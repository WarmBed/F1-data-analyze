#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
F1 即時勝率預測系統 - Phase 1: 比賽前勝率模型
===============================================

使用 XGBoost 訓練比賽前勝率預測模型。

訓練集: 2023 + 2024 (~46 場比賽)
測試集: 2025 (~22 場比賽)

特徵:
- 排位賽結果 (grid_position)
- 車手歷史表現 (driver_rating)
- 車隊實力 (team_rating)  
- 賽道超車難度 (overtaking_difficulty)
- 車手在該賽道的歷史表現 (track_history)

輸出:
- 訓練好的模型: models/win_probability_phase1.pkl
- 預測結果: 每位車手的賽前勝率

作者: F1 Telemetry Station Pro
日期: 2025-11-26
"""

import json
import os
import pickle
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from dataclasses import dataclass, field
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd

# 嘗試導入 XGBoost
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("[WARN] XGBoost 未安裝，將使用簡化模型")

# 嘗試導入 sklearn
try:
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import accuracy_score, log_loss
    from sklearn.preprocessing import LabelEncoder
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("[WARN] sklearn 未安裝")


@dataclass
class RaceResult:
    """單場比賽結果"""
    year: int
    track: str
    driver: str
    team: str
    grid_position: int
    finish_position: int
    is_winner: bool = False
    dnf: bool = False


@dataclass  
class DriverStats:
    """車手統計數據"""
    driver: str
    total_races: int = 0
    wins: int = 0
    podiums: int = 0
    avg_finish: float = 0.0
    avg_grid: float = 0.0
    win_rate: float = 0.0
    podium_rate: float = 0.0
    track_performances: Dict[str, List[int]] = field(default_factory=dict)


class WinProbabilityModel:
    """勝率預測模型 - Phase 1"""
    
    # 2024 賽季車隊評分 (基於建造者積分)
    TEAM_RATINGS_2024 = {
        "Red Bull Racing": 0.95,
        "Ferrari": 0.88,
        "McLaren": 0.90,
        "Mercedes": 0.85,
        "Aston Martin": 0.70,
        "Alpine": 0.55,
        "Williams": 0.45,
        "Racing Bulls": 0.50,
        "Kick Sauber": 0.35,
        "Haas F1 Team": 0.40,
        # 別名
        "Red Bull": 0.95,
        "AlphaTauri": 0.50,
        "Alfa Romeo": 0.35,
        "Sauber": 0.35,
    }
    
    def __init__(self, base_path: str = "."):
        self.base_path = base_path
        self.model = None
        self.driver_stats = {}
        self.overtaking_difficulty = {}
        self.label_encoder = LabelEncoder() if HAS_SKLEARN else None
        self.feature_names = []
        
    def load_overtaking_difficulty(self):
        """載入賽道超車難度數據"""
        path = os.path.join(self.base_path, "json", "track_overtaking_difficulty.json")
        
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.overtaking_difficulty = {
                track: info["difficulty_index"]
                for track, info in data.get("tracks", {}).items()
            }
            print(f"[INFO] 載入 {len(self.overtaking_difficulty)} 個賽道的超車難度")
        else:
            print("[WARN] 找不到超車難度數據，使用預設值 0.5")
            
    def load_race_results(self, years: List[int]) -> List[RaceResult]:
        """從 Live F1 數據載入比賽結果"""
        
        all_results = []
        
        for year in years:
            year_path = os.path.join(self.base_path, "json", "LiveF1", str(year))
            
            if not os.path.exists(year_path):
                print(f"[WARN] 找不到 {year} 數據")
                continue
                
            races = [r for r in os.listdir(year_path) if "_Race" in r]
            
            for race in races:
                track = race.replace("_Race", "")
                race_path = os.path.join(year_path, race)
                
                results = self._parse_race_results(race_path, year, track)
                all_results.extend(results)
        
        print(f"[INFO] 載入 {len(all_results)} 筆比賽結果")
        return all_results
    
    def _parse_race_results(self, race_path: str, year: int, track: str) -> List[RaceResult]:
        """解析單場比賽結果"""
        
        results = []
        
        # 讀取車手列表
        driver_path = os.path.join(race_path, "DriverList.json")
        timing_path = os.path.join(race_path, "TimingData.json")
        
        drivers = {}  # {number: {name, team}}
        
        if os.path.exists(driver_path):
            try:
                with open(driver_path, 'r', encoding='utf-8') as f:
                    dl = json.load(f)
                
                for rec in dl.get('records', []):
                    data = rec.get('data', {})
                    if isinstance(data, dict):
                        for num, info in data.items():
                            if isinstance(info, dict) and 'Tla' in info:
                                drivers[num] = {
                                    'name': info.get('Tla', ''),
                                    'team': info.get('TeamName', ''),
                                }
            except Exception as e:
                print(f"  [ERROR] 解析 DriverList 失敗: {e}")
        
        # 讀取最終排名和起跑位置
        if os.path.exists(timing_path):
            try:
                with open(timing_path, 'r', encoding='utf-8') as f:
                    td = json.load(f)
                
                records = td.get('records', [])
                
                # 累積位置和起跑位置
                final_positions = {}
                grid_positions = {}
                
                for rec in records:
                    data = rec.get('data', {})
                    if isinstance(data, dict) and 'Lines' in data:
                        for num, info in data['Lines'].items():
                            if isinstance(info, dict):
                                if 'Position' in info:
                                    final_positions[num] = int(info['Position'])
                                if 'GridPos' in info:
                                    grid_positions[num] = int(info['GridPos'])
                
                # 建立結果
                winner_num = None
                for num, pos in final_positions.items():
                    if pos == 1:
                        winner_num = num
                        break
                
                for num, finish_pos in final_positions.items():
                    driver_info = drivers.get(num, {})
                    grid_pos = grid_positions.get(num, finish_pos)  # 如果沒有 grid，用 finish
                    
                    result = RaceResult(
                        year=year,
                        track=track,
                        driver=driver_info.get('name', f'#{num}'),
                        team=driver_info.get('team', 'Unknown'),
                        grid_position=grid_pos,
                        finish_position=finish_pos,
                        is_winner=(num == winner_num),
                        dnf=(finish_pos > 20)
                    )
                    results.append(result)
                    
            except Exception as e:
                print(f"  [ERROR] 解析 TimingData 失敗: {e}")
        
        return results
    
    def calculate_driver_stats(self, results: List[RaceResult]):
        """計算車手統計數據"""
        
        driver_data = defaultdict(lambda: {
            'races': 0,
            'wins': 0,
            'podiums': 0,
            'finishes': [],
            'grids': [],
            'track_finishes': defaultdict(list)
        })
        
        for r in results:
            d = driver_data[r.driver]
            d['races'] += 1
            if r.is_winner:
                d['wins'] += 1
            if r.finish_position <= 3:
                d['podiums'] += 1
            d['finishes'].append(r.finish_position)
            d['grids'].append(r.grid_position)
            d['track_finishes'][r.track].append(r.finish_position)
        
        for driver, data in driver_data.items():
            self.driver_stats[driver] = DriverStats(
                driver=driver,
                total_races=data['races'],
                wins=data['wins'],
                podiums=data['podiums'],
                avg_finish=np.mean(data['finishes']) if data['finishes'] else 10,
                avg_grid=np.mean(data['grids']) if data['grids'] else 10,
                win_rate=data['wins'] / data['races'] if data['races'] > 0 else 0,
                podium_rate=data['podiums'] / data['races'] if data['races'] > 0 else 0,
                track_performances={
                    track: finishes for track, finishes in data['track_finishes'].items()
                }
            )
        
        print(f"[INFO] 計算 {len(self.driver_stats)} 位車手的統計數據")
    
    def prepare_features(self, results: List[RaceResult]) -> Tuple[np.ndarray, np.ndarray]:
        """準備訓練特徵"""
        
        features = []
        labels = []
        
        for r in results:
            # 跳過 DNF
            if r.dnf:
                continue
            
            # 特徵
            f = self._extract_features(r)
            features.append(f)
            
            # 標籤: 是否獲勝
            labels.append(1 if r.is_winner else 0)
        
        X = np.array(features)
        y = np.array(labels)
        
        print(f"[INFO] 準備 {len(features)} 筆訓練數據，{sum(labels)} 個贏家")
        
        return X, y
    
    def _extract_features(self, result: RaceResult) -> List[float]:
        """提取特徵"""
        
        # 1. 起跑位置 (歸一化)
        grid_normalized = result.grid_position / 20.0
        
        # 2. 車隊評分
        team_rating = self.TEAM_RATINGS_2024.get(result.team, 0.5)
        
        # 3. 賽道超車難度
        track_difficulty = self.overtaking_difficulty.get(result.track, 0.5)
        
        # 4. 車手統計
        driver_stat = self.driver_stats.get(result.driver)
        if driver_stat:
            win_rate = driver_stat.win_rate
            podium_rate = driver_stat.podium_rate
            avg_finish_normalized = driver_stat.avg_finish / 20.0
            
            # 車手在該賽道的歷史表現
            track_history = driver_stat.track_performances.get(result.track, [])
            track_avg = np.mean(track_history) / 20.0 if track_history else 0.5
        else:
            win_rate = 0.0
            podium_rate = 0.0
            avg_finish_normalized = 0.5
            track_avg = 0.5
        
        # 5. 起跑位置優勢 (與超車難度交互)
        # 超車越難，起跑位置越重要
        grid_advantage = (1 - grid_normalized) * track_difficulty
        
        # 6. 前排起跑 (P1-P3)
        is_front_row = 1.0 if result.grid_position <= 3 else 0.0
        
        # 7. 桿位優勢
        is_pole = 1.0 if result.grid_position == 1 else 0.0
        
        features = [
            grid_normalized,           # 0: 起跑位置
            team_rating,               # 1: 車隊評分
            track_difficulty,          # 2: 超車難度
            win_rate,                  # 3: 車手勝率
            podium_rate,               # 4: 車手登台率
            avg_finish_normalized,     # 5: 平均完賽位置
            track_avg,                 # 6: 賽道歷史表現
            grid_advantage,            # 7: 起跑優勢
            is_front_row,              # 8: 前排起跑
            is_pole,                   # 9: 桿位
        ]
        
        self.feature_names = [
            'grid_position', 'team_rating', 'track_difficulty',
            'driver_win_rate', 'driver_podium_rate', 'avg_finish',
            'track_history', 'grid_advantage', 'is_front_row', 'is_pole'
        ]
        
        return features
    
    def train(self, X: np.ndarray, y: np.ndarray):
        """訓練模型"""
        
        if not HAS_XGBOOST:
            print("[WARN] 使用簡化邏輯回歸模型")
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
            'use_label_encoder': False,
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
        
        print(f"[INFO] 驗證集準確率: {accuracy:.3f}")
        print(f"[INFO] 驗證集 Log Loss: {logloss:.3f}")
        
        # 特徵重要性
        print("\n[INFO] 特徵重要性:")
        importance = self.model.feature_importances_
        for name, imp in sorted(zip(self.feature_names, importance), key=lambda x: -x[1]):
            print(f"  {name}: {imp:.3f}")
    
    def _train_simple_model(self, X: np.ndarray, y: np.ndarray):
        """簡化模型 (無 XGBoost 時使用)"""
        
        # 使用加權特徵計算
        # 權重基於經驗
        self.simple_weights = {
            'grid_position': -3.0,      # 起跑位置越前越好
            'team_rating': 2.0,         # 車隊越強越好
            'track_difficulty': 1.0,    # 超車難度影響
            'driver_win_rate': 4.0,     # 歷史勝率
            'driver_podium_rate': 2.0,  # 登台率
            'avg_finish': -1.5,         # 平均完賽位置
            'track_history': -1.0,      # 賽道歷史
            'grid_advantage': 2.5,      # 起跑優勢
            'is_front_row': 1.5,        # 前排加成
            'is_pole': 2.0,             # 桿位加成
        }
        
        print("[INFO] 簡化模型訓練完成")
    
    def predict_race(self, race_data: List[Dict]) -> List[Dict]:
        """預測單場比賽的勝率"""
        
        predictions = []
        
        # 提取所有車手的特徵
        features = []
        for driver_data in race_data:
            r = RaceResult(
                year=driver_data.get('year', 2025),
                track=driver_data.get('track', ''),
                driver=driver_data.get('driver', ''),
                team=driver_data.get('team', ''),
                grid_position=driver_data.get('grid_position', 10),
                finish_position=0,
            )
            f = self._extract_features(r)
            features.append(f)
        
        X = np.array(features)
        
        # 預測概率
        if self.model is not None and HAS_XGBOOST:
            probabilities = self.model.predict_proba(X)[:, 1]
        else:
            # 簡化計算
            probabilities = self._simple_predict(X)
        
        # 標準化概率 (總和 = 1)
        prob_sum = np.sum(probabilities)
        if prob_sum > 0:
            probabilities = probabilities / prob_sum
        
        # 組裝結果
        for i, driver_data in enumerate(race_data):
            predictions.append({
                'driver': driver_data.get('driver', ''),
                'team': driver_data.get('team', ''),
                'grid_position': driver_data.get('grid_position', 0),
                'win_probability': float(probabilities[i]),
                'win_probability_pct': f"{probabilities[i] * 100:.1f}%"
            })
        
        # 按勝率排序
        predictions.sort(key=lambda x: -x['win_probability'])
        
        return predictions
    
    def _simple_predict(self, X: np.ndarray) -> np.ndarray:
        """簡化預測 (無 XGBoost)"""
        
        weights = np.array([
            self.simple_weights.get(name, 0)
            for name in self.feature_names
        ])
        
        # 加權分數
        scores = np.dot(X, weights)
        
        # Softmax 轉換為概率
        exp_scores = np.exp(scores - np.max(scores))
        probabilities = exp_scores / np.sum(exp_scores)
        
        return probabilities
    
    def save_model(self, path: str = "models/win_probability_phase1.pkl"):
        """保存模型"""
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        model_data = {
            'model': self.model,
            'driver_stats': self.driver_stats,
            'overtaking_difficulty': self.overtaking_difficulty,
            'feature_names': self.feature_names,
            'team_ratings': self.TEAM_RATINGS_2024,
        }
        
        if not HAS_XGBOOST:
            model_data['simple_weights'] = getattr(self, 'simple_weights', {})
        
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"[INFO] 模型已保存到: {path}")
    
    def load_model(self, path: str = "models/win_probability_phase1.pkl"):
        """載入模型"""
        
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data.get('model')
        self.driver_stats = model_data.get('driver_stats', {})
        self.overtaking_difficulty = model_data.get('overtaking_difficulty', {})
        self.feature_names = model_data.get('feature_names', [])
        
        if 'simple_weights' in model_data:
            self.simple_weights = model_data['simple_weights']
        
        print(f"[INFO] 模型已載入: {path}")


def evaluate_on_2025(model: WinProbabilityModel, base_path: str):
    """在 2025 數據上評估模型"""
    
    print("\n" + "=" * 60)
    print("2025 賽季預測評估")
    print("=" * 60)
    
    # 載入 2025 數據
    results_2025 = model.load_race_results([2025])
    
    # 按比賽分組
    races = defaultdict(list)
    for r in results_2025:
        races[r.track].append(r)
    
    correct_top1 = 0
    correct_top3 = 0
    total_races = 0
    
    for track, race_results in races.items():
        if not race_results:
            continue
        
        # 找出真正的贏家
        actual_winner = None
        for r in race_results:
            if r.is_winner:
                actual_winner = r.driver
                break
        
        if not actual_winner:
            continue
        
        # 準備預測數據
        race_data = [
            {
                'year': r.year,
                'track': r.track,
                'driver': r.driver,
                'team': r.team,
                'grid_position': r.grid_position,
            }
            for r in race_results
        ]
        
        # 預測
        predictions = model.predict_race(race_data)
        
        # 評估
        predicted_top3 = [p['driver'] for p in predictions[:3]]
        predicted_winner = predictions[0]['driver'] if predictions else None
        
        is_top1_correct = (predicted_winner == actual_winner)
        is_top3_correct = (actual_winner in predicted_top3)
        
        if is_top1_correct:
            correct_top1 += 1
        if is_top3_correct:
            correct_top3 += 1
        total_races += 1
        
        # 輸出詳情
        status = "✅" if is_top1_correct else ("⚠️" if is_top3_correct else "❌")
        print(f"\n{track}:")
        print(f"  實際贏家: {actual_winner}")
        print(f"  預測 Top 3: {predicted_top3}")
        print(f"  結果: {status}")
    
    # 總結
    print("\n" + "=" * 60)
    print("評估總結")
    print("=" * 60)
    print(f"總比賽數: {total_races}")
    print(f"Top-1 準確率: {correct_top1}/{total_races} = {correct_top1/total_races*100:.1f}%")
    print(f"Top-3 準確率: {correct_top3}/{total_races} = {correct_top3/total_races*100:.1f}%")
    
    return {
        'total_races': total_races,
        'top1_accuracy': correct_top1 / total_races if total_races > 0 else 0,
        'top3_accuracy': correct_top3 / total_races if total_races > 0 else 0,
    }


def main():
    """主函數"""
    
    print("=" * 60)
    print("F1 勝率預測模型 - Phase 1 訓練")
    print("=" * 60)
    
    # 設定路徑
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 初始化模型
    model = WinProbabilityModel(base_path)
    
    # 載入超車難度
    model.load_overtaking_difficulty()
    
    # 載入訓練數據 (2023 + 2024)
    print("\n[STEP 1] 載入訓練數據...")
    train_results = model.load_race_results([2023, 2024])
    
    # 計算車手統計
    print("\n[STEP 2] 計算車手統計...")
    model.calculate_driver_stats(train_results)
    
    # 準備特徵
    print("\n[STEP 3] 準備訓練特徵...")
    X, y = model.prepare_features(train_results)
    
    # 訓練模型
    print("\n[STEP 4] 訓練模型...")
    model.train(X, y)
    
    # 保存模型
    print("\n[STEP 5] 保存模型...")
    model_path = os.path.join(base_path, "models", "win_probability_phase1.pkl")
    model.save_model(model_path)
    
    # 在 2025 上評估
    print("\n[STEP 6] 評估模型...")
    metrics = evaluate_on_2025(model, base_path)
    
    return model, metrics


if __name__ == "__main__":
    main()
