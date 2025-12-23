#!/usr/bin/env python3
"""
完整模擬 Brake Performance Loader 的數據驗證流程

模擬 _validate_data_format 的實際執行
"""

import json
import os
from typing import Any

def brake_validate_data_format(raw_data: Any) -> bool:
    """完全複製 brake_performance_loader.py 的 _validate_data_format"""
    print("\n🔍 開始驗證數據格式...")
    print(f"  Step 1: 檢查 raw_data 是否為 dict")
    if not isinstance(raw_data, dict):
        print(f"    ❌ 失敗: raw_data 不是 dict，是 {type(raw_data)}")
        return False
    print(f"    ✅ 通過")
    
    print(f"  Step 2: 檢查 success 欄位")
    success = raw_data.get("success", False)
    if not success:
        print(f"    ❌ 失敗: success={success}")
        return False
    print(f"    ✅ 通過: success={success}")

    print(f"  Step 3: 檢查第一層 data")
    first_layer = raw_data.get("data")
    if not isinstance(first_layer, dict):
        print(f"    ❌ 失敗: first_layer 不是 dict，是 {type(first_layer)}")
        return False
    print(f"    ✅ 通過: first_layer 是 dict")
    
    print(f"  Step 4: 檢查是否有第二層 data (API 嵌套)")
    if "data" in first_layer:
        payload = first_layer.get("data")
        print(f"    ℹ️  發現第二層嵌套，使用 first_layer['data']")
    else:
        payload = first_layer
        print(f"    ℹ️  無第二層嵌套，直接使用 first_layer")
    
    print(f"  Step 5: 檢查 payload 是否為 dict")
    if not isinstance(payload, dict):
        print(f"    ❌ 失敗: payload 不是 dict，是 {type(payload)}")
        return False
    print(f"    ✅ 通過: payload 是 dict")
    print(f"    Keys: {list(payload.keys())}")

    print(f"  Step 6: 檢查 driver_brakes 欄位")
    driver_brakes = payload.get("driver_brakes")
    if not isinstance(driver_brakes, list):
        print(f"    ❌ 失敗: driver_brakes 不是 list")
        print(f"       實際類型: {type(driver_brakes)}")
        print(f"       實際值: {driver_brakes}")
        print(f"\n    🔍 可用的 keys: {list(payload.keys())}")
        return False
    print(f"    ✅ 通過: driver_brakes 是 list，長度={len(driver_brakes)}")

    print(f"\n✅ 所有驗證通過！")
    return True

def speed_validate_data_format(raw_data: Any) -> bool:
    """完全複製 straight_line_speed_loader.py 的 _validate_data_format"""
    print("\n🔍 開始驗證數據格式 (Speed)...")
    print(f"  Step 1: 檢查 raw_data 是否為 dict")
    if not isinstance(raw_data, dict):
        print(f"    ❌ 失敗: raw_data 不是 dict")
        return False
    print(f"    ✅ 通過")
    
    print(f"  Step 2: 檢查 success 欄位")
    success = raw_data.get("success", False)
    if not success:
        print(f"    ❌ 失敗: success={success}")
        return False
    print(f"    ✅ 通過: success={success}")

    print(f"  Step 3: 檢查第一層 data")
    first_layer = raw_data.get("data")
    if not isinstance(first_layer, dict):
        print(f"    ❌ 失敗: first_layer 不是 dict")
        return False
    print(f"    ✅ 通過")
    
    print(f"  Step 4: 檢查payload")
    if "data" in first_layer:
        payload = first_layer.get("data")
        print(f"    ℹ️  使用第二層 data")
    else:
        payload = first_layer
        print(f"    ℹ️  使用第一層 data")
    
    if not isinstance(payload, dict):
        print(f"    ❌ 失敗: payload 不是 dict")
        return False
    print(f"    ✅ 通過")
    print(f"    Keys: {list(payload.keys())}")

    print(f"  Step 5: 檢查 driver_speeds 欄位")
    driver_speeds = payload.get("driver_speeds")
    if not isinstance(driver_speeds, list):
        print(f"    ❌ 失敗: driver_speeds 不是 list")
        print(f"       實際類型: {type(driver_speeds)}")
        print(f"       可用 keys: {list(payload.keys())}")
        return False
    print(f"    ✅ 通過: driver_speeds 是 list，長度={len(driver_speeds)}")

    print(f"\n✅ 所有驗證通過 (Speed)！")
    return True

def main():
    print("="*80)
    print("🧪 模擬 Loader 數據驗證流程")
    print("="*80)
    
    # 測試 Brake Performance
    brake_json = "json/brake_performance_2025_Singapore_R.json"
    print(f"\n📂 載入: {brake_json}")
    
    if not os.path.exists(brake_json):
        print(f"❌ 檔案不存在")
        return
    
    with open(brake_json, 'r', encoding='utf-8') as f:
        brake_data = json.load(f)
    
    print(f"✅ 檔案載入成功 ({os.path.getsize(brake_json)} bytes)")
    print(f"頂層 keys: {list(brake_data.keys())}")
    
    brake_result = brake_validate_data_format(brake_data)
    
    print(f"\n{'='*80}")
    print(f"🎯 Brake Performance 驗證結果: {'✅ 通過' if brake_result else '❌ 失敗'}")
    print(f"{'='*80}")
    
    # 測試 Speed Analysis
    speed_json = "json/all_drivers_straight_line_speed_2025_Singapore_R.json"
    print(f"\n📂 載入: {speed_json}")
    
    if not os.path.exists(speed_json):
        print(f"❌ 檔案不存在")
        return
    
    with open(speed_json, 'r', encoding='utf-8') as f:
        speed_data = json.load(f)
    
    print(f"✅ 檔案載入成功 ({os.path.getsize(speed_json)} bytes)")
    print(f"頂層 keys: {list(speed_data.keys())}")
    
    speed_result = speed_validate_data_format(speed_data)
    
    print(f"\n{'='*80}")
    print(f"🎯 Speed Analysis 驗證結果: {'✅ 通過' if speed_result else '❌ 失敗'}")
    print(f"{'='*80}")
    
    # 總結
    print(f"\n{'='*80}")
    print(f"📊 總結")
    print(f"{'='*80}")
    
    if brake_result and speed_result:
        print("✅ 兩者都通過驗證，不應該彈警告")
    elif not brake_result and speed_result:
        print("⚠️  Brake 驗證失敗，Speed 通過")
        print("💡 這解釋了為什麼只有 Brake 彈警告！")
    elif brake_result and not speed_result:
        print("⚠️  Brake 通過，Speed 失敗")
        print("❓ 但為什麼 Speed 沒彈警告？")
    else:
        print("❌ 兩者都失敗，但只有 Brake 彈警告？")

if __name__ == "__main__":
    main()
