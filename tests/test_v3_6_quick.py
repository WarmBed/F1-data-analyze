#!/usr/bin/env python3
"""
v3.6 快速測試腳本 - Monaco 賽道 50 次試驗

用途：快速驗證訓練流程是否正常運作
"""
import sys
from train_v3_6_single_track import TrackExpertTrainer

def main():
    print("\n" + "="*60)
    print("🧪 v3.6 快速測試 - Monaco 賽道 (50 次試驗)")
    print("="*60)
    
    # 創建訓練器（使用較少的試驗次數）
    trainer = TrackExpertTrainer(
        track_name='Monaco',
        n_trials=50,  # 測試用 50 次
        verbose=True
    )
    
    # 執行訓練
    result = trainer.train_complete_pipeline()
    
    if result['success']:
        print("\n" + "="*60)
        print("✅ 測試成功!")
        print("="*60)
        print(f"  最佳 CV MAE: {result['best_cv_mae']:.4f}s")
        print(f"  訓練時間: {result['duration_seconds']:.1f}s")
        print(f"  模型路徑: {result['model_path']}")
        print("\n💡 測試通過，可以開始完整訓練 (500 次試驗)")
        return 0
    else:
        print("\n" + "="*60)
        print("❌ 測試失敗!")
        print("="*60)
        print(f"  錯誤: {result.get('error', 'Unknown')}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
