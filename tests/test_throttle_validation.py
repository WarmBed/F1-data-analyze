#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
測試 Throttle Box Plot 數據格式驗證邏輯
"""

import json
from typing import Any, Dict

def _validate_data_format(data: Any) -> bool:
    """
    複製 throttle_box_plot_analysis_mdi.py 的驗證邏輯
    """
    print(f"[STEP 1] 檢查數據類型: {type(data)}")
    if not isinstance(data, dict):
        print("❌ 數據格式錯誤：必須是字典格式")
        return False
    
    print(f"[STEP 2] 檢查是否包含 'analysis' 鍵: {list(data.keys())}")
    if "analysis" not in data:
        print("❌ 數據格式錯誤：缺少 analysis 欄位")
        return False
    
    analysis = data["analysis"]
    print(f"[STEP 3] 檢查 analysis 類型和內容: {type(analysis)}, 鍵: {list(analysis.keys()) if isinstance(analysis, dict) else 'NOT DICT'}")
    if not isinstance(analysis, dict) or "drivers" not in analysis:
        print("❌ 數據格式錯誤：analysis 中缺少 drivers")
        return False
    
    print("✅ 驗證通過")
    return True

def test_api_response():
    """測試 API 響應格式"""
    print("=" * 60)
    print("測試 1: 完整 API 響應")
    print("=" * 60)
    
    # 載入實際 JSON 檔案
    with open('json/driver_throttle_ratio_2025_Brazil_SQ.json', 'r', encoding='utf-8') as f:
        full_response = json.load(f)
    
    print("\n[API 響應結構]")
    print(f"Root keys: {list(full_response.keys())}")
    print(f"success: {full_response.get('success')}")
    print(f"message: {full_response.get('message')}")
    
    # 模擬 API Worker 的數據提取
    print("\n" + "=" * 60)
    print("測試 2: 提取 'data' 欄位（模擬 payload.get('data')）")
    print("=" * 60)
    
    data = full_response.get("data")
    print(f"\nExtracted data type: {type(data)}")
    print(f"Extracted data keys: {list(data.keys()) if isinstance(data, dict) else 'NOT DICT'}")
    
    # 執行驗證
    print("\n" + "=" * 60)
    print("測試 3: 執行驗證邏輯")
    print("=" * 60)
    result = _validate_data_format(data)
    
    print("\n" + "=" * 60)
    print(f"最終結果: {'✅ 驗證通過' if result else '❌ 驗證失敗'}")
    print("=" * 60)
    
    # 額外檢查
    if result:
        drivers_count = len(data['analysis']['drivers'])
        print(f"\n📊 數據統計:")
        print(f"  - 車手數量: {drivers_count}")
        print(f"  - 第一位車手: {data['analysis']['drivers'][0]['driver_code']}")
        print(f"  - 第一位車手圈數: {len(data['analysis']['drivers'][0]['laps'])}")

if __name__ == "__main__":
    test_api_response()
