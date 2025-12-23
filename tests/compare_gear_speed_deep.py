"""
深度比較 gear_trace.py 和 speed_trace.py 的 Widget 類別內部方法
"""
import re

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

gear_content = read_file('modules/gui/live_timing/live_timing_modules/gear_trace.py')
speed_content = read_file('modules/gui/live_timing/live_timing_modules/speed_trace.py')

# 提取 Widget 類別的內容
gear_widget_match = re.search(r'class GearTraceWidget\(QWidget\):.*?(?=class Live)', gear_content, re.DOTALL)
speed_widget_match = re.search(r'class SpeedTraceWidget\(QWidget\):.*?(?=class Live)', speed_content, re.DOTALL)

if not gear_widget_match or not speed_widget_match:
    print("❌ 無法提取 Widget 類別內容")
    exit(1)

gear_widget = gear_widget_match.group(0)
speed_widget = speed_widget_match.group(0)

print("=" * 80)
print("Widget 類別深度比較")
print("=" * 80)

# 1. 初始化中的屬性名稱
print("\n1. Widget 初始化屬性:")
print("-" * 40)
gear_attrs = re.findall(r'self\._primary_(\w+)_lap:', gear_widget)
speed_attrs = re.findall(r'self\._primary_(\w+)_lap:', speed_widget)
print(f"Gear attributes:  {set(gear_attrs)}")
print(f"Speed attributes: {set(speed_attrs)}")

# 2. 檢查 _all_best_laps 的類型提示
print("\n2. _all_best_laps 類型提示:")
print("-" * 40)
gear_best_type = re.search(r'self\._all_best_laps: Dict\[str, (\w+)\]', gear_widget)
speed_best_type = re.search(r'self\._all_best_laps: Dict\[str, (\w+)\]', speed_widget)
print(f"Gear:  Dict[str, {gear_best_type.group(1) if gear_best_type else '?'}]")
print(f"Speed: Dict[str, {speed_best_type.group(1) if speed_best_type else '?'}]")

# 3. 檢查 _all_current_laps 的類型提示
print("\n3. _all_current_laps 類型提示:")
print("-" * 40)
gear_current_type = re.search(r'self\._all_current_laps: Dict\[str, (\w+)\]', gear_widget)
speed_current_type = re.search(r'self\._all_current_laps: Dict\[str, (\w+)\]', speed_widget)
print(f"Gear:  Dict[str, {gear_current_type.group(1) if gear_current_type else '?'}]")
print(f"Speed: Dict[str, {speed_current_type.group(1) if speed_current_type else '?'}]")

# 4. 檢查繪圖方法中的數據訪問
print("\n4. 繪圖方法中數據訪問模式:")
print("-" * 40)
gear_draw = re.findall(r'lap_data\.(gears|speeds)\[', gear_widget)
speed_draw = re.findall(r'lap_data\.(gears|speeds)\[', speed_widget)
print(f"Gear:  lap_data.{gear_draw[0] if gear_draw else 'NOT FOUND'}[i]")
print(f"Speed: lap_data.{speed_draw[0] if speed_draw else 'NOT FOUND'}[i]")

# 5. 檢查類型註解
print("\n5. LapData 類型使用:")
print("-" * 40)
gear_type_hints = re.findall(r'Optional\[(Lap\w+Data)\]', gear_widget)
speed_type_hints = re.findall(r'Optional\[(Lap\w+Data)\]', speed_widget)
print(f"Gear:  {set(gear_type_hints)}")
print(f"Speed: {set(speed_type_hints)}")

# 6. 檢查實例化
print("\n6. LapData 實例化:")
print("-" * 40)
gear_init = re.findall(r'(Lap\w+Data)\(', gear_widget)
speed_init = re.findall(r'(Lap\w+Data)\(', speed_widget)
print(f"Gear:  {set(gear_init)}")
print(f"Speed: {set(speed_init)}")

# 7. 檢查 update_from_snapshot 中的變數
print("\n7. update_from_snapshot 方法中的關鍵變數:")
print("-" * 40)
gear_update = re.search(r'def update_from_snapshot.*?(?=def \w+)', gear_widget, re.DOTALL)
speed_update = re.search(r'def update_from_snapshot.*?(?=def \w+)', speed_widget, re.DOTALL)

if gear_update and speed_update:
    gear_vars = re.findall(r'\b(gear|speed)\b = driver_data\.get', gear_update.group(0))
    speed_vars = re.findall(r'\b(gear|speed)\b = driver_data\.get', speed_update.group(0))
    print(f"Gear:  變數名稱 = {gear_vars[0] if gear_vars else 'NOT FOUND'}")
    print(f"Speed: 變數名稱 = {speed_vars[0] if speed_vars else 'NOT FOUND'}")
    
    # 檢查是否還有錯誤的引用
    if gear_update:
        wrong_refs = re.findall(r'\bspeed\b(?!\w)', gear_update.group(0).lower())
        if wrong_refs:
            print(f"   ⚠️  Gear 模組中發現 {len(wrong_refs)} 個 'speed' 引用")

# 8. 檢查 _calculate_distance 方法簽名
print("\n8. _calculate_distance 方法簽名:")
print("-" * 40)
gear_calc = re.search(r'def _calculate_distance\(self, driver_num: str, (\w+): \w+,', gear_widget)
speed_calc = re.search(r'def _calculate_distance\(self, driver_num: str, (\w+): \w+,', speed_widget)
print(f"Gear:  def _calculate_distance(self, driver_num: str, {gear_calc.group(1) if gear_calc else '?'}: ..., ...)")
print(f"Speed: def _calculate_distance(self, driver_num: str, {speed_calc.group(1) if speed_calc else '?'}: ..., ...)")

# 9. 檢查 add_point 調用
print("\n9. add_point 方法調用:")
print("-" * 40)
gear_add_call = re.findall(r'\.add_point\([^,]+,\s*(\w+),', gear_widget)
speed_add_call = re.findall(r'\.add_point\([^,]+,\s*(\w+),', speed_widget)
print(f"Gear:  .add_point(distance, {gear_add_call[0] if gear_add_call else '?'}, timestamp)")
print(f"Speed: .add_point(distance, {speed_add_call[0] if speed_add_call else '?'}, timestamp)")

print("\n" + "=" * 80)
print("深度比較完成")
print("=" * 80)
