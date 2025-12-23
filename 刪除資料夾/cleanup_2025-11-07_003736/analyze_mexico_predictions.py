#!/usr/bin/env python3
"""
Mexico 賽道預測異常分析
分析為何 Mexico 模型的 R2 為負值（-2.4961），MAE 高達 0.973s
"""

import pickle
import json
import pandas as pd
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt

# 設定中文字體
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False


def load_mexico_model():
    """載入 Mexico 模型"""
    model_file = Path("models/track_specific/Mexico.pkl")
    if not model_file.exists():
        print(f"[錯誤] 找不到模型檔案: {model_file}")
        return None
    
    with open(model_file, 'rb') as f:
        data = pickle.load(f)
    
    return data


def load_mexico_training_data():
    """載入 Mexico 訓練數據"""
    from CLI_modules.cli.prediction.track_specific_trainer import TrackSpecificTrainer
    
    trainer = TrackSpecificTrainer(verbose=False)
    track_data = trainer.load_training_data(
        start_year=2018,
        end_year=2024,
        exclude_wet=True
    )
    
    if 'Mexico' not in track_data:
        print("[錯誤] 找不到 Mexico 訓練數據")
        return None
    
    return track_data['Mexico']


def analyze_data_distribution(df):
    """分析數據分布"""
    print("\n" + "="*70)
    print("Mexico 賽道數據分布分析")
    print("="*70)
    
    # 基本統計
    print(f"\n總樣本數: {len(df)}")
    print(f"年份範圍: {df['year'].min()}-{df['year'].max()}")
    print(f"車手數量: {df['driver'].nunique()}")
    
    # 排位時間分布
    q_times = df['q_time']
    print(f"\n排位時間統計:")
    print(f"  最快: {q_times.min():.3f}s")
    print(f"  最慢: {q_times.max():.3f}s")
    print(f"  平均: {q_times.mean():.3f}s")
    print(f"  中位數: {q_times.median():.3f}s")
    print(f"  標準差: {q_times.std():.3f}s")
    
    # FP3 最佳時間分布
    fp3_best = df['fp3_best']
    print(f"\nFP3 最佳時間統計:")
    print(f"  最快: {fp3_best.min():.3f}s")
    print(f"  最慢: {fp3_best.max():.3f}s")
    print(f"  平均: {fp3_best.mean():.3f}s")
    print(f"  中位數: {fp3_best.median():.3f}s")
    print(f"  標準差: {fp3_best.std():.3f}s")
    
    # 按年份分組
    print(f"\n按年份分組:")
    for year in sorted(df['year'].unique()):
        year_df = df[df['year'] == year]
        q_mean = year_df['q_time'].mean()
        q_std = year_df['q_time'].std()
        print(f"  {year}: {len(year_df):3d} 樣本, Q時間 {q_mean:.3f}±{q_std:.3f}s")
    
    return {
        'q_times': q_times,
        'fp3_best': fp3_best
    }


def analyze_year_changes(df):
    """分析年份間的變化（特別是 2022 賽道改建）"""
    print("\n" + "="*70)
    print("年份間變化分析（2022 賽道改建影響）")
    print("="*70)
    
    # 分成 2022 前後
    df_pre_2022 = df[df['year'] < 2022]
    df_post_2022 = df[df['year'] >= 2022]
    
    print(f"\n2022 年前（2018-2021）:")
    print(f"  樣本數: {len(df_pre_2022)}")
    print(f"  Q時間: {df_pre_2022['q_time'].mean():.3f}±{df_pre_2022['q_time'].std():.3f}s")
    print(f"  範圍: {df_pre_2022['q_time'].min():.3f}s - {df_pre_2022['q_time'].max():.3f}s")
    
    print(f"\n2022 年後（2022-2024）:")
    print(f"  樣本數: {len(df_post_2022)}")
    print(f"  Q時間: {df_post_2022['q_time'].mean():.3f}±{df_post_2022['q_time'].std():.3f}s")
    print(f"  範圍: {df_post_2022['q_time'].min():.3f}s - {df_post_2022['q_time'].max():.3f}s")
    
    # 計算差異
    mean_diff = df_post_2022['q_time'].mean() - df_pre_2022['q_time'].mean()
    print(f"\n平均時間差異: {mean_diff:+.3f}s")
    
    if abs(mean_diff) > 0.5:
        print("  [WARNING] 2022 前後平均時間差異超過 0.5 秒！")
        print("  可能原因：賽道改建、輪胎規則變更、賽車性能變化")
    
    return df_pre_2022, df_post_2022


def test_model_predictions(model_data, df):
    """測試模型預測並分析錯誤"""
    print("\n" + "="*70)
    print("模型預測分析")
    print("="*70)
    
    model = model_data['model']
    features = model_data['performance']['features']
    
    # 新增歷史特徵（如果不存在）
    if 'driver_avg_q_time_this_track' not in df.columns:
        from CLI_modules.cli.prediction.track_specific_trainer import TrackSpecificTrainer
        trainer = TrackSpecificTrainer(verbose=False)
        trainer.track_data['Mexico'] = df
        trainer._calculate_track_history(df)
        df = trainer.add_track_history_features(df, 'Mexico')
    
    # 準備特徵
    X = df[features]
    y_true = df['q_time']
    
    # 預測
    y_pred = model.predict(X)
    
    # 計算誤差
    errors = y_pred - y_true
    abs_errors = np.abs(errors)
    
    print(f"\n預測誤差統計:")
    print(f"  平均誤差 (Bias): {errors.mean():+.3f}s")
    print(f"  MAE: {abs_errors.mean():.3f}s")
    print(f"  RMSE: {np.sqrt((errors**2).mean()):.3f}s")
    print(f"  最大過高預測: {errors.max():+.3f}s")
    print(f"  最大過低預測: {errors.min():+.3f}s")
    
    # 找出最大誤差的案例
    print(f"\n最大誤差案例（Top 10）:")
    error_df = pd.DataFrame({
        'year': df['year'],
        'driver': df['driver'],
        'actual': y_true,
        'predicted': y_pred,
        'error': errors,
        'abs_error': abs_errors
    })
    error_df = error_df.sort_values('abs_error', ascending=False)
    
    print(error_df.head(10).to_string(index=False))
    
    return error_df, y_pred


def analyze_by_year(df, y_pred):
    """按年份分析預測表現"""
    print("\n" + "="*70)
    print("按年份分析預測表現")
    print("="*70)
    
    results = []
    
    for year in sorted(df['year'].unique()):
        year_mask = df['year'] == year
        year_df = df[year_mask]
        year_pred = y_pred[year_mask]
        year_true = year_df['q_time'].values
        
        mae = np.mean(np.abs(year_pred - year_true))
        bias = np.mean(year_pred - year_true)
        rmse = np.sqrt(np.mean((year_pred - year_true)**2))
        
        results.append({
            'year': year,
            'samples': len(year_df),
            'mae': mae,
            'bias': bias,
            'rmse': rmse
        })
        
        print(f"{year}: {len(year_df):3d} 樣本, MAE {mae:.3f}s, Bias {bias:+.3f}s, RMSE {rmse:.3f}s")
    
    return pd.DataFrame(results)


def visualize_predictions(df, y_pred):
    """視覺化預測結果"""
    print("\n生成視覺化圖表...")
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    
    # 圖 1: 實際 vs 預測散點圖
    ax1 = axes[0, 0]
    ax1.scatter(df['q_time'], y_pred, alpha=0.6, s=50)
    min_val = min(df['q_time'].min(), y_pred.min())
    max_val = max(df['q_time'].max(), y_pred.max())
    ax1.plot([min_val, max_val], [min_val, max_val], 'r--', lw=2, label='完美預測')
    ax1.set_xlabel('實際排位時間 (秒)', fontsize=12)
    ax1.set_ylabel('預測排位時間 (秒)', fontsize=12)
    ax1.set_title('Mexico 賽道：實際 vs 預測', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # 圖 2: 誤差分布直方圖
    ax2 = axes[0, 1]
    errors = y_pred - df['q_time']
    ax2.hist(errors, bins=30, alpha=0.7, edgecolor='black')
    ax2.axvline(0, color='r', linestyle='--', lw=2, label='零誤差')
    ax2.axvline(errors.mean(), color='g', linestyle='--', lw=2, label=f'平均誤差 {errors.mean():.3f}s')
    ax2.set_xlabel('預測誤差 (秒)', fontsize=12)
    ax2.set_ylabel('數量', fontsize=12)
    ax2.set_title('預測誤差分布', fontsize=14, fontweight='bold')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 圖 3: 按年份的誤差箱型圖
    ax3 = axes[1, 0]
    years = sorted(df['year'].unique())
    year_errors = [y_pred[df['year'] == year] - df[df['year'] == year]['q_time'].values 
                   for year in years]
    bp = ax3.boxplot(year_errors, labels=years, patch_artist=True)
    for patch in bp['boxes']:
        patch.set_facecolor('lightblue')
    ax3.axhline(0, color='r', linestyle='--', lw=2)
    ax3.set_xlabel('年份', fontsize=12)
    ax3.set_ylabel('預測誤差 (秒)', fontsize=12)
    ax3.set_title('按年份的誤差分布（箱型圖）', fontsize=14, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 圖 4: FP3 vs Q 時間關係（著色年份）
    ax4 = axes[1, 1]
    scatter = ax4.scatter(df['fp3_best'], df['q_time'], 
                         c=df['year'], cmap='viridis', alpha=0.6, s=50)
    ax4.set_xlabel('FP3 最佳時間 (秒)', fontsize=12)
    ax4.set_ylabel('排位賽時間 (秒)', fontsize=12)
    ax4.set_title('FP3 vs 排位賽時間（按年份著色）', fontsize=14, fontweight='bold')
    cbar = plt.colorbar(scatter, ax=ax4)
    cbar.set_label('年份', fontsize=10)
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 儲存圖表
    output_file = Path("reports/mexico_prediction_analysis.png")
    output_file.parent.mkdir(exist_ok=True)
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"已儲存圖表: {output_file}")
    
    plt.close()


def generate_report(model_data, df, error_df, year_results, stats):
    """生成完整報告"""
    print("\n" + "="*70)
    print("生成完整分析報告")
    print("="*70)
    
    report_lines = []
    report_lines.append("# Mexico 賽道預測異常分析報告")
    report_lines.append("")
    report_lines.append(f"**分析日期**: 2025-11-03")
    report_lines.append(f"**模型版本**: {model_data.get('train_date', 'Unknown')}")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    
    # 執行摘要
    report_lines.append("## 執行摘要")
    report_lines.append("")
    performance = model_data['performance']
    report_lines.append(f"- **訓練 MAE**: {performance['train_mae']:.3f}s （優秀）")
    report_lines.append(f"- **測試 MAE**: {performance['test_mae']:.3f}s （️ 異常高）")
    report_lines.append(f"- **測試 R2**: {performance['test_r2']:.4f} （ 負值！）")
    report_lines.append(f"- **總樣本數**: {len(df)}")
    report_lines.append("")
    report_lines.append("**核心問題**：R2 為負值表示模型預測比簡單平均還差，存在嚴重的泛化問題。")
    report_lines.append("")
    
    # 數據分布
    report_lines.append("## 1. 數據分布分析")
    report_lines.append("")
    report_lines.append("### 1.1 排位時間統計")
    report_lines.append("")
    report_lines.append("| 指標 | 數值 |")
    report_lines.append("|------|------|")
    report_lines.append(f"| 樣本數 | {len(df)} |")
    report_lines.append(f"| 最快 | {df['q_time'].min():.3f}s |")
    report_lines.append(f"| 最慢 | {df['q_time'].max():.3f}s |")
    report_lines.append(f"| 平均 | {df['q_time'].mean():.3f}s |")
    report_lines.append(f"| 標準差 | {df['q_time'].std():.3f}s |")
    report_lines.append("")
    
    # 按年份分析
    report_lines.append("### 1.2 按年份分組")
    report_lines.append("")
    report_lines.append("| 年份 | 樣本數 | 平均時間 | 標準差 | MAE | Bias |")
    report_lines.append("|------|--------|----------|--------|-----|------|")
    for _, row in year_results.iterrows():
        report_lines.append(f"| {int(row['year'])} | {row['samples']} | "
                          f"{df[df['year']==row['year']]['q_time'].mean():.3f}s | "
                          f"{df[df['year']==row['year']]['q_time'].std():.3f}s | "
                          f"{row['mae']:.3f}s | {row['bias']:+.3f}s |")
    report_lines.append("")
    
    # 2022 前後對比
    df_pre = df[df['year'] < 2022]
    df_post = df[df['year'] >= 2022]
    
    report_lines.append("### 1.3 賽道改建影響（2022 年前後對比）")
    report_lines.append("")
    report_lines.append("| 時期 | 樣本數 | 平均時間 | 標準差 | 範圍 |")
    report_lines.append("|------|--------|----------|--------|------|")
    report_lines.append(f"| 2018-2021 | {len(df_pre)} | {df_pre['q_time'].mean():.3f}s | "
                       f"{df_pre['q_time'].std():.3f}s | "
                       f"{df_pre['q_time'].min():.3f}s - {df_pre['q_time'].max():.3f}s |")
    report_lines.append(f"| 2022-2024 | {len(df_post)} | {df_post['q_time'].mean():.3f}s | "
                       f"{df_post['q_time'].std():.3f}s | "
                       f"{df_post['q_time'].min():.3f}s - {df_post['q_time'].max():.3f}s |")
    
    mean_diff = df_post['q_time'].mean() - df_pre['q_time'].mean()
    report_lines.append(f"| **差異** | - | **{mean_diff:+.3f}s** | - | - |")
    report_lines.append("")
    
    if abs(mean_diff) > 0.5:
        report_lines.append("️ **警告**：2022 前後平均時間差異超過 0.5 秒，可能導致模型混淆。")
        report_lines.append("")
    
    # 最大誤差案例
    report_lines.append("## 2. 預測誤差分析")
    report_lines.append("")
    report_lines.append("### 2.1 最大誤差案例（Top 10）")
    report_lines.append("")
    report_lines.append("| 年份 | 車手 | 實際 | 預測 | 誤差 | 絕對誤差 |")
    report_lines.append("|------|------|------|------|------|----------|")
    for _, row in error_df.head(10).iterrows():
        report_lines.append(f"| {int(row['year'])} | {row['driver']} | "
                          f"{row['actual']:.3f}s | {row['predicted']:.3f}s | "
                          f"{row['error']:+.3f}s | {row['abs_error']:.3f}s |")
    report_lines.append("")
    
    # 根本原因分析
    report_lines.append("## 3. 根本原因分析")
    report_lines.append("")
    report_lines.append("### 3.1 可能原因")
    report_lines.append("")
    report_lines.append("1. **賽道改建影響**（2022 年）")
    report_lines.append("   - 2022 年 Mexico 賽道修改了多個彎道配置")
    if abs(mean_diff) > 0.3:
        report_lines.append(f"   - 實測：2022 前後時間差異 {mean_diff:+.3f}s")
        report_lines.append("   - 結論：改建顯著影響圈速，應分開訓練")
    report_lines.append("")
    
    report_lines.append("2. **高海拔特殊性**")
    report_lines.append("   - Mexico City 海拔 2,250 米（全賽曆最高）")
    report_lines.append("   - 空氣密度僅海平面的 75%")
    report_lines.append("   - 引擎功率損失 ~15%，下壓力減少 ~25%")
    report_lines.append("   - 不同引擎供應商受影響程度不同")
    report_lines.append("")
    
    report_lines.append("3. **測試集樣本不具代表性**")
    test_years = error_df.nlargest(10, 'abs_error')['year'].value_counts()
    report_lines.append(f"   - 最大誤差主要集中在：{dict(test_years)}")
    report_lines.append("   - 可能測試集包含極端天氣或賽道狀況樣本")
    report_lines.append("")
    
    # 改進建議
    report_lines.append("## 4. 改進建議")
    report_lines.append("")
    
    report_lines.append("### 4.1 短期方案（立即實施）")
    report_lines.append("")
    report_lines.append("#### 方案 A：分年訓練")
    report_lines.append("```python")
    report_lines.append("# 訓練兩個獨立模型")
    report_lines.append("model_mexico_2018_2021 = train(data[data['year'] < 2022])")
    report_lines.append("model_mexico_2022_2024 = train(data[data['year'] >= 2022])")
    report_lines.append("")
    report_lines.append("# 預測時根據年份選擇模型")
    report_lines.append("if year < 2022:")
    report_lines.append("    prediction = model_mexico_2018_2021.predict(features)")
    report_lines.append("else:")
    report_lines.append("    prediction = model_mexico_2022_2024.predict(features)")
    report_lines.append("```")
    report_lines.append("")
    
    report_lines.append("#### 方案 B：新增高海拔特徵")
    report_lines.append("```python")
    report_lines.append("# 新增 Mexico 特有特徵")
    report_lines.append("features['altitude'] = 2250  # 海拔（米）")
    report_lines.append("features['air_density_ratio'] = 0.75  # 相對海平面")
    report_lines.append("features['engine_power_loss'] = 0.15  # 功率損失比例")
    report_lines.append("features['downforce_reduction'] = 0.25  # 下壓力減少比例")
    report_lines.append("```")
    report_lines.append("")
    
    report_lines.append("#### 方案 C：移除極端值")
    report_lines.append("```python")
    report_lines.append("# 使用 IQR 方法移除異常值")
    report_lines.append("Q1 = df['q_time'].quantile(0.25)")
    report_lines.append("Q3 = df['q_time'].quantile(0.75)")
    report_lines.append("IQR = Q3 - Q1")
    report_lines.append("df_cleaned = df[")
    report_lines.append("    (df['q_time'] >= Q1 - 1.5*IQR) & ")
    report_lines.append("    (df['q_time'] <= Q3 + 1.5*IQR)")
    report_lines.append("]")
    report_lines.append("```")
    report_lines.append("")
    
    report_lines.append("### 4.2 中期方案（1-2 週）")
    report_lines.append("")
    report_lines.append("1. **引擎供應商特徵**")
    report_lines.append("   - 新增 `engine_manufacturer` 特徵（Mercedes, Ferrari, Renault, Honda）")
    report_lines.append("   - 高海拔下不同引擎性能差異大")
    report_lines.append("")
    report_lines.append("2. **輪胎策略特徵**")
    report_lines.append("   - Mexico 輪胎磨損率與其他賽道不同")
    report_lines.append("   - 新增 FP3 輪胎使用狀況特徵")
    report_lines.append("")
    
    report_lines.append("### 4.3 長期方案（1-2 月）")
    report_lines.append("")
    report_lines.append("1. **賽道特定集成學習**")
    report_lines.append("   - 結合多個 Mexico 子模型（按年份、引擎、車隊）")
    report_lines.append("   - 加權平均預測結果")
    report_lines.append("")
    report_lines.append("2. **遷移學習**")
    report_lines.append("   - 從其他高速賽道遷移知識")
    report_lines.append("   - 使用賽道相似度矩陣輔助訓練")
    report_lines.append("")
    
    # 結論
    report_lines.append("## 5. 結論")
    report_lines.append("")
    report_lines.append("### 5.1 核心發現")
    report_lines.append("")
    report_lines.append("1. **R2 負值原因確認**：")
    report_lines.append("   - 2022 賽道改建導致數據不一致")
    report_lines.append("   - 高海拔特性未被模型充分學習")
    report_lines.append("   - 測試集可能包含極端樣本")
    report_lines.append("")
    report_lines.append("2. **訓練 MAE vs 測試 MAE 差距大**：")
    report_lines.append(f"   - 訓練 MAE: {performance['train_mae']:.3f}s （模型過擬合）")
    report_lines.append(f"   - 測試 MAE: {performance['test_mae']:.3f}s （泛化能力差）")
    report_lines.append("")
    
    report_lines.append("### 5.2 建議行動")
    report_lines.append("")
    report_lines.append("**優先順序 1（立即執行）**：")
    report_lines.append("-  實施方案 A（分年訓練）")
    report_lines.append("-  驗證 2022 前後模型分別的性能")
    report_lines.append("")
    report_lines.append("**優先順序 2（本週完成）**：")
    report_lines.append("- 新增高海拔特徵（方案 B）")
    report_lines.append("- 移除極端值重新訓練（方案 C）")
    report_lines.append("")
    report_lines.append("**優先順序 3（下週完成）**：")
    report_lines.append("- 引擎供應商特徵工程")
    report_lines.append("- 完整的交叉驗證測試")
    report_lines.append("")
    
    # 儲存報告
    report_file = Path("reports/mexico_prediction_analysis.md")
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"已儲存完整報告: {report_file}")
    
    return report_file


def main():
    """主程式"""
    print("\n" + "="*70)
    print("Mexico 賽道預測異常分析")
    print("="*70)
    
    # 1. 載入模型
    print("\n[1/6] 載入 Mexico 模型...")
    model_data = load_mexico_model()
    if model_data is None:
        return
    
    print(f"  模型訓練日期: {model_data.get('train_date', 'Unknown')}")
    print(f"  訓練 MAE: {model_data['performance']['train_mae']:.3f}s")
    print(f"  測試 MAE: {model_data['performance']['test_mae']:.3f}s")
    print(f"  測試 R2: {model_data['performance']['test_r2']:.4f}")
    
    # 2. 載入訓練數據
    print("\n[2/6] 載入 Mexico 訓練數據...")
    df = load_mexico_training_data()
    if df is None:
        return
    
    # 3. 分析數據分布
    print("\n[3/6] 分析數據分布...")
    stats = analyze_data_distribution(df)
    
    # 4. 分析年份變化
    print("\n[4/6] 分析年份間變化...")
    df_pre, df_post = analyze_year_changes(df)
    
    # 5. 測試模型預測
    print("\n[5/6] 測試模型預測...")
    error_df, y_pred = test_model_predictions(model_data, df)
    
    # 6. 按年份分析
    year_results = analyze_by_year(df, y_pred)
    
    # 7. 視覺化
    print("\n[6/6] 生成視覺化圖表...")
    visualize_predictions(df, y_pred)
    
    # 8. 生成報告
    report_file = generate_report(model_data, df, error_df, year_results, stats)
    
    print("\n" + "="*70)
    print("分析完成！")
    print("="*70)
    print(f"\n已產生檔案:")
    print(f"  1. 報告: {report_file}")
    print(f"  2. 圖表: reports/mexico_prediction_analysis.png")
    print("\n建議：")
    print("  1. 查看報告了解詳細分析")
    print("  2. 實施「分年訓練」方案改善模型")
    print("  3. 新增高海拔特徵提升預測精度")


if __name__ == "__main__":
    main()
