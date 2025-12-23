#!/usr/bin/env python3
"""
測試車隊資訊修復
Test Team Information Fix

驗證 CLI 後端是否正確輸出車隊資訊

作者: F1T Team
日期: 2025-10-28
"""

import sys
import json
import os


def test_cli_team_output():
    """測試 CLI 後端是否輸出車隊資訊"""
    print("=" * 60)
    print("階段 1: 檢查現有 JSON 檔案的車隊資訊")
    print("=" * 60)
    
    # 檢查緩存目錄中的 JSON 檔案
    json_dir = "json"
    if not os.path.exists(json_dir):
        print(f"[SKIP] 目錄不存在: {json_dir}")
        return False
    
    # 尋找 driver_race_position JSON 檔案
    found_files = []
    for filename in os.listdir(json_dir):
        if "driver_race_position" in filename and filename.endswith(".json"):
            found_files.append(filename)
    
    if not found_files:
        print("[INFO] 尚未找到任何 driver_race_position JSON 檔案")
        print("[INFO] 請先執行 CLI 命令生成數據:")
        print("       python f1_analysis_modular_main.py -f 25 -y 2024 -r Japan -s R")
        return False
    
    print(f"[OK] 找到 {len(found_files)} 個 JSON 檔案")
    
    # 檢查第一個檔案
    test_file = os.path.join(json_dir, found_files[0])
    print(f"\n檢查檔案: {test_file}")
    
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 檢查數據結構
        if "all_drivers_position_analysis" not in data:
            print("[FAIL] 缺少 'all_drivers_position_analysis' 鍵")
            return False
        
        all_drivers = data["all_drivers_position_analysis"]
        print(f"[OK] 包含 {len(all_drivers)} 位車手數據")
        
        # 檢查前 3 位車手的車隊資訊
        print("\n車隊資訊檢查:")
        has_team_info = True
        for i, (driver, driver_data) in enumerate(list(all_drivers.items())[:3], 1):
            team = driver_data.get("team", "NOT_FOUND")
            if team == "NOT_FOUND":
                print(f"  {i}. {driver}: [FAIL] 缺少 'team' 欄位")
                has_team_info = False
            elif team == "Unknown":
                print(f"  {i}. {driver}: [WARN] 車隊為 'Unknown'（可能需要重新生成數據）")
            else:
                print(f"  {i}. {driver}: [OK] {team}")
        
        if has_team_info:
            print("\n[SUCCESS] 所有車手都包含 'team' 欄位")
            return True
        else:
            print("\n[FAIL] 部分車手缺少 'team' 欄位")
            return False
            
    except Exception as e:
        print(f"[FAIL] 讀取檔案失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cli_modification():
    """驗證 CLI 後端代碼修改"""
    print("\n" + "=" * 60)
    print("階段 2: 驗證 CLI 後端代碼修改")
    print("=" * 60)
    
    cli_file = "CLI_modules/cli/analyzer/single_driver_position_analysis.py"
    
    if not os.path.exists(cli_file):
        print(f"[FAIL] 找不到檔案: {cli_file}")
        return False
    
    try:
        with open(cli_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查關鍵修改
        checks = [
            ('results_data', '是否獲取 results_data'),
            ('"team":', '是否添加 team 欄位'),
            ("driver_result = results_data[results_data['Abbreviation'] == drv]", '是否從 results 提取車隊'),
            ("team_name = driver_result.iloc[0]['TeamName']", '是否讀取 TeamName'),
        ]
        
        all_passed = True
        for check_str, description in checks:
            if check_str in content:
                print(f"[OK] {description}")
            else:
                print(f"[FAIL] {description}")
                all_passed = False
        
        if all_passed:
            print("\n[SUCCESS] CLI 後端代碼修改正確")
            return True
        else:
            print("\n[FAIL] CLI 後端代碼修改不完整")
            return False
            
    except Exception as e:
        print(f"[FAIL] 讀取檔案失敗: {e}")
        return False


def main():
    """主測試流程"""
    print("\n[TEST] 開始測試車隊資訊修復")
    print("=" * 60)
    
    results = []
    
    # 階段 1: 檢查現有 JSON
    success = test_cli_team_output()
    results.append(("JSON 車隊資訊", success))
    
    # 階段 2: 驗證代碼修改
    success = test_cli_modification()
    results.append(("CLI 代碼修改", success))
    
    # 總結
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "[OK] 通過" if passed else "[FAIL] 失敗"
        print(f"{status} - {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n[SUCCESS] 所有測試通過！")
        print("\n[INFO] 下一步:")
        print("  1. 刪除舊的 JSON 檔案（如果車隊為 'Unknown'）")
        print("  2. 重新執行 CLI 命令生成新數據:")
        print("     python f1_analysis_modular_main.py -f 25 -y 2024 -r Japan -s R")
        print("  3. 重啟 GUI 測試車隊顯示")
        return True
    else:
        print("\n[WARNING] 部分測試失敗")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
