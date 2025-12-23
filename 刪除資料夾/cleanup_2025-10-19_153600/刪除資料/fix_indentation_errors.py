# -*- coding: utf-8 -*-
"""
修復縮排錯誤 - 所有被編輯的模組都有 def _ensure_telemetry_data_for_fastest_laps 缺少縮排
"""

import re
import os

FILES_TO_FIX = [
    ('modules/gui/lap_analysis/speed_analysis/speed_analysis_mdi.py', 1014),
    ('modules/gui/lap_analysis/Throttle_analysis/throttle_analysis_mdi.py', None),
    ('modules/gui/lap_analysis/gear_analysis/gear_analysis_mdi.py', None),
    ('modules/gui/lap_analysis/acceleration_analysis/acceleration_analysis_mdi.py', None),
    ('modules/gui/lap_analysis/speeddiff_analysis/speeddiff_analysis_mdi.py', None),
    ('modules/gui/lap_analysis/distancediff_analysis/distancediff_analysis_mdi.py', None)
]

def fix_indentation(file_path):
    """修復檔案中 def _ensure_telemetry_data_for_fastest_laps 的縮排"""
    print(f"\n{'='*80}")
    print(f"修復: {file_path}")
    print(f"{'='*80}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 尋找錯誤的模式：def _ensure_telemetry_data_for_fastest_laps (沒有前導空格)
        # 應該是:     def _ensure_telemetry_data_for_fastest_laps (4個空格)
        
        # 計算修復前後
        before_count = content.count('\ndef _ensure_telemetry_data_for_fastest_laps(')
        
        # 修復：在行首的 def _ensure_telemetry_data_for_fastest_laps 前添加 4 個空格
        fixed_content = re.sub(
            r'\ndef _ensure_telemetry_data_for_fastest_laps\(',
            r'\n    def _ensure_telemetry_data_for_fastest_laps(',
            content
        )
        
        after_count = fixed_content.count('\n    def _ensure_telemetry_data_for_fastest_laps(')
        
        if before_count > 0:
            print(f"  ✅ 找到 {before_count} 個缺少縮排的方法定義")
            print(f"  ✅ 已修復為正確的縮排 (4 個空格)")
            
            # 備份
            backup_path = file_path + '.backup_indent'
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  📦 已備份: {backup_path}")
            
            # 寫入修復後的內容
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)
            print(f"  💾 已寫入修復後的檔案")
            
            return True
        else:
            print(f"  ⏭️  沒有找到需要修復的縮排問題")
            return False
            
    except Exception as e:
        print(f"  ❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_syntax(file_path):
    """驗證 Python 語法"""
    import py_compile
    try:
        py_compile.compile(file_path, doraise=True)
        print(f"  ✅ 語法驗證通過")
        return True
    except py_compile.PyCompileError as e:
        print(f"  ❌ 語法錯誤: {e}")
        return False

def main():
    print("🚀 開始修復縮排錯誤...")
    print(f"📋 需要檢查的檔案數: {len(FILES_TO_FIX)}")
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for file_path, line_num in FILES_TO_FIX:
        if fix_indentation(file_path):
            # 驗證語法
            if verify_syntax(file_path):
                success_count += 1
            else:
                fail_count += 1
        else:
            skip_count += 1
    
    print("\n" + "="*80)
    print("📊 修復結果統計:")
    print(f"  ✅ 成功修復: {success_count}")
    print(f"  ⏭️  無需修復: {skip_count}")
    print(f"  ❌ 修復失敗: {fail_count}")
    print("="*80)
    
    if fail_count == 0:
        print("\n🎉 所有檔案縮排修復完成且語法驗證通過！")
    else:
        print("\n⚠️ 部分檔案修復失敗，請檢查錯誤訊息")

if __name__ == "__main__":
    main()
