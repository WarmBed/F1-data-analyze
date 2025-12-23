#!/usr/bin/env python3
"""
v3.5 批次訓練器 - 添加 FP3→Q 改進率特徵

v3.5 特徵架構 (20 特徵):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【v3.0 基礎特徵 (8)】
  1-4.  ideal_s1, ideal_s2, ideal_s3, ideal_lap (圈速基礎)
  5-7.  low_speed_apex, mid_speed_apex, high_speed_apex (彎道速度)
  8.    max_speed (速度陷阱)

【v3.3 交互特徵 (3)】
  9.    s1_s2_ratio (賽道平衡)
  10.   sector_cv (圈速一致性)
  11.   s2_lap_ratio (S2 權重)

【v3.4 速度特徵 (3)】
  12.   max_speed_lap_ratio (速度效率)
  13.   max_speed_s2_ratio (直道優勢)
  14.   speed_consistency (彎道平衡)

【v3.5 改進率特徵 (6)】✨ 新增
  15.   track_avg_improvement_rate (賽道平均 FP3→Q 改進率)
  16.   adjusted_ideal_lap (修正後 ideal lap)
  17.   fp3_relative_position (FP3 相對排名)
  18.   fp3_gap_to_fastest (FP3 與最快的差距)
  19.   is_top_driver (頂尖車手標記)
  20.   driver_historical_improvement (車手歷史改進能力)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

核心改進：
1. 數據清洗：移除 FP3→Q 改進率異常的樣本（天氣/數據錯誤）
2. 改進率特徵：捕捉 FP3→Q 的系統性提升模式
3. 車手能力：區分頂尖車手的 Q 極限發揮能力
"""
import sys
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor
from collections import defaultdict

# 導入 v3.0 trainer 用於數據載入
sys.path.append(str(Path(__file__).parent))
from CLI_modules.cli.prediction.track_specific_trainer_v3 import TrackSpecificTrainerV3


class BatchTrainerV3_5:
    """v3.5 批次訓練器 - 添加 FP3→Q 改進率特徵"""
    
    def __init__(self):
        self.base_trainer = TrackSpecificTrainerV3(verbose=False)
        self.models_dir = Path("models/track_specific_v3.5")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = {}
        self.prediction_results = {}
        
        # 從 FP3→Q 分析結果載入賽道改進率（清洗後）
        self.track_improvement_rates = self._load_track_improvement_rates()
        
        # 頂尖車手列表（2022-2024 積分前列車手）
        self.top_drivers = ['VER', 'HAM', 'LEC', 'NOR', 'PIA', 'SAI', 'RUS', 'PER']
        
        # 車手歷史改進能力（從分析結果計算）
        self.driver_improvement_dict = {}
    
    def _load_track_improvement_rates(self) -> dict:
        """
        載入賽道改進率（從 fp3_q_improvement_analysis.json）
        並移除異常數據後重新計算
        """
        print("\n[載入賽道改進率]")
        
        analysis_file = Path("fp3_q_improvement_analysis.json")
        if not analysis_file.exists():
            print("  [警告] 找不到分析檔案，使用預設值")
            return self._get_default_improvement_rates()
        
        with open(analysis_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 使用清洗後的數據（移除異常值）
        track_rates = {}
        for track, track_data in data['by_track'].items():
            avg_rate = track_data['avg_improvement_rate']
            
            # 異常檢測：改進率 < -5% 或 > 15% 視為異常
            if avg_rate < -0.05 or avg_rate > 0.15:
                print(f"  [異常] {track:20s}: {avg_rate*100:6.2f}% (使用預設值 1.5%)")
                track_rates[track] = 0.015  # 使用保守的預設值
            else:
                track_rates[track] = avg_rate
                print(f"  [正常] {track:20s}: {avg_rate*100:6.2f}%")
        
        return track_rates
    
    def _get_default_improvement_rates(self) -> dict:
        """預設賽道改進率（基於物理原則的保守估計）"""
        return {
            # 高速賽道（引擎模式影響大）
            'Italy': 0.0074,
            'Belgium': 0.0150,  # 修正：排除 2024 異常
            'Great Britain': 0.0126,  # 僅使用 2023 數據
            'Austria': 0.015,
            
            # 街道賽（賽道進化明顯）
            'Monaco': 0.0159,
            'Singapore': 0.0075,  # 修正：排除 2022 異常
            'Azerbaijan': 0.0091,
            'Saudi Arabia': 0.0117,  # 修正：排除 2023 異常
            'Miami': 0.0119,
            'Las Vegas': 0.0121,
            
            # 技術型賽道
            'Hungary': 0.0041,  # 修正：排除 2022 異常
            'Netherlands': 0.0149,  # 修正：排除 2024 異常
            'Spain': 0.0159,
            'Japan': 0.0136,
            'China': 0.015,
            
            # 混合型賽道
            'Bahrain': 0.0189,
            'Australia': 0.0097,
            'Canada': 0.0095,  # 修正：排除 2022 異常
            'Abu Dhabi': 0.0104,
            'Brazil': 0.012,
            'United States': 0.0131,
            'Mexico': 0.0063,
            'Qatar': 0.012,
            'Emilia Romagna': 0.012,
        }
    
    def clean_outlier_samples(self, df: pd.DataFrame, track_name: str) -> pd.DataFrame:
        """
        清洗異常樣本（FP3→Q 改進率異常）
        
        異常標準：
        - 改進率 < -5%（Q 比 FP3 慢太多，可能是天氣變化）
        - 改進率 > 15%（改進過大，可能是數據錯誤）
        """
        if df.empty:
            return df
        
        # 計算改進率
        df['improvement'] = df['ideal_lap'] - df['actual_q_time']
        df['improvement_rate'] = df['improvement'] / df['ideal_lap']
        
        # 異常檢測
        valid_mask = (df['improvement_rate'] >= -0.05) & (df['improvement_rate'] <= 0.15)
        
        removed = len(df) - valid_mask.sum()
        if removed > 0:
            print(f"  [數據清洗] 移除 {removed} 個異常樣本（改進率異常）")
            
            # 顯示被移除的樣本資訊
            outliers = df[~valid_mask]
            for _, row in outliers.iterrows():
                print(f"    - {row['year']} {row.get('driver', 'N/A')}: "
                      f"FP3 {row['ideal_lap']:.3f}s → Q {row['actual_q_time']:.3f}s "
                      f"({row['improvement_rate']*100:+.1f}%)")
        
        # 移除臨時欄位
        df_clean = df[valid_mask].copy()
        df_clean = df_clean.drop(['improvement', 'improvement_rate'], axis=1)
        
        return df_clean
    
    def add_v35_features(self, df: pd.DataFrame, track_name: str) -> pd.DataFrame:
        """添加 v3.5 所有特徵（v3.4 + 6 個改進率特徵）"""
        df = df.copy()
        
        # ========== v3.3 交互特徵 (保留) ==========
        df['s1_s2_ratio'] = df['ideal_s1'] / (df['ideal_s2'] + 1e-6)
        sector_mean = (df['ideal_s1'] + df['ideal_s2'] + df['ideal_s3']) / 3
        sector_std = df[['ideal_s1', 'ideal_s2', 'ideal_s3']].std(axis=1)
        df['sector_cv'] = sector_std / (sector_mean + 1e-6)
        df['s2_lap_ratio'] = df['ideal_s2'] / (df['ideal_lap'] + 1e-6)
        
        # ========== v3.4 速度特徵 (保留) ==========
        df['max_speed_lap_ratio'] = df['max_speed'] / (df['ideal_lap'] + 1e-6)
        df['max_speed_s2_ratio'] = df['max_speed'] / (df['ideal_s2'] + 1e-6)
        apex_std = df[['low_speed_apex', 'mid_speed_apex', 'high_speed_apex']].std(axis=1)
        df['speed_consistency'] = apex_std / (df['max_speed'] + 1e-6)
        
        # ========== v3.5 改進率特徵 (新增) ==========
        
        # 特徵 15: 賽道平均改進率
        track_rate = self.track_improvement_rates.get(track_name, 0.015)  # 預設 1.5%
        df['track_avg_improvement_rate'] = track_rate
        
        # 特徵 16: 修正後的 ideal lap（考慮預期改進）
        df['adjusted_ideal_lap'] = df['ideal_lap'] * (1 - track_rate)
        
        # 特徵 17: FP3 相對排名（該車手在該場的 FP3 排名）
        # 使用 groupby 確保同一場比賽內排名
        df['fp3_relative_position'] = df.groupby(['year'])['ideal_lap'].rank(method='min')
        
        # 特徵 18: FP3 與最快的差距
        df['fp3_gap_to_fastest'] = df.groupby(['year'])['ideal_lap'].transform(lambda x: x - x.min())
        
        # 特徵 19: 頂尖車手標記
        df['is_top_driver'] = df['driver'].isin(self.top_drivers).astype(int)
        
        # 特徵 20: 車手歷史改進能力
        # （簡化版：頂尖車手 +0.2%，其他車手 0%）
        df['driver_historical_improvement'] = df['is_top_driver'] * 0.002
        
        return df
    
    def train_single_track(self, race_name: str, start_year: int = 2022, 
                          end_year: int = 2024) -> dict:
        """訓練單一賽道模型"""
        print(f"\n{'='*70}")
        print(f"Training: {race_name}")
        print(f"{'='*70}")
        
        try:
            # 步驟 1: 使用 v3.0 trainer 載入數據
            try:
                df = self.base_trainer.load_training_data_v3(race_name, start_year, end_year)
            except Exception as e:
                print(f"  [ERROR] 載入數據失敗: {e}")
                print(f"  [SKIP] {race_name} - 數據格式問題")
                return None
            
            if df.empty:
                print(f"  [SKIP] No data available")
                return None
            
            print(f"  [原始數據] {len(df)} 樣本")
            
            # 步驟 2: 數據清洗（移除異常樣本）
            df = self.clean_outlier_samples(df, race_name)
            
            if df.empty:
                print(f"  [SKIP] No valid data after cleaning")
                return None
            
            print(f"  [清洗後] {len(df)} 樣本")
            
            # 步驟 3: 添加所有特徵 (v3.3 + v3.4 + v3.5)
            df = self.add_v35_features(df, race_name)
            
            # 清理 NaN/Inf
            if df.isnull().any().any() or np.isinf(df.select_dtypes(include=[np.number])).any().any():
                df = df.replace([np.inf, -np.inf], np.nan).dropna()
            
            if df.empty:
                print(f"  [SKIP] No valid data after feature engineering")
                return None
            
            # 步驟 4: 準備特徵 (20 個)
            feature_cols = [
                # v3.0 基礎特徵 (8)
                'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
                'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
                # v3.3 交互特徵 (3)
                's1_s2_ratio', 'sector_cv', 's2_lap_ratio',
                # v3.4 速度特徵 (3)
                'max_speed_lap_ratio', 'max_speed_s2_ratio', 'speed_consistency',
                # v3.5 改進率特徵 (6)
                'track_avg_improvement_rate', 'adjusted_ideal_lap',
                'fp3_relative_position', 'fp3_gap_to_fastest',
                'is_top_driver', 'driver_historical_improvement'
            ]
            
            X = df[feature_cols]
            y = df['actual_q_time']
            
            # 步驟 5: 訓練模型
            model = XGBRegressor(
                n_estimators=50,
                max_depth=3,
                learning_rate=0.1,
                random_state=42,
                verbosity=0
            )
            
            model.fit(X, y)
            
            # 步驟 6: 評估效能
            y_pred = model.predict(X)
            r2 = r2_score(y, y_pred)
            mae = mean_absolute_error(y, y_pred)
            
            # 步驟 7: 保存模型
            model_file = self.models_dir / f"{race_name}.pkl"
            with open(model_file, 'wb') as f:
                pickle.dump(model, f)
            
            # 步驟 8: 特徵重要性分析
            feature_importance = dict(zip(feature_cols, model.feature_importances_))
            
            # 計算 max_speed 相關特徵的總占比
            max_speed_features = ['max_speed', 'max_speed_lap_ratio', 'max_speed_s2_ratio', 'speed_consistency']
            max_speed_total = sum(feature_importance.get(f, 0) for f in max_speed_features)
            
            # 計算改進率特徵的總占比
            improvement_features = ['track_avg_improvement_rate', 'adjusted_ideal_lap', 
                                   'fp3_relative_position', 'fp3_gap_to_fastest',
                                   'is_top_driver', 'driver_historical_improvement']
            improvement_total = sum(feature_importance.get(f, 0) for f in improvement_features)
            
            print(f"  [SUCCESS] R² {r2:.4f}, MAE {mae:.3f}s, Samples {len(df)}")
            print(f"  max_speed 相關: {max_speed_total*100:5.2f}%, 改進率相關: {improvement_total*100:5.2f}%")
            
            # 顯示 Top 5 特徵
            top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"  Top 5 特徵:")
            for feat, imp in top_features:
                print(f"    {feat:30s} {imp*100:6.2f}%")
            
            return {
                'race': race_name,
                'r2': r2,
                'mae': mae,
                'samples': len(df),
                'max_speed_ratio': max_speed_total,
                'improvement_ratio': improvement_total,
                'top_features': dict(top_features),
                'all_features': feature_importance
            }
        
        except Exception as e:
            print(f"  [ERROR] {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def train_all_tracks(self):
        """訓練所有賽道"""
        # 2025 賽道列表
        tracks = [
            "Australia", "China", "Japan", "Bahrain", "Saudi Arabia",
            "Miami", "Monaco", "Spain", "Canada", "Austria",
            "Great Britain", "Belgium", "Hungary", "Netherlands",
            "Italy", "Azerbaijan", "Singapore", "United States",
            "Mexico", "Brazil", "Las Vegas", "Qatar", "Abu Dhabi"
        ]
        
        print("\n" + "="*70)
        print("v3.5 批次訓練 - 所有賽道")
        print("="*70)
        
        success_count = 0
        
        for track in tracks:
            result = self.train_single_track(track, 2022, 2024)
            if result:
                self.results[track] = result
                success_count += 1
        
        self.generate_summary_report()
        self.save_results()
        
        print(f"\n[完成] 成功訓練 {success_count}/{len(tracks)} 個賽道")
    
    def generate_summary_report(self):
        """生成訓練總結報告"""
        if not self.results:
            print("\n[錯誤] 沒有訓練結果")
            return
        
        print("\n" + "="*70)
        print("v3.5 訓練總結報告")
        print("="*70)
        
        # 整體統計
        all_r2 = [r['r2'] for r in self.results.values()]
        all_mae = [r['mae'] for r in self.results.values()]
        all_max_speed = [r['max_speed_ratio'] for r in self.results.values()]
        all_improvement = [r['improvement_ratio'] for r in self.results.values()]
        
        print(f"\n[整體表現]")
        print(f"  平均 R²: {np.mean(all_r2):.4f} (std: {np.std(all_r2):.4f})")
        print(f"  平均 MAE: {np.mean(all_mae):.3f}s (std: {np.std(all_mae):.3f}s)")
        print(f"  平均 max_speed 占比: {np.mean(all_max_speed)*100:.2f}%")
        print(f"  平均改進率特徵占比: {np.mean(all_improvement)*100:.2f}%")
        
        # 問題賽道分析
        print(f"\n[Great Britain & Canada 分析]")
        for track in ['Great Britain', 'Canada']:
            if track in self.results:
                result = self.results[track]
                print(f"  {track}:")
                print(f"    R²: {result['r2']:.4f}, MAE: {result['mae']:.3f}s")
                print(f"    max_speed 占比: {result['max_speed_ratio']*100:.2f}%")
                print(f"    改進率特徵占比: {result['improvement_ratio']*100:.2f}%")
        
        # max_speed 依賴排名
        print(f"\n[Top 5 max_speed 依賴賽道]")
        sorted_by_max_speed = sorted(
            self.results.items(),
            key=lambda x: x[1]['max_speed_ratio'],
            reverse=True
        )[:5]
        
        for i, (track, result) in enumerate(sorted_by_max_speed, 1):
            print(f"  {i}. {track:20s}: {result['max_speed_ratio']*100:5.2f}%")
        
        # 改進率特徵貢獻排名
        print(f"\n[Top 5 改進率特徵貢獻賽道]")
        sorted_by_improvement = sorted(
            self.results.items(),
            key=lambda x: x[1]['improvement_ratio'],
            reverse=True
        )[:5]
        
        for i, (track, result) in enumerate(sorted_by_improvement, 1):
            print(f"  {i}. {track:20s}: {result['improvement_ratio']*100:5.2f}%")
    
    def save_results(self):
        """保存訓練結果"""
        output_file = Path("v3.5_training_results.json")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n[保存結果] {output_file}")


def main():
    trainer = BatchTrainerV3_5()
    trainer.train_all_tracks()


if __name__ == '__main__':
    main()
