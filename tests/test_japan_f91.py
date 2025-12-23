#!/usr/bin/env python3
"""測試 Japan F91 預測"""
import sys
import traceback
from CLI_modules.cli.prediction.fp2_race_ml_predictor_v2 import FP2RaceMLPredictorV2

try:
    print("開始測試 Japan F91 預測...")
    predictor = FP2RaceMLPredictorV2(verbose=True)
    result = predictor.predict_race(2025, 'Japan', 'FP2')
    
    if result:
        print("\n✅ 預測成功!")
        print(f"輸出檔案: {result}")
    else:
        print("\n❌ 預測失敗（返回 False）")
        
except Exception as e:
    print(f"\n❌ 預測失敗: {e}")
    print("\n完整錯誤堆疊:")
    traceback.print_exc()
