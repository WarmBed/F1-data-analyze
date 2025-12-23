"""
比較 gear_trace.py 和 speed_trace.py 的關鍵差異
"""
import re

def read_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

gear_content = read_file('modules/gui/live_timing/live_timing_modules/gear_trace.py')
speed_content = read_file('modules/gui/live_timing/live_timing_modules/speed_trace.py')

print("=" * 80)
print("關鍵差異比較：gear_trace.py vs speed_trace.py")
print("=" * 80)

# 1. 類別名稱
print("\n1. 數據類別名稱:")
gear_class = re.search(r'class (Lap\w+Data)', gear_content)
speed_class = re.search(r'class (Lap\w+Data)', speed_content)
print(f"   Gear:  {gear_class.group(1) if gear_class else 'NOT FOUND'}")
print(f"   Speed: {speed_class.group(1) if speed_class else 'NOT FOUND'}")

# 2. 數據欄位
print("\n2. 數據欄位:")
gear_field = re.search(r'(gears|speeds|Gears|Speeds): List\[(\w+)\].*?# (.+)', gear_content)
speed_field = re.search(r'(gears|speeds|Gears|Speeds): List\[(\w+)\].*?# (.+)', speed_content)
print(f"   Gear:  {gear_field.group(1) if gear_field else 'NOT FOUND'}: List[{gear_field.group(2) if gear_field else '?'}]  # {gear_field.group(3) if gear_field else '?'}")
print(f"   Speed: {speed_field.group(1) if speed_field else 'NOT FOUND'}: List[{speed_field.group(2) if speed_field else '?'}]  # {speed_field.group(3) if speed_field else '?'}")

# 3. add_point 方法
print("\n3. add_point 方法參數:")
gear_add = re.search(r'def add_point\(self, distance: float, (\w+): (\w+), timestamp: float\)', gear_content)
speed_add = re.search(r'def add_point\(self, distance: float, (\w+): (\w+), timestamp: float\)', speed_content)
print(f"   Gear:  def add_point(self, distance: float, {gear_add.group(1) if gear_add else '?'}: {gear_add.group(2) if gear_add else '?'}, timestamp: float)")
print(f"   Speed: def add_point(self, distance: float, {speed_add.group(1) if speed_add else '?'}: {speed_add.group(2) if speed_add else '?'}, timestamp: float)")

# 4. Widget 類別名稱
print("\n4. Widget 類別名稱:")
gear_widget = re.search(r'class (\w+TraceWidget)\(QWidget\)', gear_content)
speed_widget = re.search(r'class (\w+TraceWidget)\(QWidget\)', speed_content)
print(f"   Gear:  {gear_widget.group(1) if gear_widget else 'NOT FOUND'}")
print(f"   Speed: {speed_widget.group(1) if speed_widget else 'NOT FOUND'}")

# 5. 數據範圍設定
print("\n5. 數據範圍設定:")
gear_min = re.search(r'self\.min_(gear|speed) = (\d+)', gear_content)
gear_max = re.search(r'self\.max_(gear|speed) = (\d+)', gear_content)
speed_min = re.search(r'self\.min_(gear|speed) = (\d+)', speed_content)
speed_max = re.search(r'self\.max_(gear|speed) = (\d+)', speed_content)
print(f"   Gear:  min_{gear_min.group(1) if gear_min else '?'} = {gear_min.group(2) if gear_min else '?'}, max_{gear_max.group(1) if gear_max else '?'} = {gear_max.group(2) if gear_max else '?'}")
print(f"   Speed: min_{speed_min.group(1) if speed_min else '?'} = {speed_min.group(2) if speed_min else '?'}, max_{speed_max.group(1) if speed_max else '?'} = {speed_max.group(2) if speed_max else '?'}")

# 6. snapshot 讀取邏輯
print("\n6. Snapshot 數據讀取:")
gear_get = re.search(r'(\w+) = driver_data\.get\([\'"](\w+)[\'"]\)', gear_content)
speed_get = re.search(r'(\w+) = driver_data\.get\([\'"](\w+)[\'"]\)', speed_content)
print(f"   Gear:  {gear_get.group(1) if gear_get else '?'} = driver_data.get('{gear_get.group(2) if gear_get else '?'}')")
print(f"   Speed: {speed_get.group(1) if speed_get else '?'} = driver_data.get('{speed_get.group(2) if speed_get else '?'}')")

# 7. MDI 類別名稱
print("\n7. MDI 類別名稱:")
gear_mdi = re.search(r'class (LiveTiming\w+Trace)\(BaseLiveTimingMDI\)', gear_content)
speed_mdi = re.search(r'class (LiveTiming\w+Trace)\(BaseLiveTimingMDI\)', speed_content)
print(f"   Gear:  {gear_mdi.group(1) if gear_mdi else 'NOT FOUND'}")
print(f"   Speed: {speed_mdi.group(1) if speed_mdi else 'NOT FOUND'}")

# 8. MODULE_ID
print("\n8. MODULE_ID:")
gear_id = re.search(r'MODULE_ID = [\'"]([^\'\"]+)[\'"]', gear_content)
speed_id = re.search(r'MODULE_ID = [\'"]([^\'\"]+)[\'"]', speed_content)
print(f"   Gear:  '{gear_id.group(1) if gear_id else 'NOT FOUND'}'")
print(f"   Speed: '{speed_id.group(1) if speed_id else 'NOT FOUND'}'")

# 9. 搜索所有 'gear' 或 'speed' 變數出現
print("\n9. 關鍵變數使用統計:")
gear_var_count = len(re.findall(r'\bgear\b', gear_content, re.IGNORECASE))
speed_var_count = len(re.findall(r'\bspeed\b', speed_content, re.IGNORECASE))
print(f"   Gear 檔案中 'gear' 出現次數: {gear_var_count}")
print(f"   Speed 檔案中 'speed' 出現次數: {speed_var_count}")

# 10. 檢查錯誤模式
print("\n10. 潛在錯誤檢查:")
gear_speed_ref = re.findall(r'speed', gear_content, re.IGNORECASE)
speed_gear_ref = re.findall(r'gear', speed_content, re.IGNORECASE)
print(f"   ⚠️  Gear 檔案中包含 'speed' 引用: {len(gear_speed_ref)} 次")
print(f"   ⚠️  Speed 檔案中包含 'gear' 引用: {len(speed_gear_ref)} 次")

if len(gear_speed_ref) > 10:  # 允許少量註解中的出現
    print("   ❌ Gear 檔案可能還有未完全替換的 'speed' 引用！")
    # 找出具體位置
    lines = gear_content.split('\n')
    for i, line in enumerate(lines[:50], 1):  # 只檢查前50行
        if 'speed' in line.lower() and 'gear' not in line.lower():
            print(f"      Line {i}: {line.strip()[:80]}")

print("\n" + "=" * 80)
print("比較完成")
print("=" * 80)
