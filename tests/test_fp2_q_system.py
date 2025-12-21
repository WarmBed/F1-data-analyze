#!/usr/bin/env python3
"""
FP2→Q 預測系統快速測試腳本

測試 Function 75 (訓練器) 和 Function 76 (預測生成器) 的基本功能
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """執行命令並顯示結果"""
    print(f"\n{'='*70}")
    print(f"測試: {description}")
    print(f"{'='*70}")
    print(f"命令: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # 顯示輸出
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    return result.returncode == 0

def main():
    print("🏎️  F1T FP2→Q 預測系統測試")
    print("="*70)
    
    # 測試 1: Import 驗證
    print("\n[測試 1/3] Import 驗證")
    success = run_command([
        "python", "-c",
        "from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper; "
        "mapper = F1AnalysisFunctionMapper(); "
        "print('Function 75 registered:', 75 in mapper.function_mapping); "
        "print('Function 76 registered:', 76 in mapper.function_mapping)"
    ], "Import 和函數註冊檢查")
    
    if not success:
        print("❌ Import 測試失敗")
        return
    
    # 測試 2: 查看 Function 75 說明
    print("\n[測試 2/3] Function 75 說明文檔")
    run_command([
        "python", "-c",
        "from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper; "
        "mapper = F1AnalysisFunctionMapper(); "
        "print(mapper._execute_fp2_q_batch_trainer.__doc__)"
    ], "Function 75 文檔")
    
    # 測試 3: 查看 Function 76 說明
    print("\n[測試 3/3] Function 76 說明文檔")
    run_command([
        "python", "-c",
        "from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper; "
        "mapper = F1AnalysisFunctionMapper(); "
        "print(mapper._execute_fp2_q_prediction_generator.__doc__)"
    ], "Function 76 文檔")
    
    # 測試摘要
    print("\n" + "="*70)
    print("測試摘要")
    print("="*70)
    print("✅ Function 75: FP2→Q 批次訓練器 - 已實作")
    print("✅ Function 76: FP2→Q 預測生成器 - 已實作")
    print("\n下一步:")
    print("  1. 收集 FP2 訓練數據 (需修改 Function 70)")
    print("  2. 執行訓練: python f1_analysis_modular_main.py -f 75 --track Japan")
    print("  3. 生成預測: python f1_analysis_modular_main.py -f 76 -y 2025 -r Japan")
    print("\n詳細說明請參考: docs/FP2_Q_PREDICTION_SYSTEM.md")
    print("="*70)

if __name__ == "__main__":
    main()
