#!/usr/bin/env python3
"""
診斷為什麼只有 Brake 彈出警告

檢查三個關鍵點：
1. Brake 的 JSON 是否存在
2. Speed 的 JSON 是否存在
3. 兩者的檔案搜索模式差異
"""

import os
import glob
from pathlib import Path

def check_json_files():
    """檢查 JSON 檔案是否存在"""
    print("="*80)
    print("📂 檢查 JSON 檔案存在性")
    print("="*80)
    
    # 測試參數
    test_params = {
        "year": "2025",
        "race": "Singapore",
        "session": "R"
    }
    
    # Brake 的檔案模式
    brake_patterns = [
        f"all_drivers_brake_performance_2025_Singapore_R.json",
        f"all_drivers_brake_performance_2025_Singapore_R.json",
        f"all_drivers_brake_performance_*_Singapore_R.json",
        f"all_drivers_brake_performance_*_Singapore_R.json",
        f"brake_performance_2025_Singapore_R.json",
        f"brake_performance_2025_Singapore_R.json",
    ]
    
    # Speed 的檔案模式
    speed_patterns = [
        f"all_drivers_straight_line_speed_2025_Singapore_R.json",
        f"all_drivers_straight_line_speed_2025_Singapore_R.json",
        f"all_drivers_straight_line_speed_*_Singapore_R.json",
        f"all_drivers_straight_line_speed_*_Singapore_R.json",
        f"straight_line_speed_2025_Singapore_R.json",
        f"straight_line_speed_2025_Singapore_R.json",
    ]
    
    # 搜索目錄
    search_dirs = ["json", "cache", "f1_analysis_cache"]
    
    print(f"\n🧪 測試參數: {test_params}")
    print(f"\n📁 搜索目錄: {search_dirs}")
    
    # 檢查 Brake 檔案
    print(f"\n{'='*40}")
    print("🔴 Brake Performance 檔案")
    print(f"{'='*40}")
    
    brake_found = []
    for directory in search_dirs:
        if not os.path.exists(directory):
            print(f"  ❌ 目錄不存在: {directory}")
            continue
        
        print(f"\n  📂 搜索: {directory}/")
        for pattern in brake_patterns:
            full_pattern = os.path.join(directory, pattern)
            matches = glob.glob(full_pattern)
            if matches:
                for match in matches:
                    size = os.path.getsize(match)
                    brake_found.append(match)
                    print(f"    ✅ {match} ({size} bytes)")
            # else:
            #     print(f"    ❌ 無匹配: {pattern}")
    
    if not brake_found:
        print(f"\n  ⚠️  找不到任何 Brake Performance JSON 檔案")
        print(f"  💡 這會觸發 API 調用 → 可能失敗 → 彈出警告")
    
    # 檢查 Speed 檔案
    print(f"\n{'='*40}")
    print("🔵 Speed Analysis 檔案")
    print(f"{'='*40}")
    
    speed_found = []
    for directory in search_dirs:
        if not os.path.exists(directory):
            continue
        
        print(f"\n  📂 搜索: {directory}/")
        for pattern in speed_patterns:
            full_pattern = os.path.join(directory, pattern)
            matches = glob.glob(full_pattern)
            if matches:
                for match in matches:
                    size = os.path.getsize(match)
                    speed_found.append(match)
                    print(f"    ✅ {match} ({size} bytes)")
    
    if not speed_found:
        print(f"\n  ⚠️  找不到任何 Speed Analysis JSON 檔案")
        print(f"  💡 這會觸發 API 調用 → 可能失敗 → 應該也彈出警告")
    
    # 總結
    print(f"\n{'='*80}")
    print("📊 總結")
    print(f"{'='*80}")
    
    print(f"\n🔴 Brake Performance:")
    print(f"  找到 {len(brake_found)} 個檔案")
    if brake_found:
        print(f"  狀態: ✅ 有本地檔案 → 不應該呼叫 API")
    else:
        print(f"  狀態: ⚠️ 無本地檔案 → 會呼叫 API → 可能觸發警告")
    
    print(f"\n🔵 Speed Analysis:")
    print(f"  找到 {len(speed_found)} 個檔案")
    if speed_found:
        print(f"  狀態: ✅ 有本地檔案 → 不會呼叫 API → 不會彈警告")
    else:
        print(f"  狀態: ⚠️ 無本地檔案 → 會呼叫 API → 應該也彈警告")
    
    # 結論
    print(f"\n{'='*80}")
    print("🎯 結論")
    print(f"{'='*80}")
    
    if brake_found and not speed_found:
        print("\n❌ 矛盾！Brake 有檔案但還是彈警告？")
        print("   可能原因：")
        print("   1. 檔案格式錯誤或損壞")
        print("   2. 檔案搜索模式不匹配")
        print("   3. 檔案驗證失敗")
    elif not brake_found and speed_found:
        print("\n✅ 合理！Brake 無檔案觸發 API → 失敗 → 彈警告")
        print("          Speed 有檔案不觸發 API → 不彈警告")
    elif not brake_found and not speed_found:
        print("\n⚠️  兩者都沒檔案，但只有 Brake 彈警告？")
        print("   可能原因：")
        print("   1. Speed 在你打開前已被其他操作生成")
        print("   2. API 對 Speed 的響應更快/成功率更高")
        print("   3. Speed 的錯誤處理邏輯不同")
    else:
        print("\n✅ 兩者都有檔案，不應該彈警告")
        print("   如果還是彈了，可能是：")
        print("   1. 檔案驗證邏輯有問題")
        print("   2. 其他錯誤觸發了警告")

if __name__ == "__main__":
    check_json_files()
