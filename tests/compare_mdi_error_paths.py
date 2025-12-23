#!/usr/bin/env python3
"""
深度比對 Brake 和 Speed MDI 的錯誤處理路徑

檢查為什麼只有 Brake 會彈出警告
"""

import os
import re

def analyze_file(filepath, module_name):
    """分析檔案的錯誤處理路徑"""
    print(f"\n{'='*80}")
    print(f"📋 分析 {module_name}")
    print(f"{'='*80}")
    
    if not os.path.exists(filepath):
        print(f"❌ 檔案不存在: {filepath}")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    # 1. 檢查 load_error 信號連接
    print("\n🔗 信號連接:")
    for i, line in enumerate(lines, 1):
        if 'load_error.connect' in line:
            print(f"  Line {i}: {line.strip()}")
    
    # 2. 檢查 _on_load_error 實現
    print("\n⚠️ _on_load_error 實現:")
    in_on_load_error = False
    for i, line in enumerate(lines, 1):
        if 'def _on_load_error' in line:
            in_on_load_error = True
            start_line = i
        elif in_on_load_error:
            if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('"""'):
                if line.startswith('    def ') or (line.strip() and not line.startswith(' ' * 4)):
                    in_on_load_error = False
                else:
                    print(f"  Line {i}: {line}")
    
    # 3. 檢查所有 QMessageBox 調用
    print("\n💬 QMessageBox 調用:")
    for i, line in enumerate(lines, 1):
        if 'QMessageBox' in line and 'critical' in line:
            print(f"  Line {i}: {line.strip()}")
    
    # 4. 檢查 load_data 調用
    print("\n📥 load_data 調用:")
    for i, line in enumerate(lines, 1):
        if 'self.data_manager.load_data' in line:
            # 打印前後 5 行上下文
            start = max(0, i-3)
            end = min(len(lines), i+3)
            print(f"  Context (lines {start+1}-{end}):")
            for j in range(start, end):
                marker = ">>> " if j == i-1 else "    "
                print(f"  {marker}Line {j+1}: {lines[j]}")
    
    # 5. 檢查錯誤處理後的邏輯
    print("\n🔄 load_initial_data 完整實現:")
    in_load_initial = False
    for i, line in enumerate(lines, 1):
        if 'def load_initial_data' in line:
            in_load_initial = True
            start_line = i
        elif in_load_initial:
            if line.strip() and not line.strip().startswith('#') and not line.strip().startswith('"""'):
                if (line.startswith('    def ') or line.startswith('    @')) and i > start_line + 1:
                    in_load_initial = False
                else:
                    print(f"  Line {i}: {line.rstrip()}")

def main():
    brake_mdi = r"modules\gui\all_drivers_brake_performance_analysis\all_drivers_brake_performance_mdi.py"
    speed_mdi = r"modules\gui\all_drivers_straight_line_speed_analysis\all_drivers_straight_line_speed_mdi.py"
    
    analyze_file(brake_mdi, "Brake Performance MDI")
    analyze_file(speed_mdi, "Speed Analysis MDI")
    
    print(f"\n{'='*80}")
    print("📊 關鍵差異總結")
    print(f"{'='*80}")
    
    # 檢查 loader 的 load_data 返回值處理
    print("\n🔍 檢查 load_data 返回值處理:")
    print("  Brake MDI:")
    check_load_data_handling(brake_mdi)
    print("\n  Speed MDI:")
    check_load_data_handling(speed_mdi)

def check_load_data_handling(filepath):
    """檢查 load_data 的返回值是否有處理"""
    if not os.path.exists(filepath):
        print("    檔案不存在")
        return
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
    
    for i, line in enumerate(lines, 1):
        if 'self.data_manager.load_data' in line:
            # 檢查是否有 if success 檢查
            next_5_lines = lines[i:min(i+5, len(lines))]
            has_success_check = any('success' in l.lower() or 'if not' in l for l in next_5_lines)
            
            print(f"    Line {i}: {line.strip()}")
            if 'success =' in line or 'if' in line:
                print(f"      ✅ 有檢查返回值")
            else:
                print(f"      ⚠️  無檢查返回值 (可能被忽略)")
            
            # 打印後續 3 行
            for j, next_line in enumerate(next_5_lines[1:4], 1):
                print(f"      +{j}: {next_line.rstrip()}")

if __name__ == "__main__":
    main()
