#!/usr/bin/env python3
"""
快速修正所有模組中的 📅 字符編碼問題
"""

import os
import glob

def fix_calendar_emoji_in_file(file_path):
    """修正單個檔案中的 📅 字符"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否包含 📅 字符
        if '📅' in content:
            # 替換為 [DATE] 標記
            new_content = content.replace('📅', '[DATE]')
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            print(f"✅ 修正檔案: {file_path}")
            return True
        
        return False
    except Exception as e:
        print(f"❌ 修正失敗 {file_path}: {e}")
        return False

def main():
    """主要修正流程"""
    print("🔧 開始修正 📅 字符編碼問題...")
    
    # 搜尋所有 Python 檔案
    pattern = "modules/**/*.py"
    files = glob.glob(pattern, recursive=True)
    
    fixed_count = 0
    
    for file_path in files:
        if fix_calendar_emoji_in_file(file_path):
            fixed_count += 1
    
    print(f"\n📊 修正完成: {fixed_count} 個檔案")
    print("✅ 所有 📅 字符已替換為 [DATE]")

if __name__ == "__main__":
    main()
