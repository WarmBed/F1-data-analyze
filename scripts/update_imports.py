#!/usr/bin/env python3
"""
導入路徑自動更新工具
====================
自動更新所有 Python 檔案中的 import 路徑

使用方法:
    python scripts/update_imports.py --dry-run   # 預覽變更
    python scripts/update_imports.py             # 執行更新
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple
import argparse

class ImportPathUpdater:
    """導入路徑更新器"""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.updated_files = []
        self.changes_count = 0

        # 導入路徑映射表（舊路徑 -> 新路徑）
        self.import_mappings = self._build_import_mappings()

    def _build_import_mappings(self) -> Dict[str, str]:
        """建立導入路徑映射表"""
        return {
            # ========== 遙測分析模組 ==========
            "modules.gui.lap_analysis.speed_analysis": "modules.gui.telemetry.speed",
            "modules.gui.lap_analysis.brake_analysis": "modules.gui.telemetry.brake",
            "modules.gui.lap_analysis.Throttle_analysis": "modules.gui.telemetry.throttle",
            "modules.gui.lap_analysis.gear_analysis": "modules.gui.telemetry.gear",
            "modules.gui.lap_analysis.rpm_analysis": "modules.gui.telemetry.rpm",
            "modules.gui.lap_analysis.acceleration_analysis": "modules.gui.telemetry.acceleration",
            "modules.gui.lap_analysis.speeddiff_analysis": "modules.gui.telemetry.speed_diff",
            "modules.gui.lap_analysis.distancediff_analysis": "modules.gui.telemetry.distance_diff",
            "modules.gui.lap_analysis.timediff_analysis": "modules.gui.telemetry.time_diff",

            # ========== 油門分析整合 ==========
            "modules.gui.Throttle_analysis.throttle_box_plot_analysis": "modules.gui.telemetry.throttle",
            "modules.gui.Throttle_analysis.throttle_line_chart_analysis": "modules.gui.telemetry.throttle",

            # ========== 全車手分析模組 ==========
            "modules.gui.all_drivers_brake_chart": "modules.gui.all_drivers.brake",
            "modules.gui.all_drivers_brake_performance_analysis": "modules.gui.all_drivers.brake",
            "modules.gui.all_drivers_brake_all_laps_analysis": "modules.gui.all_drivers.brake",
            "modules.gui.all_drivers_acceleration_chart": "modules.gui.all_drivers.acceleration",
            "modules.gui.all_drivers_corner_performance_analysis": "modules.gui.all_drivers.corner_performance",
            "modules.gui.all_drivers_straight_line_speed_analysis": "modules.gui.all_drivers.straight_line_speed",
            "modules.gui.all_drivers_max_speed_analysis": "modules.gui.all_drivers.max_speed",

            # ========== 圈速分析模組 ==========
            "modules.gui.driver_race.lap_box_plot_analysis": "modules.gui.lap_analysis.laptime_boxplot",
            "modules.gui.lap_box_plot_analysis": "modules.gui.lap_analysis.laptime_boxplot",
            "modules.gui.driver_race.detailed_lap_analysis": "modules.gui.lap_analysis.detailed_laptime",
            "modules.gui.ideal_lap_analysis.ideal_lap_ranking_table": "modules.gui.lap_analysis.ideal_lap_ranking",
            "modules.gui.ideal_lap_analysis.ideal_lap_sector_comparison": "modules.gui.lap_analysis.ideal_lap_sector_comparison",
            "modules.gui.ideal_lap_analysis.ideal_lap_sector_heatmap": "modules.gui.lap_analysis.ideal_lap_sector_heatmap",

            # ========== 賽事分析模組 ==========
            "modules.gui.pitstop_analysis": "modules.gui.race_analysis.pitstop",
            "modules.gui.accident_analysis": "modules.gui.race_analysis.accident",
            "modules.gui.weather_timeline": "modules.gui.race_analysis.weather",
            "modules.gui.rain_analysis": "modules.gui.race_analysis.rain_intensity",
            "modules.gui.tire_analysis": "modules.gui.race_analysis.tire_strategy",

            # ========== 賽道分析模組 ==========
            "modules.gui.track_analysis": "modules.gui.track.track_map",
            "modules.gui.Historical_track_map": "modules.gui.track.historical_track_map",

            # ========== 積分榜模組 ==========
            "modules.gui.driver_standings": "modules.gui.standings.driver_standings",
            "modules.gui.constructor_standings": "modules.gui.standings.constructor_standings",
            "modules.gui.season_progress": "modules.gui.standings.season_progress",
            "modules.gui.championship_standings_demo": "modules.gui.standings.championship_summary",

            # ========== 預測系統 ==========
            "modules.gui.qualifying_prediction": "modules.gui.prediction.qualifying",
            "modules.gui.race_prediction": "modules.gui.prediction.race",
            "modules.gui.laptime_prediction_compare": "modules.gui.prediction.laptime",

            # ========== 工具模組 ==========
            "modules.gui.diagnostics": "modules.gui.utilities.diagnostics",
            "modules.gui.partupdated_analysis": "modules.gui.utilities.parts_analysis",
            "modules.gui.themes": "modules.gui.utilities.themes",

            # ========== 共用組件 ==========
            "modules.gui.lap_analysis.linkage": "modules.gui.shared.linkage",
        }

    def update_imports_in_file(self, file_path: Path, dry_run: bool = False) -> Tuple[bool, int]:
        """
        更新單個檔案中的導入路徑

        Returns:
            (是否有變更, 變更數量)
        """
        try:
            content = file_path.read_text(encoding='utf-8')
            original_content = content
            changes = 0

            for old_path, new_path in self.import_mappings.items():
                # 處理 from ... import ...
                pattern1 = rf'from {re.escape(old_path)}'
                replacement1 = f'from {new_path}'
                new_content, count1 = re.subn(pattern1, replacement1, content)
                content = new_content
                changes += count1

                # 處理 import ...
                pattern2 = rf'import {re.escape(old_path)}'
                replacement2 = f'import {new_path}'
                new_content, count2 = re.subn(pattern2, replacement2, content)
                content = new_content
                changes += count2

            if content != original_content:
                if not dry_run:
                    file_path.write_text(content, encoding='utf-8')
                return True, changes

            return False, 0

        except Exception as e:
            print(f"  ❌ 處理失敗 {file_path.relative_to(self.project_root)}: {e}")
            return False, 0

    def find_python_files(self) -> List[Path]:
        """找出所有需要更新的 Python 檔案"""
        python_files = []

        # 掃描 modules/gui
        python_files.extend(self.project_root.glob("modules/gui/**/*.py"))

        # 主程式
        main_file = self.project_root / "f1t_gui_main.py"
        if main_file.exists():
            python_files.append(main_file)

        # 排除 __pycache__
        python_files = [f for f in python_files if "__pycache__" not in str(f)]

        return python_files

    def preview_changes(self):
        """預覽將要進行的變更"""
        python_files = self.find_python_files()

        print("=" * 80)
        print("導入路徑更新預覽")
        print("=" * 80)
        print(f"\n掃描到 {len(python_files)} 個 Python 檔案")

        files_to_update = []
        total_changes = 0

        print("\n分析中...")
        for file_path in python_files:
            changed, count = self.update_imports_in_file(file_path, dry_run=True)
            if changed:
                files_to_update.append((file_path, count))
                total_changes += count

        if files_to_update:
            print(f"\n📋 需要更新的檔案（{len(files_to_update)} 個）：")
            print("-" * 80)
            for file_path, count in sorted(files_to_update):
                rel_path = file_path.relative_to(self.project_root)
                print(f"  🔄 {rel_path} ({count} 處變更)")

            print("\n" + "=" * 80)
            print(f"總計：{len(files_to_update)} 個檔案，{total_changes} 處變更")
            print("=" * 80)
        else:
            print("\n✅ 沒有需要更新的檔案！")

        return len(files_to_update) > 0

    def execute_update(self, dry_run: bool = False):
        """執行導入路徑更新"""
        python_files = self.find_python_files()

        if dry_run:
            print("\n🔍 模擬模式（不會實際更新）")
            return self.preview_changes()

        print("\n🚀 開始更新導入路徑...")

        for i, file_path in enumerate(python_files, 1):
            changed, count = self.update_imports_in_file(file_path, dry_run=False)

            if changed:
                self.updated_files.append(file_path)
                self.changes_count += count
                rel_path = file_path.relative_to(self.project_root)
                print(f"  ✅ [{i}/{len(python_files)}] {rel_path} ({count} 處變更)")

        print("\n" + "=" * 80)
        print(f"✅ 更新完成!")
        print(f"  已更新檔案: {len(self.updated_files)} 個")
        print(f"  總變更數: {self.changes_count} 處")
        print("=" * 80)

    def generate_report(self):
        """生成更新報告"""
        report_path = self.project_root / "import_update_report.txt"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("導入路徑更新報告\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"已更新檔案（{len(self.updated_files)} 個）：\n")
            f.write("-" * 80 + "\n")
            for file in sorted(self.updated_files):
                f.write(f"{file.relative_to(self.project_root)}\n")

            f.write(f"\n總變更數：{self.changes_count} 處\n")

            f.write("\n導入路徑映射表：\n")
            f.write("-" * 80 + "\n")
            for old_path, new_path in sorted(self.import_mappings.items()):
                f.write(f"{old_path}\n  → {new_path}\n\n")

        print(f"\n📝 更新報告已儲存: {report_path}")


def main():
    """主程式"""
    parser = argparse.ArgumentParser(description="導入路徑自動更新工具")
    parser.add_argument("--dry-run", action="store_true", help="模擬模式，不實際更新")
    parser.add_argument("--yes", "-y", action="store_true", help="跳過確認，直接執行")
    args = parser.parse_args()

    # 獲取專案根目錄
    project_root = Path(__file__).parent.parent

    updater = ImportPathUpdater(project_root)

    # 顯示預覽
    has_changes = updater.preview_changes()

    if not has_changes:
        print("\n✅ 沒有需要更新的導入路徑!")
        return 0

    # 確認執行
    if not args.yes and not args.dry_run:
        print("\n⚠️  警告：這個操作會修改檔案（建議先用 Git 提交目前變更）")
        response = input("確定要執行更新嗎？(yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("❌ 已取消")
            return 1

    # 執行更新
    updater.execute_update(dry_run=args.dry_run)

    # 生成報告
    if not args.dry_run:
        updater.generate_report()

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
