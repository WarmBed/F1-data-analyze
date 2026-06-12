#!/usr/bin/env python3
"""
批量將 GUI 模組中的 print 語句轉換為 logger 調用

用法:
    python scripts/convert_prints_to_logger.py [--dry-run]
    
選項:
    --dry-run  預覽變更而不實際修改檔案
"""

import re
import os
import sys
from pathlib import Path

# 目標模組目錄
GUI_MODULES_DIR = Path("modules/gui")

# 要排除的目錄和檔案模式
EXCLUDE_PATTERNS = [
    "demo",        # demo 目錄
    "test_",       # 測試檔案
    "__pycache__", # 快取
]

# Logger 替換規則 (按優先順序排列)
PRINT_PATTERNS = [
    # 特殊格式: 註解的 print (跳過)
    # (r'#\s*print\(', '#print('),  # 保持原樣
    
    # 帶有日誌等級標籤的 print
    (r'print\(f?"\[WARNING\]\s*', 'logger.warning(f"'),
    (r"print\(f?'\[WARNING\]\s*", "logger.warning(f'"),
    (r'print\(f?"\[ERROR\]\s*', 'logger.error(f"'),
    (r"print\(f?'\[ERROR\]\s*", "logger.error(f'"),
    (r'print\(f?"\[DEBUG\]\s*', 'logger.debug(f"'),
    (r"print\(f?'\[DEBUG\]\s*", "logger.debug(f'"),
    (r'print\(f?"\[INFO\]\s*', 'logger.info(f"'),
    (r"print\(f?'\[INFO\]\s*", "logger.info(f'"),
    
    # 帶有 OK 標籤 (轉為 info)
    (r'print\(f?"\[OK\]\s*', 'logger.info(f"'),
    (r"print\(f?'\[OK\]\s*", "logger.info(f'"),
    (r'print\(f?"✅\s*', 'logger.info(f"'),
    
    # 狀態類標籤 (轉為 debug)
    (r'print\(f?"\[(CLEAR|LOAD|REFRESH|STATUS|PROGRESS|UPDATE|EXPORT|UI|RESIZE|TABLE|RANK|VALIDATE|TITLE|SEARCH|ANNOUNCE|GREEN|TOOL)\]', r'logger.debug(f"[\1]'),
    (r'print\("\[(CLEAR|LOAD|REFRESH|STATUS|PROGRESS|UPDATE|EXPORT|UI|RESIZE|TABLE|RANK|VALIDATE|TITLE|SEARCH|ANNOUNCE|GREEN|TOOL)\]', r'logger.debug("[\1]'),
    
    # 模組名稱標籤 (轉為 debug)
    (r'print\("\[([A-Z_]+_MODULE)\]\s*', r'logger.debug("[\1] '),
    (r'print\(f"\[([A-Z_]+_MODULE)\]\s*', r'logger.debug(f"[\1] '),
    (r'print\("\[([A-Z_]+_WIDGET)\]\s*', r'logger.debug("[\1] '),
    (r'print\(f"\[([A-Z_]+_WIDGET)\]\s*', r'logger.debug(f"[\1] '),
    (r'print\("\[([A-Z_]+_LOADER)\]\s*', r'logger.debug("[\1] '),
    (r'print\(f"\[([A-Z_]+_LOADER)\]\s*', r'logger.debug(f"[\1] '),
    (r'print\("\[([A-Z_]+_MDI)\]\s*', r'logger.debug("[\1] '),
    (r'print\(f"\[([A-Z_]+_MDI)\]\s*', r'logger.debug(f"[\1] '),
    (r'print\("\[([A-Z_]+_CHART)\]\s*', r'logger.debug("[\1] '),
    (r'print\(f"\[([A-Z_]+_CHART)\]\s*', r'logger.debug(f"[\1] '),
    (r'print\("\[([A-Z_]+_ANALYSIS)\]\s*', r'logger.debug("[\1] '),
    (r'print\(f"\[([A-Z_]+_ANALYSIS)\]\s*', r'logger.debug(f"[\1] '),
    
    # Emoji 開頭的 print (轉為 debug/info)
    (r'print\(f?"🔄\s*', 'logger.debug(f"'),
    (r'print\(f?"📊\s*', 'logger.debug(f"'),
    (r'print\(f?"📦\s*', 'logger.debug(f"'),
    (r'print\(f?"🚀\s*', 'logger.info(f"'),
    (r'print\(f?"🔍\s*', 'logger.debug(f"'),
    (r'print\(f?"⚠️\s*', 'logger.warning(f"'),
    (r'print\(f?"❌\s*', 'logger.error(f"'),
    (r'print\(f?"🔴\s*', 'logger.warning(f"'),
    (r'print\(f?"📅\s*', 'logger.debug(f"'),
    (r'print\(f?"🕒\s*', 'logger.debug(f"'),
    (r'print\(f?"🎯\s*', 'logger.debug(f"'),
    (r'print\(f?"🏁\s*', 'logger.debug(f"'),
    (r'print\(f?"🧹\s*', 'logger.debug(f"'),
    (r'print\(f?"🖱️\s*', 'logger.debug(f"'),
    (r'print\(f?"📄\s*', 'logger.debug(f"'),
    (r'print\(f?"🧪\s*', 'logger.debug(f"'),
    (r'print\(f?"📋\s*', 'logger.debug(f"'),
    
    # 一般的 print with tag patterns
    (r'print\("\[([A-Z][A-Z0-9_]+)\]', r'logger.debug("[\1]'),
    (r'print\(f"\[([A-Z][A-Z0-9_]+)\]', r'logger.debug(f"[\1]'),
]

# Logger import 語句
LOGGER_IMPORT = """from core.logger import get_logger
logger = get_logger(__name__)
"""


def should_skip_file(filepath: Path) -> bool:
    """檢查是否應該跳過此檔案"""
    path_str = str(filepath)
    for pattern in EXCLUDE_PATTERNS:
        if pattern in path_str:
            return True
    return False


def has_logger_import(content: str) -> bool:
    """檢查檔案是否已有 logger import"""
    return "from core.logger import get_logger" in content


def add_logger_import(content: str) -> str:
    """添加 logger import 語句"""
    # 尋找最後一個 import 語句的位置
    lines = content.split('\n')
    last_import_idx = -1
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('import ') or stripped.startswith('from '):
            # 跳過在函數或類內部的 import
            if i > 0 and lines[i-1].strip().startswith(('def ', 'class ', 'try:', 'except')):
                continue
            last_import_idx = i
    
    if last_import_idx >= 0:
        # 在最後一個 import 後插入
        lines.insert(last_import_idx + 1, '')
        lines.insert(last_import_idx + 2, LOGGER_IMPORT.strip())
        return '\n'.join(lines)
    
    return content


def convert_prints(content: str) -> tuple:
    """
    轉換 print 語句為 logger 調用
    
    Returns:
        (轉換後的內容, 轉換數量)
    """
    count = 0
    
    for pattern, replacement in PRINT_PATTERNS:
        new_content, n = re.subn(pattern, replacement, content)
        if n > 0:
            count += n
            content = new_content
    
    return content, count


def process_file(filepath: Path, dry_run: bool = False) -> dict:
    """
    處理單個檔案
    
    Returns:
        處理結果字典
    """
    result = {
        'file': str(filepath),
        'skipped': False,
        'logger_added': False,
        'prints_converted': 0,
        'remaining_prints': 0,
        'error': None
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 計算原始 print 數量
        original_prints = len(re.findall(r'(?<!#\s*)print\(', content))
        
        # 檢查是否有 print 語句
        if original_prints == 0:
            result['skipped'] = True
            return result
        
        # 添加 logger import (如果需要)
        if not has_logger_import(content):
            content = add_logger_import(content)
            result['logger_added'] = True
        
        # 轉換 print 語句
        content, count = convert_prints(content)
        result['prints_converted'] = count
        
        # 計算剩餘 print 數量
        result['remaining_prints'] = len(re.findall(r'(?<!#\s*)print\(', content))
        
        # 寫回檔案 (如果不是 dry-run 模式且有變更)
        if not dry_run and content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


def main():
    dry_run = '--dry-run' in sys.argv
    
    if dry_run:
        print("=== DRY RUN 模式 (不會實際修改檔案) ===\n")
    else:
        print("=== 執行轉換模式 ===\n")
    
    # 收集所有 Python 檔案
    files = list(GUI_MODULES_DIR.rglob("*.py"))
    
    total_files = 0
    total_converted = 0
    total_remaining = 0
    results = []
    
    for filepath in sorted(files):
        if should_skip_file(filepath):
            continue
        
        result = process_file(filepath, dry_run)
        
        if result['skipped']:
            continue
        
        total_files += 1
        total_converted += result['prints_converted']
        total_remaining += result['remaining_prints']
        results.append(result)
        
        if result['prints_converted'] > 0:
            status = "✅" if not result['error'] else "❌"
            print(f"{status} {filepath.relative_to(GUI_MODULES_DIR)}")
            print(f"   - Logger 添加: {'是' if result['logger_added'] else '否'}")
            print(f"   - 轉換: {result['prints_converted']}, 剩餘: {result['remaining_prints']}")
            if result['error']:
                print(f"   - 錯誤: {result['error']}")
    
    print(f"\n=== 總結 ===")
    print(f"處理檔案數: {total_files}")
    print(f"轉換 print 數: {total_converted}")
    print(f"剩餘 print 數: {total_remaining}")
    
    if dry_run:
        print("\n提示: 移除 --dry-run 參數以實際執行轉換")


if __name__ == "__main__":
    main()
