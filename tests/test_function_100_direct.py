#!/usr/bin/env python3
"""
直接測試 Function 100 CLI 實現
"""

import sys
import traceback

def test_function_100_cli():
    """直接測試 CLI Function 100"""
    
    print("=" * 70)
    print("CLI Function 100 直接測試")
    print("=" * 70)
    
    try:
        print("\n[步驟 1] 導入模組...")
        from CLI_modules.cli.analyzer.historical_flags_analysis import (
            run_historical_flags_analysis_json
        )
        print("✅ 模組導入成功")
        
        print("\n[步驟 2] 執行分析...")
        print("參數: race=Japan, start_year=2022, end_year=2025, session_type=R")
        
        result = run_historical_flags_analysis_json(
            race="Japan",
            start_year=2022,
            end_year=2025,
            session_type="R"
        )
        
        print("\n[步驟 3] 檢查結果...")
        print(f"結果類型: {type(result)}")
        
        if isinstance(result, dict):
            print(f"成功標誌: {result.get('success')}")
            print(f"訊息: {result.get('message', 'N/A')}")
            
            if 'data' in result:
                print("\n數據結構:")
                for key in result['data'].keys():
                    print(f"  - {key}")
            
            if 'error' in result:
                print(f"\n錯誤: {result['error']}")
                if 'traceback' in result:
                    print(f"追蹤: {result['traceback']}")
        
        print("\n✅ 測試完成")
        return result
        
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        print("\n完整追蹤:")
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = test_function_100_cli()
    
    if result:
        print("\n" + "=" * 70)
        print("結果摘要:")
        print("=" * 70)
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str)[:1000])
