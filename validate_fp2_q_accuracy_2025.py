"""
2025 FP2→Q 預測準確度驗證腳本
分析 v3.10 模型 (含 Quali Sim 過濾) 的預測準確度
"""
import json
from pathlib import Path
from typing import Dict, List
import pandas as pd
import numpy as np
from scipy.stats import spearmanr

def load_prediction_file(file_path: Path) -> Dict:
    """載入單一預測檔案"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def calculate_metrics(predictions: List[Dict]) -> Dict:
    """計算準確度指標"""
    # 提取預測值和實際值
    predicted_times = [p['predicted_time'] for p in predictions]
    actual_times = [p['actual_q_time'] for p in predictions]
    predicted_ranks = [p['rank'] for p in predictions]
    actual_ranks = [p['actual_q_rank'] for p in predictions]
    
    # 1. 時間預測誤差
    mae = np.mean([abs(p - a) for p, a in zip(predicted_times, actual_times)])
    rmse = np.sqrt(np.mean([(p - a)**2 for p, a in zip(predicted_times, actual_times)]))
    
    # 2. 排名相關性
    spearman_corr, _ = spearmanr(predicted_ranks, actual_ranks)
    
    # 3. Top-N 準確度
    top_1_correct = sum(1 for p in predictions if p['rank'] == 1 and p['actual_q_rank'] == 1)
    top_3_correct = sum(1 for p in predictions if p['rank'] <= 3 and p['actual_q_rank'] <= 3)
    top_5_correct = sum(1 for p in predictions if p['rank'] <= 5 and p['actual_q_rank'] <= 5)
    
    # 4. 排名偏差
    rank_deviations = [abs(p['rank'] - p['actual_q_rank']) for p in predictions]
    avg_rank_deviation = np.mean(rank_deviations)
    max_rank_deviation = max(rank_deviations)
    
    # 5. 完美預測數
    perfect_predictions = sum(1 for p in predictions if p['rank'] == p['actual_q_rank'])
    
    return {
        'time_mae': mae,
        'time_rmse': rmse,
        'spearman_corr': spearman_corr,
        'top_1_accuracy': top_1_correct / len(predictions),
        'top_3_accuracy': top_3_correct / 3 / len(predictions),  # 正規化到 [0,1]
        'top_5_accuracy': top_5_correct / 5 / len(predictions),  # 正規化到 [0,1]
        'avg_rank_deviation': avg_rank_deviation,
        'max_rank_deviation': max_rank_deviation,
        'perfect_predictions': perfect_predictions,
        'perfect_predictions_rate': perfect_predictions / len(predictions)
    }

def analyze_quali_sim_impact(predictions: List[Dict]) -> Dict:
    """分析 Quali Sim 過濾的影響"""
    # 這裡假設預測結果中沒有明確標記 Quali Sim，所以只能從結果推測
    # 可以通過查看預測時間與 FP2 時間的差異來推測
    
    improvements = [p['fp2_time'] - p['predicted_time'] for p in predictions]
    avg_improvement = np.mean(improvements)
    
    # 計算預測準確度（與實際改進的差異）
    actual_improvements = [p['fp2_time'] - p['actual_q_time'] for p in predictions]
    improvement_errors = [abs(pred - actual) for pred, actual in zip(improvements, actual_improvements)]
    avg_improvement_error = np.mean(improvement_errors)
    
    return {
        'avg_predicted_improvement': avg_improvement,
        'avg_actual_improvement': np.mean(actual_improvements),
        'avg_improvement_error': avg_improvement_error
    }

def main():
    print("\n" + "="*70)
    print("2025 FP2→Q 預測準確度驗證")
    print("="*70)
    print("模型版本: v3.10 (含 Quali Sim 過濾)")
    
    # 查找所有預測檔案
    json_dir = Path("json")
    prediction_files = list(json_dir.glob("fp2_qualifying_prediction_2025_*.json"))
    
    print(f"\n找到 {len(prediction_files)} 個預測檔案")
    
    if len(prediction_files) == 0:
        print("\n⚠️  未找到預測檔案，請先執行批次預測生成")
        print("   命令: python batch_generate_fp2_q_predictions_2025.py")
        return
    
    # 分析每個賽事
    all_metrics = []
    
    for file_path in sorted(prediction_files):
        race_name = file_path.stem.replace("fp2_qualifying_prediction_2025_", "")
        print(f"\n{'='*70}")
        print(f"分析: {race_name}")
        print(f"{'='*70}")
        
        try:
            data = load_prediction_file(file_path)
            predictions = data.get('predictions', [])
            
            if not predictions:
                print(f"⚠️  {race_name} 無預測數據")
                continue
            
            # 計算指標
            metrics = calculate_metrics(predictions)
            metrics['race'] = race_name
            metrics['driver_count'] = len(predictions)
            
            # 分析 Quali Sim 影響
            quali_sim_metrics = analyze_quali_sim_impact(predictions)
            metrics.update(quali_sim_metrics)
            
            # 顯示結果
            print(f"\n時間預測準確度:")
            print(f"  MAE: {metrics['time_mae']:.3f}秒")
            print(f"  RMSE: {metrics['time_rmse']:.3f}秒")
            
            print(f"\n排名預測準確度:")
            print(f"  Spearman 相關係數: {metrics['spearman_corr']:.4f}")
            print(f"  Top-1 準確度: {metrics['top_1_accuracy']:.2%}")
            print(f"  Top-3 準確度: {metrics['top_3_accuracy']:.2%}")
            print(f"  Top-5 準確度: {metrics['top_5_accuracy']:.2%}")
            print(f"  平均排名偏差: {metrics['avg_rank_deviation']:.2f} 名")
            print(f"  完美預測數: {metrics['perfect_predictions']}/{metrics['driver_count']}")
            
            print(f"\nQuali Sim 過濾效果:")
            print(f"  預測平均改進: {metrics['avg_predicted_improvement']:.3f}秒")
            print(f"  實際平均改進: {metrics['avg_actual_improvement']:.3f}秒")
            print(f"  改進誤差: {metrics['avg_improvement_error']:.3f}秒")
            
            all_metrics.append(metrics)
            
        except Exception as e:
            print(f"❌ {race_name} 分析失敗: {str(e)}")
            continue
    
    if not all_metrics:
        print("\n⚠️  沒有成功分析任何賽事")
        return
    
    # 整體統計
    print(f"\n{'='*70}")
    print("整體統計 (所有賽事平均)")
    print(f"{'='*70}")
    
    df = pd.DataFrame(all_metrics)
    
    print(f"\n時間預測準確度:")
    print(f"  平均 MAE: {df['time_mae'].mean():.3f}秒 (σ={df['time_mae'].std():.3f})")
    print(f"  平均 RMSE: {df['time_rmse'].mean():.3f}秒 (σ={df['time_rmse'].std():.3f})")
    print(f"  最佳 MAE: {df['time_mae'].min():.3f}秒 ({df.loc[df['time_mae'].idxmin(), 'race']})")
    print(f"  最差 MAE: {df['time_mae'].max():.3f}秒 ({df.loc[df['time_mae'].idxmax(), 'race']})")
    
    print(f"\n排名預測準確度:")
    print(f"  平均 Spearman 相關係數: {df['spearman_corr'].mean():.4f} (σ={df['spearman_corr'].std():.4f})")
    print(f"  平均 Top-1 準確度: {df['top_1_accuracy'].mean():.2%}")
    print(f"  平均 Top-3 準確度: {df['top_3_accuracy'].mean():.2%}")
    print(f"  平均 Top-5 準確度: {df['top_5_accuracy'].mean():.2%}")
    print(f"  平均排名偏差: {df['avg_rank_deviation'].mean():.2f} 名 (σ={df['avg_rank_deviation'].std():.2f})")
    print(f"  平均完美預測率: {df['perfect_predictions_rate'].mean():.2%}")
    
    print(f"\nQuali Sim 過濾效果:")
    print(f"  平均預測改進: {df['avg_predicted_improvement'].mean():.3f}秒")
    print(f"  平均實際改進: {df['avg_actual_improvement'].mean():.3f}秒")
    print(f"  平均改進誤差: {df['avg_improvement_error'].mean():.3f}秒")
    
    # 保存完整報告
    report_file = Path("fp2_q_v3.10_accuracy_validation_report.csv")
    df.to_csv(report_file, index=False)
    print(f"\n✅ 完整報告已保存: {report_file}")
    
    # 生成摘要
    summary = {
        "model_version": "v3.10_FP2",
        "filtering_method": "Quali Sim (SOFT tire + ≤3 lap stint + tire age ≤3)",
        "races_analyzed": len(all_metrics),
        "total_predictions": int(df['driver_count'].sum()),
        "avg_time_mae": float(df['time_mae'].mean()),
        "avg_time_rmse": float(df['time_rmse'].mean()),
        "avg_spearman_corr": float(df['spearman_corr'].mean()),
        "avg_top_1_accuracy": float(df['top_1_accuracy'].mean()),
        "avg_top_3_accuracy": float(df['top_3_accuracy'].mean()),
        "avg_top_5_accuracy": float(df['top_5_accuracy'].mean()),
        "avg_rank_deviation": float(df['avg_rank_deviation'].mean()),
        "avg_perfect_predictions_rate": float(df['perfect_predictions_rate'].mean()),
        "avg_predicted_improvement": float(df['avg_predicted_improvement'].mean()),
        "avg_actual_improvement": float(df['avg_actual_improvement'].mean()),
        "avg_improvement_error": float(df['avg_improvement_error'].mean())
    }
    
    summary_file = Path("fp2_q_v3.10_accuracy_validation_summary.json")
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 摘要已保存: {summary_file}")
    
    print(f"\n{'='*70}")
    print("驗證完成！")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
