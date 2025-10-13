#!/usr/bin/env python3
"""
測試理想圈排名表格 - API 調用版本
"""

import sys
sys.path.insert(0, 'd:\\OneDrive\\Code\\F1-data-analyze')

print("=" * 70)
print("理想圈排名表格 - API 調用測試")
print("=" * 70)
print()

# 測試 2: 檢查 requests 套件
print("測試 1: 檢查 requests 套件...")
try:
    import requests
    print(f"✅ requests 版本: {requests.__version__}")
except ImportError:
    print("❌ requests 套件未安裝")
    print("請執行: pip install requests")
    sys.exit(1)

print()

# 測試 3: 檢查 API 端點
print("測試 2: 檢查 API 可用性...")
try:
    api_url = "https://api.f1telemetrystationpro.org/health"
    print(f"  嘗試連接: {api_url}")
    response = requests.get(api_url, timeout=5.0)
    if response.status_code == 200:
        print(f"✅ API 可用 (狀態: {response.status_code})")
    else:
        print(f"⚠️  API 回應異常 (狀態: {response.status_code})")
except Exception as e:
    print(f"❌ API 無法連接: {e}")
    print("注意: 這可能是正常的（API 服務器未啟動）")

print()
print("=" * 70)
print("🎯 重要變更說明")
print("=" * 70)
print()
print("現在理想圈排名表格模組已實作 API 調用功能：")
print()
print("1. **優先使用 API**")
print("   - API URL: https://api.f1telemetrystationpro.org")
print("   - 端點: POST /api/v2/analysis/execute?function_id=53")
print()
print("2. **備援本地 JSON**")
print("   - 如果 API 失敗，自動嘗試讀取本地 JSON 檔案")
print("   - 位置: json/ideal_lap_ranking_2025_Japan_R.json")
print()
print("3. **終端訊息**")
print("   - 會顯示詳細的 API 調用過程")
print("   - 包含進度、延遲、數據源等資訊")
print()
print("=" * 70)
print("下一步: 啟動 GUI 並測試")
print("=" * 70)
print()
print("1. 啟動 GUI: python f1t_gui_main.py")
print("2. 選擇參數: 2025, Japan, R")
print("3. 點擊「理想圈分析」→「排名表格」")
print("4. 觀察終端輸出中的 API 調用訊息：")
print("   [API_WORKER] 🌐 調用 API: ...")
print("   [API_WORKER] ✅ API 調用成功")
print("   [IDEAL_LAP_MDI] ✅ 已從 API 載入資料")
