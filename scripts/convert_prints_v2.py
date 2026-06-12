#!/usr/bin/env python3
"""
批量將 GUI 模組中的 print 語句轉換為 logger 調用 - V2 簡化版

用法:
    python scripts/convert_prints_v2.py [--dry-run] [--file FILEPATH]
    
選項:
    --dry-run     預覽變更而不實際修改檔案
    --file PATH   只處理指定檔案
"""

import re
import sys
from pathlib import Path

# 目標模組目錄
GUI_MODULES_DIR = Path("modules/gui")

# 要排除的目錄和檔案模式
EXCLUDE_PATTERNS = ["demo", "test_", "__pycache__"]

# Logger import 語句
LOGGER_IMPORT_LINE = "from core.logger import get_logger"
LOGGER_INIT_LINE = "logger = get_logger(__name__)"


def should_skip_file(filepath: Path) -> bool:
    """檢查是否應該跳過此檔案"""
    path_str = str(filepath)
    for pattern in EXCLUDE_PATTERNS:
        if pattern in path_str:
            return True
    return False


def has_logger_import(content: str) -> bool:
    """檢查檔案是否已有 logger import"""
    return LOGGER_IMPORT_LINE in content


def add_logger_import(content: str) -> str:
    """添加 logger import 語句"""
    lines = content.split('\n')
    
    # 尋找適合插入的位置（在最後一個 import 之後）
    last_import_idx = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('import ') or stripped.startswith('from '):
            # 確保這不是在函數內的 import
            if i > 0:
                prev_line = lines[i-1].strip()
                if prev_line.endswith(':') or prev_line.startswith('def ') or prev_line.startswith('class '):
                    continue
            last_import_idx = i
    
    if last_import_idx >= 0:
        # 在最後一個 import 後插入空行和 logger import
        lines.insert(last_import_idx + 1, '')
        lines.insert(last_import_idx + 2, LOGGER_IMPORT_LINE)
        lines.insert(last_import_idx + 3, LOGGER_INIT_LINE)
        return '\n'.join(lines)
    
    return content


def classify_print(line: str) -> str:
    """
    根據 print 內容決定日誌等級
    
    Returns:
        'error', 'warning', 'info', 'debug'
    """
    upper = line.upper()
    
    # Error 等級
    if '[ERROR]' in upper or 'ERROR:' in upper or '❌' in line:
        return 'error'
    
    # Warning 等級
    if '[WARNING]' in upper or 'WARNING:' in upper or '⚠️' in line or '[CRITICAL]' in upper:
        return 'warning'
    
    # Info 等級
    if '[INFO]' in upper or '[OK]' in upper or '✅' in line or '[SUCCESS]' in upper:
        return 'info'
    
    # Debug 等級（其他所有）
    return 'debug'


def convert_print_line(line: str) -> str:
    """
    轉換單行 print 語句為 logger 調用
    
    Returns:
        轉換後的行，或原行（如果不需要轉換）
    """
    # 檢查是否是 print 語句
    stripped = line.strip()
    
    # 跳過註解行
    if stripped.startswith('#'):
        return line
    
    # 檢查是否包含 print(
    if 'print(' not in line:
        return line
    
    # 計算縮排
    indent = len(line) - len(line.lstrip())
    indent_str = ' ' * indent
    
    # 決定日誌等級
    level = classify_print(line)
    
    # 嘗試簡單替換 print( 為 logger.level(
    # 處理各種 print 格式
    
    # 模式1: print(f"[TAG] ...") 或 print("[TAG] ...")
    tag_pattern = r'print\((f?["\'])\[([A-Z_]+)\]\s*'
    match = re.search(tag_pattern, line)
    if match:
        quote_type = match.group(1)
        tag = match.group(2)
        # 移除標籤，因為 logger 已經有模組名稱
        # 但保留一些重要標籤作為訊息前綴
        if tag in ('ERROR', 'WARNING', 'DEBUG', 'INFO', 'OK', 'SUCCESS'):
            new_line = re.sub(tag_pattern, f'logger.{level}({quote_type}', line)
        else:
            new_line = re.sub(tag_pattern, f'logger.{level}({quote_type}[{tag}] ', line)
        return new_line
    
    # 模式2: print(f"emoji ...") - emoji 開頭
    emoji_pattern = r'print\((f?["\'])([✅❌⚠️🔄📊🚀🔍📦📅🕒🎯🏁🧹🖱️📄🧪📋🔴]+)\s*'
    match = re.search(emoji_pattern, line)
    if match:
        quote_type = match.group(1)
        # 移除 emoji
        new_line = re.sub(emoji_pattern, f'logger.{level}({quote_type}', line)
        return new_line
    
    # 模式3: print(var) 或 print(expression)
    var_pattern = r'^(\s*)print\(([^"\']+)\)$'
    match = re.match(var_pattern, line)
    if match:
        var_expr = match.group(2).strip()
        # 轉換為 f-string 格式
        new_line = f'{indent_str}logger.{level}(f"{{' + var_expr + '}")'
        return new_line
    
    # 模式4: 普通 print("...") 或 print(f"...")
    simple_pattern = r'print\((f?["\'])'
    if re.search(simple_pattern, line):
        new_line = re.sub(simple_pattern, f'logger.{level}(\\1', line)
        return new_line
    
    # 無法處理的格式，保持原樣
    return line


def process_file(filepath: Path, dry_run: bool = False) -> dict:
    """處理單個檔案"""
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
        lines = content.split('\n')
        
        # 計算原始 print 數量（排除註解）
        original_prints = sum(1 for line in lines 
                            if 'print(' in line and not line.strip().startswith('#'))
        
        if original_prints == 0:
            result['skipped'] = True
            return result
        
        # 添加 logger import（如果需要）
        need_logger = not has_logger_import(content)
        if need_logger:
            content = add_logger_import(content)
            result['logger_added'] = True
            lines = content.split('\n')
        
        # 轉換每一行
        new_lines = []
        converted = 0
        for line in lines:
            if 'print(' in line and not line.strip().startswith('#'):
                new_line = convert_print_line(line)
                if new_line != line:
                    converted += 1
                new_lines.append(new_line)
            else:
                new_lines.append(line)
        
        result['prints_converted'] = converted
        new_content = '\n'.join(new_lines)
        
        # 計算剩餘 print 數量
        remaining = sum(1 for line in new_lines 
                       if 'print(' in line and not line.strip().startswith('#'))
        result['remaining_prints'] = remaining
        
        # 寫回檔案
        if not dry_run and new_content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
    
    except Exception as e:
        result['error'] = str(e)
        import traceback
        result['traceback'] = traceback.format_exc()
    
    return result


def main():
    dry_run = '--dry-run' in sys.argv
    
    # 檢查是否指定單個檔案
    single_file = None
    if '--file' in sys.argv:
        idx = sys.argv.index('--file')
        if idx + 1 < len(sys.argv):
            single_file = Path(sys.argv[idx + 1])
    
    mode_str = "DRY RUN" if dry_run else "執行轉換"
    print(f"=== {mode_str} 模式 ===\n")
    
    # 收集檔案
    if single_file:
        files = [single_file]
    else:
        files = list(GUI_MODULES_DIR.rglob("*.py"))
    
    total_files = 0
    total_converted = 0
    total_remaining = 0
    
    for filepath in sorted(files):
        if not single_file and should_skip_file(filepath):
            continue
        
        result = process_file(filepath, dry_run)
        
        if result['skipped']:
            continue
        
        total_files += 1
        total_converted += result['prints_converted']
        total_remaining += result['remaining_prints']
        
        # 顯示結果
        rel_path = filepath.relative_to(GUI_MODULES_DIR) if not single_file else filepath
        status = "✅" if not result['error'] else "❌"
        
        if result['prints_converted'] > 0 or result['error']:
            print(f"{status} {rel_path}")
            print(f"   轉換: {result['prints_converted']}, 剩餘: {result['remaining_prints']}")
            if result['logger_added']:
                print(f"   已添加 logger import")
            if result['error']:
                print(f"   錯誤: {result['error']}")
    
    print(f"\n=== 總結 ===")
    print(f"處理檔案數: {total_files}")
    print(f"轉換 print 數: {total_converted}")
    print(f"剩餘 print 數: {total_remaining}")
    
    if dry_run:
        print("\n提示: 移除 --dry-run 參數以實際執行轉換")


if __name__ == "__main__":
    main()
