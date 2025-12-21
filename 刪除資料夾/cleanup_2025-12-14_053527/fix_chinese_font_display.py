"""
修復 visualize_f120_results.py 中的中文字體顯示問題
將所有含中文的 text/title/label 加上 fontproperties 參數
"""

import re
from pathlib import Path

def fix_font_properties(file_path: str):
    """在所有中文文字設定處加上 fontproperties=self.chinese_font"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 定義需要替換的模式
    replacements = [
        # suptitle 含中文的行
        (
            r"(fig\.suptitle\(f'[^']*[\u4e00-\u9fff]+[^']*',\s*\n\s*fontsize=\d+,\s*fontweight='bold')\)",
            r"\1, fontproperties=self.chinese_font)"
        ),
        (
            r"(plt\.suptitle\(f'[^']*[\u4e00-\u9fff]+[^']*',\s*\n\s*fontsize=\d+,\s*fontweight='bold')\)",
            r"\1, fontproperties=self.chinese_font)"
        ),
        # set_xlabel 含中文的行
        (
            r"(ax\.set_xlabel\('[^']*[\u4e00-\u9fff]+[^']*',\s*fontsize=\d+,\s*fontweight='bold')\)",
            r"\1, fontproperties=self.chinese_font)"
        ),
        (
            r"(plt\.xlabel\('[^']*[\u4e00-\u9fff]+[^']*',\s*fontsize=\d+,\s*fontweight='bold')\)",
            r"\1, fontproperties=self.chinese_font)"
        ),
        # set_ylabel 含中文的行
        (
            r"(ax\.set_ylabel\('[^']*[\u4e00-\u9fff]+[^']*',\s*fontsize=\d+,\s*fontweight='bold')\)",
            r"\1, fontproperties=self.chinese_font)"
        ),
        (
            r"(plt\.ylabel\('[^']*[\u4e00-\u9fff]+[^']*',\s*fontsize=\d+,\s*fontweight='bold')\)",
            r"\1, fontproperties=self.chinese_font)"
        ),
        # set_title 含中文的行
        (
            r"(ax\.set_title\(f?'[^']*[\u4e00-\u9fff]+[^']*',\s*\n?\s*fontsize=\d+,\s*fontweight='bold')\)",
            r"\1, fontproperties=self.chinese_font)"
        ),
        (
            r"(plt\.title\(f?'[^']*[\u4e00-\u9fff]+[^']*',\s*\n?\s*fontsize=\d+,\s*fontweight='bold')\)",
            r"\1, fontproperties=self.chinese_font)"
        ),
    ]
    
    modified = content
    changes = 0
    
    for pattern, replacement in replacements:
        new_modified, count = re.subn(pattern, replacement, modified)
        if count > 0:
            print(f"✅ 替換 {count} 處: {pattern[:50]}...")
            modified = new_modified
            changes += count
    
    if changes > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified)
        print(f"\n✅ 共修改 {changes} 處，檔案已更新")
    else:
        print("⚠️ 沒有找到需要修改的地方")
    
    return changes

if __name__ == '__main__':
    file_path = Path(__file__).parent / 'visualize_f120_results.py'
    print(f"修復檔案: {file_path}\n")
    fix_font_properties(str(file_path))
