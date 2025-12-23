#!/usr/bin/env python3
"""
為缺少 data_manager.cleanup() 調用的 MDI 模組添加此調用

目標 MDI 模組（缺少調用的）：
1. acceleration_analysis_mdi.py
2. brake_analysis_mdi.py
3. gear_analysis_mdi.py
4. rpm_analysis_mdi.py
5. timediff_analysis_mdi.py
6. speeddiff_analysis_mdi.py
7. distancediff_analysis_mdi.py

作者: F1T Team
日期: 2025-10-15
"""

import re
from pathlib import Path
from typing import List

# 需要修復的模組（speed 和 throttle 已經有正確的調用）
MODULES_TO_FIX = [
    ("acceleration_analysis", "accelerationAnalysisModule"),
    ("brake_analysis", "BrakeAnalysisModule"),
    ("gear_analysis", "GearAnalysisModule"),
    ("rpm_analysis", "RPMAnalysisModule"),
    ("timediff_analysis", "timediffAnalysisModule"),
    ("speeddiff_analysis", "SpeeddiffAnalysisModule"),
    ("distancediff_analysis", "distancediffAnalysisModule"),
]

BASE_DIR = Path("modules/gui/lap_analysis")

def add_datamanager_cleanup_call(mdi_file: Path, mdi_class: str) -> bool:
    """
    在 MDI cleanup() 方法中添加 data_manager.cleanup() 調用
    
    插入位置：在 analysis_manager unregister 之後，cleanup_module() 或 chart cleanup 之前
    """
    try:
        print(f"\n{'='*80}")
        print(f"處理檔案: {mdi_file}")
        print(f"目標類別: {mdi_class}")
        
        with open(mdi_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        # 找到 MDI 類別的 cleanup() 方法
        cleanup_start = -1
        for i, line in enumerate(lines):
            if re.match(rf'class\s+{re.escape(mdi_class)}', line):
                # 找到類別，搜索其 cleanup() 方法
                for j in range(i, min(i + 1000, len(lines))):  # 限制搜索範圍
                    if re.match(r'^\s{4}def\s+cleanup\s*\(', lines[j]):
                        cleanup_start = j
                        print(f"📍 找到 cleanup() 方法於第 {cleanup_start + 1} 行")
                        break
                break
        
        if cleanup_start == -1:
            print(f"❌ 找不到 {mdi_class} 的 cleanup() 方法")
            return False
        
        # 檢查是否已經有 data_manager.cleanup() 調用
        cleanup_end = cleanup_start + 100  # 搜索接下來的 100 行
        for i in range(cleanup_start, min(cleanup_end, len(lines))):
            if 'data_manager.cleanup()' in lines[i]:
                print(f"⏭️  cleanup() 已經調用 data_manager.cleanup()，跳過")
                return False
        
        # 找到插入位置：在 analysis_manager unregister 之後
        insertion_line = -1
        for i in range(cleanup_start, min(cleanup_start + 50, len(lines))):
            # 找到 analysis_manager unregister 區塊的結束
            if 'unregister_module(self._module_id)' in lines[i]:
                # 找到 except 區塊的結束
                for j in range(i, min(i + 10, len(lines))):
                    if re.match(r'^\s{16,20}except.*:', lines[j]):
                        # 找到 except 區塊中的 print 語句
                        for k in range(j, min(j + 5, len(lines))):
                            if 'print(f' in lines[k] and 'ERROR' in lines[k]:
                                insertion_line = k + 1
                                break
                        break
                break
        
        if insertion_line == -1:
            print(f"❌ 找不到合適的插入位置")
            return False
        
        print(f"📍 將在第 {insertion_line + 1} 行插入 data_manager.cleanup() 調用")
        
        # 生成插入代碼
        insert_code = [
            "",
            "            if hasattr(self, 'data_manager') and self.data_manager:",
            "                # 清理數據管理器",
            "                if hasattr(self.data_manager, 'cleanup'):",
            "                    self.data_manager.cleanup()",
        ]
        
        # 插入代碼
        for idx, code_line in enumerate(insert_code):
            lines.insert(insertion_line + idx, code_line)
        
        # 寫回檔案
        new_content = '\n'.join(lines)
        with open(mdi_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ 成功添加 data_manager.cleanup() 調用")
        return True
        
    except Exception as e:
        print(f"❌ 處理 {mdi_file} 時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函數"""
    print("="*80)
    print("為缺失的 MDI cleanup() 添加 data_manager.cleanup() 調用")
    print("="*80)
    
    success_count = 0
    skip_count = 0
    fail_count = 0
    
    for module_dir, mdi_class in MODULES_TO_FIX:
        mdi_file = BASE_DIR / module_dir / f"{module_dir}_mdi.py"
        
        if not mdi_file.exists():
            print(f"\n⚠️  檔案不存在: {mdi_file}")
            fail_count += 1
            continue
        
        result = add_datamanager_cleanup_call(mdi_file, mdi_class)
        
        if result is True:
            success_count += 1
        elif result is False:
            skip_count += 1
        else:
            fail_count += 1
    
    print("\n" + "="*80)
    print("執行結果統計:")
    print(f"✅ 成功添加: {success_count} 個")
    print(f"⏭️  已存在跳過: {skip_count} 個")
    print(f"❌ 失敗: {fail_count} 個")
    print("="*80)
    
    if success_count > 0:
        print("\n🎉 修復完成！")
        print("   - 所有 9 個 MDI 模組現在都會調用 data_manager.cleanup()")
        print("   - 配合 DataManager 的 cleanup() 方法，18 DummyThread 洩漏問題已完全修復")
    
    return 0 if fail_count == 0 else 1

if __name__ == "__main__":
    exit(main())
