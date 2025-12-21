#!/usr/bin/env python3
"""
修復 logger import 位置問題

確保 logger import 在檔案開頭（在其他 import 之後，但在代碼之前）
"""

import re
import sys
from pathlib import Path

GUI_MODULES_DIR = Path("c:/Users/mike2/OneDrive/Code/F1-data-analyze/modules/gui")
EXCLUDE_PATTERNS = ["demo", "test_", "__pycache__"]

LOGGER_IMPORT = "from core.logger import get_logger"
LOGGER_INIT = "logger = get_logger(__name__)"


def should_skip_file(filepath: Path) -> bool:
    path_str = str(filepath)
    for pattern in EXCLUDE_PATTERNS:
        if pattern in path_str:
            return True
    return False


def fix_logger_position(filepath: Path, dry_run: bool = False) -> dict:
    """修復 logger import 位置"""
    result = {
        'file': str(filepath),
        'fixed': False,
        'error': None
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否有 logger import
        if LOGGER_IMPORT not in content:
            return result
        
        lines = content.split('\n')
        
        # 找到所有 logger 相關行的位置
        logger_import_indices = []
        logger_init_indices = []
        
        for i, line in enumerate(lines):
            if LOGGER_IMPORT in line and not line.strip().startswith('#'):
                logger_import_indices.append(i)
            if LOGGER_INIT in line and not line.strip().startswith('#'):
                logger_init_indices.append(i)
        
        # 如果只有一個 logger import，檢查它是否在正確位置
        if len(logger_import_indices) == 1:
            idx = logger_import_indices[0]
            # 檢查前面是否都是 import/from 語句、註解、空行或 docstring
            valid_position = True
            in_docstring = False
            
            for i in range(idx):
                line = lines[i].strip()
                if line.startswith('"""') or line.startswith("'''"):
                    in_docstring = not in_docstring
                    continue
                if in_docstring:
                    continue
                if not line or line.startswith('#'):
                    continue
                if line.startswith('import ') or line.startswith('from '):
                    continue
                if line.startswith('#!/'):
                    continue
                # 發現非 import 代碼
                valid_position = False
                break
            
            if valid_position:
                return result  # 位置正確，不需要修復
        
        # 需要修復：移除現有的 logger import/init，然後在正確位置添加
        new_lines = []
        logger_lines_to_add = []
        
        for i, line in enumerate(lines):
            if i in logger_import_indices or i in logger_init_indices:
                logger_lines_to_add.append(line)
                continue
            new_lines.append(line)
        
        # 找到最後一個 import 語句的位置
        last_import_idx = -1
        in_docstring = False
        
        for i, line in enumerate(new_lines):
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_docstring = not in_docstring
                continue
            if in_docstring:
                continue
            if stripped.startswith('import ') or stripped.startswith('from '):
                # 確保不是函數內的 import
                indent = len(line) - len(line.lstrip())
                if indent == 0:
                    last_import_idx = i
        
        if last_import_idx >= 0:
            # 在最後一個 import 後插入 logger import
            insert_lines = ['', LOGGER_IMPORT, LOGGER_INIT]
            new_lines = new_lines[:last_import_idx+1] + insert_lines + new_lines[last_import_idx+1:]
            result['fixed'] = True
            
            if not dry_run:
                new_content = '\n'.join(new_lines)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
        
    except Exception as e:
        result['error'] = str(e)
    
    return result


def main():
    dry_run = '--dry-run' in sys.argv
    
    mode = "DRY RUN" if dry_run else "執行修復"
    print(f"=== {mode} 模式 ===\n")
    
    files = list(GUI_MODULES_DIR.rglob("*.py"))
    
    fixed_count = 0
    
    for filepath in sorted(files):
        if should_skip_file(filepath):
            continue
        
        result = fix_logger_position(filepath, dry_run)
        
        if result['fixed']:
            fixed_count += 1
            print(f"✅ {filepath.relative_to(GUI_MODULES_DIR)}")
            if result['error']:
                print(f"   錯誤: {result['error']}")
    
    print(f"\n=== 總結 ===")
    print(f"修復檔案數: {fixed_count}")
    
    if dry_run:
        print("\n提示: 移除 --dry-run 參數以實際執行修復")


if __name__ == "__main__":
    main()
