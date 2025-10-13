#!/usr/bin/env python3
"""測試 CLI function 98 並捕獲詳細錯誤"""

import sys
import traceback

try:
    print("[DEBUG] 開始測試 CLI function 98...")
    
    # 導入分析函數
    from CLI_modules.cli.analyzer.team_color_analysis import generate_team_color_report
    
    print("[DEBUG] 模組導入成功，開始執行...")
    
    # 執行分析
    result = generate_team_color_report(
        year=2024,
        colormap="fastf1",
        save_json=True,
        include_drivers=True,
        force=False,
    )
    
    print("\n[SUCCESS] 分析完成!")
    print(f"成功: {result.get('success')}")
    print(f"訊息: {result.get('message')}")
    print(f"車隊數: {result.get('metadata', {}).get('teams_count')}")
    print(f"車手數: {len(result.get('data', {}).get('drivers', {}))}")
    
    if result.get("metadata", {}).get("output_file"):
        print(f"輸出檔案: {result['metadata']['output_file']}")

except Exception as e:
    print("\n[ERROR] 執行失敗!")
    print(f"錯誤類型: {type(e).__name__}")
    print(f"錯誤訊息: {str(e)}")
    print("\n完整追蹤:")
    traceback.print_exc()
    sys.exit(1)
