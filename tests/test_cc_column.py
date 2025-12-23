"""
測試 ranking_tower.py 的 CC% 欄位修改
"""

print("=" * 70)
print("檢查 ranking_tower.py 的 CC% 欄位修改")
print("=" * 70)

# 檢查欄位數量
with open('modules/gui/live_timing/live_timing_modules/ranking_tower.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
# 檢查 1: setColumnCount
if 'setColumnCount(24)' in content:
    print("✅ 欄位數量已更新為 24")
else:
    print("❌ 欄位數量未更新")

# 檢查 2: 表頭包含 CC%
if '"OT%", "CC%"' in content:
    print("✅ 表頭包含 OT% 和 CC%")
else:
    print("❌ 表頭未包含 CC%")

# 檢查 3: CC% 欄位寬度
if content.count('41,   # CC% (近距離接觸機率)') > 0:
    print("✅ CC% 欄位寬度已設置")
else:
    print("❌ CC% 欄位寬度未設置")

# 檢查 4: _set_close_combat_probability 方法
if 'def _set_close_combat_probability' in content:
    print("✅ _set_close_combat_probability 方法已添加")
else:
    print("❌ _set_close_combat_probability 方法未添加")

# 檢查 5: 調用 CC% 設置
if '_set_close_combat_probability(row, driver_data, default_text_color)' in content:
    print("✅ CC% 設置方法已調用")
else:
    print("❌ CC% 設置方法未調用")

# 檢查 6: DRS 欄位索引更新為 23
if 'self.table.setItem(row, 23, drs_item)' in content:
    print("✅ DRS 欄位索引已更新為 23")
else:
    print("❌ DRS 欄位索引未更新")

print("\n" + "=" * 70)
print("修改檢查完成")
print("=" * 70)
print("\n說明:")
print("  - 欄位 21: OT% (超車機率)")
print("  - 欄位 22: CC% (近距離接觸機率) ⭐ 新增")
print("  - 欄位 23: DRS")
print("\n顏色編碼:")
print("  - OT% >= 80%: 橙色背景 (極高超車機會)")
print("  - CC% >= 70%: 淺藍色背景 (高機率追近)")
