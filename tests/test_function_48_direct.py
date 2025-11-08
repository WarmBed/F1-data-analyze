"""
直接調用 Function 48 執行邏輯以繞過 CLI 參數解析
"""

import sys
import os

# 設置路徑
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from CLI_modules.cli.core.function_mapper import F1AnalysisFunctionMapper

def main():
    print("\n" + "="*80)
    print("🔧 直接調用 Function 48 測試")
    print("="*80)
    
    try:
        # 創建函數映射器
        mapper = F1AnalysisFunctionMapper()
        
        # 執行 Function 48
        print("\n[開始] 執行全部車手直線速度分析...")
        result = mapper.execute_function(
            function_id=48,
            year=2025,
            race="Japan",
            session="R"
        )
        
        print("\n" + "="*80)
        print("📊 執行結果")
        print("="*80)
        print(f"成功: {result.get('success')}")
        print(f"訊息: {result.get('message')}")
        print(f"Function ID: {result.get('function_id')}")
        
        if result.get("success"):
            print("\n✅ Function 48 執行成功！")
            print("💾 JSON 檔案應已生成在 json/ 目錄")
        else:
            print("\n❌ Function 48 執行失敗")
            
    except Exception as e:
        print(f"\n❌ 執行失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
