"""
驗證 GUI 是否正確顯示最高速度時間欄位

檢查項目：
1. GUI 表格 Widget 的列標題（應該有「最高速度時間」）
2. 數據填充邏輯（應該讀取 max_speed_time_seconds）
3. 確認「最終速度」欄位已移除
"""
import sys
import json

def verify_table_widget():
    """驗證表格 Widget 代碼"""
    print("=" * 80)
    print("驗證 GUI 表格 Widget")
    print("=" * 80)
    
    widget_file = "modules/gui/all_drivers_straight_line_speed_analysis/all_drivers_straight_line_speed_table_widget.py"
    
    with open(widget_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 檢查列標題
    print("\n1. 檢查列標題定義:")
    if "max_speed_time" in content:
        print("   ✅ 找到 'max_speed_time' 欄位")
    else:
        print("   ❌ 未找到 'max_speed_time' 欄位")
    
    if "最高速度時間" in content:
        print("   ✅ 找到中文標題 '最高速度時間'")
    else:
        print("   ❌ 未找到中文標題 '最高速度時間'")
    
    # 檢查是否移除了「最終速度」
    if "segment_end_speed" in content and "最終速度" in content:
        print("   ⚠️  仍然存在 'segment_end_speed' 和 '最終速度'（可能在註釋或其他位置）")
    else:
        print("   ✅ 已移除 'segment_end_speed' 欄位")
    
    # 檢查數據讀取
    print("\n2. 檢查數據讀取邏輯:")
    if "max_speed_time_seconds" in content:
        print("   ✅ 找到讀取 'max_speed_time_seconds' 的代碼")
    else:
        print("   ❌ 未找到讀取 'max_speed_time_seconds' 的代碼")
    
    # 檢查 setItem
    print("\n3. 檢查數據填充:")
    if "max_speed_time_item" in content:
        print("   ✅ 找到 'max_speed_time_item' 的創建代碼")
    else:
        print("   ❌ 未找到 'max_speed_time_item' 的創建代碼")
    
    if "self.table.setItem(row, 6, max_speed_time_item)" in content:
        print("   ✅ 找到第 6 欄填充代碼")
    else:
        print("   ❌ 第 6 欄填充代碼錯誤")

def verify_json_data():
    """驗證 JSON 數據是否包含 max_speed_time_seconds"""
    print("\n" + "=" * 80)
    print("驗證 JSON 數據")
    print("=" * 80)
    
    json_file = "json/all_drivers_straight_line_speed_2025_China_R.json"
    
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        print(f"\n📄 JSON 檔案: {json_file}")
        print(f"Algorithm Version: {data.get('algorithm_version', 'N/A')}")
        
        # 檢查第一位車手
        if "drivers" in data and len(data["drivers"]) > 0:
            first_driver = data["drivers"][0]
            driver_name = first_driver.get("driver", "Unknown")
            
            print(f"\n第一位車手: {driver_name}")
            print(f"  segment_accel_time_seconds: {first_driver.get('segment_accel_time_seconds', 'N/A')}")
            print(f"  max_speed_time_seconds: {first_driver.get('max_speed_time_seconds', 'N/A')}")
            print(f"  segment_unified_end_speed_kmh: {first_driver.get('segment_unified_end_speed_kmh', 'N/A')}")
            print(f"  segment_personal_max_speed_kmh: {first_driver.get('segment_personal_max_speed_kmh', 'N/A')}")
            
            # 檢查是否有 max_speed_time_seconds
            if "max_speed_time_seconds" in first_driver:
                print("\n✅ JSON 數據包含 'max_speed_time_seconds' 欄位")
            else:
                print("\n❌ JSON 數據不包含 'max_speed_time_seconds' 欄位")
        else:
            print("❌ JSON 數據中沒有車手數據")
    
    except FileNotFoundError:
        print(f"❌ 找不到 JSON 檔案: {json_file}")
    except Exception as e:
        print(f"❌ 讀取 JSON 失敗: {e}")

if __name__ == "__main__":
    verify_table_widget()
    verify_json_data()
    
    print("\n" + "=" * 80)
    print("驗證完成")
    print("=" * 80)
    print("\n💡 提示: 請在 GUI 中開啟「全車手直線加速分析」模組，檢查是否顯示「最高速度時間」欄位")
