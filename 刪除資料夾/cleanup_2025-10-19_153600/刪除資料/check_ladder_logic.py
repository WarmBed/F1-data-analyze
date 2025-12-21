"""
檢查 F48 階梯式邏輯是否正確實現
"""
import json
import sys

json_file = "json/all_drivers_straight_line_speed_2025_Singapore_R.json"

try:
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 獲取 metadata
    if 'data' in data:
        metadata = data['data'].get('metadata', {})
    else:
        metadata = data.get('metadata', {})
    
    # 檢查 unified_speed_range
    unified_range = metadata.get('unified_speed_range', {})
    
    print("=" * 80)
    print("F48 階梯式邏輯驗證報告")
    print("=" * 80)
    
    if unified_range:
        start_speed = unified_range.get('start_speed_kmh')
        end_speed = unified_range.get('end_speed_kmh')
        adjustment_reason = unified_range.get('adjustment_reason', '')
        
        print(f"\n統一起始速度: {start_speed} km/h")
        print(f"統一終點速度: {end_speed} km/h")
        print(f"\n調整原因: {adjustment_reason}")
        
        # 檢查是否為 10 的倍數
        print("\n" + "=" * 80)
        print("階梯式邏輯檢查:")
        print("=" * 80)
        
        if start_speed and start_speed % 10 == 0:
            print(f"✅ 起始速度 {start_speed} km/h 符合 10 km/h 階梯")
        else:
            print(f"⚠️  起始速度 {start_speed} km/h 不是 10 的倍數")
        
        if end_speed and end_speed % 10 == 0:
            print(f"✅ 終點速度 {end_speed} km/h 符合 10 km/h 階梯")
        else:
            print(f"⚠️  終點速度 {end_speed} km/h 不是 10 的倍數")
        
        # 檢查是否在合理範圍內
        print("\n" + "=" * 80)
        print("合理性檢查:")
        print("=" * 80)
        
        if start_speed:
            if 100 <= start_speed <= 200:
                print(f"✅ 起始速度 {start_speed} km/h 在合理範圍 (100-200)")
            else:
                print(f"⚠️  起始速度 {start_speed} km/h 超出預期範圍 (100-200)")
        
        if end_speed:
            if 250 <= end_speed <= 300:
                print(f"✅ 終點速度 {end_speed} km/h 在合理範圍 (250-300)")
            else:
                print(f"⚠️  終點速度 {end_speed} km/h 超出預期範圍 (250-300)")
        
        # 檢查調整原因是否提到「階梯式」
        if '階梯式' in adjustment_reason:
            print("\n✅ 調整原因中包含「階梯式」關鍵字，確認新邏輯已啟用")
        else:
            print("\n⚠️  調整原因中未提到「階梯式」，可能仍使用舊邏輯")
    
    else:
        print("\n❌ 未找到 unified_speed_range 元數據")
        print("可能需要重新執行 CLI 分析生成新的 JSON 檔案")
    
    print("\n" + "=" * 80)

except FileNotFoundError:
    print(f"❌ 找不到檔案: {json_file}")
    print("請先執行: python f1_analysis_modular_main.py -f 48 -y 2025 -r Singapore -s R")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"❌ JSON 解析錯誤: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 未預期的錯誤: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
