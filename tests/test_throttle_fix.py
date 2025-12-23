#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試 Throttle Box Plot 雙層嵌套修復
"""

import requests
import json

def test_api_response_format():
    """測試 API 響應格式和 GUI 處理"""
    print("=" * 60)
    print("測試 Throttle Box Plot API 數據格式修復")
    print("=" * 60)
    
    # 調用 API
    print("\n[步驟 1] 調用 API 獲取數據...")
    url = "http://localhost:8000/api/v2/analysis/execute"
    params = {
        "function_id": "54",
        "year": 2025,
        "race": "Japan",
        "session": "R"
    }
    
    response = requests.post(url, params=params, timeout=120)
    print(f"HTTP 狀態: {response.status_code}")
    
    # 解析響應
    print("\n[步驟 2] 解析 API 響應...")
    payload = response.json()
    print(f"外層 keys: {list(payload.keys())}")
    print(f"success: {payload.get('success')}")
    
    # 模擬 GUI 數據提取（舊邏輯）
    print("\n[步驟 3] 模擬舊邏輯（應該失敗）...")
    raw_data_old = payload.get("data")
    print(f"raw_data keys: {list(raw_data_old.keys())}")
    print(f"Has 'analysis': {'analysis' in raw_data_old}")  # 應該是 False
    
    # 模擬 GUI 數據提取（新邏輯）
    print("\n[步驟 4] 模擬新邏輯（應該成功）...")
    raw_data_new = payload.get("data")
    
    # 檢測雙層嵌套
    if isinstance(raw_data_new, dict) and "data" in raw_data_new and "success" in raw_data_new:
        print("✅ 檢測到雙層嵌套格式")
        print(f"外層 keys: {list(raw_data_new.keys())}")
        raw_data_new = raw_data_new["data"]  # 提取內層
        print(f"內層 keys: {list(raw_data_new.keys())}")
    
    # 驗證數據格式
    print("\n[步驟 5] 驗證數據格式...")
    def validate_format(data):
        if not isinstance(data, dict):
            print("❌ 必須是字典格式")
            return False
        if "analysis" not in data:
            print("❌ 缺少 analysis 欄位")
            return False
        if "drivers" not in data["analysis"]:
            print("❌ analysis 中缺少 drivers")
            return False
        return True
    
    result = validate_format(raw_data_new)
    print(f"驗證結果: {'✅ 通過' if result else '❌ 失敗'}")
    
    # 統計數據
    if result:
        print("\n[步驟 6] 數據統計...")
        drivers_count = len(raw_data_new['analysis']['drivers'])
        print(f"  - 車手數量: {drivers_count}")
        print(f"  - 第一位車手: {raw_data_new['analysis']['drivers'][0]['driver_code']}")
        print(f"  - Metadata 年份: {raw_data_new['metadata']['year']}")
        print(f"  - Metadata 賽事: {raw_data_new['metadata']['race']}")

if __name__ == "__main__":
    test_api_response_format()
