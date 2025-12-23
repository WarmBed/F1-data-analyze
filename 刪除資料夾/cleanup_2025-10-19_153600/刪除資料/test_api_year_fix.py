#!/usr/bin/env python3
"""
測試 API 年份限制修復
驗證 2020-2025 年份範圍是否正常工作
"""

import requests
import json
from typing import Dict, Any

# API 基礎 URL
API_BASE_URL = "http://localhost:8000"  # 本地測試
# API_BASE_URL = "https://api.f1telemetrystationpro.org"  # 生產環境

def test_year_range():
    """測試不同年份的 API 請求"""
    
    print("=" * 70)
    print("測試 API 年份限制修復")
    print("=" * 70)
    
    test_cases = [
        # (year, expected_status, description)
        (2019, 422, "2019 - 應拒絕（低於最小值）"),
        (2020, 200, "2020 - 應接受（最小值）"),
        (2021, 200, "2021 - 應接受"),
        (2022, 200, "2022 - 應接受"),
        (2023, 200, "2023 - 應接受（原始問題）"),
        (2024, 200, "2024 - 應接受"),
        (2025, 200, "2025 - 應接受（最大值）"),
        (2026, 422, "2026 - 應拒絕（超過最大值）"),
    ]
    
    results = []
    
    for year, expected_status, description in test_cases:
        print(f"\n📋 測試: {description}")
        print(f"   年份: {year}, 預期狀態: {expected_status}")
        
        # 構建測試請求
        url = f"{API_BASE_URL}/api/v2/analysis/execute"
        params = {
            "function_id": "99",  # 使用功能 99（賽季日曆查詢）
            "year": year,
        }
        
        try:
            response = requests.post(url, params=params, timeout=5)
            actual_status = response.status_code
            
            # 檢查結果
            if actual_status == expected_status:
                result = "✅ 通過"
                status_icon = "✅"
            else:
                result = f"❌ 失敗 (實際: {actual_status})"
                status_icon = "❌"
            
            print(f"   結果: {result}")
            
            # 記錄結果
            results.append({
                "year": year,
                "expected": expected_status,
                "actual": actual_status,
                "passed": actual_status == expected_status,
                "description": description
            })
            
            # 如果是 200，顯示部分響應
            if actual_status == 200:
                try:
                    data = response.json()
                    if data.get("success"):
                        print(f"   ✅ API 成功返回數據")
                    else:
                        print(f"   ⚠️  API 返回失敗: {data.get('message', 'unknown')}")
                except:
                    pass
                    
        except requests.exceptions.ConnectionError:
            print(f"   ⚠️  無法連接到 API 服務器")
            print(f"   提示: 請確保 API 服務器正在運行")
            results.append({
                "year": year,
                "expected": expected_status,
                "actual": "CONNECTION_ERROR",
                "passed": False,
                "description": description
            })
        except Exception as e:
            print(f"   ❌ 測試失敗: {e}")
            results.append({
                "year": year,
                "expected": expected_status,
                "actual": f"ERROR: {e}",
                "passed": False,
                "description": description
            })
    
    # 統計結果
    print("\n" + "=" * 70)
    print("測試結果總結")
    print("=" * 70)
    
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    
    print(f"\n總測試數: {total}")
    print(f"通過: {passed}")
    print(f"失敗: {total - passed}")
    print(f"通過率: {passed/total*100:.1f}%")
    
    # 詳細結果
    print("\n詳細結果:")
    for r in results:
        status = "✅" if r["passed"] else "❌"
        print(f"  {status} {r['year']} - {r['description']}")
        if not r["passed"]:
            print(f"     預期: {r['expected']}, 實際: {r['actual']}")
    
    # 關鍵測試
    print("\n" + "=" * 70)
    print("關鍵測試點驗證")
    print("=" * 70)
    
    # 檢查 2023 年（原始問題）
    year_2023 = next((r for r in results if r["year"] == 2023), None)
    if year_2023 and year_2023["passed"]:
        print("✅ 2023 年請求修復成功（原始問題已解決）")
    else:
        print("❌ 2023 年請求仍然失敗")
    
    # 檢查範圍邊界
    year_2020 = next((r for r in results if r["year"] == 2020), None)
    year_2025 = next((r for r in results if r["year"] == 2025), None)
    if year_2020 and year_2020["passed"] and year_2025 and year_2025["passed"]:
        print("✅ 年份範圍邊界正確 (2020-2025)")
    else:
        print("❌ 年份範圍邊界有問題")
    
    # 檢查超出範圍的拒絕
    year_2019 = next((r for r in results if r["year"] == 2019), None)
    year_2026 = next((r for r in results if r["year"] == 2026), None)
    if year_2019 and year_2019["passed"] and year_2026 and year_2026["passed"]:
        print("✅ 超出範圍的年份正確拒絕")
    else:
        print("❌ 超出範圍的年份處理有問題")
    
    print("\n" + "=" * 70)
    
    return all(r["passed"] for r in results)


if __name__ == "__main__":
    try:
        success = test_year_range()
        if success:
            print("\n🎉 所有測試通過！API 年份限制修復成功！")
            exit(0)
        else:
            print("\n⚠️  部分測試失敗，請檢查上述詳細結果")
            exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  測試被用戶中斷")
        exit(1)
    except Exception as e:
        print(f"\n❌ 測試執行失敗: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
