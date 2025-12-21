"""
簡化版 Gap 欄位測試 - 僅檢查代碼變更
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 80)
print("Gap 欄位顯示修復驗證")
print("=" * 80)

# 測試 Constructor Standings
print("\n[1] Constructor Standings Widget")
with open('modules/gui/constructor_standings/constructor_standings_widget.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
if 'f"+{delta:.1f}"' in content:
    print("    X 仍有 + 符號")
elif 'f"{delta:.1f}"' in content and '# 4. Points delta (只顯示數字，不顯示符號)' in content:
    print("    ✓ 修復完成：只顯示數字，不顯示符號")
    print("    ✓ 格式：f\"{delta:.1f}\"")
else:
    print("    ? 狀態未知")

# 測試 Driver Standings  
print("\n[2] Driver Standings Widget")
with open('modules/gui/driver_standings/driver_standings_widget.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
if 'f"+{delta:.1f}"' in content:
    print("    X 仍有 + 符號")
elif 'f"{delta:.1f}"' in content and '# 6. 落後差距 (只顯示數字，不顯示符號)' in content:
    print("    ✓ 修復完成：只顯示數字，不顯示符號")
    print("    ✓ 格式：f\"{delta:.1f}\"")
else:
    print("    ? 狀態未知")

print("\n" + "=" * 80)
print("修改前範例：+21.0 (帶符號)")
print("修改後範例：21.0 (純數字)")
print("=" * 80)
