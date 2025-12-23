#!/usr/bin/env python3
"""
JSON 檔案自動分類遷移工具
===========================

自動將 json/ 目錄中的 280+ 個檔案分類到對應子目錄。

功能:
- 自動識別檔案類型
- 移動到對應子目錄
- 生成詳細遷移報告
- 支援 dry-run 安全預覽
- 自動備份原始檔案

使用方式:
    # Dry-run 模式 (安全預覽)
    python tools/migrate_json_files.py --dry-run
    
    # 正式執行遷移
    python tools/migrate_json_files.py
    
    # 自動備份後執行
    python tools/migrate_json_files.py --backup

Author: F1T Development Team
Date: 2025-10-10
Version: 1.0.0
"""

import os
import sys
import shutil
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple
from collections import Counter

# 添加項目根目錄到 Python 路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 導入配置模組
from CLI_modules.cli.core.json_output_config import (
    get_analysis_type_from_filename,
    get_subdirectory_for_type,
    get_base_json_directory
)

# ========== 配置 ==========

JSON_DIR = get_base_json_directory()
BACKUP_DIR = Path("json_backup")
REPORT_DIR = Path("logs")

# ========== 核心功能 ==========

def scan_json_files() -> List[Path]:
    """
    掃描 json/ 目錄中的所有 JSON 檔案
    
    Returns:
        List[Path]: JSON 檔案路徑列表
    """
    json_files = []
    
    # 只掃描根目錄的 JSON 檔案 (不包含已分類的子目錄)
    for file in JSON_DIR.iterdir():
        if file.is_file() and file.suffix == ".json":
            json_files.append(file)
    
    return sorted(json_files)


def classify_file(file_path: Path) -> Tuple[str, str]:
    """
    分類單個檔案
    
    Args:
        file_path: 檔案路徑
        
    Returns:
        Tuple[str, str]: (分析類型, 目標子目錄)
    """
    filename = file_path.name
    analysis_type = get_analysis_type_from_filename(filename)
    subdirectory = get_subdirectory_for_type(analysis_type)
    
    return analysis_type, subdirectory


def create_migration_plan(files: List[Path]) -> Dict[str, List[Path]]:
    """
    創建遷移計畫
    
    Args:
        files: 要遷移的檔案列表
        
    Returns:
        Dict[str, List[Path]]: {子目錄: [檔案列表]} 映射
    """
    plan = {}
    
    for file in files:
        _, subdirectory = classify_file(file)
        
        if subdirectory not in plan:
            plan[subdirectory] = []
        
        plan[subdirectory].append(file)
    
    return plan


def backup_files(files: List[Path]) -> bool:
    """
    備份檔案到 json_backup/ 目錄
    
    Args:
        files: 要備份的檔案列表
        
    Returns:
        bool: 備份是否成功
    """
    try:
        # 創建帶時間戳的備份目錄
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"backup_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)
        
        print(f"\n📦 備份檔案到: {backup_path}")
        
        for file in files:
            dest = backup_path / file.name
            shutil.copy2(file, dest)
        
        print(f"✅ 成功備份 {len(files)} 個檔案")
        return True
        
    except Exception as e:
        print(f"❌ 備份失敗: {e}")
        return False


def migrate_files(migration_plan: Dict[str, List[Path]], dry_run: bool = False) -> Dict[str, int]:
    """
    執行檔案遷移
    
    Args:
        migration_plan: 遷移計畫
        dry_run: 是否為預覽模式 (不實際移動檔案)
        
    Returns:
        Dict[str, int]: 統計資訊 {子目錄: 檔案數量}
    """
    stats = {}
    
    print("\n" + "=" * 80)
    if dry_run:
        print("🔍 DRY-RUN 模式 - 預覽遷移計畫 (不會實際移動檔案)")
    else:
        print("🚀 執行檔案遷移")
    print("=" * 80)
    
    for subdirectory, files in sorted(migration_plan.items()):
        target_dir = JSON_DIR / subdirectory
        
        print(f"\n📁 目標目錄: {subdirectory}/ ({len(files)} 個檔案)")
        
        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)
        
        for i, file in enumerate(files, 1):
            source = file
            dest = target_dir / file.name
            
            # 顯示進度 (每10個檔案顯示一次，避免輸出過多)
            if i <= 5 or i % 10 == 0 or i == len(files):
                print(f"  [{i:3d}/{len(files)}] {file.name}")
                if not dry_run:
                    print(f"           → {subdirectory}/{file.name}")
            
            # 實際移動檔案
            if not dry_run:
                try:
                    shutil.move(str(source), str(dest))
                except Exception as e:
                    print(f"  ⚠️ 移動失敗: {e}")
        
        stats[subdirectory] = len(files)
        
        if len(files) > 5:
            print(f"  ... (已省略 {len(files) - 5} 個檔案名稱)")
    
    return stats


def generate_report(stats: Dict[str, int], total_files: int, dry_run: bool = False):
    """
    生成遷移報告
    
    Args:
        stats: 統計資訊
        total_files: 總檔案數
        dry_run: 是否為預覽模式
    """
    print("\n" + "=" * 80)
    print("📊 遷移統計報告")
    print("=" * 80)
    
    print(f"\n總檔案數: {total_files}")
    print(f"目標目錄數: {len(stats)}")
    
    print("\n目錄分佈:")
    for subdirectory, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_files * 100) if total_files > 0 else 0
        bar = "█" * int(percentage / 2)
        print(f"  {subdirectory:20s} {count:3d} 檔案 ({percentage:5.1f}%) {bar}")
    
    # 保存報告到檔案
    if not dry_run:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = REPORT_DIR / f"json_migration_report_{timestamp}.json"
        
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "total_files": total_files,
            "target_directories": len(stats),
            "distribution": stats,
            "mode": "dry_run" if dry_run else "actual"
        }
        
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 詳細報告已保存: {report_file}")


def show_summary(files: List[Path]):
    """
    顯示檔案摘要
    
    Args:
        files: 檔案列表
    """
    print("\n" + "=" * 80)
    print("📋 檔案摘要")
    print("=" * 80)
    
    # 統計分析類型
    types = [get_analysis_type_from_filename(f.name) for f in files]
    type_counts = Counter(types)
    
    print(f"\n發現的檔案類型 (Top 10):")
    for analysis_type, count in type_counts.most_common(10):
        subdirectory = get_subdirectory_for_type(analysis_type)
        print(f"  {analysis_type:40s} → {subdirectory:20s} ({count:3d} 檔案)")
    
    if len(type_counts) > 10:
        print(f"  ... (還有 {len(type_counts) - 10} 種類型)")


# ========== 主程式 ==========

def main():
    """主函數"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="JSON 檔案自動分類遷移工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
範例:
  # Dry-run 模式 (安全預覽)
  python tools/migrate_json_files.py --dry-run
  
  # 正式執行遷移
  python tools/migrate_json_files.py
  
  # 自動備份後執行
  python tools/migrate_json_files.py --backup
        """
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="預覽模式 (不實際移動檔案)"
    )
    
    parser.add_argument(
        "--backup",
        action="store_true",
        help="執行遷移前自動備份所有檔案"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="強制執行 (跳過確認)"
    )
    
    args = parser.parse_args()
    
    # 標題
    print("=" * 80)
    print("🗂️  JSON 檔案自動分類遷移工具")
    print("=" * 80)
    print(f"日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"模式: {'DRY-RUN (預覽)' if args.dry_run else '正式執行'}")
    
    # 掃描檔案
    print(f"\n🔍 掃描 {JSON_DIR}/ 目錄...")
    files = scan_json_files()
    print(f"✅ 發現 {len(files)} 個 JSON 檔案")
    
    if len(files) == 0:
        print("\n⚠️ 沒有需要遷移的檔案")
        return
    
    # 顯示摘要
    show_summary(files)
    
    # 創建遷移計畫
    print(f"\n📋 創建遷移計畫...")
    migration_plan = create_migration_plan(files)
    
    # 顯示計畫
    print(f"✅ 計畫完成 - 將分類到 {len(migration_plan)} 個子目錄")
    
    # 備份 (如果需要)
    if args.backup and not args.dry_run:
        if not backup_files(files):
            print("\n❌ 備份失敗，取消遷移")
            return
    
    # 用戶確認 (除非 --force)
    if not args.dry_run and not args.force:
        print("\n" + "=" * 80)
        print("⚠️  警告: 即將移動 {} 個檔案".format(len(files)))
        print("=" * 80)
        response = input("\n確定要執行遷移嗎? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("❌ 用戶取消遷移")
            return
    
    # 執行遷移
    stats = migrate_files(migration_plan, dry_run=args.dry_run)
    
    # 生成報告
    generate_report(stats, len(files), dry_run=args.dry_run)
    
    # 完成
    print("\n" + "=" * 80)
    if args.dry_run:
        print("✅ DRY-RUN 完成 - 沒有實際移動檔案")
        print("💡 提示: 移除 --dry-run 參數以執行實際遷移")
    else:
        print("✅ 遷移完成!")
        print(f"📁 檔案已分類到 {JSON_DIR}/ 的子目錄中")
    print("=" * 80)


if __name__ == "__main__":
    main()
