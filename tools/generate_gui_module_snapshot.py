#!/usr/bin/env python3
"""Generate a snapshot of GUI modules for Phase 0 planning."""
from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Dict, List, Tuple

SOURCE_EXTENSIONS = {".py", ".pyi", ".qml"}
DEFAULT_ROOT = Path("modules/gui")


def iter_module_directories(root: Path) -> List[Path]:
    modules: List[Path] = []
    for path in sorted(root.iterdir()):
        if not path.is_dir():
            continue
        if path.name.startswith("__"):  # skip __pycache__ etc.
            continue
        modules.append(path)
    return modules


def count_lines(path: Path) -> int:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return sum(1 for _ in fh)
    except UnicodeDecodeError:
        with path.open("r", encoding="utf-8", errors="ignore") as fh:
            return sum(1 for _ in fh)
    except OSError:
        return 0


def collect_files(module_path: Path) -> Tuple[List[Dict[str, object]], Dict[str, int]]:
    files: List[Dict[str, object]] = []
    stats = defaultdict(int)
    for file_path in module_path.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix not in SOURCE_EXTENSIONS:
            continue
        rel_path = file_path.relative_to(module_path.parent)
        line_count = count_lines(file_path)
        files.append({
            "relative_path": rel_path.as_posix(),
            "lines": line_count,
        })
        stats["files"] += 1
        stats["lines"] += line_count
    files.sort(key=lambda f: f["relative_path"])
    return files, stats


def build_snapshot(root: Path) -> Dict[str, object]:
    modules_data: List[Dict[str, object]] = []
    total_files = 0
    total_lines = 0
    for module_dir in iter_module_directories(root):
        files, stats = collect_files(module_dir)
        modules_data.append({
            "module": module_dir.name,
            "path": module_dir.relative_to(root.parent).as_posix(),
            "file_count": stats["files"],
            "line_count": stats["lines"],
            "files": files,
        })
        total_files += stats["files"]
        total_lines += stats["lines"]
    return {
    "generated_at": datetime.now(UTC).isoformat(),
        "root": root.as_posix(),
        "summary": {
            "module_count": len(modules_data),
            "file_count": total_files,
            "line_count": total_lines,
        },
        "modules": modules_data,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate GUI module snapshot JSON")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="Root directory of GUI modules")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON file path")
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.exists():
        raise SystemExit(f"Root directory not found: {root}")

    snapshot = build_snapshot(root)
    output_path = args.output.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(snapshot, fh, indent=2, ensure_ascii=False)

    print(f"Snapshot written to {output_path}")
    print(json.dumps(snapshot["summary"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
