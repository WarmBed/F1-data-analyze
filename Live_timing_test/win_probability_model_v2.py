#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
F1 勝率預測模型 - Phase 1: 使用 FastF1 訓練數據
==============================================

使用 FastF1 載入官方 F1 數據（比賽結果、排位賽）來訓練模型。

訓練集: 2023 + 2024 (~46 場比賽)
測試集: 2025 (目前可用的比賽)

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

# FastF1
try:
    import fastf1
    fastf1.Cache.enable_cache('f1_analysis_cache')
    HAS_FASTF1 = True
except ImportError:
    HAS_FASTF1 = False
    print("[ERROR] FastF1 未安裝!")

# XGBoost
try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("[WARN] XGBoost 未安裝，將使用簡化模型")

# sklearn
try:
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, log_loss
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("[WARN] sklearn 未安裝")


@dataclass
class RaceResult:
    """單場比賽結果"""
    year: int
    round: int
    track: str
    driver: str
    driver_code: str
    team: str
    grid_position: int
    finish_position: int
    is_winner: bool = False
    status: str = "Finished"


class WinProbabilityModelV2:
    """勝率預測模型 V2 - 使用 FastF1"""
    
    # 2024 賽季車隊評分 (基於建造者積分)
    TEAM_RATINGS = {
        "Red Bull Racing": 0.95,
        "Ferrari": 0.88,
        "McLaren": 0.90,
        "Mercedes": 0.85,
        "Aston Martin": 0.70,
        "Alpine": 0.55,
        "Williams": 0.45,
        "RB": 0.50,
        "Kick Sauber": 0.35,
        "Haas F1 Team": 0.40,
        # 2023 別名
        "Alfa Romeo": 0.35,
        "AlphaTauri": 0.50,
    }
    
    # 2023-2024 賽季時間表
    SCHEDULE = {
        2023: [
            "Bahrain", "Saudi Arabia", "Australia", "Azerbaijan", "Miami",
            "Monaco", "Spain", "Canada", "Austria", "Britain", 
            "Hungary", "Belgium", "Netherlands", "Italy", "Singapore",
            "Japan", "Qatar", "United States", "Mexico", "Brazil",
            "Las Vegas", "Abu Dhabi"
        ],
        2024: [
            "Bahrain", "Saudi Arabia", "Australia", "Japan", "China",
            "Miami", "Monaco", "Canada", "Spain", "Austria",
            "Britain", "Hungary", "Belgium", "Netherlands", "Italy",
            "Azerbaijan", "Singapore", "United States", "Mexico", "Brazil",
            "Las Vegas", "Qatar", "Abu Dhabi"
        ],
        2025: [
            "Australia", "China", "Japan", "Bahrain", "Saudi Arabia",
            "Miami", "Monaco", "Spain", "Canada", "Austria",
            "Britain", "Belgium", "Hungary", "Netherlands", "Italy",
            "Azerbaijan", "Singapore", "United States", "Mexico", "Brazil",
            "Las Vegas", "Qatar", "Abu Dhabi"
        ]
    }
    
    def __init__(self, base_path: str = "."):
        self.base_path = base_path
        self.model = None
        self.driver_stats = {}
        self.overtaking_difficulty = {}
        self.feature_names = []
        self.simple_weights = {}
        
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
    
    def load_race_results_fastf1(self, years: List[int]) -> List[RaceResult]:
        """使用 FastF1 載入比賽結果"""
        
        if not HAS_FASTF1:
            print("[ERROR] FastF1 未安裝!")
            return []
        
        all_results = []
        
        for year in years:
            schedule = self.SCHEDULE.get(year, [])
            
            for round_num, track in enumerate(schedule, 1):
                print(f"[INFO] 載入 {year} R{round_num} {track}...", end=" ")
                
                try:
                    session = fastf1.get_session(year, round_num, 'R')
                    # 只載入最小必要數據，不載入遙測
                    session.load(telemetry=False, weather=False, messages=False)
                    
                    results = session.results
                    
                    if results is None or results.empty:
                        print("無數據")
                        continue
                    
                    count = 0
                    for _, row in results.iterrows():
                        grid_pos = row.get('GridPosition', 0)
                        finish_pos = row.get('Position', 0)
                        
                        # 跳過無效數據
                        if not grid_pos or not finish_pos:
                            continue
                            
                        result = RaceResult(
                            year=year,
                            round=round_num,
                            track=track,
                            driver=row.get('FullName', ''),
                            driver_code=row.get('Abbreviation', ''),
                            team=row.get('TeamName', ''),
                            grid_position=int(grid_pos),
                            finish_position=int(finish_pos),
                            is_winner=(int(finish_pos) == 1),
                            status=row.get('Status', 'Finished')
                        )
                        all_results.append(result)
                        count += 1
                    
                    print(f"OK ({count} 車手)")
                        
                except Exception as e:
                    print(f"失敗: {e}")
                    continue
        
        print(f"\n[INFO] 總共載入 {len(all_results)} 筆比賽結果")
        return all_results
    
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
            # 使用車手代碼作為 key
            key = r.driver_code if r.driver_code else r.driver
            d = driver_data[key]
            
            # 跳過 DNF (位置 > 20 或狀態不是 Finished)
            if r.finish_position > 20:
                continue
                
            d['races'] += 1
            if r.is_winner:
                d['wins'] += 1
            if r.finish_position <= 3:
                d['podiums'] += 1
            d['finishes'].append(r.finish_position)
            d['grids'].append(r.grid_position)
            
            # 標準化賽道名稱
            track_normalized = self._normalize_track_name(r.track)
            d['track_finishes'][track_normalized].append(r.finish_position)
        
        for driver, data in driver_data.items():
            self.driver_stats[driver] = {
                'total_races': data['races'],
                'wins': data['wins'],
                'podiums': data['podiums'],
                'avg_finish': np.mean(data['finishes']) if data['finishes'] else 10,
                'avg_grid': np.mean(data['grids']) if data['grids'] else 10,
                'win_rate': data['wins'] / data['races'] if data['races'] > 0 else 0,
                'podium_rate': data['podiums'] / data['races'] if data['races'] > 0 else 0,
                'track_performances': dict(data['track_finishes'])
            }
        
        print(f"[INFO] 計算 {len(self.driver_stats)} 位車手的統計數據")
        
    def _normalize_track_name(self, track: str) -> str:
        """標準化賽道名稱"""
        
        # 移除空格並轉換常見變體
        mapping = {
            "Saudi Arabia": "Saudi_Arabian",
            "United States": "United_States",
            "Great Britain": "British",
            "Britain": "British",
            "Las Vegas": "Las_Vegas",
            "Abu Dhabi": "Abu_Dhabi",
        }
        
        return mapping.get(track, track.replace(" ", "_"))
    
    def prepare_features(self, results: List[RaceResult]) -> Tuple[np.ndarray, np.ndarray]:
        """準備訓練特徵"""
        
        features = []
        labels = []
        
        for r in results:
            # 跳過無效數據
            if r.finish_position <= 0 or r.grid_position <= 0:
                continue
            if r.finish_position > 20:  # DNF
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
        
        driver_key = result.driver_code if result.driver_code else result.driver
        track_normalized = self._normalize_track_name(result.track)
        
        # 1. 起跑位置 (歸一化)
        grid_normalized = min(result.grid_position, 20) / 20.0
        
        # 2. 車隊評分
        team_rating = self.TEAM_RATINGS.get(result.team, 0.5)
        
        # 3. 賽道超車難度
        track_difficulty = self.overtaking_difficulty.get(track_normalized, 0.5)
        
        # 4. 車手統計
        driver_stat = self.driver_stats.get(driver_key, {})
        win_rate = driver_stat.get('win_rate', 0.0)
        podium_rate = driver_stat.get('podium_rate', 0.0)
        avg_finish = driver_stat.get('avg_finish', 10)
        avg_finish_normalized = min(avg_finish, 20) / 20.0
        
        # 5. 車手在該賽道的歷史表現
        track_history = driver_stat.get('track_performances', {}).get(track_normalized, [])
        track_avg = np.mean(track_history) / 20.0 if track_history else 0.5
        
        # 6. 起跑位置優勢 (與超車難度交互)
        grid_advantage = (1 - grid_normalized) * track_difficulty
        
        # 7. 前排起跑 (P1-P3)
        is_front_row = 1.0 if result.grid_position <= 3 else 0.0
        
        # 8. 桿位
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
            bar = "█" * int(imp * 30)
            print(f"  {name:20s}: {imp:.3f} {bar}")
    
    def _train_simple_model(self, X: np.ndarray, y: np.ndarray):
        """簡化模型 (無 XGBoost 時使用)"""
        
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
        """預測單場比賽的勝率"""
        
        predictions = []
        
        # 提取所有車手的特徵
        features = []
        for driver_data in race_data:
            r = RaceResult(
                year=driver_data.get('year', 2025),
                round=0,
                track=driver_data.get('track', ''),
                driver=driver_data.get('driver', ''),
                driver_code=driver_data.get('driver_code', ''),
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
            probabilities = self._simple_predict(X)
        
        # 標準化概率 (總和 = 1)
        prob_sum = np.sum(probabilities)
        if prob_sum > 0:
            probabilities = probabilities / prob_sum
        
        # 組裝結果
        for i, driver_data in enumerate(race_data):
            predictions.append({
                'driver': driver_data.get('driver', ''),
                'driver_code': driver_data.get('driver_code', ''),
                'team': driver_data.get('team', ''),
                'grid_position': driver_data.get('grid_position', 0),
                'win_probability': float(probabilities[i]),
                'win_probability_pct': f"{probabilities[i] * 100:.1f}%"
            })
        
        # 按勝率排序
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
    
    def save_model(self, path: str = "models/win_probability_phase1_v2.pkl"):
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
        
        print(f"[INFO] 模型已保存到: {path}")
    
    def load_model(self, path: str = "models/win_probability_phase1_v2.pkl"):
        """載入模型"""
        
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data.get('model')
        self.driver_stats = model_data.get('driver_stats', {})
        self.overtaking_difficulty = model_data.get('overtaking_difficulty', {})
        self.feature_names = model_data.get('feature_names', [])
        self.simple_weights = model_data.get('simple_weights', {})
        
        print(f"[INFO] 模型已載入: {path}")


def evaluate_on_2025(model: WinProbabilityModelV2):
    """在 2025 數據上評估模型"""
    
    print("\n" + "=" * 60)
    print("2025 賽季預測評估")
    print("=" * 60)
    
    if not HAS_FASTF1:
        print("[ERROR] 需要 FastF1 來評估!")
        return {}
    
    # 2025 已完成的比賽 (嘗試載入直到失敗)
    correct_top1 = 0
    correct_top3 = 0
    total_races = 0
    
    for round_num in range(1, 24):  # 最多 23 場
        try:
            session = fastf1.get_session(2025, round_num, 'R')
            session.load(telemetry=False, weather=False, messages=False)
            results = session.results
            
            if results is None or results.empty:
                print(f"[INFO] R{round_num}: 無數據，停止評估")
                break
                
            track = session.event['EventName'] if hasattr(session, 'event') else f"R{round_num}"
                
        except Exception as e:
            print(f"[INFO] R{round_num}: 無法載入 ({e})，停止評估")
            break
        
        # 找出真正的贏家
        winner_code = None
        for _, row in results.iterrows():
            if int(row.get('Position', 0)) == 1:
                winner_code = row.get('Abbreviation', '')
                break
        
        if not winner_code:
            continue
        
        # 準備預測數據
        race_data = []
        for _, row in results.iterrows():
            grid_pos = row.get('GridPosition', 10)
            if not grid_pos or grid_pos == 0:
                grid_pos = 10
            race_data.append({
                'year': 2025,
                'track': track,
                'driver': row.get('FullName', ''),
                'driver_code': row.get('Abbreviation', ''),
                'team': row.get('TeamName', ''),
                'grid_position': int(grid_pos),
            })
        
        # 預測
        predictions = model.predict_race(race_data)
        
        # 評估
        predicted_top3 = [p['driver_code'] for p in predictions[:3]]
        predicted_winner = predictions[0]['driver_code'] if predictions else None
        
        is_top1_correct = (predicted_winner == winner_code)
        is_top3_correct = (winner_code in predicted_top3)
        
        if is_top1_correct:
            correct_top1 += 1
        if is_top3_correct:
            correct_top3 += 1
        total_races += 1
        
        # 輸出詳情
        status_icon = "[O]" if is_top1_correct else ("[~]" if is_top3_correct else "[X]")
        print(f"\nR{round_num} {track}:")
        print(f"  實際贏家: {winner_code}")
        print(f"  預測 Top 3: {predicted_top3}")
        print(f"  預測勝率: {predictions[0]['win_probability_pct']} ({predictions[0]['driver_code']})")
        print(f"  結果: {status_icon}")
    
    # 總結
    if total_races > 0:
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
    print("F1 勝率預測模型 V2 - Phase 1 訓練 (FastF1)")
    print("=" * 60)
    
    # 設定路徑
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 初始化模型
    model = WinProbabilityModelV2(base_path)
    
    # 載入超車難度
    print("\n[STEP 1] 載入賽道超車難度...")
    model.load_overtaking_difficulty()
    
    # 載入訓練數據 (2023 + 2024)
    print("\n[STEP 2] 載入訓練數據 (FastF1)...")
    train_results = model.load_race_results_fastf1([2023, 2024])
    
    if not train_results:
        print("[ERROR] 沒有載入到任何訓練數據!")
        return None, {}
    
    # 計算車手統計
    print("\n[STEP 3] 計算車手統計...")
    model.calculate_driver_stats(train_results)
    
    # 準備特徵
    print("\n[STEP 4] 準備訓練特徵...")
    X, y = model.prepare_features(train_results)
    
    # 訓練模型
    print("\n[STEP 5] 訓練模型...")
    model.train(X, y)
    
    # 保存模型
    print("\n[STEP 6] 保存模型...")
    model_path = os.path.join(base_path, "models", "win_probability_phase1_v2.pkl")
    model.save_model(model_path)
    
    # 在 2025 上評估
    print("\n[STEP 7] 評估模型...")
    metrics = evaluate_on_2025(model)
    
    return model, metrics


if __name__ == "__main__":
    main()
