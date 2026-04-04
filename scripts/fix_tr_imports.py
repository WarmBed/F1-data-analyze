"""
tr() 覆蓋率掃描工具
====================
掃描所有 GUI .py 檔案，找出未 import tr() 的檔案，
並可選擇性地自動加入 import 語句。

用法：
    python scripts/fix_tr_imports.py              # 預覽模式
    python scripts/fix_tr_imports.py --stats      # 只顯示統計
    python scripts/fix_tr_imports.py --apply      # 自動加入 import（需確認）
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
GUI_ROOT = ROOT / "modules" / "gui"

# 各種現有的 tr() import 寫法
TR_IMPORT_PATTERNS = [
    re.compile(r"from\s+core\.gui_i18n\s+import\s+[^\n]*\btr\b"),
    re.compile(r"from\s+core\.gui_i18n\s+import\s+\("),  # 多行 import
    re.compile(r"import\s+core\.gui_i18n"),
]

CANONICAL_TR_IMPORT = "from core.gui_i18n import tr\n"


def has_tr_import(content: str) -> bool:
    """檢查檔案是否已有 tr() 相關 import。"""
    for pattern in TR_IMPORT_PATTERNS:
        if pattern.search(content):
            return True
    return False


def uses_tr_call(content: str) -> bool:
    """檢查檔案是否實際有呼叫 tr()。"""
    return bool(re.search(r'\btr\s*\(', content))


def inject_tr_import(content: str) -> str:
    """在檔案的適當位置插入 tr() import。

    優先插在最後一個 'from core.' import 後面，
    否則插在最後一個 import 後面，否則插在開頭。
    """
    lines = content.split("\n")
    last_core_import = -1
    last_import = -1

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("from core.") or stripped.startswith("import core."):
            last_core_import = i
        if stripped.startswith("from ") or stripped.startswith("import "):
            last_import = i

    insert_after = last_core_import if last_core_import >= 0 else last_import
    if insert_after >= 0:
        lines.insert(insert_after + 1, CANONICAL_TR_IMPORT.rstrip())
    else:
        # 找到 docstring 結束後插入
        lines.insert(0, CANONICAL_TR_IMPORT.rstrip())

    return "\n".join(lines)


def scan_gui_files() -> tuple[list[Path], list[Path], list[Path]]:
    """
    回傳三個列表：
    - missing_and_unused: 缺少 import，且沒有使用 tr()
    - missing_but_needs:  缺少 import，但有 tr() 呼叫（需要修復）
    - has_import:         已有 import
    """
    missing_and_unused: list[Path] = []
    missing_but_needs: list[Path] = []
    has_import: list[Path] = []

    py_files = list(GUI_ROOT.rglob("*.py"))
    for py_file in sorted(py_files):
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if has_tr_import(content):
            has_import.append(py_file)
        elif uses_tr_call(content):
            missing_but_needs.append(py_file)
        else:
            missing_and_unused.append(py_file)

    return missing_and_unused, missing_but_needs, has_import


def main() -> None:
    parser = argparse.ArgumentParser(description="tr() import 覆蓋率掃描工具")
    parser.add_argument("--stats", action="store_true", help="只顯示統計，不列出檔案")
    parser.add_argument("--apply", action="store_true", help="自動修復缺少 import 的檔案")
    args = parser.parse_args()

    if not GUI_ROOT.exists():
        print(f"找不到 GUI 目錄：{GUI_ROOT}")
        sys.exit(1)

    print(f"掃描目錄：{GUI_ROOT}")
    missing_and_unused, missing_but_needs, has_import = scan_gui_files()
    total = len(missing_and_unused) + len(missing_but_needs) + len(has_import)

    coverage_pct = (len(has_import) / total * 100) if total > 0 else 0.0

    print(f"\n=== tr() 覆蓋率報告 ===")
    print(f"  總 .py 檔案    : {total}")
    print(f"  已有 import    : {len(has_import)} ({coverage_pct:.1f}%)")
    print(f"  缺少且需要修復 : {len(missing_but_needs)}")
    print(f"  缺少但未使用   : {len(missing_and_unused)}")

    if not args.stats:
        if missing_but_needs:
            print(f"\n[需要修復 - 有 tr() 呼叫但缺少 import] ({len(missing_but_needs)} 個)")
            for f in missing_but_needs:
                rel = f.relative_to(ROOT)
                print(f"  {rel}")

        if missing_and_unused:
            print(f"\n[建議加入 import - 尚未使用 tr()] ({len(missing_and_unused)} 個)")
            for f in missing_and_unused[:20]:  # 只顯示前 20 個
                rel = f.relative_to(ROOT)
                print(f"  {rel}")
            if len(missing_and_unused) > 20:
                print(f"  ... 以及另外 {len(missing_and_unused) - 20} 個檔案")

    if args.apply:
        target_files = missing_but_needs  # 只自動修復「已使用 tr() 但缺少 import」
        if not target_files:
            print("\n沒有需要修復的檔案。")
        else:
            print(f"\n即將為 {len(target_files)} 個檔案加入 tr() import...")
            fixed = 0
            for py_file in target_files:
                try:
                    content = py_file.read_text(encoding="utf-8")
                    new_content = inject_tr_import(content)
                    py_file.write_text(new_content, encoding="utf-8")
                    fixed += 1
                    print(f"  已修復：{py_file.relative_to(ROOT)}")
                except Exception as e:
                    print(f"  失敗：{py_file.relative_to(ROOT)} - {e}")
            print(f"\n完成：已修復 {fixed} 個檔案")


if __name__ == "__main__":
    main()
