#!/usr/bin/env python3
"""
F1T GUI 模組清理腳本
=====================
安全刪除備份檔案、舊版本檔案和緩存目錄

執行前會顯示將要刪除的檔案清單，需要確認後才執行
"""

import os
import shutil
from pathlib import Path
from typing import List, Tuple

class GUIModuleCleaner:
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.gui_modules_path = project_root / "modules" / "gui"
        self.deleted_files = []
        self.deleted_dirs = []

    def find_backup_files(self) -> List[Path]:
        """找出所有備份檔案"""
        backup_patterns = [
            "*.backup",
            "*.backup_indent",
            "*.backup_telemetry_method",
            "*-XM*.py",
        ]

        backup_files = []
        for pattern in backup_patterns:
            backup_files.extend(self.gui_modules_path.rglob(pattern))

        return backup_files

    def find_old_version_files(self) -> List[Path]:
        """找出所有舊版本檔案"""
        old_files = [
            # ideal_lap_sector_heatmap
            self.gui_modules_path / "ideal_lap_analysis" / "ideal_lap_sector_heatmap" / "ideal_lap_sector_heatmap_widget_old.py",

            # ideal_lap_sector_comparison
            self.gui_modules_path / "ideal_lap_analysis" / "ideal_lap_sector_comparison" / "ideal_lap_sector_comparison_widget_OLD.py",
            self.gui_modules_path / "ideal_lap_analysis" / "ideal_lap_sector_comparison" / "ideal_lap_sector_comparison_widget_V1_OLD.py",
            self.gui_modules_path / "ideal_lap_analysis" / "ideal_lap_sector_comparison" / "ideal_lap_sector_comparison_widget_V2_COMPACT.py",
            self.gui_modules_path / "ideal_lap_analysis" / "ideal_lap_sector_comparison" / "ideal_lap_sector_comparison_widget_NEW.py",

            # live_timing
            self.gui_modules_path / "live_timing" / "live_timing_modules" / "gear_trace_old.py",
            self.gui_modules_path / "live_timing" / "live_timing_modules" / "drs_trace_old.py",
            self.gui_modules_path / "live_timing" / "live_timing_modules" / "rpm_trace_old.py",

            # corner_performance
            self.gui_modules_path / "all_drivers_corner_performance_analysis" / "corner_performance_scatter_widget_backup.py",
        ]

        return [f for f in old_files if f.exists()]

    def find_pycache_dirs(self) -> List[Path]:
        """找出所有 __pycache__ 目錄"""
        return list(self.gui_modules_path.rglob("__pycache__"))

    def preview_cleanup(self) -> Tuple[List[Path], List[Path], List[Path]]:
        """預覽將要刪除的檔案"""
        backup_files = self.find_backup_files()
        old_files = self.find_old_version_files()
        pycache_dirs = self.find_pycache_dirs()

        return backup_files, old_files, pycache_dirs

    def print_preview(self):
        """顯示清理預覽"""
        backup_files, old_files, pycache_dirs = self.preview_cleanup()

        print("=" * 80)
        print("F1T GUI 模組清理預覽")
        print("=" * 80)

        print(f"\n📋 將要刪除的備份檔案（{len(backup_files)} 個）：")
        print("-" * 80)
        for f in sorted(backup_files):
            rel_path = f.relative_to(self.project_root)
            print(f"  ❌ {rel_path}")

        print(f"\n📋 將要刪除的舊版本檔案（{len(old_files)} 個）：")
        print("-" * 80)
        for f in sorted(old_files):
            rel_path = f.relative_to(self.project_root)
            print(f"  ❌ {rel_path}")

        print(f"\n📋 將要刪除的 __pycache__ 目錄（{len(pycache_dirs)} 個）：")
        print("-" * 80)
        # 只顯示前10個，避免輸出過長
        for d in sorted(pycache_dirs)[:10]:
            rel_path = d.relative_to(self.project_root)
            print(f"  🗑️  {rel_path}")
        if len(pycache_dirs) > 10:
            print(f"  ... 還有 {len(pycache_dirs) - 10} 個")

        print("\n" + "=" * 80)
        print(f"總計：{len(backup_files) + len(old_files)} 個檔案，{len(pycache_dirs)} 個目錄")
        print("=" * 80)

        return len(backup_files) + len(old_files) + len(pycache_dirs) > 0

    def execute_cleanup(self, dry_run: bool = False):
        """執行清理"""
        backup_files, old_files, pycache_dirs = self.preview_cleanup()

        if dry_run:
            print("\n🔍 模擬模式（不會實際刪除）")
            return

        print("\n🚀 開始清理...")

        # 刪除備份檔案
        print(f"\n刪除備份檔案...")
        for f in backup_files:
            try:
                f.unlink()
                self.deleted_files.append(f)
                print(f"  ✅ 已刪除: {f.relative_to(self.project_root)}")
            except Exception as e:
                print(f"  ❌ 刪除失敗: {f.relative_to(self.project_root)} - {e}")

        # 刪除舊版本檔案
        print(f"\n刪除舊版本檔案...")
        for f in old_files:
            try:
                f.unlink()
                self.deleted_files.append(f)
                print(f"  ✅ 已刪除: {f.relative_to(self.project_root)}")
            except Exception as e:
                print(f"  ❌ 刪除失敗: {f.relative_to(self.project_root)} - {e}")

        # 刪除 __pycache__ 目錄
        print(f"\n刪除 __pycache__ 目錄...")
        for d in pycache_dirs:
            try:
                shutil.rmtree(d)
                self.deleted_dirs.append(d)
                # 只顯示每5個
                if len(self.deleted_dirs) % 5 == 0:
                    print(f"  ✅ 已刪除 {len(self.deleted_dirs)} 個緩存目錄...")
            except Exception as e:
                print(f"  ❌ 刪除失敗: {d.relative_to(self.project_root)} - {e}")

        print(f"\n" + "=" * 80)
        print(f"✅ 清理完成!")
        print(f"  已刪除檔案: {len(self.deleted_files)} 個")
        print(f"  已刪除目錄: {len(self.deleted_dirs)} 個")
        print("=" * 80)

    def generate_report(self):
        """生成清理報告"""
        report_path = self.project_root / "cleanup_report.txt"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("F1T GUI 模組清理報告\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"已刪除檔案（{len(self.deleted_files)} 個）：\n")
            f.write("-" * 80 + "\n")
            for file in sorted(self.deleted_files):
                f.write(f"{file.relative_to(self.project_root)}\n")

            f.write(f"\n已刪除目錄（{len(self.deleted_dirs)} 個）：\n")
            f.write("-" * 80 + "\n")
            for dir in sorted(self.deleted_dirs):
                f.write(f"{dir.relative_to(self.project_root)}\n")

        print(f"\n📝 清理報告已儲存: {report_path}")


def main():
    """主程式"""
    import argparse

    parser = argparse.ArgumentParser(description="F1T GUI 模組清理工具")
    parser.add_argument("--dry-run", action="store_true", help="模擬模式，不實際刪除")
    parser.add_argument("--yes", "-y", action="store_true", help="跳過確認，直接執行")
    args = parser.parse_args()

    # 獲取專案根目錄
    project_root = Path(__file__).parent.parent

    cleaner = GUIModuleCleaner(project_root)

    # 顯示預覽
    has_files = cleaner.print_preview()

    if not has_files:
        print("\n✅ 沒有需要清理的檔案!")
        return 0

    # 確認執行
    if not args.yes and not args.dry_run:
        print("\n⚠️  警告：這個操作無法撤銷（但 Git 可以恢復）")
        response = input("確定要執行清理嗎？(yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("❌ 已取消")
            return 1

    # 執行清理
    cleaner.execute_cleanup(dry_run=args.dry_run)

    # 生成報告
    if not args.dry_run:
        cleaner.generate_report()

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
