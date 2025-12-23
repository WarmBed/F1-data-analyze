#!/usr/bin/env python3
"""測試 Function 54 執行流程"""
import sys
import warnings

# 抑制所有 FutureWarning
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

import argparse
from f1_analysis_modular_main import F1AnalysisModularCLI

# 創建參數
args = argparse.Namespace(
    year=2025,
    race='Singapore',
    session='R',
    function=54,
    driver=None,
    driver2=None,
    lap=None,
    lap1=None,
    lap2=None,
    corner=None,
    show_detailed_output=False,
    no_detailed_output=True,
    language=None,
    list_races=False
)

print("\n" + "="*80)
print("🧪 Function 54 - Throttle Box Plot 測試執行")
print("="*80)

cli = F1AnalysisModularCLI(args)
print("\n✅ CLI 實例創建成功\n")

result = cli.run()

print("\n" + "="*80)
print(f"📊 執行結果: {'成功' if result else '失敗'}")
print("="*80)

if result:
    print("\n✅ Function 54 執行成功！")
    print("📁 請檢查 json/ 目錄中的 throttle_ratio_2025_singapore_R.json 檔案")
else:
    print("\n❌ 執行失敗")
    if hasattr(cli, 'last_error_message') and cli.last_error_message:
        print(f"錯誤訊息: {cli.last_error_message}")
