#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接測試 Function 96 - 繞過 CLI 主程式
"""
import sys
import traceback

def test_f96_direct():
    """直接測試 _execute_race_weather_forecast"""
    try:
        print("=" * 80)
        print("開始直接測試 Function 96")
        print("=" * 80)
        
        # Step 1: Import function_mapper
        print("\n[1/5] 引入 function_mapper...")
        from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper
        print("✅ function_mapper 引入成功")
        
        # Step 2: Initialize mapper
        print("\n[2/5] 初始化 mapper...")
        mapper = F1AnalysisFunctionMapper(
            year=2025,
            race="Japan",
            session="R",
            driver1=None,
            driver2=None
        )
        print("✅ mapper 初始化成功")
        
        # Step 3: Check _execute_race_weather_forecast exists
        print("\n[3/5] 檢查 _execute_race_weather_forecast 方法...")
        if hasattr(mapper, '_execute_race_weather_forecast'):
            print("✅ 方法存在")
        else:
            print("❌ 方法不存在")
            return False
        
        # Step 4: Execute function
        print("\n[4/5] 執行 _execute_race_weather_forecast...")
        result = mapper._execute_race_weather_forecast(
            year=2025,
            race="Japan",
            force=False
        )
        print("✅ 執行完成")
        
        # Step 5: Check result
        print("\n[5/5] 檢查結果...")
        if result:
            print(f"✅ 結果類型: {type(result)}")
            if isinstance(result, dict):
                print(f"✅ 結果鍵: {result.keys()}")
                if 'success' in result:
                    print(f"✅ success = {result['success']}")
                if 'message' in result:
                    print(f"✅ message = {result['message']}")
            return True
        else:
            print("❌ 結果為空")
            return False
            
    except Exception as e:
        print(f"\n❌ 測試失敗: {type(e).__name__}")
        print(f"錯誤訊息: {str(e)}")
        print("\n完整 Traceback:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_f96_direct()
    print("\n" + "=" * 80)
    if success:
        print("✅ Function 96 直接測試成功")
        sys.exit(0)
    else:
        print("❌ Function 96 直接測試失敗")
        sys.exit(1)
