#!/usr/bin/env python3
"""
快速訓練腳本 - Live Win Probability Model
"""

from CLI_modules.cli.prediction.live_win_probability.model_trainer import WinProbabilityModelTrainer
from datetime import datetime

def main():
    print("=" * 60)
    print("Live Win Probability - Model Training")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # 初始化訓練器
    trainer = WinProbabilityModelTrainer()

    # 載入數據
    print("[1/4] Loading data...")
    n_train, n_val = trainer.load_data(
        "data/live_win_probability/training_data.csv",
        "data/live_win_probability/validation_data.csv"
    )
    print(f"  Training samples: {n_train}")
    print(f"  Validation samples: {n_val}")
    print()

    # 訓練模型
    print("[2/4] Training model...")
    print("  (This may take 1-2 minutes...)")
    metrics = trainer.train(
        n_estimators=200,
        max_depth=8,
        learning_rate=0.1,
        verbose=True
    )
    print()

    # 顯示特徵重要性
    print("[3/4] Feature Importance (Top 10):")
    importance = trainer.get_feature_importance()
    for i, (feature, imp) in enumerate(list(importance.items())[:10]):
        bar = "#" * int(imp * 50)
        print(f"  {i+1:2d}. {feature:25s}: {imp:.4f} {bar}")
    print()

    # 保存模型
    print("[4/4] Saving model...")
    trainer.save_model("models/win_probability_xgb_v1.pkl")

    print()
    print("=" * 60)
    print("Training Summary")
    print("=" * 60)
    print(f"  Validation MAE: {metrics['val_mae']:.3f} positions")
    print(f"  Validation RMSE: {metrics['val_rmse']:.3f} positions")
    print(f"  Exact Position Accuracy: {metrics['val_exact_accuracy']:.2%}")
    print(f"  Top-3 Prediction Accuracy: {metrics['val_top3_accuracy']:.2%}")
    print(f"  Model saved to: models/win_probability_xgb_v1.pkl")
    print()


if __name__ == "__main__":
    main()
