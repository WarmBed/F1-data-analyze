#!/usr/bin/env python3
"""
v3.6 批次訓練器 - 所有賽道超參數深度調優

功能：
1. 並行訓練所有 2025 賽道
2. 每個賽道獨立 500 次 Optuna 調優
3. 自動保存模型和調優歷史
4. 生成完整訓練報告

使用方法：
    python batch_train_v3_6_all_tracks.py --trials 500 --workers 8
"""
import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import multiprocessing as mp
from functools import partial

# 導入單賽道訓練器
from train_v3_6_single_track import TrackExpertTrainer


# 2025 賽季賽道列表（使用實際檔案名稱格式：空格而非底線）
TRACKS_2025 = [
    'Bahrain',
    'Saudi Arabia',  # 修正：底線 → 空格
    'Japan',
    'Monaco',
    'Canada',
    'Great Britain',  # 修正：底線 → 空格
    'Hungary',
    'Netherlands',
    'Italy',
    'Azerbaijan'
]


def train_single_track_wrapper(track_name: str, n_trials: int) -> Dict:
    """
    單賽道訓練包裝函數（用於多進程）
    
    Args:
        track_name: 賽道名稱
        n_trials: Optuna 試驗次數
        
    Returns:
        訓練結果字典
    """
    try:
        print(f"\n{'='*60}")
        print(f"🏁 開始訓練: {track_name}")
        print(f"{'='*60}")
        
        # 創建訓練器
        trainer = TrackExpertTrainer(
            track_name=track_name,
            n_trials=n_trials,
            verbose=True
        )
        
        # 執行訓練
        result = trainer.train_complete_pipeline()
        
        return result
        
    except Exception as e:
        return {
            'success': False,
            'track': track_name,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def train_sequential(tracks: List[str], n_trials: int) -> List[Dict]:
    """
    串行訓練所有賽道
    
    Args:
        tracks: 賽道列表
        n_trials: 每個賽道的試驗次數
        
    Returns:
        所有賽道的訓練結果
    """
    results = []
    
    for i, track in enumerate(tracks, 1):
        print(f"\n{'#'*60}")
        print(f"# 訓練進度: {i}/{len(tracks)} - {track}")
        print(f"{'#'*60}")
        
        result = train_single_track_wrapper(track, n_trials)
        results.append(result)
        
        if result['success']:
            print(f"\n  ✅ {track} 完成 - MAE: {result['best_cv_mae']:.4f}s")
        else:
            print(f"\n  ❌ {track} 失敗 - {result['error']}")
    
    return results


def train_parallel(tracks: List[str], n_trials: int, n_workers: int) -> List[Dict]:
    """
    並行訓練所有賽道
    
    Args:
        tracks: 賽道列表
        n_trials: 每個賽道的試驗次數
        n_workers: 並行工作進程數
        
    Returns:
        所有賽道的訓練結果
    """
    print(f"\n{'='*60}")
    print(f"🚀 並行訓練 {len(tracks)} 個賽道 (工作進程: {n_workers})")
    print(f"{'='*60}")
    
    # 創建進程池
    with mp.Pool(processes=n_workers) as pool:
        # 並行執行
        train_func = partial(train_single_track_wrapper, n_trials=n_trials)
        results = pool.map(train_func, tracks)
    
    return results


def generate_training_report(results: List[Dict], output_path: str):
    """
    生成訓練報告
    
    Args:
        results: 訓練結果列表
        output_path: 報告輸出路徑
    """
    # 統計數據
    total_tracks = len(results)
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    n_success = len(successful)
    n_failed = len(failed)
    
    total_duration = sum(r.get('duration_seconds', 0) for r in successful)
    avg_duration = total_duration / n_success if n_success > 0 else 0
    
    # 按 MAE 排序
    successful_sorted = sorted(successful, key=lambda x: x['best_cv_mae'])
    
    # 生成報告
    report = {
        'summary': {
            'total_tracks': total_tracks,
            'successful': n_success,
            'failed': n_failed,
            'success_rate': f"{n_success/total_tracks*100:.1f}%",
            'total_duration_seconds': total_duration,
            'avg_duration_per_track': avg_duration,
            'timestamp': datetime.now().isoformat()
        },
        'successful_tracks': [],
        'failed_tracks': []
    }
    
    # 添加成功的賽道
    for result in successful_sorted:
        track_info = {
            'track': result['track'],
            'best_cv_mae': result['best_cv_mae'],
            'n_samples': result['n_samples'],
            'n_trials': result['n_trials'],
            'duration_seconds': result['duration_seconds'],
            'best_params': result['best_params'],
            'top_features': result.get('top_features', [])
        }
        report['successful_tracks'].append(track_info)
    
    # 添加失敗的賽道
    for result in failed:
        track_info = {
            'track': result['track'],
            'error': result['error']
        }
        report['failed_tracks'].append(track_info)
    
    # 保存報告
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 打印摘要
    print(f"\n{'='*60}")
    print(f"📊 訓練報告")
    print(f"{'='*60}")
    print(f"  總賽道數: {total_tracks}")
    print(f"  成功: {n_success} ({n_success/total_tracks*100:.1f}%)")
    print(f"  失敗: {n_failed}")
    print(f"  總時間: {total_duration:.1f}s ({total_duration/60:.1f}min)")
    print(f"  平均時間: {avg_duration:.1f}s/賽道")
    
    if successful_sorted:
        print(f"\n  🏆 Top 5 最佳賽道:")
        for i, result in enumerate(successful_sorted[:5], 1):
            print(f"     {i}. {result['track']:20s}: MAE = {result['best_cv_mae']:.4f}s")
    
    if failed:
        print(f"\n  ❌ 失敗的賽道:")
        for result in failed:
            print(f"     - {result['track']:20s}: {result['error']}")
    
    print(f"\n  📄 完整報告: {output_path}")


def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='v3.6 批次訓練所有賽道')
    parser.add_argument('--trials', type=int, default=500, help='每個賽道的 Optuna 試驗次數 (默認: 500)')
    parser.add_argument('--workers', type=int, default=8, help='並行工作進程數 (默認: 8)')
    parser.add_argument('--sequential', action='store_true', help='使用串行模式（不並行）')
    parser.add_argument('--tracks', nargs='+', help='指定訓練的賽道（默認: 全部）')
    
    args = parser.parse_args()
    
    # 確定要訓練的賽道
    tracks = args.tracks if args.tracks else TRACKS_2025
    
    print(f"\n{'='*60}")
    print(f"🏎️  v3.6 批次訓練器")
    print(f"{'='*60}")
    print(f"  賽道數量: {len(tracks)}")
    print(f"  每賽道試驗: {args.trials}")
    print(f"  並行模式: {'否 (串行)' if args.sequential else f'是 ({args.workers} 工作進程)'}")
    print(f"  預估時間: {len(tracks) * 30 / (1 if args.sequential else args.workers):.1f} 分鐘")
    
    # 開始訓練
    start_time = time.time()
    
    if args.sequential:
        results = train_sequential(tracks, args.trials)
    else:
        results = train_parallel(tracks, args.trials, args.workers)
    
    end_time = time.time()
    total_duration = end_time - start_time
    
    # 生成報告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"v3.6_batch_training_report_{timestamp}.json"
    generate_training_report(results, report_path)
    
    print(f"\n{'='*60}")
    print(f"✅ 批次訓練完成!")
    print(f"{'='*60}")
    print(f"  總時間: {total_duration:.1f}s ({total_duration/60:.1f}min)")
    
    return 0


if __name__ == '__main__':
    # Windows 多進程支援
    mp.freeze_support()
    sys.exit(main())
