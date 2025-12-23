#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API-ONLY 模式完整驗證腳本 (2025-10-03 v2)

驗證所有 GUI 模組已完全禁用 CLI 調用，確保系統只通過 API 獲取數據

已修復模組清單 (共 11 個):
1. universal_data_loader_base.py - 基礎數據載入器 + CliAnalysisWorker 類別
2. rain_analysis_mdi.py - 降雨分析
3. track_analysis_mdi.py - 賽道分析  
4. track_data_loader.py - 賽道數據載入器
5. tire_analysis_mdi.py - 輪胎分析
6. lap_box_plot_analysis_mdi.py - 單圈時間箱型圖
7. driverlap_analysis_mdi.py - 車手單圈分析
8. accident_data_manager.py - 事故數據管理
9. pitstop_analysis_mdi.py - 進站分析 (3個方法)
10. laptime_boxplot_widget.py - 單圈時間箱型圖小工具
11. CliAnalysisWorker.run() - QThread 執行方法 (核心禁用)
"""

import os
import re
import sys

# 需要檢查的檔案清單
TARGET_FILES = [
    "modules/gui/base/universal_data_loader_base.py",
    "modules/gui/rain_analysis/rain_analysis_mdi.py",
    "modules/gui/track_analysis/track_analysis_mdi.py",
    "modules/gui/track_analysis/track_data_loader.py",
    "modules/gui/tire_analysis/tire_analysis_mdi.py",
    "modules/gui/driver_race/lap_box_plot/lap_box_plot_analysis_mdi.py",
    "modules/gui/driver_race/detailed_lap_analysis/driverlap_analysis_mdi.py",
    "modules/gui/accident_analysis/accident_data_manager.py",
    "modules/gui/pitstop_analysis/pitstop_analysis_mdi.py",
    "modules/gui/driver_race/detailed_lap_analysis/laptime_boxplot_widget.py",
]

# 禁止的模式 (會啟動 CLI 進程)
FORBIDDEN_PATTERNS = [
    # subprocess 調用 CLI
    (r'subprocess\.Popen\(.*f1_analysis_modular_main', "subprocess.Popen 調用 CLI"),
    (r'subprocess\.run\(.*f1_analysis_modular_main', "subprocess.run 調用 CLI"),
    (r'subprocess\.call\(.*f1_analysis_modular_main', "subprocess.call 調用 CLI"),
    
    # CliAnalysisWorker 實例化 (帶參數)
    (r'CliAnalysisWorker\(\s*\d+', "CliAnalysisWorker 實例化"),
    (r'self\.cli_worker\s*=\s*CliAnalysisWorker\(', "self.cli_worker 賦值"),
    
    # CLI 執行緒啟動
    (r'\.start\(\).*#.*CLI', "CLI 執行緒啟動"),
    (r'threading\.Thread\(.*run_cli', "threading.Thread 調用 CLI"),
]

# 允許的模式 (僅限類別定義和匯入)
ALLOWED_PATTERNS = [
    r'^class\s+CliAnalysisWorker',  # 類別定義
    r'from.*import.*CliAnalysisWorker',  # 匯入語句
    r'def\s+create_cli_worker\(.*\)',  # 工廠方法定義
    r'""".*CliAnalysisWorker.*"""',  # 文檔字串
    r'#.*CliAnalysisWorker',  # 註解
]


def check_file(file_path: str) -> list:
    """
    檢查單個檔案是否包含禁止的 CLI 調用模式
    
    Args:
        file_path: 檔案路徑
        
    Returns:
        list: 發現的違規行 [(行號, 模式描述, 行內容), ...]
    """
    violations = []
    
    if not os.path.exists(file_path):
        print(f"⚠️  檔案不存在: {file_path}")
        return violations
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    for line_num, line in enumerate(lines, start=1):
        # 跳過註解和文檔字串
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('"""') or stripped.startswith("'''"):
            continue
        
        # 檢查是否是允許的模式
        is_allowed = any(re.search(pattern, line) for pattern in ALLOWED_PATTERNS)
        if is_allowed:
            continue
        
        # 檢查禁止的模式
        for pattern, description in FORBIDDEN_PATTERNS:
            if re.search(pattern, line):
                violations.append((line_num, description, line.strip()))
    
    return violations


def main():
    """主驗證流程"""
    print("=" * 80)
    print("🔍 API-ONLY 模式完整性驗證")
    print("=" * 80)
    print()
    
    total_violations = 0
    failed_files = []
    
    for file_path in TARGET_FILES:
        print(f"📄 檢查: {file_path}")
        violations = check_file(file_path)
        
        if violations:
            print(f"   ❌ 發現 {len(violations)} 個違規:")
            for line_num, description, line_content in violations:
                print(f"      Line {line_num}: {description}")
                print(f"         → {line_content}")
            total_violations += len(violations)
            failed_files.append(file_path)
        else:
            print(f"   ✅ 通過驗證")
        print()
    
    # 總結報告
    print("=" * 80)
    if total_violations == 0:
        print("🎉 驗證成功! 所有模組已完全禁用 CLI 調用")
        print(f"✅ 已檢查 {len(TARGET_FILES)} 個檔案")
        print()
        print("📋 已修復模組清單:")
        for idx, file_path in enumerate(TARGET_FILES, start=1):
            module_name = os.path.basename(file_path)
            print(f"   {idx}. {module_name}")
        print()
        print("✅ API-ONLY 模式實施完成 - GUI 只允許通過 API 獲取數據")
        return 0
    else:
        print(f"❌ 驗證失敗! 發現 {total_violations} 個違規")
        print(f"❌ 違規檔案數: {len(failed_files)}")
        print()
        print("🔧 需要修復的檔案:")
        for file_path in failed_files:
            print(f"   - {file_path}")
        print()
        print("⚠️  請禁用所有 CLI 調用，系統只允許通過 API 獲取數據")
        return 1


if __name__ == "__main__":
    sys.exit(main())
