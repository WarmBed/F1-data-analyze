#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修復 f1_analysis_modular_main.py 中的 Unicode 編碼問題
替換所有 emoji 字符為 ASCII 兼容的文字
"""
import re

def fix_unicode_emoji(file_path):
    """修復檔案中的 Unicode emoji 字符"""
    
    # emoji 到 ASCII 的映射
    emoji_replacements = {
        '✅': '[OK]',
        '❌': '[ERROR]',
        '⚠️': '[WARNING]',  
        '📊': '[DATA]',
        '🔄': '[REFRESH]',
        '🚀': '[START]',
        '📈': '[CHART]',
        '📉': '[DECLINE]',
        '🎯': '[TARGET]',
        '🔍': '[SEARCH]',
        '💾': '[SAVE]',
        '📋': '[LIST]',
        '🔧': '[TOOL]',
        '🌧️': '[RAIN]',
        '🏁': '[FINISH]',
        '🏎️': '[CAR]',
        '📝': '[NOTE]',
        '🔥': '[HOT]',
        '⭐': '[STAR]',
        '💡': '[IDEA]',
        '🎉': '[CELEBRATION]'
    }
    
    try:
        # 讀取檔案
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"原始檔案大小: {len(content)} 字符")
        
        # 統計替換數量
        total_replacements = 0
        
        # 執行替換
        for emoji, replacement in emoji_replacements.items():
            count = content.count(emoji)
            if count > 0:
                content = content.replace(emoji, replacement)
                total_replacements += count
                print(f"替換 {emoji} -> {replacement}: {count} 次")
        
        # 寫回檔案
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\n✅ 修復完成！")
        print(f"總共替換了 {total_replacements} 個 emoji 字符")
        print(f"修復後檔案大小: {len(content)} 字符")
        
        return True
        
    except Exception as e:
        print(f"❌ 修復失敗: {e}")
        return False

if __name__ == "__main__":
    file_path = "f1_analysis_modular_main.py"
    fix_unicode_emoji(file_path)
