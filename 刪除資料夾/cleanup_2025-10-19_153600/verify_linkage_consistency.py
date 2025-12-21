#!/usr/bin/env python3
"""
連動系統一致性驗證腳本
Linkage System Consistency Verification Script

驗證所有 Lap Analysis 模組的連動系統是否與 Speed Analysis 一致

執行方式:
    python verify_linkage_consistency.py

預期輸出:
    ✅ 所有模組的連動系統實現一致
    ❌ 發現不一致的實現（顯示詳細差異）
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

# 需要檢查的模組列表
MODULES_TO_CHECK = [
    "speed_analysis",
    "brake_analysis",
    "acceleration_analysis",
    "rpm_analysis",
    "gear_analysis",
]

# 檔案路徑模板
FILE_TEMPLATE = "modules/gui/lap_analysis/{module}/{module}_chart_widget.py"

# 檢查項目
CHECKS = {
    "update_callback": r"self\.update_callback\s*=\s*self\.update",
    "register_module": r"linkage_manager\.register_module\(self,",
    "sync_master_state": r"current_master_state\s*=\s*linkage_manager\.is_master_linkage_enabled\(\)",
    "set_master_linkage": r"self\.set_master_linkage_enabled\(current_master_state\)",
    "cleanup_unregister": r"linkage_manager\.unregister_module\(self\)",
}


def check_file(file_path: Path, module_name: str) -> Dict[str, bool]:
    """檢查單個檔案的連動系統實現"""
    results = {}
    
    if not file_path.exists():
        print(f"❌ 檔案不存在: {file_path}")
        return {check: False for check in CHECKS}
    
    content = file_path.read_text(encoding="utf-8")
    
    for check_name, pattern in CHECKS.items():
        found = bool(re.search(pattern, content))
        results[check_name] = found
    
    return results


def print_results(results: Dict[str, Dict[str, bool]]):
    """印出檢查結果"""
    print("\n" + "="*80)
    print("🔍 連動系統一致性檢查結果")
    print("="*80 + "\n")
    
    # 檢查項目說明
    check_descriptions = {
        "update_callback": "設置更新回調 (update_callback)",
        "register_module": "主動註冊到連動管理器",
        "sync_master_state": "同步主開關狀態",
        "set_master_linkage": "設置主連動開關",
        "cleanup_unregister": "cleanup() 解除註冊",
    }
    
    # 統計
    total_checks = len(CHECKS) * len(MODULES_TO_CHECK)
    passed_checks = 0
    
    # 逐模組顯示結果
    for module, checks in results.items():
        print(f"📊 {module.upper()}")
        print("-" * 80)
        
        module_passed = True
        for check_name, passed in checks.items():
            status = "✅" if passed else "❌"
            description = check_descriptions.get(check_name, check_name)
            print(f"  {status} {description}")
            if passed:
                passed_checks += 1
            else:
                module_passed = False
        
        if module_passed:
            print(f"  🎉 {module} 模組檢查通過！\n")
        else:
            print(f"  ⚠️ {module} 模組存在問題，需要修復\n")
    
    # 總結
    print("="*80)
    print(f"📈 總結: {passed_checks}/{total_checks} 項檢查通過")
    print("="*80 + "\n")
    
    if passed_checks == total_checks:
        print("🎉 所有模組的連動系統實現完全一致！")
        return True
    else:
        print("⚠️ 部分模組的連動系統實現不一致，請參考上方詳細結果")
        return False


def main():
    """主函數"""
    print("🚀 開始檢查連動系統一致性...\n")
    
    results = {}
    
    for module in MODULES_TO_CHECK:
        file_path = Path(FILE_TEMPLATE.format(module=module))
        print(f"🔍 檢查 {module}...")
        results[module] = check_file(file_path, module)
    
    all_passed = print_results(results)
    
    if all_passed:
        print("\n✅ 驗證完成：所有模組符合標準！")
        exit(0)
    else:
        print("\n❌ 驗證失敗：存在不一致的實現")
        exit(1)


if __name__ == "__main__":
    main()
