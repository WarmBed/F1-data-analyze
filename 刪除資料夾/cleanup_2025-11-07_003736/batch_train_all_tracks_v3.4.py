#!/usr/bin/env python3
"""
批次訓練所有賽道的 v3.4 模型 (2022-2024)
然後對 2025 賽季進行預測並生成完整分析報告

v3.4 特徵架構 (14 特徵):
- v3.0 基礎特徵 (8): ideal_s1/s2/s3/lap, low/mid/high_speed_apex, max_speed
- v3.3 交互特徵 (3): s1_s2_ratio, sector_cv, s2_lap_ratio
- v3.4 新增特徵 (3): max_speed_lap_ratio, max_speed_s2_ratio, speed_consistency

目標：解決 Great Britain max_speed 過度主導問題 (55.50% → < 30%)
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

# 導入 v3.0 trainer 用於數據載入
sys.path.append(str(Path(__file__).parent))
from CLI_modules.cli.prediction.track_specific_trainer_v3 import TrackSpecificTrainerV3


class BatchTrainerV3_4:
    """v3.4 批次訓練器 - 添加 max_speed 交互特徵"""
    
    def __init__(self):
        self.base_trainer = TrackSpecificTrainerV3(verbose=False)
        self.models_dir = Path("models/track_specific_v3.4")
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        self.results = {}
        self.prediction_results = {}
    
    def add_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加所有交互特徵 (v3.3 + v3.4)"""
        df = df.copy()
        
        # ========== v3.3 交互特徵 (保留) ==========
        # 交互特徵 1: S1/S2 比率 (賽道平衡指標)
        df['s1_s2_ratio'] = df['ideal_s1'] / (df['ideal_s2'] + 1e-6)
        
        # 交互特徵 2: Sector 變異係數 (一致性指標)
        sector_mean = (df['ideal_s1'] + df['ideal_s2'] + df['ideal_s3']) / 3
        sector_std = df[['ideal_s1', 'ideal_s2', 'ideal_s3']].std(axis=1)
        df['sector_cv'] = sector_std / (sector_mean + 1e-6)
        
        # 交互特徵 3: S2/Lap 比率 (S2 權重指標)
        df['s2_lap_ratio'] = df['ideal_s2'] / (df['ideal_lap'] + 1e-6)
        
        # ========== v3.4 新增特徵 ==========
        # 新特徵 1: max_speed / ideal_lap (速度效率)
        # 物理意義: 單位時間內的速度能力，高值表示直道型賽道
        df['max_speed_lap_ratio'] = df['max_speed'] / (df['ideal_lap'] + 1e-6)
        
        # 新特徵 2: max_speed / ideal_s2 (直道優勢)
        # 物理意義: 長直道速度相對於 S2 圈速，捕捉直道特性
        df['max_speed_s2_ratio'] = df['max_speed'] / (df['ideal_s2'] + 1e-6)
        
        # 新特徵 3: 彎道速度一致性
        # 物理意義: 彎道 vs 直道平衡，低值表示直道依賴型
        apex_std = df[['low_speed_apex', 'mid_speed_apex', 'high_speed_apex']].std(axis=1)
        df['speed_consistency'] = apex_std / (df['max_speed'] + 1e-6)
        
        return df
    
    def train_single_track(self, race_name: str, start_year: int = 2022, 
                          end_year: int = 2024) -> dict:
        """訓練單一賽道模型"""
        print(f"\n{'='*70}")
        print(f"Training: {race_name}")
        print(f"{'='*70}")
        
        try:
            # 步驟 1: 使用 v3.0 trainer 載入數據
            df = self.base_trainer.load_training_data_v3(race_name, start_year, end_year)
            
            if df.empty:
                print(f"  [SKIP] No data available")
                return None
            
            # 步驟 2: 添加交互特徵 (v3.3 + v3.4)
            df = self.add_interaction_features(df)
            
            # 清理 NaN/Inf
            if df.isnull().any().any() or np.isinf(df.select_dtypes(include=[np.number])).any().any():
                df = df.replace([np.inf, -np.inf], np.nan).dropna()
            
            if df.empty:
                print(f"  [SKIP] No valid data after cleaning")
                return None
            
            # 步驟 3: 準備特徵 (14 個)
            feature_cols = [
                # v3.0 基礎特徵 (8)
                'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
                'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
                # v3.3 交互特徵 (3)
                's1_s2_ratio', 'sector_cv', 's2_lap_ratio',
                # v3.4 新增特徵 (3)
                'max_speed_lap_ratio', 'max_speed_s2_ratio', 'speed_consistency'
            ]
            
            X = df[feature_cols]
            y = df['actual_q_time']
            
            # 步驟 4: 訓練模型
            model = XGBRegressor(
                n_estimators=50,
                max_depth=3,
                learning_rate=0.1,
                random_state=42,
                verbosity=0
            )
            
            model.fit(X, y)
            
            # 步驟 5: 評估效能
            y_pred = model.predict(X)
            r2 = r2_score(y, y_pred)
            mae = mean_absolute_error(y, y_pred)
            
            # 步驟 6: 保存模型
            model_file = self.models_dir / f"{race_name}.pkl"
            with open(model_file, 'wb') as f:
                pickle.dump(model, f)
            
            # 步驟 7: 特徵重要性
            feature_importance = dict(zip(feature_cols, model.feature_importances_))
            
            # 計算 max_speed 相關特徵的總占比
            max_speed_features = ['max_speed', 'max_speed_lap_ratio', 'max_speed_s2_ratio', 'speed_consistency']
            max_speed_total = sum(feature_importance.get(f, 0) for f in max_speed_features)
            
            print(f"  [SUCCESS] R² {r2:.4f}, MAE {mae:.3f}s, Samples {len(df)}")
            print(f"  max_speed 相關特徵總占比: {max_speed_total*100:.2f}%")
            
            # 顯示 Top 5 特徵
            top_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]
            print(f"  Top 5 特徵:")
            for feat, imp in top_features:
                print(f"    {feat:25s} {imp*100:6.2f}%")
            
            return {
                'race': race_name,
                'r2_score': float(r2),
                'mae': float(mae),
                'n_samples': int(len(df)),
                'feature_importance': {k: float(v) for k, v in feature_importance.items()},
                'max_speed_total_importance': float(max_speed_total),
                'model_path': str(model_file)
            }
        
        except Exception as e:
            print(f"  [ERROR] {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def predict_2025(self, race_name: str) -> dict:
        """對 2025 賽季進行預測"""
        print(f"\n[2025 預測] {race_name}")
        
        try:
            # 載入模型
            model_file = self.models_dir / f"{race_name}.pkl"
            if not model_file.exists():
                print(f"  [SKIP] Model not found")
                return None
            
            with open(model_file, 'rb') as f:
                model = pickle.load(f)
            
            # 載入 2025 數據
            df = self.base_trainer.load_training_data_v3(race_name, start_year=2025, end_year=2025)
            
            if df.empty:
                print(f"  [SKIP] No 2025 data")
                return None
            
            # 添加交互特徵
            df = self.add_interaction_features(df)
            
            # 清理 NaN/Inf
            if df.isnull().any().any() or np.isinf(df.select_dtypes(include=[np.number])).any().any():
                df = df.replace([np.inf, -np.inf], np.nan).dropna()
            
            if df.empty:
                print(f"  [SKIP] No valid 2025 data after cleaning")
                return None
            
            # 準備特徵
            feature_cols = [
                'ideal_s1', 'ideal_s2', 'ideal_s3', 'ideal_lap',
                'low_speed_apex', 'mid_speed_apex', 'high_speed_apex', 'max_speed',
                's1_s2_ratio', 'sector_cv', 's2_lap_ratio',
                'max_speed_lap_ratio', 'max_speed_s2_ratio', 'speed_consistency'
            ]
            
            X = df[feature_cols]
            y_actual = df['actual_q_time']
            
            # 預測
            y_pred = model.predict(X)
            
            # 評估
            mae = mean_absolute_error(y_actual, y_pred)
            spearman, _ = spearmanr(y_actual, y_pred)
            
            print(f"  [RESULT] MAE {mae:.3f}s, Spearman {spearman:.3f}, Samples {len(df)}")
            
            return {
                'race': race_name,
                'mae': float(mae),
                'spearman': float(spearman),
                'n_samples': int(len(df)),
                'actual': y_actual.tolist(),
                'predicted': y_pred.tolist()
            }
        
        except Exception as e:
            print(f"  [ERROR] {e}")
            return None
    
    def run_batch_training(self):
        """批次訓練所有賽道"""
        print("\n" + "="*80)
        print("v3.4 批次訓練開始 - 添加 max_speed 交互特徵")
        print("="*80)
        
        # 賽道列表（與 v3.3 相同）
        tracks = [
            "Abu Dhabi", "Australia", "Austria", "Azerbaijan", "Bahrain",
            "Belgium", "Brazil", "Canada", "China", "Dutch",
            "France", "Great Britain", "Hungary", "Italy", "Japan",
            "Mexico", "Miami", "Monaco", "Portugal", "Russia",
            "Saudi Arabia", "Singapore", "Spain", "Turkey", "United States"
        ]
        
        success_count = 0
        
        for track in tracks:
            result = self.train_single_track(track, start_year=2022, end_year=2024)
            if result:
                self.results[track] = result
                success_count += 1
        
        print(f"\n{'='*80}")
        print(f"訓練完成: {success_count}/{len(tracks)} 個賽道成功")
        print(f"{'='*80}")
        
        # 保存訓練結果
        results_file = Path("v3.4_training_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\n訓練結果已保存: {results_file}")
        
        # 生成統計摘要
        self.print_training_summary()
    
    def print_training_summary(self):
        """列印訓練統計摘要"""
        if not self.results:
            return
        
        print(f"\n{'='*80}")
        print("v3.4 訓練統計摘要")
        print(f"{'='*80}")
        
        r2_scores = [r['r2_score'] for r in self.results.values()]
        mae_scores = [r['mae'] for r in self.results.values()]
        
        print(f"\n整體統計:")
        print(f"  平均 R²:  {np.mean(r2_scores):.4f}")
        print(f"  平均 MAE: {np.mean(mae_scores):.3f}s")
        print(f"  R² > 0.98 賽道數: {sum(1 for r2 in r2_scores if r2 > 0.98)}/{len(r2_scores)}")
        
        # Great Britain 專項檢查
        if "Great Britain" in self.results:
            gb = self.results["Great Britain"]
            print(f"\nGreat Britain 專項檢查:")
            print(f"  訓練 R²:  {gb['r2_score']:.4f}")
            print(f"  訓練 MAE: {gb['mae']:.3f}s")
            
            # max_speed 相關特徵分析
            feat_imp = gb['feature_importance']
            max_speed_imp = feat_imp.get('max_speed', 0) * 100
            max_speed_lap_imp = feat_imp.get('max_speed_lap_ratio', 0) * 100
            max_speed_s2_imp = feat_imp.get('max_speed_s2_ratio', 0) * 100
            speed_consistency_imp = feat_imp.get('speed_consistency', 0) * 100
            
            print(f"\n  max_speed 相關特徵分佈:")
            print(f"    max_speed (直接):        {max_speed_imp:6.2f}%")
            print(f"    max_speed_lap_ratio:     {max_speed_lap_imp:6.2f}%")
            print(f"    max_speed_s2_ratio:      {max_speed_s2_imp:6.2f}%")
            print(f"    speed_consistency:       {speed_consistency_imp:6.2f}%")
            print(f"    總計:                    {gb['max_speed_total_importance']*100:6.2f}%")
            
            if max_speed_imp < 30:
                print(f"  ✅ max_speed 占比已降低（< 30%）")
            else:
                print(f"  ⚠️  max_speed 占比仍然偏高（{max_speed_imp:.2f}%）")
        
        # Top 5 & Bottom 5 賽道
        sorted_tracks = sorted(self.results.items(), key=lambda x: x[1]['r2_score'], reverse=True)
        
        print(f"\nTop 5 表現最佳賽道:")
        for i, (track, result) in enumerate(sorted_tracks[:5], 1):
            print(f"  {i}. {track:20s} R² {result['r2_score']:.4f}, MAE {result['mae']:.3f}s")
        
        print(f"\nBottom 5 需要改進賽道:")
        for i, (track, result) in enumerate(sorted_tracks[-5:], 1):
            print(f"  {i}. {track:20s} R² {result['r2_score']:.4f}, MAE {result['mae']:.3f}s")
    
    def run_2025_validation(self):
        """對 2025 賽季進行驗證"""
        print(f"\n{'='*80}")
        print("v3.4 - 2025 賽季驗證")
        print(f"{'='*80}")
        
        for track in self.results.keys():
            result = self.predict_2025(track)
            if result:
                self.prediction_results[track] = result
        
        print(f"\n{'='*80}")
        print(f"2025 驗證完成: {len(self.prediction_results)} 個賽道")
        print(f"{'='*80}")
        
        # 保存預測結果
        predictions_file = Path("v3.4_2025_validation_results.json")
        with open(predictions_file, 'w', encoding='utf-8') as f:
            json.dump(self.prediction_results, f, indent=2, ensure_ascii=False)
        print(f"\n預測結果已保存: {predictions_file}")
        
        # 生成驗證統計
        self.print_validation_summary()
    
    def print_validation_summary(self):
        """列印 2025 驗證統計摘要"""
        if not self.prediction_results:
            return
        
        print(f"\n{'='*80}")
        print("v3.4 - 2025 驗證統計摘要")
        print(f"{'='*80}")
        
        spearman_scores = [r['spearman'] for r in self.prediction_results.values()]
        mae_scores = [r['mae'] for r in self.prediction_results.values()]
        
        print(f"\n整體統計:")
        print(f"  平均 Spearman: {np.mean(spearman_scores):.4f}")
        print(f"  平均 MAE:      {np.mean(mae_scores):.3f}s")
        print(f"  Spearman > 0.6: {sum(1 for s in spearman_scores if s > 0.6)}/{len(spearman_scores)}")
        
        # Great Britain 專項檢查
        if "Great Britain" in self.prediction_results:
            gb = self.prediction_results["Great Britain"]
            print(f"\nGreat Britain 2025 驗證結果:")
            print(f"  MAE:      {gb['mae']:.3f}s")
            print(f"  Spearman: {gb['spearman']:.3f}")
            
            # 與 v3.3 對比（v3.3: MAE 6.474s, Spearman 0.194）
            if gb['mae'] < 6.474:
                improvement = (6.474 - gb['mae']) / 6.474 * 100
                print(f"  ✅ MAE 改進: -{improvement:.1f}% (v3.3: 6.474s)")
            
            if gb['spearman'] > 0.194:
                improvement = gb['spearman'] - 0.194
                print(f"  ✅ Spearman 改進: +{improvement:.3f} (v3.3: 0.194)")
        
        # Top 5 & Bottom 5
        sorted_predictions = sorted(self.prediction_results.items(), 
                                   key=lambda x: x[1]['spearman'], reverse=True)
        
        print(f"\nTop 5 預測最準確賽道:")
        for i, (track, result) in enumerate(sorted_predictions[:5], 1):
            print(f"  {i}. {track:20s} Spearman {result['spearman']:.3f}, MAE {result['mae']:.3f}s")
        
        print(f"\nBottom 5 預測需改進賽道:")
        for i, (track, result) in enumerate(sorted_predictions[-5:], 1):
            print(f"  {i}. {track:20s} Spearman {result['spearman']:.3f}, MAE {result['mae']:.3f}s")


def main():
    """主程式"""
    trainer = BatchTrainerV3_4()
    
    # 步驟 1: 批次訓練
    trainer.run_batch_training()
    
    # 步驟 2: 2025 驗證
    trainer.run_2025_validation()
    
    print(f"\n{'='*80}")
    print("v3.4 完整流程結束")
    print(f"{'='*80}")
    print(f"\n結果檔案:")
    print(f"  訓練結果: v3.4_training_results.json")
    print(f"  驗證結果: v3.4_2025_validation_results.json")
    print(f"  模型目錄: models/track_specific_v3.4/")


if __name__ == "__main__":
    main()
