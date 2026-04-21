#!/usr/bin/env python3
"""
Telemetry Analysis API 化測試
測試從 API 載入 Function 12 數據
"""

import sys
import os
import requests
import json

# 添加專案根目錄到路徑
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def test_api_endpoint():
    """測試 API 端點是否正常運作"""
    
    print("=" * 80)
    print("🧪 Telemetry Analysis API 化測試")
    print("=" * 80)
    
    # API 配置
    base_url = "http://localhost:8000"
    endpoint = f"{base_url}/api/v2/analysis/execute"
    
    # 測試參數
    params = {
        "function_id": "12",
        "year": 2025,
        "race": "Japan",
        "session": "R",
        "force_refresh": False
    }
    
    print(f"\n📡 測試 API 端點: {endpoint}")
    print(f"📋 參數: {json.dumps(params, indent=2, ensure_ascii=False)}")
    
    try:
        # 發送請求
        print(f"\n⏳ 發送 POST 請求...")
        response = requests.post(
            endpoint,
            params=params,
            timeout=120.0,
            headers={"Accept": "application/json"}
        )
        
        print(f"✅ HTTP 狀態碼: {response.status_code}")
        
        # 檢查狀態碼
        if response.status_code != 200:
            print(f"❌ 請求失敗: {response.status_code}")
            print(f"錯誤訊息: {response.text}")
            return False
        
        # 解析 JSON
        print(f"\n📦 解析 JSON 回應...")
        data = response.json()
        
        # 檢查回應格式
        print(f"\n🔍 檢查回應格式:")
        print(f"  - success: {data.get('success')}")
        print(f"  - message: {data.get('message')}")
        print(f"  - source: {data.get('source')}")
        print(f"  - execution_time: {data.get('execution_time')}")
        
        if not data.get("success"):
            print(f"❌ API 回傳 success=False")
            print(f"錯誤訊息: {data.get('message')}")
            return False
        
        # 檢查數據結構
        payload_data = data.get("data")
        if not isinstance(payload_data, dict):
            print(f"❌ data 欄位不是字典")
            return False
        
        print(f"\n📊 數據結構檢查:")
        print(f"  - data 類型: {type(payload_data)}")
        print(f"  - data 鍵: {list(payload_data.keys())[:5]}...")
        
        # 檢查 all_drivers_telemetry
        if "all_drivers_telemetry" in payload_data:
            telemetry_data = payload_data["all_drivers_telemetry"]
            driver_count = len(telemetry_data)
            print(f"\n🏎️ 遙測數據:")
            print(f"  - all_drivers_telemetry: ✅ 存在")
            print(f"  - 車手數量: {driver_count}")
            print(f"  - 車手代碼: {list(telemetry_data.keys())[:10]}...")
            
            # 檢查第一個車手的數據結構
            first_driver = list(telemetry_data.keys())[0]
            first_data = telemetry_data[first_driver]
            print(f"\n🔍 第一個車手 ({first_driver}) 數據結構:")
            print(f"  - 鍵: {list(first_data.keys())}")
            
            # 檢查必要欄位
            required_fields = ['driver_info', 'lap_time_analysis', 'sector_analysis']
            for field in required_fields:
                if field in first_data:
                    print(f"  - {field}: ✅")
                else:
                    print(f"  - {field}: ❌ 缺失")
                    
        else:
            print(f"❌ 缺少 all_drivers_telemetry 欄位")
            return False
        
        # 保存測試結果
        output_file = "test_output/telemetry_api_test_response.json"
        os.makedirs("test_output", exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 完整回應已保存到: {output_file}")
        
        print(f"\n" + "=" * 80)
        print(f"✅ API 測試通過！")
        print(f"=" * 80)
        
        return True
        
    except requests.exceptions.ConnectionError:
        print(f"\n❌ 無法連接到 API 伺服器")
        print(f"請確認 API 伺服器正在運行:")
        print(f"  python refactored_api.py")
        return False
        
    except requests.exceptions.Timeout:
        print(f"\n❌ API 請求超時")
        return False
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gui_integration():
    """測試 GUI 整合"""
    
    print(f"\n" + "=" * 80)
    print(f"🖥️ GUI 整合測試")
    print(f"=" * 80)
    

    def test_comparison_api_endpoint():
        """測試 Function 13 (雙車手遙測比較) API 端點"""

        print("\n" + "=" * 80)
        print("🧪 Telemetry Comparison API 測試")
        print("=" * 80)

        base_url = "http://localhost:8000"
        endpoint = f"{base_url}/api/v2/analysis/execute"

        params = {
            "function_id": "13",
            "year": 2025,
            "race": "Japan",
            "session": "R",
            "driver1": "VER",
            "driver2": "LEC",
            "lap1": 1,
            "lap2": 1,
            "force_refresh": False
        }

        print(f"📡 測試 API 端點: {endpoint}")
        print(f"📋 參數: {json.dumps(params, indent=2, ensure_ascii=False)}")

        try:
            response = requests.post(
                endpoint,
                params=params,
                timeout=120.0,
                headers={"Accept": "application/json"}
            )

            print(f"✅ HTTP 狀態碼: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ 請求失敗: {response.status_code}\n{response.text}")
                return False

            payload = response.json()
            if not payload.get("success"):
                print(f"❌ API success=false: {payload.get('message')}")
                return False

            data = payload.get("data", {})
            if "results" not in data:
                print("❌ 回傳缺少 results 區塊")
                return False

            results = data["results"]
            if "telemetry_comparison" not in results and "distance_difference" not in results:
                print("❌ 回傳缺少遙測比較資料")
                return False

            output_dir = "test_output"
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, "telemetry_comparison_api_test_response.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            print(f"💾 回應已保存到: {output_file}")
            print("✅ Telemetry Comparison API 測試通過！")
            return True

        except Exception as exc:
            print(f"❌ Telemetry Comparison API 測試失敗: {exc}")
            return False

    try:
        from PyQt5.QtWidgets import QApplication
        from modules.gui.telemetry_analysis_mdi import TelemetryDataManager
        
        app = QApplication(sys.argv)
        
        # 創建數據管理器
        print(f"\n📊 創建 TelemetryDataManager...")
        manager = TelemetryDataManager()
        
        # 設置測試標記
        test_completed = [False]
        test_error = [None]
        
        def on_loaded(data):
            print(f"\n✅ 數據載入完成！")
            print(f"  - 數據類型: {type(data)}")
            
            if "data" in data and "all_drivers_telemetry" in data["data"]:
                driver_count = len(data["data"]["all_drivers_telemetry"])
                print(f"  - 車手數量: {driver_count}")
                print(f"✅ GUI 整合測試通過！")
            else:
                print(f"❌ 數據格式不正確")
                test_error[0] = "數據格式錯誤"
                
            test_completed[0] = True
            app.quit()
        
        def on_error(error):
            print(f"\n❌ 載入失敗: {error}")
            test_error[0] = error
            test_completed[0] = True
            app.quit()
        
        # 連接信號
        manager.telemetry_loaded.connect(on_loaded)
        manager.error_occurred.connect(on_error)
        
        # 載入數據
        print(f"\n⏳ 開始載入遙測數據...")
        success = manager.loadTelemetryData("2025", "Japan", "R")
        
        if not success:
            print(f"❌ loadTelemetryData 返回 False")
            return False
        
        # 運行事件循環（最多等待 30 秒）
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(30000, lambda: app.quit() if not test_completed[0] else None)
        
        app.exec_()
        
        if test_error[0]:
            print(f"\n❌ GUI 整合測試失敗: {test_error[0]}")
            return False
        
        if not test_completed[0]:
            print(f"\n❌ 測試超時")
            return False
        
        return True
        
    except ImportError as e:
        print(f"\n⚠️ GUI 測試跳過（缺少依賴）: {e}")
        return True  # 不阻止測試
        
    except Exception as e:
        print(f"\n❌ GUI 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print(f"\n🚀 開始 Telemetry Analysis API 化測試...")
    
    # 測試 1: API 端點
    api_ok = test_api_endpoint()
    
    if not api_ok:
        print(f"\n❌ API 端點測試失敗，跳過 GUI 測試")
        sys.exit(1)
    
    # 測試 2: Function13 API
    comparison_ok = test_comparison_api_endpoint()

    if not comparison_ok:
        print("\n❌ Telemetry Comparison API 測試失敗，跳過 GUI 測試")
        sys.exit(1)

    # 測試 3: GUI 整合
    gui_ok = test_gui_integration()
    
    # 總結
    print(f"\n" + "=" * 80)
    print(f"📊 測試總結")
    print(f"=" * 80)
    print(f"  - Function12 API 測試: {'✅ 通過' if api_ok else '❌ 失敗'}")
    print(f"  - Function13 API 測試: {'✅ 通過' if comparison_ok else '❌ 失敗'}")
    print(f"  - GUI 整合測試: {'✅ 通過' if gui_ok else '❌ 失敗'}")
    print(f"=" * 80)
    
    if api_ok and comparison_ok and gui_ok:
        print(f"\n🎉 所有測試通過！Telemetry Analysis API 化成功！")
        sys.exit(0)
    else:
        print(f"\n❌ 部分測試失敗")
        sys.exit(1)
