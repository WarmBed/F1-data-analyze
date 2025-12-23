#!/usr/bin/env python3
"""
直接測試功能 76 - 集成學習訓練
繞過 CLI 參數解析，直接調用函數映射器
"""

import sys
import os

# 確保路徑正確
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'CLI_modules'))
sys.path.insert(0, current_dir)

print("=" * 70)
print("功能 76 直接測試 - 集成學習訓練")
print("=" * 70)

try:
    print("\n[1/4] 導入模組...")
    from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper
    print("✅ 函數映射器導入成功")
    
    print("\n[2/4] 創建映射器實例...")
    mapper = F1AnalysisFunctionMapper()
    print("✅ 映射器實例創建成功")
    
    print("\n[3/4] 檢查功能 76 是否註冊...")
    if 76 in mapper.function_mapping:
        print("✅ 功能 76 已註冊")
    else:
        print("❌ 功能 76 未註冊")
        sys.exit(1)
    
    print("\n[4/4] 執行功能 76...")
    print("-" * 70)
    result = mapper.execute_function_by_number(76)
    print("-" * 70)
    
    print("\n執行結果:")
    print(f"  成功: {result.get('success')}")
    print(f"  訊息: {result.get('message')}")
    
    if result.get('success'):
        print(f"\n✅ 訓練成功！")
        print(f"  最佳方法: {result.get('best_method')}")
        print(f"  驗證 MAE: {result.get('validation_mae')}")
        if result.get('test_mae'):
            print(f"  測試 MAE: {result.get('test_mae'):.4f}s")
            print(f"  改進幅度: {result.get('improvement_pct'):+.2f}%")
            print(f"  目標達成: {'是' if result.get('target_achieved') else '否'}")
    else:
        print(f"\n❌ 訓練失敗！")
        print(f"  錯誤詳情:")
        for key, value in result.items():
            if key not in ['success', 'message']:
                print(f"    {key}: {value}")
    
except ImportError as e:
    print(f"\n❌ 導入錯誤: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ 執行錯誤: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("測試完成")
print("=" * 70)
