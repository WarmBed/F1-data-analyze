"""
腳本分類遷移工具
================
掃描根目錄中的散落腳本並建議分類位置。
執行後會列出建議，不會自動移動任何檔案。

用法：
    python scripts/organize_root_scripts.py          # 僅預覽
    python scripts/organize_root_scripts.py --apply  # 實際移動（有風險：確認後再用）
"""
from __future__ import annotations

import sys
import shutil
import argparse
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()

# 分類規則：前綴 → 目標子目錄
PREFIX_RULES: list[tuple[str, str]] = [
    ("check_",    "scripts/diagnostics"),
    ("debug_",    "scripts/diagnostics"),
    ("temp_",     "scripts/one-off"),
    ("batch_",    "scripts/batch"),
    ("generate_", "scripts/generators"),
    ("analyze_",  "scripts/generators"),
    ("verify_",   "scripts/validators"),
    ("validate_", "scripts/validators"),
    ("export_",   "scripts/generators"),
    ("collect_",  "scripts/batch"),
    ("download_", "scripts/batch"),
    ("compare_",  "scripts/diagnostics"),
    ("evaluate_", "scripts/validators"),
]

# 根目錄保留的核心檔案（不移動）
KEEP_IN_ROOT: set[str] = {
    "f1t_gui_main.py",
    "f1_analysis_modular_main.py",
    "refactored_api.py",
    "APIserver.py",
    "strategy_simulator_main.py",
    "setup.py",
    "conftest.py",
    "example_f125_usage.py",
}

def classify_file(py_file: Path) -> str | None:
    """根據前綴規則決定目標目錄，回傳 None 表示不移動。"""
    name = py_file.name
    if name in KEEP_IN_ROOT:
        return None
    for prefix, dest in PREFIX_RULES:
        if name.startswith(prefix):
            return dest
    return "scripts/one-off"  # 未匹配的非核心腳本

def main() -> None:
    parser = argparse.ArgumentParser(description="根目錄腳本分類工具")
    parser.add_argument("--apply", action="store_true", help="實際移動檔案（危險！）")
    args = parser.parse_args()

    root_py_files = [
        f for f in ROOT.glob("*.py")
        if f.name not in KEEP_IN_ROOT
    ]

    print(f"掃描完成：根目錄共 {len(root_py_files)} 個非核心 .py 檔案\n")

    moves: list[tuple[Path, Path]] = []
    for py_file in sorted(root_py_files):
        dest_dir = classify_file(py_file)
        if dest_dir:
            dest = ROOT / dest_dir / py_file.name
            moves.append((py_file, dest))
            action = "移動" if args.apply else "建議移至"
            print(f"  {action}：{py_file.name}  →  {dest_dir}/")

    print(f"\n共 {len(moves)} 個檔案建議移動")

    if args.apply:
        print("\n警告：即將移動檔案，這可能破壞 import！")
        confirm = input("輸入 YES 確認：")
        if confirm.strip().upper() != "YES":
            print("已取消")
            sys.exit(0)
        for src, dst in moves:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
            print(f"  已移動：{src.name}")
        print("完成")
    else:
        print("\n（預覽模式。加上 --apply 才會實際移動檔案）")

if __name__ == "__main__":
    main()
