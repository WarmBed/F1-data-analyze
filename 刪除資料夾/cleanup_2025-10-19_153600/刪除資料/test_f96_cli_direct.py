#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Function 96 完整測試腳本 - 使用正確的 CLI 調用方式
"""
import sys
import os

# 直接執行 CLI 主程式的模擬環境
if __name__ == "__main__":
    try:
        # 模擬命令列參數
        sys.argv = [
            "f1_analysis_modular_main.py",
            "-f", "96",
            "-y", "2025",
            "-r", "Japan"
        ]
        
        print("=" * 80)
        print("Function 96 CLI 測試")
        print("命令: python f1_analysis_modular_main.py -f 96 -y 2025 -r Japan")
        print("=" * 80)
        
        # 導入並執行主程式
        from f1_analysis_modular_main import F1AnalysisModularCLI
        
        app = F1AnalysisModularCLI()
        success = app.run()
        
        print("\n" + "=" * 80)
        if success:
            print("✅ Function 96 測試成功")
            sys.exit(0)
        else:
            print("❌ Function 96 測試失敗")
            print(f"錯誤訊息: {getattr(app, 'last_error_message', 'Unknown')}")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ 測試失敗: {type(e).__name__}")
        print(f"錯誤訊息: {str(e)}")
        import traceback
        print("\n完整 Traceback:")
        traceback.print_exc()
        sys.exit(1)
