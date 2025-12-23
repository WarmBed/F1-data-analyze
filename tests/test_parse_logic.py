"""深度調試 - 手動執行解析邏輯"""
import re
from pathlib import Path
import PyPDF2

pdf_path = Path('FIAdoc/2025/2025 São Paulo Grand Prix - Parts and parameters been replaced and or changed during Parc Fermé.pdf')

# 提取文字
with open(pdf_path, 'rb') as file:
    reader = PyPDF2.PdfReader(file)
    text = reader.pages[0].extract_text()

# 檢查條件
print(f"檢查 1: 'parts and parameters' in text.lower() = {'parts and parameters' in text.lower()}")
print(f"檢查 2: 'parc ferm' in text.lower() = {'parc ferm' in text.lower()}")

# 按行處理
lines = [line.strip() for line in text.split('\n')]
print(f"\n總行數: {len(lines)}")

current_team = None
current_car_number = None
changes_count = 0

skip_patterns = [
    r'^from the fia',
    r'^to the stewards',
    r'^\d{4}\s+.+grand prix$',
    r'^technical delegate.?s report$',
    r'^date\s+\d',
    r'^time\s+\d',
    r'^page\s+\d',
    r'^document\s+\d'
]

for i, line in enumerate(lines, 1):
    if not line or len(line) < 3:
        continue
    
    line_lower = line.lower()
    
    # 檢查跳過條件
    should_skip = any(re.match(pattern, line_lower) for pattern in skip_patterns)
    if should_skip:
        print(f"第 {i:2d} 行: [SKIP] {line[:50]}")
        continue
    
    # 檢測車隊標題
    if line.endswith(':') and not line.startswith('Car'):
        current_team = line[:-1].strip()
        current_car_number = None
        print(f"第 {i:2d} 行: [TEAM] {current_team}")
        continue
    
    # 檢測車號行
    car_match = re.match(r'Car\s+(\d+):\s*(.*)', line, re.IGNORECASE)
    if car_match:
        current_car_number = car_match.group(1)
        part = car_match.group(2).strip()
        if part and len(part) > 3:
            changes_count += 1
            print(f"第 {i:2d} 行: [CAR+PART] 車號 {current_car_number}, 部件: {part}")
        else:
            print(f"第 {i:2d} 行: [CAR] 車號 {current_car_number}")
        continue
    
    # 接續部件
    if current_car_number and current_team and not line.endswith(':'):
        if not (re.match(r'^\d+$', line) or re.match(r'^[A-Z]{2,3}$', line)):
            changes_count += 1
            print(f"第 {i:2d} 行: [PART] 車號 {current_car_number}, 部件: {line}")
            continue
    
    print(f"第 {i:2d} 行: [IGNORE] {line[:50]}")

print(f"\n✅ 總共應提取 {changes_count} 筆記錄")
