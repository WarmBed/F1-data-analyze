# -*- coding: utf-8 -*-
"""
Quick v3.6 vs v3.5 comparison report generator
"""

import os
import pickle
import pandas as pd
import numpy as np
from datetime import datetime
from scipy.stats import spearmanr
import sys

# Force UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from CLI_modules.cli.prediction.track_specific_trainer_v3 import TrackSpecificTrainerV3


def load_models():
    """Load all v3.6 models"""
    models_dir = "models/v3.6"
    models = {}
    
    model_files = [f for f in os.listdir(models_dir) if f.endswith('.pkl')]
    
    for model_file in model_files:
        track_name = model_file.replace('.pkl', '')
        model_path = os.path.join(models_dir, model_file)
        with open(model_path, 'rb') as f:
            model_data = pickle.load(f)
        models[track_name] = model_data
    
    return models


def predict_2025(models):
    """Predict 2025 races"""
    base_trainer = TrackSpecificTrainerV3()
    results = {}
    
    for track_name, model_data in sorted(models.items()):
        try:
            # Load 2025 FP3 data (真正的預測！)
            fp3_data = base_trainer.load_training_data_v3(
                track_name=track_name,
                start_year=2025,
                end_year=2025
            )
            
            if fp3_data.empty:
                print(f"No 2025 data for {track_name}")
                continue
            
            model = model_data['model']
            feature_names = model_data['feature_names']
            
            # Predict
            X_pred = fp3_data[feature_names].values
            drivers = fp3_data['driver'].values
            y_pred = model.predict(X_pred)
            
            # Create results DataFrame
            predictions_df = pd.DataFrame({
                'driver': drivers,
                'predicted_time': y_pred,
                'predicted_rank': pd.Series(y_pred).rank().values
            })
            
            # Add actual results if available
            if 'actual_q_time' in fp3_data.columns:
                predictions_df['actual_time'] = fp3_data['actual_q_time'].values
                predictions_df['actual_rank'] = fp3_data['actual_q_time'].rank().values
                predictions_df['time_error'] = predictions_df['predicted_time'] - predictions_df['actual_time']
                predictions_df['time_error_pct'] = (predictions_df['time_error'] / predictions_df['actual_time'] * 100).abs()
                predictions_df['rank_error'] = (predictions_df['predicted_rank'] - predictions_df['actual_rank']).abs()
                
                # Calculate metrics
                mae = predictions_df['time_error'].abs().mean()
                spearman, _ = spearmanr(predictions_df['actual_rank'], predictions_df['predicted_rank'])
                
                # Top5 accuracy
                actual_top5 = set(predictions_df.nsmallest(5, 'actual_time')['driver'])
                predicted_top5 = set(predictions_df.nsmallest(5, 'predicted_time')['driver'])
                top5_correct = len(actual_top5 & predicted_top5)
                top5_accuracy = top5_correct / 5 * 100
                
                results[track_name] = {
                    'predictions': predictions_df.sort_values('predicted_time'),
                    'mae': mae,
                    'spearman': spearman,
                    'top5_accuracy': top5_accuracy,
                    'top5_correct': top5_correct,
                    'cv_mae': model_data['best_cv_mae']
                }
                
                print(f"{track_name:15s}: MAE {mae:.3f}s, Spearman {spearman:.3f}, Top5 {top5_accuracy:.0f}% ({top5_correct}/5)")
            else:
                print(f"{track_name:15s}: No actual Q data")
                
        except Exception as e:
            print(f"{track_name}: ERROR - {e}")
            import traceback
            traceback.print_exc()
    
    return results


def generate_markdown_report(results, output_path):
    """Generate detailed markdown report"""
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# v3.6 2025 賽季 Top5 預測分析報告\n\n")
        f.write(f"**生成日期**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**模型版本**: v3.6 (Optuna 超參數優化賽道專家模型)\n")
        f.write(f"**訓練數據**: 2022-2024 年（3 年歷史數據）\n")
        f.write(f"**預測年份**: 2025 年賽季（真正的未來預測）\n")
        f.write(f"**分析賽事**: {len(results)}\n\n")
        f.write("---\n\n")
        
        # Overall statistics
        f.write("## Overall Statistics\n\n")
        
        total_correct = sum(r['top5_correct'] for r in results.values())
        total_possible = len(results) * 5
        overall_accuracy = total_correct / total_possible * 100
        
        avg_mae = np.mean([r['mae'] for r in results.values()])
        avg_spearman = np.mean([r['spearman'] for r in results.values()])
        avg_cv_mae = np.mean([r['cv_mae'] for r in results.values()])
        
        f.write("| Metric | Value |\n")
        f.write("|--------|-------|\n")
        f.write(f"| **Top5 Accuracy** | **{overall_accuracy:.1f}%** ({total_correct}/{total_possible}) |\n")
        f.write(f"| **Average MAE** | {avg_mae:.3f}s |\n")
        f.write(f"| **Average CV MAE** | {avg_cv_mae:.3f}s |\n")
        f.write(f"| **Average Spearman** | {avg_spearman:.3f} |\n")
        f.write(f"| **Races Analyzed** | {len(results)} |\n\n")
        
        # Per-track analysis
        f.write("## Per-Track Detailed Analysis\n\n")
        
        for track, data in sorted(results.items(), key=lambda x: x[1]['top5_accuracy'], reverse=True):
            predictions = data['predictions']
            
            f.write(f"### {track}\n\n")
            
            # Metrics
            f.write(f"**性能指標:**\n")
            f.write(f"- 訓練 CV MAE: {data['cv_mae']:.3f}s\n")
            f.write(f"- 2025 預測 MAE: {data['mae']:.3f}s\n")
            f.write(f"- Spearman 相關性: {data['spearman']:.3f}\n")
            f.write(f"- Top5 準確率: {data['top5_accuracy']:.1f}% ({data['top5_correct']}/5)\n\n")
            
            # Top5 prediction vs actual
            f.write("**Predicted Top5 vs Actual:**\n\n")
            f.write("| Pred Rank | Driver | Pred Time | Actual Time | Actual Rank | Time Error | Error % |\n")
            f.write("|-----------|--------|-----------|-------------|-------------|------------|---------|\n")
            
            top5_pred = predictions.head(5)
            for _, row in top5_pred.iterrows():
                f.write(f"| {int(row['predicted_rank'])} | {row['driver']} | "
                       f"{row['predicted_time']:.3f}s | {row['actual_time']:.3f}s | "
                       f"{int(row['actual_rank'])} | {row['time_error']:.3f}s | "
                       f"{row['time_error_pct']:.2f}% |\n")
            
            # Check if predicted top5 matches actual top5
            actual_top5_drivers = set(predictions.nsmallest(5, 'actual_time')['driver'])
            predicted_top5_drivers = set(predictions.head(5)['driver'])
            
            f.write(f"\n**Top5 Driver Match:**\n")
            f.write(f"- Actual Top5: {', '.join(sorted(actual_top5_drivers))}\n")
            f.write(f"- Predicted Top5: {', '.join(sorted(predicted_top5_drivers))}\n")
            f.write(f"- Correct: {', '.join(sorted(actual_top5_drivers & predicted_top5_drivers))}\n")
            f.write(f"- Missed: {', '.join(sorted(actual_top5_drivers - predicted_top5_drivers))}\n")
            f.write(f"- False Positives: {', '.join(sorted(predicted_top5_drivers - actual_top5_drivers))}\n\n")
            
            f.write("---\n\n")
        
        # v3.5 comparison would go here
        f.write("## v3.5 vs v3.6 Comparison\n\n")
        f.write("*(To be completed with v3.5 results)*\n\n")
    
    print(f"\nReport generated: {output_path}")


def main():
    print("="*60)
    print("v3.6 2025 Prediction Report Generator")
    print("="*60)
    
    # Load models
    print("\nLoading v3.6 models...")
    models = load_models()
    print(f"Loaded {len(models)} models: {', '.join(sorted(models.keys()))}\n")
    
    # Predict 2025 races (真正的預測！)
    print("Predicting 2025 races...")
    print("="*60)
    results = predict_2025(models)
    print("="*60)
    
    if not results:
        print("No results to report!")
        return
    
    # Generate report
    print("\nGenerating markdown report...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"V3.6_2025_TOP5_REPORT_{timestamp}.md"
    generate_markdown_report(results, report_path)
    
    print("\n" + "="*60)
    print("DONE!")
    print("="*60)
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
