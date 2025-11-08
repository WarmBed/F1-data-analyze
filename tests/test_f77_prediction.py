#!/usr/bin/env python3
"""
測試 Function 77 預測功能
"""
import sys
sys.path.insert(0, 'd:\\OneDrive\\Code\\F1-data-analyze')

from CLI_modules.cli.prediction.track_specific_trainer import TrackSpecificTrainer

def main():
    print("="*70)
    print("測試 Function 77 預測功能")
    print("="*70)
    
    # 建立訓練器
    trainer = TrackSpecificTrainer(verbose=True)
    
    # 執行預測
    result = trainer.predict_2025_qualifying('Mexico', 2025)
    
    print("\n" + "="*70)
    print("預測結果摘要")
    print("="*70)
    
    if result.get('success'):
        print(f"✅ 預測成功")
        print(f"\n評估指標:")
        print(f"  MAE (時間誤差): {result['mae']:.4f}s")
        print(f"  R² Score: {result['r2']:.4f}")
        print(f"  Spearman (名次相關): {result['spearman']:.4f}")
    else:
        print(f"❌ 預測失敗")
        print(f"錯誤訊息: {result.get('message')}")
    
    return result

if __name__ == '__main__':
    main()
