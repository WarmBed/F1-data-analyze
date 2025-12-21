"""
測試三種回歸方案的精度比較

方案 1: 純線性回歸
方案 2: 純 XGBoost
方案 3: 混合模型（物理 + XGBoost 殘差）
"""

import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import pickle
import os

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def load_training_data():
    """載入 F92 的訓練數據"""
    model_path = "models/f92_hybrid_model.pkl"
    
    if not os.path.exists(model_path):
        print(f"[錯誤] 找不到訓練數據: {model_path}")
        print("請先執行 F92 訓練生成模型檔案")
        return None
    
    with open(model_path, 'rb') as f:
        model_data = pickle.load(f)
    
    if 'training_df' not in model_data:
        print("[錯誤] 模型檔案中沒有 training_df")
        return None
    
    df = model_data['training_df']
    print(f"[成功] 載入訓練數據: {len(df)} 樣本")
    print(f"  年份: {df['year'].unique()}")
    print(f"  賽道數: {df['circuit'].nunique()}")
    
    return df


def test_linear_regression(X_train, X_test, y_train, y_test):
    """方案 1: 純線性回歸"""
    print("\n" + "=" * 60)
    print("方案 1: 純線性回歸（LinearRegression）")
    print("=" * 60)
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # 預測
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)
    
    # 評估
    train_mae = mean_absolute_error(y_train, train_pred)
    test_mae = mean_absolute_error(y_test, test_pred)
    train_r2 = r2_score(y_train, train_pred)
    test_r2 = r2_score(y_test, test_pred)
    
    print(f"訓練集 MAE: {train_mae:.4f}s, R²: {train_r2:.4f}")
    print(f"測試集 MAE: {test_mae:.4f}s, R²: {test_r2:.4f}")
    
    return {
        'name': '線性回歸',
        'train_mae': train_mae,
        'test_mae': test_mae,
        'train_r2': train_r2,
        'test_r2': test_r2,
        'predictions': test_pred
    }


def test_xgboost_direct(X_train, X_test, y_train, y_test):
    """方案 2: 純 XGBoost（直接預測圈速）"""
    print("\n" + "=" * 60)
    print("方案 2: 純 XGBoost（直接預測圈速）")
    print("=" * 60)
    
    model = XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # 預測
    train_pred = model.predict(X_train)
    test_pred = model.predict(X_test)
    
    # 評估
    train_mae = mean_absolute_error(y_train, train_pred)
    test_mae = mean_absolute_error(y_test, test_pred)
    train_r2 = r2_score(y_train, train_pred)
    test_r2 = r2_score(y_test, test_pred)
    
    print(f"訓練集 MAE: {train_mae:.4f}s, R²: {train_r2:.4f}")
    print(f"測試集 MAE: {test_mae:.4f}s, R²: {test_r2:.4f}")
    
    return {
        'name': '純 XGBoost',
        'train_mae': train_mae,
        'test_mae': test_mae,
        'train_r2': train_r2,
        'test_r2': test_r2,
        'predictions': test_pred
    }


def test_hybrid_model(df, X_train, X_test, y_train, y_test, test_indices):
    """方案 3: 混合模型（物理 + XGBoost 殘差）"""
    print("\n" + "=" * 60)
    print("方案 3: 混合模型（物理 + XGBoost 殘差）- F92 目前架構")
    print("=" * 60)
    
    # 步驟 1: 計算物理預測
    df_test = df.iloc[test_indices].copy()
    physics_pred_test = df_test['physics_pred'].values
    
    # 步驟 2: 計算真實殘差
    residuals_test = y_test - physics_pred_test
    
    # 步驟 3: 訓練 XGBoost 預測殘差
    df_train = df.drop(test_indices).copy()
    residuals_train = df_train['residual'].values
    
    model = XGBRegressor(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, residuals_train)
    
    # 預測殘差
    train_residual_pred = model.predict(X_train)
    test_residual_pred = model.predict(X_test)
    
    # 步驟 4: 物理預測 + 殘差預測
    physics_pred_train = df_train['physics_pred'].values
    train_pred = physics_pred_train + train_residual_pred
    test_pred = physics_pred_test + test_residual_pred
    
    # 評估
    train_mae = mean_absolute_error(y_train, train_pred)
    test_mae = mean_absolute_error(y_test, test_pred)
    train_r2 = r2_score(y_train, train_pred)
    test_r2 = r2_score(y_test, test_pred)
    
    print(f"訓練集 MAE: {train_mae:.4f}s, R²: {train_r2:.4f}")
    print(f"測試集 MAE: {test_mae:.4f}s, R²: {test_r2:.4f}")
    
    # 分析物理模型 vs ML 校正的貢獻
    physics_mae = mean_absolute_error(y_test, physics_pred_test)
    print(f"\n物理模型單獨 MAE: {physics_mae:.4f}s")
    print(f"ML 校正後改善: {physics_mae - test_mae:.4f}s ({(physics_mae - test_mae) / physics_mae * 100:.1f}%)")
    
    return {
        'name': '混合模型',
        'train_mae': train_mae,
        'test_mae': test_mae,
        'train_r2': train_r2,
        'test_r2': test_r2,
        'predictions': test_pred,
        'physics_mae': physics_mae
    }


def plot_comparison(results, y_test):
    """繪製三種方案的比較圖"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # 1. MAE 比較（柱狀圖）
    ax = axes[0, 0]
    names = [r['name'] for r in results]
    test_maes = [r['test_mae'] for r in results]
    
    colors = ['#3498db', '#e74c3c', '#2ecc71']
    bars = ax.bar(names, test_maes, color=colors, alpha=0.7, edgecolor='black')
    
    # 在柱子上顯示數值
    for bar, mae in zip(bars, test_maes):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height + 0.02,
                f'{mae:.3f}s', ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    ax.set_ylabel('測試集 MAE (秒)', fontsize=12)
    ax.set_title('三種方案精度比較（越低越好）', fontsize=13, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(0, max(test_maes) * 1.2)
    
    # 2. R² 比較（柱狀圖）
    ax = axes[0, 1]
    test_r2s = [r['test_r2'] for r in results]
    
    bars = ax.bar(names, test_r2s, color=colors, alpha=0.7, edgecolor='black')
    
    for bar, r2 in zip(bars, test_r2s):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, height - 0.05,
                f'{r2:.3f}', ha='center', va='top', fontsize=11, fontweight='bold', color='white')
    
    ax.set_ylabel('測試集 R²', fontsize=12)
    ax.set_title('三種方案擬合度比較（越高越好）', fontsize=13, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(0, 1.0)
    
    # 3. 預測 vs 真實（散點圖）- 混合模型
    ax = axes[1, 0]
    hybrid_result = [r for r in results if r['name'] == '混合模型'][0]
    
    ax.scatter(y_test, hybrid_result['predictions'], alpha=0.5, s=20, color='#2ecc71', edgecolors='black', linewidth=0.5)
    ax.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2, label='完美預測')
    
    ax.set_xlabel('真實圈速 (秒)', fontsize=12)
    ax.set_ylabel('預測圈速 (秒)', fontsize=12)
    ax.set_title(f'混合模型預測結果（MAE: {hybrid_result["test_mae"]:.3f}s）', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3)
    
    # 4. 誤差分布（直方圖）
    ax = axes[1, 1]
    
    for result, color in zip(results, colors):
        errors = result['predictions'] - y_test
        ax.hist(errors, bins=30, alpha=0.5, color=color, label=result['name'], edgecolor='black', linewidth=0.5)
    
    ax.axvline(0, color='red', linestyle='--', linewidth=2, label='零誤差')
    ax.set_xlabel('預測誤差 (秒)', fontsize=12)
    ax.set_ylabel('樣本數', fontsize=12)
    ax.set_title('誤差分布比較', fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    
    output_path = 'reports/linear_vs_xgb_comparison.png'
    os.makedirs('reports', exist_ok=True)
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\n[圖表] 已保存至: {output_path}")
    
    plt.close()


def main():
    """主函數"""
    print("=" * 60)
    print("F92 回歸方案比較測試")
    print("=" * 60)
    
    # 載入數據
    df = load_training_data()
    if df is None:
        return
    
    # 準備特徵
    feature_cols = [
        'fp2_best_lap', 'fp2_mean_lap', 'fp2_median_lap', 'fp2_std_lap', 'fp2_lap_count',
        'soft_ratio', 'medium_ratio', 'hard_ratio',
        'grip_evolution',
        'air_temp', 'track_temp', 'humidity', 'wind_speed',
        'track_base_deg_soft', 'track_base_deg_medium', 'track_base_deg_hard',
        'fuel_effect_coef',
        'lap_number', 'stint_lap',
        'compound_soft', 'compound_medium', 'compound_hard'
    ]
    
    # 確保所有特徵存在
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0
    
    X = df[feature_cols].values
    y = df['actual_time'].values
    
    # 分割訓練/測試
    X_train, X_test, y_train, y_test, train_indices, test_indices = train_test_split(
        X, y, df.index, test_size=0.2, random_state=42
    )
    
    print(f"\n訓練集: {len(X_train)} 樣本")
    print(f"測試集: {len(X_test)} 樣本")
    
    # 測試三種方案
    results = []
    
    # 方案 1: 線性回歸
    result1 = test_linear_regression(X_train, X_test, y_train, y_test)
    results.append(result1)
    
    # 方案 2: 純 XGBoost
    result2 = test_xgboost_direct(X_train, X_test, y_train, y_test)
    results.append(result2)
    
    # 方案 3: 混合模型
    result3 = test_hybrid_model(df, X_train, X_test, y_train, y_test, test_indices)
    results.append(result3)
    
    # 繪製比較圖
    plot_comparison(results, y_test)
    
    # 總結
    print("\n" + "=" * 60)
    print("總結報告")
    print("=" * 60)
    
    for result in results:
        print(f"\n{result['name']}:")
        print(f"  測試 MAE: {result['test_mae']:.4f}s")
        print(f"  測試 R²: {result['test_r2']:.4f}")
    
    # 找出最佳方案
    best_result = min(results, key=lambda x: x['test_mae'])
    print(f"\n🏆 最佳方案: {best_result['name']} (MAE: {best_result['test_mae']:.4f}s)")
    
    # 混合模型的特殊報告
    hybrid = [r for r in results if r['name'] == '混合模型'][0]
    if 'physics_mae' in hybrid:
        improvement = hybrid['physics_mae'] - hybrid['test_mae']
        improvement_pct = improvement / hybrid['physics_mae'] * 100
        print(f"\n📊 混合模型分析:")
        print(f"  物理模型單獨 MAE: {hybrid['physics_mae']:.4f}s")
        print(f"  ML 校正後 MAE: {hybrid['test_mae']:.4f}s")
        print(f"  改善幅度: {improvement:.4f}s ({improvement_pct:.1f}%)")


if __name__ == '__main__':
    main()
